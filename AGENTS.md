# P13 pf-data

このディレクトリは製品コードです。実装前にワークスペース（`project`）側を読む。

1. `project/portfolio-plan/instructions.md` または `project/AGENTS.md`
2. `project/data-platform/AGENTS.md`（なければ `instructions.md`）
3. `project/portfolio-plan/data-platform/DESIGN.md`
4. `project/portfolio-idea/19-etl-data-pipeline.md`
5. `project/data-platform/chat-context/` をファイル名順

テスト: リポジトリルートで `python -m pip install -e ".[dev]"` のあと `python -m pytest`。通ってからこのリポジトリにコミットする。P06/P10 の本番エクスポートをソースにしたことにしない。架空 CSV のみ。
