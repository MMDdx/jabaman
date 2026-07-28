
import http.server
import os
from http.cookies import SimpleCookie

import models
import router

HOST = "localhost"
PORT = 8000
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


class RequestHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        session_id = self.get_session_id()
        user_id = models.get_user_by_session(session_id)
        path = self.path.split('?')[0]

        # ۱. مسیرهای داینامیک (Router) — شامل تمام صفحات HTML
        dynamic_response = router.process_get(path, user_id)
        if dynamic_response is not None:
            self._send(dynamic_response)
            return

        if path.startswith("/static/"):
            file_path = os.path.join(STATIC_DIR, path[len("/static/"):])
            if os.path.exists(file_path) and os.path.isfile(file_path):
                content_type = self._guess_content_type(file_path)
                with open(file_path, "rb") as f:
                    body = f.read()
                # CSS/JS را no-cache می‌کنیم تا تغییرات سریع دیده شوند.
                # اما فونت‌ها و تصاویر را cache می‌کنیم (با مدت زمان طولانی)
                ext = os.path.splitext(file_path)[1].lower()
                if ext in (".woff", ".woff2", ".png", ".jpg", ".jpeg",
                          ".gif", ".svg", ".ico", ".webp"):
                    cache_control = "public, max-age=2592000"  # ۳۰ روز
                else:
                    cache_control = "no-cache, must-revalidate"
                self._send((200, content_type, body, [
                    ("Cache-Control", cache_control)
                ]))
            else:
                self._send_error(404)
            return

        self._send_error(404)

    def do_POST(self):
        session_id = self.get_session_id()
        user_id = models.get_user_by_session(session_id)
        path = self.path.split('?')[0]
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length else b''
        # پاس دادن هدرها به router برای تشخیص درخواست AJAX (fetch)
        response = router.process_post(path, post_data, user_id, self.headers)
        self._send(response)

    # ----------------- متدهای کمکی -----------------

    def _send(self, response):
        """
        - (status, content_type, body)
        - (status, content_type, body, headers_list)
        """
        if not isinstance(response, (list, tuple)):
            response = (500, "text/html; charset=utf-8", "Internal Server Error", [])

        if len(response) == 3:
            status, content_type, body = response
            headers = []
        elif len(response) == 4:
            status, content_type, body, headers = response
        else:
            status, content_type, body, headers = (
                500, "text/html; charset=utf-8", "Internal Server Error", []
            )

        self.send_response(status)
        self.send_header("Content-type", content_type)
        # هدرهای اضافی (Set-Cookie, Location, ...)
        for header_name, header_value in headers:
            self.send_header(header_name, header_value)
        self.end_headers()

        if isinstance(body, str):
            body = body.encode("utf-8")
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass  # disconnect

    def _send_error(self, code):
        """ارسال صفحه خطای سفارشی.
        """
        if code == 404:
            resp = router.error_404()
        elif code == 403:
            resp = router.error_403()
        elif code == 500:
            resp = router.error_500()
        else:
            resp = (code, "text/html; charset=utf-8", f"Error {code}", [])

        # همیشه ۴تایی است، اما برای اطمینان از هر دو حالت پشتیبانی می‌کنیم
        if len(resp) == 3:
            status, content_type, body = resp
            headers = []
        else:
            status, content_type, body, headers = resp

        self.send_response(status)
        self.send_header("Content-type", content_type)
        for header_name, header_value in headers:
            self.send_header(header_name, header_value)
        self.end_headers()

        if isinstance(body, str):
            body = body.encode("utf-8")
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass

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
        super().log_message(format, *args)


def start():
    """اجرای سرور با ThreadingHTTPServer داخلی پایتون."""
    server_address = (HOST, PORT)

    httpd = http.server.ThreadingHTTPServer(server_address, RequestHandler)
    httpd.daemon_threads = True
    print(f"سرور در http://{HOST}:{PORT} اجرا شد.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nسرور متوقف شد.")
        httpd.shutdown()