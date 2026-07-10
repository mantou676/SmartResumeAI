/**
 * API 封装层
 * 所有后端接口调用集中管理
 */
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
  headers: {
    'Accept': 'application/json',
  },
});

// 响应拦截器：统一错误处理
client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      const detail = error.response.data?.detail;
      const message = typeof detail === 'object' ? detail.message : (detail || error.message);
      throw new Error(message);
    }
    if (error.code === 'ECONNABORTED') {
      throw new Error('请求超时，请检查网络连接');
    }
    throw new Error('网络错误，无法连接到服务器');
  }
);

/**
 * 上传 PDF 简历并解析
 * @param {File} file - PDF 文件
 * @returns {Promise<object>} 解析结果
 */
export async function uploadResume(file) {
  const formData = new FormData();
  formData.append('file', file);
  return client.post('/api/resume/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}

/**
 * AI 提取简历关键信息
 * @param {string} resumeId - 简历 ID
 * @returns {Promise<object>} 提取的结构化信息
 */
export async function extractInfo(resumeId) {
  return client.post(`/api/resume/${resumeId}/extract`);
}

/**
 * 简历与岗位匹配评分
 * @param {string} resumeId - 简历 ID
 * @param {string} jobDescription - 岗位描述
 * @param {boolean} useAiScoring - 是否使用 AI 深度评分
 * @returns {Promise<object>} 匹配评分结果
 */
export async function matchResume(resumeId, jobDescription, useAiScoring = true) {
  return client.post(`/api/resume/${resumeId}/match`, {
    job_description: jobDescription,
    use_ai_scoring: useAiScoring,
  });
}

/**
 * 健康检查
 * @returns {Promise<object>} 服务状态
 */
export async function healthCheck() {
  return client.get('/api/health');
}
