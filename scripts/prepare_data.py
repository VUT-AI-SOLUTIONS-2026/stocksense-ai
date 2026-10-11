"""Validate Kaggle train.csv and save the scoped sales file and audit."""
import argparse
import hashlib
import json
from pathlib import Path

from stocksense.data import audit_sales, load_sales, select_scope

ROOT = Path(__file__).resolve().parents[1]
PREPARED = ROOT / "data" / "prepared" / "store_1_items_1_to_5.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "data" / "raw" / "train.csv")
    parser.add_argument("--output", type=Path, default=PREPARED)
    parser.add_argument("--audit", type=Path, default=ROOT / "artifacts" / "data_audit.json")
    args = parser.parse_args()
    if len({args.source.resolve(), args.output.resolve(), args.audit.resolve()}) != 3:
        parser.error("The source, prepared CSV and audit must have different paths.")
    try:
        source = load_sales(args.source)
        selected = select_scope(source)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Data preparation failed: {error}\n")
    with args.source.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    audit = {
        "source_filename": args.source.name,
        "source_sha256": digest,
        "source": audit_sales(source),
        "selected_scope": audit_sales(selected),
        "raw_records_by_period": {
            "training_2013_2015": int(selected["date"].between("2013-01-01", "2015-12-31").sum()),
            "validation_2016": int(selected["date"].between("2016-01-01", "2016-12-31").sum()),
            "test_2017": int(selected["date"].between("2017-01-01", "2017-12-31").sum()),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    selected.to_csv(args.output, index=False, date_format="%Y-%m-%d")
    args.audit.write_text(json.dumps(audit, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Validated {len(source):,} source rows; prepared {len(selected):,} rows for store 1, items 1-5.")
    print(f"Prepared data: {args.output}")
    print(f"Data audit: {args.audit}")


if __name__ == "__main__":
    main()
