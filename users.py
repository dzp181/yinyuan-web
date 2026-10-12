#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""邮箱注册 / 登录 / 会话 —— 零第三方依赖，SQLite 存储

安全实现：
  · 口令：PBKDF2-HMAC-SHA256 + 每用户随机盐，定时比较（hmac.compare_digest）
  · 会话：secrets.token_urlsafe(32) 随机 token，带过期时间
  · 查询：全部走参数化 SQL，杜绝拼接注入
"""
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(ROOT, "data")
DB_PATH = os.path.join(DB_DIR, "yinyuan.db")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ROUNDS = 120000          # PBKDF2 迭代轮数
MIN_PW = 6               # 最短口令
MAX_PW = 128
SESSION_SECONDS = 30 * 24 * 3600   # 会话有效期 30 天

INIT_SQL = [
    """CREATE TABLE IF NOT EXISTS users (
         id         INTEGER PRIMARY KEY AUTOINCREMENT,
         email      TEXT UNIQUE NOT NULL,
           pw_hash  TEXT NOT NULL,
         pw_salt    TEXT NOT NULL,
         created_at REAL NOT NULL
       )""",
    """CREATE TABLE IF NOT EXISTS sessions (
         token      TEXT PRIMARY KEY,
         user_id    INTEGER NOT NULL,
         created_at REAL NOT NULL,
         expires_at REAL NOT NULL
       )""",
    """CREATE TABLE IF NOT EXISTS records (
         id         INTEGER PRIMARY KEY AUTOINCREMENT,
         user_id    INTEGER NOT NULL,
         mode       TEXT NOT NULL,
         title      TEXT NOT NULL,
         summary    TEXT,
         payload    TEXT NOT NULL,
         created_at REAL NOT NULL
       )""",
    "CREATE INDEX IF NOT EXISTS idx_sessions_user  ON sessions(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_records_user   ON records(user_id, created_at)",
]


def connect():
    """每个请求独立连接（多线程安全）"""
    need_init = not os.path.exists(DB_PATH)
    if need_init:
        os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=8)
    conn.row_factory = sqlite3.Row
    if need_init:
        for sql in INIT_SQL:
            conn.execute(sql)
        conn.commit()
    return conn


# ---------------- 口令 ----------------
def _hash(password, salt_hex):
    salt = bytes.fromhex(salt_hex)
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ROUNDS).hex()


def check_email(email):
    email = (email or "").strip().lower()
    if not email:
        raise ValueError("请填写邮箱")
    if len(email) > 120 or not EMAIL_RE.match(email):
        raise ValueError("邮箱格式不正确")
    return email


def check_password(password):
    pw = password or ""
    if len(pw) < MIN_PW:
        raise ValueError("密码至少 %d 位" % MIN_PW)
    if len(pw) > MAX_PW:
        raise ValueError("密码过长")
    return pw


# ---------------- 注册 / 登录 ----------------
def register(email, password, nickname=""):
    email = check_email(email)
    pw = check_password(password)
    conn = connect()
    try:
        row = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if row:
            raise ValueError("该邮箱已注册，请直接登录")
        salt = secrets.token_hex(16)
        cur = conn.execute(
            "INSERT INTO users(email, pw_hash, pw_salt, created_at) VALUES(?,?,?,?)",
            (email, _hash(pw, salt), salt, time.time()))
        conn.commit()
        user = {"id": cur.lastrowid, "email": email}
        return user, create_session(conn, user["id"])
    finally:
        conn.close()


def login(email, password):
    email = check_email(email)
    pw = password or ""
    conn = connect()
    try:
        row = conn.execute(
            "SELECT id, email, pw_hash, pw_salt FROM users WHERE email=?", (email,)).fetchone()
        if not row:
            raise ValueError("邮箱或密码不正确")
        calc = _hash(pw, row["pw_salt"])
        if not hmac.compare_digest(calc, row["pw_hash"]):
            raise ValueError("邮箱或密码不正确")
        user = {"id": row["id"], "email": row["email"]}
        return user, create_session(conn, user["id"])
    finally:
        conn.close()


# ---------------- 会话 ----------------
def create_session(conn, user_id):
    token = secrets.token_urlsafe(32)
    now = time.time()
    # 顺带清理该用户的过期会话
    conn.execute("DELETE FROM sessions WHERE user_id=? AND expires_at<?", (user_id, now))
    conn.execute(
        "INSERT INTO sessions(token, user_id, created_at, expires_at) VALUES(?,?,?,?)",
        (token, user_id, now, now + SESSION_SECONDS))
    conn.commit()
    return token


def user_of_token(token):
    if not token:
        return None
    conn = connect()
    try:
        row = conn.execute(
            "SELECT u.id, u.email, s.expires_at FROM sessions s "
            "JOIN users u ON u.id=s.user_id WHERE s.token=?", (token,)).fetchone()
        if not row:
            return None
        if row["expires_at"] < time.time():
            conn.execute("DELETE FROM sessions WHERE token=?", (token,))
            conn.commit()
            return None
        return {"id": row["id"], "email": row["email"]}
    finally:
        conn.close()


def logout(token):
    if not token:
        return
    conn = connect()
    try:
        conn.execute("DELETE FROM sessions WHERE token=?", (token,))
        conn.commit()
    finally:
        conn.close()


# ---------------- 测算历史 ----------------
def save_record(user_id, mode, title, summary, payload):
    conn = connect()
    try:
        conn.execute(
            "INSERT INTO records(user_id, mode, title, summary, payload, created_at) "
            "VALUES(?,?,?,?,?,?)",
            (user_id, mode, title, (summary or "")[:200], payload, time.time()))
        conn.commit()
    finally:
        conn.close()


def list_records(user_id, limit=20):
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT id, mode, title, summary, payload, created_at FROM records "
            "WHERE user_id=? ORDER BY created_at DESC LIMIT ?", (user_id, limit)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def stats():
    """简易统计（可选，用于健康检查展示用户数）"""
    conn = connect()
    try:
        n = conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
        return {"users": n}
    finally:
        conn.close()
