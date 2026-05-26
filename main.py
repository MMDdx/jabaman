import os
import db_setup
import server

if __name__ == '__main__':
    if not os.path.exists(db_setup.DB_NAME):
        print("ساخت دیتابیس ...")
        db_setup.main()
    server.start()