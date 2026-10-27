"""Offline parsing of bounded, identity-bound Goofish public main-item DOM.

These are source claims, never checkout, authenticity, or selected-SKU proof.
The fixed browser expression reads DOM only; this module performs no I/O.
"""

import re
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit

from .models import parse_price, safe_url

_MAX_HTML_BYTES = 64 * 1024
CAPTURE_JS = r"""() => {
  const mains = document.querySelectorAll('[class^="item-main-container--"]');
  const main = mains.length === 1 ? mains[0] : null;
  const infos = main ? main.querySelectorAll('[class^="item-main-info--"]') : [];
  const info = infos.length === 1 ? infos[0] : null;
  const count = selector => info ? info.querySelectorAll(selector).length : 0;
  const html = main ? main.outerHTML : '';
  const bytes = new TextEncoder().encode(html).length;
  return {url: location.href, title: document.title.slice(0, 4096),
    capturedAt: new Date().toISOString(),
    mainHtml: bytes <= 65536 ? html : '', mainHtmlBytes: bytes,
    mainHtmlTruncated: bytes > 65536,
    cardinalities: {main: mains.length, info: infos.length,
      price: count('[class^="price--"]'),
      description: count('[class^="notLoginContainer--"] [class^="main--"]'),
      labels: count('[class^="notLoginContainer--"] [class^="labels--"]')}};
}"""

_VOID = {'img', 'br', 'input', 'hr', 'meta', 'link', 'source', 'area', 'wbr', 'embed',
         'param', 'track', 'col', 'base'}


class _Node:
    def __init__(self, tag='', attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []

    def text(self):
        pieces, todo = [], [self]
        while todo:
            node = todo.pop()
            if isinstance(node, str):
                pieces.append(node)
            elif node.tag not in {'script', 'style', 'template'}:
                todo.extend(reversed(node.children))
        return ' '.join(pieces).strip()

    def find(self, prefix):
        found, todo = [], [self]
        while todo:
            node = todo.pop()
            # Match the observed CSS [class^=...] contract exactly.
            if (node.attrs.get('class') or '').startswith(prefix):
                found.append(node)
            if node.tag not in {'script', 'style', 'template'}:
                todo.extend(c for c in reversed(node.children) if isinstance(c, _Node))
        return found


class _Parser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _Node()
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = _Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in _VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(_Node(tag, attrs))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                self.stack = self.stack[:index]
                break

    def handle_data(self, value):
        if value.strip():
            self.stack[-1].children.append(value.strip())


def _item_id(url):
    if not safe_url(url, 'goofish'):
        raise ValueError('Expected an HTTPS Goofish item URL')
    parts = urlsplit(url)
    ids = parse_qs(parts.query, keep_blank_values=True).get('id', [])
    if (parts.hostname not in {'www.goofish.com', 'goofish.com'} or parts.path != '/item'
            or len(ids) != 1 or not re.fullmatch(r'[0-9]+', ids[0])):
        raise ValueError('Expected one numeric Goofish item id')
    return ids[0]


def _capacities(text):
    return {str(int(n)) + unit[0].upper() for n, unit in re.findall(
        r'(?<![\d.])(\d+)\s*(TB?|GB?)(?![A-Za-z])', text, re.I)
            if not (unit.upper() == 'G' and int(n) in {2, 3, 4, 5, 6})}


def _models(text):
    return {re.sub(r'\s+', '', match).lower() for match in re.findall(
        r'(?:iPhone\s*)?(\d{2}\s*Pro(?:\s*Max)?)(?![A-Za-z])', text, re.I)}


def _condition_claims(sources):
    """Bind literal conditions within clauses; repair evidence is independent."""
    evidence = []
    pattern = (r'几乎全新|近乎全新|轻微使用痕迹|使用痕迹|\d{1,2}(?:成)?新|'
               r'二手|磕碰|划痕|全新')
    component = r'(?:屏幕|外屏|内屏|电池|手机壳|保护壳|耳垫|充电器|数据线)'
    repair_pattern = (r'(?:换过|更换过?|换了|换上|维修过?|替换)(?:了|过|的)?'
                      r'\s*(?:全新|新|原装)?\s*' + component + r'|'
                      + component + r'(?:有|经过)?维修')
    main_device = any(_models(text) for _, text in sources)
    for source, text in sources:
        for clause in re.split(r'[，,。；;！!？?\n]+', text):
            repair_spans = []
            for match in re.finditer(repair_pattern, clause):
                if re.search(r'(?:无|没有|未|未经|没)\s*$', clause[:match.start()]):
                    continue
                repair_spans.append((match.start(), match.end()))
                evidence.append({'source': source, 'source_excerpt': match.group(),
                                 'scope': 'main_product', 'repair_or_replacement_claim': True,
                                 'condition': None})
            for match in re.finditer(pattern, clause):
                if re.search(r'(?:无|没有|非|不是|并非|不售卖|不卖)\s*$', clause[:match.start()]):
                    continue
                prefix = clause[max(0, match.start() - 16):match.start()]
                suffix = clause[match.end():match.end() + 16]
                replacement = any(start <= match.start() and end >= match.start() - 16
                                  for start, end in repair_spans)
                gift = bool(re.search(r'赠送|附赠|赠品|附送', prefix))
                subject_prefix = re.sub(r'(?:无|没有|未|未经|没)\s*(?:' + repair_pattern + ')', '', prefix)
                component_subject = bool(re.search(component + r'\s*(?:是|为|的)?\s*$', subject_prefix)
                                         or re.match(r'\s*(?:(?:的|原装|一个|新的)\s*){0,2}' + component, suffix))
                off_main = source != 'attribute_rows' and (
                    replacement or gift or main_device and component_subject)
                evidence.append({'source': source,
                                 'source_excerpt': (prefix + match.group() + suffix) if off_main else match.group(),
                                 'scope': 'component_or_gift' if off_main else 'main_product',
                                 'repair_or_replacement_claim': replacement,
                                 'condition': None if off_main else 'new' if match.group() == '全新' else 'used'})
    states = {claim['condition'] for claim in evidence if claim['condition'] is not None}
    if 'new' in states and any(claim.get('repair_or_replacement_claim') for claim in evidence):
        return 'unknown', 'main_condition_with_repair_claim', evidence
    reason = ('conflicting_source_claims' if len(states) > 1 else
              'explicit_source_claim' if states else 'only_component_or_gift_claims' if evidence else 'no_explicit_source_claim')
    return (next(iter(states)) if len(states) == 1 else 'unknown'), reason, evidence


def _price_basis_claims(sources):
    evidence = []
    for source, text in sources:
        for match in re.finditer(r'标价[^。\n，,！!；;]{0,80}|价格仅供参考[^。\n！!；;]{0,80}', text):
            if re.search(r'预售|裸机|仅供参考', match.group()):
                evidence.append({'source': source, 'source_excerpt': match.group(),
                                 'reason': 'qualified_base_or_reference_price'})
    return evidence


def parse_capture(capture, requested_url):
    """Return one raw offer; reject wrong identity or incomplete primary DOM.

    Accepts the capture value (not an MCP response envelope). Historical retained
    captures may omit cardinalities; in that case the DOM is counted locally.
    """
    if not isinstance(capture, dict):
        raise ValueError('Capture must be an object')
    item_id = _item_id(requested_url)
    if _item_id(capture.get('url')) != item_id:
        raise ValueError('Requested and captured Goofish item IDs differ')
    stamp = capture.get('capturedAt')
    try:
        parsed_time = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
        if parsed_time.tzinfo is None:
            raise ValueError
    except (ValueError, TypeError, AttributeError):
        raise ValueError('Capture requires a timezone-aware capturedAt') from None
    html = capture.get('mainHtml')
    if (not isinstance(html, str) or not html or len(html.encode('utf-8')) > _MAX_HTML_BYTES
            or capture.get('mainHtmlTruncated')):
        raise ValueError('Main DOM is missing, truncated, or exceeds 64 KiB')
    parser = _Parser()
    parser.feed(html)
    parser.close()
    mains = parser.root.find('item-main-container--')
    if len(mains) != 1 or len(parser.stack) != 1:
        raise ValueError('Expected one complete main item container')
    infos = mains[0].find('item-main-info--')
    if len(infos) != 1:
        raise ValueError('Expected one main item info region')
    info = infos[0]
    containers = info.find('notLoginContainer--')
    descriptions = [n for c in containers for n in c.find('main--')]
    labels = [n for c in containers for n in c.find('labels--')]
    prices = info.find('price--')
    actual = {'main': 1, 'info': 1, 'price': len(prices),
              'description': len(descriptions), 'labels': len(labels)}
    counts = capture.get('cardinalities')
    if counts is not None and (not isinstance(counts, dict) or any(
            type(counts.get(k)) is not int or counts[k] != v for k, v in actual.items())):
        raise ValueError('Capture cardinalities disagree with primary DOM')
    if len(containers) != 1 or len(descriptions) != 1 or len(labels) != 1:
        raise ValueError('Primary description/attributes structure is ambiguous')
    description = descriptions[0].text()
    if not description:
        raise ValueError('Primary product description is empty')
    title = capture.get('title')
    if not isinstance(title, str) or not title.strip():
        title = description.split('  ')[0]
    attributes, attribute_rows = {}, []
    duplicate_attributes = False
    for node in labels[0].children:
        if not isinstance(node, _Node):
            continue
        literal = node.text()
        parts = re.split('[：:]', literal, maxsplit=1)
        if len(parts) == 2:
            key, value = ''.join(parts[0].split()), parts[1].strip()
            duplicate_attributes |= key in attributes and attributes[key] != value
            attributes[key] = value
            attribute_rows.append({'label': key, 'value': value, 'raw': literal})
    storage = attributes.get('存储容量', '')
    # These are untyped literal quantities, not RAM/SSD/VRAM specifications.
    # In particular, 内存容量 on a console does not establish the hardware role.
    capacity_claims = [
        {'source': 'attribute_rows', 'label': row['label'], 'value': row['value'],
         'source_excerpt': row['raw'], 'interpretation': 'unresolved'}
        for row in attribute_rows if '容量' in row['label'] and _capacities(row['value'])]
    capacities = _capacities(title + '\n' + description + '\n' + '\n'.join(
        claim['value'] for claim in capacity_claims))
    models = _models(title + '\n' + description + '\n' + attributes.get('型号', ''))
    mixed = len(capacities) > 1 or len(models) > 1 or duplicate_attributes
    consistent = (not mixed and len(capacities) == 1 and bool(_capacities(storage))
                  and bool(_capacities(description)) and len(models) == 1)
    binding = 'mixed_or_conflicting_variants' if mixed else (
        'single_listing_consistent' if consistent else 'unknown')
    price_texts = [n.text() for n in prices]
    price_text = price_texts[0] if len(price_texts) == 1 else None
    amount = parse_price(price_text, 'CNY')
    # Financing availability alone is not a deposit or monthly-price claim.
    partial = bool(re.search(r'定金|订金|首付|月供|每月|deposit|per month',
                             title + '\n' + description, re.I))
    source_texts = [('title', title), ('description', description)]
    price_basis_evidence = _price_basis_claims(source_texts)
    priced = consistent and amount is not None and not partial and not price_basis_evidence
    shipping = [n.text() for n in info.find('post--')]
    purchase = [n.text() for n in info.find('buy--')]
    main_text = info.text()
    availability = 'source_claimed_available' if any('立即购买' in x for x in purchase) else 'unknown'
    availability_claims = []
    for pattern, state in [(r'已售出|已卖出|卖掉了', 'sold'), (r'已下架|已删除|商品不存在', 'delisted'),
                           (r'已售罄|无货|缺货', 'unavailable')]:
        claims = re.findall(pattern, main_text)
        if claims:
            availability_claims = claims
            availability = state
            priced = False
            break
    pickup_only = bool(re.search(r'仅[^。\n]{0,30}自提|只[^。\n]{0,20}自提|不邮寄|不发货', description))
    wholesale = '批发' in description
    condition_sources = source_texts + [
        ('attribute_rows', row['raw']) for row in attribute_rows
        if row['label'] in {'成色', '拆修和功能', '功能状态'}]
    condition, condition_reason, condition_evidence = _condition_claims(condition_sources)
    warnings = ['Public listing claims only; selected SKU, stock quantity and checkout are unverified.',
                'Fulfillment destination, shipping charges and eligibility remain unresolved.',
                'Used-device imports require condition and import-rule review; no legal clearance is established.']
    if mixed:
        warnings.append('Mixed/conflicting model or capacity evidence; displayed amount cannot price an exact configuration.')
    if price_basis_evidence:
        warnings.append('Wrong price basis: qualified base/presale unit or reference quote; not an exact full-product price.')
    if condition_reason == 'conflicting_source_claims':
        warnings.append('Conflicting condition source claims; normalized condition remains unknown.')
    if any(claim['label'] == '内存容量' for claim in capacity_claims):
        warnings.append('Literal 内存容量 retained without assigning RAM or storage hardware semantics.')
    if not priced:
        warnings.append('Exact full-price binding is unresolved; retain the literal main price as evidence only.')
    if pickup_only:
        warnings.append('Seller restricts fulfillment to pickup; generic shipping badges do not establish shipping.')
    if pickup_only and any('包邮' in s for s in shipping):
        warnings.append('Pickup-only description conflicts with the generic free-shipping badge.')
    if wholesale:
        warnings.append('Wholesale price qualifier retained; minimum quantity and eligibility are unknown.')
    detail = {'capture': dict(capture), 'requested_url': requested_url, 'attributes': attributes,
              'attribute_rows': attribute_rows, 'description': description, 'price_text': price_text,
              'price_texts': price_texts, 'shipping_badges': shipping, 'purchase_controls': purchase,
              'cardinalities': actual, 'configuration_binding': binding, 'selected_sku_id': None,
              'availability_evidence': ('public_listing_with_purchase_control'
                                      if availability == 'source_claimed_available' else availability),
              'availability_claims': availability_claims,
              'stock_quantity': None, 'checkout_verified': False,
              'pickup_only': pickup_only, 'wholesale_qualifier': wholesale,
              'repair_claim': attributes.get('拆修和功能'), 'condition_claim': attributes.get('成色'),
              'condition_basis': 'source_claim_only', 'condition_reason': condition_reason,
              'condition_evidence': condition_evidence,
              'partial_price_claim': partial, 'price_basis_evidence': price_basis_evidence,
              'capacity_claims': capacity_claims, 'capacity_evidence_kind': 'untyped_literal_tokens',
              'capacity_evidence': sorted(capacities), 'model_evidence': sorted(models),
              'variant_basis': 'literal_listing_attributes; selected SKU remains unknown'}
    if not priced and price_text is not None:
        detail['price_observation'] = {'amount': price_text, 'currency': 'CNY', 'source_url': capture['url'],
                                       'price_basis': 'unresolved_primary_display', 'configuration_binding': binding,
                                       'observed_at': stamp, 'crawl_age': None, 'checkout_verified': False}
    return {'item_id': item_id, 'url': capture['url'], 'title': title, 'description': description,
            'variant': '; '.join(attributes[key] for key in ('型号', '存储容量', '版本') if attributes.get(key)),
            'currency': 'CNY', 'price': amount if priced else None,
            'price_basis': 'displayed' if priced else (
                'wrong_basis' if price_basis_evidence else 'configuration_unresolved'),
            'source_mode': 'guest_product_page', 'observed_at': stamp,
            'source_detail': detail, 'attributes': attributes,
            'configuration_binding': binding, 'selected_sku_id': None,
            'availability': availability, 'availability_evidence': detail['availability_evidence'],
            'stock_quantity': None, 'checkout_verified': False,
            'condition': condition, 'domestic_free_shipping': None,
            'source_warnings': warnings}
