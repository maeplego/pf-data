# BI

ダッシュボードが読むのは **`marts`**（とパイプライン健全性の `ops.job_runs`）だけです。コマースや求人のコネクタはありません。

Compose が成功したあと、最小経路は `dashboards/marts_kpis.sql` を Postgres `localhost:5413`（ユーザー / DB `data`）に対して実行することです。期待値は `seeds/expected_kpi.json` です。

Metabase は既定では起動しません。使うときだけ:

```powershell
cd deploy
docker compose --env-file .env --profile bi up -d metabase
```

http://localhost:3313 でローカル管理者を作ります。資格情報はコミットしないでください。接続先は Compose ネットワークならホスト `postgres`、DB / ユーザー / パスワードは `.env.example` の `data`、スキーマは `marts` です。
