# pf-data

学習用の ETL です。最初のパイプラインは **架空の店舗売上 CSV** を MinIO へ載せ、品質チェック、Postgres `raw`、dbt の marts まで通します。コマースや求人の本番エクスポートは接続していません。**本番 DWH の置き換えではありません。**

| ディレクトリ | 役割 |
| --- | --- |
| `seeds/` | 架空 CSV と期待 KPI |
| `ingest/` | 抽出、品質ゲート、raw 投入 |
| `transform/` | dbt（staging と marts） |
| `orchestrate/` | Dagster ジョブ |
| `bi/` | 任意の Metabase と KPI SQL |

## 起動

```powershell
cd deploy
copy .env.example .env
docker compose --env-file .env up --build
```

| URL | 用途 |
| --- | --- |
| http://localhost:3013 | Dagster |
| http://localhost:9113 | MinIO コンソール（`pfdata` / `.env` のパスワード） |
| localhost:5413 | Postgres（`data` / `data`、DB `data`） |

同じシードを再実行すると `raw` を truncate してから載せるので、KPI は二重になりません。期待値は `seeds/expected_kpi.json` です（例: 2026-08-01 は注文 3、点数 6、売上 11500 円）。

壊れた CSV を流すと品質ゲートで止まり、昨日の marts は残ります。

```powershell
cd deploy
docker compose --env-file .env run --rm -e PIPELINE_SOURCE=broken pipeline
```

Metabase は任意です（`docker compose --profile bi`）。最小経路は `bi/dashboards/marts_kpis.sql` を marts に対して実行することです。

## テスト

```powershell
python -m pip install -e ".[dev]"
python -m pytest
```

Spark、CDC、実在 PII ソースは非目標です。

設計の詳細は [portfolio-plan](https://github.com/maeplego/portfolio-plan) の `portfolio-plan/data-platform/docs/` です。

## ライセンスと利用条件

本リポジトリは **デモ・学習・社内評価用** です。現状品質に **保証はありません**。

- 許可: クローン、ローカル実行、学習、非本番の評価
- 別契約が必要: 本番運用、有償サービスへの組込み、再販・托管の提供

詳細は [LICENSE](./LICENSE) と [licensing.md](https://github.com/maeplego/portfolio-plan/blob/master/portfolio-plan/licensing.md) を参照してください。

