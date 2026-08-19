# shopify-channel-performance

A Claude skill that tells a Shopify merchant which acquisition channels actually produce
revenue, not just traffic. Sessions, conversion rate, orders, revenue and AOV, split by
referring channel, with the interpretation rules that keep those numbers from lying.

No API token, no app creation, no local setup. It runs on the Shopify connector in
claude.ai.

[![License: MIT](https://img.shields.io/badge/license-MIT-B0257A)](LICENSE)
[![ShopifyQL 2026-07](https://img.shields.io/badge/ShopifyQL-2026--07-95BF47)](https://shopify.dev/docs/api/shopifyql)

[![Website](https://img.shields.io/badge/website-sixfit.ai-B0257A)](https://sixfit.ai)
[![Email](https://img.shields.io/badge/email-hello@sixfit.ai-E9D9F8)](mailto:hello@sixfit.ai?subject=shopify-channel-performance)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-SixFit%20AI-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/company/sixfit-ai/)
[![Instagram](https://img.shields.io/badge/Instagram-@sixfit.ai-E4405F?logo=instagram&logoColor=white)](https://www.instagram.com/sixfit.ai)
[![Slack](https://img.shields.io/badge/Slack-join%20community-4A154B?logo=slack&logoColor=white)](https://join.slack.com/t/sixfit-external/shared_invite/zt-469zq1bv8-AhAsIliYSU1S_TYW4AFIlA)

Questions, or the setup did not work? Email [hello@sixfit.ai](mailto:hello@sixfit.ai) or open an
[issue](../../issues).

## Setup

This takes about five minutes and requires no technical background. You do not need to
write code, install anything, or create a Shopify app.

### What you are actually setting up

Three plain-language definitions, so the steps below make sense:

- **Claude** is the AI assistant at [claude.ai](https://claude.ai). You chat with it in a
  browser, the same way you would use ChatGPT.
- **A skill** is a file you upload to Claude that teaches it how to do one specific job
  well. This repository *is* that file. Once uploaded, Claude uses it automatically
  whenever you ask a question about your traffic sources. You never have to "run" it.
- **A connector** is a secure, read-only link between Claude and another service, in this
  case your Shopify store. It lets Claude look up your real numbers instead of guessing.
  You approve it through Shopify's own login screen, so Claude never sees your password.

### Before you start

- A [claude.ai](https://claude.ai) account, logged in **in a web browser on a computer**.
  The Skills and Connectors settings are not available in the mobile app.
- A Shopify store you are the owner or staff member of, with permission to view analytics.
- Custom skills and connectors are features of Claude's paid plans. If you do not see the
  menus described below, check your plan under **Settings → Account**.

### Step 1 — Download the skill file

At the top of this page, click **`shopify-channel-performance.skill`**, then click the
**Download** button. Save it somewhere you can find again, such as your Downloads folder.

Do not unzip, rename, or open the file. Claude expects it exactly as downloaded.

### Step 2 — Turn on code execution

Claude cannot load any skill until this setting is on.

1. Go to [claude.ai](https://claude.ai) and log in.
2. Click your **name or profile picture** in the bottom-left corner, then **Settings**.
3. Open the **Capabilities** section.
4. Turn on **Code execution and file creation**.

If this is off, the skill will appear to upload correctly but will never actually run.

### Step 3 — Upload the skill

1. Still in Claude, open **Settings → Capabilities → Skills**. (Depending on your version
   of the interface, this may appear under **Customize → Skills**.)
2. Click **Upload skill**.
3. Select the `shopify-channel-performance.skill` file you downloaded in Step 1.
4. Confirm that **shopify-channel-performance** now appears in your list of skills and is
   switched on.

Skills are per user. Uploading it to your account does not add it for your colleagues, and
each person who wants it uploads their own copy.

### Step 4 — Connect your Shopify store

1. In Claude, open **Settings → Connectors**.
2. Find **Shopify** in the list and click **Connect**.
3. A Shopify window opens. Log in if asked, then choose the store you want to analyze.
4. Review the permissions Shopify shows you and click **Install** or **Authorize**.
5. You are returned to Claude, and Shopify now shows as connected.

The connector holds **one store at a time**. If you manage several stores, you analyze one,
then reconnect to switch to another.

### Step 5 — Check that it worked

Start a new chat and ask:

> Which channel actually made me money last month?

A correct setup looks like this: Claude first names the store it is connected to, then
shows a chart or table of your real numbers, then explains what they mean.

If instead it answers in general terms without naming your store or showing figures, one of
the steps above did not take effect. Work back through this checklist:

| Symptom | Most likely cause |
| --- | --- |
| Claude gives generic advice, no numbers | The store is not connected (Step 4) |
| Claude says it cannot find the skill | Code execution is off (Step 2) |
| Numbers belong to a different shop | A different store is authorized (Step 4) |
| The Skills or Connectors menu is missing | Plan does not include them, or you are on mobile |

Still stuck? Email [hello@sixfit.ai](mailto:hello@sixfit.ai) or open an
[issue](../../issues) and describe which step failed.

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
