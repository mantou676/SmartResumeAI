# 📄 SmartResumeAI — AI 赋能的智能简历分析系统

> 上传 PDF 简历 → AI 提取关键信息 → 岗位匹配评分，帮助招聘者快速筛选候选人。

[![Tech Stack](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![AI Model](https://img.shields.io/badge/AI-通义千问_(DashScope)-FF6B00)](https://dashscope.aliyun.com/)
[![Cloud](https://img.shields.io/badge/Cloud-阿里云_FC-FF6A00?logo=alibabacloud)](https://www.aliyun.com/product/fc)
[![Frontend](https://img.shields.io/badge/Frontend-React_18-61DAFB?logo=react)](https://react.dev/)

---

## ✨ 功能特性

| 模块 | 功能 | 状态 |
|------|------|------|
| 📤 简历上传与解析 | 支持 PDF 上传，PyMuPDF 提取文本，自动清洗分段 | ✅ 必选 |
| 🔍 关键信息提取 | AI 提取姓名/电话/邮箱/地址 (必选) + 求职意向/薪资/学历/项目经历 (加分) | ✅ 必选 |
| 📊 简历评分与匹配 | 关键词匹配 + 通义千问 AI 深度评分 | ✅ 必选 |
| 💾 结果缓存 | 内存 LRU 缓存 + Redis 缓存（加分项） | ✅ 必选 |
| 🖥 前端页面 | React 18 + Vite，拖拽上传，可视化评分 | ✅ 必选 |

---

## 🏗 技术架构

```
┌─────────────┐     HTTP/JSON      ┌──────────────────┐
│   React 18  │ ◄─────────────────► │  FastAPI (阿里云FC) │
│   (GitHub   │                    │  ┌───────────────┐│
│    Pages)   │                    │  │ PyMuPDF 解析  ││
└─────────────┘                    │  ├───────────────┤│
                                   │  │ DashScope AI  ││
                                   │  ├───────────────┤│
                                   │  │ Redis 缓存    ││
                                   │  └───────────────┘│
                                   └──────────────────┘
```

### 技术栈

| 层 | 选型 | 说明 |
|---|------|------|
| 运行环境 | 阿里云函数计算 FC | Serverless，按量付费 |
| 后端框架 | **FastAPI** (Python 3.10) | 自动 OpenAPI 文档，Pydantic 校验 |
| PDF 解析 | **PyMuPDF** (fitz) | 中文支持好，多页简历提取 |
| AI 模型 | **通义千问 qwen-plus** | 阿里云 DashScope SDK |
| 缓存 | 内存 LRU + **Redis** | Redis 不可用时自动降级 |
| 前端 | **React 18 + Vite** | 组件化，构建快 |
| 部署工具 | **Serverless Devs** (s.yaml) | FC 一键部署 |

---

## 🚀 快速开始

### 1. 环境准备

```bash
# Python 3.10+
python --version

# Node.js 18+
node --version

# 阿里云账号 + Serverless Devs
npm install -g @serverless-devs/s
s config add
```

### 2. 后端本地运行

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
export DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxx"
# 可选：Redis 配置
export REDIS_HOST="r-xxx.redis.rds.aliyuncs.com"
export REDIS_PASSWORD="your-password"

# 启动服务（http://localhost:8000）
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

访问 `http://localhost:8000/docs` 查看 Swagger API 文档。

### 3. 前端本地运行

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器（http://localhost:5173）
npm run dev
```

开发模式下 Vite 已配置代理，API 请求自动转发到 `http://localhost:8000`。

### 4. 后端部署到阿里云 FC

```bash
# 在项目根目录
export DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxx"

s deploy
```

### 5. 前端部署到 GitHub Pages

推送代码到 GitHub `main` 分支后，GitHub Actions 自动构建部署。

或手动部署：

```bash
cd frontend
npm run build
npx gh-pages -d dist
```

---

## 📡 API 文档

### `POST /api/resume/upload` — 上传简历

```bash
curl -X POST http://localhost:8000/api/resume/upload \
  -F "file=@resume.pdf"
```

### `POST /api/resume/{resume_id}/extract` — 提取信息

```bash
curl -X POST http://localhost:8000/api/resume/{resume_id}/extract
```

### `POST /api/resume/{resume_id}/match` — 匹配评分

```bash
curl -X POST http://localhost:8000/api/resume/{resume_id}/match \
  -H "Content-Type: application/json" \
  -d '{"job_description": "招聘高级前端工程师...", "use_ai_scoring": true}'
```

### `GET /api/health` — 健康检查

```bash
curl http://localhost:8000/api/health
```

---

## 📁 项目结构

```
SmartResumeAI/
├── backend/                      # FastAPI 后端
│   ├── main.py                   # 应用入口，CORS，路由注册
│   ├── config.py                 # 环境变量配置
│   ├── routers/
│   │   ├── resume.py             # 简历上传/提取路由
│   │   └── match.py              # 匹配评分路由
│   ├── services/
│   │   ├── pdf_parser.py         # PyMuPDF 文本提取
│   │   ├── text_cleaner.py       # 文本清洗
│   │   ├── ai_extractor.py       # DashScope 信息提取
│   │   └── scorer.py             # 关键词匹配 + AI 评分
│   ├── models/
│   │   └── schemas.py            # Pydantic 数据模型
│   ├── cache/
│   │   ├── base.py               # 缓存抽象接口
│   │   ├── memory_cache.py       # 内存 LRU 缓存
│   │   └── redis_cache.py        # Redis 缓存
│   ├── utils/
│   │   └── validators.py         # 正则校验工具
│   └── requirements.txt
├── frontend/                     # React 前端
│   ├── src/
│   │   ├── App.jsx               # 主应用
│   │   ├── components/
│   │   │   ├── FileUpload.jsx    # 拖拽上传
│   │   │   ├── ResumePreview.jsx # 解析结果
│   │   │   ├── JobInput.jsx      # JD 输入
│   │   │   ├── MatchResult.jsx   # 评分展示
│   │   │   └── ScoreCircle.jsx   # SVG 评分圆环
│   │   ├── hooks/
│   │   │   └── useAnalysis.js    # 状态管理 Hook
│   │   └── api/
│   │       └── index.js          # API 封装
│   └── vite.config.js
├── s.yaml                        # Serverless Devs 部署配置
├── .github/workflows/            # CI/CD
└── README.md
```

---

## ⚙️ 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `DASHSCOPE_API_KEY` | ✅ | 阿里云 DashScope API Key |
| `REDIS_HOST` | ❌ | Redis 主机地址（不配则使用内存缓存）|
| `REDIS_PORT` | ❌ | Redis 端口，默认 6379 |
| `REDIS_PASSWORD` | ❌ | Redis 密码 |
| `DEBUG` | ❌ | 调试模式，默认 false |

---

## 🔒 安全设计

- API Key 通过环境变量注入，不硬编码
- PDF 文件魔数校验（`%PDF`），防止恶意文件上传
- 文件大小限制 10MB
- CORS 白名单只允许 GitHub Pages 和本地开发域名
- AI 输出经过 Pydantic 校验 + 正则二次校验

---

## 📝 开发日志

- **架构设计**：FastAPI + 通义千问 + React，3 层分离
- **缓存策略**：Cache-Aside 模式，Redis 不可用时自动降级为内存缓存
- **AI 容错**：JSON 解析失败重试 2 次，正则兜底校验关键字段
- **评分策略**：基础关键词匹配（快速）+ AI 语义评分（精准），两阶段互补

---

## 📄 License

MIT License
