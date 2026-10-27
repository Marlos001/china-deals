"""Network-free, caller-asserted browser captures for the new China markets."""

from datetime import datetime

from .marketplaces import canonical_product_url

MAX_HTML_BYTES = 2 * 1024 * 1024
CAPTURE_JS = """() => {
  const html = document.documentElement.outerHTML;
  const bytes = new TextEncoder().encode(html).length;
  return {url: location.href, capturedAt: new Date().toISOString(),
    html: bytes <= 2097152 ? html : null, htmlBytes: bytes,
    htmlTruncated: bytes > 2097152};
}"""


def parse_capture(capture, marketplace, requested_url):
    if marketplace not in {'tmall', '1688', 'weidian'}:
        raise ValueError('This capture reader supports Tmall, 1688 and Weidian')
    if not isinstance(capture, dict):
        raise ValueError('Capture must be an object')
    expected = canonical_product_url(marketplace, requested_url)
    actual = canonical_product_url(marketplace, capture.get('url'))
    if not expected or actual != expected:
        raise ValueError('Requested and captured native item identities must agree')
    stamp = capture.get('capturedAt')
    try:
        clock = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
        if clock.tzinfo is None:
            raise ValueError
    except (ValueError, TypeError, AttributeError):
        raise ValueError('Capture requires a timezone-aware capturedAt') from None
    body = capture.get('html')
    if not isinstance(body, str) or not body or capture.get('htmlTruncated') is not False:
        raise ValueError('Capture requires complete, nonempty HTML')
    size = len(body.encode('utf-8'))
    if type(capture.get('htmlBytes')) is not int or capture['htmlBytes'] != size or size > MAX_HTML_BYTES:
        raise ValueError('Capture HTML byte count must match and remain within 2 MiB')
    from . import adapters, guest
    try:
        guest._html(body)
    except adapters._Failure:
        raise ValueError('Captured page requests login or verification; no product observation imported') from None
    from .china_public import parse_product_page
    row = parse_product_page(body, marketplace, expected, stamp)
    row.setdefault('source_detail', {})['capture_provenance'] = {
        'captured_url': capture['url'], 'captured_at': stamp, 'authenticity': 'caller_supplied',
        'network_request_performed': False,
    }
    row.setdefault('warnings', []).append('Imported HTML and capture time are caller supplied; authenticity is not independently verified.')
    return row
