# AI 简历教练（AI Resume Coach）

招聘方视角的两段式评估工具：**第一步 · 简历评估**（4 步串行深挖）→ **第二步 · 面试评分**（5 维度量化打分）。前端单文件 HTML，后端 FastAPI + DeepSeek，简历数据仅在本机流转。

## 功能亮点

- **4 步简历评估**：第一印象定论 → 地毯式深度审计 → 致命弱点 + 约面追问清单 → 最终裁决（约面 / 不约面 / 待定）
- **5 维度面试评分**：专业能力与深度 / 简历真实性与一致度 / 岗位匹配度 / 结构化思维与表达 / 学习潜力与主动性，等权总分 + 三档判定（通过 / 待定 / 不通过）
- **SSE 流式逐步展示**：每步评估完成即刻推送到前端，进度实时可见
- **JD 岗位库**：增删改查、文件上传解析、后端持久化，评估时一键选用
- **历史记录**：评估与评分结果本地保存，随时回看
- **一键启动**：Windows 双击 `start.bat` 即用

## 评估流程

```mermaid
flowchart LR
    A["上传简历<br/>选择 JD"] --> B["Step 1<br/>第一印象<br/>初步诊断"]
    B --> C["Step 2<br/>地毯式<br/>深度审计"]
    C --> D["Step 3<br/>致命弱点<br/>追问清单"]
    D --> E["Step 4<br/>最终裁决"]
    E --> F["面试评分<br/>5 维度 + 三档判定"]
```

## 目录结构

```
简历优化教练-workspace/
├── shaping/                  # 产品定型文档
├── prd/PRD.md                # 产品需求文档
├── prototype/index.html      # 前端（单文件）
└── backend/
    ├── app.py                # FastAPI 后端
    ├── prompts.py            # 全部 prompt
    ├── requirements.txt
    └── .env.example          # 配置模板
```

## 一、配置 DeepSeek Key

1. 复制 `.env.example` 为 `.env`：
   ```bash
   cd backend
   cp .env.example .env
   ```
2. 编辑 `.env`，填入你的 key：
   ```
   DEEPSEEK_API_KEY=sk-你的真实key
   ```

## 二、安装依赖

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## 三、启动

**方式一：一键启动（Windows，推荐）**

双击项目根目录的 `start.bat`，自动启动后端并打开浏览器。

**方式二：命令行**

```bash
cd backend
python app.py
```

启动后访问：**http://127.0.0.1:8000**

> 后端会同时托管前端页面（`prototype/`），无需单独打开 HTML。

## 四、使用流程

1. **第一步·简历评估**：上传简历 PDF（或 txt），可选粘贴 JD → 点「开始评估」→ 等 1–3 分钟 → 得到 4 步评估结论。
2. **第二步·面试评分**：点「进入面试评分」→ 粘贴面试过程记录 → 点「开始评分」→ 得到 5 维度打分 + 总分 + 三档判定 + 总评。
3. 结果会保存到浏览器本地（历史记录页），刷新不丢。

## 五、API

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/api/assess` | POST | multipart：`file`（简历文件）+ `jd`（可选文本），返回 4 步评估 |
| `/api/score` | POST | JSON：`{resume_review, interview_text, jd}`，返回 5 维度评分 |

## 六、评分规则（已确认）

- 5 维度各 0–10 分，小数点一位：专业能力与深度 / 简历真实性与一致度 / 岗位匹配度 / 结构化思维与表达 / 学习潜力与主动性
- 总分 = 5 维度等权平均，10 分制，小数点一位
- 三档判定：≥8 通过；6–8 待定；<6 不通过

## 七、注意事项

- 图片简历（jpg/png）暂不支持直接 OCR，请先转成 PDF（文字版）再上传。
- 4 步评估为串行调用，耗时约 1–3 分钟，属正常。
- 简历属敏感数据，仅本机内部使用，数据不出域。

## 八、开发与测试

**E2E 打印验证种子**：URL 带 `#print-verify` hash 时，页面自动注入模拟评估数据并进入结果页（第 2 张卡片故意保持折叠），用于无头浏览器验证 `@media print` 样式，正常使用零影响：

```bash
# 启动后端后，用无头 Chrome 打印验证（print 媒体原生渲染）
chrome --headless=new --no-pdf-header-footer \
  --print-to-pdf=out.pdf --virtual-time-budget=6000 \
  "http://127.0.0.1:8000/index.html#print-verify"
```

判定要点：PDF 中应含全部 4 步内容（含被折叠的 Step2「业绩数据」——证明打印时强制展开）；不应含侧边栏用户名与按钮文字。

**历史数据迁移**：Step5→Step4 重编号前的旧评估记录，页面加载时自动将 `step5` 键归一化为 `step4`（`migrateHistory()`），并在渲染层对旧键名做兜底。
