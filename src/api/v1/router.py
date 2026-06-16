"""
TRIZ IFR Agent API 路由聚合
"""
from fastapi import APIRouter

from src.api.v1.endpoints import router as solve_router

router = APIRouter()

# 注册求解路由
router.include_router(solve_router, tags=["TRIZ IFR 求解"])
