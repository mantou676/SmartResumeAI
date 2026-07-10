"""
Pydantic 请求/响应数据模型
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


# ──── 基础子模型 ────

class BasicInfo(BaseModel):
    """基本信息"""
    name: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""


class JobInfo(BaseModel):
    """求职信息（加分项）"""
    desired_position: str = ""
    expected_salary: str = ""


class Project(BaseModel):
    """项目经历"""
    name: str = ""
    role: str = ""
    duration: str = ""
    description: str = ""
    tech_stack: List[str] = Field(default_factory=list)


class Education(BaseModel):
    """教育背景"""
    school: str = ""
    degree: str = ""
    major: str = ""
    year: str = ""


class Background(BaseModel):
    """背景信息（加分项）"""
    work_years: str = ""
    education: str = ""                              # AI 返回学历描述字符串
    education_list: List[Education] = Field(default_factory=list)  # 结构化学历（预留）
    projects: List[Project] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)


class ExtractedInfo(BaseModel):
    """完整的提取信息"""
    basic_info: BasicInfo = Field(default_factory=BasicInfo)
    job_info: JobInfo = Field(default_factory=JobInfo)
    background: Background = Field(default_factory=Background)


# ──── 上传/解析 ────

class UploadResponse(BaseModel):
    """简历上传响应"""
    resume_id: str
    filename: str
    file_size: int
    page_count: int
    raw_text: str
    cleaned_text: str
    created_at: str


class ExtractResponse(BaseModel):
    """信息提取响应"""
    resume_id: str
    basic_info: BasicInfo = Field(default_factory=BasicInfo)
    job_info: JobInfo = Field(default_factory=JobInfo)
    background: Background = Field(default_factory=Background)
    tokens_used: int = 0


# ──── 评分匹配 ────

class MatchRequest(BaseModel):
    """匹配请求"""
    job_description: str = Field(..., min_length=1, max_length=5000, description="岗位需求描述")
    use_ai_scoring: bool = Field(default=True, description="是否使用 AI 深度评分")


class ScoreBreakdown(BaseModel):
    """分项得分"""
    skill_match: dict = Field(default_factory=dict)
    experience_relevance: dict = Field(default_factory=dict)
    education_match: dict = Field(default_factory=dict)
    keyword_overlap: dict = Field(default_factory=dict)


class KeywordAnalysis(BaseModel):
    """关键词分析"""
    keyword: str
    weight: float
    matched: bool


class MatchResponse(BaseModel):
    """匹配评分响应"""
    resume_id: str
    overall_score: float = 0.0
    score_breakdown: ScoreBreakdown = Field(default_factory=ScoreBreakdown)
    keyword_analysis: List[KeywordAnalysis] = Field(default_factory=list)
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    ai_feedback: str = ""
    tokens_used: int = 0


# ──── 通用 ────

class ErrorResponse(BaseModel):
    """统一错误响应"""
    error: str
    message: str


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    redis_enabled: bool
    dashscope_configured: bool
