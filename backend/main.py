"""
FastAPI 主应用
提供因子管理和分析的 REST API
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import logging

from backend.core.database import init_db
from backend.core.settings import settings
from backend.core.exceptions import (
    AppException,
    NotFoundException,
    BadRequestException,
    ValidationException,
    app_exception_handler,
    http_exception_handler,
    general_exception_handler,
)
from backend.services import factor_service, analysis_service, data_service

# 配置日志
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=settings.LOG_FORMAT,
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(
    title="FactorFlow API",
    description="因子分析平台 API",
    version="0.2.0",
)

# 注册异常处理器
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# Pydantic 模型
class FactorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="因子名称")
    formula: str = Field(..., min_length=1, description="因子公式")
    description: str = Field(default="", description="因子描述")
    category: str = Field(default="custom", description="因子分类")


class FactorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    formula: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    category: Optional[str] = None


class AnalysisRequest(BaseModel):
    symbols: List[str] = Field(..., min_length=1, description="品种代码列表")
    factors: List[str] = Field(..., min_length=1, description="因子名称列表")
    start_date: str = Field(..., pattern=r"^\d{8}$", description="开始日期 (YYYYMMDD)")
    end_date: str = Field(..., pattern=r"^\d{8}$", description="结束日期 (YYYYMMDD)")
    mode: str = Field(default="pool", pattern="^(single|pool)$", description="分析模式")


class FormulaValidate(BaseModel):
    formula: str = Field(..., min_length=1, description="因子公式")


class HealthResponse(BaseModel):
    status: str
    timestamp: str


# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    logger.info("正在初始化数据库...")
    init_db()
    logger.info("正在初始化系统因子...")
    factor_service.init_system_factors()
    logger.info("API 服务启动完成")


# 健康检查
@app.get(
    "/health",
    response_model=HealthResponse,
    summary="健康检查",
    description="检查 API 服务是否正常运行",
)
async def health_check() -> HealthResponse:
    """健康检查接口"""
    return HealthResponse(status="ok", timestamp=datetime.now().isoformat())


# ========== 因子管理 API ==========

@app.get(
    "/api/factors",
    summary="获取因子列表",
    description="获取所有因子，支持按来源过滤",
)
async def get_factors(source: Optional[str] = None):
    """获取所有因子"""
    factors = factor_service.get_all_factors(source=source)
    return {"success": True, "data": factors}


@app.get(
    "/api/factors/stats",
    summary="获取因子统计",
    description="获取因子数量统计信息",
)
async def get_factor_stats():
    """获取因子统计信息"""
    stats = factor_service.get_factor_stats()
    return {"success": True, "data": stats}


@app.post("/api/factors", summary="创建因子", description="创建新的自定义因子")
async def create_factor(factor: FactorCreate):
    """创建新因子"""
    factor_service.add_factor(
        name=factor.name,
        formula=factor.formula,
        description=factor.description,
        category=factor.category,
    )
    return {"success": True, "message": "因子创建成功"}


@app.put("/api/factors/{factor_id}", summary="更新因子", description="更新因子信息")
async def update_factor(factor_id: int, factor: FactorUpdate):
    """更新因子"""
    factor_service.update_factor(
        factor_id=factor_id,
        name=factor.name,
        formula=factor.formula,
        description=factor.description,
        category=factor.category,
    )
    return {"success": True, "message": "因子更新成功"}


@app.delete("/api/factors/{factor_id}", summary="删除因子", description="删除自定义因子")
async def delete_factor(factor_id: int):
    """删除因子"""
    factor_service.delete_factor(factor_id=factor_id)
    return {"success": True, "message": "因子删除成功"}


@app.post(
    "/api/factors/validate",
    summary="验证因子公式",
    description="验证因子公式是否正确",
)
async def validate_formula(request: FormulaValidate):
    """验证因子公式"""
    result = factor_service.validate_formula(request.formula)
    return {"success": True, "data": result}


# ========== 数据获取 API ==========

@app.get(
    "/api/data/{symbol}",
    summary="获取市场数据",
    description="获取指定品种的期货行情数据",
)
async def get_market_data(
    symbol: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """获取市场数据"""
    df = data_service.get_futures_data(
        symbol=symbol, start_date=start_date, end_date=end_date, use_cache=True
    )

    # 转换为 JSON 格式
    data = df.reset_index().to_dict(orient="records")

    return {"success": True, "data": data}


# ========== 因子分析 API ==========

@app.post(
    "/api/analysis",
    summary="执行因子分析",
    description="执行因子分析，返回模型训练结果和 IC 分析",
)
async def run_analysis(request: AnalysisRequest):
    """执行因子分析"""
    results = analysis_service.execute_analysis(
        symbols=request.symbols,
        factors=request.factors,
        start_date=request.start_date,
        end_date=request.end_date,
        mode=request.mode,
    )
    return {"success": True, "data": results}


@app.get(
    "/api/analysis/factors/{symbol}",
    summary="计算因子值",
    description="为指定品种计算因子值",
)
async def compute_factors_for_symbol(symbol: str, factors: str):
    """为指定品种计算因子"""
    factor_list = factors.split(",")

    result = analysis_service.compute_factors_for_symbol(symbol, factor_list)

    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level=settings.LOG_LEVEL.lower(),
    )
