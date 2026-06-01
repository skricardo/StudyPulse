"""
StudyPulse — Database Layer
SQLite storage for topics, sessions, planner slots, reminders, and user stats.
"""
import sqlite3
import os
from datetime import datetime, date

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
_DEFAULT_DB = os.path.join(BASE_DIR, "studypulse.db")
_current_db = [_DEFAULT_DB]
def set_user_db(username: str):
    """
    Define o banco de dados para o usuário logado.
    Só migra o banco legado se ele realmente contiver este usuário.
    """
    user_db = os.path.join(BASE_DIR, f"studypulse_{username.strip().lower()}.db")
    if not os.path.exists(user_db) and os.path.exists(_DEFAULT_DB):
        # Verificar se o banco legado pertence a este usuário antes de migrar
        try:
            import sqlite3 as _sq
            _conn = _sq.connect(_DEFAULT_DB)
            row = _conn.execute(
                "SELECT username FROM users WHERE username = ? COLLATE NOCASE LIMIT 1",
                (username,)
            ).fetchone()
            _conn.close()
            if row:
                os.rename(_DEFAULT_DB, user_db)
        except Exception:
            pass
    _current_db[0] = user_db
def get_connection() -> sqlite3.Connection:
    """Get a database connection with row_factory enabled."""
    conn = sqlite3.connect(_current_db[0])
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            priority INTEGER NOT NULL DEFAULT 2 CHECK (priority IN (1, 2, 3)),
            color TEXT NOT NULL DEFAULT '#7c3aed',
            icon TEXT NOT NULL DEFAULT 'book',
            weekly_target_minutes INTEGER NOT NULL DEFAULT 0,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            archived INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS planner_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
            planned_minutes INTEGER NOT NULL DEFAULT 60,
            week_start_date TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0,
            sort_order INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            duration_minutes REAL NOT NULL DEFAULT 0,
            xp_earned INTEGER NOT NULL DEFAULT 0,
            session_type TEXT NOT NULL DEFAULT 'stopwatch',
            notes TEXT,
            FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'general',
            due_date TEXT,
            completed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            badge_id TEXT NOT NULL UNIQUE,
            unlocked_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS user_stats (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            total_xp INTEGER NOT NULL DEFAULT 0,
            current_streak INTEGER NOT NULL DEFAULT 0,
            best_streak INTEGER NOT NULL DEFAULT 0,
            streak_freeze_available INTEGER NOT NULL DEFAULT 0,
            last_study_date TEXT
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

    """)

    # Ensure user_stats has exactly 1 row
    cursor.execute("SELECT COUNT(*) FROM user_stats")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO user_stats (id, total_xp, current_streak, best_streak) "
            "VALUES (1, 0, 0, 0)"
        )
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)
    # Inserir categorias padrão se tabela estiver vazia
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        for cat in ["Aula", "Livros", "Exercícios", "Curso", "Geral"]:
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (cat,))
    
    # Migração: adicionar coluna category em topics
    try:
        cursor.execute("ALTER TABLE topics ADD COLUMN category TEXT NOT NULL DEFAULT 'Geral'")
    except Exception:
        pass

    # Migração: adicionar coluna sort_order em categories
    try:
        cursor.execute("ALTER TABLE categories ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0")
        rows = cursor.execute("SELECT id FROM categories ORDER BY name").fetchall()
        for i, row in enumerate(rows):
            cursor.execute("UPDATE categories SET sort_order = ? WHERE id = ?", (i, row["id"]))
    except Exception:
        pass
    # Migração: adicionar pergunta e resposta secreta em users
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN security_question TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN security_answer_hash TEXT")
    except Exception:
        pass
    conn.commit()
    conn.close()


def get_categories():
    """Retorna todas as categorias."""
    conn = get_connection()
    rows = conn.execute("SELECT name FROM categories ORDER BY sort_order, name").fetchall()
    conn.close()
    return [r["name"] for r in rows]


def add_category(name: str):
    """Adiciona uma nova categoria."""
    conn = get_connection()
    conn.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()

def swap_category_order(name_a: str, name_b: str):
    """Troca a ordem de duas categorias."""
    conn = get_connection()
    row_a = conn.execute("SELECT sort_order FROM categories WHERE name = ?", (name_a,)).fetchone()
    row_b = conn.execute("SELECT sort_order FROM categories WHERE name = ?", (name_b,)).fetchone()
    if row_a and row_b:
        conn.execute("UPDATE categories SET sort_order = ? WHERE name = ?", (row_b["sort_order"], name_a))
        conn.execute("UPDATE categories SET sort_order = ? WHERE name = ?", (row_a["sort_order"], name_b))
        conn.commit()
    conn.close()

def delete_category(name: str):
    """Deleta uma categoria e move temas para 'Geral'."""
    conn = get_connection()
    conn.execute("UPDATE topics SET category = 'Geral' WHERE category = ?", (name,))
    conn.execute("DELETE FROM categories WHERE name = ?", (name,))
    conn.commit()
    conn.close()


def get_planner_slot_by_id(slot_id: int):
    """Get a single planner slot by its ID."""
    conn = get_connection()
    row = conn.execute(
        "SELECT ps.*, t.priority, t.name as topic_name "
        "FROM planner_slots ps "
        "JOIN topics t ON ps.topic_id = t.id "
        "WHERE ps.id = ?",
        (slot_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ─── Topics ───────────────────────────────────────────────────────

def get_topics(include_archived=False):
    """Return all topics as list of dicts."""
    conn = get_connection()
    query = "SELECT * FROM topics"
    if not include_archived:
        query += " WHERE archived = 0"
    query += " ORDER BY sort_order, priority DESC, name"
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_topic(name: str, priority: int, color: str, icon: str, weekly_target: int, category: str = "Geral") -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO topics (name, priority, color, icon, weekly_target_minutes, category) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (name, priority, color, icon, weekly_target, category),
    )
    topic_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return topic_id


def update_topic(topic_id: int, **kwargs):
    """Update a topic's fields."""
    allowed = {"name", "priority", "color", "icon", "weekly_target_minutes", "sort_order", "archived", "category"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [topic_id]
    conn = get_connection()
    conn.execute(f"UPDATE topics SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()


def delete_topic(topic_id: int):
    """Delete a topic and all its related data."""
    conn = get_connection()
    conn.execute("DELETE FROM topics WHERE id = ?", (topic_id,))
    conn.commit()
    conn.close()


# ─── Planner Slots ────────────────────────────────────────────────

def get_week_start(ref_date: date | None = None) -> str:
    """Get the Monday of the week for the given date as YYYY-MM-DD string."""
    d = ref_date or date.today()
    monday = d - __import__("datetime").timedelta(days=d.weekday())
    return monday.isoformat()


def get_planner_slots(week_start: str):
    """Get all planner slots for a given week."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT ps.*, t.name as topic_name, t.priority, t.color, t.icon "
        "FROM planner_slots ps "
        "JOIN topics t ON ps.topic_id = t.id "
        "WHERE ps.week_start_date = ? "
        "ORDER BY ps.day_of_week, ps.completed DESC, ps.sort_order, t.priority DESC",
        (week_start,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_planner_slot(topic_id: int, day_of_week: int, planned_minutes: int, week_start: str) -> int:
    """Add a topic slot to a specific day of the week."""
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO planner_slots (topic_id, day_of_week, planned_minutes, week_start_date) "
        "VALUES (?, ?, ?, ?)",
        (topic_id, day_of_week, planned_minutes, week_start),
    )
    slot_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return slot_id


def update_planner_slot(slot_id: int, **kwargs):
    """Update a planner slot."""
    allowed = {"planned_minutes", "completed", "sort_order"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [slot_id]
    conn = get_connection()
    conn.execute(f"UPDATE planner_slots SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()


def update_planner_slots_order(updates: list[dict]):
    """Update day_of_week and sort_order for multiple slots.
    updates is a list of dicts: [{'id': 1, 'day_of_week': 2, 'sort_order': 0}, ...]
    """
    conn = get_connection()
    for u in updates:
        conn.execute(
            "UPDATE planner_slots SET day_of_week = ?, sort_order = ? WHERE id = ?",
            (u['day_of_week'], u['sort_order'], u['id'])
        )
    conn.commit()
    conn.close()


def delete_planner_slot(slot_id: int):
    """Remove a planner slot."""
    conn = get_connection()
    conn.execute("DELETE FROM planner_slots WHERE id = ?", (slot_id,))
    conn.commit()
    conn.close()


# ─── Study Sessions ──────────────────────────────────────────────

def add_session(topic_id: int, duration_minutes: float, xp_earned: int,
                session_type: str = "stopwatch", notes: str = "",
                session_date: str | None = None) -> int:
    """Record a completed study session."""
    now = datetime.now()
    if session_date:
        dt_str = f"{session_date}T{now.strftime('%H:%M:%S')}"
    else:
        dt_str = now.isoformat()
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO study_sessions (topic_id, start_time, end_time, duration_minutes, "
        "xp_earned, session_type, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (topic_id, dt_str, dt_str, duration_minutes, xp_earned, session_type, notes),
    )
    session_id = cursor.lastrowid

    # Update user total XP
    conn.execute("UPDATE user_stats SET total_xp = total_xp + ? WHERE id = 1", (xp_earned,))

    # Update streak
    _update_streak(conn)

    conn.commit()
    conn.close()
    return session_id

def delete_session(session_id: int) -> int:
    """Apaga uma sessão e desconta o XP. Retorna o XP descontado."""
    conn = get_connection()
    row = conn.execute(
        "SELECT xp_earned FROM study_sessions WHERE id = ?", (session_id,)
    ).fetchone()
    xp = 0
    if row:
        xp = row["xp_earned"]
        conn.execute("DELETE FROM study_sessions WHERE id = ?", (session_id,))
        conn.execute("UPDATE user_stats SET total_xp = MAX(0, total_xp - ?) WHERE id = 1", (xp,))
        conn.commit()
    conn.close()
    return xp

def undo_planner_quick_log(topic_id: int, duration_minutes: float, session_date: str | None = None) -> int:
    """Finds the quick log session for this topic/date and deletes it, undoing the XP."""
    conn = get_connection()
    if session_date:
        row = conn.execute(
            "SELECT id, xp_earned FROM study_sessions "
            "WHERE session_type = 'planner_quick_log' AND topic_id = ? "
            "AND date(start_time) = ? "
            "ORDER BY id DESC LIMIT 1",
            (topic_id, session_date)
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT id, xp_earned FROM study_sessions "
            "WHERE session_type = 'planner_quick_log' AND topic_id = ? "
            "ORDER BY id DESC LIMIT 1",
            (topic_id,)
        ).fetchone()
    xp_deducted = 0
    if row:
        session_id = row["id"]
        xp_deducted = row["xp_earned"]
        conn.execute("DELETE FROM study_sessions WHERE id = ?", (session_id,))
        conn.execute("UPDATE user_stats SET total_xp = MAX(0, total_xp - ?) WHERE id = 1", (xp_deducted,))
        conn.commit()
    conn.close()
    return xp_deducted


def get_sessions(topic_id: int | None = None, days: int = 30):
    """Get study sessions, optionally filtered by topic, for the last N days."""
    conn = get_connection()
    query = (
        "SELECT ss.*, t.name as topic_name, t.priority, t.color "
        "FROM study_sessions ss "
        "JOIN topics t ON ss.topic_id = t.id "
        "WHERE ss.start_time >= date('now', 'localtime', ?)"
    )
    params: list = [f"-{days} days"]
    if topic_id:
        query += " AND ss.topic_id = ?"
        params.append(topic_id)
    query += " ORDER BY ss.start_time DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_daily_minutes(days: int = 365):
    """Get total study minutes per day for heatmap."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT date(start_time) as study_date, SUM(duration_minutes) as total_min "
        "FROM study_sessions "
        "WHERE start_time >= date('now', 'localtime', ?) "
        "GROUP BY date(start_time) "
        "ORDER BY study_date",
        (f"-{days} days",),
    ).fetchall()
    conn.close()
    return {row["study_date"]: row["total_min"] for row in rows}

def get_topic_totals():
    """Get total minutes studied per topic (all time)."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT t.id, t.name, t.priority, t.color, "
        "COALESCE(SUM(ss.duration_minutes), 0) as total_minutes "
        "FROM topics t "
        "LEFT JOIN study_sessions ss ON t.id = ss.topic_id "
        "WHERE t.archived = 0 "
        "GROUP BY t.id HAVING total_minutes > 0 ORDER BY total_minutes DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_topic_totals_monthly():
    """Get total minutes studied per topic for the current month."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT t.id, t.name, t.color, "
        "COALESCE(SUM(ss.duration_minutes), 0) as total_minutes "
        "FROM topics t "
        "LEFT JOIN study_sessions ss ON t.id = ss.topic_id "
        "   AND strftime('%Y-%m', ss.start_time) = strftime('%Y-%m', 'now', 'localtime') "
        "WHERE t.archived = 0 "
        "GROUP BY t.id HAVING total_minutes > 0 ORDER BY total_minutes DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

    
def get_topic_totals_weekly(week_start: str):
    """Get total minutes studied per topic for a specific week."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT t.id, t.name, t.color, "
        "COALESCE(SUM(ss.duration_minutes), 0) as total_minutes "
        "FROM topics t "
        "LEFT JOIN study_sessions ss ON t.id = ss.topic_id "
        "   AND date(ss.start_time) >= ? AND date(ss.start_time) < date(?, '+7 days') "
        "WHERE t.archived = 0 "
        "GROUP BY t.id HAVING total_minutes > 0 ORDER BY total_minutes DESC",
        (week_start, week_start)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_weekly_minutes(week_start: str):
    """Get minutes studied per day for a specific week."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT date(start_time) as study_date, SUM(duration_minutes) as total_min "
        "FROM study_sessions "
        "WHERE date(start_time) >= ? AND date(start_time) < date(?, '+7 days') "
        "GROUP BY date(start_time) ORDER BY study_date",
        (week_start, week_start),
    ).fetchall()
    conn.close()
    return {row["study_date"]: row["total_min"] for row in rows}

def get_sessions_for_date(target_date: str):
    """Get all study sessions for a specific date (YYYY-MM-DD)."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT ss.*, t.name as topic_name, t.priority, t.color "
        "FROM study_sessions ss "
        "JOIN topics t ON ss.topic_id = t.id "
        "WHERE date(ss.start_time) = ? "
        "ORDER BY ss.start_time DESC",
        (target_date,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_day_planner_slots(day_of_week: int, week_start: str):
    """Get planner slots for a specific day of the week."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT ps.*, t.name as topic_name, t.priority, t.color, t.icon "
        "FROM planner_slots ps "
        "JOIN topics t ON ps.topic_id = t.id "
        "WHERE ps.day_of_week = ? AND ps.week_start_date = ? "
        "ORDER BY ps.completed DESC, ps.sort_order, t.priority DESC",
        (day_of_week, week_start),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_completed_count_for_day(day_of_week: int, week_start: str, slot_id: int) -> int:
    """Conta quantos slots concluídos existem num dia, excluindo o slot informado."""
    conn = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM planner_slots "
        "WHERE day_of_week = ? AND week_start_date = ? AND completed = 1 AND id != ?",
        (day_of_week, week_start, slot_id)
    ).fetchone()[0]
    conn.close()
    return count



# ─── Reminders ────────────────────────────────────────────────────

def get_reminders(show_completed=False):
    """Get all reminders, ordered by due date then creation."""
    conn = get_connection()
    query = "SELECT * FROM reminders"
    if not show_completed:
        query += " WHERE completed = 0"
    query += " ORDER BY completed ASC, due_date ASC NULLS LAST, created_at DESC"
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_reminder(text: str, category: str = "general", due_date: str | None = None) -> int:
    """Add a new reminder."""
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO reminders (text, category, due_date) VALUES (?, ?, ?)",
        (text, category, due_date),
    )
    reminder_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return reminder_id


def toggle_reminder(reminder_id: int):
    """Toggle a reminder's completed status."""
    conn = get_connection()
    conn.execute(
        "UPDATE reminders SET completed = CASE WHEN completed = 0 THEN 1 ELSE 0 END "
        "WHERE id = ?",
        (reminder_id,),
    )
    conn.commit()
    conn.close()


def delete_reminder(reminder_id: int):
    """Delete a reminder."""
    conn = get_connection()
    conn.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()


# ─── Achievements ─────────────────────────────────────────────────

def get_unlocked_badges():
    """Get all unlocked badge IDs."""
    conn = get_connection()
    rows = conn.execute("SELECT badge_id, unlocked_at FROM achievements").fetchall()
    conn.close()
    return {row["badge_id"]: row["unlocked_at"] for row in rows}


def unlock_badge(badge_id: str) -> bool:
    """Unlock a badge. Returns True if newly unlocked, False if already had it."""
    conn = get_connection()
    try:
        conn.execute("INSERT INTO achievements (badge_id) VALUES (?)", (badge_id,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


# ─── User Stats ───────────────────────────────────────────────────

def get_user_stats() -> dict:
    """Get the single user stats row."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM user_stats WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else {"total_xp": 0, "current_streak": 0, "best_streak": 0}


def _update_streak(conn: sqlite3.Connection):
    """Update streak based on today's date (called inside a transaction)."""
    today = date.today().isoformat()
    yesterday = (date.today() - __import__("datetime").timedelta(days=1)).isoformat()

    stats = conn.execute("SELECT * FROM user_stats WHERE id = 1").fetchone()
    last_date = stats["last_study_date"]

    if last_date == today:
        return  # Already studied today

    if last_date == yesterday:
        new_streak = stats["current_streak"] + 1
    else:
        new_streak = 1

    best = max(stats["best_streak"], new_streak)
    conn.execute(
        "UPDATE user_stats SET current_streak = ?, best_streak = ?, last_study_date = ? "
        "WHERE id = 1",
        (new_streak, best, today),
    )

# ─── Users & Auth ────────────────────────────────────────────────
def create_user(username: str, password_hash: str, display_name: str,
                security_question: str = "", security_answer_hash: str = "") -> int | None:
    """Cria um novo usuário. Retorna o id ou None se username já existe."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO users (username, password_hash, display_name, security_question, security_answer_hash) "
            "VALUES (?, ?, ?, ?, ?)",
            (username, password_hash, display_name, security_question, security_answer_hash),
        )
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None
def get_user_by_username(username: str) -> dict | None:
    """Busca um usuário pelo username (case-insensitive)."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ? COLLATE NOCASE", (username,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None
def create_session(user_id: int, token: str, expires_at: str) -> int:
    """Cria uma sessão persistente para o usuário."""
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
        (user_id, token, expires_at),
    )
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id
def get_session_by_token(token: str) -> dict | None:
    """Busca uma sessão pelo token, retorna None se expirada ou inexistente."""
    conn = get_connection()
    row = conn.execute(
        "SELECT s.*, u.username, u.display_name "
        "FROM sessions s JOIN users u ON s.user_id = u.id "
        "WHERE s.token = ? AND s.expires_at > datetime('now', 'localtime')",
        (token,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None
def delete_session_by_token(token: str):
    """Remove uma sessão (logout)."""
    conn = get_connection()
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()

def get_security_question(username: str) -> str | None:
    """Retorna a pergunta secreta do usuário, ou None se não encontrado."""
    conn = get_connection()
    row = conn.execute(
        "SELECT security_question FROM users WHERE username = ? COLLATE NOCASE",
        (username,)
    ).fetchone()
    conn.close()
    if row and row["security_question"]:
        return row["security_question"]
    return None
def update_user_password(user_id: int, new_password_hash: str):
    """Redefine a senha do usuário."""
    conn = get_connection()
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (new_password_hash, user_id)
    )
    conn.commit()
    conn.close()

def update_user_security_question(user_id: int, question: str, answer_hash: str):
    """Salva ou atualiza a pergunta e resposta secreta do usuário."""
    conn = get_connection()
    conn.execute(
        "UPDATE users SET security_question = ?, security_answer_hash = ? WHERE id = ?",
        (question, answer_hash, user_id)
    )
    conn.commit()
    conn.close()