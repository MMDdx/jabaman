# server.py
"""لایه‌ی HTTP سرور — هندلر BaseHTTPRequestHandler.

تغییرات نسبت به نسخه‌ی قبل:
- پشتیبانی از هدرهای اضافی در پاسخ (Set-Cookie, Location, ...).
- استفاده از ThreadingHTTPServer برای پاسخگویی همزمان.
- ارسال واقعی Set-Cookie هنگام ورود و خروج.
- ریدایرکت‌های واقعی HTTP (با هدر Location).
- رفع مشکل charset در content-type ها.
"""
import http.server
import socketserver
import os
from http.cookies import SimpleCookie

import models
import router

HOST = "localhost"
PORT = 8000
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# مسیرهای استاتیک HTML که به‌طور مستقیم از static/ سرو می‌شوند
GET_STATIC_ROUTES = {
    "/contact": "contact.html",
    "/register": "signup.html",
    "/login": "login.html",
    "/add-property": "add-property.html",
}


class RequestHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        session_id = self.get_session_id()
        user_id = models.get_user_by_session(session_id)
        path = self.path.split('?')[0]

        # ۱. مسیرهای داینامیک (Router)
        dynamic_response = router.process_get(path, user_id)
        if dynamic_response is not None:
            self._send(dynamic_response)
            return

        # ۲. صفحات HTML استاتیک (login, signup, contact, add-property)
        if path in GET_STATIC_ROUTES:
            file_name = GET_STATIC_ROUTES[path]
            file_path = os.path.join(STATIC_DIR, file_name)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                self._send((200, "text/html; charset=utf-8",
                            open(file_path, "rb").read(), []))
            else:
                self._send_error(404)
            return

        # ۳. فایل‌های استاتیک عمومی (CSS, JS, images)
        if path.startswith("/static/"):
            file_path = os.path.join(STATIC_DIR, path[len("/static/"):])
            if os.path.exists(file_path) and os.path.isfile(file_path):
                content_type = self._guess_content_type(file_path)
                with open(file_path, "rb") as f:
                    body = f.read()
                self._send((200, content_type, body, []))
            else:
                self._send_error(404)
            return

        # ۴. هیچ‌کدام → ۴۰۴
        self._send_error(404)

    def do_POST(self):
        session_id = self.get_session_id()
        user_id = models.get_user_by_session(session_id)
        path = self.path.split('?')[0]
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length else b''
        response = router.process_post(path, post_data, user_id)
        self._send(response)

    # ----------------- متدهای کمکی -----------------

    def _send(self, response):
        """ارسال پاسخ به کلاینت.

        response می‌تواند یکی از این فرمت‌ها باشد:
        - (status, content_type, body)
        - (status, content_type, body, headers_list)
        """
        if len(response) == 3:
            status, content_type, body = response
            headers = []
        elif len(response) == 4:
            status, content_type, body, headers = response
        else:
            status, content_type, body = 500, "text/html; charset=utf-8", "Internal Server Error"
            headers = []

        self.send_response(status)
        self.send_header("Content-type", content_type)
        # هدرهای اضافی (Set-Cookie, Location, ...)
        for header_name, header_value in headers:
            self.send_header(header_name, header_value)
        self.end_headers()

        if isinstance(body, str):
            body = body.encode("utf-8")
        self.wfile.write(body)

    def _send_error(self, code):
        """ارسال صفحه خطای سفارشی."""
        if code == 404:
            _, _, body = router.error_404()
        elif code == 403:
            _, _, body = router.error_403()
        elif code == 500:
            _, _, body = router.error_500()
        else:
            body = f"Error {code}".encode("utf-8") if isinstance(body := f"Error {code}", str) else b"Error"

        self.send_response(code)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.wfile.write(body)

    def _guess_content_type(self, file_path):
        """حدس Content-Type بر اساس پسوند فایل."""
        ext = os.path.splitext(file_path)[1].lower()
        types = {
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".html": "text/html; charset=utf-8",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml",
            ".ico": "image/x-icon",
            ".woff": "font/woff",
            ".woff2": "font/woff2",
        }
        return types.get(ext, "application/octet-stream")

    def get_session_id(self):
        """خواندن session_id از کوکی."""
        cookie_header = self.headers.get('Cookie')
        if cookie_header:
            cookies = SimpleCookie()
            cookies.load(cookie_header)
            if 'session_id' in cookies:
                return cookies['session_id'].value
        return None

    def log_message(self, format, *args):
        """لاگ سفارشی برای خوانایی بهتر."""
        # برای خاموش‌کردن لاگ، خط زیر را کامنت کنید
        super().log_message(format, *args)


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """سرور HTTP چندنخی برای پاسخگویی همزمان به چند درخواست."""
    daemon_threads = True
    allow_reuse_address = True


def start():
    server_address = (HOST, PORT)
    httpd = ThreadingHTTPServer(server_address, RequestHandler)
    print(f"سرور در http://{HOST}:{PORT} اجرا شد.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nسرور متوقف شد.")
        httpd.shutdown()