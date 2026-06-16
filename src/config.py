"""
TRIZ IFR Agent 配置模块
"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    # Agent 基础信息
    AGENT_NAME: str = "triz-ifr-agent"
    AGENT_VERSION: str = "1.0.0"
    AGENT_DESCRIPTION: str = "TRIZ IFR 通用逆向收敛专家"

    # API 配置
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # AI 模型配置
    AI_MODEL: str = "deepseek-chat"
    AI_API_KEY: str = ""
    AI_BASE_URL: str = "https://api.deepseek.com/v1"

    # 控制面配置
    CP_API_KEY: str = ""
    CP_BASE_URL: str = "https://administrator.chmjk67.top"

    # 外部资源搜索配置
    WEB_SEARCH_ENABLED: bool = True
    GITHUB_API_ENABLED: bool = True
    ARXIV_ENABLED: bool = True

    # 日志配置
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
