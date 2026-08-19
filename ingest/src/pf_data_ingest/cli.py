from __future__ import annotations

import sys

from pf_data_ingest.pipeline import run


def main() -> None:
    result = run()
    if not result.ok:
        print(f"pipeline failed: {result.failure_reason}", file=sys.stderr)
        raise SystemExit(1)
    print(f"pipeline ok run_id={result.run_id} rows={result.row_count}")


if __name__ == "__main__":
    main()
