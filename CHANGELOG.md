# 开发日志

## V1.3A - A股AI硬件龙头库扩充

### 已完成

- `watchlist.csv` 新增 `tier` 字段
- A股AI硬件公司扩充
- 海外龙头定位为产业锚点
- 产业链百科支持按 `tier` 展示
- 健康检查支持 `tier` 校验

### 说明

- 系统定位调整为：A股AI产业链图谱 + 海外龙头验证层
- A股为主库，海外公司作为产业趋势锚点和验证器
- 本阶段不新增行情逻辑、新闻抓取、AI Agent、自动交易或买卖建议

## V1.2 - 驱动因素库

### 已完成

- 新增 `drivers.csv`
- 新增 `data_sources/drivers_loader.py`
- `AI产业链地图` 支持显示核心驱动因素
- 首页核心四问显示云厂Capex驱动因素
- 健康检查支持驱动因素库

### 说明

- 驱动因素库用于区分长期影响产业链的领先指标和滞后指标
- 本阶段不新增新闻抓取、AI Agent、行情逻辑、ETF逻辑或交易功能

## V1.1 - 事件影响矩阵

### 已完成

- 新增 `event_impact_matrix.csv`
- 新增 `data_sources/event_matrix_loader.py`
- 事件中心支持事件 -> 产业链 -> 公司映射
- 支持事件影响评分
- 健康检查支持事件影响矩阵

### 说明

- 事件影响评分 = 同一事件下 `strength` 求和，仅作为研究参考
- 本阶段不新增新闻抓取、AI Agent、行情逻辑、ETF逻辑或交易功能

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
