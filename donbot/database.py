"""
Couche d'accès aux données (SQLite).
Gère : dons, objectif de collecte, classement des donateurs.
"""
import sqlite3
import time
from contextlib import contextmanager
from config import DB_PATH, DEFAULT_GOAL_AMOUNT


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS donations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER NOT NULL,
                username TEXT,
                amount REAL NOT NULL,
                currency TEXT NOT NULL,
                method TEXT NOT NULL,          -- mtn / airtel / moov / wave / paypal / crypto
                provider_ref TEXT,             -- id de transaction côté fournisseur
                status TEXT NOT NULL DEFAULT 'pending',  -- pending / paid / failed
                created_at INTEGER NOT NULL,
                paid_at INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS goal (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                target_amount REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'XAF'
            )
        """)
        # initialiser l'objectif s'il n'existe pas encore
        cur = conn.execute("SELECT COUNT(*) as c FROM goal")
        if cur.fetchone()["c"] == 0:
            conn.execute(
                "INSERT INTO goal (id, target_amount, currency) VALUES (1, ?, 'XAF')",
                (DEFAULT_GOAL_AMOUNT,),
            )


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def create_pending_donation(telegram_user_id, username, amount, currency, method):
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO donations
               (telegram_user_id, username, amount, currency, method, status, created_at)
               VALUES (?, ?, ?, ?, ?, 'pending', ?)""",
            (telegram_user_id, username, amount, currency, method, int(time.time())),
        )
        return cur.lastrowid


def set_provider_ref(donation_id, provider_ref):
    with get_conn() as conn:
        conn.execute(
            "UPDATE donations SET provider_ref = ? WHERE id = ?",
            (provider_ref, donation_id),
        )


def mark_paid(donation_id=None, provider_ref=None):
    """Marque un don comme payé, par id interne OU par référence fournisseur."""
    with get_conn() as conn:
        if donation_id is not None:
            conn.execute(
                "UPDATE donations SET status = 'paid', paid_at = ? WHERE id = ?",
                (int(time.time()), donation_id),
            )
            row = conn.execute("SELECT * FROM donations WHERE id = ?", (donation_id,)).fetchone()
        else:
            conn.execute(
                "UPDATE donations SET status = 'paid', paid_at = ? WHERE provider_ref = ?",
                (int(time.time()), provider_ref),
            )
            row = conn.execute("SELECT * FROM donations WHERE provider_ref = ?", (provider_ref,)).fetchone()
        return dict(row) if row else None


def mark_failed(donation_id=None, provider_ref=None):
    with get_conn() as conn:
        if donation_id is not None:
            conn.execute("UPDATE donations SET status = 'failed' WHERE id = ?", (donation_id,))
        else:
            conn.execute("UPDATE donations SET status = 'failed' WHERE provider_ref = ?", (provider_ref,))


def get_donation(donation_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM donations WHERE id = ?", (donation_id,)).fetchone()
        return dict(row) if row else None


def get_total_paid():
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) as total FROM donations WHERE status = 'paid'"
        ).fetchone()
        return row["total"]


def get_goal():
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM goal WHERE id = 1").fetchone()
        return dict(row) if row else None


def set_goal(target_amount):
    with get_conn() as conn:
        conn.execute("UPDATE goal SET target_amount = ? WHERE id = 1", (target_amount,))


def get_leaderboard(limit=10):
    """Classement des donateurs par somme totale payée, plus gros donateur en premier."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT telegram_user_id, username, SUM(amount) as total
               FROM donations
               WHERE status = 'paid'
               GROUP BY telegram_user_id
               ORDER BY total DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
