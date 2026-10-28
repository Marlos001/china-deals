# china-deals

Research marketplace listings and estimate the cost of bringing a purchase to Brazil, from your terminal.

china-deals searches Taobao, Tmall, 1688, Weidian, JD.com, Goofish (Xianyu), Blibli, Alibaba.com and AliExpress. It helps you compare product details and prices, estimate Fansbuy shipping, and work through import costs. It is read-only: it does not place orders, contact sellers or make payments.

Guest access is the default, so you can get started without a marketplace account or AI API key. You can also use the CLI with a coding agent for translation and analysis; the CLI itself makes no AI calls.

## Install

You need Python 3.11 or later. The default HTTP guest mode has no runtime dependencies.

```sh
uv tool install git+https://github.com/Marlos001/china-deals.git
```

Or install in a virtual environment with pip:

```sh
pip install git+https://github.com/Marlos001/china-deals.git
```

## Get started

Search a few marketplaces for a product:

```sh
china-deals search 'ROG Zephyrus G16' --zh-query '华硕 ROG 幻16 笔记本' \
  --markets taobao,jd,goofish --limit 5
```

Chinese marketplaces require a query containing Chinese characters. Use `--zh-query` as above, or pass a Chinese query directly. English queries work for Alibaba.com and AliExpress. Use `china-deals marketplaces` to see the available sources.

Read a specific listing using its marketplace ID or URL:

```sh
china-deals detail jd 100214660452
```

This JD listing is a research example, not a recommendation; its price was masked when last checked. Output is JSON by default. Add `--format markdown` for a shorter report, or run `china-deals --help` to explore the commands.

## Estimate shipping and import costs

For a China-origin parcel, provide its packed weight, dimensions and applicable categories:

```sh
china-deals shipping --market jd --weight-g 1000 --dimensions-cm 20 20 15 \
  --ordinary-goods --format markdown
```

Use `--ordinary-goods` only when no special categories apply. For example, electronics and batteries have separate category flags. Shipping quotes are estimates; final packing, fees and Brazilian taxes can change the total. Alibaba.com and AliExpress shipping must be entered manually; Fansbuy support for those marketplaces is not assumed. Blibli is in Indonesia and is excluded from Fansbuy freight by default.

To estimate landed cost, supply your own exchange rates, freight and ICMS rate:

```sh
china-deals estimate --goods-cny 300 --freight-cny 168.75 \
  --cny-brl 0.75 --usd-brl 5.40 --icms-rate 0.20
```

These numbers are examples, not current rates or a tax determination. See the [shipping and import guide](docs/REFERENCE.md#fansbuy--brazil-and-truthful-declarations) for assumptions, categories and limitations. Use the actual transaction value and an accurate description for customs.

## What to expect from results

Marketplace access and prices can change. A search result may be an indexed lead rather than a current offer; a product page may be blocked, show a masked price or omit the exact variant. Check source links, timestamps and warnings before comparing prices. An empty or blocked result does not mean a product is unavailable.

The tool does not verify stock, seller authenticity, checkout prices or import clearance. Estimates and coupon eligibility depend on the information you supply. See the [validation reports](docs/validation/README.md) for what has and has not been verified.

## More ways to use it

- [Full reference](docs/REFERENCE.md): search options, filters, price history, coupons, browser backends and cost calculations.
- [Agent guide](docs/AGENT_GUIDE.md): use a terminal-capable agent to translate queries and interpret results.
- [Fresh data guide](docs/FRESH_DATA.md): refresh listings and compare import scenarios with Brazilian offers.
- [Research index](docs/research/README.md): sources, marketplace access and Brazil import policy.
- [Automotive buying guide](docs/research/audi-a4-b9-ambiente-2018-2019-buying-guide.md): an Audi A4 research example. Product plans can help with terminology and fitment checks; they do not certify compatibility.

## Development

```sh
git clone https://github.com/Marlos001/china-deals.git
cd china-deals
uv run python -m unittest discover -s tests -v
```

See the [contributing guide](CONTRIBUTING.md) for setup and pull requests, and [validation](docs/VALIDATION.md) for the scope of the checks.

## License

Released under the [MIT License](LICENSE). You can use, modify and share the project, including commercially, as long as you retain the copyright and license notice. See [third-party notices](THIRD_PARTY.md) for external tools and data sources.
