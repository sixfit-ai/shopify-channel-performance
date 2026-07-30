# shopify-channel-performance

A Claude skill for untangling Shopify performance per acquisition channel: sessions,
conversion rate, orders, revenue, AOV, margin and new-vs-returning, split by referrer or UTM.

It is a set of validated ShopifyQL recipes plus the interpretation rules that keep the numbers
from lying to you, and one ~60-line stdlib Python script to run them.

## Why not Storefront MCP

The obvious question. Storefront MCP is an unauthenticated **buyer-facing** server — its
entire tool set is `search_catalog`, `lookup_catalog`, `get_product`,
`search_shop_policies_and_faqs`, and the deprecated `get_cart` / `update_cart`. No orders, no
sessions, no revenue, no attribution. There are no merchant analytics on that surface at all.

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

Query errors exit non-zero with `parseErrors` on stderr — a typo never reads as an empty
result set.

```sh
python3 shopifyql.py --selftest   # offline check, no network
```

## Limitations

- **No CAC, no ROAS.** Shopify holds no ad spend. Out of scope by design, not an oversight.
- **Last-click, 30-day window.** First-click and linear attribution exist only in the
  `campaign_sales` schema (recipe 4).
- **No first-touch attribution or per-channel LTV cohorts.** That needs
  `Order.customerJourneySummary`, walked order by order — not in v1.
- **Joined conversion rate is approximate below ~28-day windows.** Sessions are stamped at
  session time, sales at order time.

Written against ShopifyQL `2026-07`. Fields churn between versions; the skill tells Claude to
verify against the schema reference rather than trust the recipes verbatim.

## License

MIT
