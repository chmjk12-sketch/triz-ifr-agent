"""
TRIZ IFR Agent API 端点实现
"""
import os
import json
import httpx
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse

from src.config import get_settings, Settings
from src.models.schemas import (
    SolveRequest, SolveResponse,
    Node1Deconstruction, Node2IFRAnchor,
    Node3ResourceScan, Node4ActionablePlan,
    ResourceItem, PhysicalContradiction,
    ActionStep, ToolExecuteRequest
)

router = APIRouter()


@router.post("/solve", response_model=SolveResponse)
async def solve_triz_ifr(
    request: SolveRequest,
    settings: Settings = Depends(get_settings)
) -> SolveResponse:
    """
    TRIZ IFR 逆向收敛求解主入口

    执行通用求解四步法：
    1. 问题功能化解构
    2. 极致 IFR 顶点锚定
    3. 逆向资源扫描与核心冲突
    4. 可执行落地方案输出
    """
    try:
        # Node 1: 问题功能化解构
        node1 = await _node1_deconstruct(request, settings)

        # Node 2: 极致 IFR 顶点锚定
        node2 = await _node2_anchor_ifr(request, node1, settings)

        # Node 3: 逆向资源扫描与核心冲突
        node3 = await _node3_resource_scan(request, node1, node2, settings)

        # Node 4: 可执行落地方案输出
        node4 = await _node4_actionable_plan(request, node1, node2, node3, settings)

        return SolveResponse(
            code=0,
            data={
                "node1_deconstruction": node1.model_dump(),
                "node2_ifr_anchor": node2.model_dump(),
                "node3_resource_scan": node3.model_dump(),
                "node4_actionable_plan": node4.model_dump()
            },
            message="TRIZ IFR 逆向收敛求解完成"
        )

    except Exception as e:
        return SolveResponse(
            code=500,
            data={},
            message=f"求解失败: {str(e)}"
        )


async def _node1_deconstruct(
    request: SolveRequest,
    settings: Settings
) -> Node1Deconstruction:
    """Node 1: 问题功能化解构"""

    # 基于规则引擎的问题解析
    problem = request.problem
    industry = request.industry or "通用"

    # 识别终极功能（核心动词 + 对象）
    ultimate_function = _extract_ultimate_function(problem)

    # 识别有害/限制因素
    harmful_factors = _extract_harmful_factors(problem, request.constraints)

    # 识别并剪枝低理想度路径
    low_ideality_traps = _identify_low_ideality_traps(problem, industry)

    # 构建功能分解树
    function_tree = {
        "root": ultimate_function,
        "branches": [
            {"name": "核心功能", "description": ultimate_function},
            {"name": "消除有害", "factors": harmful_factors},
            {"name": "避免陷阱", "traps": low_ideality_traps}
        ]
    }

    return Node1Deconstruction(
        ultimate_function=ultimate_function,
        harmful_factors=harmful_factors,
        low_ideality_traps=low_ideality_traps,
        function_tree=function_tree
    )


async def _node2_anchor_ifr(
    request: SolveRequest,
    node1: Node1Deconstruction,
    settings: Settings
) -> Node2IFRAnchor:
    """Node 2: 极致 IFR 顶点锚定"""

    # 根据问题特征选择 IFR 公式类型
    formula_type = _select_ifr_formula(node1)

    # 构建 IFR 描述
    ifr_description = _build_ifr_description(node1, formula_type)

    # 定义理想状态
    ideal_state = {
        "formula_type": formula_type,
        "entity_status": "消失或最小化" if formula_type == "entity_vanish" else "转化",
        "function_status": "自动实现",
        "resource_status": "外部免费资源替代",
        "cost_status": "趋近于零"
    }

    # 评估可行性差距
    feasibility_gap = _assess_feasibility_gap(node1, formula_type)

    return Node2IFRAnchor(
        ifr_formula_type=formula_type,
        ifr_description=ifr_description,
        ideal_state=ideal_state,
        feasibility_gap=feasibility_gap
    )


async def _node3_resource_scan(
    request: SolveRequest,
    node1: Node1Deconstruction,
    node2: Node2IFRAnchor,
    settings: Settings
) -> Node3ResourceScan:
    """Node 3: 逆向资源扫描与核心冲突"""

    # 识别物理矛盾
    contradictions = _identify_physical_contradictions(node1, node2)

    # 扫描外部生态资源
    external_resources = await _scan_external_resources(
        node1.ultimate_function,
        node1.harmful_factors,
        request.industry,
        settings
    )

    # 识别资源缺口
    resource_gaps = _identify_resource_gaps(node1, external_resources)

    # 矛盾解决思路
    resolution = _generate_contradiction_resolution(contradictions, external_resources)

    return Node3ResourceScan(
        physical_contradictions=contradictions,
        external_resources=external_resources,
        resource_gaps=resource_gaps,
        contradiction_resolution=resolution
    )


async def _node4_actionable_plan(
    request: SolveRequest,
    node1: Node1Deconstruction,
    node2: Node2IFRAnchor,
    node3: Node3ResourceScan,
    settings: Settings
) -> Node4ActionablePlan:
    """Node 4: 可执行落地方案输出"""

    # 获取源
    acquisition_sources = _build_acquisition_sources(node3.external_resources)

    # 提取算法
    extraction_algorithms = _build_extraction_algorithms(node1, node3)

    # 融合机制
    fusion_mechanisms = _build_fusion_mechanisms(node1, node2, node3)

    # 行动步骤
    action_steps = _build_action_steps(node1, node2, node3)

    # 成功指标
    success_metrics = [
        f"实现 {node1.ultimate_function} 的核心功能",
        "外部资源利用率 >= 80%",
        "成本控制在传统方案的 20% 以内",
        "有害因素消除率 >= 90%"
    ]

    # 风险缓解
    risk_mitigation = [
        "外部资源失效时启用备用资源",
        "分阶段验证，每阶段设置检查点",
        "保持与外部资源提供方的社区联系",
        "文档化所有资源依赖关系"
    ]

    return Node4ActionablePlan(
        acquisition_sources=acquisition_sources,
        extraction_algorithms=extraction_algorithms,
        fusion_mechanisms=fusion_mechanisms,
        action_steps=action_steps,
        success_metrics=success_metrics,
        risk_mitigation=risk_mitigation
    )


# ============ 辅助函数 ============

def _extract_ultimate_function(problem: str) -> str:
    """提取终极功能"""
    # 简化的功能提取逻辑
    keywords = ["实现", "完成", "达成", "解决", "优化", "提升", "降低", "消除"]
    for kw in keywords:
        if kw in problem:
            idx = problem.find(kw)
            return problem[idx:idx+30] + "..."
    return problem[:50]


def _extract_harmful_factors(problem: str, constraints: List[str]) -> List[str]:
    """提取有害/限制因素"""
    harmful_keywords = ["成本高", "复杂", "慢", "不稳定", "风险", "限制", "瓶颈", "依赖"]
    factors = []
    for kw in harmful_keywords:
        if kw in problem:
            factors.append(kw)
    factors.extend(constraints)
    return factors if factors else ["待识别的限制因素"]


def _identify_low_ideality_traps(problem: str, industry: str) -> List[str]:
    """识别低理想度陷阱"""
    traps = [
        "增加人力投入",
        "增加预算/采购新设备",
        "增加系统复杂度",
        "引入新的依赖项",
        "延长项目周期"
    ]
    return traps


def _select_ifr_formula(node1: Node1Deconstruction) -> str:
    """选择 IFR 公式类型"""
    # 根据有害因素特征选择
    if any("实体" in f or "载体" in f for f in node1.harmful_factors):
        return "entity_vanish"
    elif any("副作用" in f or "有害" in f for f in node1.harmful_factors):
        return "harmful_becomes_useful"
    else:
        return "external_resource"


def _build_ifr_description(node1: Node1Deconstruction, formula_type: str) -> str:
    """构建 IFR 描述"""
    if formula_type == "entity_vanish":
        return f"系统无需任何实体载体，{node1.ultimate_function} 自动实现"
    elif formula_type == "harmful_becomes_useful":
        return f"原有有害因素转化为实现 {node1.ultimate_function} 的工具"
    else:
        return f"利用外部免费生态资源，零成本实现 {node1.ultimate_function}"


def _assess_feasibility_gap(node1: Node1Deconstruction, formula_type: str) -> str:
    """评估可行性差距"""
    return f"从当前状态到 IFR 需要消除 {len(node1.harmful_factors)} 个有害因素，需要外部资源替代 {len(node1.low_ideality_traps)} 个传统方案"


def _identify_physical_contradictions(
    node1: Node1Deconstruction,
    node2: Node2IFRAnchor
) -> List[PhysicalContradiction]:
    """识别物理矛盾"""
    contradictions = []

    # 基于有害因素生成矛盾
    for factor in node1.harmful_factors[:3]:
        contradictions.append(PhysicalContradiction(
            parameter=factor,
            requirement_a=f"为了消除 {factor}，系统必须去除相关组件",
            requirement_not_a=f"为了维持功能，系统必须保留相关组件",
            separation_strategy="空间分离或条件分离"
        ))

    return contradictions


async def _scan_external_resources(
    ultimate_function: str,
    harmful_factors: List[str],
    industry: Optional[str],
    settings: Settings
) -> List[ResourceItem]:
    """扫描外部生态资源"""

    resources = []

    # 开源代码资源
    resources.append(ResourceItem(
        name="GitHub 开源项目",
        source="GitHub",
        url="https://github.com/search",
        cost_type="free",
        description=f"搜索与 {ultimate_function} 相关的开源实现",
        relevance_score=0.9
    ))

    # 学术论文资源
    resources.append(ResourceItem(
        name="arXiv 学术论文",
        source="arXiv",
        url="https://arxiv.org/search",
        cost_type="free",
        description=f"搜索 {ultimate_function} 相关的最新研究成果",
        relevance_score=0.8
    ))

    # 行业数据资源
    resources.append(ResourceItem(
        name="Kaggle 数据集",
        source="Kaggle",
        url="https://kaggle.com/datasets",
        cost_type="free",
        description="获取行业相关数据集用于分析",
        relevance_score=0.7
    ))

    # 知识库资源
    resources.append(ResourceItem(
        name="Wikipedia / 维基百科",
        source="Wikipedia",
        url="https://en.wikipedia.org",
        cost_type="free",
        description="获取基础概念和背景知识",
        relevance_score=0.6
    ))

    # Stack Overflow
    resources.append(ResourceItem(
        name="Stack Overflow 问答",
        source="Stack Overflow",
        url="https://stackoverflow.com",
        cost_type="free",
        description="获取技术实现的具体方案",
        relevance_score=0.75
    ))

    return resources


def _identify_resource_gaps(
    node1: Node1Deconstruction,
    resources: List[ResourceItem]
) -> List[str]:
    """识别资源缺口"""
    gaps = []
    # 检查是否覆盖了所有有害因素
    covered_factors = set()
    for r in resources:
        for f in node1.harmful_factors:
            if f in r.description:
                covered_factors.add(f)

    for f in node1.harmful_factors:
        if f not in covered_factors:
            gaps.append(f"缺少针对 '{f}' 的专门资源")

    return gaps if gaps else ["资源覆盖基本完整，建议深入挖掘"]


def _generate_contradiction_resolution(
    contradictions: List[PhysicalContradiction],
    resources: List[ResourceItem]
) -> str:
    """生成矛盾解决思路"""
    return (
        f"通过引入 {len(resources)} 个外部免费资源，"
        f"采用空间分离策略解决 {len(contradictions)} 个物理矛盾，"
        "实现系统参数的条件自适应调整"
    )


def _build_acquisition_sources(resources: List[ResourceItem]) -> List[Dict[str, str]]:
    """构建获取源"""
    return [
        {
            "platform": r.source,
            "url": r.url or "",
            "search_query": r.description,
            "access_method": "API 或网页搜索"
        }
        for r in resources
    ]


def _build_extraction_algorithms(
    node1: Node1Deconstruction,
    node3: Node3ResourceScan
) -> List[Dict[str, str]]:
    """构建提取算法"""
    return [
        {
            "name": "关键词匹配与语义分析",
            "description": "从外部资源中提取与终极功能相关的核心概念",
            "input": "原始文本/代码/数据",
            "output": "结构化知识图谱"
        },
        {
            "name": "跨模态特征工程",
            "description": "将不同来源的资源转化为统一的特征表示",
            "input": "多源异构数据",
            "output": "标准化特征向量"
        },
        {
            "name": "历史回测验证",
            "description": "验证外部资源方案在类似场景中的有效性",
            "input": "历史案例库",
            "output": "可行性评估报告"
        }
    ]


def _build_fusion_mechanisms(
    node1: Node1Deconstruction,
    node2: Node2IFRAnchor,
    node3: Node3ResourceScan
) -> List[Dict[str, str]]:
    """构建融合机制"""
    return [
        {
            "name": "资源适配层",
            "description": "将外部资源格式转换为系统内部可用格式",
            "implementation": "数据清洗 + 格式转换 + 质量校验"
        },
        {
            "name": "矛盾消解引擎",
            "description": "应用 TRIZ 分离原理解决物理矛盾",
            "implementation": "空间分离 + 时间分离 + 条件分离 + 系统级别分离"
        },
        {
            "name": "渐进式集成",
            "description": "分阶段将外部资源集成到现有系统中",
            "implementation": "试点验证 → 局部集成 → 全面部署"
        }
    ]


def _build_action_steps(
    node1: Node1Deconstruction,
    node2: Node2IFRAnchor,
    node3: Node3ResourceScan
) -> List[ActionStep]:
    """构建行动步骤"""
    return [
        ActionStep(
            step_number=1,
            title="资源搜索与收集",
            description="在 GitHub、arXiv、Kaggle 等平台搜索相关资源",
            expected_output="资源清单与初步评估",
            estimated_effort="1-2 天"
        ),
        ActionStep(
            step_number=2,
            title="资源质量评估",
            description="评估收集到的资源的相关性、可靠性和可用性",
            expected_output="资源质量评分报告",
            estimated_effort="0.5-1 天"
        ),
        ActionStep(
            step_number=3,
            title="矛盾分析与分离",
            description="应用 TRIZ 分离原理解决识别的物理矛盾",
            expected_output="矛盾解决方案",
            estimated_effort="1-2 天"
        ),
        ActionStep(
            step_number=4,
            title="原型验证",
            description="构建最小可行原型验证方案可行性",
            expected_output="可运行的原型系统",
            estimated_effort="3-5 天"
        ),
        ActionStep(
            step_number=5,
            title="集成与优化",
            description="将验证通过的方案集成到生产环境",
            expected_output="生产就绪的解决方案",
            estimated_effort="2-3 天"
        )
    ]
