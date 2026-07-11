"""
FastAPI 应用主入口
在阿里云 FC 中以 ASGI 模式运行: uvicorn main:app
"""
from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from cache.memory_cache import MemoryCache
from cache.redis_cache import RedisCache
from routers import resume, match

# 日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


# ──── 全局缓存实例 ────
memory_cache = MemoryCache(max_size=100)
redis_cache: RedisCache | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化 Redis，关闭时清理"""
    global redis_cache
    logger.info("SmartResumeAI 启动中...")

    # 初始化 Redis（如果配置了）
    if settings.redis_enabled:
        redis_cache = RedisCache(
            redis_url=settings.redis_url,
            ttl=settings.CACHE_TTL_SECONDS
        )
        if redis_cache.available:
            logger.info("Redis 缓存已启用")
        else:
            logger.warning("Redis 不可用，降级为内存缓存")

    logger.info(f"DashScope 已配置: {settings.dashscope_configured}")
    yield

    logger.info("SmartResumeAI 关闭")


# ──── 创建 FastAPI App ────
app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="AI 赋能的智能简历分析系统",
    lifespan=lifespan,
)

# ──── CORS 中间件 ────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,
)

# ──── OPTIONS 兜底（FC 代理层可能导致预检返回非 200）──
@app.options("/{rest_of_path:path}")
async def preflight_handler():
    return JSONResponse(status_code=200, content={"message": "OK"})


# ──── 全局异常处理 ────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """兜底异常处理"""
    logger.error(f"未处理异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_ERROR", "message": "服务器内部错误，请稍后重试"}
    )


# ──── 注册路由 ────
app.include_router(resume.router, prefix="/api", tags=["简历管理"])
app.include_router(match.router, prefix="/api", tags=["评分匹配"])


# ──── 根路径重定向 ────
@app.get("/")
async def root():
    return {
        "service": "SmartResumeAI",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/api/health",
        "frontend": "https://mantou676.github.io/SmartResumeAI/"
    }


# ──── 健康检查 ────
@app.get("/api/health", tags=["系统"])
async def health_check():
    """服务健康检查"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "redis_enabled": redis_cache is not None and redis_cache.available if redis_cache else False,
        "dashscope_configured": settings.dashscope_configured,
    }
