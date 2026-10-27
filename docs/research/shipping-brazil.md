# Fansbuy → Brazil: source-audited findings

Checked 2026-10-27. Live carrier data, current official guidance and shipment-specific unknowns are separate. This research supports an indicative calculator; it does not grant customs clearance.

## Fansbuy public calculator

The user confirmed [fansbuy.com](https://fansbuy.com/). Its [public estimator](https://fansbuy.com/estimates) loaded without login and requested country, category, grams and centimetres. Corporate ownership, competitor quality, procurement percentages and corporate lineage were not established.

The observed first-party [EstimatesView.DX2h0m2j.js](https://fansbuy.com/assets/js/EstimatesView.DX2h0m2j.js) uses these public calls, which also succeeded directly without credentials:

```http
POST https://fansbuy.com/apiv2/web/cart/checkarea
Content-Type: application/json

{"serch":"hot"}
```

The English/Chinese groups identified Brazil as region_id 29, c_code BR. The implementation resolves it dynamically rather than relying on 29 forever.

```http
POST https://fansbuy.com/apiv2/estimatesTest
Content-Type: application/json

{"weight":1000,"volume":6000,"currency":"CNY","price":0,"country":"29"}
```

For a **1,000 g, 20×20×15 cm** test package, this returned **15 route records**, including a disabled HK-UPS record. Fifteen records must not be described as fifteen usable routes. The [public fixture](../../tests/fixtures/fansbuy-estimates-2026-10-27.json) records request, response and capture time without credentials/customer data. With an explicit ordinary-goods assertion, the CLI admitted 14 records at that capture.

| Example route | CNY base total | Advertised days |
|---|---:|---|
| BJ-E-ETK | 168.75 | 10–30 |
| BJ-EUB | 206.58 | 15–30 |
| China Post Sea Mail | 236.39 | 60–180 |

These are observations for that package/time, before tax and unresolved charges, not reusable tariffs or confirmed acceptance/delivery. The CLI uses total_fee without automatically subtracting discount_display: coupon eligibility is unverified. Carrier “tax-free” descriptions do not establish Brazilian tax exemption.

The frontend computes volumetric grams as cm³/divisor × 1,000, compares that with actual grams and has conditional side-length triggers. The API includes weight/side limits, divisors and category flags. These are carrier data, not legislation. Disabled/incompatible/oversize/overweight/ambiguous routes are retained under rejected, with reasons.

Frontend category mapping: Electric→ischarged, Brand→isbrand, liquid→isliquid, bag→isbag, food→isfood, shoes→isshose, Battery→iscell, Knives→istool, powder→ispowder, watch→iswatch, cosmetics→iscosmetics, magnetic→ismagnetism, perfume→isperfume. The source spelling isshose is intentional. Numeric/string 1 means the frontend treats the category as accepted; 0 triggers its incompatibility message. Missing values remain unresolved.

Electric and Battery are distinct Fansbuy flags. Correct classification, packaging, declaration and dangerous-goods compliance require carrier confirmation. [IATA's lithium-battery guidance](https://www.iata.org/en/programs/cargo/dangerous-goods/lithium-batteries/) was retrieved as a primary transport reference. Chemistry, Wh, cell count, standalone/packed/contained configuration, state of charge, carrier and current packing instructions must be checked for the actual item. No universal battery/container requirement is inferred.

## Current tax guidance: May 2026 changes matter

The [Receita Federal taxation manual](https://www.gov.br/receitafederal/pt-br/assuntos/aduana-e-comercio-exterior/manuais/remessas-postal-e-expressa/topicos/tributacao) was retrieved directly on 2026-10-27. Its current text says:

- RTS applies to eligible consignments with customs value **goods + freight + insurance up to USD3,000**, or equivalent, to natural/legal persons. Other regimes exist; this CLI does not calculate commercial container-import costs.
- General federal import duty is **60%** when specific rules do not apply.
- For qualifying purchases on certified PRC sites, destined to a **natural person**, applicable to **DIR registered from 2026-05-12**: **0% through USD50**; above USD50, **60% less USD30 equivalent** from the duty.
- It explicitly identifies **20% below USD50 and a USD20 deduction** as the historic rules for **2024-08-01 through 2026-05-11**.
- ICMS varies **17%–20% according to state**, independently of PRC status. Carrier clearance-service charges may apply; these are private service charges, not federal taxes.

The [PRC explainer](https://www.gov.br/receitafederal/pt-br/assuntos/aduana-e-comercio-exterior/manuais/remessas-postal-e-expressa/programa-remessa-conforme-o-que-e-como-funciona) and [certified-company list](https://www.gov.br/receitafederal/pt-br/assuntos/aduana-e-comercio-exterior/manuais/remessas-postal-e-expressa/empresas-certificadas-no-programa-remessa-conforme-prc) also show the current zero/USD30 structure. No literal fansbuy match was found in the retrieved company-list text. **That alone does not prove corporate non-participation or transaction eligibility.** The CLI defaults to the general 60% assumption; selecting PRC explicitly asserts eligibility and does not verify certification.

The [consolidated CONFAZ Convênio ICMS 81/23](https://www.confaz.fazenda.gov.br/legislacao/convenios/2023/CV081_23), retrieved directly, records the 135/24 amendment effective 2025-04-01 and authorizes a 17% or 20% equivalent burden including applicable state additions. It does not establish each state's current choice. **No state map or default ICMS is hard-coded.** Verify the recipient state's current rule with its SEFAZ and supply it. Current decrees for all 27 units were not verified.

Indicative arithmetic:

```text
assumed customs value = (goods + all supplied freight + insurance) × CNY/BRL
general duty = customs value × 0.60
conditional PRC duty = 0 if value ≤ USD50; otherwise max(0, value × 0.60 − USD30 equivalent)
ICMS = (customs value + duty) × rate / (1 − rate)
estimate = customs value + duty + ICMS + separately supplied buying-agent fee
```

Domestic freight is included in the assumed customs base and USD3,000 check. Buying-agent fees are separate with a valuation warning: actual assessment may differ. Decimal line amounts are rounded and summed. FX/ICMS are user inputs, not official customs rates. Special exemptions, full classification, customs adjustments, payment/FX fees, packing, storage, brokerage, penalties, commercial duties and fixed carrier charges are not inferred. No universal R$15 handling fee is hard-coded.

## Used goods and regulated products

The [Receita restrictions/prohibitions manual](https://www.gov.br/receitafederal/pt-br/assuntos/aduana-e-comercio-exterior/manuais/remessas-postal-e-expressa/topicos/restricoes-proibicoes), retrieved directly, distinguishes prohibitions and restricted procedures. Its list contains the literal phrase **“bens usados ou recondicionados, exceto para uso e consumo pessoal”**, followed by further exceptions. Check the full rule and facts; do not conclude that every secondhand item is always prohibited or every personal-use purchase automatically allowed. NCM, condition, import purpose, modality, trade controls and exceptions require case-specific review. Goofish listings deserve particular condition scrutiny.

The same manual directs readers to administrative-control authorities and carrier restrictions. The CLI returns manual_review with category-specific topics:

- Used/reconditioned goods: Receita/trade controls, exceptions and procedure.
- Wireless/telecom: Anatel applicability/certification; electrical equipment is not necessarily radio equipment.
- Cosmetics, food, medicines: Anvisa and applicable agriculture/environment controls; no blanket consumer-quantity authorization.
- Batteries, liquids, perfume, magnetic contents: carrier and dangerous-goods classification/packing/mode.
- Knives/potentially controlled items: classification, administrative controls and carrier acceptance.

[Anvisa's electronic-smoking-device page](https://www.gov.br/anvisa/pt-br/assuntos/tabaco/cigarro-eletronico), retrieved directly, states that RDC855/2024 maintains the prohibition on sale/import of DEF. The CLI does not implement a complete vape/medicine/controlled-goods classifier. Wildlife, plant/animal materials and other regulated goods need the actual IBAMA/MAPA/Anvisa rules for their NCM/material.

**Sea/container transport does not cure an import prohibition.** No source here establishes that the user's unspecified product must come in a container. Sea-mail price/time data are carrier observations, not evidence of lawful commercial container import.

## Source audit and remaining checks

The initial delegated research was audited against direct first-party retrieval. Unsupported assertions about corporate lineage, competitor quality, fees, universal PRC non-participation, state mappings, fixed handling fees, blanket used-goods bans and obsolete PRC rates were removed. Local retained pages/drafts remain private; [policy-sources.json](policy-sources.json) records selected public excerpts and retained-file hashes.

A real shortlist still needs exact product/condition, lawful import procedure, recipient state/current rate, policy/FX, packed size/weight, full categories, carrier acceptance, Fansbuy charges and any Indonesia→China leg for Blibli. No purchase, payment, shipment submission or customs declaration was made.
