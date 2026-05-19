"""本地存储模块"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .config import config


class Storage:
    """本地SQLite存储"""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.get_storage_path() / "assistant.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """初始化数据库"""
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tokens INTEGER DEFAULT 0,
                    cost REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                );

                CREATE TABLE IF NOT EXISTS cost_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    prompt_tokens INTEGER DEFAULT 0,
                    completion_tokens INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    cost REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_messages_conversation
                ON messages(conversation_id);

                CREATE INDEX IF NOT EXISTS idx_cost_records_created
                ON cost_records(created_at);
            """)

    def _get_conn(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_conversation(self, title: str, provider: str, model: str) -> int:
        """创建对话"""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO conversations (title, provider, model) VALUES (?, ?, ?)",
                (title, provider, model),
            )
            return cursor.lastrowid

    def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        tokens: int = 0,
        cost: float = 0.0,
    ) -> int:
        """添加消息"""
        with self._get_conn() as conn:
            cursor = conn.execute(
                """INSERT INTO messages (conversation_id, role, content, tokens, cost)
                   VALUES (?, ?, ?, ?, ?)""",
                (conversation_id, role, content, tokens, cost),
            )
            # 更新对话时间
            conn.execute(
                "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (conversation_id,),
            )
            return cursor.lastrowid

    def get_conversation(self, conversation_id: int) -> Optional[dict[str, Any]]:
        """获取对话"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
            ).fetchone()
            if row:
                return dict(row)
        return None

    def get_conversation_messages(self, conversation_id: int) -> list[dict[str, Any]]:
        """获取对话消息"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at",
                (conversation_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_conversations(self, limit: int = 50) -> list[dict[str, Any]]:
        """列出对话"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def delete_conversation(self, conversation_id: int) -> None:
        """删除对话"""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))

    def add_cost_record(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        cost: float,
    ) -> None:
        """添加成本记录"""
        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO cost_records
                   (provider, model, prompt_tokens, completion_tokens, total_tokens, cost)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (provider, model, prompt_tokens, completion_tokens, total_tokens, cost),
            )

    def get_cost_stats(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict[str, Any]:
        """获取成本统计"""
        with self._get_conn() as conn:
            query = "SELECT * FROM cost_records"
            params = []

            if start_date or end_date:
                conditions = []
                if start_date:
                    conditions.append("created_at >= ?")
                    params.append(start_date)
                if end_date:
                    conditions.append("created_at <= ?")
                    params.append(end_date)
                query += " WHERE " + " AND ".join(conditions)

            rows = conn.execute(query, params).fetchall()

            # 汇总统计
            total_cost = 0.0
            total_tokens = 0
            by_provider: dict[str, float] = {}
            by_model: dict[str, float] = {}

            for row in rows:
                row_dict = dict(row)
                total_cost += row_dict["cost"]
                total_tokens += row_dict["total_tokens"]

                provider = row_dict["provider"]
                by_provider[provider] = by_provider.get(provider, 0) + row_dict["cost"]

                model = row_dict["model"]
                by_model[model] = by_model.get(model, 0) + row_dict["cost"]

            return {
                "total_cost": round(total_cost, 4),
                "total_tokens": total_tokens,
                "record_count": len(rows),
                "by_provider": {k: round(v, 4) for k, v in by_provider.items()},
                "by_model": {k: round(v, 4) for k, v in by_model.items()},
            }

    def get_recent_cost(self, days: int = 30) -> float:
        """获取最近N天的成本"""
        with self._get_conn() as conn:
            row = conn.execute(
                """SELECT COALESCE(SUM(cost), 0) as total
                   FROM cost_records
                   WHERE created_at >= datetime('now', ?)""",
                (f"-{days} days",),
            ).fetchone()
            return round(row["total"], 4)

    def cleanup_old_records(self, days: int = 90) -> int:
        """清理旧记录"""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "DELETE FROM cost_records WHERE created_at < datetime('now', ?)",
                (f"-{days} days",),
            )
            return cursor.rowcount


# 全局存储实例
storage = Storage()
