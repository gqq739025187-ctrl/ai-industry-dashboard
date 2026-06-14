# AI产业链投资驾驶舱

这是一个本地运行的个人投资研究平台，定位是 **AI产业链知识图谱 + 投研驾驶舱**，不是自动交易系统。

本项目以 **A股AI产业链** 为主，海外龙头作为产业趋势锚点和验证层。

系统重点回答四个问题：

1. AI资本开支是否增强？
2. 哪个产业链环节最受益？
3. 当前股票池和持仓是否处在相关环节中？
4. 市场是否已经交易了这个逻辑？

## 当前功能

- 资产数据库：从 `watchlist.csv` 管理股票池。
- AI产业链地图：展示云厂Capex、GPU、HBM、交换机/ASIC、光模块、光器件、PCB 的上下游关系。
- 产业链百科：按产业链环节查看公司、主营业务、市场关注点和一句话理解。
- 事件中心：从 `events.csv` 建立“事件 -> 产业链 -> 公司”的映射。
- 市场预期层：记录产业逻辑、景气度、资金热度、估值吸引力和预期程度。
- 事件影响矩阵：把事件映射到产业链和受影响公司。
- 驱动因素库：记录长期影响产业链的领先指标和滞后指标。
- A股AI硬件龙头库：以A股公司为主库，覆盖AI硬件产业链关键环节。
- 海外龙头验证层：用海外核心公司验证产业趋势和资本开支方向。
- 行情监控：手动刷新 A股、美股、ETF 数据，避免页面打开时自动请求外部接口。
- ETF溢价监控：监控 ETF 价格、IOPV/NAV 和溢价率。
- AI产业链日报：基于本地规则和已有缓存生成投研摘要，不调用大模型 API。

## 项目结构

```text
app.py
data_layer.py
config/
  constants.py
data_sources/
  watchlist_loader.py
  market_a_share.py
  market_us.py
  etf_data.py
  events_loader.py
  event_matrix_loader.py
  relations_loader.py
  expectation_loader.py
  drivers_loader.py
  source_loader.py
  news_fetcher.py
  keyword_mapper.py
  utils.py
dashboard/
  logic.py
  views.py
  cache.py
  loaders.py
  pages/
scripts/
  health_check.py
  fetch_news.py
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

## 可信源消息抓取

第一版只抓公开 RSS，不抓需要登录的网站正文，不绕过付费墙，也不保存账号密码到仓库。

运行方式：

```bash
python scripts/fetch_news.py
```

系统已预留以下接入类型：

- `public_rss`
- `public_api`
- `email_feed`
- `authenticated_source`

当前实际自动抓取只实现 `public_rss`。

未来需要登录的网站只能通过用户授权、环境变量、OAuth、邮件源或浏览器会话方式处理。代码和 CSV 中只允许保存环境变量名，不保存真实密钥、账号或密码。

## 数据文件

- `watchlist.csv`：股票池和产业链分类。
- `events.csv`：静态事件库。
- `event_impact_matrix.csv`：事件影响矩阵，用于描述“事件 -> 产业链 -> 公司”的映射关系和影响强度。
- `drivers.csv`：长期驱动因素库，用于记录哪些指标是领先指标、哪些是滞后指标。
- `etf_config.csv`：ETF监控配置，可手动填写 IOPV/NAV。
- `chain_relations.csv`：产业链上下游关系表，用于描述环节之间的需求传导、产品配套和资本开支驱动关系。
- `market_expectation.csv`：市场预期层，用于记录产业逻辑、景气度、资金热度、估值吸引力和市场预期程度。
- `unified_sources.csv`：统一消息源配置，预留公开 RSS、公开 API、邮件源和授权源。
- `raw_news.csv`：可信源自动抓取消息，默认状态为 `pending_review`。

健康检查会同时检查 `chain_relations.csv` 的字段、分类合法性和重要性评分，也会检查 `market_expectation.csv` 的字段、分类、分数和预期程度。

事件中心开始支持：

```text
事件
↓
产业链
↓
公司
```

映射关系，并根据影响强度生成事件影响评分。

`drivers.csv` 用于记录长期驱动因素，帮助系统识别哪些指标是领先指标、哪些是滞后指标。

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
