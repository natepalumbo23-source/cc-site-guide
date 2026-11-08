"""Credit Cowboy Guide — clickable prototype (mock payments)."""
from __future__ import annotations

import json
import os
import sqlite3
import secrets
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / "data" / "guide.db"

app = Flask(__name__)
app.secret_key = os.environ.get("CC_SECRET") or os.environ.get("SECRET_KEY") or "cc-guide-dev-secret-change-me"

NAVY = "#1F2244"

SECTIONS = {
    "qas": {
        "title": "Q&As",
        "blurb": "Interview questions and how to think through them.",
        "placeholder": [
            "What Makes a Good Credit (the 5 things).",
            "Credit vs. IB on day 1.",
            "Storytelling when you broke in from a non-target.",
        ],
    },
    "paper-lbo": {
        "title": "Paper LBO",
        "blurb": "Practice template plus a step-by-step walkthrough.",
        "placeholder": [
            "Downloadable Paper LBO template (Excel).",
            "Step-by-step walkthrough of the template.",
            "Common mistakes and how interviewers catch them.",
        ],
    },
    "model-tests": {
        "title": "Model Tests",
        "blurb": "Timed drills that mirror what desks actually send.",
        "placeholder": [
            "Credit memo outline drill.",
            "Simple returns / leverage check.",
            "Industry case prompts (no sample answers yet).",
        ],
    },
    "resume-builder": {
        "title": "Resume Builder",
        "blurb": "Structure built from resumes that cleared elite screens.",
        "placeholder": [
            "Resume structure checklist.",
            "Bullet rewrite patterns (anonymized).",
            "Before / after examples (content TBD from Nate).",
        ],
    },
}


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS funnel_leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            first_name TEXT,
            email TEXT,
            phone TEXT,
            where_now TEXT,
            school_or_title TEXT,
            hear_about TEXT,
            answers_json TEXT,
            created_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            first_name TEXT,
            lead_id INTEGER,
            paid_mock INTEGER DEFAULT 0,
            created_at TEXT
        );
        """
    )
    db.commit()
    db.close()


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("account_id"):
            return redirect(url_for("paywall"))
        return fn(*args, **kwargs)

    return wrapper


@app.route("/")
def index():
    if session.get("account_id"):
        return redirect(url_for("home"))
    return render_template("funnel.html")


@app.route("/api/funnel", methods=["POST"])
def api_funnel():
    data = request.get_json(force=True) or {}
    sid = session.get("funnel_sid") or secrets.token_hex(16)
    session["funnel_sid"] = sid
    now = datetime.utcnow().isoformat() + "Z"

    def _clean(v):
        if v is None:
            return None
        v = str(v).strip()
        return v or None

    fields = {
        "first_name": _clean(data.get("first_name")),
        "email": _clean(data.get("email")),
        "phone": _clean(data.get("phone")),
        "where_now": _clean(data.get("where_now")),
        "school_or_title": _clean(data.get("school_or_title")),
        "hear_about": _clean(data.get("hear_about")),
    }
    answers = data.get("answers") or fields

    db = get_db()
    row = db.execute(
        "SELECT id FROM funnel_leads WHERE session_id = ?", (sid,)
    ).fetchone()
    if row:
        db.execute(
            """
            UPDATE funnel_leads SET
              first_name = COALESCE(?, first_name),
              email = COALESCE(?, email),
              phone = COALESCE(?, phone),
              where_now = COALESCE(?, where_now),
              school_or_title = COALESCE(?, school_or_title),
              hear_about = COALESCE(?, hear_about),
              answers_json = ?,
              updated_at = ?
            WHERE session_id = ?
            """,
            (
                fields["first_name"],
                fields["email"],
                fields["phone"],
                fields["where_now"],
                fields["school_or_title"],
                fields["hear_about"],
                json.dumps(answers),
                now,
                sid,
            ),
        )
    else:
        db.execute(
            """
            INSERT INTO funnel_leads
              (session_id, first_name, email, phone, where_now,
               school_or_title, hear_about, answers_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sid,
                fields["first_name"],
                fields["email"],
                fields["phone"],
                fields["where_now"],
                fields["school_or_title"],
                fields["hear_about"],
                json.dumps(answers),
                now,
                now,
            ),
        )
    db.commit()

    if fields.get("email"):
        session["lead_email"] = fields["email"]
    if fields.get("first_name"):
        session["lead_first_name"] = fields["first_name"]

    return jsonify({"ok": True, "session_id": sid})


@app.route("/paywall")
def paywall():
    if session.get("account_id"):
        return redirect(url_for("home"))
    return render_template(
        "paywall.html",
        prefill_email=session.get("lead_email", ""),
        first_name=session.get("lead_first_name", ""),
    )


@app.route("/api/account", methods=["POST"])
def api_account():
    """Create account + mock payment. Stripe Checkout hook lives here later."""
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    mock_pay = bool(data.get("mock_pay", True))

    if not email or "@" not in email:
        return jsonify({"ok": False, "error": "Enter a valid email."}), 400
    if len(password) < 6:
        return jsonify({"ok": False, "error": "Password needs at least 6 characters."}), 400

    # Placeholder for Stripe Checkout Session creation:
    # stripe.checkout.Session.create(... success_url=..., cancel_url=...)
    # For now we only mark paid_mock=1 when the test button is used.

    now = datetime.utcnow().isoformat() + "Z"
    # Intentionally trivial hash for prototype only (NOT production).
    password_hash = "proto:" + secrets.token_hex(8) + ":" + str(abs(hash(password + email)))

    db = get_db()
    lead = None
    sid = session.get("funnel_sid")
    if sid:
        lead = db.execute(
            "SELECT * FROM funnel_leads WHERE session_id = ?", (sid,)
        ).fetchone()

    first_name = (lead["first_name"] if lead else None) or session.get(
        "lead_first_name"
    )

    existing = db.execute(
        "SELECT id FROM accounts WHERE email = ?", (email,)
    ).fetchone()
    if existing:
        db.execute(
            "UPDATE accounts SET password_hash = ?, paid_mock = ?, first_name = COALESCE(?, first_name) WHERE id = ?",
            (password_hash, 1 if mock_pay else 0, first_name, existing["id"]),
        )
        account_id = existing["id"]
    else:
        cur = db.execute(
            """
            INSERT INTO accounts (email, password_hash, first_name, lead_id, paid_mock, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                email,
                password_hash,
                first_name,
                lead["id"] if lead else None,
                1 if mock_pay else 0,
                now,
            ),
        )
        account_id = cur.lastrowid
    db.commit()

    session["account_id"] = account_id
    session["account_email"] = email
    session["account_name"] = first_name or ""
    return jsonify({"ok": True, "redirect": url_for("home")})


@app.route("/home")
@login_required
def home():
    return render_template(
        "home.html",
        name=session.get("account_name") or "",
        sections=SECTIONS,
    )


@app.route("/section/<slug>")
@login_required
def section(slug: str):
    info = SECTIONS.get(slug)
    if not info:
        return redirect(url_for("home"))
    return render_template("section.html", slug=slug, section=info)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/api/leads")
def api_leads():
    """Dev helper only. Disabled unless LEADS_TOKEN is set and matches ?token=."""
    expected = os.environ.get("LEADS_TOKEN", "").strip()
    if not expected or request.args.get("token") != expected:
        return jsonify({"error": "Not found"}), 404
    rows = get_db().execute(
        "SELECT id, first_name, email, phone, where_now, school_or_title, hear_about, created_at FROM funnel_leads ORDER BY id DESC"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


# Production entry: gunicorn app:app
init_db()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5055"))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
