#!/usr/bin/env python3
"""Run a ShopifyQL query against the Admin GraphQL API, print CSV.

  export SHOPIFY_STORE=my-shop.myshopify.com
  export SHOPIFY_ADMIN_TOKEN=shpat_...
  python shopifyql.py "FROM sales SHOW total_sales DURING last_30d"
  echo "FROM sessions SHOW sessions DURING last_7d" | python shopifyql.py
"""
import csv
import json
import os
import sys
import urllib.request

API_VERSION = "2026-07"
QUERY = """query($q: String!) {
  shopifyqlQuery(query: $q) {
    __typename
    ... on TableResponse {
      tableData { columns { name } rows }
      parseErrors { code message range { start { line character } } }
    }
  }
}"""


def to_csv(payload, out):
    """payload -> rows on `out`. Returns list of parse error messages."""
    errors = [f"{e['message']} ({e['code']})" for e in payload.get("parseErrors") or []]
    if errors:
        return errors
    table = payload.get("tableData") or {}
    w = csv.writer(out)
    w.writerow(c["name"] for c in table.get("columns", []))
    w.writerows(table.get("rows", []))
    return []


def main():
    for var in ("SHOPIFY_STORE", "SHOPIFY_ADMIN_TOKEN"):
        if not os.environ.get(var):
            sys.exit(f"{var} is not set. See SKILL.md > Setup.")
    q = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    req = urllib.request.Request(
        f"https://{os.environ['SHOPIFY_STORE']}/admin/api/{API_VERSION}/graphql.json",
        data=json.dumps({"query": QUERY, "variables": {"q": q.strip()}}).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": os.environ["SHOPIFY_ADMIN_TOKEN"],
        },
    )
    with urllib.request.urlopen(req) as r:
        body = json.load(r)
    if body.get("errors"):
        sys.exit("GraphQL errors:\n" + json.dumps(body["errors"], indent=2))
    errors = to_csv(body["data"]["shopifyqlQuery"] or {}, sys.stdout)
    if errors:
        sys.exit("ShopifyQL parse errors:\n" + "\n".join(errors))


def selftest():
    import io

    out = io.StringIO()
    assert to_csv(
        {
            "tableData": {
                "columns": [{"name": "referring_channel"}, {"name": "total_sales"}],
                "rows": [["Search", "1200.00"], ["Direct", "800.50"]],
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

    # a parse error must never look like an empty result set
    errs = to_csv(
        {"tableData": None, "parseErrors": [{"code": "PARSE_ERROR", "message": "bad"}]},
        io.StringIO(),
    )
    assert errs == ["bad (PARSE_ERROR)"], errs
    print("selftest ok")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main()
