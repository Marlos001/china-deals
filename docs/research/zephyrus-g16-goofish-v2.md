# Zephyrus G16 on Goofish: second guest research pass

Inspected **2026-10-27** for the current **china-deals 0.2** report. This pass owns only this note and `.local/access-v2/goofish/`. No code, commits, pushes, account use, purchases, seller contacts, extension installation, security-challenge solving or private API calls were performed.

**The user's correction is valid: one delisted item does not characterize Goofish's G16 inventory.** This broader pass still could not establish a current purchasable G16 offer. It retained one readable G16-family item, four distinct historical Xianyu share links, an unresolved recommendation-only lead, and a confirmed HP false positive. These are evidence classes, not a count of Goofish inventory. Additional listings can exist beyond guest access and this search index.

## Search coverage and access

Used the web search connector and **two agent-owned T3 preview Incognito tabs**, without saved account logins. The [query log](../../.local/access-v2/goofish/query-log.json) records 68 query instances in 17 bounded search calls, including spelling variants, exclusions, crosspost discovery and manufacturer checks. Raw connector results are retained as `search-01.json` through `search-17.json`; supplemental manufacturer evidence is separate. Some calls returned no results, and many returned the same few pages. This is broad query coverage, not exhaustive marketplace coverage.

All requested query families were searched through the connector and attempted as native guest searches:

| Chinese/native query | Observed guest result | Retained evidence |
| --- | --- | --- |
| 华硕 ROG 幻16 Air | Eventually no matching-results message; unrelated “猜你喜欢” carousel. | [native-search-01.json](../../.local/access-v2/goofish/native-search-01.json) |
| 幻16air | Loading state at capture; no bound target result established. | [native-search-02.json](../../.local/access-v2/goofish/native-search-02.json) |
| 幻16 air 2025 5060 | No matching-results message; unrelated recommendations. | [native-search-2025-5060.json](../../.local/access-v2/goofish/native-search-2025-5060.json) |
| 幻16 2023 4060 | No matching-results message; unrelated recommendations. | [native-search-2023-4060.json](../../.local/access-v2/goofish/native-search-2023-4060.json) |
| GU605 | Loading state at capture; no bound target result established. | [native-search-GU605.json](../../.local/access-v2/goofish/native-search-GU605.json) |
| GA605 | No matching-results message; unrelated recommendations. | [native-search-GA605.json](../../.local/access-v2/goofish/native-search-GA605.json) |
| 幻16 4070 4080 | No matching-results message. Connector also searched the GPU terms separately. | [native-search-4070-4080.json](../../.local/access-v2/goofish/native-search-4070-4080.json) |

A shorter native `幻16` query was also attempted; its retained body read was still loading. No native target-results pagination was established. The page's `1/1` indicator, loading states and no-results messages **do not prove absent inventory**. The underlying cause of missing guest results was not established; a visible login invitation alone does not prove that signing in would fix it.

One item navigation returned `Preview automation navigate timed out after 15000ms.`; a subsequent read of that same tab succeeded. No browser-system switch or access-control workaround was needed. The retained browser JSON is DOM text/link evidence, **not a screenshot**.

## Exact URLs and item adjudication

Machine-readable fields, evidence filenames and null prices are retained in [catalogue.json](../../.local/access-v2/goofish/catalogue.json). An exact share URL is retained as found; it is not silently converted into a guessed Goofish item ID.

### G01 — readable G16-family listing, explicitly delisted

[Goofish item 985148706040](https://www.goofish.com/item?categoryId=126854525&id=985148706040)

Exact main-product title: **华硕ROG 幻16Air2024 4060高端U9笔记本**.

The main item displayed **CNY 7,999** and **已下架**. Its model attribute names `Asus ROG 幻 16 Air 2024`. The seller claims Ultra 9 185H, RTX 4060 with 8GB VRAM, 32GB 7467MHz memory, Samsung 1TB PCIe 4.0 SSD with 1,501 hours, and a 15.9-inch 2.5K/240Hz display. The panel technology and exact GU605 suffix are absent from the listing evidence.

Condition claims: personal use, bought April 2024 at JD with purchase record, working, no disassembly/repair, ordinary wear and small visible knocks around the edges, no major knock; original charger included, no other accessories. These claims were not physically checked. The seller's 15.9-inch description should remain literal rather than be silently normalized to the manufacturer's 16-inch family specification.

The free-shipping badge conflicts with the description: CNY 7,999 is stated to be the collection price, local delivery/shipping adds CNY 40, and out-of-town SF shipping is collect. Do not use the badge to infer a zero domestic shipping charge.

Evidence: [fresh item-bound browser capture](../../.local/access-v2/goofish/browser-985148706040.json), [indexed observation](../../.local/access-v2/goofish/search-09.json). **Not an available deal or a price floor for other listings.**

### Historical share links — distinct leads, current details unresolved

| Lead and exact Xianyu share URL | Source-bound claims | Current price / condition / availability |
| --- | --- | --- |
| H01: [Air 4060 grey](https://m.tb.cn/h.g2nAkzj?tk=jAtEWFoDhRR) | [Seller crosspost, 2024-05-19](https://www.v2ex.com/t/1042003), title “出一台 ROG 幻 16Air 4060 灰色”; historical ask CNY 12,000, Xi'an collection preferred. CPU, RAM, SSD and exact SKU missing. | Current price unknown; detailed condition unknown. Share link returned an error page. Plausible G16 Air historical lead, not a current offer. |
| H02: [幻16 4070 version](https://m.tb.cn/h.6f5VjmH?tk=IwO7eCVTPW7) | [Seller crosspost, 2025-04-03](https://www.v2ex.com/t/1123220): 13th-gen i9, 16GB, 1TB, RTX 4070; seller says little use and July 2024 purchase. | No bound current asking price. July 2026 warranty claim is historical and already past. Share error; exact model family unresolved. Comment amounts CNY 7,500/7,300 compare other machines and are **not** this item's validated ask. |
| H03: [2023 幻16 4070 / 32GB / 1TB+2TB](https://m.tb.cn/h.UCz0M4h?tk=KZIWdJcTupO) | [Seller crosspost, 2023-06-13](https://www.v2ex.com/t/948202), described as standard version. CPU, exact SKU and detailed condition missing. | Price unknown; share error; current availability and G16/M16 identity unresolved. “标准版” alone does not settle the family. |
| H04: [2023 幻16 4070](https://m.tb.cn/h.UI7TYxU?tk=fgiIdk793DQ) | [Seller crosspost, 2023-04-04](https://www.v2ex.com/t/929593), seller reports roughly one month of use and objectionable fan noise. | Crosspost explicitly marked sold on 2023-04-08; share error too. Exact family unresolved. Excluded from current leads. |

The four different share URLs must not be counted as four verified G16 item IDs. Each returned `m.tb.cn/scanError.htm` with a generic message listing nonexistent code, expiry or system-busy possibilities. This proves the observed share-link failure, **not** which of those explanations applies and not a definitive current item status. Browser receipts: [H01](../../.local/access-v2/goofish/share-1042003.json), [H02](../../.local/access-v2/goofish/share-1123220.json), [H03](../../.local/access-v2/goofish/share-948202.json), [H04](../../.local/access-v2/goofish/share-929593.json). Crosspost bodies: [H01](../../.local/access-v2/goofish/cached-page-and-v2ex.json), [H02–H04](../../.local/access-v2/goofish/historical-crosspost-pages.json).

### Recommendation contamination — do not promote these prices

[Goofish item 1042739963304](https://www.goofish.com/item?categoryId=126854525&id=1042739963304) repeatedly appeared in searches for 幻16. Its actual main title is **暗影精灵10 i7 14650hx 4070 16 1tb**, with **CNY 5,999** displayed: an **HP Omen**, not a Zephyrus G16. Its main attributes even contain an inconsistent HP model label; none support a G16 identity. Chat and buy controls appeared, but checkout and actual availability were not tested. [Fresh main-item capture](../../.local/access-v2/goofish/browser-1042739963304.json).

The cached result contains a separate recommendation reading `华硕rog幻16 i9 13900hx 4060 16 1t` at **CNY 6,299**. That recommended product's own exact URL was not recovered. The HP carrier URL cannot be assigned to it. Its CPU wording also needs checking against the intended model. **CNY 6,299 is unbound discovery text, not a validated G16 price.** [Indexed evidence](../../.local/access-v2/goofish/search-09.json).

Similarly, [V2EX 1018739](https://www.v2ex.com/t/1018739) mentions waiting for a 幻16 Air but actually sells a Lenovo Xiaoxin Pro16. Its Lenovo share link and price were excluded. A [Telegram index result](https://t.me/s/SecHorse/139444?q=%23rog) separately describes a sold AMD HX370/4060 Air; surrounding mouse/other-product share links were not attached to that laptop. [Discovery receipts](../../.local/access-v2/goofish/search-15.json). These examples explain why matching page text is insufficient.

## Model identity and hardware-aware research priorities

Manufacturer pages establish family context; they do not fill missing seller fields or validate the hardware in a particular secondhand machine.

| Chinese label / code | Manufacturer mapping | Use in this research |
| --- | --- | --- |
| 幻16 2023, **GU603** | [Zephyrus G16 2023](https://rog.asus.com.cn/laptops/rog-zephyrus/rog-zephyrus-g16-2023-series/spec/) | Valid older G16 search family. Retrieved CN GU603VV configurations specify i9-13900H, RTX 4060 8GB, 120W including Dynamic Boost, 2560×1600/240Hz and DDR4 memory. Do not assume every listing has that exact configuration. |
| 幻16 Air 2024, **GU605** | [Zephyrus G16 2024](https://rog.asus.com.cn/laptops/rog-zephyrus/rog-zephyrus-g16-2024/spec/) | Retrieved CN MV/MI variants distinguish 4060/4070, OLED/240Hz and soldered memory. A used 32GB example is worth verifying if that capacity and lighter chassis are priorities; G01 itself is delisted. |
| 幻16 Air 2025, **GU605** | [Intel Zephyrus G16 2025](https://rog.asus.com.cn/laptops/rog-zephyrus/rog-zephyrus-g16-2025-gu605/spec/) | Search GU605CM / Ultra 9 285H / RTX 5060, preserving exact suffix and RAM. Indexed ASUS specs identify the 5060 and soldered 32GB; direct connector opening timed out, so that particular retrieval is index evidence. No Goofish item-bound current offer was established. |
| 幻16 Air 2025, **GA605** | [AMD Zephyrus G16 2025](https://rog.asus.com.cn/laptops/rog-zephyrus/rog-zephyrus-g16-2025-ga605/spec/) | Retrieved GA605KM350 variants specify Ryzen AI 7 350, RTX 5060 **8GB GDDR7**, 105W including Dynamic Boost, soldered 32GB, and OLED/240Hz. Verify generation: GA605 alone is not a complete SKU. |
| 幻16 星空版/经典版, **GU604** | [Zephyrus M16 2023](https://rog.asus.com.cn/laptops/rog-zephyrus/rog-zephyrus-m16-2023-series/spec/) | Exclude from a strict G16 shortlist or compare separately with an explicit M16 label. CN page includes 4070, 4080/12GB and 4090/16GB. |
| 幻16 翻转, **GV601** | [Flow X16 2023](https://rog.asus.com.cn/laptops/rog-flow/rog-flow-x16-2023-series/spec/) | Different convertible family; exclude from strict G16 shortlist. |
| 枪神 / 魔霸 / 魔霸新锐, **G614** | [Strix G16](https://rog.asus.com.cn/laptops/rog-strix/rog-strix-g16-2025-g614/spec/) | “G16” in this family is Strix, not Zephyrus. Exclude or label separately. |

Manufacturer receipts: [GU603 and GA605 pages](../../.local/access-v2/goofish/hardware-pages.json), [GU604/GV601/GU605 pages](../../.local/access-v2/goofish/hardware-pages-2.json), [name mapping searches](../../.local/access-v2/goofish/search-13.json), [2025/Strix context](../../.local/access-v2/goofish/hardware-search.json).

Conditional follow-up priorities:

- **Lower acquisition cost:** verify a genuine GU603 2023/4060 listing alongside used GU605 2024/4060 listings. Compare actual memory arrangement, total RAM, SSD, display technology, repairs and asking price. No current prices for those alternatives were established here.
- **OLED and portability:** prioritize exact GU605/GA605 Air listings, checking panel wear/burn-in, battery condition, charger, serial/model proof and soldered RAM capacity. These are verification criteria, not conditions observed on the unresolved leads.
- **Newer platform / RTX 5060:** compare GU605CM/285H and GA605KM/AI 7 350 as different CPU/platform candidates. A newer GPU number alone does not prove better value; the AMD 5060 configuration still has 8GB VRAM.
- **More VRAM:** seek an exact GU605 RTX 4080/12GB item if the workload needs it. [ASUS's GU605 specification](https://rog.asus.com/us/laptops/rog-zephyrus/rog-zephyrus-g16-2024/spec/) identifies 4080/12GB versus 4070/8GB; the 4080's specified power is 115W including Dynamic Boost in that family. This is manufacturer context, not a found Goofish offer. Do not accidentally substitute a GU604 M16 or Strix 4080. [Retained index context](../../.local/access-v2/goofish/hardware-gpu-context.json).

No performance-per-real ranking or universal winner is supported. The missing item-bound TGP, panel details, condition and current price prevent complete comparison groups.

## BRL reference amounts for the 0.2 report

Use the existing local [ECB snapshot](../../.local/guest-research/ecb-fx-snapshot.json), **rate date 2026-10-26**, not an invented current payment rate:

- CNY 1 = **BRL 0.838076216774**.
- USD 1 = **BRL 5.588398283876**.
- The [retained ECB XML](../../.local/guest-research/ecb-fx.xml) records EUR 1 = CNY 7.4603 and BRL 6.2523. Formula: CNY × 6.2523 ÷ 7.4603, rounded to BRL cents.

G01's delisted **CNY 7,999 = BRL 6,703.77** as a goods-only reference. H01's **2024 historical** ask CNY 12,000 would convert to BRL 10,056.91 at the same 2026 reference rate; that does not make it a current offer or a contemporaneous 2024 conversion.

The recommendation-only CNY 6,299 stays unpriced/unranked in the candidate catalogue; there is no eligible item-bound offer to compare with G01. Conversions exclude domestic shipping, international freight, payment/FX spread, IOF, insurance, agent charges, customs duties and ICMS. No landed total is calculated. ICMS remains an explicit destination-state input under the existing [Brazil research](shipping-brazil.md); 0.2 is the CLI version, not an assumed tax rate.

Snapshot SHA-256: `bed1708bf4a7f800bb2c9fd11eccec79e7a153dc88a2d59e9d554c95c4121f9a`. XML SHA-256: `d9a9303535c3084d4526af8934821c61f086333fd1c9d5889ca290bac4ec97a9`.

## Handoff and remaining evidence

This pass found **one readable G16-family main item ID, explicitly delisted; four historical share URLs; zero newly verified currently available G16 offers**. That describes this pass only. It does not refute the user's observation of more listings.

The remaining work is to obtain fresh exact item URLs for the GU603/4060, GU605 Air 2024, GU605CM/5060, GA605KM/5060 and GU605/4080 candidates; recover the recommended CNY 6,299 item's own URL; and validate each main item's title, complete description, exact SKU, price basis, condition, availability and seller/transaction terms. H02/H03 additionally need G16-versus-M16 identity. Without that evidence, retain them as unresolved rather than recycling old amounts into current offers.

Private captures are ignored by Git under `.local/` and must accompany a local handoff if their full provenance is needed. [Catalogue](../../.local/access-v2/goofish/catalogue.json) and [query log](../../.local/access-v2/goofish/query-log.json) are the entry points. No external work is running.
