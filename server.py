# server.py (اصلاح شده)

import http.server
import os
import router

HOST = "localhost"
PORT = 8000
STATIC_DIR = "static"

GET_ROUTES = {
    "/contact": "contact.html",
    "/register": "signup.html",
    "/add-property": "add-property.html",
}

class RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?')[0]

        # ۱. مسیرهای داینامیک (از جمله /, /catalog, /admin/..., /property/...)
        dynamic_response = router.process_get(path)
        if dynamic_response is not None:
            status, content_type, body = dynamic_response
            self.send_response(status)
            self.send_header("Content-type", content_type)
            self.end_headers()
            self.wfile.write(body.encode() if isinstance(body, str) else body)
            return

        # ۲. فایل‌های HTML استاتیک
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
                # فایل HTML پیدا نشد -> 404 سفارشی
                self.send_custom_error(404)
            return

        # ۳. سایر فایل‌های استاتیک (CSS, JS, images...)
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

        # ۴. هیچ مسیری یافت نشد
        self.send_custom_error(404)

    def do_POST(self):
        path = self.path.split('?')[0]
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length else b''
        status, content_type, body = router.process_post(path, post_data)
        self.send_response(status)
        self.send_header("Content-type", content_type)
        self.end_headers()
        self.wfile.write(body.encode() if isinstance(body, str) else body)

    def send_custom_error(self, code):
        """ارسال صفحه خطای سفارشی با استفاده از router"""
        if code == 404:
            _, _, body = router.error_404()
        elif code == 403:
            # می‌توانیم بعداً اضافه کنیم
            _, _, body = router.error_403() if hasattr(router, 'error_403') else (403, "text/html", "Forbidden")
        elif code == 500:
            _, _, body = router.error_500() if hasattr(router, 'error_500') else (500, "text/html", "Internal Server Error")
        else:
            body = f"Error {code}"
        self.send_response(code)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode() if isinstance(body, str) else body)

def start():
    server_address = (HOST, PORT)
    httpd = http.server.HTTPServer(server_address, RequestHandler)
    print(f"سرور در http://{HOST}:{PORT} اجرا شد.")
    httpd.serve_forever()