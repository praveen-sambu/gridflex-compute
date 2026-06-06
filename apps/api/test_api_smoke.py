from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def fetch_json(base_url: str, path: str) -> dict | list:
    with urllib.request.urlopen(f"{base_url}{path}") as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_text(base_url: str, path: str) -> str:
    with urllib.request.urlopen(f"{base_url}{path}") as response:
        return response.read().decode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Lightweight smoke test for the GridFlex FastAPI app.")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL for the API under test.")
    args = parser.parse_args()

    try:
        health = fetch_json(args.base_url, "/health")
        demo = fetch_json(args.base_url, "/api/v1/demo")
        demo_dgx = fetch_json(args.base_url, "/api/v1/demo-dgx")
        kpis = fetch_json(args.base_url, "/api/v1/kpis")
        metrics = fetch_text(args.base_url, "/metrics")

        checks = {
            "health_status_ok": health.get("status") == "ok",
            "demo_has_kpis": isinstance(demo, dict) and "kpis" in demo,
            "demo_dgx_has_run_id": isinstance(demo_dgx, dict) and "run_id" in demo_dgx,
            "kpis_has_jobs_total": isinstance(kpis, dict) and "jobs_total" in kpis,
            "metrics_contains_jobs_total": "gridflex_jobs_total" in metrics,
        }

        failed = [name for name, passed in checks.items() if not passed]
        summary = {
            "base_url": args.base_url,
            "checks": checks,
            "failed": failed,
        }
        print(json.dumps(summary, indent=2))
        return 1 if failed else 0
    except urllib.error.HTTPError as exc:
        print(f"HTTP error: {exc.code} {exc.reason}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"URL error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())