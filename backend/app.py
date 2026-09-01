# -*- coding: utf-8 -*-
"""AI 简历教练 —— FastAPI 后端。

接口：
- POST /api/assess  上传简历文件 + JD → 4 步简历评估
- POST /api/score   面试记录 + 第一步结果 → 5 维度面试评分

依赖 DeepSeek API（deepseek-chat），通过环境变量 DEEPSEEK_API_KEY 配置。
"""

import io
import json
import os
import re
import threading
import uuid
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from prompts import (
    SCORE_SYSTEM,
    STEP1_SYSTEM,
    STEP2_SYSTEM,
    STEP3_SYSTEM,
    STEP5_SYSTEM,
    assess_user,
    score_user,
)

app = FastAPI(title="AI 简历教练")

# 加载 .env（若存在），优先于已设置的环境变量
load_dotenv(Path(__file__).parent / ".env")

# 允许前端（file:// 或 localhost）跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"
TEMPERATURE = 0.7


# ---------- DeepSeek 调用 ----------

def call_deepseek(system: str, user: str) -> str:
    if not DEEPSEEK_API_KEY:
        raise HTTPException(status_code=500, detail="未配置 DEEPSEEK_API_KEY，请在环境变量或 .env 中设置。")
    resp = requests.post(
        DEEPSEEK_URL,
        headers={
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": TEMPERATURE,
            "response_format": {"type": "json_object"},
            "stream": False,
        },
        timeout=180,
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"DeepSeek 调用失败：{resp.status_code} {resp.text[:300]}")
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def parse_json(text: str):
    """容错解析 LLM 返回的 JSON（兼容 markdown 代码块包裹）。"""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    return json.loads(text)


# ---------- 文档解析 ----------

def extract_text(filename: str, data: bytes) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".pdf":
        try:
            import pdfplumber
        except ImportError:
            raise HTTPException(status_code=500, detail="缺少 pdfplumber，请先 pip install pdfplumber。")
        text = ""
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                t = page.extract_text() or ""
                text += t + "\n"
        text = text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="PDF 未提取到文本，可能是扫描件/纯图片，请提供可复制文字的 PDF 或直接粘贴文本。")
        return text
    if ext in {".txt", ".md", ".text"}:
        text = data.decode("utf-8", errors="ignore").strip()
        if not text:
            raise HTTPException(status_code=400, detail="文件内容为空。")
        return text
    raise HTTPException(
        status_code=400,
        detail=f"暂不支持 {ext} 格式，请上传 PDF 或 txt/md 文本文件（图片简历请先转成 PDF）。",
    )


# ---------- 业务编排 ----------

def run_assess(resume_text: str, jd_text: str) -> dict:
    """第一步：4 步串行评估（每步结果作为下一步上下文）。"""
    s1 = parse_json(call_deepseek(STEP1_SYSTEM, assess_user(resume_text, jd_text)))

    s2_user = assess_user(resume_text, jd_text) + f"\n\n<step1_result>{json.dumps(s1, ensure_ascii=False)}</step1_result>"
    s2 = parse_json(call_deepseek(STEP2_SYSTEM, s2_user))

    s3_user = assess_user(resume_text, jd_text) + f"\n\n<step2_result>{json.dumps(s2, ensure_ascii=False)}</step2_result>"
    s3 = parse_json(call_deepseek(STEP3_SYSTEM, s3_user))

    prev = {"step1": s1, "step2": s2, "step3": s3}
    s5_user = assess_user(resume_text, jd_text) + f"\n\n<previous_results>{json.dumps(prev, ensure_ascii=False)}</previous_results>"
    s5 = parse_json(call_deepseek(STEP5_SYSTEM, s5_user))

    return {"step1": s1, "step2": s2, "step3": s3, "step5": s5}


def run_score(resume_review: dict, interview_text: str, jd_text: str) -> dict:
    """第二步：5 维度面试评分。"""
    review_str = json.dumps(resume_review, ensure_ascii=False)
    user = score_user(review_str, interview_text, jd_text)
    return parse_json(call_deepseek(SCORE_SYSTEM, user))


# ---------- 接口 ----------

@app.post("/api/assess")
async def assess(file: UploadFile = File(...), jd: str = Form("")):
    data = await file.read()
    resume_text = extract_text(file.filename, data)
    try:
        result = run_assess(resume_text, jd)
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"评估失败：{str(e)}")
    return {"resume_name": file.filename, "result": result}


@app.post("/api/score")
async def score(payload: dict):
    resume_review = payload.get("resume_review") or {}
    interview_text = payload.get("interview_text") or ""
    jd_text = payload.get("jd") or ""
    if not interview_text.strip():
        raise HTTPException(status_code=400, detail="面试记录为空，请先粘贴面试过程。")
    try:
        result = run_score(resume_review, interview_text, jd_text)
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"评分失败：{str(e)}")
    return {"result": result}


@app.post("/api/parse-file")
async def parse_file(file: UploadFile = File(...)):
    """解析上传的 txt/md/pdf 文件为纯文本（用于 JD 文件上传）。"""
    data = await file.read()
    text = extract_text(file.filename, data)
    return {"filename": file.filename, "text": text}


# ---------- JD 存储（后端 JSON 文件持久化，避免依赖 localStorage） ----------

JD_FILE = Path(__file__).parent / "jds.json"
_jd_lock = threading.Lock()


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _load_jds() -> list:
    if JD_FILE.exists():
        try:
            data = json.loads(JD_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []
    return []


def _save_jds(jds: list) -> None:
    with _jd_lock:
        JD_FILE.write_text(json.dumps(jds, ensure_ascii=False, indent=2), encoding="utf-8")


@app.get("/api/jds")
def list_jds():
    return {"jds": _load_jds()}


@app.post("/api/jds")
async def create_jd(payload: dict):
    name = (payload.get("name") or "").strip()
    content = (payload.get("content") or "").strip()
    if not name or not content:
        raise HTTPException(status_code=400, detail="岗位名称和内容不能为空")
    jds = _load_jds()
    jd = {
        "id": "jd_" + uuid.uuid4().hex[:12],
        "name": name,
        "content": content,
        "createdAt": _now(),
        "updatedAt": _now(),
    }
    jds.append(jd)
    _save_jds(jds)
    return {"jd": jd}


@app.put("/api/jds/{jd_id}")
async def update_jd(jd_id: str, payload: dict):
    jds = _load_jds()
    jd = next((j for j in jds if j.get("id") == jd_id), None)
    if jd is None:
        raise HTTPException(status_code=404, detail="JD 不存在")
    if "name" in payload:
        jd["name"] = (payload.get("name") or "").strip()
    if "content" in payload:
        jd["content"] = (payload.get("content") or "").strip()
    jd["updatedAt"] = _now()
    _save_jds(jds)
    return {"jd": jd}


@app.delete("/api/jds/{jd_id}")
async def delete_jd(jd_id: str):
    _save_jds([j for j in _load_jds() if j.get("id") != jd_id])
    return {"ok": True}


# 静态托管前端（在所有 API 路由之后、启动之前注册；html=True 让 / 返回 index.html）
PROTOTYPE_DIR = Path(__file__).parent.parent / "prototype"
if PROTOTYPE_DIR.exists():
    app.mount("/", StaticFiles(directory=str(PROTOTYPE_DIR), html=True), name="static")


if __name__ == "__main__":
    import sys

    import uvicorn

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    if not DEEPSEEK_API_KEY:
        print("[提示] 未设置 DEEPSEEK_API_KEY，请先 export DEEPSEEK_API_KEY=sk-xxx 或写入 .env 文件。")
    uvicorn.run(app, host="127.0.0.1", port=8000)
