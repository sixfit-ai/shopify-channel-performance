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

## Requirements

`shopifyqlQuery` is gated by three separate things. All three must be satisfied, and the first
two are not enough on their own.

| Requirement | Where it lives |
| --- | --- |
| `read_reports` access scope | App configuration, Admin API access scopes |
| Level 2 protected customer data access | App configuration, Protected customer data access |
| Store plan: Shopify, Advanced, or Plus | Store settings, Plan |

**Development stores cannot run this skill.** Level 2 protected customer data access covers
customer name, address, phone and email, and Shopify only offers it on Shopify, Advanced and
Plus. On a Basic plan or a development store the setting is not merely off, it is not shown at
all, and the store settings display an upgrade prompt in its place. Every query returns
`ACCESS_DENIED` regardless of how the app is configured.

This is worth knowing before you spend an afternoon on setup. Point the skill at a store that
is already on a qualifying plan.

## Setup

**1. Create an app with a token.**

As of January 1, 2026 merchants can no longer create legacy custom apps. Two routes remain:

- Partner-owned development stores still expose **Settings → Apps and sales channels → Develop
  apps → Allow legacy custom app development**. This yields a long-lived `shpat_` token straight
  from the admin UI and is the shorter path.
- Otherwise build the app in the Dev Dashboard and mint a token through the client credentials
  grant. Those tokens are `shpua_` prefixed and **expire after 24 hours**, so anything
  long-running needs to refresh them.

**2. Grant the scope.** App → Configuration → Admin API integration → Configure → `read_reports`
→ Save.

**3. Grant Level 2 protected customer data.** App → Configuration → Protected customer data
access. Request access, then also tick the individual protected customer fields (name, email,
phone, address). Granting the top-level access without the field-level boxes is not sufficient.
Admin-created custom apps are not subject to Shopify review, so this takes effect on save.

**4. Install and copy the token.** Permission changes do not propagate to an already-issued
token. If you change scopes after installing, uninstall and reinstall the app and take the new
token.

```
export SHOPIFY_STORE=my-shop.myshopify.com
export SHOPIFY_ADMIN_TOKEN=shpat_...
```

**5. Install the skill.** Drop the folder into `~/.claude/skills/` (or your project's
`.claude/skills/`) and ask Claude about channel performance. `SKILL.md` and `shopifyql.py` must
sit at the root of that folder, not in a nested subdirectory.

## Verifying the install

```
python3 shopifyql.py --selftest   # offline, no network, no credentials
```

Then the smallest possible live query:

```
$ python3 shopifyql.py "FROM sales SHOW total_sales SINCE -30d UNTIL today"
total_sales
0
```

**A header row is the success condition.** If you see comma-separated column names, the token
was accepted, the scopes cleared, the query parsed, and the CSV writer ran. Zeroes underneath
mean the store has no data in the window, which is a property of the store and not a failure of
the skill. A store with no orders is a perfectly good way to confirm the plumbing works.

Failure looks different: no header at all, and a `GraphQL errors:` or `ShopifyQL parse errors:`
block on stderr with a non-zero exit.

## Example

```
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

Figures above are illustrative. The skill's job is what comes next: Direct is a residual bucket
and not a channel; Social's CVR is a sixth of Search's on comparable traffic; Email is retention
revenue rather than acquisition.

Empty cells are normal. Shopify returns an empty string rather than zero for metrics it cannot
compute, so `average_order_value` on a channel with no orders leaves the row ending in a comma.

Query errors exit non-zero with `parseErrors` on stderr, so a typo never reads as an empty
result set.

## Troubleshooting

**`ACCESS_DENIED` naming `read_reports` and Level 2 customer data.** The scope is probably fine
and the plan is the real blocker. Check the store plan first, then the field-level protected
customer data boxes, then reinstall for a fresh token. See Requirements above.

**`No such type X` or `Field 'y' doesn't exist on type 'Z'`.** A GraphQL shape mismatch, not a
permissions problem. The request reached Shopify and authenticated fine. The response shape this
script targets is:

```graphql
shopifyqlQuery(query: $q) {
  tableData { columns { name } rows }
  parseErrors
}
```

`tableData` and `parseErrors` are plain fields on `ShopifyqlQueryResponse`, not members of a
union, so there is no inline fragment. `rows` is a `JSON` scalar keyed by column name.
`parseErrors` is a flat list of strings.

**`shop_not_permitted` when minting a Dev Dashboard token.** The app is not installed on that
store.

**Header row but every value empty or zero.** Working as intended on a store with no data in
the window. Widen the range or point at a store with traffic.

## Limitations

- **No CAC, no ROAS.** Shopify holds no ad spend. Out of scope by design, not an oversight.
- **Last-click, 30-day window.** First-click and linear attribution exist only in the
  `campaign_sales` schema (recipe 4).
- **No first-touch attribution or per-channel LTV cohorts.** That needs
  `Order.customerJourneySummary`, walked order by order, which is not in v1.
- **Joined conversion rate is approximate below roughly 28-day windows.** Sessions are stamped
  at session time, sales at order time.
- **UTM data cannot be synthesised for testing.** Sessions are populated by the storefront's own
  analytics on real browser visits. There is no API to write them, and orders created through
  the Admin API carry no attribution. A campaign is stamped on the first page view of a session,
  so any interstitial that redirects before the UTM-bearing URL loads, a storefront password
  page for instance, causes the visit to land as Direct.

Written against ShopifyQL `2026-07`. Fields churn between versions; the skill tells Claude to
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
Three things, all required. A Shopify app with the `read_reports` scope, Level 2 protected
customer data access with the individual protected fields ticked, and a store on the Shopify,
Advanced or Plus plan. Basic plans and development stores cannot run it at all: Level 2 access
is not offered on those plans, so every query returns `ACCESS_DENIED`. The Admin API access
token is exported as an environment variable. See Requirements above.

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
