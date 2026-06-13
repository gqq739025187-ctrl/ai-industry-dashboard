# 开发日志

## V1.0 - 市场预期层

### 已完成

- 新增 `market_expectation.csv`
- 新增 `data_sources/expectation_loader.py`
- `AI产业链地图` 支持显示逻辑强度、景气度、资金热度、估值吸引力和市场预期程度
- 健康检查支持市场预期层

### 说明

- 市场预期层用于辅助判断“产业逻辑是否已经被市场充分交易”
- 本阶段不新增新闻抓取、AI Agent、自动交易或买卖建议

## V0.9 - 产业链关系图谱

### 已完成

- 新增 `chain_relations.csv`
- 新增 `data_sources/relations_loader.py`
- `AI产业链地图` 支持上下游关系展示
- 健康检查支持产业链关系表

### 说明

- 产业链关系表用于描述环节之间的需求传导、供给约束、资本开支驱动、产品配套和替代竞争等关系
- 本阶段不新增行情、新闻抓取、AI Agent 或交易相关功能

## V0.8 - 结构治理完成

### 已完成

- 新增 `config/constants.py`，统一管理字段、产业链分类、ETF代码和产业链顺序
- 拆分 `dashboard/views.py` 为 `dashboard/pages/` 多个页面模块
- 新增 `dashboard/cache.py`，集中管理 `session_state` 缓存
- 新增 `dashboard/loaders.py`，集中管理数据加载和兜底空表
- `data_layer.py` 保留为兼容入口
- 新增 `scripts/health_check.py` 健康检查脚本
- `README.md` 增加健康检查运行方式

### 当前能力

- 产业链首页
- AI产业链地图
- 投资地图
- 产业链百科
- 事件中心
- 资产数据库
- 配置检查
- 行情监控
- ETF监控
- AI日报

### 当前原则

- 不做自动交易
- 不做自动买卖建议
- 行情数据手动刷新
- 新闻和AI Agent 暂缓
- 优先建设 AI产业链知识图谱和事件映射

### 下一步计划

P1：

- 强化事件影响矩阵
- 完善 watchlist 公司主数据
- 完善 events 事件知识库
- 增加产业链上下游关系字段

P2：

- 规则日报升级
- AI解释层
- 新闻源接入
