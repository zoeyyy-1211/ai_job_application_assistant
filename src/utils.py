from pathlib import Path


def save_uploaded_file(uploaded_file, upload_dir: Path) -> Path | None:
    """保存上传文件到本地 uploads 目录，便于后续追踪。"""
    if uploaded_file is None:
        return None
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / uploaded_file.name
    file_path.write_bytes(uploaded_file.getbuffer())
    return file_path
