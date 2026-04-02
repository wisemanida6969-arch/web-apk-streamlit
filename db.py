"""
db.py — SQLite 캐시 레이어
사용자가 아무런 설정 없이 곧바로 DB 기능을 사용할 수 있도록 내장 SQLite를 사용합니다.
"""

import sqlite3
import json
import os

DB_PATH = "youtube_cache.db"


def _get_connection():
    """DB 연결 객체를 반환하며, 테이블이 없으면 생성합니다."""
    conn = sqlite3.connect(DB_PATH)
    # 테이블이 없으면 생성
    conn.execute('''
        CREATE TABLE IF NOT EXISTS youtube_cache (
            video_id TEXT PRIMARY KEY,
            concepts TEXT NOT NULL,
            timed_text TEXT NOT NULL,
            total_entries INTEGER NOT NULL,
            duration TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_usage (
            user_id TEXT,
            usage_date DATE,
            usage_count INTEGER,
            PRIMARY KEY (user_id, usage_date)
        )
    ''')
    # 추가: 글로벌 일일 예산 관리 테이블
    conn.execute('''
        CREATE TABLE IF NOT EXISTS global_budget (
            budget_date DATE PRIMARY KEY,
            total_cost_usd REAL DEFAULT 0.0
        )
    ''')
    conn.commit()
    return conn


def get_cached(video_id: str) -> dict | None:
    """
    video_id로 캐시된 분석 결과를 조회합니다.
    """
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT concepts, timed_text, total_entries, duration
            FROM youtube_cache
            WHERE video_id = ?
        ''', (video_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            concepts_str, timed_text, total_entries, duration = row
            return {
                "concepts": json.loads(concepts_str),
                "timed_text": timed_text,
                "total_entries": total_entries,
                "duration": duration,
            }
        return None
    except Exception as e:
        print(f"DB Read Error: {e}")
        return None


def save_to_cache(
    video_id: str,
    concepts: list,
    timed_text: str,
    total_entries: int,
    duration: str,
) -> bool:
    """
    분석 결과를 DB에 저장합니다. (이미 존재하면 덮어쓰기)
    """
    try:
        conn = _get_connection()
        concepts_str = json.dumps(concepts, ensure_ascii=False)
        
        # SQLite Upsert 구문 (video_id 일치 시 업데이트)
        conn.execute('''
            INSERT INTO youtube_cache (video_id, concepts, timed_text, total_entries, duration)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(video_id) DO UPDATE SET
                concepts = excluded.concepts,
                timed_text = excluded.timed_text,
                total_entries = excluded.total_entries,
                duration = excluded.duration,
                created_at = CURRENT_TIMESTAMP
        ''', (video_id, concepts_str, timed_text, total_entries, duration))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"DB Write Error: {e}")
        return False


def is_db_connected() -> bool:
    """내장 시스템이므로 무조건 True입니다."""
    return True


def get_daily_usage(user_id: str) -> int:
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT usage_count FROM user_usage 
            WHERE user_id = ? AND usage_date = DATE('now')
        ''', (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0
    except Exception as e:
        print(f"DB Read Error: {e}")
        return 0


def increment_daily_usage(user_id: str):
    try:
        conn = _get_connection()
        conn.execute('''
            INSERT INTO user_usage (user_id, usage_date, usage_count)
            VALUES (?, DATE('now'), 1)
            ON CONFLICT(user_id, usage_date) DO UPDATE SET
                usage_count = usage_count + 1
        ''', (user_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Write Error: {e}")


def get_global_daily_cost() -> float:
    """오늘 전체 사용자의 누적 API 비용($)을 반환합니다."""
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT total_cost_usd FROM global_budget 
            WHERE budget_date = DATE('now')
        ''', )
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0.0
    except Exception as e:
        print(f"Global Cost Read Error: {e}")
        return 0.0


def add_global_cost(amount: float):
    """오늘 전체 누적 API 비용에 금액을 합산합니다."""
    try:
        conn = _get_connection()
        conn.execute('''
            INSERT INTO global_budget (budget_date, total_cost_usd)
            VALUES (DATE('now'), ?)
            ON CONFLICT(budget_date) DO UPDATE SET
                total_cost_usd = total_cost_usd + excluded.total_cost_usd
        ''', (amount,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Global Cost Write Error: {e}")
