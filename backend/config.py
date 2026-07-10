"""
应用配置管理
从环境变量读取所有配置，提供默认值
"""
import os
from pathlib import Path

# 自动加载 .env 文件（如果存在）
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


class Settings:
    """全局配置单例"""

    # 阿里云 DashScope (通义千问)
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # AI 模型选择
    AI_EXTRACT_MODEL: str = "qwen-plus"       # 信息提取
    AI_SCORE_MODEL: str = "qwen-plus"          # 评分匹配

    # AI 参数
    AI_EXTRACT_TEMPERATURE: float = 0.1
    AI_SCORE_TEMPERATURE: float = 0.3
    AI_MAX_TOKENS_EXTRACT: int = 2000
    AI_MAX_TOKENS_SCORE: int = 1000
    AI_TIMEOUT_SECONDS: int = 30
    AI_MAX_RETRIES: int = 2

    # 文件上传
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_MIME_TYPES: list = ["application/pdf"]

    # Redis 缓存 (加分项)
    REDIS_HOST: str = os.getenv("REDIS_HOST", "")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    CACHE_TTL_SECONDS: int = 24 * 3600  # 24 小时

    # 服务信息
    APP_TITLE: str = "SmartResumeAI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    @property
    def redis_url(self) -> str:
        """构建 Redis 连接 URL"""
        if not self.REDIS_HOST:
            return ""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def redis_enabled(self) -> bool:
        """Redis 是否已配置"""
        return bool(self.REDIS_HOST)

    @property
    def dashscope_configured(self) -> bool:
        """DashScope API Key 是否已配置"""
        return bool(self.DASHSCOPE_API_KEY)


settings = Settings()
