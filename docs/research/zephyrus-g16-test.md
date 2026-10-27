# Zephyrus G16 research: evidence and verification notes

Audit date: 2026-10-27. Scope: retained guest research; no live price or checkout validation. See [bounded Blibli report](zephyrus-g16-blibli.md) for the candidate links and BRL reference estimates.

| Evidence | Observation | Limit |
| --- | --- | --- |
| [Blibli HTTP probes](../../.local/guest-research/blibli/access-probe.json) | Tested endpoints returned HTTP 403. | Does not establish availability, prices, or a universal access policy. |
| [Blibli browser evidence](../../.local/guest-research/blibli/t3-browser-evidence.json) | Browser reached a challenge/verification page. | No product or account flow was verified. |
| [Prepared listing leads](../../.local/guest-research/blibli/discovered-listings.json) | Contains candidate URLs and asserted listing details. | It is a compiled lead file, not a retained first-party product response; unsupported specifications, prices and seller status are not verified. |
| Independent Google observations provided with this task | GU603VV Rp 32,998,960; GU603VI Rp 35,998,960; GU603ZU Rp 25,998,960; GA605WV Rp 48,000,000. | Search-index only, potentially recommendation contamination; exact SKU-to-price binding and current status unverified. Root captures [google-g16.html](../../.local/guest-research/google-g16.html) and [google-web.txt](../../.local/guest-research/google-web.txt) did not independently establish these bindings in this audit. |
| [JD guest detail](../../.local/guest-research/g16-jd-detail.json), [raw page](../../.local/guest-research/guest-1.html) | Item 100214660452 title includes U9 285H, 32G, 1T, RTX5060, 2.5K, 240Hz; raw price is `1??99`. | Price is masked; stock and checkout are unknown. |
| [Goofish browser observations](../../.local/guest-research/china-access/browser-observations.md) | Item 985148706040 observed ¥7,999 and delisted. | Historical guest observation, not an available deal; configuration is a seller claim. |
| [ECB XML](../../.local/guest-research/ecb-fx.xml) | 2026-10-26 reference rates: EUR/BRL 6.2523, EUR/CNY 7.4603, EUR/IDR 20320.32, EUR/USD 1.1188. | Reference conversions exclude all transaction costs and do not validate marketplace amounts. |

The outstanding evidence is an accessible exact product/variant page and checkout, current stock and price, seller and warranty verification, account and payment eligibility, and any applicable delivery or agent quote. Account benefits and Indonesian forwarding support remain unknown. Search-index observations cannot select a winner or establish current deals.

## Integrated CLI checks

The optional guest browser CLI was run across Taobao, JD, Goofish and Blibli with Chinese `华硕 ROG 幻16 Air` for China and the original English query for Blibli. All four Google discovery requests stopped at a verification challenge; there were zero offers, and exit 3 correctly reported partial/unavailable coverage. This is not proof of absent inventory. Private receipt: `.local/guest-research/g16-browser-cli-v3.json`.

A fresh HTTP detail read of JD SKU `100214660452` succeeded without cookies or an account. Its exact title was preserved and the numeric price remained null. Private receipt: `.local/guest-research/g16-jd-detail-v2.json`.

The earlier rendered Google observation has now been retained privately as `.local/guest-research/blibli-root-google-observation.json`. It includes the four rich-result amounts and also shows the GU603VV price repeated in other products' recommendation snippets. It strengthens provenance of the index observation, not current price or checkout verification. A separate quoted search for GA605WV and `38.999.000` found no documents in the inspected Google page; this does not establish a market-wide minimum.

## Hypothetical Fansbuy laptop parcel

A live public calculator request used **3,000g, 45×35×15cm**, destination Brazil and categories **Electric + Brand**. These are scenario inputs, not measured G16 packaging. The returned routes passing the implemented constraints were:

| Route | Freight CNY | ECB reference BRL | Advertised days |
| --- | ---: | ---: | --- |
| China Post Sea Mail 0–20kg | 309.99 | 259.80 | 60–180 |
| JD-EXP-EF E 0–3kg | 530.68 | 444.75 | 7–20 |
| JD-EXP-EF 0–30kg | 570.30 | 477.95 | 7–20 |
| JD-EXP-EF Battery-line 0–7kg | 772.96 | 647.80 | 7–20 |

Seven routes were rejected. Private receipt: `.local/guest-research/g16-parcel-scenario-3kg.json`. Confirm actual packed dimensions, installed battery classification, carrier restrictions, insurance and customs eligibility with Fansbuy before using a route. Category flags alone do not grant acceptance. No evidence establishes that this laptop must travel by container or sea. Sea mail is a service category, not proof of a particular container shipment. A sea route does not cure import restrictions.

No current eligible China purchase price was established, so no current G16 landed total or best-deal winner is claimed. Use explicit goods/freight/FX/ICMS inputs with `estimate` for a scenario. Blibli remains product-only; freight is excluded from all Blibli comparisons.
