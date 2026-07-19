# main.py
"""نقطه ورود برنامه.

ابتدا دیتابیس را (در صورت عدم وجود) می‌سازد، سپس سرور را راه‌اندازی می‌کند.
"""
import os
import sys

# اطمینان از اینکه مسیر پروژه در sys.path است
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import db_setup
import server

if __name__ == '__main__':
    if not os.path.exists(db_setup.DB_NAME):
        print("ساخت دیتابیس ...")
        db_setup.main()
    else:
        # حتی اگر دیتابیس موجود باشد، مهاجرت را اجرا کن تا ستون‌های جدید اعمال شوند
        print("بررسی مهاجرت دیتابیس ...")
        db_setup.main()

    print("\n" + "=" * 50)
    print("  راه‌اندازی سرور jabaman")
    print("=" * 50)
    server.start()
