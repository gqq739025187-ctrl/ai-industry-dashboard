# AI产业链投资驾驶舱

这是一个本地运行的个人投资研究平台，定位是 **AI产业链知识图谱 + 投研驾驶舱**，不是自动交易系统。

系统重点回答三个问题：

1. AI资本开支是否增强？
2. 哪个产业链环节最受益？
3. 当前股票池和持仓是否处在相关环节中？

## 当前功能

- 资产数据库：从 `watchlist.csv` 管理股票池。
- AI产业链地图：展示云厂Capex、GPU、HBM、交换机/ASIC、光模块、光器件、PCB 的上下游关系。
- 产业链百科：按产业链环节查看公司、主营业务、市场关注点和一句话理解。
- 事件中心：从 `events.csv` 建立“事件 -> 产业链 -> 公司”的映射。
- 行情监控：手动刷新 A股、美股、ETF 数据，避免页面打开时自动请求外部接口。
- ETF溢价监控：监控 ETF 价格、IOPV/NAV 和溢价率。
- AI产业链日报：基于本地规则和已有缓存生成投研摘要，不调用大模型 API。

## 项目结构

```text
app.py
data_layer.py
data_sources/
  watchlist_loader.py
  market_a_share.py
  market_us.py
  etf_data.py
  events_loader.py
  utils.py
dashboard/
  logic.py
  views.py
watchlist.csv
events.csv
etf_config.csv
requirements.txt
```

## 本地运行

先进入项目文件夹：

```bash
cd /Users/xiaogutongxue/Documents/Codex/2026-06-11/ai-hbm-ai-etf-etf-513310
```

启动 Streamlit：

```bash
HOME=$PWD .venv/bin/streamlit run app.py --server.port 8503 --server.address 127.0.0.1 --server.headless true --browser.gatherUsageStats false
```

打开浏览器：

```text
http://localhost:8503
```

## 数据文件

- `watchlist.csv`：股票池和产业链分类。
- `events.csv`：静态事件库。
- `etf_config.csv`：ETF监控配置，可手动填写 IOPV/NAV。

## 重要说明

- 本项目不自动交易。
- 本项目不自动下单。
- 本项目不提供买卖建议。
- 页面中的分析和日报仅用于个人研究，不构成投资建议。
