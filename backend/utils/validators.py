"""
通用校验工具
正则表达式校验电话、邮箱等
"""
import re


# 中国大陆手机号：1 开头，第二位 3-9，共 11 位
PHONE_PATTERN = re.compile(r'1[3-9]\d{9}')

# 邮箱正则
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

# 中文姓名：2-4 个汉字
CHINESE_NAME_PATTERN = re.compile(r'[一-龥]{2,4}')

# PDF 文件头魔数
PDF_MAGIC_BYTES = b'%PDF'


def is_valid_pdf_magic(content: bytes) -> bool:
    """检查文件头是否为 PDF"""
    return content[:4] == PDF_MAGIC_BYTES


def extract_phone(text: str) -> str:
    """从文本中提取手机号"""
    match = PHONE_PATTERN.search(text)
    return match.group() if match else ""


def extract_email(text: str) -> str:
    """从文本中提取邮箱地址"""
    match = EMAIL_PATTERN.search(text.lower())
    return match.group() if match else ""


def validate_phone(phone: str) -> bool:
    """校验手机号格式"""
    return bool(phone and PHONE_PATTERN.fullmatch(str(phone)))


def validate_email(email: str) -> bool:
    """校验邮箱格式"""
    return bool(email and EMAIL_PATTERN.fullmatch(str(email)))


def clean_phone(phone: str) -> str:
    """清洗手机号：去除非数字字符"""
    return re.sub(r'[^\d]', '', str(phone))


def clean_email(email: str) -> str:
    """清洗邮箱：去空格、转小写"""
    return str(email).strip().lower()
