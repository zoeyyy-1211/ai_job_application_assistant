from pathlib import Path
from typing import BinaryIO


def parse_txt(file: BinaryIO) -> str:
    """解析 TXT 简历，兼容常见 UTF-8 文本。"""
    content = file.read()
    if isinstance(content, bytes):
        return content.decode("utf-8", errors="ignore")
    return str(content)


def parse_pdf(file: BinaryIO) -> str:
    """解析 PDF 简历；扫描件 PDF 可能无法提取文本。"""
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ValueError("当前环境未安装 pypdf，请运行 pip install -r requirements.txt 后再上传 PDF。") from exc

    reader = PdfReader(file)
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    text = "\n".join(pages).strip()
    if not text:
        raise ValueError("未能从 PDF 中提取文字，可能是扫描件或图片型 PDF。")
    return text


def parse_docx(file: BinaryIO) -> str:
    """解析 DOCX 简历正文段落。"""
    try:
        from docx import Document
    except ImportError as exc:
        raise ValueError("当前环境未安装 python-docx，请运行 pip install -r requirements.txt 后再上传 DOCX。") from exc

    document = Document(file)
    paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
    text = "\n".join(paragraphs).strip()
    if not text:
        raise ValueError("未能从 DOCX 中提取文字。")
    return text


def parse_resume(uploaded_file) -> tuple[str, str | None]:
    """根据文件扩展名解析简历，返回文本和错误信息。"""
    if uploaded_file is None:
        return "", "请先上传简历文件。"

    suffix = Path(uploaded_file.name).suffix.lower()
    try:
        if suffix == ".txt":
            return parse_txt(uploaded_file), None
        if suffix == ".pdf":
            return parse_pdf(uploaded_file), None
        if suffix == ".docx":
            return parse_docx(uploaded_file), None
        return "", "暂不支持该文件格式，请上传 PDF、DOCX 或 TXT。"
    except Exception as exc:
        return "", f"简历解析失败：{exc}"
