"""
简历上传与解析路由
POST /api/resume/upload  — 上传 PDF 简历
POST /api/resume/{id}/extract — AI 信息提取
"""
import hashlib
import uuid
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, UploadFile, File, HTTPException
from models.schemas import UploadResponse, ExtractResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# 北京时区
TZ_BEIJING = timezone(timedelta(hours=8))


def generate_resume_id(raw_text: str) -> str:
    """基于内容指纹生成简历 ID（相同简历重复上传命中缓存）"""
    fingerprint = raw_text[:2000].encode("utf-8")
    content_hash = hashlib.md5(fingerprint).hexdigest()[:12]
    short_uuid = uuid.uuid4().hex[:8]
    return f"{content_hash}{short_uuid}"


@router.post("/resume/upload", response_model=UploadResponse)
async def upload_resume(file: UploadFile = File(...)):
    """
    上传 PDF 简历，解析文本内容

    - 仅支持 PDF 格式
    - 文件大小限制 10MB
    - 自动清洗和分段
    """
    from utils.validators import is_valid_pdf_magic

    # 1. 校验文件类型
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail={"error": "INVALID_FILE", "message": "仅支持 PDF 格式文件"})

    # 2. 读取文件内容
    content = await file.read()

    # 3. 校验文件大小
    from config import settings
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail={
            "error": "FILE_TOO_LARGE",
            "message": f"文件大小不能超过 {settings.MAX_FILE_SIZE // (1024 * 1024)}MB"
        })

    # 4. 校验 PDF 文件头
    if not is_valid_pdf_magic(content):
        raise HTTPException(status_code=400, detail={"error": "INVALID_FILE", "message": "文件不是有效的 PDF 格式"})

    # 5. 解析 PDF 文本
    from services.pdf_parser import parse_pdf_bytes
    try:
        raw_text, page_count = parse_pdf_bytes(content)
    except Exception as e:
        logger.error(f"PDF 解析失败: {e}")
        raise HTTPException(status_code=422, detail={"error": "PDF_PARSE_ERROR", "message": f"PDF 解析失败: {str(e)}"})

    if not raw_text.strip():
        raise HTTPException(status_code=422, detail={"error": "EMPTY_CONTENT", "message": "PDF 文件中未提取到文本内容，可能是扫描件或图片型 PDF"})

    # 6. 文本清洗
    from services.text_cleaner import clean_resume_text
    cleaned_text = clean_resume_text(raw_text)

    # 7. 生成 ID 并缓存
    resume_id = generate_resume_id(cleaned_text)

    parsed_data = {
        "raw_text": raw_text,
        "cleaned_text": cleaned_text,
        "page_count": page_count,
        "filename": file.filename,
        "file_size": len(content),
    }

    from main import memory_cache
    await memory_cache.set(f"{resume_id}:parsed", parsed_data)

    return UploadResponse(
        resume_id=resume_id,
        filename=file.filename,
        file_size=len(content),
        page_count=page_count,
        raw_text=raw_text,
        cleaned_text=cleaned_text,
        created_at=datetime.now(TZ_BEIJING).isoformat(),
    )


@router.post("/resume/{resume_id}/extract", response_model=ExtractResponse)
async def extract_resume_info(resume_id: str):
    """
    利用 AI 从简历文本中提取关键信息

    - 必选：姓名、电话、邮箱、地址
    - 加分：求职意向、期望薪资、工作年限、学历、项目经历
    """
    # 1. 查缓存
    from main import memory_cache, redis_cache
    cache_key = f"{resume_id}:extracted"

    cached = await memory_cache.get(cache_key)
    if cached:
        return ExtractResponse(**cached)

    if redis_cache and redis_cache.available:
        cached = await redis_cache.get(f"resume:{cache_key}")
        if cached:
            return ExtractResponse(**cached)

    # 2. 获取已解析文本
    parsed = await memory_cache.get(f"{resume_id}:parsed")
    if not parsed:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "简历不存在或已过期，请重新上传"})

    cleaned_text = parsed["cleaned_text"]

    # 3. 调用 AI 提取
    from services.ai_extractor import extract_info_from_text
    try:
        result = await extract_info_from_text(cleaned_text)
    except Exception as e:
        logger.error(f"AI 提取失败: {e}")
        raise HTTPException(status_code=500, detail={"error": "AI_EXTRACT_ERROR", "message": f"AI 信息提取失败: {str(e)}"})

    # 4. 缓存结果
    response_data = {
        "resume_id": resume_id,
        "basic_info": result.get("basic_info", {}),
        "job_info": result.get("job_info", {}),
        "background": result.get("background", {}),
        "tokens_used": result.get("tokens_used", 0),
    }

    await memory_cache.set(cache_key, response_data)
    if redis_cache and redis_cache.available:
        await redis_cache.set(f"resume:{cache_key}", response_data)

    return ExtractResponse(**response_data)
