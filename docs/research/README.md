# Research index and final selection

Source review and live checks: 2026-10-27. The user means **Blibli Indonesia** and **fansbuy.com**. No AI API is required by the selected architecture.

- [Framework comparison](frameworks.md): nine source pins, Agent-Reach/OpenCLI internals, browser-use, Stagehand, Crawl4AI, Firecrawl and Scrapling; licenses, sessions, cost/dependency boundaries and actual output contracts. **Selected: OpenCLI 2.0.2 as an external dependency**, not an Agent-Reach fork. Its deterministic adapters cover Taobao/JD/Xianyu; the project adds comparison/provenance, Blibli access and Brazil cost logic.
- [Marketplace alternatives](marketplaces.md): Goofish CLIs/MCPs and official-affiliate API candidates. Official APIs may require business credentials and approved methods and may expose affiliate pools rather than full inventory. Unlicensed repositories are not copying candidates. Mock fallbacks are not live marketplace evidence.
- [Blibli and adapter verification](blibli.md): source/package command contracts, exact npm version, boundary tests and actual 403 response. Browser fallback is available but product extraction remains unverified. Blibli is IDR/Indonesia and has no established Fansbuy forwarding leg.
- [Fansbuy and Brazil](shipping-brazil.md): root-audited public calculator requests, real route capture, current Receita/CONFAZ policy and remaining product/legal uncertainty. The original delegated tax draft was corrected against direct primary sources, including the May 2026 PRC changes.
- [Policy-source evidence](policy-sources.json): selected public excerpts, retrieval date and retained UTF-8 page hashes. These prove the consulted policy snapshot, not shipment eligibility.
- [Validation](../VALIDATION.md): actual checks, independent-review findings and current access limits.

The Python core has zero runtime dependencies. Existing subscription agents handle query translation, product reasoning and presentation by invoking the CLI. An MCP wrapper is optional; neither protocol inherently requires paid AI APIs or guarantees lower token use.

- [Fansbuy named marketplaces](fansbuy-marketplaces-2026-10-27.md): five explicitly named platforms, separate keyword/link/procurement claims and non-exhaustive cached evidence.
