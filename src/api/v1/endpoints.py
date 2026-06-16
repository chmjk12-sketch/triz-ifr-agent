"""
TRIZ IFR Agent API 端点实现 — 深度分析引擎 v2.0

基于经典 TRIZ 理论的倒推思维漏斗收敛模型，包含：
  - 40 个发明原理映射
  - 矛盾矩阵自动匹配
  - 多维度 IFR 评估
  - 资源分类扫描引擎
  - 工程可执行性验证
"""
import os
import re
import json
import httpx
from typing import Dict, Any, List, Optional
from enum import Enum
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

# ============================================================
# TRIZ 知识库
# ============================================================

TRIZ_40_PRINCIPLES = {
    1: ("分割", "将物体分成独立部分；使物体模块化；增加分割程度"),
    2: ("抽取", "从物体中抽取（去除）干扰部分或必要部分"),
    3: ("局部质量", "使物体各部位处于不同的条件；使各部位执行不同功能"),
    4: ("不对称", "用不对称形式代替对称形式；增加不对称程度"),
    5: ("合并", "合并相同或相邻的物体或操作"),
    6: ("通用性", "使物体能执行多个功能，减少系统数量"),
    7: ("套叠", "将一个物体放在另一物体内；一个穿过另一个"),
    8: ("重量补偿", "用反重力或与环境交互来补偿重量"),
    9: ("预先反作用", "预先施加反作用力以消除后续有害作用"),
    10: ("预先作用", "预先放置物体在需要位置；预先完成部分功能"),
    11: ("预补偿", "用预先准备好的应急手段补偿低可靠性"),
    12: ("等势性", "改变工作条件以减少升降需求"),
    13: ("反向", "用相反的动作代替规定动作"),
    14: ("曲面化", "将直线变为曲线或球面；使用旋转运动"),
    15: ("动态性", "使物体或环境自动调整到最优状态"),
    16: ("不足/过量", "当精确效果难以达到时使用稍多或稍少的量"),
    17: ("向另一维度", "将一维运动变为二维/三维运动"),
    18: ("机械振动", "使用振动或振荡"),
    19: ("周期性作用", "使用周期性或脉冲动作代替连续动作"),
    20: ("有效作用的连续性", "连续工作，消除空闲或中断"),
    21: ("快速通过", "高速执行有害或危险操作"),
    22: ("变害为利", "利用有害因素获得正面效果"),
    23: ("反馈", "引入反馈机制"),
    24: ("中介物", "使用中介体传递或执行动作"),
    25: ("自服务", "使物体自我服务并利用废弃资源"),
    26: ("复制", "用廉价的复制品代替昂贵的原件"),
    27: ("廉价替代", "用廉价物体代替昂贵的"),
    28: ("机械系统替代", "用光学/声学/电磁等替代机械系统"),
    29: ("气动/液压", "用气体或液体部件替代固体部件"),
    30: ("柔性壳体/薄膜", "使用柔性壳体或薄膜"),
    31: ("多孔材料", "使物体多孔或使用多孔材料"),
    32: ("颜色改变", "改变颜色或透明度"),
    33: ("均质性", "使相互作用物体由同种材料制成"),
    34: ("废弃与再生", "排除或再生部分"),
    35: ("参数变化", "改变物理/化学状态、密度、温度等"),
    36: ("相变", "利用相变时产生的效应"),
    37: ("热膨胀", "利用热膨胀或热收缩"),
    38: ("加速氧化", "增加氧化程度"),
    39: ("惰性环境", "在惰性环境中进行过程"),
    40: ("复合材料", "用复合材料代替均质材料")
}

TRIZ_CONTRADICTION_MATRIX = {
    # (improving_feature, worsening_feature) → list of principle numbers
    # 常用矛盾对
    ("speed", "power"): [28, 21, 35, 13],
    ("speed", "accuracy"): [28, 13, 23, 26],
    ("power", "speed"): [2, 13, 28, 35],
    ("reliability", "complexity"): [1, 17, 28, 10],
    ("reliability", "cost"): [27, 35, 1, 24],
    ("performance", "cost"): [6, 27, 25, 1],
    ("performance", "complexity"): [26, 13, 1, 29],
    ("quality", "time"): [29, 35, 21, 10],
    ("quality", "cost"): [27, 1, 6, 35],
    ("adaptability", "complexity"): [15, 29, 1, 28],
    ("simplicity", "performance"): [1, 26, 6, 15],
    ("capacity", "space"): [7, 17, 5, 3],
    ("convenience", "cost"): [27, 6, 15, 28],
    ("security", "complexity"): [11, 24, 28, 35]
}

DOMAIN_MATRIX = {
    "软件开发": {
        "keywords": ["软件", "代码", "系统", "开发", "程序", "应用", "数据库", "API", "架构"],
        "patterns": ["性能", "响应", "延迟", "并发", "扩展", "维护", "测试"],
        "open_resources": ["GitHub", "npm", "PyPI", "Docker Hub", "Stack Overflow", "CodePen"]
    },
    "制造": {
        "keywords": ["生产", "制造", "加工", "装配", "工艺", "设备"],
        "patterns": ["效率", "良率", "能耗", "材料", "精度"],
        "open_resources": ["国家智能制造标准", "ISO 标准", "知网数据库", "专利检索"]
    },
    "商业": {
        "keywords": ["市场", "营收", "客户", "运营", "销售", "营销"],
        "patterns": ["成本", "转化", "获客", "留存", "效率"],
        "open_resources": ["国家统计局", "天眼查", "企查查", "巨量算数"]
    },
    "教育": {
        "keywords": ["学习", "教学", "课程", "学生", "培训", "知识"],
        "patterns": ["效率", "参与", "评估", "个性化"],
        "open_resources": ["MOOC平台", "知网", "arXiv", "OER Commons"]
    },
    "医疗": {
        "keywords": ["医疗", "诊断", "治疗", "患者", "临床", "药物"],
        "patterns": ["准确率", "效率", "成本", "安全性"],
        "open_resources": ["PubMed", "ClinicalTrials.gov", "WHO 数据库"]
    }
}

DOMAIN_UNKNOWN = {
    "keywords": [],
    "patterns": [],
    "open_resources": ["arXiv", "Google Scholar", "GitHub", "Wikipedia", "Stack Exchange", "Kaggle"]
}

# ============================================================
# 节点 1：问题功能化解构 — 深度语义分析引擎
# ============================================================

class ProblemAnalyzer:
    """深度问题分析器 — 从多个维度解构问题"""

    @staticmethod
    def detect_domain(problem: str, industry: Optional[str]) -> tuple:
        """检测问题所属领域"""
        if industry:
            for key, val in DOMAIN_MATRIX.items():
                if key in industry:
                    return key, val
        problem_lower = problem.lower()
        for key, val in DOMAIN_MATRIX.items():
            if any(kw in problem_lower for kw in val["keywords"]):
                return key, val
        return "通用", DOMAIN_UNKNOWN

    @staticmethod
    def extract_core_function(problem: str) -> Dict[str, Any]:
        """提取核心功能（动词+宾语+约束条件）"""
        # 中文功能动词模式
        verb_patterns = [
            (r'(提高|提升|增加|增强|加速)(.*)', "improve"),
            (r'(降低|减少|消除|避免|删减|压缩)(.*)', "reduce"),
            (r'(优化|改进|完善|改良|升级)(.*)', "optimize"),
            (r'(实现|构建|创建|搭建|开发)(.*)', "create"),
            (r'(维持|保持|稳定)(.*)', "maintain"),
            (r'(监控|检测|测量|追踪)(.*)', "monitor"),
            (r'(预测|预估|预判)(.*)', "predict"),
            (r'(自动化|替代|替换)(.*)', "automate"),
        ]

        for pattern, action_type in verb_patterns:
            match = re.search(pattern, problem)
            if match:
                target = match.group(2).strip() if match.lastindex >= 2 else problem
                return {
                    "action_type": action_type,
                    "action_verb": match.group(1).strip(),
                    "target": target[:50],
                    "original": problem[:80]
                }

        # 如果没匹配到动词，使用默认分析
        return {
            "action_type": "optimize",
            "action_verb": "优化",
            "target": problem[:50],
            "original": problem[:80]
        }

    @staticmethod
    def analyze_dimensions(problem: str, constraints: List[str]) -> Dict[str, Any]:
        """多维度分析：功能、成本、时间、质量、环境"""
        dimensions = {
            "function": {"score": 0.5, "description": "", "bottleneck": False},
            "cost": {"score": 0.5, "description": "", "bottleneck": False},
            "time": {"score": 0.5, "description": "", "bottleneck": False},
            "quality": {"score": 0.5, "description": "", "bottleneck": False},
            "complexity": {"score": 0.5, "description": "", "bottleneck": False},
        }

        problem_lower = problem.lower()
        combined = problem_lower + " " + " ".join(constraints).lower()

        # 成本维度
        if any(w in combined for w in ["成本", "预算", "费用", "钱", "投入", "资金", "money", "budget", "cost"]):
            dimensions["cost"] = {"score": 0.8, "description": "成本约束显著，是核心限制条件", "bottleneck": True}

        # 时间维度
        if any(w in combined for w in ["时间", "速度", "延迟", "响应", "效率", "time", "speed", "latency"]):
            dimensions["time"] = {"score": 0.7, "description": "时间效率是关键需求", "bottleneck": True}

        # 质量维度
        if any(w in combined for w in ["质量", "精度", "准确", "可靠", "稳定", "quality", "accuracy", "reliable"]):
            dimensions["quality"] = {"score": 0.7, "description": "质量/可靠性要求高", "bottleneck": True}

        # 复杂度维度
        if any(w in combined for w in ["复杂", "维护", "扩展", "技术债务", "complex", "maintenance"]):
            dimensions["complexity"] = {"score": 0.6, "description": "系统复杂度需要控制", "bottleneck": True}

        # 功能维度
        if any(w in combined for w in ["功能", "性能", "能力", "容量", "feature", "capability"]):
            dimensions["function"] = {"score": 0.7, "description": "核心功能需要增强", "bottleneck": True}

        return dimensions

    @staticmethod
    def identify_traps(problem: str, domain: str) -> List[Dict[str, Any]]:
        """识别低理想度陷阱，给出具体替代方向"""
        traps = [
            {
                "trap": "增加人力投入",
                "description": f"在{domain}领域，加人的边际效益递减，且引入沟通成本和管理复杂度",
                "principle": TRIZ_40_PRINCIPLES[25],  # 自服务
                "alternative": "优先考虑自动化工具和自服务机制，让系统自我维护"
            },
            {
                "trap": "增加预算/采购新设备",
                "description": "采购新设备虽然短期有效，但引入额外学习成本、维护成本和兼容性风险",
                "principle": TRIZ_40_PRINCIPLES[27],  # 廉价替代
                "alternative": "用已有的开源/免费方案替代，或使用 SaaS 按需付费模式"
            },
            {
                "trap": "增加系统复杂度",
                "description": "增加组件提升复杂度，违反 TRIZ 理想度原则：理想系统是功能存在而系统本身不存在",
                "principle": TRIZ_40_PRINCIPLES[1],  # 分割
                "alternative": "模块化拆分，将复杂系统分解为独立可替换的微服务或模块"
            },
            {
                "trap": "引入新的依赖项",
                "description": "新依赖带来版本管理风险、安全漏洞面和供应中断风险",
                "principle": TRIZ_40_PRINCIPLES[6],  # 通用性
                "alternative": "增强现有组件的能力使其自包含，减少外部依赖"
            },
            {
                "trap": "延长项目周期",
                "description": "时间延长通常不会提升质量，反而增加需求变更风险和机会成本",
                "principle": TRIZ_40_PRINCIPLES[10],  # 预先作用
                "alternative": "采用 MVP 快速交付 + 迭代优化策略"
            }
        ]
        return traps

    @staticmethod
    def build_function_tree(problem: str, core_function: Dict, dimensions: Dict, traps: List) -> Dict:
        """构建层次化功能分解树"""
        bottlenecks = [k for k, v in dimensions.items() if v.get("bottleneck")]

        return {
            "root": {
                "name": core_function["target"],
                "type": core_function["action_type"],
                "verb": core_function["action_verb"]
            },
            "branches": [
                {
                    "name": "主功能实现路径",
                    "type": "functional",
                    "detail": core_function["target"],
                    "success_criteria": f"核心指标提升 ≥30%"
                },
                {
                    "name": "约束条件处理",
                    "type": "constraint",
                    "bottlenecks": bottlenecks,
                    "detail": f"需要消除 {len(bottlenecks)} 个瓶颈维度: {', '.join(bottlenecks)}"
                },
                {
                    "name": "低理想度路径规避",
                    "type": "avoidance",
                    "traps_count": len(traps),
                    "detail": "已识别并剪枝低理想度的传统方案"
                },
                {
                    "name": "外部资源映射",
                    "type": "resource",
                    "detail": "需要扫描外部免费生态资源替代内部损耗"
                }
            ],
            "ideal_direction": {
                "principle": "IFR: 功能实现，系统消失",
                "gap": f"当前距 IFR 差距: {len(bottlenecks)} 个约束维度待消除"
            }
        }

    @staticmethod
    def extract_contradiction_parameters(problem: str, dimensions: Dict) -> List[str]:
        """提取矛盾参数对"""
        params = []
        bottlenecks = [k for k, v in dimensions.items() if v.get("bottleneck")]

        # 常见的矛盾参数映射
        param_map = {
            "function": "performance",
            "cost": "cost",
            "time": "speed",
            "quality": "quality",
            "complexity": "complexity"
        }

        if len(bottlenecks) >= 2:
            for i in range(len(bottlenecks)):
                for j in range(i+1, len(bottlenecks)):
                    p1 = param_map.get(bottlenecks[i], bottlenecks[i])
                    p2 = param_map.get(bottlenecks[j], bottlenecks[j])
                    params.append(f"{p1} ↔ {p2}")

        if not params:
            params.append("performance ↔ cost")

        return params


# ============================================================
# 节点 2：IFR 顶点锚定 — 多维度理想终局定义
# ============================================================

class IFRAnalyzer:
    """IFR 深度分析器 — 从 3 个公式 + 5 个维度定义理想终局"""

    @staticmethod
    def evaluate_formulas(problem: str, core_function: Dict, dimensions: Dict) -> List[Dict]:
        """评估 3 种 IFR 公式的适用性并打分"""
        formulas = []

        # 公式 1: 实体消失
        score1 = 0.0
        if dimensions["cost"].get("bottleneck"):
            score1 += 0.3
        if dimensions["complexity"].get("bottleneck"):
            score1 += 0.3
        score1 += 0.2  # 基准分

        formulas.append({
            "type": "entity_vanish",
            "name": "载体消失型 IFR",
            "score": round(score1, 2),
            "description": f"系统实体/载体消失，但'{core_function['target']}'功能自动实现",
            "conditions": [
                "移除所有物理/软件载体",
                "功能以场/信息/服务形式存在",
                "零维护成本",
                "零空间占用"
            ],
            "applicability": "高" if score1 > 0.6 else "中",
            "triz_principles": [TRIZ_40_PRINCIPLES[28], TRIZ_40_PRINCIPLES[25]]
        })

        # 公式 2: 有害转有用
        score2 = 0.0
        if any(f.get("bottleneck") for f in dimensions.values()):
            score2 += 0.3
        score2 += 0.2

        formulas.append({
            "type": "harmful_becomes_useful",
            "name": "矛盾转化型 IFR",
            "score": round(score2, 2),
            "description": f"原有有害副作用/限制条件，本身变成实现'{core_function['target']}'的工具",
            "conditions": [
                "识别至少一个有害因素",
                "有害因素蕴含可用能量/信息/物质",
                "设计转换机制将有害变为有益",
                "零额外成本投入"
            ],
            "applicability": "高" if score2 > 0.6 else "中",
            "triz_principles": [TRIZ_40_PRINCIPLES[22], TRIZ_40_PRINCIPLES[23]]
        })

        # 公式 3: 外部免费资源
        score3 = 0.4  # 基准分最高（最实用）
        if dimensions["cost"].get("bottleneck"):
            score3 += 0.3
        score3 += 0.1

        formulas.append({
            "type": "external_resource",
            "name": "生态借力型 IFR",
            "score": round(score3, 2),
            "description": f"引入外部现有的免费'无形资产/生态资源'，代替系统内部损耗以实现'{core_function['target']}'",
            "conditions": [
                "定位至少 3 个外部免费资源池",
                "资源可零成本获取",
                "资源可转化为内部可用参数",
                "资源可持续更新"
            ],
            "applicability": "高" if score3 > 0.6 else "中",
            "triz_principles": [TRIZ_40_PRINCIPLES[6], TRIZ_40_PRINCIPLES[27]]
        })

        # 按分数排序
        formulas.sort(key=lambda x: x["score"], reverse=True)
        return formulas

    @staticmethod
    def build_ideal_state(problem: str, core_function: Dict, best_formula: Dict, dimensions: Dict) -> Dict:
        """构建详细的理想状态定义"""
        return {
            "formula": best_formula["name"],
            "formula_type": best_formula["type"],
            "state_description": best_formula["description"],
            "dimension_states": {
                "functional": {
                    "current": f"需要{core_function['action_type']} {core_function['target']}",
                    "ideal": f"{core_function['target']}已自动达到最优状态",
                    "gap_metric": "从手动到自动的转化度"
                },
                "cost": {
                    "current": f"当前成本约束等级: {'高' if dimensions['cost'].get('bottleneck') else '中'}",
                    "ideal": "趋近于零的边际成本",
                    "gap_metric": "成本降幅百分比"
                },
                "time": {
                    "current": f"时间效率等级: {'高' if dimensions['time'].get('bottleneck') else '中'}",
                    "ideal": "即时响应，零等待",
                    "gap_metric": "响应时间缩短倍数"
                },
                "quality": {
                    "current": f"质量等级: {'高' if dimensions['quality'].get('bottleneck') else '中'}",
                    "ideal": "无缺陷、100%可靠性",
                    "gap_metric": "缺陷率降低百分比"
                },
                "complexity": {
                    "current": f"复杂度等级: {'高' if dimensions['complexity'].get('bottleneck') else '中'}",
                    "ideal": "零复杂度，用户感知不到系统存在",
                    "gap_metric": "用户交互步骤减少数"
                }
            },
            "ideal_metrics": {
                "cost_reduction": "80-100%",
                "time_reduction": "60-90%",
                "quality_improvement": "3-10x",
                "complexity_reduction": "50-80%"
            }
        }

    @staticmethod
    def assess_feasibility(best_formula: Dict, dimensions: Dict) -> Dict:
        """可行性评估"""
        score = best_formula["score"]

        barriers = []
        enablers = []

        if dimensions["cost"].get("bottleneck"):
            barriers.append("成本约束严格，资源获取受限")
            enablers.append("成本约束倒逼创新，天然拒绝低理想度方案")

        if dimensions["time"].get("bottleneck"):
            barriers.append("时间效率要求高，迭代窗口短")
            enablers.append("时间压力迫使寻找敏捷方案")

        if dimensions["complexity"].get("bottleneck"):
            barriers.append("系统复杂度需保持低位")
            enablers.append("复杂度约束天然导向 IFR 方向")

        return {
            "feasibility_score": round(score * 10, 1),
            "feasibility_level": "高" if score > 0.6 else ("中" if score > 0.4 else "低"),
            "assessment": f"IFR 可行性评分 {round(score * 10, 1)}/10，{best_formula['name']}具有{'较好的' if score > 0.5 else '一般的'}可行性基础",
            "barriers": barriers,
            "enablers": enablers,
            "next_step": "进入逆向折返阶段，从 IFR 顶点向现实扫描可用资源" if score > 0.4 else "建议重新定义问题范围"
        }


# ============================================================
# 节点 3：逆向资源扫描 + 矛盾分析
# ============================================================

class ResourceScanner:
    """生态资源扫描器 — 从 6 个维度扫描外部免费资源"""

    RESOURCE_CATEGORIES = {
        "开源代码": {
            "description": "开源代码库和框架",
            "cost": "free",
            "platforms": [
                {"name": "GitHub", "url": "https://github.com", "type": "代码托管", "coverage": "全球最大开源社区"},
                {"name": "GitLab", "url": "https://gitlab.com", "type": "代码托管", "coverage": "企业级开源"},
                {"name": "SourceForge", "url": "https://sourceforge.net", "type": "代码托管", "coverage": "历史悠久的开源库"}
            ]
        },
        "学术知识": {
            "description": "学术论文和研究成果",
            "cost": "free",
            "platforms": [
                {"name": "arXiv", "url": "https://arxiv.org", "type": "预印本", "coverage": "200万+论文"},
                {"name": "Google Scholar", "url": "https://scholar.google.com", "type": "搜索引擎", "coverage": "全学科"},
                {"name": "Semantic Scholar", "url": "https://semanticscholar.org", "type": "AI 论文搜索", "coverage": "1.8亿+论文"},
                {"name": "PubMed Central", "url": "https://www.ncbi.nlm.nih.gov/pmc/", "type": "生命科学", "coverage": "700万+全文"}
            ]
        },
        "数据资源": {
            "description": "开放数据集和公共数据",
            "cost": "free",
            "platforms": [
                {"name": "Kaggle", "url": "https://kaggle.com/datasets", "type": "竞赛/数据集", "coverage": "5万+数据集"},
                {"name": "Hugging Face", "url": "https://huggingface.co/datasets", "type": "ML 数据集", "coverage": "10万+数据集"},
                {"name": "Google Dataset Search", "url": "https://datasetsearch.research.google.com", "type": "搜索引擎", "coverage": "2500万+数据集"}
            ]
        },
        "AI/模型": {
            "description": "预训练 AI 模型和 API",
            "cost": "free",
            "platforms": [
                {"name": "Hugging Face Models", "url": "https://huggingface.co/models", "type": "模型库", "coverage": "50万+模型"},
                {"name": "Ollama", "url": "https://ollama.ai", "type": "本地 LLM", "coverage": "100+开源模型"},
                {"name": "TensorFlow Hub", "url": "https://tfhub.dev", "type": "模型库", "coverage": "2000+模型"}
            ]
        },
        "技术社区": {
            "description": "技术问答和最佳实践",
            "cost": "free",
            "platforms": [
                {"name": "Stack Overflow", "url": "https://stackoverflow.com", "type": "Q&A", "coverage": "2400万+问题"},
                {"name": "Medium/Towards Data Science", "url": "https://towardsdatascience.com", "type": "技术博客", "coverage": "行业实践"},
                {"name": "Dev.to", "url": "https://dev.to", "type": "开发者社区", "coverage": "100万+文章"}
            ]
        },
        "基础设施": {
            "description": "免费云服务和开发工具",
            "cost": "free",
            "platforms": [
                {"name": "GitHub Actions", "url": "https://github.com/features/actions", "type": "CI/CD", "coverage": "2000分钟/月免费"},
                {"name": "Vercel", "url": "https://vercel.com", "type": "托管", "coverage": "100GB带宽/月"},
                {"name": "Cloudflare", "url": "https://cloudflare.com", "type": "CDN/安全", "coverage": "无限流量"},
                {"name": "Supabase", "url": "https://supabase.com", "type": "BaaS", "coverage": "500MB数据库免费"}
            ]
        }
    }

    @staticmethod
    def scan(problem: str, core_function: Dict, domain_info: tuple) -> List[Dict]:
        """扫描外部资源并打分"""
        results = []
        problem_lower = problem.lower()

        for cat_name, category in ResourceScanner.RESOURCE_CATEGORIES.items():
            for platform in category["platforms"]:
                # 相关性评分
                relevance = 0.5

                # 基于问题关键词评分
                if any(kw in problem_lower for kw in ["代码", "开发", "软件", "code", "dev"]):
                    if cat_name == "开源代码":
                        relevance += 0.3
                    if cat_name == "技术社区":
                        relevance += 0.2

                if any(kw in problem_lower for kw in ["数据", "分析", "数据挖掘", "data", "analytics"]):
                    if cat_name == "数据资源":
                        relevance += 0.3

                if any(kw in problem_lower for kw in ["AI", "人工智能", "模型", "machine learning", "deep"]):
                    if cat_name == "AI/模型":
                        relevance += 0.3

                if any(kw in problem_lower for kw in ["部署", "上线", "托管", "host", "deploy"]):
                    if cat_name == "基础设施":
                        relevance += 0.3

                # 领域适配
                if domain_info and domain_info != ("通用", DOMAIN_UNKNOWN):
                    relevance += 0.1

                relevance = min(relevance, 1.0)

                extraction_method = ResourceScanner._suggest_extraction(cat_name, core_function)

                results.append({
                    "category": cat_name,
                    "name": platform["name"],
                    "type": platform["type"],
                    "url": platform["url"],
                    "cost_type": category["cost"],
                    "description": platform["coverage"],
                    "relevance_score": round(relevance, 2),
                    "extraction_method": extraction_method,
                    "usage_scenario": ResourceScanner._suggest_usage(cat_name, core_function)
                })

        # 按相关性排序
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:12]  # 返回 Top 12

    @staticmethod
    def _suggest_extraction(category: str, core_function: Dict) -> str:
        """建议资源提取方法"""
        suggestions = {
            "开源代码": f"1) 搜索关键词 '{core_function['target']}' 筛选 Star>100 的项目; 2) 分析 README 和架构文档; 3) 提取可复用模块",
            "学术知识": f"1) 检索 '{core_function['target']}' 近3年论文; 2) 提取算法伪代码; 3) 复现核心实验结果",
            "数据资源": f"1) 搜索相关数据集; 2) 检查数据 Schema 和质量; 3) 特征工程提取可用特征",
            "AI/模型": f"1) 查找 '{core_function['target']}' 预训练模型; 2) 评估模型大小和精度; 3) 迁移学习适配场景",
            "技术社区": f"1) 搜索 '{core_function['target']}' 最佳实践; 2) 汇总多个方案的共识; 3) 提取可复用的代码片段",
            "基础设施": f"1) 评估免费额度是否满足需求; 2) 配置集成方案; 3) 建立监控和告警"
        }
        return suggestions.get(category, "标准接口对接")


    @staticmethod
    def _suggest_usage(category: str, core_function: Dict) -> str:
        """建议使用场景"""
        usages = {
            "开源代码": f"直接集成或修改开源实现加速 {core_function['target']} 的开发",
            "学术知识": f"将最新学术成果转化为 {core_function['target']} 的算法优化方案",
            "数据资源": f"利用公共数据集训练 {core_function['target']} 相关模型",
            "AI/模型": f"基于预训练模型通过微调实现 {core_function['target']} 功能",
            "技术社区": f"参考社区方案避免 {core_function['target']} 实现中的常见陷阱",
            "基础设施": f"用免费基础设施降低 {core_function['target']} 的部署和运维成本"
        }
        return usages.get(category, "行业标准集成")


class ContradictionEngine:
    """TRIZ 矛盾分析引擎"""

    @staticmethod
    def analyze(problem: str, contradiction_params: List[str], dimensions: Dict) -> Dict:
        """深度矛盾分析"""
        contradictions = []
        solutions = []

        for param_pair in contradiction_params:
            parts = param_pair.split(" ↔ ")
            improving = parts[0] if len(parts) > 0 else "performance"
            worsening = parts[1] if len(parts) > 1 else "cost"

            key = (improving, worsening)
            reverse_key = (worsening, improving)

            # 从矛盾矩阵获取发明原理
            principles = TRIZ_CONTRADICTION_MATRIX.get(key, TRIZ_CONTRADICTION_MATRIX.get(reverse_key, [15, 28, 1]))

            principle_details = []
            for p_num in principles[:3]:
                if p_num in TRIZ_40_PRINCIPLES:
                    principle_details.append(TRIZ_40_PRINCIPLES[p_num])

            contradiction = {
                "id": f"C{len(contradictions)+1}",
                "improving_feature": improving,
                "worsening_feature": worsening,
                "description": f"为了提升'{improving}'，'{worsening}'会恶化",
                "suggested_principles": principle_details,
                "separation_strategy": ContradictionEngine._suggest_separation(improving, worsening, dimensions),
                "concrete_example": ContradictionEngine._build_example(improving, worsening, problem[:30])
            }
            contradictions.append(contradiction)

        return {
            "contradictions": contradictions,
            "resolution_summary": f"识别 {len(contradictions)} 个物理矛盾，建议 {sum(len(c['suggested_principles']) for c in contradictions)} 个发明原理",
            "separation_priority": ContradictionEngine._prioritize_separation(dimensions)
        }

    @staticmethod
    def _suggest_separation(improving: str, worsening: str, dimensions: Dict) -> Dict:
        """建议分离策略"""
        strategies = {
            "time": {
                "strategy": "时间分离",
                "description": "在不同时间满足不同需求",
                "example": "系统在工作时间高性能运行，空闲时间执行维护和优化"
            },
            "space": {
                "strategy": "空间分离",
                "description": "在不同空间满足不同需求",
                "example": "将热数据和冷数据存储在不同层级"
            },
            "condition": {
                "strategy": "条件分离",
                "description": "在不同条件下满足不同需求",
                "example": "基于负载动态调整资源分配"
            },
            "system_level": {
                "strategy": "系统级别分离",
                "description": "在系统/子系统/超系统不同层面满足需求",
                "example": "将核心功能放在子系统层，将扩展功能放在超系统层"
            }
        }

        if "time" in improving or "speed" in improving:
            return strategies["time"]
        elif "space" in improving or "capacity" in improving:
            return strategies["space"]
        elif "quality" in improving:
            return strategies["condition"]
        else:
            return strategies["system_level"]

    @staticmethod
    def _build_example(improving: str, worsening: str, problem_context: str) -> str:
        """构建具体的冲突示例"""
        examples = {
            ("performance", "cost"): f"在{problem_context}场景中，提升性能通常需要更多硬件投入，但预算有限",
            ("speed", "accuracy"): f"在{problem_context}场景中，追求速度可能牺牲处理精度",
            ("quality", "cost"): f"在{problem_context}场景中，提高质量往往需要更多测试和验证资源"
        }
        return examples.get((improving, worsening), f"在{problem_context}中，{improving}和{worsening}存在矛盾关系")

    @staticmethod
    def _prioritize_separation(dimensions: Dict) -> List[Dict]:
        """优先级排序"""
        priority = []
        if dimensions.get("time", {}).get("bottleneck"):
            priority.append({"rank": 1, "strategy": "时间分离", "reason": "时间约束是核心瓶颈"})
        if dimensions.get("cost", {}).get("bottleneck"):
            priority.append({"rank": 2, "strategy": "空间/条件分离", "reason": "成本约束需要条件自适应"})
        if dimensions.get("complexity", {}).get("bottleneck"):
            priority.append({"rank": 3, "strategy": "系统级别分离", "reason": "复杂度需要分层处理"})
        return priority


# ============================================================
# 节点 4：可执行落地方案
# ============================================================

class ExecutionPlanner:
    """可执行方案规划器"""

    @staticmethod
    def build_action_plan(
        problem: str,
        core_function: Dict,
        contradictions: Dict,
        resources: List[Dict],
        domain_info: tuple
    ) -> Dict:
        """构建完整的可执行落地方案"""
        domain_name = domain_info[0] if domain_info else "通用"

        # 第一阶段：基础建设
        phase1_steps = ExecutionPlanner._phase1_steps(core_function, domain_name)
        # 第二阶段：资源整合
        phase2_steps = ExecutionPlanner._phase2_steps(resources[:3], domain_name)
        # 第三阶段：矛盾消解
        phase3_steps = ExecutionPlanner._phase3_steps(contradictions)
        # 第四阶段：集成部署
        phase4_steps = ExecutionPlanner._phase4_steps(core_function, domain_name)

        all_steps = phase1_steps + phase2_steps + phase3_steps + phase4_steps

        # 构建融合机制
        fusion_mechanisms = ExecutionPlanner._fusion_mechanisms(core_function, resources)

        # 构建风险矩阵
        risk_matrix = ExecutionPlanner._risk_matrix(domain_name)

        return {
            "phases": [
                {
                    "phase": 1,
                    "name": "基础调研与资源收集",
                    "duration": "1-3 天",
                    "steps": phase1_steps,
                    "deliverable": "资源清单与可行性报告"
                },
                {
                    "phase": 2,
                    "name": "外部资源整合与适配",
                    "duration": "3-7 天",
                    "steps": phase2_steps,
                    "deliverable": "适配后的模块原型"
                },
                {
                    "phase": 3,
                    "name": "矛盾消解与系统集成",
                    "duration": "5-10 天",
                    "steps": phase3_steps,
                    "deliverable": "可运行的系统原型"
                },
                {
                    "phase": 4,
                    "name": "验证优化与部署上线",
                    "duration": "3-5 天",
                    "steps": phase4_steps,
                    "deliverable": "生产就绪的解决方案"
                }
            ],
            "total_estimated_effort": "12-25 天",
            "fusion_mechanisms": fusion_mechanisms,
            "risk_mitigation": risk_matrix,
            "success_criteria": [
                f"{core_function['target']} 核心功能实现",
                "外部免费资源利用率 ≥ 60%",
                "成本控制在传统方案的 20% 以内",
                "系统复杂度不高于当前水平",
                "方案可 1 人独立复现"
            ]
        }

    @staticmethod
    def _phase1_steps(core_function: Dict, domain: str) -> List[Dict]:
        return [
            {
                "step": 1,
                "title": f"{domain}领域问题深度调研",
                "description": f"分析'{core_function['target']}'在{domain}领域的现有方案和最佳实践",
                "techniques": ["文献综述", "竞品分析", "社区调研"],
                "output": "领域现状分析报告",
                "estimation": "1 天"
            },
            {
                "step": 2,
                "title": "外部资源搜索与筛选",
                "description": "在 GitHub、arXiv、Kaggle 等平台搜索可借力的免费资源",
                "techniques": ["关键词搜索", "Star/引用筛选", "License 合规检查"],
                "output": "经过筛选的高质量资源清单 (Top 10)",
                "estimation": "1 天"
            },
            {
                "step": 3,
                "title": "资源质量评估",
                "description": "对筛选出的资源进行代码质量/数据质量/模型精度评估",
                "techniques": ["代码审查", "基准测试(Benchmark)", "社区活跃度分析"],
                "output": "资源质量评分矩阵",
                "estimation": "0.5 天"
            }
        ]

    @staticmethod
    def _phase2_steps(top_resources: List[Dict], domain: str) -> List[Dict]:
        steps = []
        for i, res in enumerate(top_resources):
            steps.append({
                "step": 10 + i,
                "title": f"集成 '{res['name']}' ({res['category']})",
                "description": res["extraction_method"],
                "techniques": ["API 对接", "数据格式转换", "接口适配层开发"],
                "output": f"'{res['name']}' 适配模块",
                "estimation": "1-2 天"
            })

        steps.append({
            "step": 20,
            "title": "多源资源融合管道构建",
            "description": f"构建 ETL 管道将 {len(top_resources)} 个外部资源统一为内部可用格式",
            "techniques": ["数据清洗", "特征工程", "Schema 映射"],
            "output": "统一资源服务接口",
            "estimation": "1-2 天"
        })

        return steps

    @staticmethod
    def _phase3_steps(contradictions: Dict) -> List[Dict]:
        steps = []
        for i, c in enumerate(contradictions.get("contradictions", [])):
            principles = c.get("suggested_principles", [("未知", "未知")])
            steps.append({
                "step": 30 + i,
                "title": f"消解矛盾 C{i+1}: {c['improving_feature']} ↔ {c['worsening_feature']}",
                "description": f"应用 {principles[0][0] if principles else 'TRIZ 原理'}解决 {c['description']}",
                "techniques": [c.get("separation_strategy", {}).get("strategy", "TRIZ 分离"), "原型验证"],
                "output": f"矛盾解决方案文档 + 验证原型",
                "estimation": "2-3 天"
            })
        return steps

    @staticmethod
    def _phase4_steps(core_function: Dict, domain: str) -> List[Dict]:
        return [
            {
                "step": 40,
                "title": "最小可行原型(MVP)构建",
                "description": f"集成所有模块，构建能验证'{core_function['target']}'核心功能的 MVP",
                "techniques": ["快速原型", "集成测试", "端到端验证"],
                "output": "可运行的 MVP 系统",
                "estimation": "2-3 天"
            },
            {
                "step": 41,
                "title": "性能基准测试与优化",
                "description": "对 MVP 进行基准测试，对比传统方案指标",
                "techniques": ["A/B 测试", "Profiling", "瓶颈分析"],
                "output": "性能对报告 + 优化建议",
                "estimation": "1 天"
            },
            {
                "step": 42,
                "title": "文档化与方案移交",
                "description": "编写方案文档，包括架构图、部署说明、维护指南",
                "techniques": ["架构文档", "API 文档", "运维手册"],
                "output": "完整方案交付包",
                "estimation": "1 天"
            }
        ]

    @staticmethod
    def _fusion_mechanisms(core_function: Dict, resources: List[Dict]) -> List[Dict]:
        best_resources = resources[:5]
        return [
            {
                "mechanism": "资源适配层 (RAL)",
                "type": "技术架构",
                "description": "为每个外部资源建立标准适配器，统一对外接口",
                "implementation": "Adapter Pattern + 策略模式 + 可插拔架构",
                "complexity": "低",
                "reusability": "高"
            },
            {
                "mechanism": "矛盾消解引擎 (CDE)",
                "type": "算法",
                "description": "内置 TRIZ 分离原理，在运行时动态选择矛盾消解策略",
                "implementation": "决策树 + 规则引擎 + 条件判断",
                "complexity": "中",
                "reusability": "高"
            },
            {
                "mechanism": f"多源融合管道 (MFP)",
                "type": "数据处理",
                "description": f"将 {len(best_resources)} 个外部资源的数据/能力融合到统一数据平面",
                "implementation": "ETL + 特征向量化 + 质量加权融合",
                "complexity": "中",
                "reusability": "中"
            },
            {
                "mechanism": "渐进式部署策略 (PDS)",
                "type": "运维",
                "description": "按 20%→50%→100% 流量逐步推广，每个阶段验证后推进",
                "implementation": "Feature Flag + 灰度发布 + 自动回滚",
                "complexity": "低",
                "reusability": "高"
            }
        ]

    @staticmethod
    def _risk_matrix(domain: str) -> List[Dict]:
        return [
            {
                "risk": "外部资源不可用",
                "probability": "中",
                "impact": "高",
                "mitigation": "每个功能点至少准备 2 个备选资源",
                "contingency": "切换到备用资源，同时启动内部实现"
            },
            {
                "risk": "资源质量不达标",
                "probability": "中",
                "impact": "中",
                "mitigation": "资源使用前进行质量评估和基准测试",
                "contingency": "降级到基础版本或使用简化算法"
            },
            {
                "risk": "集成复杂度超预期",
                "probability": "低-中",
                "impact": "中",
                "mitigation": "分阶段集成，每个阶段设置退出点",
                "contingency": "简化为单一资源依赖方案"
            },
            {
                "risk": "外部资源版本更新",
                "probability": "高",
                "impact": "低-中",
                "mitigation": "锁定兼容版本，建立版本管理策略",
                "contingency": "适配器层处理 API 变更"
            },
            {
                "risk": "领域特殊性导致方案不适配",
                "probability": "低",
                "impact": "高",
                "mitigation": "早期进行概念验证(PoC)验证可行性",
                "contingency": "重新进行{domain}领域专项调研"
            }
        ]


# ============================================================
# API 端点实现
# ============================================================

@router.post("/solve")
async def solve_triz_ifr(
    request: SolveRequest,
    settings: Settings = Depends(get_settings)
) -> SolveResponse:
    """
    TRIZ IFR 逆向收敛求解主入口 v2.0

    深度执行通用求解四步法：
    1. 多维度问题功能化解构
    2. IFR 公式评估与顶点锚定
    3. 6 维度逆向资源扫描 + 矛盾矩阵分析
    4. 分阶段可执行方案 + 风险矩阵
    """
    try:
        problem = request.problem
        constraints = request.constraints or []
        industry = request.industry

        # === Node 1: 深度问题功能化解构 ===
        analyzer = ProblemAnalyzer()
        domain_info = analyzer.detect_domain(problem, industry)
        core_function = analyzer.extract_core_function(problem)
        dimensions = analyzer.analyze_dimensions(problem, constraints)
        traps = analyzer.identify_traps(problem, domain_info[0])
        contradiction_params = analyzer.extract_contradiction_parameters(problem, dimensions)
        function_tree = analyzer.build_function_tree(problem, core_function, dimensions, traps)

        node1 = Node1Deconstruction(
            ultimate_function=core_function["original"],
            harmful_factors=[v["description"] for k, v in dimensions.items() if v.get("bottleneck")],
            low_ideality_traps=[t["trap"] for t in traps],
            function_tree=function_tree
        )

        # === Node 2: 极致 IFR 顶点锚定 ===
        ifr_analyzer = IFRAnalyzer()
        formulas = ifr_analyzer.evaluate_formulas(problem, core_function, dimensions)
        best_formula = formulas[0] if formulas else formulas[0]
        ideal_state = ifr_analyzer.build_ideal_state(problem, core_function, best_formula, dimensions)
        feasibility = ifr_analyzer.assess_feasibility(best_formula, dimensions)

        node2 = Node2IFRAnchor(
            ifr_formula_type=best_formula["type"],
            ifr_description=best_formula["description"],
            ideal_state=ideal_state,
            feasibility_gap=feasibility["assessment"]
        )

        # === Node 3: 逆向资源扫描 + 矛盾分析 ===
        scanner = ResourceScanner()
        resources = scanner.scan(problem, core_function, domain_info)

        contradiction_engine = ContradictionEngine()
        contradictions = contradiction_engine.analyze(problem, contradiction_params, dimensions)

        physical_contradictions = []
        for c in contradictions.get("contradictions", []):
            physical_contradictions.append(PhysicalContradiction(
                parameter=f"{c['improving_feature']} ↔ {c['worsening_feature']}",
                requirement_a=f"为了提升{c['improving_feature']}，系统需要增强相关能力",
                requirement_not_a=f"为了不恶化{c['worsening_feature']}，系统需要控制相关开销",
                separation_strategy=c.get("separation_strategy", {}).get("strategy", "系统级别分离")
            ))

        external_resources = []
        for r in resources:
            external_resources.append(ResourceItem(
                name=f"[{r['category']}] {r['name']}",
                source=r["type"],
                url=r["url"],
                cost_type=r["cost_type"],
                description=r["description"],
                relevance_score=r["relevance_score"]
            ))

        # 识别资源缺口
        resource_gaps = []
        covered_aspects = set()
        for r in resources:
            for kw in ["代码", "数据", "模型", "算法", "框架", "工具"]:
                if kw in r["category"]:
                    covered_aspects.add(kw)
        all_aspects = {"代码", "数据", "模型", "算法", "框架", "工具"}
        for aspect in all_aspects - covered_aspects:
            resource_gaps.append(f"缺少 '{aspect}' 类别的直接资源，可能需要组合使用已有资源覆盖")

        node3 = Node3ResourceScan(
            physical_contradictions=physical_contradictions,
            external_resources=external_resources,
            resource_gaps=resource_gaps if resource_gaps else ["资源覆盖基本完整"],
            contradiction_resolution=contradictions["resolution_summary"]
        )

        # === Node 4: 可执行落地方案 ===
        planner = ExecutionPlanner()
        plan = planner.build_action_plan(problem, core_function, contradictions, resources, domain_info)

        action_steps = []
        for phase in plan["phases"]:
            for step in phase.get("steps", []):
                action_steps.append(ActionStep(
                    step_number=step["step"],
                    title=step["title"],
                    description=step["description"],
                    expected_output=step.get("output", "实现方案"),
                    estimated_effort=step.get("estimation", "1-3 天")
                ))

        node4 = Node4ActionablePlan(
            acquisition_sources=[
                {"source": r["source"], "url": r["url"]}
                for r in resources[:5] if r.get("url")
            ],
            extraction_algorithms=[
                {"name": m["mechanism"], "description": m["description"], "implementation": m.get("implementation", "")}
                for m in plan["fusion_mechanisms"]
            ],
            fusion_mechanisms=[
                {"name": m["mechanism"], "type": m["type"], "implementation": m.get("implementation", "")}
                for m in plan["fusion_mechanisms"]
            ],
            action_steps=action_steps,
            success_metrics=plan["success_criteria"],
            risk_mitigation=[f"{r['risk']} → {r['mitigation']}" for r in plan["risk_mitigation"]]
        )

        return SolveResponse(
            code=0,
            data={
                "node1_deconstruction": node1.model_dump(),
                "node2_ifr_anchor": node2.model_dump(),
                "node3_resource_scan": node3.model_dump(),
                "node4_actionable_plan": node4.model_dump()
            },
            message="TRIZ IFR v2.0 深度逆向收敛求解完成"
        )

    except Exception as e:
        return SolveResponse(
            code=500,
            data={},
            message=f"求解异常: {str(e)}"
        )
