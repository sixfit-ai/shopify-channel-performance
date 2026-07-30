---
name: shopify-channel-performance
description: Analyze Shopify performance by acquisition channel — sessions, conversion rate, AOV and revenue per referrer or UTM — using ShopifyQL on the Admin GraphQL API.
---

# Shopify channel performance

Answers "which acquisition channel is working?" from Shopify's own analytics engine
(`shopifyqlQuery` on the Admin GraphQL API — the same data behind Admin → Analytics → Reports).

Shopify holds no ad spend, so **CAC and ROAS are out of scope**. This skill covers sessions,
conversion rate, orders, revenue, AOV, margin and new-vs-returning split per channel.

## Setup

One-time, by the merchant:

1. Shopify Admin → Settings → Apps and sales channels → **Develop apps** → Create an app.
2. Configuration → Admin API integration → grant **`read_reports`**.
3. Install the app, then reveal and copy the **Admin API access token** (`shpat_…`, shown once).
4. Export both:

```sh
export SHOPIFY_STORE=my-shop.myshopify.com
export SHOPIFY_ADMIN_TOKEN=shpat_...
```

Then run any query through the bundled script, which prints CSV:

```sh
python3 shopifyql.py "FROM sales SHOW total_sales SINCE -30d UNTIL today"
```

Requires Level 2 protected customer data access, which for admin-created custom apps is
plan-dependent rather than review-dependent. Admin-created custom apps also get
`read_all_orders`, so there is no 60-day history cliff.

## Query recipes

Start with recipe 0, then 1. Everything else is a drill-down on what 1 shows.

### 0. Taxonomy hygiene — run this before ranking anything

```
FROM sessions
  SHOW sessions
  GROUP BY utm_source
  SINCE -90d UNTIL today
  ORDER BY sessions DESC
  LIMIT 50
```

Scan the output for the same source spelled several ways (`Facebook` / `facebook` / `fb` /
`FB_ads`). Fragmented UTM tagging is the most common reason a channel looks weak, and it
invalidates every ranking below until it is accounted for.

### 1. Channel scorecard

```
FROM sales, sessions
  SHOW sessions, conversion_rate, orders, total_sales, average_order_value
  GROUP BY referring_channel
  SINCE -30d UNTIL today
  ORDER BY total_sales DESC
```

The one table: traffic, conversion, volume and basket size per channel.

### 2. UTM drill-down

```
FROM sales, sessions
  SHOW sessions, conversion_rate, orders, total_sales
  WHERE referring_channel = 'Social'
  GROUP BY utm_source, utm_medium, utm_campaign
  SINCE -30d UNTIL today
  ORDER BY total_sales DESC
  LIMIT 25
```

Where inside a channel the revenue actually comes from. Swap the `WHERE` value for whichever
channel recipe 1 flagged.

### 3. Trend and momentum

```
FROM sales, sessions
  SHOW sessions, orders, total_sales
  WHERE referring_channel = 'Search'
  TIMESERIES week
  SINCE -90d UNTIL today
  COMPARE TO previous_period
```

Is this channel decaying or did it have one bad week? A level read from recipe 1 cannot tell
the difference.

### 4. Campaign level, with attribution models

```
FROM campaign_sessions, campaign_sales
  SHOW campaign_sessions,
       campaign_conversion_rate,
       campaign_last_click_order_count,
       campaign_last_click_total_sales,
       campaign_first_click_total_sales,
       campaign_linear_total_sales
  GROUP BY utm_campaign, utm_source
  SINCE -30d UNTIL today
  ORDER BY campaign_last_click_total_sales DESC
  LIMIT 25
```

The `campaign_*` schemas are the only place Shopify exposes first-click and linear attribution.
A campaign whose first-click sales dwarf its last-click sales is an awareness driver being
undercounted everywhere else in this skill.

### 5. New vs returning by channel

```
FROM sales
  SHOW orders, total_sales, average_order_value
  GROUP BY referring_channel, new_or_returning_customer
  SINCE -90d UNTIL today
  ORDER BY total_sales DESC
```

Separates acquisition from re-engagement. Email and Direct usually collapse to mostly
returning — that is retention revenue, not channel performance.

### 6. Margin by channel

```
FROM sales
  SHOW total_sales, cost_of_goods_sold, gross_profit, gross_margin
  GROUP BY referring_channel
  SINCE -90d UNTIL today
  ORDER BY gross_profit DESC
```

Needs cost-per-item filled in on products. For landed cost (shipping, duties, adjustments) use
the `profitability` schema, which carries `referring_channel` and `order_utm_*` but exposes
per-order averages rather than totals.

## Interpretation

Reporting the ranking is not the job. These are the things that make a ranking wrong:

- **`referring_channel` and `utm_source` are different taxonomies.** The first is Shopify's
  bucketing of the referrer; the second is raw merchant-controlled text. Never sum them
  together or compare a number from one against a number from the other.
- **Attribution is last-click on a 30-day window** by default. Recipe 4 is the only escape.
- **Direct / Unknown is a residual, not a channel.** It absorbs dark traffic, in-app browser
  referrers, apps that strip the referrer, and untagged links. Report it as *unattributed*
  with its share of sessions and revenue. Never call it the top performer.
- **Sessions and sales are stamped at different times.** A session on day 1 that converts on
  day 5 lands in a day-1 sessions row and a day-5 sales row. Day-level joined conversion rate
  is therefore approximate — use windows of **28 days or more** for channel CVR, and treat
  daily CVR as directional only.
- **Low-session channels are noise.** A channel with 40 sessions and 2 orders is not a 5% CVR,
  it is two orders. Say so rather than ranking it.
- **No CAC, no ROAS.** Shopify has no ad spend. If asked, say that plainly and offer revenue,
  CVR and margin per channel instead of estimating.

## Schema discovery

The recipes above were written against ShopifyQL `2026-07`. Fields churn between versions —
confirm rather than trust:

- Syntax: <https://shopify.dev/docs/api/shopifyql.txt>
- All schemas: <https://shopify.dev/docs/api/shopifyql/latest/schemas>
- One schema: `…/latest/schemas/<category>/<name>.md`, e.g.
  `…/latest/schemas/sessions_and_behavior/sessions.md`

A `parseErrors` response means **look up the schema**, not guess again. Two rules that cause
most of them:

- Multi-schema `FROM a, b` requires every `GROUP BY` field to exist **with the same name in
  both schemas**. If a join errors, run the two schemas as separate queries and merge.
- Clause order is fixed: `FROM … SHOW … WHERE … GROUP BY … TIMESERIES … WITH … HAVING …
  SINCE/UNTIL/DURING … COMPARE TO … ORDER BY … LIMIT … VISUALIZE`. There is no `last_30d`
  keyword — `DURING` takes named ranges (`last_month`, `this_quarter`); use
  `SINCE -30d UNTIL today` for rolling windows.

## Known limits

First-touch attribution and per-channel LTV cohorts are **not** answerable from ShopifyQL
outside the `campaign_*` schemas. The only general route is `Order.customerJourneySummary` on
the Admin GraphQL API (`firstVisit`/`lastVisit` → `source`, `utmParameters`, `referrerUrl`,
plus `daysToConversion` and `customerOrderIndex`), which requires walking orders one by one.
That is out of scope here — say so rather than approximating it with last-click numbers.
