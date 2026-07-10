"""
简历评分与匹配路由
POST /api/resume/{id}/match — 岗位匹配度评分
"""
import hashlib
import logging
from fastapi import APIRouter, HTTPException
from models.schemas import MatchRequest, MatchResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/resume/{resume_id}/match", response_model=MatchResponse)
async def match_resume(resume_id: str, req: MatchRequest):
    """
    将简历与岗位需求进行匹配度评分

    - 基础评分：关键词匹配 + 经验相关性
    - AI 评分（可选）：利用 AI 模型做更精准的语义匹配
    """
    # 1. 查缓存
    jd_hash = hashlib.md5(req.job_description.encode("utf-8")).hexdigest()[:12]
    cache_key = f"{resume_id}:match:{jd_hash}"

    from main import memory_cache, redis_cache

    cached = await memory_cache.get(cache_key)
    if cached:
        return MatchResponse(**cached)

    if redis_cache and redis_cache.available:
        cached = await redis_cache.get(f"resume:{cache_key}")
        if cached:
            return MatchResponse(**cached)

    # 2. 获取已解析文本和提取信息
    parsed = await memory_cache.get(f"{resume_id}:parsed")
    if not parsed:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "简历不存在，请先上传"})

    extracted = await memory_cache.get(f"{resume_id}:extracted")
    if not extracted:
        # 还没提取过，自动触发提取
        logger.info("尚未提取信息，自动触发 AI 提取...")
        from services.ai_extractor import extract_info_from_text
        try:
            ai_result = await extract_info_from_text(parsed["cleaned_text"])
            extracted = {
                "resume_id": resume_id,
                "basic_info": ai_result.get("basic_info", {}),
                "job_info": ai_result.get("job_info", {}),
                "background": ai_result.get("background", {}),
                "tokens_used": ai_result.get("tokens_used", 0),
            }
            await memory_cache.set(f"{resume_id}:extracted", extracted)
            if redis_cache and redis_cache.available:
                await redis_cache.set(f"resume:{resume_id}:extracted", extracted)
        except Exception as e:
            raise HTTPException(status_code=500, detail={"error": "AUTO_EXTRACT_FAILED", "message": f"自动提取失败: {str(e)}"})

    # 3. 基础关键词匹配评分
    from services.scorer import basic_score, ai_score
    cleaned_text = parsed["cleaned_text"]

    basic_result = basic_score(cleaned_text, req.job_description, extracted)

    # 4. 可选 AI 深度评分
    ai_feedback = ""
    tokens_used = 0
    if req.use_ai_scoring:
        try:
            ai_result = await ai_score(cleaned_text, req.job_description, extracted)
            # 合并 AI 评分
            basic_result["overall_score"] = ai_result.get("overall_score", basic_result["overall_score"])
            basic_result["score_breakdown"] = ai_result.get("score_breakdown", basic_result["score_breakdown"])
            ai_feedback = ai_result.get("recommendation", "")
            tokens_used = ai_result.get("tokens_used", 0)
            # 合并关键词
            if ai_result.get("matched_keywords"):
                basic_result["matched_keywords"] = ai_result["matched_keywords"]
            if ai_result.get("missing_keywords"):
                basic_result["missing_keywords"] = ai_result["missing_keywords"]
        except Exception as e:
            logger.warning(f"AI 评分失败，使用基础评分: {e}")
            ai_feedback = "AI 评分暂时不可用，当前为基础关键词匹配结果"

    # 5. 构建响应
    response_data = {
        "resume_id": resume_id,
        "overall_score": basic_result["overall_score"],
        "score_breakdown": basic_result.get("score_breakdown", {}),
        "keyword_analysis": basic_result.get("keyword_analysis", []),
        "matched_keywords": basic_result.get("matched_keywords", []),
        "missing_keywords": basic_result.get("missing_keywords", []),
        "ai_feedback": ai_feedback,
        "tokens_used": tokens_used,
    }

    # 6. 缓存结果
    await memory_cache.set(cache_key, response_data)
    if redis_cache and redis_cache.available:
        await redis_cache.set(f"resume:{cache_key}", response_data)

    return MatchResponse(**response_data)
