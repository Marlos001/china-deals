# Third-party components and research sources

`china-deals` is original MIT-licensed orchestration, normalization and estimation code. It does not vendor the projects below. External programs keep their own licenses and terms.

- **OpenCLI** — [jackwener/OpenCLI](https://github.com/jackwener/OpenCLI/tree/97dc0cd5214b9602bcda78d7422f231ee8a803e9), Apache-2.0; optional external runtime dependency `@jackwener/opencli@2.0.2`. Search/detail commands and output contracts are used through a subprocess. No upstream source is copied into this package. [License](https://github.com/jackwener/OpenCLI/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/LICENSE).
- **Agent-Reach** — [Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach/tree/14c213405669414492bda0f8d52cc6531d062c45), MIT; research inspiration. No runtime dependency or copied source. [License](https://github.com/Panniantong/Agent-Reach/blob/14c213405669414492bda0f8d52cc6531d062c45/LICENSE).
- **Fansbuy** — [public estimator](https://fansbuy.com/estimates). The unofficial adapter reads the same public calculator endpoints observed on 2026-10-27. No affiliation, API stability guarantee or right to redistribute private customer data is implied. Published test fixtures must be public, credential-free data with provenance.
- **Blibli, Taobao, JD and Goofish** are third-party marketplaces. Their names identify data sources and do not imply endorsement. Their site data, accounts and browser extensions are governed by their respective terms.

Additional candidates in `docs/research/` are evaluated as alternatives, not silently bundled dependencies. Repository availability without a license does not authorize copying.
