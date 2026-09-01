# AI 简历教练 · 运行说明

两段式招聘评估工具：第一步简历评估（4 步），第二步面试评分（5 维度）。前端单文件 HTML，后端 FastAPI + DeepSeek。

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
