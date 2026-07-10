"""
PDF 解析服务
使用 PyMuPDF (fitz) 逐页提取文本，支持多页简历
"""
import io
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def parse_pdf_bytes(content: bytes) -> Tuple[str, int]:
    """
    从 PDF 字节流中提取文本

    Args:
        content: PDF 文件的字节内容

    Returns:
        (提取的完整文本, 总页数)

    Raises:
        ValueError: 文件无效或无法解析
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("请安装 PyMuPDF: pip install pymupdf")

    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception as e:
        raise ValueError(f"无法打开 PDF 文件: {e}")

    page_count = doc.page_count
    if page_count == 0:
        doc.close()
        raise ValueError("PDF 文件为空，没有页面")

    all_text_parts = []
    for page_num in range(page_count):
        try:
            page = doc.load_page(page_num)
            page_text = page.get_text("text")
            if page_text.strip():
                all_text_parts.append(page_text.strip())
        except Exception as e:
            logger.warning(f"第 {page_num + 1} 页提取失败: {e}")
            continue

    doc.close()

    if not all_text_parts:
        raise ValueError("无法从 PDF 中提取任何文本，可能是扫描件或图片型 PDF")

    # 用换页符连接各页
    full_text = "\n\n".join(all_text_parts)

    return full_text, page_count


def parse_pdf_file(filepath: str) -> Tuple[str, int]:
    """
    从文件路径读取 PDF 并提取文本

    Args:
        filepath: PDF 文件路径

    Returns:
        (提取的完整文本, 总页数)
    """
    with open(filepath, "rb") as f:
        content = f.read()
    return parse_pdf_bytes(content)
