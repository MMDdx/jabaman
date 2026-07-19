import sqlite3
import uuid


DB_NAME = "db.sqlite"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ---------- کاربران ----------
def get_user(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return user

def get_all_users():
    conn = get_db()
    rows = conn.execute("SELECT id, first_name, last_name, phone, account_type, created_at FROM users").fetchall()
    conn.close()
    return rows

def create_user(first_name, last_name, phone, password_hash, account_type):
    conn = get_db()
    conn.execute("INSERT INTO users (first_name, last_name, phone, password, account_type) VALUES (?,?,?,?,?)",
                 (first_name, last_name, phone, password_hash, account_type))
    conn.commit()
    conn.close()

def update_user(user_id, first_name, last_name, phone, account_type):
    conn = get_db()
    conn.execute("UPDATE users SET first_name=?, last_name=?, phone=?, account_type=? WHERE id=?",
                 (first_name, last_name, phone, account_type, user_id))
    conn.commit()
    conn.close()

# ---------- اقامتگاه‌ها ----------
def get_all_properties():
    conn = get_db()
    rows = conn.execute("SELECT id, host_id, title, property_type, location, price_per_night, max_guests, bedrooms, bathrooms, description, amenities, images, created_at FROM properties").fetchall()
    conn.close()
    return rows

def get_property(property_id):
    conn = get_db()
    prop = conn.execute("SELECT * FROM properties WHERE id=?", (property_id,)).fetchone()
    conn.close()
    return prop

def get_featured_properties(limit=6):
    conn = get_db()
    rows = conn.execute("SELECT id, title, property_type, location, price_per_night FROM properties ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return rows

def create_property(host_id, title, description, property_type, location, price_per_night, max_guests, bedrooms, bathrooms):
    conn = get_db()
    conn.execute("INSERT INTO properties (host_id, title, description, property_type, location, price_per_night, max_guests, bedrooms, bathrooms) VALUES (?,?,?,?,?,?,?,?,?)",
                 (host_id, title, description, property_type, location, price_per_night, max_guests, bedrooms, bathrooms))
    conn.commit()
    conn.close()

def update_property(property_id, title, description, property_type, location, price_per_night, max_guests, bedrooms, bathrooms):
    conn = get_db()
    conn.execute("UPDATE properties SET title=?, description=?, property_type=?, location=?, price_per_night=?, max_guests=?, bedrooms=?, bathrooms=? WHERE id=?",
                 (title, description, property_type, location, price_per_night, max_guests, bedrooms, bathrooms, property_id))
    conn.commit()
    conn.close()

# ---------- پیام‌ها ----------
def get_all_messages():
    conn = get_db()
    rows = conn.execute("SELECT id, fullname, email, phone, topic, message_text, is_read, created_at FROM messages").fetchall()
    conn.close()
    return rows

def get_message(message_id):
    conn = get_db()
    msg = conn.execute("SELECT * FROM messages WHERE id=?", (message_id,)).fetchone()
    conn.close()
    return msg

def create_message(fullname, email, phone, topic, message_text):
    conn = get_db()
    conn.execute("INSERT INTO messages (fullname, email, phone, topic, message_text) VALUES (?,?,?,?,?)",
                 (fullname, email, phone, topic, message_text))
    conn.commit()
    conn.close()

# ---------- نظرات ----------
def get_comments_for_property(property_id):
    conn = get_db()
    comments = conn.execute(
        "SELECT c.comment_text, c.rating, c.created_at, u.first_name || ' ' || u.last_name as user_name "
        "FROM comments c JOIN users u ON c.user_id = u.id "
        "WHERE c.property_id = ? ORDER BY c.created_at DESC", (property_id,)
    ).fetchall()
    conn.close()
    return comments

def add_comment(user_id, property_id, comment_text, rating):
    conn = get_db()
    conn.execute("INSERT INTO comments (user_id, property_id, comment_text, rating) VALUES (?,?,?,?)",
                 (user_id, property_id, comment_text, rating))
    conn.commit()
    conn.close()

# ---------- سبد خرید ----------
def get_cart_items(user_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT p.id, p.title, p.location, p.price_per_night, p.images "
        "FROM cart c JOIN properties p ON c.property_id = p.id "
        "WHERE c.user_id = ?", (user_id,)
    ).fetchall()
    conn.close()
    return rows

def add_to_cart(user_id, property_id):
    conn = get_db()
    conn.execute("INSERT INTO cart (user_id, property_id) VALUES (?,?)", (user_id, property_id))
    conn.commit()
    conn.close()

# ---------- علاقمندی ----------
def get_wishlist_items(user_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT p.id, p.title, p.location, p.price_per_night, p.images "
        "FROM wishlist w JOIN properties p ON w.property_id = p.id "
        "WHERE w.user_id = ?", (user_id,)
    ).fetchall()
    conn.close()
    return rows

def add_to_wishlist(user_id, property_id):
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO wishlist (user_id, property_id) VALUES (?,?)", (user_id, property_id))
    conn.commit()
    conn.close()


def create_session(user_id):
    session_id = str(uuid.uuid4())
    conn = get_db()
    conn.execute("INSERT INTO sessions (id, user_id) VALUES (?, ?)", (session_id, user_id))
    conn.commit()
    conn.close()
    return session_id

def get_user_by_session(session_id):
    if not session_id:
        return None
    conn = get_db()
    session = conn.execute(
        "SELECT user_id FROM sessions WHERE id = ?", (session_id,)
    ).fetchone()
    conn.close()
    if session:
        return session["user_id"]
    return None

def delete_session(session_id):
    conn = get_db()
    conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

def get_user_by_phone(phone):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE phone = ?", (phone,)).fetchone()
    conn.close()
    return user