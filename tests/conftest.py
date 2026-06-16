"""
测试配置
"""
import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """FastAPI 测试客户端"""
    return TestClient(app)


@pytest.fixture
def sample_solve_request():
    """示例求解请求"""
    return {
        "problem": "如何在不增加成本的情况下提升系统性能",
        "context": "当前系统响应慢，但预算有限",
        "industry": "软件开发",
        "constraints": ["成本高", "时间紧"]
    }
