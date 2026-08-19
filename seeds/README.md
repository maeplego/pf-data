# 架空シード

創作した店舗売上です。コマースや求人のエクスポートではありません。

`orders.csv` と `products.csv` が正常系です。`broken_orders.csv` は品質ゲート用（負の数量・価格、壊れた日付）です。`expected_kpi.json` は pytest と `dbt build` 成功後に照合する mart の粒度です。
