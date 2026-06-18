from fastapi import APIRouter, File, UploadFile, HTTPException
from docx import Document
from PyPDF2 import PdfReader
from io import BytesIO
import asyncio

# ai处理合同的业务逻辑
from core.config import stream_review_contract

router = APIRouter()
allow_ext = {"pdf", "doc", "docx"}
MAX_SIZE = 20 * 1024 * 1024

# 提取docx文字（同步方法，丢线程池避免阻塞uvicorn）
def extract_docx_text(file_bytes):
    doc = Document(BytesIO(file_bytes))
    full_text = []
    for para in doc.paragraphs:
        if para.text.strip():
            full_text.append(para.text)
    return "\n".join(full_text)

# 提取pdf文字（同步方法，丢线程池避免阻塞uvicorn）
def extract_pdf_text(file_bytes):
    pdf_reader = PdfReader(BytesIO(file_bytes))
    full_text = []
    for page in pdf_reader.pages:
        text = page.extract_text()
        if text.strip():
            full_text.append(text)
    return "\n".join(full_text)


@router.post('/upload')
async def upload_cotract(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1].lower()
    if ext not in allow_ext:
        raise HTTPException(status_code=400, detail="仅支持 PDF / doc / docx 文件")

    all_bytes = await file.read()
    file_size = len(all_bytes)
    if file_size > MAX_SIZE:
        raise HTTPException(status_code=400, detail="文件不能超过20MB")

    content_text = ""
    loop = asyncio.get_running_loop()
    if ext == "docx":
        # 同步解析丢到线程池，不阻塞异步事件循环
        content_text = await loop.run_in_executor(None, extract_docx_text, all_bytes)
    elif ext == "pdf":
        content_text = await loop.run_in_executor(None, extract_pdf_text, all_bytes)
    elif ext == "doc":
        content_text = "暂不支持解析.doc格式，请上传docx或PDF"

    # 新增：空文本拦截，防止传给大模型无内容报错
    if not content_text.strip():
        raise HTTPException(status_code=400, detail="文件内未识别到有效文本内容")

    return await stream_review_contract(content_text)



@router.get("/result/{task_id}")
async def get_result(task_id: str):
    return {
        "message" : "结果查询"
    }