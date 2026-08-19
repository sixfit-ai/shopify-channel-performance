# shopify-channel-performance

A Claude skill that tells a Shopify merchant which acquisition channels actually produce
revenue, not just traffic. Sessions, conversion rate, orders, revenue and AOV, split by
referring channel, with the interpretation rules that keep those numbers from lying.

No API token, no app creation, no local setup. It runs on the Shopify connector in
claude.ai.

## Setup

**1. Enable code execution.** Settings, then Capabilities, then turn on Code execution and
file creation. Skills do not load without it.

**2. Upload the skill.** Customize, then Skills, then upload `shopify-channel-performance.skill`.

**3. Connect the store.** Settings, then Connectors, then Shopify. Authorize the store you
want to analyze.

That is the whole setup. Custom skills on claude.ai are per user, so each merchant uploads
their own copy.

## Usage

Ask in plain language:

- Which channel actually made me money last month?
- Where are my customers coming from?
- Is Instagram worth it?
- I get lots of traffic but nobody buys.

The skill confirms which store is connected, runs the relevant ShopifyQL recipe, and
interprets the result.

## What it corrects for

The table Shopify returns is easy to misread. The skill applies these rules on every run:

- `direct` is a residual bucket for unattributable sessions, not a channel. A large direct
  share is a tagging gap.
- Raw referrer names come back lowercase and ungrouped (`bing`, `facebook`). They are
  rolled into channels before presentation.
- A channel with zero orders has an undefined conversion rate and AOV. The tool can return
  blank cells for these. Blank is never reported as zero.
- Email is retention revenue. Comparing its conversion rate to acquisition channels is
  meaningless and the skill says so.
- Buckets under roughly 100 sessions are flagged as too small to act on.

## Limitations

- **No CAC, no ROAS.** Shopify holds no ad spend. The skill can say a channel produced
  little revenue. It cannot say a channel lost money.
- **Last click, 30 day window.** No first touch or multi touch attribution.
- **No per channel LTV cohorts.**
- **Joined conversion rate is approximate below about 28 day windows.** Sessions are
  stamped at session time, sales at order time.
- **One store at a time.** The connector holds a single authorized store. Switching stores
  means reauthorizing.

## Recipe verification status

Recipe 1 has been run against a live store and returns the expected columns. Recipes 2, 3
and 4 are built from the field names documented in the `run-analytics-query` tool and have
not yet been confirmed against live data. ShopifyQL fields change between versions, so the
skill instructs Claude to treat the tool's own example queries as the source of truth and
retry rather than guess on a parse error.

## Relation to the previous version

This replaces the earlier version, which used a standalone Python script against the Admin
GraphQL API with `SHOPIFY_STORE` and `SHOPIFY_ADMIN_TOKEN` environment variables. That
version required creating a custom app and granting `read_reports` on every store, which
is not a reasonable ask for a merchant. The recipes and interpretation rules carried over.
The script did not.

One thing was lost in the move. The script guaranteed that a query error exited non zero
and never read as an empty result set. Over MCP that guarantee lives in the skill
instructions instead of in code, which is why the data integrity rules are stated
explicitly in `SKILL.md`.

## License

MIT
