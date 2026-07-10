"""
简历评分与匹配服务
- basic_score: 基于关键词的快速评分（无需 AI）
- ai_score: 基于通义千问的深度语义评分
"""
import json
import re
import logging
from config import settings

logger = logging.getLogger(__name__)

# ──── 技术关键词匹配模式 ────

TECH_PATTERNS = [
    # 编程语言
    r'\b(python|java|javascript|typescript|golang|go\b|rust|c\+\+|c#|php|ruby|swift|kotlin|scala|r\b|matlab)\b',
    # 前端
    r'\b(react|vue|angular|svelte|next\.?js|nuxt\.?js|jquery|bootstrap|tailwind|webpack|vite|html5?|css3?)\b',
    # 后端
    r'\b(django|flask|fastapi|spring\s?boot|express|node\.?js|nestjs|gin|laravel|rails)\b',
    # 云 & DevOps
    r'\b(docker|kubernetes|k8s|aws|azure|gcp|aliyun|terraform|jenkins|gitlab|github\s?actions|ci/cd|devops)\b',
    # 数据库 & 中间件
    r'\b(redis|mysql|postgresql|mongodb|elasticsearch|kafka|rabbitmq|nginx|haproxy|etcd|zookeeper)\b',
    # AI & 数据
    r'\b(machine\s?learning|deep\s?learning|nlp|computer\s?vision|tensorflow|pytorch|pandas|numpy|spark|hadoop|flink)\b',
    # 架构
    r'\b(microservice|restful|graphql|grpc|api|saas|paas|serverless|mvc|mvvm|ddd)\b',
    # 管理
    r'\b(agile|scrum|kanban|jira|confluence|项目管理|团队管理|技术管理)\b',
]


def _extract_keywords(text: str) -> set:
    """从文本中提取技术关键词"""
    text_lower = text.lower()
    keywords = set()
    for pattern in TECH_PATTERNS:
        matches = re.findall(pattern, text_lower)
        if matches:
            # matches 可能是字符串或元组（取决于正则分组）
            for m in matches:
                if isinstance(m, tuple):
                    keywords.update(k for k in m if k)
                else:
                    keywords.add(m)
    return keywords


def _parse_years_from_text(text: str) -> float:
    """从文本中解析工作年限数字"""
    # "5年" / "3-5年" / "5 years" / "工作5年"
    patterns = [
        r'(\d+)\s*年',
        r'(\d+)\s*years?',
        r'(\d+)\s*-\s*(\d+)\s*年',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            if len(groups) == 2:
                return (int(groups[0]) + int(groups[1])) / 2
            return float(groups[0])
    return 0.0


def basic_score(resume_text: str, jd_text: str, extracted_info: dict) -> dict:
    """
    基础关键词匹配评分（不调用 AI）

    Returns:
        包含 overall_score, score_breakdown, keyword_analysis, matched_keywords, missing_keywords 的字典
    """
    # 1. 提取 JD 关键词
    jd_keywords = _extract_keywords(jd_text)

    # 也提取 JD 中的大写词（可能是专有名词/职位名）
    caps = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', jd_text)
    jd_keywords.update(c.lower() for c in caps if len(c) > 2)

    # 2. 提取简历关键词
    resume_keywords = _extract_keywords(resume_text)

    # 3. 匹配计算
    matched = jd_keywords & resume_keywords
    missing = jd_keywords - resume_keywords

    if len(jd_keywords) == 0:
        skill_match_rate = 0.0
    else:
        skill_match_rate = len(matched) / len(jd_keywords)

    # 4. 关键词权重分析
    keyword_analysis = []
    for kw in jd_keywords:
        # 简单权重：按关键词出现频率
        weight = min(1.0, jd_text.lower().count(kw) * 0.3 + 0.5)
        keyword_analysis.append({
            "keyword": kw,
            "weight": round(weight, 2),
            "matched": kw in matched,
        })

    # 5. 经验相关性
    work_years_str = str(extracted_info.get("background", {}).get("work_years", ""))
    candidate_years = _parse_years_from_text(work_years_str)
    jd_years = _parse_years_from_text(jd_text)

    if jd_years == 0:
        exp_relevance_score = 70.0
        exp_detail = "岗位未明确要求工作年限"
    elif candidate_years >= jd_years:
        exp_relevance_score = 90.0
        exp_detail = f"候选人 {work_years_str} 满足岗位要求 {jd_years}年"
    elif candidate_years >= jd_years * 0.6:
        exp_relevance_score = 65.0
        exp_detail = f"候选人 {work_years_str} 接近岗位要求 {jd_years}年"
    else:
        exp_relevance_score = 30.0
        exp_detail = f"候选人 {work_years_str} 低于岗位要求 {jd_years}年"

    # 6. 综合评分
    overall_score = round(skill_match_rate * 100, 1)

    return {
        "overall_score": overall_score,
        "score_breakdown": {
            "skill_match": {
                "score": round(skill_match_rate * 100, 1),
                "matched": list(matched),
                "missing": list(missing),
            },
            "experience_relevance": {
                "score": exp_relevance_score,
                "detail": exp_detail,
            },
            "education_match": {
                "score": 70.0,
                "detail": "学历信息需人工确认",
            },
            "keyword_overlap": {
                "score": round(skill_match_rate * 100, 1),
                "overlap_count": len(matched),
                "keywords": list(jd_keywords),
            },
        },
        "keyword_analysis": keyword_analysis,
        "matched_keywords": list(matched),
        "missing_keywords": list(missing),
    }


# ──── AI 评分 Prompt ────

SCORING_SYSTEM_PROMPT = """你是一个专业的招聘评估助手。请根据岗位需求(JD)和候选人简历信息进行匹配度评估。

你必须严格返回 JSON 格式，不要包含任何 markdown 标记或解释文本。

输出 JSON Schema：
{
  "overall_score": 0-100的整数总分,
  "score_breakdown": {
    "skill_match": {
      "score": 0-100的技能匹配分数,
      "matched": ["匹配的技能"],
      "missing": ["JD需要但简历缺失的技能"]
    },
    "experience_relevance": {
      "score": 0-100的经验相关度分数,
      "detail": "简要说明"
    },
    "education_match": {
      "score": 0-100的学历匹配分数,
      "detail": "简要说明"
    }
  },
  "matched_keywords": ["JD和简历都有的关键词"],
  "missing_keywords": ["JD有但简历没有的关键词"],
  "strengths": ["候选人的2-3个优势"],
  "weaknesses": ["候选人的2-3个不足"],
  "recommendation": "2-3句话的总体评价和建议"
}

评分标准：
- 技能匹配（40%权重）：技术栈重叠度
- 经验水平（30%权重）：工作年限是否达标
- 行业相关性（20%权重）：项目经验与岗位的相关性
- 学历匹配（10%权重）：学历是否符合要求
"""

SCORING_USER_TEMPLATE = """=== 岗位需求 ===
{jd_text}

=== 候选人信息 ===
姓名: {name}
期望职位: {desired_position}
工作年限: {work_years}
学历: {education}
技能: {skills}

项目经历:
{projects}

简历全文:
{resume_text}

请评估匹配度并返回 JSON："""


async def ai_score(resume_text: str, jd_text: str, extracted_info: dict) -> dict:
    """
    AI 深度评分（调用通义千问）

    Args:
        resume_text: 简历清洗文本
        jd_text: 岗位需求描述
        extracted_info: AI 提取的结构化信息

    Returns:
        包含 overall_score, score_breakdown, matched_keywords, missing_keywords, recommendation 的字典
    """
    if not settings.dashscope_configured:
        raise RuntimeError("DashScope API Key 未配置")

    try:
        from openai import AsyncOpenAI
    except ImportError:
        raise ImportError("请安装 openai: pip install openai")

    client = AsyncOpenAI(
        api_key=settings.DASHSCOPE_API_KEY,
        base_url=settings.DASHSCOPE_BASE_URL,
        timeout=settings.AI_TIMEOUT_SECONDS,
    )

    basic_info = extracted_info.get("basic_info", {})
    job_info = extracted_info.get("job_info", {})
    background = extracted_info.get("background", {})

    skills = background.get("skills", [])
    projects = background.get("projects", [])
    projects_str = json.dumps(projects, ensure_ascii=False, indent=2) if projects else "无"

    user_message = SCORING_USER_TEMPLATE.format(
        jd_text=jd_text[:2000],
        name=basic_info.get("name", "未知"),
        desired_position=job_info.get("desired_position", "未填写"),
        work_years=background.get("work_years", "未填写"),
        education=background.get("education", "未填写"),
        skills=", ".join(skills) if skills else "未填写",
        projects=projects_str,
        resume_text=resume_text[:4000],
    )

    last_error = None
    for attempt in range(settings.AI_MAX_RETRIES + 1):
        try:
            completion = await client.chat.completions.create(
                model=settings.AI_SCORE_MODEL,
                messages=[
                    {"role": "system", "content": SCORING_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=settings.AI_SCORE_TEMPERATURE,
                max_tokens=settings.AI_MAX_TOKENS_SCORE,
            )

            raw_output = completion.choices[0].message.content
            tokens_used = completion.usage.total_tokens if completion.usage else 0

            result = _parse_json_output(raw_output)
            result["tokens_used"] = tokens_used
            return result

        except json.JSONDecodeError as e:
            logger.warning(f"AI 评分返回非 JSON (尝试 {attempt + 1}): {e}")
            last_error = e
        except Exception as e:
            logger.error(f"AI 评分调用失败 (尝试 {attempt + 1}): {e}")
            last_error = e
            if attempt >= settings.AI_MAX_RETRIES:
                raise

    raise RuntimeError(f"AI 评分失败（已重试 {settings.AI_MAX_RETRIES} 次），最后错误: {last_error}")


def _parse_json_output(raw_output: str) -> dict:
    """尝试解析 AI 返回的 JSON"""
    text = raw_output.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:]) if len(lines) > 1 else text
    if text.endswith("```"):
        text = text[:-3].strip()
    return json.loads(text)
