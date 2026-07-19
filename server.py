import http.server
import os
from http.cookies import SimpleCookie

import models
import router

HOST = "localhost"
PORT = 8000
STATIC_DIR = "static"

GET_ROUTES = {
    "/contact": "contact.html",
    "/register": "signup.html",   # ← نام فایل signup.html
    "/login": "login.html",
    "/add-property": "add-property.html",
}

class RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        session_id = self.get_session_id()
        user_id = models.get_user_by_session(session_id)  # import models
        path = self.path.split('?')[0]

        # ۱. مسیرهای داینامیک (Router)
        dynamic_response = router.process_get(path, user_id)
        if dynamic_response is not None:
            status, content_type, body = dynamic_response
            self.send_response(status)
            self.send_header("Content-type", content_type)
            self.end_headers()
            self.wfile.write(body.encode() if isinstance(body, str) else body)
            return

        # ۲. صفحات HTML استاتیک (login, signup, contact, add-property)
        if path in GET_ROUTES:
            file_name = GET_ROUTES[path]
            file_path = os.path.join(STATIC_DIR, file_name)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_custom_error(404)
            return

        # ۳. فایل‌های استاتیک عمومی (CSS, JS, images)
        if path.startswith("/static/"):
            file_path = path[1:]
            if os.path.exists(file_path) and os.path.isfile(file_path):
                self.send_response(200)
                if file_path.endswith(".css"):
                    self.send_header("Content-type", "text/css")
                elif file_path.endswith(".js"):
                    self.send_header("Content-type", "application/javascript")
                else:
                    self.send_header("Content-type", "application/octet-stream")
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_custom_error(404)
            return

        # ۴. هیچ‌کدام → ۴۰۴
        self.send_custom_error(404)

    def do_POST(self):
        session_id = self.get_session_id()
        user_id = models.get_user_by_session(session_id)  # import models
        # (همانند قبل، تغییری نکنید)
        path = self.path.split('?')[0]
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length else b''
        status, content_type, body = router.process_post(path, post_data, user_id)
        self.send_response(status)
        self.send_header("Content-type", content_type)
        self.end_headers()
        self.wfile.write(body.encode() if isinstance(body, str) else body)

    def send_custom_error(self, code):
        """ارسال صفحه خطای سفارشی"""
        if code == 404:
            _, _, body = router.error_404()
        elif code == 403:
            _, _, body = router.error_403()
        elif code == 500:
            _, _, body = router.error_500()
        else:
            body = f"Error {code}"
        self.send_response(code)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode() if isinstance(body, str) else body)

    def get_session_id(self):
        cookie_header = self.headers.get('Cookie')
        if cookie_header:
            cookies = SimpleCookie()
            cookies.load(cookie_header)
            if 'session_id' in cookies:
                return cookies['session_id'].value
        return None

def start():
    server_address = (HOST, PORT)
    httpd = http.server.HTTPServer(server_address, RequestHandler)
    print(f"سرور در http://{HOST}:{PORT} اجرا شد.")
    httpd.serve_forever()