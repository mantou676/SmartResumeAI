"""
文本清洗服务
对 PDF 提取的原始文本进行规范化处理
"""
import re


def clean_resume_text(raw_text: str) -> str:
    """
    清洗简历文本，使其适合 AI 分析

    处理步骤：
    1. 去除控制字符（保留换行）
    2. 合并多余空白行
    3. 全角转半角（英文/数字部分）
    4. 去除页眉页脚常见干扰
    5. 规范化中英文混排间距
    """

    # 1. 去除控制字符（\x00-\x08, \x0b-\x0c, \x0e-\x1f）
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', raw_text)

    # 2. 制表符 → 空格
    text = text.replace('\t', ' ')

    # 3. 合并连续空白行（3+ 换行 → 2 换行）
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

    # 4. 去除行首行尾多余空格
    lines = [line.strip() for line in text.split('\n')]

    # 5. 去除纯符号行（分割线等）
    lines = [l for l in lines if not re.match(r'^[=+\-—_\s*#~•·●]{5,}$', l)]

    # 6. 去除太短的无意义行（单字符）
    lines = [l for l in lines if len(l) > 1 or l.isdigit()]

    text = '\n'.join(lines)

    # 7. 规范化中文和英文/数字之间的间距（可选：在中文和英文之间加空格）
    # text = re.sub(r'([一-龥])([a-zA-Z0-9])', r'\1 \2', text)
    # text = re.sub(r'([a-zA-Z0-9])([一-龥])', r'\1 \2', text)

    # 8. 去除多余空格
    text = re.sub(r' {2,}', ' ', text)

    return text.strip()
