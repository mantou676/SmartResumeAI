/**
 * 核心业务状态管理 Hook
 * 管理整个简历分析流程的状态转换
 *
 * 状态机:
 *   idle → uploading → parsed → extracting → extracted → matching → complete
 *   any → error
 */
import { useState, useCallback } from 'react';
import { uploadResume, extractInfo, matchResume } from '../api';

export function useAnalysis() {
  const [step, setStep] = useState('idle');
  const [resumeId, setResumeId] = useState(null);
  const [parsedResume, setParsedResume] = useState(null);
  const [extractedInfo, setExtractedInfo] = useState(null);
  const [matchResult, setMatchResult] = useState(null);
  const [error, setError] = useState(null);

  /**
   * 上传简历文件
   */
  const handleUpload = useCallback(async (file) => {
    setStep('uploading');
    setError(null);
    try {
      const result = await uploadResume(file);
      setResumeId(result.resume_id);
      setParsedResume(result);
      setStep('parsed');
      return result;
    } catch (e) {
      setError(e.message);
      setStep('error');
      throw e;
    }
  }, []);

  /**
   * 提取简历信息
   */
  const handleExtract = useCallback(async (id) => {
    const targetId = id || resumeId;
    if (!targetId) {
      setError('请先上传简历');
      setStep('error');
      return;
    }
    setStep('extracting');
    setError(null);
    try {
      const result = await extractInfo(targetId);
      setExtractedInfo(result);
      setStep('extracted');
      return result;
    } catch (e) {
      setError(e.message);
      setStep('error');
      throw e;
    }
  }, [resumeId]);

  /**
   * 匹配评分
   */
  const handleMatch = useCallback(async (id, jd, useAi = true) => {
    const targetId = id || resumeId;
    if (!targetId) {
      setError('请先上传简历');
      setStep('error');
      return;
    }
    setStep('matching');
    setError(null);
    try {
      const result = await matchResume(targetId, jd, useAi);
      setMatchResult(result);
      setStep('complete');
      return result;
    } catch (e) {
      setError(e.message);
      setStep('error');
      throw e;
    }
  }, [resumeId]);

  /**
   * 一键分析：上传 + 提取 + 匹配
   */
  const handleFullAnalysis = useCallback(async (file, jd, useAi = true) => {
    setError(null);
    try {
      const uploadResult = await handleUpload(file);
      const extractResult = await handleExtract(uploadResult.resume_id);
      const matchResult = await handleMatch(uploadResult.resume_id, jd, useAi);
      return { uploadResult, extractResult, matchResult };
    } catch (e) {
      // 错误已在各 handler 中设置
    }
  }, [handleUpload, handleExtract, handleMatch]);

  /**
   * 重置所有状态
   */
  const reset = useCallback(() => {
    setStep('idle');
    setResumeId(null);
    setParsedResume(null);
    setExtractedInfo(null);
    setMatchResult(null);
    setError(null);
  }, []);

  return {
    step,
    resumeId,
    parsedResume,
    extractedInfo,
    matchResult,
    error,
    handleUpload,
    handleExtract,
    handleMatch,
    handleFullAnalysis,
    reset,
  };
}
