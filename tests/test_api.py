"""
API 端点测试
"""
import pytest
import respx
from httpx import Response


def test_solve_endpoint(client, sample_solve_request):
    """测试 TRIZ IFR 求解端点"""
    response = client.post("/api/v1/solve", json=sample_solve_request)
    assert response.status_code == 200

    data = response.json()
    assert data["code"] == 0
    assert "data" in data
    assert "message" in data

    # 验证四步法数据结构
    result_data = data["data"]
    assert "node1_deconstruction" in result_data
    assert "node2_ifr_anchor" in result_data
    assert "node3_resource_scan" in result_data
    assert "node4_actionable_plan" in result_data


def test_solve_node1_structure(client, sample_solve_request):
    """测试 Node 1 数据结构"""
    response = client.post("/api/v1/solve", json=sample_solve_request)
    data = response.json()

    node1 = data["data"]["node1_deconstruction"]
    assert "ultimate_function" in node1
    assert "harmful_factors" in node1
    assert "low_ideality_traps" in node1
    assert "function_tree" in node1

    # 验证低理想度陷阱已剪枝
    assert len(node1["low_ideality_traps"]) > 0


def test_solve_node2_structure(client, sample_solve_request):
    """测试 Node 2 数据结构"""
    response = client.post("/api/v1/solve", json=sample_solve_request)
    data = response.json()

    node2 = data["data"]["node2_ifr_anchor"]
    assert "ifr_formula_type" in node2
    assert "ifr_description" in node2
    assert "ideal_state" in node2
    assert "feasibility_gap" in node2

    # 验证 IFR 公式类型有效
    assert node2["ifr_formula_type"] in ["entity_vanish", "harmful_becomes_useful", "external_resource"]


def test_solve_node3_structure(client, sample_solve_request):
    """测试 Node 3 数据结构"""
    response = client.post("/api/v1/solve", json=sample_solve_request)
    data = response.json()

    node3 = data["data"]["node3_resource_scan"]
    assert "physical_contradictions" in node3
    assert "external_resources" in node3
    assert "resource_gaps" in node3
    assert "contradiction_resolution" in node3

    # 验证外部资源列表
    resources = node3["external_resources"]
    assert len(resources) > 0
    for resource in resources:
        assert "name" in resource
        assert "source" in resource
        assert "cost_type" in resource
        assert resource["cost_type"] in ["free", "low_cost", "paid"]


def test_solve_node4_structure(client, sample_solve_request):
    """测试 Node 4 数据结构"""
    response = client.post("/api/v1/solve", json=sample_solve_request)
    data = response.json()

    node4 = data["data"]["node4_actionable_plan"]
    assert "acquisition_sources" in node4
    assert "extraction_algorithms" in node4
    assert "fusion_mechanisms" in node4
    assert "action_steps" in node4
    assert "success_metrics" in node4
    assert "risk_mitigation" in node4

    # 验证行动步骤
    steps = node4["action_steps"]
    assert len(steps) > 0
    for step in steps:
        assert "step_number" in step
        assert "title" in step
        assert "description" in step
        assert "expected_output" in step


def test_mcp_tools_endpoint(client):
    """测试 MCP 工具列表端点"""
    response = client.get("/mcp/tools")
    assert response.status_code == 200

    data = response.json()
    assert "tools" in data
    assert len(data["tools"]) > 0

    # 验证工具结构
    for tool in data["tools"]:
        assert "name" in tool
        assert "description" in tool
        assert "parameters" in tool


def test_mcp_tool_execute_triz_solve(client):
    """测试 MCP triz_solve 工具执行"""
    request_data = {
        "problem": "测试问题",
        "context": "测试上下文"
    }
    response = client.post("/mcp/tools/triz_solve", json=request_data)
    assert response.status_code == 200

    data = response.json()
    assert data["code"] == 0
    assert "data" in data


def test_mcp_tool_execute_unknown(client):
    """测试 MCP 未知工具执行"""
    response = client.post("/mcp/tools/unknown_tool", json={})
    assert response.status_code == 404

    data = response.json()
    assert data["code"] == 404


def test_solve_with_empty_problem(client):
    """测试空问题请求"""
    response = client.post("/api/v1/solve", json={"problem": ""})
    assert response.status_code == 422  # 验证错误


def test_solve_without_industry(client):
    """测试无行业信息的请求"""
    request_data = {
        "problem": "如何优化系统性能"
    }
    response = client.post("/api/v1/solve", json=request_data)
    assert response.status_code == 200

    data = response.json()
    assert data["code"] == 0
