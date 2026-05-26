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

        # ۱. ابتدا مسیرهای داینامیک را امتحان کن
        dynamic_response = router.process_get(path)
        if dynamic_response is not None:
            status, content_type, body = dynamic_response
            self.send_response(status)
            self.send_header("Content-type", content_type)
            self.end_headers()
            self.wfile.write(body.encode() if isinstance(body, str) else body)
            return

        # ۲. مسیرهای استاتیک HTML
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
                self.send_error(404, "HTML file not found")
            return

        # ۳. سرو فایل‌های استاتیک (CSS, JS, ...)
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
                self.send_error(404)
            return

        # ۴. هیچ مسیری پیدا نشد
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Page not found")

    def do_POST(self):
        path = self.path.split('?')[0]
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length else b''

        status, content_type, body = router.process_post(path, post_data)

        self.send_response(status)
        self.send_header("Content-type", content_type)
        self.end_headers()
        self.wfile.write(body.encode() if isinstance(body, str) else body)

def start():
    server_address = (HOST, PORT)
    httpd = http.server.HTTPServer(server_address, RequestHandler)
    print(f"سرور در http://{HOST}:{PORT} اجرا شد.")
    httpd.serve_forever()