"""
TRIZ IFR Agent 数据模型定义
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class SolveRequest(BaseModel):
    """求解请求"""
    problem: str = Field(..., description="用户输入的问题描述", min_length=1)
    context: Optional[str] = Field(None, description="额外上下文信息")
    industry: Optional[str] = Field(None, description="所属行业/领域")
    constraints: Optional[List[str]] = Field(default_factory=list, description="已知约束条件")
    preferred_resources: Optional[List[str]] = Field(default_factory=list, description="偏好的资源类型")


class Node1Deconstruction(BaseModel):
    """Node 1: 问题功能化解构"""
    ultimate_function: str = Field(..., description="系统要实现的终极功能")
    harmful_factors: List[str] = Field(default_factory=list, description="需要消除的有害/限制因素")
    low_ideality_traps: List[str] = Field(default_factory=list, description="低理想度错误路径（已剪枝）")
    function_tree: Dict[str, Any] = Field(default_factory=dict, description="功能分解树")


class Node2IFRAnchor(BaseModel):
    """Node 2: 极致 IFR 顶点锚定"""
    ifr_formula_type: str = Field(..., description="IFR 公式类型: entity_vanish | harmful_becomes_useful | external_resource")
    ifr_description: str = Field(..., description="IFR 顶点状态描述")
    ideal_state: Dict[str, Any] = Field(default_factory=dict, description="理想状态详细定义")
    feasibility_gap: str = Field(..., description="从现实到 IFR 的可行性差距")


class ResourceItem(BaseModel):
    """生态资源项"""
    name: str = Field(..., description="资源名称")
    source: str = Field(..., description="资源来源（平台/社区/公域）")
    url: Optional[str] = Field(None, description="资源链接")
    cost_type: str = Field("free", description="成本类型: free | low_cost | paid")
    description: str = Field(..., description="资源描述")
    relevance_score: float = Field(0.0, ge=0.0, le=1.0, description="与问题的相关度评分")


class PhysicalContradiction(BaseModel):
    """物理矛盾"""
    parameter: str = Field(..., description="矛盾参数")
    requirement_a: str = Field(..., description="条件 A 的要求")
    requirement_not_a: str = Field(..., description="条件非 A 的要求")
    separation_strategy: Optional[str] = Field(None, description="分离策略建议")


class Node3ResourceScan(BaseModel):
    """Node 3: 逆向资源扫描与核心冲突"""
    physical_contradictions: List[PhysicalContradiction] = Field(default_factory=list, description="物理矛盾列表")
    external_resources: List[ResourceItem] = Field(default_factory=list, description="外部生态资源列表")
    resource_gaps: List[str] = Field(default_factory=list, description="资源缺口")
    contradiction_resolution: str = Field(..., description="矛盾解决思路")


class ActionStep(BaseModel):
    """行动步骤"""
    step_number: int = Field(..., description="步骤序号")
    title: str = Field(..., description="步骤标题")
    description: str = Field(..., description="步骤描述")
    expected_output: str = Field(..., description="预期产出")
    estimated_effort: Optional[str] = Field(None, description="预估工作量")


class Node4ActionablePlan(BaseModel):
    """Node 4: 可执行落地方案"""
    acquisition_sources: List[Dict[str, str]] = Field(default_factory=list, description="获取源列表")
    extraction_algorithms: List[Dict[str, str]] = Field(default_factory=list, description="提取算法")
    fusion_mechanisms: List[Dict[str, str]] = Field(default_factory=list, description="融合机制")
    action_steps: List[ActionStep] = Field(default_factory=list, description="行动步骤")
    success_metrics: List[str] = Field(default_factory=list, description="成功指标")
    risk_mitigation: List[str] = Field(default_factory=list, description="风险缓解措施")


class SolveResponse(BaseModel):
    """求解响应"""
    code: int = Field(0, description="状态码")
    data: Dict[str, Any] = Field(default_factory=dict, description="求解结果数据")
    message: str = Field("success", description="状态消息")


class ToolInfo(BaseModel):
    """MCP 工具信息"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="参数定义")


class ToolExecuteRequest(BaseModel):
    """工具执行请求"""
    parameters: Dict[str, Any] = Field(default_factory=dict, description="工具参数")
