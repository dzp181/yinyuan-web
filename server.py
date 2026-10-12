#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""月老姻缘测算网站 —— 零第三方依赖 HTTP 服务

静态托管 static/ 并暴露 JSON API：
  POST /api/zodiac   生肖配对        {a_year,b_year} 或 {a_zodiac,b_zodiac}
  POST /api/hehun    八字合婚        {a_date,a_hour,a_minute,a_sex, b_date,b_hour,b_minute,b_sex}
  POST /api/qiuqian  求签问姻缘      {name, question}
  POST /api/taohua   桃花运势        {year, status}
  POST /api/ziwei    紫微夫妻宫      {date, hour, minute, sex}
  POST /api/hongxian 红线测算        {date, hour, minute, sex, expect}

用户系统（邮箱注册登录，SQLite 持久化）：
  POST /api/auth/register   {email, password}          -> {user, token}
  POST /api/auth/login      {email, password}          -> {user, token}
  POST /api/auth/logout     需 Authorization: Bearer   -> {ok}
  GET  /api/auth/me         需 Authorization: Bearer   -> {user}
  POST /api/records         需登录 {mode,title,summary,payload}  保存测算记录
  GET  /api/records         需登录                               我的测算历史

兼容 Python 3.6+（含 ThreadingHTTPServer 缺失的低版本）
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse

try:  # Python 3.7+
    from http.server import ThreadingHTTPServer
except ImportError:  # Python 3.6：ThreadingMixIn 在 socketserver 里（http.server 到 3.7 才转出）
    from http.server import HTTPServer
    from socketserver import ThreadingMixIn

    class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from engine import zodiac, hehun, qiuqian, taohua, ziwei, hongxian  # noqa: E402
import users  # noqa: E402

STATIC_DIR = os.path.join(ROOT, "static")
MIME = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
        ".js": "application/javascript; charset=utf-8", ".svg": "image/svg+xml",
        ".png": "image/png", ".ico": "image/x-icon", ".webp": "image/webp"}


def _int(v, default=None):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


class Handler(BaseHTTPRequestHandler):
    server_version = "YinyuanWeb/1.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("[yinyuan] %s\n" % (fmt % args))

    # ---------- helpers ----------
    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _bad(self, msg, status=400):
        self._send_json({"error": msg}, status)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0:
            return {}
        raw = self.rfile.read(n)
        return json.loads(raw.decode("utf-8"))

    def _token(self):
        """从 Authorization: Bearer <token> 或 X-Token 头提取会话 token"""
        auth = self.headers.get("Authorization") or ""
        if auth.lower().startswith("bearer "):
            return auth[7:].strip()
        return (self.headers.get("X-Token") or "").strip()

    def _user(self, required=False):
        u = users.user_of_token(self._token())
        if not u and required:
            raise PermissionError("请先登录后再操作")
        return u

    def _static(self, path):
        if path == "/":
            path = "/index.html"
        rel = path.lstrip("/")
        fp = os.path.normpath(os.path.join(STATIC_DIR, rel))
        if not fp.startswith(STATIC_DIR) or not os.path.isfile(fp):
            self._bad("Not Found", 404)
            return
        ext = os.path.splitext(fp)[1]
        with open(fp, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", MIME.get(ext, "application/octet-stream"))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    # ---------- GET ----------
    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path == "/api/health":
                info = {"ok": True, "service": "yinyuan-web"}
                try:
                    info.update(users.stats())
                except Exception:
                    pass
                self._send_json(info)
                return
            if path == "/api/auth/me":
                u = self._user()
                self._send_json({"user": u} if u else {"user": None})
                return
            if path == "/api/records":
                u = self._user(required=True)
                self._send_json({"records": users.list_records(u["id"])})
                return
        except PermissionError as e:
            self._send_json({"error": str(e)}, 401)
            return
        except Exception as e:
            self._bad("服务内部错误：%s" % e, 500)
            return
        self._static(path)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Token")
        self.end_headers()

    # ---------- POST ----------
    def do_POST(self):
        path = urlparse(self.path).path
        try:
            data = self._body()
        except Exception:
            self._bad("请求体不是合法 JSON")
            return
        try:
            if path.startswith("/api/auth/"):
                self._auth_routes(path, data)
            elif path == "/api/records":
                u = self._user(required=True)
                mode = (data.get("mode") or "").strip() or "未知"
                title = (data.get("title") or "").strip() or "测算记录"
                users.save_record(u["id"], mode, title, data.get("summary"),
                                  json.dumps(data.get("payload") or {}, ensure_ascii=False))
                self._send_json({"ok": True})
            elif path == "/api/zodiac":
                self._api_zodiac(data)
            elif path == "/api/hehun":
                self._api_hehun(data)
            elif path == "/api/qiuqian":
                self._api_qiuqian(data)
            elif path == "/api/taohua":
                self._api_taohua(data)
            elif path == "/api/ziwei":
                self._api_ziwei(data)
            elif path == "/api/hongxian":
                self._api_hongxian(data)
            else:
                self._bad("Unknown API: " + path, 404)
        except ValueError as e:
            self._bad(str(e))
        except PermissionError as e:
            self._send_json({"error": str(e)}, 401)
        except Exception as e:
            self._bad("服务内部错误：%s" % e, 500)

    def _auth_routes(self, path, d):
        if path == "/api/auth/register":
            user, token = users.register(d.get("email"), d.get("password"))
            self._send_json({"user": user, "token": token})
        elif path == "/api/auth/login":
            user, token = users.login(d.get("email"), d.get("password"))
            self._send_json({"user": user, "token": token})
        elif path == "/api/auth/logout":
            users.logout(self._token())
            self._send_json({"ok": True})
        else:
            self._bad("Unknown auth API: " + path, 404)

    def _api_zodiac(self, d):
        a_year, b_year = _int(d.get("a_year")), _int(d.get("b_year"))
        a_z, b_z = d.get("a_zodiac"), d.get("b_zodiac")
        if a_year and b_year:
            r = zodiac.match(a_year=a_year, b_year=b_year)
        elif a_z and b_z:
            r = zodiac.match(a_zodiac=a_z, b_zodiac=b_z)
        else:
            raise ValueError("请提供双方出生年份（a_year/b_year）或生肖（a_zodiac/b_zodiac）")
        self._send_json(r)

    def _api_hehun(self, d):
        for k in ("a_date", "b_date"):
            if not d.get(k):
                raise ValueError("缺少 %s（格式 YYYY-MM-DD）" % k)
        r = hehun.hehun(
            d["a_date"], _int(d.get("a_hour"), 12), _int(d.get("a_minute"), 0), d.get("a_sex", "男"),
            d["b_date"], _int(d.get("b_hour"), 12), _int(d.get("b_minute"), 0), d.get("b_sex", "女"))
        self._send_json(r)

    def _api_qiuqian(self, d):
        question = (d.get("question") or "").strip()
        if not question:
            raise ValueError("请写下你想问的姻缘问题")
        self._send_json(qiuqian.draw(d.get("name") or "", question))

    def _api_taohua(self, d):
        year = _int(d.get("year"))
        if not year:
            raise ValueError("请提供出生年份 year")
        self._send_json(taohua.report(year, d.get("status"), d.get("flow_year", 2026)))

    def _api_ziwei(self, d):
        if not d.get("date"):
            raise ValueError("缺少 date（格式 YYYY-MM-DD）")
        self._send_json(ziwei.analyze(
            d["date"], _int(d.get("hour"), 12), _int(d.get("minute"), 0), d.get("sex", "男")))

    def _api_hongxian(self, d):
        if not d.get("date"):
            raise ValueError("缺少 date（格式 YYYY-MM-DD）")
        self._send_json(hongxian.analyze(
            d["date"], _int(d.get("hour"), 12), _int(d.get("minute"), 0),
            d.get("sex", "男"), d.get("expect")))


def main():
    port = int(os.environ.get("PORT", 8300))
    host = os.environ.get("HOST", "0.0.0.0")
    srv = ThreadingHTTPServer((host, port), Handler)
    print("月老姻缘测算网站已启动: http://%s:%d/" % ("127.0.0.1" if host == "0.0.0.0" else host, port))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
