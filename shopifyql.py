#!/usr/bin/env python3
"""Run a ShopifyQL query against the Admin GraphQL API, print CSV.

  export SHOPIFY_STORE=my-shop.myshopify.com
  export SHOPIFY_ADMIN_TOKEN=shpat_...
  python3 shopifyql.py "FROM sales SHOW total_sales SINCE -30d UNTIL today"
  echo "FROM sessions SHOW sessions SINCE -7d UNTIL today" | python3 shopifyql.py
"""
import csv
import json
import os
import ssl
import sys
import urllib.error
import urllib.request

API_VERSION = "2026-07"

# shopifyqlQuery returns ShopifyqlQueryResponse. tableData and parseErrors are
# plain fields on it, not members of a union, so there is no inline fragment.
# parseErrors is a list of strings.
QUERY = """query($q: String!) {
  shopifyqlQuery(query: $q) {
    tableData { columns { name } rows }
    parseErrors
  }
}"""


def to_csv(payload, out):
    """payload -> CSV rows on `out`. Returns list of parse error messages."""
    errors = [str(e) for e in (payload.get("parseErrors") or [])]
    if errors:
        return errors

    table = payload.get("tableData") or {}
    names = [c["name"] for c in table.get("columns") or []]
    w = csv.writer(out)
    w.writerow(names)

    for row in table.get("rows") or []:
        if isinstance(row, dict):
            # rows arrive keyed by column name; order by the column list
            w.writerow([row.get(n, "") for n in names])
        else:
            w.writerow(row)
    return []


def main():
    for var in ("SHOPIFY_STORE", "SHOPIFY_ADMIN_TOKEN"):
        if not os.environ.get(var):
            sys.exit(f"{var} is not set. See SKILL.md > Setup.")

    store = os.environ["SHOPIFY_STORE"].strip().rstrip("/")
    for prefix in ("https://", "http://"):
        if store.startswith(prefix):
            store = store[len(prefix):]

    q = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    if not q.strip():
        sys.exit("No query given.")

    req = urllib.request.Request(
        f"https://{store}/admin/api/{API_VERSION}/graphql.json",
        data=json.dumps({"query": QUERY, "variables": {"q": q.strip()}}).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": os.environ["SHOPIFY_ADMIN_TOKEN"].strip(),
        },
    )

    try:
        with urllib.request.urlopen(req) as r:
            body = json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        sys.exit(f"HTTP {e.code} from Shopify: {detail}")
    except urllib.error.URLError as e:
        sys.exit(f"Could not reach {store}: {e.reason}")
    except ssl.SSLError as e:
        sys.exit(f"TLS error talking to {store}: {e}")

    if body.get("errors"):
        sys.exit("GraphQL errors:\n" + json.dumps(body["errors"], indent=2))

    data = (body.get("data") or {}).get("shopifyqlQuery")
    if data is None:
        sys.exit("shopifyqlQuery returned null. Check read_reports scope and plan.")

    errors = to_csv(data, sys.stdout)
    if errors:
        sys.exit("ShopifyQL parse errors:\n" + "\n".join(errors))


def selftest():
    import io

    # fixture mirrors the real 2026-07 response: rows keyed by column name,
    # parseErrors a flat list of strings
    out = io.StringIO()
    assert to_csv(
        {
            "tableData": {
                "columns": [{"name": "referring_channel"}, {"name": "total_sales"}],
                "rows": [
                    {"referring_channel": "Search", "total_sales": "1200.00"},
                    {"referring_channel": "Direct", "total_sales": "800.50"},
                ],
            },
            "parseErrors": None,
        },
        out,
    ) == []
    assert out.getvalue().splitlines() == [
        "referring_channel,total_sales",
        "Search,1200.00",
        "Direct,800.50",
    ], out.getvalue()

    # a missing value must not shift the remaining columns left
    out = io.StringIO()
    to_csv(
        {
            "tableData": {
                "columns": [{"name": "a"}, {"name": "b"}, {"name": "c"}],
                "rows": [{"a": "1", "c": "3"}],
            },
            "parseErrors": None,
        },
        out,
    )
    assert out.getvalue().splitlines()[1] == "1,,3", out.getvalue()

    # a parse error must never look like an empty result set
    errs = to_csv(
        {"tableData": None, "parseErrors": ["Column Not Found: bogus_field"]},
        io.StringIO(),
    )
    assert errs == ["Column Not Found: bogus_field"], errs

    # an empty result set is still a header row, not a crash
    out = io.StringIO()
    assert to_csv(
        {"tableData": {"columns": [{"name": "total_sales"}], "rows": []}, "parseErrors": []},
        out,
    ) == []
    assert out.getvalue().strip() == "total_sales", out.getvalue()

    print("selftest ok")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main()
