# Framework reuse research for china-deals

Scope clarification: the user means **Blibli Indonesia**, not Bilibili. Bilibili sections below describe capabilities of the originally supplied repositories; they are not target integrations in china-deals. See [Blibli research](blibli.md) for the implemented access boundary.

Research date: 2026-10-27. This is a static, source-pinned dependency assessment, not an installation or live-site acceptance result.

## Recommendation

Use **OpenCLI as a dependency**, behind a small china-deals-owned read-only subprocess adapter. At the inspected revision it contains executable Taobao, JD, Goofish/Xianyu and Bilibili adapters, uses an existing logged-in Chrome/Chromium profile through its Browser Bridge extension, and does not require an AI API for those deterministic adapters. Its project license is Apache-2.0. Preserve the upstream package and extension rather than forking the browser transport. [Package/API surface](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/package.json); [browser/profile setup](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/README.md#quick-start); [license](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/LICENSE).

Use **Scrapling optionally for generic HTTP/HTML extraction and explicitly maintained fallback selectors**, especially if the ingestion side is Python. It is BSD-3-Clause and can use persistent browser sessions or an existing CDP browser without an AI service. It does not supply the four marketplace/video business adapters verified in OpenCLI. Do not add a second browser framework until an actual extraction gap justifies it. [Fetching/session contract](https://github.com/D4Vinci/Scrapling/blob/c0009dbee8d02e90fdfef9a426704ae61c6943df/docs/fetching/stealthy.md); [dependencies](https://github.com/D4Vinci/Scrapling/blob/c0009dbee8d02e90fdfef9a426704ae61c6943df/pyproject.toml); [license](https://github.com/D4Vinci/Scrapling/blob/c0009dbee8d02e90fdfef9a426704ae61c6943df/LICENSE).

**Agent-Reach is useful as an optional general research CLI, not the marketplace foundation.** Its current MIT code has a real normalized command runtime and Bilibili channel, but no registered Taobao/JD/Xianyu channels. More importantly, its default Bilibili backend installs `bilibili-cli==0.6.2`, which depends on `bilibili-api-python>=16.0`; the latter's package metadata declares GPL-3.0-or-later. MIT on the wrapper does not make that whole path permissive-only. [Registered channels](https://github.com/Panniantong/Agent-Reach/blob/14c213405669414492bda0f8d52cc6531d062c45/agent_reach/channels/__init__.py); [tool versions](https://github.com/Panniantong/Agent-Reach/blob/14c213405669414492bda0f8d52cc6531d062c45/agent_reach/runtime/tools.py#L51-L66); [bili-cli dependencies](https://github.com/public-clis/bilibili-cli/blob/dbe28551930df43b633baa52e9639832aeada967/pyproject.toml); [versioned PyPI metadata](https://pypi.org/pypi/bilibili-api-python/17.4.1/json).

## Evidence, scope and pins

Read the repository workflow; initial `git status --short` in `/home/marlos/projects/china-deals` was clean. Ownership for this task is only this file and `.local/research/frameworks/`. No upstream repository was cloned, installed, built, imported or executed. No browser was opened, no cookies/profile read, no login attempted and no publishing performed.

Used GitHub plugin repository metadata, commit, recursive-tree and pinned-file GETs. Graph discovery listed all 72 projects with `has_more:false` and identified `home-marlos-projects-china-deals` at the exact local root. The external repositories were examined through the GitHub plugin rather than cloned/indexed locally; there is no graph-based caller coverage for those upstreams. Claims about executable behavior come from the cited source registrations and implementations, not a graph absence. Generic frameworks were checked against their repository trees and relevant first-party docs; “no verified adapter” below is a bounded finding, not proof that a third-party plugin cannot exist.

The commits below were each the upstream default-branch head returned during this research. They are **source pins**, not a claim that every commit has a corresponding published package or extension release. Release artifacts, transitive dependencies and extension compatibility still need an implementation-time lock.

| Repository | Full commit | Committer UTC | Repository license |
|---|---|---|---|
| [Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach/commit/14c213405669414492bda0f8d52cc6531d062c45) | `14c213405669414492bda0f8d52cc6531d062c45` | 2026-10-25T04:37:23Z | MIT |
| [jackwener/opencli](https://github.com/jackwener/opencli/commit/97dc0cd5214b9602bcda78d7422f231ee8a803e9) | `97dc0cd5214b9602bcda78d7422f231ee8a803e9` | 2026-10-26T07:53:40Z | Apache-2.0 |
| [browser-use/browser-use](https://github.com/browser-use/browser-use/commit/2cc71890e65056b67fdb29d98bb407749c15bb08) | `2cc71890e65056b67fdb29d98bb407749c15bb08` | 2026-10-26T22:00:16Z | MIT |
| [browserbase/stagehand](https://github.com/browserbase/stagehand/commit/63078cf85ddfe189da88204539ec30d41959378b) | `63078cf85ddfe189da88204539ec30d41959378b` | 2026-10-27T02:30:30Z | MIT |
| [unclecode/crawl4ai](https://github.com/unclecode/crawl4ai/commit/888299fb5f0b82181897dc0e61bfb4b036f0aea5) | `888299fb5f0b82181897dc0e61bfb4b036f0aea5` | 2026-10-26T08:41:46Z | Apache-2.0 |
| [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl/commit/2b68c4c56efc54ab10229cd2f992d1f1e71961f9) | `2b68c4c56efc54ab10229cd2f992d1f1e71961f9` | 2026-10-27T08:43:00Z | AGPL-3.0 |
| [D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling/commit/c0009dbee8d02e90fdfef9a426704ae61c6943df) | `c0009dbee8d02e90fdfef9a426704ae61c6943df` | 2026-10-27T08:27:55Z | BSD-3-Clause |
| [Nemo2011/bilibili-api](https://github.com/Nemo2011/bilibili-api/commit/3798d3b3bd3c3a93678d5a0367637a19262303ef) | `3798d3b3bd3c3a93678d5a0367637a19262303ef` | 2026-07-06T13:49:41Z | No license file at current revision |
| [public-clis/bilibili-cli](https://github.com/public-clis/bilibili-cli/commit/dbe28551930df43b633baa52e9639832aeada967) | `dbe28551930df43b633baa52e9639832aeada967` | 2026-03-14T12:23:47Z | Apache-2.0 |

Retained decoded source snapshots and metadata are under `.local/research/frameworks/<owner>--<repo>/`; `tree.json` records complete non-truncated tree responses for the eight main candidates. `manifest.json` lists fetched source URLs and SHA-256 hashes of the **retained local files**, not a claim about byte-identical remote HTTP bodies. The two PyPI JSON receipts separately preserve package license and artifact hashes. No code from a fetched repository was run.

## Comparison against the actual requirements

“AI API optional” means deterministic extraction can run without sending a prompt to an AI API. It does not mean a hosted browser service is free, or that browser login is unnecessary.

| Candidate | License / no mandatory AI API | Persistent logged-in browser | Verified target adapters | Reuse judgment and costs |
|---|---|---|---|---|
| **OpenCLI** | Apache-2.0; deterministic registered adapters have no model/key requirement | Browser Bridge extension in existing Chrome profile; explicit profile selection; persistent site sessions | **Taobao search/detail/reviews; JD search/item/detail/reviews; Xianyu search/item; Bilibili search/video/subtitle/summary and more** | Best fit. Node >=20.18.1, Chrome/Chromium, extension and local daemon; browser memory, manual session renewal and adapter maintenance. [Sources](#opencli-exact-read-only-commands-and-contracts) |
| **Agent-Reach** | MIT wrapper; Bilibili default path pulls GPL dependency; base search/read does not need AI inference | Dedicated Reach browser plus site-scoped cookie reuse from a connected local browser; Bilibili native credential state | Bilibili yes; **no registered Taobao/JD/Xianyu channel** | Optional auxiliary service. Python >=3.10 plus per-channel tooling; overlaps OpenCLI; two runtimes and session management. [Sources](#agent-reach-actual-cli-dependencies-and-contracts) |
| **browser-use** | MIT; deterministic actor calls need no model; autonomous Agent needs inference, which can use a local Ollama model | `Browser(cdp_url=...)`, `user_data_dir`, `profile_directory`, `storage_state`; documented `Browser.from_system_chrome()` | No first-party target-specific adapter verified in inspected tree/docs | Good exploratory browser agent, poor default for four fixed feeds. Python >=3.11; large dependency set including provider SDKs and Browser Harness; optional local-model GPU/RAM or token charges. [README](https://github.com/browser-use/browser-use/blob/2cc71890e65056b67fdb29d98bb407749c15bb08/README.md), [actor API](https://github.com/browser-use/browser-use/blob/2cc71890e65056b67fdb29d98bb407749c15bb08/skills/open-source/references/actor.md), [browser](https://github.com/browser-use/browser-use/blob/2cc71890e65056b67fdb29d98bb407749c15bb08/skills/open-source/references/browser.md), [manifest](https://github.com/browser-use/browser-use/blob/2cc71890e65056b67fdb29d98bb407749c15bb08/pyproject.toml) |
| **Stagehand / Browserbase** | Stagehand MIT; low-level browser actions can be deterministic; natural-language `act/observe/extract` use model inference; Browserbase is a separate hosted service | v4 `localBrowser.launch({userDataDir})`, `localBrowser.connect({cdpUrl})`; Browserbase persistent contexts | No first-party target-specific adapter verified in inspected tree/docs | Useful if natural-language fallback is later required. Inspected SDK is **4.3.0, Node >=22.18.0**, not an assumed v2/v3 API. Local Chrome/extension overhead; inference and cloud browser charges if selected. [README](https://github.com/browserbase/stagehand/blob/63078cf85ddfe189da88204539ec30d41959378b/README.md), [browser config](https://github.com/browserbase/stagehand/blob/63078cf85ddfe189da88204539ec30d41959378b/packages/docs/v4/configuration/browser.mdx), [model config](https://github.com/browserbase/stagehand/blob/63078cf85ddfe189da88204539ec30d41959378b/packages/docs/v4/configuration/models.mdx), [SDK manifest](https://github.com/browserbase/stagehand/blob/63078cf85ddfe189da88204539ec30d41959378b/packages/sdk-ts/package.json) |
| **Crawl4AI** | Apache-2.0 LICENSE; CSS/XPath/regex extraction needs no model. README additionally asks for badge/text attribution; retain that notice or clarify its wording before distribution | `BrowserConfig(user_data_dir=..., use_persistent_context=True)`; session IDs retain an in-process page, which is distinct from on-disk login persistence | No first-party target-specific adapter verified in inspected tree/docs | Good document crawling/Markdown pipeline, more framework than necessary here. Python >=3.10, Playwright/Patchright browsers, LiteLLM fork and additional parsing/numeric deps; local compute/storage and selector upkeep. [README](https://github.com/unclecode/crawl4ai/blob/888299fb5f0b82181897dc0e61bfb4b036f0aea5/README.md), [session semantics](https://github.com/unclecode/crawl4ai/blob/888299fb5f0b82181897dc0e61bfb4b036f0aea5/docs/md_v2/advanced/session-management.md), [manifest](https://github.com/unclecode/crawl4ai/blob/888299fb5f0b82181897dc0e61bfb4b036f0aea5/pyproject.toml), [LICENSE](https://github.com/unclecode/crawl4ai/blob/888299fb5f0b82181897dc0e61bfb4b036f0aea5/LICENSE) |
| **Firecrawl** | **Server AGPL-3.0**, Python/JS SDKs MIT. Ordinary scrape can work without a model; hosted API requires a Firecrawl credential/credits | Hosted browser/profile APIs exist; this is not automatically reuse of a local signed-in Chrome profile. Local self-hosted parity must be checked separately | No first-party target-specific adapter verified in inspected tree/docs | Reject as the permissive-only self-hosted core. Hosted service could be a separately priced generic public-page option. API/workers, Playwright, Redis, RabbitMQ, NuQ Postgres and optional FoundationDB make self-hosting costly to operate. [server license](https://github.com/firecrawl/firecrawl/blob/2b68c4c56efc54ab10229cd2f992d1f1e71961f9/LICENSE), [SDK license](https://github.com/firecrawl/firecrawl/blob/2b68c4c56efc54ab10229cd2f992d1f1e71961f9/apps/python-sdk/LICENSE), [self-host contract](https://github.com/firecrawl/firecrawl/blob/2b68c4c56efc54ab10229cd2f992d1f1e71961f9/SELF_HOST.md), [browser/profile implementation](https://github.com/firecrawl/firecrawl/blob/2b68c4c56efc54ab10229cd2f992d1f1e71961f9/apps/api/src/controllers/v2/browser.ts), [README](https://github.com/firecrawl/firecrawl/blob/2b68c4c56efc54ab10229cd2f992d1f1e71961f9/README.md) |
| **Scrapling** | BSD-3-Clause; selectors, HTTP/browser fetches and extraction work without AI | `StealthySession(user_data_dir=...)`; `cdp_url` for existing browsers; directory option works with sessions | No first-party target-specific adapter verified in inspected tree/docs | Best optional generic fallback/parser. Python >=3.10; core lxml, browser extras add curl_cffi/Playwright/Patchright and browsers. Local resources and selector repair; no required SaaS bill. [manifest](https://github.com/D4Vinci/Scrapling/blob/c0009dbee8d02e90fdfef9a426704ae61c6943df/pyproject.toml), [browser/session config](https://github.com/D4Vinci/Scrapling/blob/c0009dbee8d02e90fdfef9a426704ae61c6943df/docs/fetching/stealthy.md), [license](https://github.com/D4Vinci/Scrapling/blob/c0009dbee8d02e90fdfef9a426704ae61c6943df/LICENSE) |
| **bilibili-api-python** | **GPL-3.0-or-later package metadata**, not permissive | Historically native Bilibili credentials, not a browser-profile adapter. Current source no longer offers an inspectable implementation | Bilibili only historically; **current upstream is a one-file shutdown notice** | Reject for a new permissive-only design. License mismatch and a concrete upstream maintenance shutdown; no honest current CLI/API contract can be recovered from this revision. [shutdown notice](https://github.com/Nemo2011/bilibili-api/blob/3798d3b3bd3c3a93678d5a0367637a19262303ef/README.md), [PyPI 17.4.1](https://pypi.org/pypi/bilibili-api-python/17.4.1/json), [latest metadata](https://pypi.org/pypi/bilibili-api-python/json) |

Repository license checks do not constitute a complete transitive-license audit. In particular, a subprocess boundary does not itself resolve GPL obligations; this design avoids selecting the GPL-backed Bilibili path.

## Agent-Reach: actual CLI, dependencies and contracts

### What it actually is now

At the pinned revision, `pyproject.toml` declares version **1.6.0** and entry point `agent-reach = agent_reach.cli:main`. The 48-line console shim configures output/logging and delegates to `agent_reach.runtime.cli.main`; the runtime parses channels/actions and dispatches backends. This is a genuine CLI with an implemented JSON interface, **and** many channels are wrappers around other CLIs/services. It is not just a skill prompt, nor a replacement browser engine. [Manifest](https://github.com/Panniantong/Agent-Reach/blob/14c213405669414492bda0f8d52cc6531d062c45/pyproject.toml); [entry shim](https://github.com/Panniantong/Agent-Reach/blob/14c213405669414492bda0f8d52cc6531d062c45/agent_reach/cli.py); [runtime parser](https://github.com/Panniantong/Agent-Reach/blob/14c213405669414492bda0f8d52cc6531d062c45/agent_reach/runtime/cli.py); [dispatch](https://github.com/Panniantong/Agent-Reach/blob/14c213405669414492bda0f8d52cc6531d062c45/agent_reach/runtime/dispatch.py).

Its README warns that the PyPI package named `agent-reach` is **not this project**. Any future installation should use an audited pinned upstream artifact, not infer identity from that PyPI name. No installation is authorized or performed here. [README](https://github.com/Panniantong/Agent-Reach/blob/14c213405669414492bda0f8d52cc6531d062c45/README.md).

The Python package depends on `requests>=2.28`, `loguru>=0.7`, `pyyaml>=6.0`, `yt-dlp[default]==2026.8.19`. Other tools are managed separately by `runtime/tools.py`, including `bilibili-cli` tested at **0.6.2** and OpenCLI tested at **1.8.7**, minimum 1.8.7, excluding 1.8.8. The inspected independent OpenCLI head is **2.0.2**; do not assume Reach's tested integration has been validated with it. Reach installs OpenCLI with `--ignore-scripts`, and its bridge checks running daemon version against package version. [Base dependencies](https://github.com/Panniantong/Agent-Reach/blob/14c213405669414492bda0f8d52cc6531d062c45/pyproject.toml); [managed tools and installer](https://github.com/Panniantong/Agent-Reach/blob/14c213405669414492bda0f8d52cc6531d062c45/agent_reach/runtime/tools.py); [bridge compatibility](https://github.com/Panniantong/Agent-Reach/blob/14c213405669414492bda0f8d52cc6531d062c45/agent_reach/runtime/bridge.py).

### Bilibili: exact runtime routes

The **action registry and methods** in `channels/bilibili.py` are authoritative. Its opening comment still refers to OpenCLI subtitles, but the actual registered subtitle backend is `bili-cli` only. yt-dlp remains a Python dependency/YouTube backend, not a Bilibili backend at this pin. [Full channel source](https://github.com/Panniantong/Agent-Reach/blob/14c213405669414492bda0f8d52cc6531d062c45/agent_reach/channels/bilibili.py).

| Agent-facing command | Actual backend invocation/route | Meaning and limitations |
|---|---|---|
| `agent-reach bilibili search "机械键盘" --limit 5` | `bili search "机械键盘" --type video -n 5 --json` | Default limit 5; only registered backend is bili-cli |
| `agent-reach bilibili read BV1GJ411x7h7` | `bili video BV1GJ411x7h7 --json`; fallback HTTP `/x/web-interface/view?bvid=...` | Video metadata, not video/audio understanding |
| `agent-reach read https://www.bilibili.com/video/BV1GJ411x7h7` | URL dispatcher selects Bilibili `read` | Same read action; BV IDs and b23.tv links also handled by channel |
| `agent-reach bilibili hot --limit 10` | `bili hot -n 10 --json`; fallback HTTP `/x/web-interface/popular?ps=10&pn=1` | Default limit 10 |
| `agent-reach bilibili subtitle BV1GJ411x7h7` | `bili video BV1GJ411x7h7 --subtitle --json` | First part only; no exposed language/part selector; may need login |
| `agent-reach bilibili read BV1GJ411x7h7 --backend bilibili-api --timeout 30` | Force the channel's built-in HTTP read implementation | **The label “bilibili-api” here does not import the GPL Python SDK.** It is an internal backend label using HTTP |
| `agent-reach bilibili hot --limit 5 --backend bilibili-api` | Force the built-in HTTP popular endpoint | This does not create a search or subtitle backend |

Do not invent `agent-reach search-bilibili`, `agent-reach taobao search`, `agent-reach jd ...`, `agent-reach goofish ...`, or a Bilibili `transcript` action. The runtime exposes `channels` for actual names; Bilibili actions are `search/read/hot/subtitle`. There is no `--json` requirement on these Reach commands: JSON is already the default. [Channel registry](https://github.com/Panniantong/Agent-Reach/blob/14c213405669414492bda0f8d52cc6531d062c45/agent_reach/channels/__init__.py); [parser](https://github.com/Panniantong/Agent-Reach/blob/14c213405669414492bda0f8d52cc6531d062c45/agent_reach/runtime/cli.py).

Auxiliary introspection commands, listed for a later implementation review and **not run here**:

```bash
agent-reach version
agent-reach channels
agent-reach doctor
agent-reach browser status
agent-reach browser profiles
```

`doctor` is documented as a local status/version check without network; `check` performs live requests. `setup/add/update/login/browser setup` can install, alter state or start browsers, so none belongs in a read-only research verification step. Management commands have a different result shape from data actions. [Runtime help/handlers](https://github.com/Panniantong/Agent-Reach/blob/14c213405669414492bda0f8d52cc6531d062c45/agent_reach/runtime/cli.py).

### Agent-facing wire format

For data actions, the source constructs one JSON object on stdout, newline terminated; logs go to stderr. Exit 0 means `ok:true`, exit 1 means error. Human `help` and selected `--text` management output are exceptions. This illustrative shape is transcribed from source, **not captured live output**:

```json
{
  "schema_version": 1,
  "ok": true,
  "channel": "bilibili",
  "action": "search",
  "backend": "bili-cli",
  "items": [
    {
      "title": "...",
      "url": "https://www.bilibili.com/video/...",
      "author": "...",
      "published_at": null,
      "text": null,
      "raw": {}
    }
  ],
  "meta": {
    "elapsed_ms": 123,
    "attempts": [{"backend": "bili-cli", "result": "ok"}]
  },
  "error": null
}
```

The normalized item keys are always `title,url,author,published_at,text,raw`; missing normalized fields become null. Preserve `raw`: normalizing video data may omit fields from the top level. On error, `backend:null`, `items:[]`, and `error:{code,message,hint}`. Codes include `NEED_SETUP,NEED_LOGIN,UPSTREAM_BROKEN,TIMEOUT,RATE_LIMITED,PLATFORM_BLOCKED,NOT_FOUND,BAD_INPUT`, plus runtime `BUSY`. Cached update information may add `meta.update`; consumers must allow additive metadata. Management output is `{schema_version,ok,action,result,error}`; do not parse it as a data envelope. [Result constructors](https://github.com/Panniantong/Agent-Reach/blob/14c213405669414492bda0f8d52cc6531d062c45/agent_reach/runtime/result.py); [stdout/management handlers](https://github.com/Panniantong/Agent-Reach/blob/14c213405669414492bda0f8d52cc6531d062c45/agent_reach/runtime/cli.py).

The dispatcher stops fallback for final errors including login, platform blocking and rate limits. A recorded rate limit pauses the channel for 3,600 seconds; attempts can include `skipped`, `retry_after_seconds` and message fields. Do not add an outer retry loop that defeats this behavior. [Dispatch state/control flow](https://github.com/Panniantong/Agent-Reach/blob/14c213405669414492bda0f8d52cc6531d062c45/agent_reach/runtime/dispatch.py).

Subtitle handling is careful but narrower than a transcript service: with no saved credential it reports `NEED_LOGIN`; an upstream `subtitle_unavailable` warning becomes `UPSTREAM_BROKEN`, explicitly **not proof that no subtitle exists**. Available subtitle segments are collapsed into item text; use direct OpenCLI if timestamps/language/part selection matter. [Subtitle method](https://github.com/Panniantong/Agent-Reach/blob/14c213405669414492bda0f8d52cc6531d062c45/agent_reach/channels/bilibili.py#L226-L239).

### Native bili-cli and login ownership

Native `bili ... --json` uses `{ok:true,schema_version:"1",data:...}`, with a **string** schema version. Failure has `{ok:false,schema_version:"1",error:{code,message,details?}}` and exit 1. That differs from both Reach and OpenCLI. Its default non-TTY output can be YAML, so `--json` must be explicit when bypassing Reach. [Formatter](https://github.com/public-clis/bilibili-cli/blob/dbe28551930df43b633baa52e9639832aeada967/bili_cli/formatter.py); [hot implementation](https://github.com/public-clis/bilibili-cli/blob/dbe28551930df43b633baa52e9639832aeada967/bili_cli/commands/discovery.py); [video implementation](https://github.com/public-clis/bilibili-cli/blob/dbe28551930df43b633baa52e9639832aeada967/bili_cli/commands/video.py).

Reach isolates native tool state under `~/.agent-reach/sessions/<tool>/`, with HOME-family overrides for that child. Its subtitle method looks for `sessions/bili-cli/.bilibili-cli/credential.json`. It can copy Bilibili cookies from an already connected local Browser Bridge into the native credential writer. The source rejects ambiguous multiple account sources and records copied state as unverified. Thus a standalone `bili login` in the ordinary shell is not automatically the same saved session that Reach uses. Keep a single owner of session setup; no login was performed in this research. [Session environment](https://github.com/Panniantong/Agent-Reach/blob/14c213405669414492bda0f8d52cc6531d062c45/agent_reach/runtime/sessions.py); [site reuse](https://github.com/Panniantong/Agent-Reach/blob/14c213405669414492bda0f8d52cc6531d062c45/agent_reach/runtime/session_reuse.py); [Bilibili reuse method](https://github.com/Panniantong/Agent-Reach/blob/14c213405669414492bda0f8d52cc6531d062c45/agent_reach/channels/bilibili.py#L80-L110).

The `public-clis/bilibili-cli` source identifies as Apache-2.0, but its manifest permits `bilibili-api-python>=16.0` and its committed lock selects **17.4.1**. PyPI 17.4.1 declares **GPL-3.0-or-later**; latest metadata currently reports 17.4.2 with the same license. Nemo2011's current GitHub commit has no parents, one README and no current LICENSE/source implementation; the README announces maintenance stopped and permanent shutdown on 2026-07-06. Do not treat old tutorials as evidence of a maintained permissive SDK. [CLI manifest](https://github.com/public-clis/bilibili-cli/blob/dbe28551930df43b633baa52e9639832aeada967/pyproject.toml); [lock](https://github.com/public-clis/bilibili-cli/blob/dbe28551930df43b633baa52e9639832aeada967/uv.lock#L257-L258); [versioned metadata](https://pypi.org/pypi/bilibili-api-python/17.4.1/json); [shutdown](https://github.com/Nemo2011/bilibili-api/blob/3798d3b3bd3c3a93678d5a0367637a19262303ef/README.md).

## OpenCLI: exact read-only commands and contracts

### Execution, browser and dependency boundaries

At this pin, `@jackwener/opencli` is **2.0.2**, ESM, Node >=20.18.1. It ships `clis/` adapter modules and exports the registry/errors/browser helpers for separately owned adapters. Its executable is `dist/src/main.js`; the package's root export also points to that CLI entry, so do not assume importing the package root is a side-effect-free scraping library. For china-deals, the simplest isolation is a pinned CLI subprocess with argument arrays and a timeout. For a genuinely missing adapter, use the public registry interface in a separate module rather than forking the transport. [Package exports](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/package.json); [registry API](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/src/registry-api.ts); [main](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/src/main.ts).

Existing site adapters execute browser navigation, DOM extraction and/or authenticated browser-side fetches. “AI-powered” in product branding does not make runtime model inference mandatory for them. Adapter authoring can be manual and deterministic. Chrome needs the Browser Bridge extension and a local daemon; the existing profile owns login state. With multiple profiles, select one explicitly. The documented commands below are reference syntax, not performed actions:

```bash
opencli profile list
opencli profile rename <contextId> china-deals
opencli profile use china-deals
opencli --profile china-deals taobao search "机械键盘" --limit 5 -f json
```

The last two profile commands change a future local default/alias; they were not executed. Prefer an explicit `--profile` on every production invocation rather than depending on a mutable default. Preserve long-lived login state separately from a page/tab session; documented `--site-session ephemeral` changes tab-session lifetime, not proof of an incognito or logged-out account. [Browser/profile and site-session docs](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/README.md).

The install manifest has postinstall hooks. At the inspected pin, `scripts/fetch-adapters.js` describes local hash-based cleanup of sparse overrides, **not network downloading**; it can remove stale official-site overrides when upstream changes. Do not assume a package version alone fixes behavior if `~/.opencli/clis/` contains local overrides. Lock package/extension versions and record effective adapter hashes; keep china-deals custom code in its own dependency/module with an explicit override policy. [Package scripts](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/package.json); [adapter sync source](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/scripts/fetch-adapters.js).

### Actual target commands

Every command below is source-derived and was **not executed**. IDs are upstream examples, not product recommendations or validation of listing availability. For a chosen profile, insert `--profile china-deals` after `opencli`.

```bash
# Taobao / 淘宝
opencli taobao search "机械键盘" --sort price --limit 5 -f json
opencli taobao detail 827563850178 -f json
opencli taobao reviews 827563850178 --limit 5 -f json

# JD / 京东
opencli jd search "机械键盘" --limit 5 -f json
opencli jd item 100291143898 --images 5 -f json
opencli jd detail 100291143898 -f json

# Goofish / 闲鱼: the CLI namespace is xianyu
opencli xianyu search "macbook" --limit 5 -f json
opencli xianyu search "小鹏G9" --min-price 100000 --max-price 200000 --city 深圳 --limit 10 -f json
opencli xianyu item 1040754408976 -f json

# Bilibili / 哔哩哔哩
opencli bilibili search "机械键盘" --type video --page 1 --limit 5 -f json
opencli bilibili video BV1GJ411x7h7 --page 1 -f json
opencli bilibili subtitle BV1GJ411x7h7 --lang zh-CN --page 1 -f json
opencli bilibili summary BV1GJ411x7h7 -f json
```

Sources: [Taobao search](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/clis/taobao/search.js), [detail](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/clis/taobao/detail.js), [reviews](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/clis/taobao/reviews.js); [JD search](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/clis/jd/search.js), [item](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/clis/jd/item.js), [detail](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/clis/jd/detail.js), [reviews registration](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/clis/jd/reviews.js); [Xianyu search](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/clis/xianyu/search.js), [item](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/clis/xianyu/item.js); [Bilibili search](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/clis/bilibili/search.js), [video](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/clis/bilibili/video.js), [subtitle](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/clis/bilibili/subtitle.js), [summary](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/clis/bilibili/summary.js).

Both **`jd item` and `jd detail` exist**. They are different adapters, not an alias to assume interchangeable. `item` has richer image/spec extraction and page-state checks. Conversely, `xianyu` is the actual namespace; do not invent `opencli goofish`.

### JSON and process contracts

At this exact pin, `-f json` goes through `emitResult` and prints:

```json
{"ok":true,"data":[{"...":"adapter-specific row"}]}
```

It is **not a bare array**, not Reach's `items` envelope, and has no common `schema_version`. Errors go through `emitFailure`: `{ok:false,error:{code,message,exitCode,hint?,...},trace?:...}`. Internally `toEnvelope` uses `help`, and `emitFailure` normalizes it to `hint`. Additional details/trace fields are possible. Preserve the complete error, stdout and stderr. The error constants define exits 0 success, 1 generic, 2 usage, 66 empty/no input, 69 unavailable, 75 temporary failure, 77 auth, 78 configuration, 130 interruption. Some unknown-outcome codes add `error.outcome:"unknown"`; never interpret that as no side effect. These are source contracts, not live command receipts. [JSON rendering](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/src/output.ts); [wire emission](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/src/command-output.ts); [error schema/codes](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/src/errors.ts).

JSON rendering passes the returned data through unchanged, while `columns` affects human tabular output. Consume actual `data`, not only displayed columns:

| Adapter | Actual data shape / important fields | Constraints and data quality |
|---|---|---|
| Taobao `search` | Array: `rank,title,price,sales,shop,location,item_id,url` | Limit default 10, clamp 1–40. `price` is display text with ¥; ID can be empty. DOM class substrings and title deduplication can lose or mispair listings; require a stable ID before ingestion |
| Taobao `detail` | Array of `{field,value}`, Chinese labels such as 商品名称, 价格, ID, 链接 | Price is the minimum of up to three regex matches in page text, not a guaranteed selected-SKU/checkout price. No stable product JSON object |
| Taobao `reviews` | Array: `rank,user,content,date,spec` | Default 10, clamp 1–20; visible-page review sampling |
| JD `search` | Array: `rank,title,price,shop,sku,url` | Default 10, clamp 1–30; DOM/data-sku and text regexes. An empty array can reflect page failure as well as no matching items |
| JD `item` | One-element array: `title,price,shop,specs,mainImages,detailImages,totalImages,pageState` | `specs` object, image arrays, `pageState` object. Price API plus DOM fallback; can return literal `"not found"`. Default image limit 200; positive image limit can cause failure if detail images are missing |
| JD `detail` | Array of Chinese `{field,value}` rows | Lightweight regex/DOM route; no equivalent completeness guarantee to `item` |
| Xianyu `search` | Array: `rank,item_id,title,price,condition,brand,location,badge,want,url` | Default 20, max 60; 30 rows/page. Browser-side `window.lib.mtop.request` to `mtop.taobao.idlemtopsearch.pc.search`; price/region filters server-side, prices in yuan |
| Xianyu `item` | One-element array: `item_id,title,description,price,original_price,want_count,collect_count,browse_count,status,condition,brand,category,location,seller_name,seller_id,seller_score,reply_ratio_24h,reply_interval,item_url,seller_url,image_count,image_urls` | Most values are strings, `image_urls` is an array. Uses site mtop API in the logged-in browser; seller score is source text, not a normalized trust score |
| Bilibili `search --type video` | Array: `rank,title,author,mid,score,plays,likes,danmaku,favorites,duration,duration_sec,pubdate_ts,url,cover,face,desc` | `score` and `plays` are both play count; `mid` is uploader ID. No separate bvid field; retain/parse the source URL. User search has a different subset |
| Bilibili `video` | Array of `{field,value}` rows | Metadata/playback flags, with optional part selection; do not assume normalized product fields |
| Bilibili `subtitle` | Array: `index,from,to,content,language,track_type` | Times are strings such as `"1.23s"`, not numeric seconds. `track_type` = `ai/cc/unknown`. Unsupported requested language silently falls back to first track: validate returned language |
| Bilibili `summary` | Array: `time,content` | Reads **Bilibili's pre-existing AI summary**, not a transcript and not an external AI API call; unavailable if the platform has not generated one |

All rows above derive from the command sources linked immediately above. Adapter-specific errors need interpretation: e.g. Xianyu item verification can surface as `EmptyResultError`, and other failures can be categorized broadly as auth. An empty result or exit 66 is **not proof of delisting or a truly empty market**. Taobao detects login/security pages; JD `item` has page-state checks; JD `search/detail` are less defensive. [Xianyu detail errors](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/clis/xianyu/item.js); [Taobao page checks](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/clis/taobao/page-state.js); [JD item](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/clis/jd/item.js).

OpenCLI also ships write adapters, including cart mutation, Bilibili interactions, Xianyu replies and publishing. **The dependency is not globally read-only.** Restrict the integration to the exact site/action allowlist above (and reviewed additions); never forward arbitrary user/agent command names. No write command was executed in this task. [Taobao docs](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/docs/adapters/browser/taobao.md); [Xianyu docs](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/docs/adapters/browser/xianyu.md); [Bilibili docs](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/docs/adapters/browser/bilibili.md).

## How to reuse the generic alternatives

- **Scrapling:** use the Python selector/fetcher API to emit an application-owned JSON record. Its CLI examples `scrapling extract get "https://example.com/" page.md` and `scrapling extract fetch "https://example.com/" page.md` write HTML/Markdown/text **files**, not OpenCLI-style product JSON envelopes. Persistent `user_data_dir` belongs to browser **sessions**; a one-shot fetch should not be mistaken for disk persistence. [CLI](https://github.com/D4Vinci/Scrapling/blob/c0009dbee8d02e90fdfef9a426704ae61c6943df/scrapling/cli.py); [session options](https://github.com/D4Vinci/Scrapling/blob/c0009dbee8d02e90fdfef9a426704ae61c6943df/docs/fetching/stealthy.md).
- **Crawl4AI:** `crwl https://example.com -o markdown` is documented for Markdown; CSS/XPath extraction through its library is the deterministic structured-data route. `-q` question answering requires inference. Its library `CrawlResult` is not a marketplace data contract. Prefer it over Scrapling only if multi-page crawling/Markdown quality is the main job. [README examples](https://github.com/unclecode/crawl4ai/blob/888299fb5f0b82181897dc0e61bfb4b036f0aea5/README.md); [session management](https://github.com/unclecode/crawl4ai/blob/888299fb5f0b82181897dc0e61bfb4b036f0aea5/docs/md_v2/advanced/session-management.md).
- **browser-use:** distinguish its Python autonomous `Agent` from its deterministic actor/CDP API. At this pin the **CLI is backed by Browser Harness**, with `browser-harness==0.1.13` in dependencies; legacy CLI tutorials are not a current command contract. The actor can perform `goto/evaluate/get_elements_by_css_selector` without a model, but that buys browser plumbing rather than ready-made product adapters. Local Ollama is an inference option, not zero compute cost. [CLI source](https://github.com/browser-use/browser-use/blob/2cc71890e65056b67fdb29d98bb407749c15bb08/browser_use/cli.py); [dependency manifest](https://github.com/browser-use/browser-use/blob/2cc71890e65056b67fdb29d98bb407749c15bb08/pyproject.toml); [actor API](https://github.com/browser-use/browser-use/blob/2cc71890e65056b67fdb29d98bb407749c15bb08/skills/open-source/references/actor.md).
- **Stagehand:** separate the local browser driver from model-powered `act/observe/extract` and hosted Browserbase. v4 supports local profile directories and CDP attach, so a cloud API is not mandatory for local browser control. A model/gateway credential is still required for ordinary provider-backed natural-language calls; local/custom model routing is possible but must be validated against the selected v4 configuration. Do not call it a free autonomous agent just because the SDK is MIT. [v4 browser](https://github.com/browserbase/stagehand/blob/63078cf85ddfe189da88204539ec30d41959378b/packages/docs/v4/configuration/browser.mdx); [v4 model routing](https://github.com/browserbase/stagehand/blob/63078cf85ddfe189da88204539ec30d41959378b/packages/docs/v4/configuration/models.mdx).
- **Firecrawl:** MIT SDK reuse against a hosted service is legally/operationally distinct from embedding or self-hosting its AGPL server. Neither SDK license nor “no model needed for scrape” makes the server permissive-only or hosted service free. The `firecrawl-cli/README.md` here is a pointer to another repository, not its implementation; no exact external CLI contract was verified. [CLI pointer](https://github.com/firecrawl/firecrawl/blob/2b68c4c56efc54ab10229cd2f992d1f1e71961f9/firecrawl-cli/README.md); [self-host](https://github.com/firecrawl/firecrawl/blob/2b68c4c56efc54ab10229cd2f992d1f1e71961f9/SELF_HOST.md).

## Proposed china-deals boundary (design only)

1. **Dependency layer:** pin OpenCLI package/release integrity, effective adapters and compatible extension; keep transport upstream. Start with one explicit logged-in profile, with one request queue per profile/site. This prevents concurrent navigation from corrupting a shared page.
2. **Read-only capability layer:** permit only reviewed site/action combinations; construct argv arrays, enforce timeouts and bounded stdout/stderr, and reject arbitrary shell text. Browser cookies stay with the profile owner; records use a non-secret profile alias.
3. **Evidence layer:** retain retrieval timestamp, source URL/ID, exact argv excluding secrets, exit status, stdout/stderr, upstream package/commit and adapter hashes, selected profile alias, and raw JSON before normalization. Keep source claims separate from inferred/normalized fields.
4. **Normalization layer:** map each actual adapter contract explicitly. Preserve displayed price/currency and original strings; represent parsed numeric price separately with provenance. Preserve original image/source links. An unknown ID, currency, availability or price stays unknown; no checkout/tax/shipping inference from listing text.
5. **Failure layer:** classify login, verification, throttling, parse drift and genuine empty results separately. Pause on challenge/rate limit; surface the official page for a future user-driven renewal. Do not rotate accounts, silently switch browser fingerprints or retry through another tool to defeat the pause.
6. **Optional fallback layer:** a separately versioned Scrapling parser/browser session only for a demonstrated gap. It must report its own backend/provenance and must not convert a blocked OpenCLI response into an apparent successful empty feed.
7. **Optional AI layer:** downstream summarization/ranking can be a local model or omitted entirely. Site collection stays deterministic; Bilibili subtitle/summary text is labeled by source and track type. This meets “no mandatory AI API” without making the extraction path depend on model availability.

Suggested application result fields (a **proposed wrapper**, not an existing upstream or implemented interface): `schema_version,ok,site,action,source_id,source_url,observed_at,backend,backend_version,adapter_sha256,profile_alias,raw_ref,items,error`. Keep raw receipts immutable so a schema/selector fix can be reviewed against retained evidence without replaying site requests.

## Operational budget and acceptance gaps

There is no mandatory model/API token bill for the recommended local OpenCLI path. There are still Chrome RAM/CPU, a running workstation/worker, network/storage and human session-renewal costs. Taobao search deliberately waits 2+8 seconds plus three scrolling delays (2 seconds each), with additional page polling possible; JD search waits 5 seconds plus scrolling and polling; Xianyu search limits API pagination to at most two 30-row pages for its 60-item cap. These are **source wait budgets, not measured end-to-end latency or a safe throughput target**. [Taobao search](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/clis/taobao/search.js); [JD search](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/clis/jd/search.js); [Xianyu search](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/clis/xianyu/search.js).

Costs are best compared as:

- OpenCLI/Scrapling: local worker/browser + storage + adapter maintenance; no required hosted bill.
- Agent-Reach: same classes of cost plus Python/upstream CLI management and overlapping session/bridge lifecycles; optional speech-to-text calls require Groq/OpenAI credentials and usage.
- browser-use/Stagehand agents: local/cloud browser **plus** model inference. Local inference exchanges API fees for hardware and latency; managed browsers add session/network charges.
- Crawl4AI: local browser crawling/index storage/selector work; optional inference and optional cloud credits.
- Firecrawl: hosted credits or a multi-service self-hosted stack, plus model cost for AI features; self-hosting does not remove the server license issue.

Browser-use's pinned README advertises cloud browsers from **$0.02/browser-hour plus network traffic**; that is a dated upstream price claim, not a current quotation or complete cost estimate. No hosted price plans were purchased or validated here. For this scope, avoid a SaaS dependency until measured local reliability/volume makes it worthwhile. [Browser-use cost statement](https://github.com/browser-use/browser-use/blob/2cc71890e65056b67fdb29d98bb407749c15bb08/README.md#L160-L172); [Reach optional STT](https://github.com/Panniantong/Agent-Reach/blob/14c213405669414492bda0f8d52cc6531d062c45/README.md).

Before accepting an implementation, the authorized implementation owner still needs to choose a released package/extension pair, lock all transitive licenses/integrity, and run user-authorized read-only canaries against the four actual sites. Validate success, expired login, security verification, real empty search, price/ID pairing, Bilibili missing/wrong-language subtitles and browser restarts. In particular, verify JD image availability and ensure `ok:true,data:[]` is not silently treated as proof of no listings.

**Evidence achieved:** pinned source/metadata/license comparison; exact source-derived command and data contracts; dependency-based architecture recommendation. **Not achieved or claimed:** installed tooling, runtime compatibility, active login, live listing correctness, throughput measurements, production readiness or permission to collect/publish.
