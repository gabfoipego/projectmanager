import sqlite3
import json
from datetime import datetime
from pathlib import Path
DB_PATH = Path.home() / ".projectmanager" / "data.db"
def get_conn():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn
def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            github_url TEXT,
            local_path TEXT,
            language TEXT,
            stars INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            color TEXT DEFAULT '#4a9eff',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'todo',
            priority TEXT DEFAULT 'medium',
            created_at TEXT DEFAULT (datetime('now')),
            completed_at TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    conn.commit()
    conn.close()
def get_projects():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]
def add_project(name, description="", github_url="", local_path="", language="", stars=0, color="#4a9eff"):
    conn = get_conn()
    conn.execute(
        "INSERT INTO projects (name, description, github_url, local_path, language, stars, color) VALUES (?,?,?,?,?,?,?)",
        (name, description, github_url, local_path, language, stars, color)
    )
    conn.commit()
    pid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return pid
def delete_project(pid):
    conn = get_conn()
    conn.execute("DELETE FROM projects WHERE id=?", (pid,))
    conn.commit()
    conn.close()
def update_project(pid, **kwargs):
    kwargs['updated_at'] = datetime.now().isoformat()
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [pid]
    conn = get_conn()
    conn.execute(f"UPDATE projects SET {fields} WHERE id=?", values)
    conn.commit()
    conn.close()
def get_tasks(project_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE project_id=? ORDER BY CASE priority WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, created_at",
        (project_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
def add_task(project_id, title, description="", priority="medium"):
    conn = get_conn()
    conn.execute(
        "INSERT INTO tasks (project_id, title, description, priority) VALUES (?,?,?,?)",
        (project_id, title, description, priority)
    )
    conn.commit()
    conn.close()
    update_project(project_id)
def update_task(task_id, **kwargs):
    if kwargs.get('status') == 'done' and 'completed_at' not in kwargs:
        kwargs['completed_at'] = datetime.now().isoformat()
    elif kwargs.get('status') != 'done':
        kwargs['completed_at'] = None
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [task_id]
    conn = get_conn()
    conn.execute(f"UPDATE tasks SET {fields} WHERE id=?", values)
    conn.commit()
    conn.close()
def delete_task(task_id):
    conn = get_conn()
    conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
def get_task_stats(project_id):
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM tasks WHERE project_id=?", (project_id,)).fetchone()[0]
    done = conn.execute("SELECT COUNT(*) FROM tasks WHERE project_id=? AND status='done'", (project_id,)).fetchone()[0]
    conn.close()
    return total, done
def get_notes(project_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM notes WHERE project_id=? ORDER BY created_at DESC", (project_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
def add_note(project_id, content):
    conn = get_conn()
    conn.execute("INSERT INTO notes (project_id, content) VALUES (?,?)", (project_id, content))
    conn.commit()
    conn.close()
def delete_note(note_id):
    conn = get_conn()
    conn.execute("DELETE FROM notes WHERE id=?", (note_id,))
    conn.commit()
    conn.close()
def get_chat_history(project_id, limit=50):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM chat_history WHERE project_id=? ORDER BY created_at DESC LIMIT ?",
        (project_id, limit)
    ).fetchall()
    conn.close()
    return list(reversed([dict(r) for r in rows]))
def add_chat_message(project_id, role, content):
    conn = get_conn()
    conn.execute(
        "INSERT INTO chat_history (project_id, role, content) VALUES (?,?,?)",
        (project_id, role, content)
    )
    conn.commit()
    conn.close()
def clear_chat_history(project_id):
    conn = get_conn()
    conn.execute("DELETE FROM chat_history WHERE project_id=?", (project_id,))
    conn.commit()
    conn.close()
def get_setting(key, default=None):
    conn = get_conn()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row[0] if row else default
def set_setting(key, value):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, str(value)))
    conn.commit()
    conn.close()
