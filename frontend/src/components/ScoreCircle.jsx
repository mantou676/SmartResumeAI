/**
 * 评分圆环组件
 * 使用 SVG 绘制圆形进度条
 */
export default function ScoreCircle({ score, size = 120, strokeWidth = 10, label = '匹配度' }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (score / 100) * circumference;

  // 根据分数决定颜色
  const getColor = (s) => {
    if (s >= 80) return '#22c55e'; // green
    if (s >= 60) return '#f59e0b'; // yellow
    return '#ef4444'; // red
  };

  const color = getColor(score);

  return (
    <div className="score-circle" style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        {/* 背景圆 */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={strokeWidth}
        />
        {/* 进度圆 */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: 'stroke-dashoffset 0.8s ease' }}
        />
      </svg>
      <div className="score-inner">
        <span className="score-value" style={{ color }}>{score}</span>
        <span className="score-label">{label}</span>
      </div>
    </div>
  );
}
