import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import DB_PATH, ensure_directories


STATUSES = ["待投递", "已投递", "笔试", "一面", "二面", "HR面", "Offer", "已拒绝", "已挂", "暂缓"]
NEXT_ACTIONS = ["修改简历", "准备笔试", "准备一面", "等待反馈", "跟进 HR", "暂无"]


def get_connection() -> sqlite3.Connection:
    """创建 SQLite 连接，并让查询结果支持按字段名访问。"""
    ensure_directories()
    conn = sqlite3.connect(Path(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """初始化投递记录表。"""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                position TEXT NOT NULL,
                position_type TEXT,
                platform TEXT,
                city TEXT,
                jd_text TEXT,
                resume_text TEXT,
                match_score INTEGER DEFAULT 0,
                status TEXT DEFAULT '待投递',
                interview_stage TEXT,
                notes TEXT,
                application_url TEXT,
                next_action TEXT,
                interview_notes TEXT,
                analysis_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        existing_columns = {row["name"] for row in conn.execute("PRAGMA table_info(applications)").fetchall()}
        migrations = {
            "application_url": "ALTER TABLE applications ADD COLUMN application_url TEXT",
            "next_action": "ALTER TABLE applications ADD COLUMN next_action TEXT",
            "interview_notes": "ALTER TABLE applications ADD COLUMN interview_notes TEXT",
        }
        for column, statement in migrations.items():
            if column not in existing_columns:
                conn.execute(statement)
        conn.commit()


def create_application(data: dict[str, Any]) -> int:
    """新增一条投递记录，返回记录 ID。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "company": data.get("company", "").strip(),
        "position": data.get("position", "").strip(),
        "position_type": data.get("position_type", ""),
        "platform": data.get("platform", ""),
        "city": data.get("city", ""),
        "jd_text": data.get("jd_text", ""),
        "resume_text": data.get("resume_text", ""),
        "match_score": int(data.get("match_score", 0) or 0),
        "status": data.get("status", "待投递"),
        "interview_stage": data.get("interview_stage", ""),
        "notes": data.get("notes", ""),
        "application_url": data.get("application_url", ""),
        "next_action": data.get("next_action", "修改简历"),
        "interview_notes": data.get("interview_notes", ""),
        "analysis_json": data.get("analysis_json", ""),
        "created_at": now,
        "updated_at": now,
    }
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO applications (
                company, position, position_type, platform, city, jd_text, resume_text,
                match_score, status, interview_stage, notes, application_url, next_action,
                interview_notes, analysis_json, created_at, updated_at
            ) VALUES (
                :company, :position, :position_type, :platform, :city, :jd_text, :resume_text,
                :match_score, :status, :interview_stage, :notes, :application_url, :next_action,
                :interview_notes, :analysis_json, :created_at, :updated_at
            )
            """,
            payload,
        )
        conn.commit()
        return int(cursor.lastrowid)


def get_applications() -> pd.DataFrame:
    """读取所有投递记录，返回 DataFrame，便于页面展示和图表分析。"""
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM applications ORDER BY created_at DESC", conn)


def update_application(
    application_id: int,
    status: str,
    interview_stage: str,
    notes: str,
    application_url: str = "",
    next_action: str = "",
    interview_notes: str = "",
) -> None:
    """更新投递状态、面试进展、备注、链接和下一步行动。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE applications
            SET status = ?, interview_stage = ?, notes = ?, application_url = ?,
                next_action = ?, interview_notes = ?, updated_at = ?
            WHERE id = ?
            """,
            (status, interview_stage, notes, application_url, next_action, interview_notes, now, application_id),
        )
        conn.commit()


def delete_application(application_id: int) -> None:
    """删除指定投递记录。"""
    with get_connection() as conn:
        conn.execute("DELETE FROM applications WHERE id = ?", (application_id,))
        conn.commit()
