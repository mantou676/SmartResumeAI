import ScoreCircle from './ScoreCircle';

/**
 * 匹配评分结果展示组件
 */
export default function MatchResult({ matchResult }) {
  if (!matchResult) return null;

  const breakdown = matchResult.score_breakdown || {};
  const overall = matchResult.overall_score || 0;

  return (
    <div className="card result-card">
      <h2>📊 匹配结果</h2>

      {/* 总分 */}
      <div className="overall-score-section">
        <ScoreCircle score={overall} />
        <div className="overall-label">
          {overall >= 80 ? '🎉 高度匹配' : overall >= 60 ? '👍 较为匹配' : '📉 匹配度较低'}
        </div>
      </div>

      {/* 分项得分 */}
      <div className="breakdown-section">
        <h3>分项得分</h3>
        <div className="breakdown-grid">
          {breakdown.skill_match && (
            <BreakdownCard
              title="技能匹配"
              score={breakdown.skill_match.score}
              detail={`匹配: ${(breakdown.skill_match.matched || []).join(', ') || '无'}`}
            />
          )}
          {breakdown.experience_relevance && (
            <BreakdownCard
              title="经验相关度"
              score={breakdown.experience_relevance.score}
              detail={breakdown.experience_relevance.detail}
            />
          )}
          {breakdown.education_match && (
            <BreakdownCard
              title="学历匹配"
              score={breakdown.education_match.score}
              detail={breakdown.education_match.detail}
            />
          )}
        </div>
      </div>

      {/* 关键词分析 */}
      <div className="keyword-section">
        <h3>关键词分析</h3>

        {/* 匹配的关键词 */}
        {matchResult.matched_keywords && matchResult.matched_keywords.length > 0 && (
          <div className="keyword-group">
            <span className="keyword-label">✅ 已匹配</span>
            <div className="skill-tags">
              {matchResult.matched_keywords.map((kw, i) => (
                <span key={i} className="skill-tag matched">{kw}</span>
              ))}
            </div>
          </div>
        )}

        {/* 缺失的关键词 */}
        {matchResult.missing_keywords && matchResult.missing_keywords.length > 0 && (
          <div className="keyword-group">
            <span className="keyword-label">❌ 缺失</span>
            <div className="skill-tags">
              {matchResult.missing_keywords.map((kw, i) => (
                <span key={i} className="skill-tag missing">{kw}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* AI 评语 */}
      {matchResult.ai_feedback && (
        <div className="ai-feedback-section">
          <h3>🤖 AI 综合评价</h3>
          <p className="ai-feedback">{matchResult.ai_feedback}</p>
        </div>
      )}
    </div>
  );
}

function BreakdownCard({ title, score, detail }) {
  const getColor = (s) => {
    if (s >= 80) return '#22c55e';
    if (s >= 60) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div className="breakdown-card">
      <div className="breakdown-header">
        <span className="breakdown-title">{title}</span>
        <span className="breakdown-score" style={{ color: getColor(score) }}>
          {score}分
        </span>
      </div>
      <div className="breakdown-detail">{detail}</div>
    </div>
  );
}
