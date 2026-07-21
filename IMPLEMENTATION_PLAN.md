# GitHub Engineer — 实施计划(v2.0)

> **重大方向调整**:基于对当前生态的深入分析,我们不再做"会写代码的 GitHub Agent",
> 改做**维护者决策智能(Maintainer Intelligence)** —— 帮维护者决定什么值得做、为什么值得做,
> 然后委托给现成的 Coding Agent 执行。

- **文档版本**:v2.0(基于对 GitHub Copilot Coding Agent / Agentic Workflows 的竞品分析重写)
- **最后更新**:2026-07
- **目标受众**:程序员 + AI 编码助手
- **目的**:提供可直接执行的、模块化的开发任务清单

---

## 目录

1. [为什么要调整方向](#1-为什么要调整方向)
2. [新的产品定位](#2-新的产品定位)
3. [技术栈选择](#3-技术栈选择)
4. [新的路线图](#4-新的路线图)
5. [v0.1 详细实施计划](#5-v01-详细实施计划)
6. [给 AI 的执行说明书](#6-给-ai-的执行说明书)

---

## 1. 为什么要调整方向

### 原计划(DESIGN.md)的主要问题

经过深入的竞品分析发现:

1. **"异步改代码 + 开 PR"已不是差异点**
   - GitHub Copilot Coding Agent 已经能后台接任务、修改代码、执行测试并提交 PR
   - GitHub Agentic Workflows 直接提供 Issue Triage,支持多模型
   - 我们计划的 v0.1(Triage)、v0.3(Draft PR)都已被平台原生功能覆盖

2. **把唯一可能有记忆点的功能放到了 v0.4**
   - "主动规划"是真正的差异点,却要等 Triage、分发、Draft PR 全做完才开发
   - 这意味着项目发布后的前几个月看起来只是"另一个 AI Triage Action"

3. **首要用户与痛点不匹配**
   - 独立开发者/小团队通常没有足够多的 Issue,未必需要自动分诊
   - 真正被 Issue 淹没的大型开源项目对安全、审计、社区关系要求极高

4. **安全设计目前达不到宣传口径**
   - "Triage 风险为零"不成立:错误标签、公开评论、刷屏都会伤害维护者信誉
   - XML 包裹和正则匹配不是可靠的 Prompt Injection 防御
   - "数据不出 CI"不准确:使用云模型时代码和上下文会发送到模型服务商

### 当前 GitHub Agent 生态的真正空白

- **不是"会不会写代码"**(Copilot / Claude / Codex 已经很强)
- **而是"什么值得做、为什么值得做"**(决策层,几乎空白)

---

## 2. 新的产品定位

### 一句话定位

**面向开源维护者的 Maintainer Intelligence:每周只告诉你最值得处理的三件事,并用证据解释原因;你批准后再交给任意 Coding Agent。**

### 核心价值主张

不跟 Copilot、Claude、Codex 比谁更会写代码,而是决定:

- **什么值得做**:基于用户影响、重复度、技术债、项目目标
- **为什么现在做**:用证据说明优先级(多少人遇到、影响范围、修复成本)
- **哪些 Issue 实际是同一问题**:去重和聚类
- **哪些任务已经准备好交给 Agent**:可复现步骤、验收标准、相关文件
- **哪些任务缺少信息,不应浪费 Agent 成本**

### 差异化

| 维度 | GitHub Copilot / Agentic Workflows | GHE(新定位) |
|---|---|---|
| **做什么** | 执行层:写代码、跑测试、开 PR | 决策层:什么值得做、为什么值得做 |
| **输入** | Issue 的具体描述 | 整个项目的全景(所有 issue + 历史 + 目标) |
| **输出** | 代码改动 + PR | 决策建议 + 优先级排序 + 证据 |
| **频率** | 按需触发(给一个 issue) | 定期综合(每周看全局) |
| **定位** | 替代编码 | 替代维护者的"每周通读所有 issue"这个苦力活 |

### 目标用户(重新聚焦)

**首要用户**:中大型开源项目的维护者(50+ open issues,真正被淹没的人)

**次要用户**:独立开发者(但不强求,没 issue 就没价值)

---

## 3. 技术栈选择

### 推荐:Python

**理由**:
1. GitHub API 生态成熟(PyGithub)
2. LLM 调用库丰富(OpenAI SDK、LiteLLM、Anthropic SDK)
3. 数据处理方便(pandas、sklearn 做聚类去重)
4. GitHub Actions 对 Python 支持好
5. 你后面让 AI 执行,Python 的 AI 编码助手生态最成熟

**备选**:TypeScript/Node(如果你更熟悉,也可以,但数据处理会麻烦一些)

### 核心依赖

```python
# requirements.txt
PyGithub>=2.1.0          # GitHub API
openai>=1.0.0            # OpenAI 兼容接口(通吃多模型)
pydantic>=2.0.0          # 结构化输出
pyyaml>=6.0              # 配置解析
python-dotenv>=1.0.0     # 环境变量
```

**v0.1 取舍**:
- `scikit-learn` / `numpy`:可选依赖,第一版可先用轻量规则 + LLM 判断重复线索
- `anthropic`:先走 OpenAI-compatible 接口,后续再加原生适配
- `markdown`:Markdown 报告用字符串模板即可,不需要额外渲染库

---

## 4. 新的路线图

**核心原则:第一个版本就做差异点,而不是等到 v0.4**

### v0.1 — Maintainer Brief 可用版(1 周)

**做什么**:
- 同时支持本地 CLI 和 GitHub Action
- 默认只读运行,不公开评论、不打标签
- 输入一个 GitHub 仓库,输出一份 Markdown《维护者周报》(Maintainer Brief)
- 报告包含:
  - 本周新增问题和重复簇
  - 用户影响证据(多少人遇到、讨论热度)
  - **最值得处理的 Top 3**(带优先级理由)
  - 可快速修复项
  - 缺失信息和风险
  - 相比上周发生了什么变化
- 输出模式:
  - `markdown`:保存到本地 `reports/`
  - `action-summary`:写入 GitHub Actions Step Summary 并上传 artifact
- GitHub Action 可通过 `workflow_dispatch` 手动运行,也可每周定时运行

**核心指标**:
- ✅ 安装后 10 分钟内能跑出第一份报告
- ✅ Action 默认配置不产生公开写操作
- ✅ 报告可读,Top 3 有证据,不是泛泛总结
- ✅ 单次运行成本和耗时可控

**验收标准**:
- 本地 CLI 能对任意公开仓库生成 `reports/{owner}_{repo}_{date}.md`
- GitHub Action 能在目标仓库生成 Step Summary 和 artifact
- 没有未捕获异常,常见配置错误有清晰提示
- README 提供完整安装、配置、运行和 Action 使用说明

### v0.2 — 决策记忆(1 周)

**做什么**:
- 记录维护者对建议的反馈:接受/拒绝/延后
- 记录拒绝原因(如"这个方向我们不做""资源不够")
- 记录项目当前目标和禁区
- 记忆存为 `.ghe/memory/decisions.yml`,通过 PR 更新(不是 Agent 静默修改)

**意义**:下次生成报告时,不再推荐已被明确拒绝的方向

### v0.3 — Agent-Ready Task Preparation(1-2 周)

**做什么**:
- 把维护者批准的任务,整理成"Agent 可直接执行"的 Issue:
  - 可复现步骤
  - 验收标准
  - 相关文件(已定位好)
  - 风险范围
  - 必须运行的测试
  - 允许和禁止修改的目录
- 这是目前 Coding Agent 生态真正缺的**上游质量层**

### v0.4 — 委托给现成 Coding Agent(1 周)

**做什么**:
- 通过适配器把批准的任务交给 Copilot、Claude Code、Codex 或其他 Agent
- **不自己维护 CLI、容器、认证和模型兼容层**
- 安全执行建立在 GitHub Agentic Workflows 的 Safe Outputs 上

### v1.0 — 打磨与社区

- 多仓库支持
- 成本优化
- 社区反馈迭代

---

## 5. v0.1 详细实施计划

### 5.1 项目初始化

**任务 ID**: `INIT-001`  
**时间估算**: 30 分钟

创建基础仓库结构:

```
github-engineer/
├── README.md
├── LICENSE (MIT)
├── requirements.txt
├── .gitignore
├── .ghe/
│   └── config.example.yml
├── src/
│   ├── __init__.py
│   ├── main.py                    # 入口
│   ├── github_client.py           # GitHub API 封装
│   ├── llm_client.py              # LLM 调用封装
│   ├── analyzer.py                # 核心分析逻辑
│   ├── report_generator.py        # 报告生成
│   └── models.py                  # Pydantic 数据模型
├── prompts/
│   └── maintainer_brief.md        # 主 prompt 模板
├── tests/
│   └── __init__.py
└── examples/
    └── sample_report.md           # 示例输出
```

**执行指令**(给 AI):
```
在 /Users/fangchen/Baidu/GitHub/GitHubEngineer 创建上述目录结构。
README.md 写一个简短的项目说明(一句话 + "WIP")。
LICENSE 用 MIT。
requirements.txt 包含 PyGithub, openai, pydantic, pyyaml, python-dotenv。
.gitignore 忽略 __pycache__, .env, *.pyc, .DS_Store。
```

---

### 5.2 配置设计

**任务 ID**: `CONFIG-001`  
**时间估算**: 20 分钟

创建 `.ghe/config.example.yml`:

```yaml
repo:
  owner: "your-org"
  name: "your-repo"
  # 或者直接 full_name: "your-org/your-repo"

github:
  token: ${GITHUB_TOKEN}  # 从环境变量读

model:
  provider: "openai-compatible"
  base_url: ${LLM_BASE_URL}     # 如 https://api.anthropic.com, https://api.openai.com
  api_key: ${LLM_API_KEY}
  model_name: "claude-sonnet-4"  # 或 gpt-4o, deepseek-chat

output:
  format: "markdown"  # markdown | action-summary
  output_dir: "reports"
  title: "Maintainer Brief - {date}"

analysis:
  lookback_days: 7              # 分析最近 7 天
  top_n: 3                      # Top N 优先级
  min_issue_age_hours: 24       # 至少开了 24 小时才纳入分析(过滤噪声)
  max_issues_for_llm: 50         # 先用规则筛选,再交给 LLM
```

**执行指令**:
```
创建 .ghe/config.example.yml,内容如上。
在 README.md 添加配置说明章节。
```

---

### 5.3 GitHub API 封装

**任务 ID**: `GITHUB-001`  
**时间估算**: 1 小时

`src/github_client.py`:

```python
from github import Github
from typing import List, Optional
from datetime import datetime, timedelta

class GitHubClient:
    def __init__(self, token: str, repo_full_name: str):
        self.gh = Github(token)
        self.repo = self.gh.get_repo(repo_full_name)
    
    def get_open_issues(self, since: Optional[datetime] = None) -> List:
        """获取 open issues(不含 PR)"""
        issues = self.repo.get_issues(state='open', sort='created', direction='desc')
        result = []
        for issue in issues:
            if issue.pull_request:  # 跳过 PR
                continue
            if since and issue.created_at < since:
                continue
            result.append(issue)
        return result
    
    def get_issue_metrics(self, issue) -> dict:
        """提取 issue 的关键指标"""
        return {
            'number': issue.number,
            'title': issue.title,
            'body': issue.body or "",
            'created_at': issue.created_at,
            'updated_at': issue.updated_at,
            'comments_count': issue.comments,
            'reactions': issue.get_reactions().totalCount,
            'labels': [label.name for label in issue.labels],
            'assignees': [a.login for a in issue.assignees],
            'state': issue.state,
            'url': issue.html_url
        }
```

**执行指令**:
```
创建 src/github_client.py,实现 GitHubClient 类。
包含 get_open_issues 和 get_issue_metrics 方法。
处理 PyGithub 的 RateLimitExceededException。
添加简单的单元测试(mock PyGithub)。
```

---

### 5.4 LLM 调用封装

**任务 ID**: `LLM-001`  
**时间估算**: 1 小时

`src/llm_client.py`:

```python
from openai import OpenAI
from typing import Optional, Dict, Any
import json

class LLMClient:
    def __init__(self, base_url: str, api_key: str, model_name: str):
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model_name = model_name
    
    def generate(self, prompt: str, system: Optional[str] = None, 
                 response_format: Optional[Dict] = None) -> str:
        """调用 LLM 生成内容"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        kwargs = {"model": self.model_name, "messages": messages}
        if response_format:
            kwargs["response_format"] = response_format
        
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    
    def generate_json(self, prompt: str, system: Optional[str] = None) -> Dict[Any, Any]:
        """生成 JSON 格式响应"""
        content = self.generate(
            prompt, 
            system, 
            response_format={"type": "json_object"}
        )
        return json.loads(content)
```

**执行指令**:
```
创建 src/llm_client.py,实现 LLMClient 类。
支持 OpenAI 兼容接口(通过 base_url 切换)。
添加错误处理(API 超时、token 超限)。
添加简单测试(mock OpenAI)。
```

---

### 5.5 数据模型定义

**任务 ID**: `MODEL-001`  
**时间估算**: 30 分钟

`src/models.py`:

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class IssueMetrics(BaseModel):
    number: int
    title: str
    body: str
    created_at: datetime
    comments_count: int
    reactions: int
    labels: List[str]
    url: str

class IssuePriority(BaseModel):
    issue_number: int
    title: str
    priority_score: float = Field(..., ge=0, le=10)
    reason: str  # 为什么优先级高
    user_impact: str  # 用户影响证据
    estimated_effort: str  # 估算工作量:"low" | "medium" | "high"

class IssueCluster(BaseModel):
    cluster_name: str  # 聚类名称,如"登录失败问题"
    issue_numbers: List[int]
    common_theme: str  # 共同主题

class MaintainerBrief(BaseModel):
    generated_at: datetime
    period: str  # "2026-07-01 to 2026-07-07"
    
    summary: str  # 本周概览
    new_issues_count: int
    
    top_priorities: List[IssuePriority]  # Top 3
    quick_wins: List[IssuePriority]  # 可快速修复的
    issue_clusters: List[IssueCluster]  # 重复问题簇
    
    missing_info_issues: List[int]  # 缺失信息的 issue
    trend: str  # 相比上周的变化
```

**执行指令**:
```
创建 src/models.py,定义 Pydantic 数据模型。
确保所有字段有类型注解和文档字符串。
添加验证规则(如 priority_score 范围 0-10)。
```

---

### 5.6 核心分析逻辑

**任务 ID**: `ANALYZER-001`  
**时间估算**: 1-2 小时(核心模块)

`src/analyzer.py`:

```python
from typing import List
from .models import IssueMetrics, IssuePriority, IssueCluster, MaintainerBrief
from .llm_client import LLMClient
from datetime import datetime

class IssueAnalyzer:
    def __init__(self, llm_client: LLMClient, max_issues_for_llm: int = 50):
        self.llm = llm_client
        self.max_issues_for_llm = max_issues_for_llm
    
    def analyze(self, issues: List[IssueMetrics], lookback_days: int) -> MaintainerBrief:
        """生成维护者周报"""
        
        # 1. 先用确定性规则筛选候选 issue,避免把所有内容塞给 LLM
        candidate_issues = self._select_candidates(issues)
        
        # 2. 轻量识别可能重复的问题簇,只作为提示,不追求算法完美
        clusters = self._find_obvious_clusters(candidate_issues)
        
        # 3. 调用 LLM 生成优先级建议
        priorities = self._calculate_priorities(candidate_issues, clusters)
        
        # 4. 识别快速修复项
        quick_wins = self._identify_quick_wins(priorities)
        
        # 5. 识别缺失信息
        missing_info = self._identify_missing_info(candidate_issues)
        
        # 6. 综合报告
        brief = self._generate_brief(
            candidate_issues, priorities, quick_wins, clusters, missing_info, lookback_days
        )
        
        return brief
    
    def _select_candidates(self, issues: List[IssueMetrics]) -> List[IssueMetrics]:
        """用公开信号筛选最值得交给 LLM 的 issue"""
        scored = sorted(
            issues,
            key=lambda issue: (
                issue.comments_count * 3
                + issue.reactions * 2
                + len(issue.labels)
            ),
            reverse=True,
        )
        return scored[: self.max_issues_for_llm]
    
    def _find_obvious_clusters(self, issues: List[IssueMetrics]) -> List[IssueCluster]:
        """v0.1 只做轻量重复识别;复杂聚类留到后续迭代"""
        # 先返回空列表也可以接受;让 LLM 基于标题和正文识别重复线索
        return []
    
    def _calculate_priorities(self, issues: List[IssueMetrics], 
                             clusters: List[IssueCluster]) -> List[IssuePriority]:
        """调用 LLM 计算优先级"""
        # 构建 prompt(见下一节)
        prompt = self._build_priority_prompt(issues, clusters)
        
        # 调用 LLM,要求返回结构化 JSON
        response = self.llm.generate_json(prompt)
        
        # 解析并验证
        priorities = [IssuePriority(**p) for p in response.get("priorities", [])]
        return sorted(priorities, key=lambda x: x.priority_score, reverse=True)
    
    def _identify_quick_wins(self, priorities: List[IssuePriority]) -> List[IssuePriority]:
        """筛选快速修复项(高优先级 + 低工作量)"""
        return [
            p for p in priorities 
            if p.priority_score >= 6 and p.estimated_effort == "low"
        ][:5]  # 最多 5 个
```

**执行指令**:
```
创建 src/analyzer.py,实现 IssueAnalyzer 类。
实现 _select_candidates 方法(按评论、reaction、标签等信号筛选)。
实现 _find_obvious_clusters 方法(v0.1 可先返回空列表,不要引入 DBSCAN)。
实现 _calculate_priorities 方法(调用 LLM)。
实现 _identify_quick_wins 方法(筛选逻辑)。
避免把所有 issue 一次性交给 LLM,默认最多 50 个。
```

---

### 5.7 Prompt 模板设计

**任务 ID**: `PROMPT-001`  
**时间估算**: 1-2 小时

`prompts/maintainer_brief.md`:

```markdown
# Maintainer Intelligence — 优先级分析

你是一个开源项目维护助手。你的任务是分析仓库的 open issues,找出最值得维护者优先处理的问题。

## 输入数据

<repository-context>
仓库名称: {repo_name}
分析周期: {period}
README 摘要: {readme_summary}
</repository-context>

<open-issues>
{issues_json}
</open-issues>

<issue-clusters>
以下是通过文本相似度识别出的重复问题簇:
{clusters_json}
</issue-clusters>

## 分析要求

### 1. 优先级评分标准

给每个 issue 评分(0-10),综合考虑:

- **用户影响** (40%):
  - 有多少人遇到?(评论数、reactions、是否在簇中)
  - 影响核心功能还是边缘功能?
  - 阻塞性如何?(完全无法使用 vs 不便)

- **技术紧迫性** (30%):
  - 是否安全漏洞?
  - 是否数据丢失风险?
  - 是否依赖即将废弃?

- **修复成本** (20%):
  - 根据描述判断复杂度
  - 是否有明确复现步骤?(有 = 成本低)
  - 是否涉及架构改动?(涉及 = 成本高)

- **对齐项目方向** (10%):
  - 是否符合 README 中的项目定位?
  - 是否偏离核心价值?

### 2. 证据要求

每个优先级判断必须给出具体证据:
- "3 个用户报告同样问题(#42, #51, #67)"
- "影响核心登录流程"
- "有明确复现步骤,预计 1-2 天可修复"

### 3. 快速修复识别

筛选出:
- 优先级 ≥ 6
- 工作量 = low (有复现步骤、范围明确、不涉及架构)
- 能快速提升用户体验

### 4. 缺失信息识别

标记出信息不足、无法评估的 issue:
- 没有复现步骤
- 描述过于模糊
- 缺少环境信息

## 输出格式

返回 JSON:

```json
{
  "priorities": [
    {
      "issue_number": 42,
      "title": "...",
      "priority_score": 9.2,
      "reason": "3 个用户报告登录失败(#42, #51, #67),影响核心功能",
      "user_impact": "高:阻塞登录,至少 3 人遇到",
      "estimated_effort": "low"
    }
  ],
  "quick_wins": [
    {
      "issue_number": 38,
      "title": "...",
      "priority_score": 7.5,
      "reason": "5 个用户请求导出功能,需求明确",
      "user_impact": "中:功能缺失但有替代方案",
      "estimated_effort": "low"
    }
  ],
  "missing_info_issues": [12, 34, 56],
  "summary": "本周新增 15 个 issue,主要集中在登录和导出功能。发现 3 个重复问题簇。"
}
```

## 重要原则

- **只推荐真正值得做的**:宁可只给 2 个高质量建议,也不要凑数。
- **用证据说话**:每个判断都要有数据支撑。
- **考虑维护者精力**:不是所有 bug 都值得立刻修,要考虑投入产出比。
- **尊重项目方向**:不推荐偏离项目核心定位的功能请求。
```

**执行指令**:
```
创建 prompts/maintainer_brief.md,内容如上。
确保 prompt 结构清晰,有明确的评分标准和输出格式。
在代码中实现 prompt 模板的变量替换。
```

---

### 5.8 报告生成器

**任务 ID**: `REPORT-001`  
**时间估算**: 1 小时

`src/report_generator.py`:

```python
from .models import MaintainerBrief
from datetime import datetime

class ReportGenerator:
    def generate_markdown(self, brief: MaintainerBrief, repo_name: str) -> str:
        """生成 Markdown 格式的维护者周报"""
        
        md = f"""# 📋 Maintainer Brief — {brief.period}

> **仓库**: {repo_name}  
> **生成时间**: {brief.generated_at.strftime('%Y-%m-%d %H:%M UTC')}

---

## 📊 本周概览

{brief.summary}

- **新增 Issue**: {brief.new_issues_count} 个
- **发现重复问题簇**: {len(brief.issue_clusters)} 个
- **识别快速修复项**: {len(brief.quick_wins)} 个

---

## 🎯 Top 3 优先级建议

"""
        
        for i, priority in enumerate(brief.top_priorities[:3], 1):
            md += f"""### {i}. #{priority.issue_number}: {priority.title}

**优先级评分**: {priority.priority_score:.1f}/10  
**理由**: {priority.reason}  
**用户影响**: {priority.user_impact}  
**估算工作量**: {priority.estimated_effort}

"""
        
        if brief.quick_wins:
            md += "\n---\n\n## ⚡ 快速修复建议\n\n"
            for qw in brief.quick_wins[:5]:
                md += f"- **#{qw.issue_number}**: {qw.title} (评分 {qw.priority_score:.1f})\n"
                md += f"  - {qw.reason}\n\n"
        
        if brief.issue_clusters:
            md += "\n---\n\n## 🔄 重复问题簇\n\n"
            for cluster in brief.issue_clusters:
                issues_str = ", ".join([f"#{n}" for n in cluster.issue_numbers])
                md += f"### {cluster.cluster_name}\n\n"
                md += f"相关 Issue: {issues_str}  \n"
                md += f"共同主题: {cluster.common_theme}\n\n"
        
        if brief.missing_info_issues:
            md += "\n---\n\n## ⚠️ 缺失信息\n\n"
            md += "以下 Issue 信息不足,建议补充后再评估:\n\n"
            for issue_num in brief.missing_info_issues[:5]:
                md += f"- #{issue_num}\n"
        
        md += f"\n---\n\n## 📈 趋势\n\n{brief.trend}\n"
        
        md += "\n---\n\n*本报告由 GitHub Engineer 自动生成。建议仅供参考,最终决策由维护者判断。*\n"
        
        return md
```

**执行指令**:
```
创建 src/report_generator.py,实现 ReportGenerator 类。
生成清晰易读的 Markdown 报告。
添加 emoji 让报告更友好。
确保所有链接可点击(GitHub Issue 编号)。
```

---

### 5.9 主入口

**任务 ID**: `MAIN-001`  
**时间估算**: 1 小时

`src/main.py`:

```python
import os
import yaml
from datetime import datetime, timedelta
from dotenv import load_dotenv

from .github_client import GitHubClient
from .llm_client import LLMClient
from .analyzer import IssueAnalyzer
from .report_generator import ReportGenerator
from .models import IssueMetrics

def load_config(config_path: str = ".ghe/config.yml"):
    """加载配置"""
    load_dotenv()  # 加载 .env 文件
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # 替换环境变量
    def replace_env(obj):
        if isinstance(obj, dict):
            return {k: replace_env(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_env(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
            env_var = obj[2:-1]
            return os.getenv(env_var, obj)
        return obj
    
    return replace_env(config)

def main():
    # 1. 加载配置
    config = load_config()
    
    # 2. 初始化客户端
    repo_full_name = f"{config['repo']['owner']}/{config['repo']['name']}"
    gh_client = GitHubClient(config['github']['token'], repo_full_name)
    llm_client = LLMClient(
        config['model']['base_url'],
        config['model']['api_key'],
        config['model']['model_name']
    )
    
    # 3. 拉取 issues
    lookback_days = config['analysis']['lookback_days']
    since = datetime.now() - timedelta(days=lookback_days)
    issues_raw = gh_client.get_open_issues(since=since)
    
    # 转换为 IssueMetrics
    issues = [IssueMetrics(**gh_client.get_issue_metrics(i)) for i in issues_raw]
    
    print(f"📊 找到 {len(issues)} 个 open issues(最近 {lookback_days} 天)")
    
    # 4. 分析
    analyzer = IssueAnalyzer(llm_client)
    brief = analyzer.analyze(issues, lookback_days)
    
    # 5. 生成报告
    generator = ReportGenerator()
    report_md = generator.generate_markdown(brief, repo_full_name)
    
    # 6. 输出:始终写本地 Markdown;Action 环境下额外写 Step Summary
    output_dir = config['output'].get('output_dir', 'reports')
    os.makedirs(output_dir, exist_ok=True)
    safe_repo_name = repo_full_name.replace("/", "_")
    output_file = os.path.join(
        output_dir,
        f"{safe_repo_name}_{datetime.now().strftime('%Y%m%d')}.md",
    )
    with open(output_file, 'w') as f:
        f.write(report_md)
    print(f"✅ 报告已生成: {output_file}")
    
    step_summary = os.getenv("GITHUB_STEP_SUMMARY")
    if step_summary and config['output'].get('format') in ("markdown", "action-summary"):
        with open(step_summary, 'a') as f:
            f.write(report_md)
            f.write("\n")
    
    print(report_md)

if __name__ == "__main__":
    main()
```

**执行指令**:
```
创建 src/main.py,实现主流程。
处理配置加载和环境变量替换。
添加清晰的日志输出(用 print 或 logging)。
添加错误处理(GitHub API 失败、LLM 超时等)。
```

---

### 5.10 本地测试

**任务 ID**: `TEST-001`  
**时间估算**: 1 小时

**测试步骤**:

1. 创建 `.env` 文件:
```bash
GITHUB_TOKEN=ghp_your_token_here
LLM_BASE_URL=https://api.anthropic.com/v1
LLM_API_KEY=sk-ant-your_key_here
```

2. 复制配置模板:
```bash
cp .ghe/config.example.yml .ghe/config.yml
```

3. 修改 `.ghe/config.yml`:
```yaml
repo:
  owner: "your-test-org"
  name: "your-test-repo"  # 选一个有 50+ open issues 的测试仓库
```

4. 安装依赖:
```bash
pip install -r requirements.txt
```

5. 运行:
```bash
python -m src.main
```

6. 检查输出:
- 应该生成 `maintainer_brief_YYYYMMDD.md`
- 报告中应该有 Top 3 建议
- 每个建议都应该有具体证据

**执行指令**:
```
按上述步骤在本地测试一次完整流程。
如果遇到错误,修复并记录到 CHANGELOG.md。
确保在测试仓库上运行不会产生任何公开评论或标签。
```

---

### 5.11 包装为 GitHub Action

**任务 ID**: `ACTION-001`  
**时间估算**: 1-2 小时

创建 `action.yml`:

```yaml
name: 'Maintainer Intelligence'
description: 'Generate a weekly Maintainer Brief for GitHub issues'
author: 'your-name'

inputs:
  github-token:
    description: 'GitHub token with issue read access'
    required: true
  llm-base-url:
    description: 'LLM API base URL (OpenAI compatible)'
    required: true
  llm-api-key:
    description: 'LLM API key'
    required: true
  llm-model:
    description: 'Model name'
    required: false
    default: 'claude-sonnet-4'
  config-path:
    description: 'Path to config file'
    required: false
    default: '.ghe/config.yml'

runs:
  using: 'composite'
  steps:
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install dependencies
      shell: bash
      run: |
        pip install -r ${{ github.action_path }}/requirements.txt

    - name: Generate Maintainer Brief
      shell: bash
      env:
        GITHUB_TOKEN: ${{ inputs.github-token }}
        LLM_BASE_URL: ${{ inputs.llm-base-url }}
        LLM_API_KEY: ${{ inputs.llm-api-key }}
        LLM_MODEL: ${{ inputs.llm-model }}
        GHE_CONFIG_PATH: ${{ inputs.config-path }}
      run: |
        python -m src.main

    - name: Upload report
      uses: actions/upload-artifact@v4
      with:
        name: maintainer-brief
        path: reports/*.md
```

创建示例 workflow `.github/workflows/maintainer-brief.example.yml`:

```yaml
name: Weekly Maintainer Brief

on:
  schedule:
    - cron: '0 9 * * 1'
  workflow_dispatch:

jobs:
  generate-brief:
    runs-on: ubuntu-latest
    permissions:
      issues: read
      contents: read

    steps:
      - uses: actions/checkout@v4

      - name: Generate Maintainer Brief
        uses: ./
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          llm-base-url: ${{ secrets.LLM_BASE_URL }}
          llm-api-key: ${{ secrets.LLM_API_KEY }}
          llm-model: ${{ vars.LLM_MODEL || 'claude-sonnet-4' }}
```

**执行指令**:
```
创建 action.yml,定义 GitHub Action。
创建 .github/workflows/maintainer-brief.example.yml 作为使用示例。
实现 action-summary 输出:如果 GITHUB_STEP_SUMMARY 存在,把报告追加进去。
始终上传 reports/*.md 作为 artifact。
在 README.md 添加"本地运行"和"GitHub Action 使用"章节,说明 secrets 配置。
测试本地 CLI;如果无法实际在 GitHub 上跑 Action,至少检查 YAML 语法和路径。
```

**默认不做,但预留配置**:
- 不默认创建 Discussion
- 不默认评论固定 issue
- 不默认发布 Marketplace

---

## 6. 给 AI 的执行说明书

### 6.1 执行顺序

**严格按以下顺序执行任务,不要跳跃**:

1. `INIT-001` — 项目初始化(创建目录结构)
2. `CONFIG-001` — 配置设计
3. `MODEL-001` — 数据模型定义
4. `GITHUB-001` — GitHub API 封装
5. `LLM-001` — LLM 调用封装
6. `PROMPT-001` — Prompt 模板设计(先做,这是产品核心)
7. `ANALYZER-001` — 核心分析逻辑(轻量候选筛选 + LLM 排序)
8. `REPORT-001` — 报告生成器
9. `MAIN-001` — 主入口
10. `TEST-001` — 本地测试
11. `ACTION-001` — 包装为 GitHub Action,输出 summary 和 artifact

### 6.2 每个任务的验收标准

完成一个任务后,必须满足以下标准才能进入下一个:

- ✅ 代码能运行(无语法错误)
- ✅ 有基本的错误处理(try-except 或 if-else)
- ✅ 复杂逻辑才加注释,不要为了注释而注释
- ✅ 函数有类型注解
- ✅ 核心模块有简单测试或可复现的本地运行命令

### 6.3 遇到问题时的处理

**不要卡住,用这个优先级解决**:

1. **缺少依赖**: 添加到 requirements.txt
2. **API 不熟悉**: 查官方文档或用简化实现(先跑通)
3. **算法不确定**: 用最简单的方案(如聚类可以先跳过,手动实现)
4. **不知道怎么测**: 先跑通主流程,测试后补

### 6.4 关键决策点

**在以下情况下停下来,询问人类**:

- Prompt 设计完全无法判断目标用户口吻时(任务 `PROMPT-001`)
- 输出格式用户有特殊要求
- GitHub API 遇到权限问题

**其他情况都自己做决定,优先跑通。**

### 6.5 代码风格要求

- **Python 风格**: PEP 8
- **命名**: 
  - 函数用 `snake_case`
  - 类用 `PascalCase`
  - 常量用 `UPPER_CASE`
- **Docstring**: 每个公开函数都要有(Google 风格)
- **导入顺序**: 标准库 → 第三方库 → 本地模块

### 6.6 性能和成本要求

- **GitHub API**: 使用分页,避免一次拉取全部(默认最多 100 个 issue)
- **LLM 调用**: 
  - 只调用一次 LLM(所有 issue 一起分析,不是一个个分析)
  - Token 预算:输入 < 30K tokens,输出 < 5K tokens
  - 如果 issue 太多,优先分析最近的、评论最多的
- **聚类**: 最多 200 个 issue,超过就采样

### 6.7 README 必须包含的内容

完成所有任务后,更新 README.md,包含:

1. **一句话说明**:这个工具是干什么的
2. **和竞品的区别**:为什么不用 Copilot / Agentic Workflows
3. **快速开始**:
   - 安装依赖
   - 配置 secrets
   - 运行一次
4. **配置说明**:每个配置项的含义
5. **成本估算**:运行一次大概花多少钱
6. **示例输出**:放一个真实的报告截图或 markdown
7. **限制**:
   - 只支持 open issues
   - 需要 50+ issues 才有效果
   - 不会自动操作仓库(只读)

---

## 7. v0.2-v0.4 简要计划(后续迭代)

### v0.2 — 决策记忆

**核心文件**:
- `.ghe/memory/decisions.yml` — 记录维护者反馈
- `src/memory_manager.py` — 读写决策记忆
- 修改 `analyzer.py` — 读取记忆,过滤已拒绝建议

**验收**:同样的建议不会连续两周推荐

### v0.3 — Agent-Ready Task Preparation

**核心文件**:
- `src/task_preparer.py` — 把 issue 整理成 Agent 可直接执行的格式
- `prompts/task_prep.md` — 任务准备的 prompt

**输出示例**:

```markdown
## Agent Task: 修复登录失败问题(#42)

**目标**: 解决用户无法登录的问题

**可复现步骤**:
1. 访问 /login
2. 输入正确的用户名密码
3. 点击登录
4. 期望:跳转到首页
5. 实际:停留在登录页,无错误提示

**验收标准**:
- [ ] 用户能成功登录
- [ ] 错误提示正确显示
- [ ] 测试通过:`npm test -- login.test.ts`

**相关文件**:
- `src/auth/login.ts` (主要逻辑)
- `src/auth/session.ts` (会话管理)
- `tests/auth/login.test.ts` (测试)

**允许修改**: `src/auth/` 目录  
**禁止修改**: `src/core/` 目录

**风险提示**: 涉及身份验证,需要仔细测试
```

### v0.4 — 委托给 Coding Agent

通过适配器调用:
- GitHub Copilot Coding Agent
- Claude Code CLI
- 其他支持 `-p` 非交互模式的 Agent

**不自己实现代码执行层**。

---

## 8. 成功标准(整个 v0.1)

### 技术指标

- ✅ 能在有 50+ open issue 的仓库上运行
- ✅ 单次运行时间 < 5 分钟
- ✅ 单次成本 < $0.50(使用 Claude Sonnet)
- ✅ 无未捕获异常
- ✅ 默认配置不产生任何公开 GitHub 写操作;公开输出必须显式开启

### 可用性指标

- ✅ 本地 CLI 一条命令能生成报告
- ✅ GitHub Action 能通过 `workflow_dispatch` 生成报告
- ✅ Action 输出 Step Summary 和 artifact
- ✅ 缺少 token、配置错误、LLM 调用失败时有清晰错误提示
- ✅ README 能让新用户 10 分钟内跑通

### 报告质量指标

- ✅ Top 3 建议必须带 issue 编号、证据和理由
- ✅ 快速修复项和缺失信息项分开呈现
- ✅ Issue 编号在 Markdown 中可点击
- ✅ 报告 5 分钟内可读完

---

## 9. 常见问题(FAQ)

### Q1: 为什么不直接用 GitHub Copilot?

A: Copilot 是执行层(会写代码),我们是决策层(决定写什么)。两者互补,不冲突。

### Q2: 聚类算法可以换吗?

A: 可以,但 v0.1 不把聚类算法作为核心路径。先用轻量候选筛选 + LLM 判断重复线索,报告质量被验证后再尝试:
- 基于 embedding 的相似度(OpenAI Embeddings)
- TF-IDF / DBSCAN
- LLM 更细粒度判断相似性(成本高但准)
- 基于 issue 引用关系的图聚类

### Q3: 能支持私有仓库吗?

A: 能。只要 GitHub token 有权限,私有仓库和公开仓库没区别。

### Q4: 能支持 GitLab 吗?

A: v0.1 不支持,但架构上预留了扩展点(平台适配层)。v1.0 可以加。

### Q5: 会不会误判?

A: 会。所以输出的是"建议",不是"命令"。维护者永远是最终决策者。

---

## 10. 下一步(完成 v0.1 后)

1. **在真实项目上试用** — 找 2-3 个开源项目(50+ issues)测试
2. **收集反馈** — 建议采纳率、报告质量、成本
3. **迭代 Prompt** — 根据反馈调优评分标准
4. **写一篇博客** — 介绍"维护者决策智能"这个方向
5. **开始 v0.2** — 决策记忆

---

**文档结束。开始编码吧!**
