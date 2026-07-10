import { useState } from 'react';

/**
 * 岗位需求输入组件
 */
export default function JobInput({ onMatch, onExtract, disabled, hasResume }) {
  const [jd, setJd] = useState('');
  const [useAi, setUseAi] = useState(true);

  const handleSubmit = () => {
    if (!jd.trim()) {
      alert('请输入岗位需求描述');
      return;
    }
    onMatch?.(jd.trim(), useAi);
  };

  return (
    <div className="card job-card">
      <h2>🎯 岗位需求描述</h2>
      <textarea
        className="jd-textarea"
        placeholder="请粘贴岗位需求（JD），例如：&#10;&#10;招聘高级前端工程师，要求3年以上经验，精通 React/Vue，熟悉 TypeScript..."
        value={jd}
        onChange={(e) => setJd(e.target.value)}
        rows={6}
        disabled={disabled}
      />
      <div className="job-actions">
        <label className="ai-toggle">
          <input
            type="checkbox"
            checked={useAi}
            onChange={(e) => setUseAi(e.target.checked)}
            disabled={disabled}
          />
          <span>🤖 AI 深度评分</span>
        </label>
        <div className="job-buttons">
          {hasResume && (
            <button
              className="btn btn-secondary"
              onClick={onExtract}
              disabled={disabled}
            >
              🔍 提取信息
            </button>
          )}
          <button
            className="btn btn-primary"
            onClick={handleSubmit}
            disabled={disabled || !jd.trim()}
          >
            📊 开始匹配
          </button>
        </div>
      </div>
    </div>
  );
}
