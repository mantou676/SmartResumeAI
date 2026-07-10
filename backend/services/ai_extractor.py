"""
AI 信息提取服务
使用通义千问 (DashScope) 从简历文本中提取结构化信息
"""
import json
import logging
from config import settings

logger = logging.getLogger(__name__)

# ──── Prompt 模板 ────

SYSTEM_PROMPT = """你是一个专业的简历解析助手。你的任务是从简历文本中提取结构化的关键信息。

你必须严格返回 JSON 格式，不要包含任何 markdown 代码块标记（如 ```json），不要添加任何解释文本。

输出 JSON Schema：
{
  "basic_info": {
    "name": "候选人姓名（字符串，找不到则为空字符串）",
    "phone": "手机号码（字符串，找不到则为空字符串）",
    "email": "邮箱地址（字符串，找不到则为空字符串）",
    "address": "所在城市或地区（字符串，找不到则为空字符串）"
  },
  "job_info": {
    "desired_position": "期望职位（字符串，找不到则为空字符串）",
    "expected_salary": "期望薪资（字符串，找不到则为空字符串）"
  },
  "background": {
    "work_years": "工作年限描述（字符串，如'5年'或'3-5年'，找不到则为空字符串）",
    "education": "最高学历及专业（字符串，如'本科-计算机科学'，找不到则为空字符串）",
    "projects": [
      {
        "name": "项目名称",
        "description": "项目简要描述（1-2句话）",
        "tech_stack": ["使用的技术1", "使用的技术2"]
      }
    ],
    "skills": ["技能1", "技能2", "技能3"]
  }
}

提取规则：
- 中文姓名通常为 2-4 个汉字，出现在简历开头或个人信息区域
- 手机号为 11 位数字，通常以 1 开头
- 邮箱包含 @ 符号
- 地址通常是中国城市名称
- 工作年限可能表述为"X年工作经验"、"工作X年"等
- 学历通常包含"本科"、"硕士"、"博士"、"大专"等关键词
- 项目经历通常以项目名称开头，包含技术栈描述
- 技能通常是专业技术名词（编程语言、框架、工具等）
- 如果某个字段确实无法从文本中找到，设为空字符串 "" 或空数组 []
- 项目经历最多提取 5 个
- 技能列表最多提取 20 项
"""

USER_TEMPLATE = """请从以下简历文本中提取结构化信息，仅返回 JSON：

=== 简历文本开始 ===
{resume_text}
=== 简历文本结束 ===

请提取信息并返回 JSON（不要添加 markdown 标记）："""


# ──── AI 调用 ────

async def extract_info_from_text(resume_text: str) -> dict:
    """
    调用通义千问从简历文本中提取关键信息

    Args:
        resume_text: 清洗后的简历文本

    Returns:
        包含 basic_info, job_info, background 的字典
    """
    if not settings.dashscope_configured:
        raise RuntimeError("DashScope API Key 未配置，请设置环境变量 DASHSCOPE_API_KEY")

    try:
        from openai import AsyncOpenAI
    except ImportError:
        raise ImportError("请安装 openai: pip install openai")

    client = AsyncOpenAI(
        api_key=settings.DASHSCOPE_API_KEY,
        base_url=settings.DASHSCOPE_BASE_URL,
        timeout=settings.AI_TIMEOUT_SECONDS,
    )

    # 截断过长文本（保留足够的上下文）
    max_chars = 8000
    text = resume_text[:max_chars]

    last_error = None
    for attempt in range(settings.AI_MAX_RETRIES + 1):
        try:
            completion = await client.chat.completions.create(
                model=settings.AI_EXTRACT_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_TEMPLATE.format(resume_text=text)},
                ],
                temperature=settings.AI_EXTRACT_TEMPERATURE,
                max_tokens=settings.AI_MAX_TOKENS_EXTRACT,
            )

            raw_output = completion.choices[0].message.content
            tokens_used = completion.usage.total_tokens if completion.usage else 0

            # 解析 JSON
            result = _parse_json_output(raw_output)
            result["tokens_used"] = tokens_used

            # 二次校验
            result = _validate_and_fix(result)

            return result

        except json.JSONDecodeError as e:
            logger.warning(f"AI 返回非 JSON 格式 (尝试 {attempt + 1}): {e}")
            last_error = e
            if attempt < settings.AI_MAX_RETRIES:
                continue

        except Exception as e:
            logger.error(f"DashScope 调用失败 (尝试 {attempt + 1}): {e}")
            last_error = e
            if attempt < settings.AI_MAX_RETRIES:
                continue
            raise

    raise RuntimeError(f"AI 信息提取失败（已重试 {settings.AI_MAX_RETRIES} 次），最后错误: {last_error}")


def _parse_json_output(raw_output: str) -> dict:
    """尝试解析 AI 返回的 JSON，兼容各种格式"""
    # 去除可能的 markdown 代码块标记
    text = raw_output.strip()
    if text.startswith("```"):
        # 找到第一个换行后的 JSON
        lines = text.split("\n")
        text = "\n".join(lines[1:]) if len(lines) > 1 else text
    if text.endswith("```"):
        text = text[:-3].strip()

    return json.loads(text)


def _validate_and_fix(data: dict) -> dict:
    """校验并修复 AI 提取结果"""
    from utils.validators import clean_phone, clean_email

    # 确保 basic_info
    if "basic_info" not in data or not isinstance(data["basic_info"], dict):
        data["basic_info"] = {}
    data["basic_info"].setdefault("name", "")
    data["basic_info"].setdefault("phone", "")
    data["basic_info"].setdefault("email", "")
    data["basic_info"].setdefault("address", "")

    # 确保 job_info
    if "job_info" not in data or not isinstance(data["job_info"], dict):
        data["job_info"] = {}
    data["job_info"].setdefault("desired_position", "")
    data["job_info"].setdefault("expected_salary", "")

    # 确保 background
    if "background" not in data or not isinstance(data["background"], dict):
        data["background"] = {}
    data["background"].setdefault("work_years", "")
    data["background"].setdefault("education", "")
    data["background"].setdefault("projects", [])
    data["background"].setdefault("skills", [])

    # 清洗电话和邮箱
    if data["basic_info"]["phone"]:
        data["basic_info"]["phone"] = clean_phone(data["basic_info"]["phone"])
    if data["basic_info"]["email"]:
        data["basic_info"]["email"] = clean_email(data["basic_info"]["email"])

    # 尝试从原文正则兜底
    if not data["basic_info"]["phone"]:
        from utils.validators import extract_phone
        data["basic_info"]["phone"] = extract_phone(str(data))

    # 确保列表字段是列表（AI 可能返回空字符串 "" 而不是空数组 []）
    for field in ["projects", "skills"]:
        if not isinstance(data["background"].get(field), list):
            data["background"][field] = []

    # 截断项目列表
    data["background"]["projects"] = data["background"]["projects"][:5]
    data["background"]["skills"] = data["background"]["skills"][:20]

    return data
