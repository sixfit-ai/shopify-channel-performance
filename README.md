# shopify-channel-performance

A Claude skill for untangling Shopify performance per acquisition channel: sessions,
conversion rate, orders, revenue, AOV, margin and new-vs-returning, split by referrer or UTM.

It is a set of validated ShopifyQL recipes plus the interpretation rules that keep the numbers
from lying to you, and one stdlib-only Python script to run them.

[![License: MIT](https://img.shields.io/badge/license-MIT-B0257A)](LICENSE)
[![ShopifyQL 2026-07](https://img.shields.io/badge/ShopifyQL-2026--07-95BF47)](https://shopify.dev/docs/api/shopifyql)

[![Website](https://img.shields.io/badge/website-sixfit.ai-B0257A)](https://sixfit.ai)
[![Email](https://img.shields.io/badge/email-hello@sixfit.ai-E9D9F8)](mailto:hello@sixfit.ai?subject=shopify-channel-performance)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-SixFit%20AI-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/company/sixfit-ai/)
[![Instagram](https://img.shields.io/badge/Instagram-@sixfit.ai-E4405F?logo=instagram&logoColor=white)](https://www.instagram.com/sixfit.ai)
[![Slack](https://img.shields.io/badge/Slack-join%20community-4A154B?logo=slack&logoColor=white)](https://join.slack.com/t/sixfit-external/shared_invite/zt-469zq1bv8-AhAsIliYSU1S_TYW4AFIlA)

Questions, or the setup did not work? Email [hello@sixfit.ai](mailto:hello@sixfit.ai) or open an
[issue](../../issues).

## Why not Storefront MCP

The obvious question. Storefront MCP is an unauthenticated **buyer-facing** server. Its entire
tool set is `search_catalog`, `lookup_catalog`, `get_product`, `search_shop_policies_and_faqs`,
and the deprecated `get_cart` / `update_cart`. No orders, no sessions, no revenue, no
attribution. There are no merchant analytics on that surface at all.

The data lives behind `shopifyqlQuery` on the Admin GraphQL API, which is what this skill uses.

## Setup

In Shopify Admin: Settings → Apps and sales channels → **Develop apps** → create an app, grant
**`read_reports`**, install it, copy the Admin API access token.

```sh
export SHOPIFY_STORE=my-shop.myshopify.com
export SHOPIFY_ADMIN_TOKEN=shpat_...
```

Drop the folder into `~/.claude/skills/` (or your project's `.claude/skills/`) and ask Claude
about channel performance.

## Example

```sh
$ python3 shopifyql.py "FROM sales, sessions
    SHOW sessions, conversion_rate, orders, total_sales, average_order_value
    GROUP BY referring_channel
    SINCE -30d UNTIL today
    ORDER BY total_sales DESC"

referring_channel,sessions,conversion_rate,orders,total_sales,average_order_value
Direct,18402,0.0121,223,19844.50,88.99
Search,11250,0.0208,234,21730.00,92.86
Social,9871,0.0061,60,4102.75,68.38
Email,2140,0.0794,170,17255.30,101.50
```

The skill's job is what comes next: Direct is a residual bucket, not a channel; Social's CVR is
a sixth of Search's on comparable traffic; Email is retention revenue, not acquisition.

Query errors exit non-zero with `parseErrors` on stderr, so a typo never reads as an empty
result set.

```sh
python3 shopifyql.py --selftest   # offline check, no network
```

## Limitations

- **No CAC, no ROAS.** Shopify holds no ad spend. Out of scope by design, not an oversight.
- **Last-click, 30-day window.** First-click and linear attribution exist only in the
  `campaign_sales` schema (recipe 4).
- **No first-touch attribution or per-channel LTV cohorts.** That needs
  `Order.customerJourneySummary`, walked order by order, which is not in v1.
- **Joined conversion rate is approximate below roughly 28 day windows.** Sessions are stamped
  at session time, sales at order time.

Written against ShopifyQL `2026-07`. Fields churn between versions, so the skill tells Claude to
verify against the schema reference rather than trust the recipes verbatim.

## FAQ

**What is shopify-channel-performance?**
An open source Claude skill that analyzes Shopify performance by acquisition channel. It queries
your store's own analytics through ShopifyQL on the Admin GraphQL API and reports sessions,
conversion rate, orders, revenue, AOV, margin and new-vs-returning per referring channel or UTM.

**Can it calculate ROAS or CAC?**
No. Shopify holds no ad spend, so the numbers are not there to calculate from. The skill says so
rather than estimating.

**Why is Direct at the top of my channel report?**
Because Direct is a residual bucket, not a channel. The skill reports it as unattributed rather
than crowning it.

**Do I need to know ShopifyQL to use it?**
No. You ask in plain English. The recipes exist so Claude starts from validated syntax instead
of inventing queries.

**What permissions does it need?**
A Shopify custom app with the `read_reports` scope, and the Admin API access token exported as
an environment variable.

**Is my Admin API token sent anywhere?**
No. The script reads it from your environment and posts directly to your own
`*.myshopify.com` Admin GraphQL endpoint. There is no third party service in the path and no
dependencies outside the Python standard library.

**Which attribution model does it use?**
Last-click on a 30 day window by default. First-click and linear attribution are available only
through the `campaign_sales` schema in recipe 4.

**What ShopifyQL version is it written against?**
`2026-07`. Fields change between versions, so the skill verifies against the live schema
reference rather than trusting the recipes verbatim.

## Contact

- Email: [hello@sixfit.ai](mailto:hello@sixfit.ai)
- Website: [sixfit.ai](https://sixfit.ai)
- LinkedIn: [SixFit AI](https://www.linkedin.com/company/sixfit-ai/)
- Instagram: [@sixfit.ai](https://www.instagram.com/sixfit.ai)
- Slack: [Join our community](https://join.slack.com/t/sixfit-external/shared_invite/zt-469zq1bv8-AhAsIliYSU1S_TYW4AFIlA)

## License

MIT
