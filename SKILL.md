---
name: shopify-channel-performance
description: Analyze which acquisition channels actually make a Shopify store money, using ShopifyQL through the connected Shopify store. Use this skill whenever a merchant asks where their customers or traffic come from, which channel or platform is worth the money, whether their ads, Instagram, TikTok, email, or Google traffic is paying off, why they get lots of visitors but few sales, which channel has the best or worst conversion rate, or any question comparing traffic sources against orders and revenue. Trigger it even when the merchant never says the word "channel" or "attribution", and even when they phrase it casually, for example "is Instagram even worth it", "where are my customers coming from", "my ads aren't working", or "lots of traffic no sales".
---

# Shopify Channel Performance

Answer the question a merchant is really asking: not how many visitors each source sent,
but which source turned into orders and revenue.

The data comes from ShopifyQL through the `run-analytics-query` tool on the connected
Shopify store. The tool renders results as a chart widget the merchant can already see.
Your job is not to restate the table. Your job is the interpretation that follows it.

## Before you query

**1. Confirm which store is connected.** Call `get-shop-info` first and name the store in
your reply. The connector holds one store at a time and the merchant may have connected a
different one than they assume. A report built on the wrong store looks completely normal
and nobody catches it.

**2. Disambiguate "channel" if the question is ambiguous.** The word means two different
things in Shopify and merchants use it for both:

- **Acquisition channel**, where the visitor came from before landing on the store:
  search, social, email, direct, referral. This skill covers this one.
- **Sales channel**, the surface where the sale happened: Online Store, POS, Shop app,
  Instagram checkout. This is a different query and different fields.

If the merchant mentions a physical store, POS, retail, or in person sales, ask which one
they mean before running anything. Otherwise assume acquisition and say so in one short
line, so a merchant who meant the other thing can correct you.

**3. Note the reporting window.** Default to the last 30 days. Attribution is last click
with a 30 day window, so shorter windows get noisier, not sharper.

## Recipes

Field names change between ShopifyQL versions. If a query returns a parse error, do not
guess replacement fields. Use the example queries in the `run-analytics-query` tool
description as the source of truth for valid table and column names, then retry.

### Recipe 1: Channel overview

The default answer to "which channel makes me money".

```
FROM sales, sessions
SHOW sessions, conversion_rate, orders, total_sales, average_order_value
GROUP BY referring_channel
SINCE -30d UNTIL today
ORDER BY total_sales DESC
```

### Recipe 2: Named referrer detail

Use when Recipe 1 shows a channel worth breaking open, for example social is large but
converting badly and the merchant needs to know whether that is Instagram or TikTok.

```
FROM sales
SHOW orders, total_sales
GROUP BY order_referrer_source, order_referrer_name
SINCE -30d UNTIL today
ORDER BY total_sales DESC
```

### Recipe 3: Funnel by channel

Use when a channel sends real traffic but few orders, to locate where the drop happens.

```
FROM sessions
SHOW sessions, sessions_with_cart_additions, sessions_that_reached_checkout,
     sessions_that_completed_checkout, conversion_rate
GROUP BY referring_channel
SINCE -30d UNTIL today
```

### Recipe 4: Trend against the previous period

Use when the merchant says something got worse, to check whether it actually did.

```
FROM sales
SHOW total_sales, orders
TIMESERIES week
SINCE -90d UNTIL today
COMPARE TO previous_period
```

## Interpretation rules

These are the point of the skill. Apply them every time.

**Direct is not a channel.** It is the residual bucket for every session whose origin
could not be determined: typed URLs, but also untagged email, messaging apps, QR codes,
and stripped referrers. A large direct share is a measurement gap, not a loyal audience.
If direct exceeds roughly 40 percent of sessions, say so and point at UTM tagging as the
fix. Never congratulate a merchant on strong direct traffic.

**Group raw referrer names into channels before presenting.** Live data returns lowercase
source names like `bing`, `facebook`, `direct`, not tidy buckets. Roll them up
(`google` and `bing` into search, `facebook`, `instagram`, and `tiktok` into social) and
show the buckets. Keep the long tail out of the summary unless one entry is material.

**Zero orders means undefined, not zero.** When a channel has no orders, conversion rate
and average order value are undefined and the tool may return blank cells for them. Never
report a blank money cell as 0.00 and never rank a channel on it. Say the channel has no
sales in the window.

**Sessions without orders is the interesting case, not an error.** A store with traffic
and no orders has a conversion problem or a store that is not live yet. Say which you
think it is and why. Do not produce a channel ranking from a table where every channel
has zero revenue.

**Email is retention, not acquisition.** Email traffic is mostly people who already
bought. Its conversion rate will beat every acquisition channel and that comparison is
meaningless. Report it separately and say why.

**Traffic share and revenue share are different rankings.** Lead with revenue. A channel
sending a third of sessions and a twentieth of revenue is the finding worth stating out
loud.

**Small numbers are not signal.** Below roughly 100 sessions or 10 orders in a bucket,
say the sample is too small to act on rather than reporting a conversion rate to two
decimals.

**Joined conversion rate is approximate under about 28 days.** Sessions are stamped at
session time and sales at order time, so short windows misalign. Mention this only if the
merchant asks for a window shorter than that.

## What this cannot tell them

State these plainly when they are relevant, rather than letting the merchant infer a
number that is not there.

- **No ad spend, so no CAC and no ROAS.** Shopify does not hold what was paid to Meta or
  Google. This skill can say a channel produced little revenue. It cannot say a channel
  lost money. That needs ad platform data alongside this.
- **Last click only.** A customer who found the store through Instagram and returned via
  search is credited to search. First touch and multi touch attribution are not available
  here.
- **No per channel lifetime value.** These numbers are one window, not cohort value over
  time.

## Response shape

Keep it short. The merchant is looking at the chart already.

1. One line naming the store and the window.
2. The headline finding, revenue first.
3. One or two caveats from the interpretation rules that actually apply. Not all of them.
4. One concrete next step, tied to a recipe above or to an action outside Shopify.

Do not repeat the table in prose. Do not open with methodology.
