from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFINITIONS = ROOT / "orchestrate" / "src" / "pf_data_orchestrate" / "definitions.py"


def test_dag_ops_are_wired_in_order():
    source = DEFINITIONS.read_text(encoding="utf-8")
    assert "@job" in source
    assert "def fictional_csv_sales" in source
    assert (
        "transform_dbt(load_staging(validate_csv(extract_fictional_csv())))" in source
    )
    for name in (
        "extract_fictional_csv",
        "validate_csv",
        "load_staging",
        "transform_dbt",
    ):
        assert f"def {name}" in source
