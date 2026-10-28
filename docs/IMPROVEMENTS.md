# Project improvement inventory

Audit baseline: commit `c5e6eb395b097f7d7f2b6e93f4c2ccee26a3ca0f`. Seven independent GPT-6.1 Terra reviews examined marketplace acquisition, calculations, data integrity, CLI behavior, security, engineering quality and product documentation. The findings below describe that baseline; they are not claims about subsequent fixes. Reproductions were offline unless stated otherwise. No live marketplace access was used. Priorities express potential impact and do not imply observed exploitation or actual financial loss.

## Correctness and safety findings

| ID | Priority | Finding and evidence | Assigned workstream |
| --- | --- | --- | --- |
| A1 | P1 | Native Blibli browser fallback can continue after an access block or rate limit and report success, obscuring the failure. See `china_deals/adapters.py` search fallback. | acquisition |
| A2 | P1 | Direct Blibli HTTP follows redirects without validating the destination before the next request. | acquisition |
| A3 | P2 | Guest URL canonicalization can remove conflicting or duplicate identity parameters rather than reject an ambiguous item. | acquisition |
| A4 | P2 | Browser detail matching compares pickup-point URLs inconsistently and may reject a matching listing; price binding must remain conservative. | acquisition |
| S1 | P1 | ECB redirects are checked after following them, allowing a request to an unapproved destination. See `china_deals/fx.py`. | security |
| S2 | P2 | Configuration size is checked after reading the entire file. See `china_deals/config.py`. | security |
| C1 | P1 | Brazil comparison can treat case or Schema.org forms of out-of-stock as comparable. | costs |
| C2 | P1 | A comparison can declare a landed-cost winner while international freight is excluded, even when an amount was supplied. | costs |
| C3 | P2 | A non-default Fansbuy configuration can pass a USD offer amount as CNY into a landed-cost scenario. See `china_deals/cli.py`. | cli |
| C4 | P3 | Extreme finite monetary values or rates can cause an uncaught Decimal exception in FX or landed-cost calculations. | decimals |
| D1 | P1 | Refresh drops `variant_observations`, potentially promoting conflicting product evidence into ranking and losing it from history. | data-roundtrip |
| D2 | P1 | Brazil comparison can accept asserted identities that conflict with textual configurations in offers. | data-roundtrip |
| D3 | P1 | For some markets, conflicting outer and nested currency declarations can be reduced to one currency and ranked. | data-core |
| D4 | P2 | Laptop comparison can select a stale price despite a retained required freshness policy. | data-core |
| D5 | P2 | History can compare prices across different configurations when selected variant strings match. | data-roundtrip |
| D6 | P2 | Product profiles can match listings explicitly saying the requested product or component is not included. | data-core |
| U1 | P1 | Search may contact an earlier market before discovering an invalid later per-market query. | cli-extra |
| U2 | P1 | Parser errors and runtime errors use inconsistent streams and output shapes; changing this contract requires compatibility design. | cli-extra |
| U3 | P1 | Search Markdown omits source error details and warnings. | cli-extra |
| U4 | P2 | `detail --fresh-only` help and its treatment of non-fresh items do not agree. | cli-extra |
| U5 | P2 | Invalid preferences can block unrelated offline commands; an explicitly selected missing environment config silently falls back. | cli-extra |
| U6 | P2 | Generic limit validation rejects valid RAM thresholds and accepts history limits the history implementation later rejects. | cli-extra / cli |
| U7 | P2 | Successful JSON responses do not consistently expose a schema version. A compatible envelope needs design. | cli-extra |
| U8 | P1 | Filtering every acquired item locally can change a successful source receipt to `empty_unverified`. | cli |
| U9 | P2 | Markdown comparison omits requested landed-cost scenarios and assumptions. | cli |
| U10 | P2 | A missing history store is indistinguishable from an existing store with no matches. | cli |
| U11 | P3 | Excluded/manual shipping renders as an empty quote table instead of the actual policy status. | cli |

## Engineering and release gaps

| ID | Priority | Gap | Assigned workstream |
| --- | --- | --- | --- |
| E1 | P1 | CI imports from the checkout after installing, so it does not reliably test wheel or sdist contents. Build, install and smoke artifacts outside the checkout. | quality |
| E2 | P1 | CI does not compare the actual project, runtime, CLI and installed-package versions. | quality |
| E3 | P2 | CI does not enforce the documented offline test boundary across subprocesses. | quality |
| E4 | P2 | Some retained-evidence regressions depend on private ignored captures and can skip in a clean checkout. Provide sanitized structural fixtures or explicit skip reporting. | quality |
| E5 | P2 | Release checks do not automatically bind artifact hashes and outside-checkout installation evidence to the exact commit. | quality |
| E6 | P3 | Ruff is configured but not required in CI. | quality |

## Opportunities and design questions

These are not established defects. Workstreams should verify feasibility and retain unresolved decisions instead of implying a feature already exists.

- **Product and onboarding:** Provide an offline first run using synthetic offers and captured shipping; document the full plan → search → detail → refresh → compare workflow; make evidence, freshness and per-source failures readable in Markdown; explore resumable local research manifests and a non-network readiness check. Owner: docs and CLI workstreams.
- **Pricing and shipping:** Represent whether a coupon is already reflected in a price; keep unknown eligibility distinct from verified checkout. Assess structured carrier constraints and expose policy effective dates and provenance without asserting current law. Owners: costs and decimals workstreams.
- **Identity and history:** Build a source-preserving labeled corpus to measure product-profile false positives and unsupported intent; consider a shared typed representation of selected SKU, independent variant and currency evidence; assess whether the 50-receipt history bound misses useful prior observations in real workloads. Owners: data workstreams.
- **Network and privacy:** Define browser subresource and private-network policy, disclose third-party search, and assess persisted evidence retention, restrictive permissions and field-level allowlists. Review Fansbuy redirect and total timeout semantics. Owners: security and docs workstreams.
- **Supply chain and platforms:** Consider immutable CI action references, pinned release installation and dependency artifacts, Python 3.12 and Windows CI coverage, an offline real-browser smoke, and branch-coverage reporting. Verify Windows subprocess behavior before claiming support. Owner: quality workstream.
- **Maintainability:** Evaluate separating CLI parsing, dispatch and rendering behind stable contracts; assess result-level sort verification. File size and missing guarantees alone do not establish defects. Owners: CLI and acquisition workstreams.
- **FX failures and accessibility:** Decide whether an explicitly supplied bad FX file should fail rather than warn; test output with narrow terminals and assistive technology before claiming an accessibility defect. Owners: CLI and docs workstreams.

## Evidence and execution boundaries

The root baseline run passed 562 local tests. This does not establish live marketplace access, current prices, tax law, carrier acceptance, checkout behavior, package publication or hosted CI success. Individual audit findings are assigned to isolated implementation workstreams; results must be reviewed and integrated, and their tests rerun together before they are marked fixed. The pre-existing untracked automotive research HTML is outside this inventory's scope.

## Delegated work

The following tasks were started with Codex GPT-6.1 Terra. Implementation tasks use isolated worktrees; design assessments are read-only. These are task identifiers, not completion receipts.

| Workstream | Task ID |
| --- | --- |
| acquisition | `node:delegated-task:command%3Amcp%3A1253efb8-4baf-48cb-b35c-0b13d3afc655%3Adelegate-task%3Achina-implement-acquisition-20261028` |
| quality | `node:delegated-task:command%3Amcp%3A1253efb8-4baf-48cb-b35c-0b13d3afc655%3Adelegate-task%3Achina-implement-quality-20261028` |
| security | `node:delegated-task:command%3Amcp%3A1253efb8-4baf-48cb-b35c-0b13d3afc655%3Adelegate-task%3Achina-implement-security-20261028` |
| costs | `node:delegated-task:command%3Amcp%3A1253efb8-4baf-48cb-b35c-0b13d3afc655%3Adelegate-task%3Achina-implement-costs-20261028` |
| cli | `node:delegated-task:command%3Amcp%3A1253efb8-4baf-48cb-b35c-0b13d3afc655%3Adelegate-task%3Achina-implement-cli-20261028` |
| docs | `node:delegated-task:command%3Amcp%3A1253efb8-4baf-48cb-b35c-0b13d3afc655%3Adelegate-task%3Achina-implement-docs-20261028` |
| cli-extra | `node:delegated-task:command%3Amcp%3A1253efb8-4baf-48cb-b35c-0b13d3afc655%3Adelegate-task%3Achina-implement-cli-extra-20261028` |
| data-core | `node:delegated-task:command%3Amcp%3A1253efb8-4baf-48cb-b35c-0b13d3afc655%3Adelegate-task%3Achina-implement-data-core-20261028` |
| data-roundtrip | `node:delegated-task:command%3Amcp%3A1253efb8-4baf-48cb-b35c-0b13d3afc655%3Adelegate-task%3Achina-implement-data-roundtrip-20261028` |
| decimals | `node:delegated-task:command%3Amcp%3A1253efb8-4baf-48cb-b35c-0b13d3afc655%3Adelegate-task%3Achina-implement-decimals-20261028` |
| future-product | `node:delegated-task:command%3Amcp%3A1253efb8-4baf-48cb-b35c-0b13d3afc655%3Adelegate-task%3Achina-future-product-20261028` |
| future-data | `node:delegated-task:command%3Amcp%3A1253efb8-4baf-48cb-b35c-0b13d3afc655%3Adelegate-task%3Achina-future-data-20261028` |
| future-security | `node:delegated-task:command%3Amcp%3A1253efb8-4baf-48cb-b35c-0b13d3afc655%3Adelegate-task%3Achina-future-security-20261028` |

## Follow-up design details

- **Calibration corpus:** Keep immutable, permitted source excerpts or sanitized artifacts with hashes, source and capture metadata, queries and independently versioned human labels. Report abstentions, disagreement and errors by language and family; synthetic results alone are not representative live accuracy.
- **Shared evidence:** Version a selected-item/SKU, variant and currency evidence envelope, preserving original values, source references, timestamps and conflicts. Migrate legacy inputs conservatively; do not turn listing-wide options into a selected SKU.
- **Coupons:** Bind `reflected`, `not_reflected` or `unknown` to a specific campaign and observed price, SKU, currency and evidence. Unknown remains a hypothetical scenario, not a verified extra discount.
- **History:** Evaluate bounded keyset pagination and a scan budget; distinguish a complete search for prior observations from one stopped by the budget. Choosing the latest observation versus the latest comparable observation is a behavior decision.
- **Policy and carriers:** Store raw source fields and versioned interpretations with source, time, destination and package scope. Require an explicit scenario date for policy selection and retain unknown applicability; neither a snapshot nor a carrier quote is legal clearance.
- **Browser boundary:** A request allowlist is defense in depth, not proof of network isolation. Evaluate an enforced network namespace or proxy and test subresources, redirects, WebSockets, private IPs and DNS rebinding with controlled fixtures.
- **Retention:** Design explicit previewable pruning and private file permissions without promising forensic deletion or silently changing existing stores. Test concurrency, rollback and history effects.
- **Readiness and reproducibility:** An offline readiness mode must distinguish local inventory from actual provider access and avoid running untrusted executables; pin and review CI dependencies and actions, and validate exact-artifact hashes and platform-specific behavior separately.
- **Manifests and sort:** If added, manifests should be opt-in, bounded, offline to open and preserve source failures, artifact hashes, timestamps and assumptions without replay. Distinguish verified local price ordering from an unverified marketplace sort.
- **Output compatibility:** Consider an opt-in versioned error and success envelope before changing existing JSON or argparse error behavior; explicitly define how invalid supplied FX files are handled.
