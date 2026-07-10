/**
 * 简历解析结果展示组件
 * 显示 AI 提取的结构化信息
 */
export default function ResumePreview({ parsedResume, extractedInfo }) {
  if (!parsedResume) return null;

  const basicInfo = extractedInfo?.basic_info || {};
  const jobInfo = extractedInfo?.job_info || {};
  const background = extractedInfo?.background || {};

  const hasExtracted = !!extractedInfo;

  return (
    <div className="card preview-card">
      <h2>📋 简历解析结果</h2>

      {/* 文件信息 */}
      <div className="file-meta">
        <span>📄 {parsedResume.filename}</span>
        <span>📄 {parsedResume.page_count} 页</span>
        <span>📦 {(parsedResume.file_size / 1024).toFixed(1)} KB</span>
      </div>

      {/* 基本信息 */}
      <div className="info-section">
        <h3>基本信息</h3>
        <div className="info-grid">
          <InfoItem label="姓名" value={basicInfo.name} />
          <InfoItem label="电话" value={basicInfo.phone} />
          <InfoItem label="邮箱" value={basicInfo.email} />
          <InfoItem label="地址" value={basicInfo.address} />
        </div>
      </div>

      {/* 求职信息（加分项） */}
      {hasExtracted && (jobInfo.desired_position || jobInfo.expected_salary) && (
        <div className="info-section">
          <h3>💼 求职意向</h3>
          <div className="info-grid">
            <InfoItem label="期望职位" value={jobInfo.desired_position} />
            <InfoItem label="期望薪资" value={jobInfo.expected_salary} />
          </div>
        </div>
      )}

      {/* 背景信息（加分项） */}
      {hasExtracted && (
        <div className="info-section">
          <h3>📚 背景信息</h3>
          <div className="info-grid">
            <InfoItem label="工作年限" value={background.work_years} />
            <InfoItem label="学历背景" value={background.education} />
          </div>
        </div>
      )}

      {/* 技能标签 */}
      {background.skills && background.skills.length > 0 && (
        <div className="info-section">
          <h3>🛠 技能</h3>
          <div className="skill-tags">
            {background.skills.map((skill, i) => (
              <span key={i} className="skill-tag">{skill}</span>
            ))}
          </div>
        </div>
      )}

      {/* 项目经历 */}
      {background.projects && background.projects.length > 0 && (
        <div className="info-section">
          <h3>📁 项目经历</h3>
          {background.projects.map((project, i) => (
            <div key={i} className="project-item">
              <div className="project-name">{project.name}</div>
              <div className="project-desc">{project.description}</div>
              {project.tech_stack && project.tech_stack.length > 0 && (
                <div className="skill-tags">
                  {project.tech_stack.map((tech, j) => (
                    <span key={j} className="skill-tag tech-tag">{tech}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function InfoItem({ label, value }) {
  if (!value) return null;
  return (
    <div className="info-item">
      <span className="info-label">{label}</span>
      <span className="info-value">{value}</span>
    </div>
  );
}
