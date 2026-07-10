import { useState } from 'react';
import FileUpload from './components/FileUpload';
import ResumePreview from './components/ResumePreview';
import JobInput from './components/JobInput';
import MatchResult from './components/MatchResult';
import { useAnalysis } from './hooks/useAnalysis';
import './App.css';

export default function App() {
  const {
    step,
    parsedResume,
    extractedInfo,
    matchResult,
    error,
    handleUpload,
    handleExtract,
    handleMatch,
    reset,
  } = useAnalysis();

  const [selectedFile, setSelectedFile] = useState(null);

  const isLoading = step === 'uploading' || step === 'extracting' || step === 'matching';

  const onFileSelect = async (file) => {
    setSelectedFile(file);
    try {
      await handleUpload(file);
    } catch {
      // error handled in hook
    }
  };

  const onExtract = () => {
    handleExtract(parsedResume?.resume_id);
  };

  const onMatch = (jd, useAi) => {
    handleMatch(parsedResume?.resume_id, jd, useAi);
  };

  const onReset = () => {
    setSelectedFile(null);
    reset();
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <h1>📄 SmartResumeAI</h1>
        <p className="app-subtitle">AI 赋能的智能简历分析系统</p>
        <p className="app-desc">上传 PDF 简历 → AI 提取关键信息 → 岗位匹配评分</p>
      </header>

      {/* Main Content */}
      <main className="app-main">
        {/* 错误提示 */}
        {error && (
          <div className="error-banner">
            <span>⚠️ {error}</span>
            <button className="btn-close">×</button>
          </div>
        )}

        {/* 加载状态 */}
        {isLoading && (
          <div className="loading-banner">
            <div className="spinner" />
            <span>
              {step === 'uploading' && '正在解析 PDF 文件...'}
              {step === 'extracting' && 'AI 正在提取关键信息...'}
              {step === 'matching' && '正在进行匹配评分...'}
            </span>
          </div>
        )}

        {/* Step 指示器 */}
        <div className="steps-bar">
          <StepIndicator num={1} label="上传简历" active={step === 'idle'} done={step !== 'idle' && step !== 'uploading' && step !== 'error'} />
          <StepIndicator num={2} label="解析提取" active={step === 'parsed' || step === 'extracting'} done={step === 'extracted' || step === 'matching' || step === 'complete'} />
          <StepIndicator num={3} label="匹配评分" active={step === 'matching'} done={step === 'complete'} />
        </div>

        {/* 上传区域 */}
        <FileUpload
          onUpload={onFileSelect}
          disabled={isLoading}
        />

        {/* 简历预览 */}
        {(parsedResume || extractedInfo) && (
          <ResumePreview
            parsedResume={parsedResume}
            extractedInfo={extractedInfo}
          />
        )}

        {/* 岗位输入 */}
        {parsedResume && (
          <JobInput
            onMatch={onMatch}
            onExtract={onExtract}
            disabled={isLoading}
            hasResume={!!parsedResume}
          />
        )}

        {/* 匹配结果 */}
        {matchResult && (
          <MatchResult matchResult={matchResult} />
        )}

        {/* 重置按钮 */}
        {(parsedResume || matchResult) && (
          <div className="reset-section">
            <button className="btn btn-reset" onClick={onReset}>
              🔄 重新分析
            </button>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p>Powered by 通义千问 (DashScope) · FastAPI · React · 阿里云 FC</p>
      </footer>
    </div>
  );
}

function StepIndicator({ num, label, active, done }) {
  const className = done ? 'step done' : active ? 'step active' : 'step';
  return (
    <div className={className}>
      <span className="step-num">{done ? '✓' : num}</span>
      <span className="step-label">{label}</span>
    </div>
  );
}
