# FactorFlow 架构说明

## 新架构（直接调用模式）

```
┌─────────────────────────────────────────┐
│          Streamlit 前端 (app.py)         │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │   BackendClient (直接调用)         │  │
│  └───────────────┬───────────────────┘  │
└──────────────────┼───────────────────────┘
                   │
           ┌───────▼────────┐
           │  后端服务模块   │
           │  - Services    │
           │  - Repositories│
           │  - Models      │
           │  - Database    │
           └────────────────┘
```

## 启动方式

### 方式1：使用批处理脚本（Windows）
```bash
run.bat
```

### 方式2：命令行启动
```bash
cd f:\pythonproject\FactorFlow
streamlit run frontend/app.py
```

## 架构优势

| 对比项 | 旧架构 (FastAPI + Streamlit) | 新架构 (直接调用) |
|--------|-----------------------------|------------------|
| 进程数 | 2个 (后端+前端) | 1个 |
| 部署复杂度 | 需要配置两个服务 | 只需启动 Streamlit |
| 数据传递 | HTTP + JSON 序列化 | 直接函数调用 |
| 性能 | 有网络开销 | 无网络开销 |
| numpy 支持 | 需要类型转换 | 原生支持 |
| 适用场景 | 多客户端、独立部署 | 单用户分析工具 |

## 项目结构

```
FactorFlow/
├── backend/                    # 后端代码
│   ├── core/                   # 核心模块
│   │   ├── analyzer.py        # 因子分析器
│   │   ├── database.py        # 数据库连接
│   │   ├── settings.py        # 配置管理
│   │   └── exceptions.py      # 异常定义
│   ├── models/                 # 数据模型
│   ├── repositories/           # 数据访问层
│   ├── services/               # 业务逻辑层
│   │   ├── factor_service.py  # 因子服务
│   │   ├── analysis_service.py# 分析服务
│   │   └── data_service.py    # 数据服务
│   └── main.py                # FastAPI 入口（可选）
│
├── frontend/                   # 前端代码
│   ├── app.py                 # Streamlit 主应用
│   └── utils/
│       ├── backend_client.py  # 后端直接调用客户端 ✨
│       ├── api_client.py      # HTTP API 客户端（备用）
│       └── config.py          # 前端配置
│
├── config/                     # 配置文件
│   └── factors.yaml           # 系统预置因子
│
├── data/                       # 数据目录
│   ├── factor_flow.db         # SQLite 数据库
│   └── cache/                 # 缓存目录
│
├── tests/                      # 测试代码
│   ├── test_core/             # 核心模块测试
│   ├── test_repositories/     # 仓储层测试
│   └── test_services/         # 服务层测试
│
├── run.bat                     # 启动脚本
└── pyproject.toml             # 项目配置
```

## 如需使用 FastAPI 模式

如果需要多客户端访问或独立部署后端，仍可使用 FastAPI 模式：

**终端1 - 启动后端：**
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**终端2 - 启动前端：**
```bash
streamlit run frontend/app.py
```

然后修改 `frontend/app.py` 将 `backend_client` 改回 `api_client`。
