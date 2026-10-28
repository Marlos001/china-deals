"""Bounded public promotion text, for human/agent adjudication of exact conditions.

No campaigns, prices, percentages, savings or eligibility are derived here.
HTTP hashes cover decoded response text encoded as UTF-8, not wire bytes.
Capture hashes cover the original caller-supplied visibleText encoded as UTF-8.
"""

import hashlib
import re
import time
from datetime import datetime
from html import escape
from html.parser import HTMLParser

from . import adapters, guest
from .marketplaces import HOSTS, PRODUCT_HOSTS, PUBLIC_METADATA_MARKETPLACES
from .models import marketplace_name, utc_now

MAX_SNIPPETS = 30
MAX_SNIPPET_CHARS = 1000
MAX_CAPTURE_BYTES = 256 * 1024
_HOSTS = {
    'jd': {'item.jd.com', 'item.m.jd.com', 'www.jd.com', 'm.jd.com'},
    'taobao': {'www.taobao.com', 'item.taobao.com', 'detail.tmall.com'},
    'goofish': {'www.goofish.com', 'goofish.com'},
    'blibli': {'www.blibli.com'},
}

_HOSTS.update({market: set(PRODUCT_HOSTS[market]) | {HOSTS[market][0], "www." + HOSTS[market][0]}
               for market in PUBLIC_METADATA_MARKETPLACES})

_TERMS = re.compile(
    r'优惠|优惠券|领券|折扣|满减|满.{0,16}减|立减|直降|折|补贴|返现|红包|促销|包邮|'
    r'\b(?:coupons?|discounts?|vouchers?|cashback|promo(?:tion)?s?|kupon|diskon|'
    r'potongan|hemat|gratis\s+ongkir|free\s+shipping)\b', re.I)
_EXCLUDED = {'script', 'style', 'template', 'head', 'noscript', 'iframe', 'object', 'svg', 'canvas'}
_BLOCKS = {'address', 'article', 'aside', 'blockquote', 'br', 'dd', 'div', 'dl', 'dt',
           'fieldset', 'figcaption', 'figure', 'footer', 'form', 'h1', 'h2', 'h3', 'h4',
           'h5', 'h6', 'header', 'hr', 'li', 'main', 'nav', 'ol', 'p', 'pre', 'section',
           'table', 'tbody', 'td', 'th', 'thead', 'tr', 'ul'}
_VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta',
         'param', 'source', 'track', 'wbr'}

# Fixed read-only expression for a caller's public T3 page. No navigation or I/O.
CAPTURE_JS = r"""() => {
  const text = document.body ? document.body.innerText : '';
  const bytes = new TextEncoder().encode(text).length;
  return {url: location.href, capturedAt: new Date().toISOString(),
    visibleText: bytes <= 262144 ? text : '', visibleTextBytes: bytes,
    visibleTextTruncated: bytes > 262144};
}"""


def _url(value, marketplace):
    if (not isinstance(value, str) or len(value) > 4096 or not value.isascii()
            or re.search(r'%(?![0-9a-f]{2})', value, re.I)
            or re.search(r'%[01][0-9a-f]|%7f', value, re.I)
            or not guest._valid_url(value, _HOSTS[marketplace])):
        raise ValueError('Promotion URL must be percent-encoded HTTPS on an allowed primary host, without credentials or port')
    return value


class _VisibleHTML(HTMLParser):
    """Preserve inline words and block boundaries; never inspect embedded data."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.stack = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        hidden = (tag in _EXCLUDED or 'hidden' in attrs or 'inert' in attrs
                  or (attrs.get('aria-hidden') or '').lower() == 'true'
                  or re.search(r'(?:display\s*:\s*none|visibility\s*:\s*hidden)',
                               attrs.get('style') or '', re.I) is not None)
        if not self.hidden and (tag in _BLOCKS or hidden):
            self.parts.append('\n')
        if tag not in _VOID:
            if len(self.stack) >= 256:
                raise adapters._Failure('unavailable', 'html_depth_limit',
                                        'Promotion HTML nesting exceeded 256; no text admitted.')
            self.stack.append((tag, hidden))
            self.hidden += hidden

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in _VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        # Malformed closing tags inside excluded content must not reveal it.
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                if any(hidden for _, hidden in self.stack[index + 1:]):
                    return
                self.hidden -= sum(hidden for _, hidden in self.stack[index:])
                del self.stack[index:]
                break
        if not self.hidden and (tag in _BLOCKS or tag in _EXCLUDED):
            self.parts.append('\n')

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def _snippets(text):
    # Neighbouring text blocks retain conditions which follow a coupon heading.
    lines = [' '.join(line.split()) for line in text.splitlines() if line.strip()]
    spans = []
    for index, line in enumerate(lines):
        if _TERMS.search(line):
            start, end = max(0, index - 1), min(len(lines), index + 2)
            if spans and start <= spans[-1][1]:
                spans[-1][1] = end
            else:
                spans.append([start, end])
    snippets, truncated = [], False
    for start, end in spans:
        section = '\n'.join(lines[start:end])
        # Long blocks may have a term far from the start. Keep bounded literal
        # windows around matches, in source order, and disclose lost context.
        if len(section) <= MAX_SNIPPET_CHARS:
            pieces = [section]
        else:
            pieces, previous_end = [], 0
            truncated = True
            for match in _TERMS.finditer(section):
                if match.start() < previous_end:
                    continue
                left = max(previous_end, match.start() - 300)
                right = min(len(section), left + MAX_SNIPPET_CHARS)
                pieces.append(section[left:right])
                previous_end = right
                if len(pieces) > MAX_SNIPPETS:
                    break
        for piece in pieces:
            if len(snippets) == MAX_SNIPPETS:
                return snippets, True
            snippets.append(piece)
    return snippets, truncated


def _envelope(marketplace, url):
    return {
        'schema_version': '1', 'marketplace': marketplace, 'status': 'unavailable',
        'requested_url': url, 'source_url': url, 'observed_at': None,
        'retrieved_at': None, 'source_updated_at': None, 'source_mode': None,
        'snippets': [], 'snippets_truncated': False, 'content_sha256': None,
        'content_sha256_basis': None, 'error': None,
        'warnings': [
            'Literal promotion text only; eligibility, exact savings, validity and checkout conditions are unverified.',
            'Page-wide excerpts may include banners or recommendations; they assert no main-product price.',
            'observed_at is retrieval/capture time, not the source update time; source_updated_at is unknown.',
            'No extracted snippet does not establish that no coupons exist.',
        ],
        'access': {'mode': 'guest', 'authenticated': False, 'attempts': []},
    }


def _evidence(result, text, content, observed_at, basis):
    snippets, truncated = _snippets(text)
    result.update(status='ok' if snippets else 'empty_unverified', source_mode='coupon_page',
                  observed_at=observed_at, snippets=snippets, snippets_truncated=truncated,
                  content_sha256=hashlib.sha256(content.encode('utf-8')).hexdigest(),
                  content_sha256_basis=basis)
    if truncated:
        result['warnings'].append('Snippet limits omitted text/conditions; excerpts are incomplete evidence.')
    return result


def read_promotions(marketplace, url, timeout=30):
    """One cookie-free guest read; invalid inputs raise ValueError.

    Return a JSON-serializable envelope. ok means matched text, empty_unverified
    means no matched text, and guest access failures retain status/error codes.
    Neither successful status establishes a usable coupon. source_mode is null
    on failure. Allowed same-market redirects bind source_url to the final URL.
    """
    if not isinstance(marketplace, str) or len(marketplace) > 32:
        raise ValueError('Invalid marketplace')
    marketplace = marketplace_name(marketplace)
    url = _url(url, marketplace)
    timeout = adapters._timeout(timeout)
    if timeout > 120:
        raise ValueError('timeout must not exceed 120 seconds')
    result = _envelope(marketplace, url)
    try:
        body, final_url = guest._read(result, url, _HOSTS[marketplace],
                                     time.monotonic() + timeout, 'coupon_page')
        try:
            _url(final_url, marketplace)
        except ValueError:
            raise adapters._Failure('blocked', 'redirect_denied', 'Final promotion URL is not allowed.') from None
        if not isinstance(body, str) or len(body.encode('utf-8')) > guest.MAX_RESPONSE_BYTES:
            raise adapters._Failure('error', 'output_limit', 'Promotion response exceeded 2 MiB; no text admitted.')
        if body.lstrip().startswith(('{', '[')):
            raise adapters._Failure('unavailable', 'non_html_response',
                                    'Structured data is not public HTML text; no promotion text admitted.')
        parser = _VisibleHTML()
        parser.feed(body)
        parser.close()
        stamp = utc_now()
        result.update(source_url=final_url, retrieved_at=stamp)
        result['warnings'].append('Static HTML text only; CSS visibility and dynamically loaded promotions are unverified.')
        return _evidence(result, ''.join(parser.parts), body, stamp, 'decoded_html_utf8')
    except adapters._Failure as exc:
        result.update(status=exc.status, error={'code': exc.code, 'message': exc.message})
        attempt = result['access']['attempts'][-1]
        if attempt['status'] != 'skipped_after_challenge':
            attempt.update(status=exc.status, error_code=exc.code)
        return result


def parse_capture(capture, marketplace, requested_url):
    """Import CAPTURE_JS's value offline, never the enclosing MCP response.

    Require exact URL identity (including query/fragment), an aware capturedAt,
    visibleText, its exact UTF-8 visibleTextBytes, and visibleTextTruncated=False.
    Invalid/truncated captures raise ValueError. Capture time is never refreshed.
    Authenticity, public access and visibility are caller-supplied assertions.
    """
    if not isinstance(marketplace, str) or len(marketplace) > 32:
        raise ValueError('Invalid marketplace')
    marketplace = marketplace_name(marketplace)
    requested_url = _url(requested_url, marketplace)
    if not isinstance(capture, dict):
        raise ValueError('Capture must be an object')
    if _url(capture.get('url'), marketplace) != requested_url:
        raise ValueError('Capture URL must exactly match requested_url')
    stamp = capture.get('capturedAt')
    try:
        if not isinstance(stamp, str) or len(stamp) > 64:
            raise ValueError
        parsed = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
        if parsed.utcoffset() is None:
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError('Capture requires a timezone-aware capturedAt') from None
    text = capture.get('visibleText')
    if (not isinstance(text, str) or len(text) > MAX_CAPTURE_BYTES
            or len(text.encode('utf-8')) > MAX_CAPTURE_BYTES
            or capture.get('visibleTextTruncated') is not False
            or type(capture.get('visibleTextBytes')) is not int
            or capture['visibleTextBytes'] != len(text.encode('utf-8'))):
        raise ValueError('Capture text must be complete, within 256 KiB, and match visibleTextBytes')
    result = _envelope(marketplace, requested_url)
    result.update(imported_at=utc_now())
    result['access'] = {'mode': 'capture_import', 'authenticated': None, 'attempts': []}
    result['warnings'].append(
        'Capture authenticity, public guest access and visible-text provenance are caller supplied; no primary fetch was performed by this import.')
    # Escape markup so visible code/text stays inert, while reusing challenge checks.
    try:
        guest._html(escape(text))
    except adapters._Failure as exc:
        result.update(status=exc.status, error={'code': exc.code, 'message': exc.message})
        return result
    return _evidence(result, text, text, stamp, 'captured_visible_text_utf8')
