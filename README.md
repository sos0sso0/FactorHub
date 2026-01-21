# FactorFlow - 因子分析平台

基于 Streamlit 和 FastAPI 的量化因子分析系统，支持因子管理、因子分析和可视化报告导出。

## 技术栈

- **前端**: Streamlit
- **后端**: FastAPI + akshare（期货数据）+ SQLite + TA-Lib
- **环境管理**: uv
- **机器学习**: XGBoost + SHAP

## 功能特性

### 因子管理
- 系统预置因子（不可删除）
- 用户自定义因子（可编辑/删除）
- 因子代码校验和上传
- 因子列表展示和统计

### 因子分析
- 单股票/股票池分析模式
- 行情预览（归一化折线图）
- SHAP 分析（力图、特征重要性、依赖图）
- 统计分析（IC、IR、时间序列、热力图等）
- Markdown 报告导出

## 安装和运行

### 1. 使用 uv 创建虚拟环境并安装依赖

```bash
# 安装 uv（如果尚未安装）
pip install uv

# 创建虚拟环境并安装依赖
uv sync
```

### 2. 启动后端服务

```bash
# 激活虚拟环境
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 启动 FastAPI 服务
uvicorn backend.main:app --reload --port 8000
```

### 3. 启动前端应用

```bash
# 在新终端中启动 Streamlit
streamlit run frontend/app.py
```

## 项目结构

```
FactorFlow/
├── backend/           # 后端 API 服务
│   ├── api/          # API 路由
│   ├── core/         # 核心业务逻辑
│   ├── models/       # 数据模型
│   └── services/     # 数据服务（akshare）
├── frontend/         # Streamlit 前端
│   ├── pages/        # 页面组件
│   └── utils/        # 工具函数
├── config/           # 配置文件
│   └── factors.yaml  # 因子配置
├── data/            # 数据存储（SQLite、缓存）
└── logs/            # 日志文件
```

## 预置因子

系统预置了以下技术指标因子：

1. **价格与收益率结构**: log_return, price_vs_sma, high_low_ratio 等
2. **动量与趋势指标**: RSI, MACD, ADX, CCI 等
3. **波动率与风险**: ATR, Bollinger Bands, Volatility 等
4. **成交量与资金流**: volume_ma_ratio, OBV 等
5. **结构与模式识别**: candle patterns, fractal, regime 等

## 使用说明

详细的因子说明和使用方法请参考系统内的文档。
