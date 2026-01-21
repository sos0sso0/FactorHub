# FactorFlow 使用指南

## 快速开始

### 1. 环境准备

确保已安装 Python 3.11 和 uv：

```bash
# 安装 uv（如果尚未安装）
pip install uv
```

### 2. 安装依赖

```bash
# 使用 uv 安装所有依赖
uv pip install --python 3.11 streamlit fastapi uvicorn akshare pandas numpy TA-Lib sqlalchemy pydantic xgboost plotly matplotlib seaborn scikit-learn requests httpx python-multipart openpyxl pyyaml
```

### 3. 启动服务

#### Windows 用户

**方式一：分别启动**

1. 启动后端 API：
   - 双击 `start_backend.bat`
   - 或在命令行运行：`.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`

2. 启动前端应用（新终端）：
   - 双击 `start_frontend.bat`
   - 或在命令行运行：`.venv\Scripts\python.exe -m streamlit run frontend/app.py`

**方式二：使用 Python 直接运行**

```bash
# 启动后端
.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 新终端，启动前端
.venv\Scripts\python.exe -m streamlit run frontend/app.py
```

#### Linux/Mac 用户

```bash
# 给脚本添加执行权限
chmod +x start_all.sh

# 启动所有服务
./start_all.sh
```

### 4. 访问应用

- **前端界面**: http://localhost:8501
- **后端 API 文档**: http://localhost:8000/docs

## 功能说明

### 因子管理

#### 查看因子列表
1. 在左侧菜单选择"因子管理"
2. 系统因子：预置的技术指标因子（不可删除）
3. 用户因子：自定义的因子（可编辑/删除）

#### 添加自定义因子
1. 点击"新增因子"标签页
2. 填写因子信息：
   - **因子名称**: 唯一标识符，如 `my_custom_factor`
   - **分类**: 选择合适的因子分类
   - **因子公式**: Python 表达式，见下方语法说明
   - **因子说明**: 详细描述因子用途
3. 点击"校验公式"验证语法
4. 点击"保存因子"提交

#### 因子公式语法

**可用的变量：**
- `df`: 包含 OHLCV 数据的 DataFrame
  - `df['open']`: 开盘价
  - `df['high']`: 最高价
  - `df['low']`: 最低价
  - `df['close']`: 收盘价
  - `df['volume']`: 成交量
- `np`: numpy 模块
- `pd`: pandas 模块
- `talib`: TA-Lib 技术指标库

**示例公式：**

```python
# 日对数收益率
np.log(df['close'] / df['close'].shift(1))

# 5日收益率
np.log(df['close'] / df['close'].shift(5))

# 20日均线相对位置
df['close'] / df['close'].rolling(window=20).mean()

# RSI 指标
talib.RSI(df['close'], timeperiod=14)

# MACD 差值线
talib.EMA(df['close'], timeperiod=12) - talib.EMA(df['close'], timeperiod=26)

# 布林带宽度
upper, middle, lower = talib.BBANDS(df['close'], 20, 2, 2)
(upper - lower) / middle

# 波动率
np.log(df['close'] / df['close'].shift(1)).rolling(window=10).std()
```

### 因子分析

#### 分析配置
1. 在左侧菜单选择"因子分析"
2. 配置分析参数：
   - **数据模式**: 单股票或股票池
   - **股票代码**: 输入期货代码（如 CU2401）
   - **选择因子**: 勾选要分析的因子
   - **时间区间**: 设置开始和结束日期

#### 分析结果

**1. 行情预览**
- 股票价格走势图
- 因子数据预览
- 统计分析

**2. 特征重要性**
- XGBoost 模型评估指标（R²、RMSE）
- 特征重要性排序和可视化
- 识别最有效的预测因子

**3. IC/IR 分析**
- 各因子的 IC（信息系数）
- IC 绝对值排序
- 评估因子预测能力

**4. 导出报告**
- 生成 Markdown 格式分析报告
- 包含所有分析结果和统计指标
- 可下载保存

## 系统预置因子

系统包含以下预置因子：

### 价格与收益率结构
- `log_return_1`: 日对数收益率
- `log_return_5`: 5日累计收益率
- `price_vs_sma20`: 相对20日均线位置
- `price_vs_sma60`: 相对60日均线位置
- `sma20_vs_sma60`: 短期vs长期趋势
- `high_low_ratio`: 日内波动幅度
- `close_open_ratio`: 收盘相对开盘强度

### 动量与趋势指标
- `rsi_14`: RSI(14) 超买超卖指标
- `macd_line`: MACD 差值线
- `macd_signal`: MACD 信号线
- `macd_hist`: MACD 柱状图
- `adx_14`: ADX(14) 趋势强度
- `cci_20`: CCI(20) 通道突破信号
- `roc_10`: 10日变化率

### 波动率与风险
- `atr_14`: ATR(14) 平均真实波幅
- `atr_norm`: 波动率相对价格水平
- `volatility_10`: 近10日收益率标准差
- `bollinger_bandwidth`: 布林带宽度
- `bollinger_position`: 价格在布林带中的位置

### 成交量与资金流
- `volume_ma_ratio`: 当日量能vs近期均量
- `obv`: OBV 累计量能趋势
- `obv_slope`: OBV 近5日斜率

### 结构与模式识别
- `is_bullish_candle`: 是否阳线
- `regime_volatility`: 高波动regime标记
- `regime_trend`: 趋势市标记

## 常见问题

### Q: akshare 数据获取失败怎么办？
A: 系统会自动生成模拟数据用于测试。确保网络连接正常，或尝试更换数据源。

### Q: TA-Lib 安装失败？
A: TA-Lib 需要 C 库支持。可以：
1. 使用 conda 安装：`conda install -c conda-forge ta-lib`
2. 或使用预编译的 wheel 文件

### Q: 如何添加新的技术指标？
A: 在"因子管理"页面，点击"新增因子"，输入 talib 函数公式即可。

### Q: 数据如何缓存？
A: akshare 数据会自动缓存到 `data/cache/` 目录，默认缓存期为1天。

## 技术架构

- **前端**: Streamlit
- **后端**: FastAPI + SQLAlchemy
- **数据库**: SQLite
- **数据源**: akshare (期货数据)
- **技术指标**: TA-Lib
- **机器学习**: XGBoost + SHAP (可选)
- **环境管理**: uv

## 项目结构

```
FactorFlow/
├── backend/               # 后端 API
│   ├── api/              # API 路由
│   ├── core/             # 核心业务逻辑
│   ├── models/           # 数据模型
│   └── services/         # 数据服务
├── frontend/             # Streamlit 前端
│   └── app.py           # 主应用
├── config/              # 配置文件
│   └── factors.yaml     # 因子配置
├── data/               # 数据存储
│   ├── cache/          # 数据缓存
│   └── factor_flow.db  # SQLite 数据库
├── logs/               # 日志文件
├── pyproject.toml      # 项目配置
├── start_backend.bat   # Windows 启动脚本（后端）
├── start_frontend.bat  # Windows 启动脚本（前端）
└── start_all.sh        # Linux/Mac 启动脚本
```

## 开发说明

### 运行测试
```bash
# 激活虚拟环境
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 运行测试
pytest
```

### 代码格式化
```bash
# 使用 black 格式化代码
black backend/ frontend/

# 使用 isort 排序导入
isort backend/ frontend/
```

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交 Issue。
