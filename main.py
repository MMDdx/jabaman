
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import db_setup
import server

if __name__ == '__main__':
    db_setup.main()

    print("\n" + "=" * 50)
    print("  راه‌اندازی سرور jabaman")
    print("=" * 50)
    server.start()
