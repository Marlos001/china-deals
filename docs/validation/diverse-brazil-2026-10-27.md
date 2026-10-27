# Diverse Brazil retail references — 27 October 2026

**Result:** fresh primary pages display Sony WH-1000XM6 Platinum Silver at **R$2,609.10 Pix/boleto** and Ryzen 7 9800X3D at **R$2,199.99 Pix**. The exact DJI Mini 4 Pro Standard with RC 2 displays **R$8,350.50 Pix but is sold out**. These are bounded retail references, not verified savings or a cheapest-store survey. **Strict foreign/Brazil equivalence remains unknown for all three because the foreign condition is missing**, with additional package/availability limitations below.

Only this report and `.local/diverse-search/brazil/` were written. Existing peer application, test and report changes were preserved. No application/tests/commits, login, cart, purchases, messages or tax/legal research.

## Sources, freshness and budget

Used **7 connector queries in 4 calls**, **0 connector merchant opens**, and **4 primary merchant navigations** in a separately owned T3 incognito tab. Initial browser status was unavailable; opening the new incognito tab succeeded. The tab was closed and final status showed no active tab. No human/peer tab was operated. No challenge was encountered on these four pages; previously recorded Blibli/DuckDuckGo/Google/Magalu restrictions were not retried or bypassed.

Fresh captures mean the actual merchant pages were read in this run, **17:53:55–17:54:47 UTC (14:53:55–14:54:47 Brazil/East)**. They establish displayed source claims, not physical inventory or final checkout. Private captures contain DOM text and embedded structured data, **not screenshots or retained raw HTTP response bodies**. Search-index crawl ages remain separate: KaBuM CPU last week; Detona Sony two weeks ago; Drones 2U last month; Pichau CPU three weeks ago. None of those indexed prices was promoted to a fresh price.

Full tool receipts, capture timestamps, exact query strings, source bindings, SHA-256 manifest and calculation records are private in [the evidence folder](../../.local/diverse-search/brazil/). The manifest hashes retained artifact bytes; it does not claim to hash the server's original HTTP response. [Blibli's existing report](diverse-blibli-2026-10-27.md) and its retained source bodies were reused offline, with the three relevant body hashes verified; no foreign page was fetched again.

## Fresh Brazilian observations

All amounts here are BRL, for the whole product. Quoted monthly installments are multiplied separately; their rounding differences are retained. Coupons, cashback and banner discounts are not deducted again.

| Product / primary merchant | Full payment conditions | Exact configuration and condition | Availability, seller and delivery limitations |
| --- | --- | --- | --- |
| **Sony WH-1000XM6 Platinum Silver**, [Detona Shop][sony], SKU `SOWH1000XM6S`; 17:54:18.752Z | **R$2,609.10 Pix/boleto**. Displayed regular total **R$2,899.00**; 12 × R$241.58 = **R$2,898.96**, four cents below listed total. Also lists 1 × R$2,899.00 without interest. | Exact model/color literal in title and included items. Includes one headphone, audio cable, USB charging cable and compact carrying case. Three-month guarantee advertised. **New/used/sealed condition not explicitly established** in retained product text/schema; ordinary retail presentation is not condition proof. | Merchant Detona Shop; footer names Detona Shop Eletro Eletrônicos Ltda ME. Schema claims `InStock`; visible availability says **04–08 business days**. Quantity and immediate dispatch unknown. CEP not entered: delivery price/date unknown. Seller authenticity/authorization not audited. |
| **AMD Ryzen 7 9800X3D**, [Pichau][pichau], SKU/MPN `100-100001084WOF`; 17:54:47.941Z | **R$2,199.99 Pix**, already includes stated 15% reduction. Listed card total **R$2,588.22**; 12 × R$215.69 = **R$2,588.28**, six cents above listed total. Crossed-out R$4,352.93 is not the payable total. | 8 cores/16 threads, AM5, 4.7/5.2 GHz; thermal solution not included. Schema explicitly claims **NewCondition**. Exact WOF part number matches KaBuM's boxed reference below; Pichau capture does not independently say “Box” or confirm sealed package contents. Foreign report has “Box” but no full MPN binding. | Schema seller **Pichau**, `InStock`; visible page also contains **“Error! undefined”**, so checkout/operational availability remains unverified. Quantity unknown. Banner offers free shipping to South/Southeast, but destination eligibility, delivery fee/date unverified. `PRUMO5OFF` and “15% Desconto em Até 6x” banner not applied or treated as verified additional eligibility. |
| **AMD Ryzen 7 9800X3D boxed corroboration**, [KaBuM][kabum], product `662405`, MPN `100-100001084WOF`; 17:53:55.932Z | Main visible text shows **10 × R$265.55 = R$2,655.50**, plus “à vista no PIX” and “-10%”, **but the full Pix number is absent from the retained visible text**. Schema has **R$2,389.99**, with no payment-method field: retain as fresh structured amount, **not a verified full Pix quote**. R$3,333.32 is a reference amount, not accepted current full payment. | Explicit **“Processador em caixa”**, one Ryzen 7 9800X3D, no thermal solution. Three-year guarantee claim. New/used/sealed condition not explicitly established. Model/package corroboration only; do not transfer this merchant's stock/payment/condition claims to Pichau. | **Sold and delivered by KaBuM!**; schema `InStock`, buy/cart controls present. Quantity unknown. CEP not supplied: delivery fee/date unknown. NuPay up to 36 installments has no verified total/eligibility. `FARMOU` 11% coupon not applied. |
| **DJI Mini 4 Pro Standard with DJI RC 2**, [Drones 2U][dji], `DJI042`; 17:54:33.819Z | Displayed **R$8,350.50 Pix**; **R$8,790.00** regular/card total, 12 × R$732.50 = **R$8,790.00**. Pix already includes 5% discount. **Unavailable price reference; exclude from available-offer comparison.** | Explicit Standard package: drone, **one battery**, **RC 2 with screen**, propeller holder, gimbal protector, three pairs of propellers (two already installed), removal tool, six screws, USB-C cable. **Not Fly More**; no hub/extra batteries/bag in the listed package. Color and new/used/sealed condition not explicitly established. | Seller **Drones 2U / SCS Tech Soluções Aéreas com Drones Ltda**. Visible **ESGOTADO**, schema `OutOfStock`, inventory **0**. A separate notice says transfer to Porto Alegre stock within six business days; this does not override sold-out state. Free-shipping banner has no checked destination/date. Actual fee/eligibility unknown. |

Source claims of guarantees, retailer status and stock have not been independently audited. No related-product amount was substituted for the requested product. In particular, Sony's wrong-color KaBuM discovery result and international Magalu bundles were not accepted, and DJI Fly More/RC-N2 alternatives were not substituted.

## Foreign product-only BRL arithmetic

The [existing ECB reference snapshot](../../examples/fx-reference-2026-10-27.json) has rate date **2026-10-27**, retrieved **16:33:29.916065 UTC**, with **1 IDR = R$0.000294810166**. It is a reference rate, **not card FX, a payment-provider quote or customs PTAX**. Decimal calculations use its full stored precision and round final results to cents.

| Foreign primary product | Existing fresh offered amount | Product-only BRL reference | Conditional Brazil minus foreign product gap |
| --- | ---: | ---: | --- |
| [Sony Platinum Silver, Sony Electronics][blibli-sony] | Rp6,179,000 | **R$1,821.63** | Detona Pix R$2,609.10 − foreign reference = **+R$787.47**. Conditional nominal gap only. |
| [Ryzen 7 9800X3D Box, Foursquare Computer][blibli-ryzen] | Rp8,905,000 | **R$2,625.28** | Pichau Pix R$2,199.99 − foreign reference = **−R$425.29**: foreign product reference is already R$425.29 higher, subject to unresolved equivalence. |
| [DJI Mini 4 Pro with RC 2, FUJISHOPid Sedayu][blibli-dji] | Rp12,266,000 | **R$3,616.14** | **No available Brazilian comparison established.** Do not turn the sold-out R$8,350.50 display into a buying threshold or savings claim. |

Foreign body capture times were **17:37:53.609726**, **17:37:55.178472**, and **17:37:57.883567 UTC**, respectively. These are the original same-day observations, not newly refreshed by this report. Offered amounts are whole-item source fields, not the smaller installment `startFrom` fields. Source payment eligibility and final payable totals remain unknown. All three foreign selected options were source-claimed available; this does not verify present physical stock.

**Strict match remains unknown:** all foreign conditions are missing; Sony's full foreign package contents are unresolved; Ryzen's full foreign MPN/seal is unresolved; DJI's foreign detailed package does not independently prove standard one-battery contents even though RC 2 is explicit and Fly More is not established. Brazilian regional warranty/package claims must not silently become foreign claims.

Blibli freight policy is excluded because the user handles transport. This does **not** establish free transport or zero taxes. Import charges, payment/FX spread, IOF where applicable, fees, transport costs and Brazilian destination delivery costs remain unknown inputs. No legal/tax rate was researched or assumed. Consequently **landed total and verified savings are unknown; no verified winner**.

## Handoff and validation

The actionable retained comparison is Sony's conditional R$787.47 nominal product gap, while the Ryzen foreign product reference exceeds the observed Brazilian Pix price by R$425.29. DJI remains an exact-package sold-out Brazilian reference. A purchase decision still needs matching condition/package evidence and complete applicable costs; this report does not request or perform a checkout.

Private validation verifies the three original Blibli body hashes, the frozen FX input, retained JSON parsing, arithmetic, report-relative links and owned evidence hashes. No application tests were run for this documentation-only task. Search and merchant budgets were not exceeded. No browser operation or background process remains.

[sony]: https://www.detonashop.com.br/fone-de-ouvido-sony-wh-1000xm6-platinum-silver.html
[pichau]: https://www.pichau.com.br/processador-amd-ryzen-7-9800x3d-8-core-16-threads-4-7ghz-5-2ghz-turbo-cache-104mb-am5-100-100001084wof
[kabum]: https://www.kabum.com.br/produto/662405/processador-amd-ryzen-7-9800x3d-4-7ghz-5-2ghz-max-turbo-cache-104mb-8-nucleos-16-threads-am5-com-video-integrado-100-100001084wof
[dji]: https://drones2u.com.br/produtos/drone-dji-mini-4-pro-standard-com-tela-br-dji042/
[blibli-sony]: https://www.blibli.com/p/sony-wh-1000xm6-noise-cancelling-headphones-1000xm6/is--SOA-60059-00376-00003
[blibli-ryzen]: https://www.blibli.com/p/amd-ryzen-7-9800x3d-box-processor-8-core-16-thread-up-to-4-7-ghz-garansi-resmi/ps--FOC-70056-02589
[blibli-dji]: https://www.blibli.com/p/dji-mini-4-pro-dji-rc-2-drone-garansi-resmi/ps--FUS-60039-01703
