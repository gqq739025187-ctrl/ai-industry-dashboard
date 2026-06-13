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

## 健康检查

每次修改项目后，可以先运行一次本地健康检查，确认基础结构没有被破坏：

```bash
python scripts/health_check.py
```

这个检查只读取本地文件和导入本地模块，不会请求外部行情接口。

## 数据文件

- `watchlist.csv`：股票池和产业链分类。
- `events.csv`：静态事件库。
- `etf_config.csv`：ETF监控配置，可手动填写 IOPV/NAV。
- `chain_relations.csv`：产业链上下游关系表，用于描述环节之间的需求传导、产品配套和资本开支驱动关系。
- `market_expectation.csv`：市场预期层，用于记录产业逻辑、景气度、资金热度、估值吸引力和市场预期程度。

健康检查会同时检查 `chain_relations.csv` 的字段、分类合法性和重要性评分，也会检查 `market_expectation.csv` 的字段、分类、分数和预期程度。

`market_expectation.csv` 用于帮助区分：

- 产业逻辑是否强
- 当前景气度是否高
- 资金是否已经拥挤
- 估值是否仍有吸引力
- 市场是否已经交易了这个逻辑

## 开发日志

开发日志请查看 `CHANGELOG.md`。

## 重要说明

- 本项目不自动交易。
- 本项目不自动下单。
- 本项目不提供买卖建议。
- 页面中的分析和日报仅用于个人研究，不构成投资建议。
