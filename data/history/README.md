# 本地历史行情数据

当在线日线数据源不可用时，数据层会读取这里的 CSV 文件计算 20 日和 60 日均线。

文件名格式：

```text
300502.SZ.csv
300308.SZ.csv
300394.SZ.csv
002281.SZ.csv
```

最少需要两列：

```csv
date,close
2026-01-01,100.00
```

如果有成交额和涨跌幅，也可以加：

```csv
date,close,amount,change_pct
```
