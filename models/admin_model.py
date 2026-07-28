
"""توابع دامنه‌ی داشبورد ادمین.
"""
from ._shared import get_db


def get_admin_stats():
    """گرفتن آمار کلی برای داشبورد ادمین."""
    with get_db() as conn:
        users_count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        properties_count = conn.execute("SELECT COUNT(*) AS c FROM properties").fetchone()["c"]
        messages_count = conn.execute("SELECT COUNT(*) AS c FROM messages").fetchone()["c"]
        unread_count = conn.execute(
            "SELECT COUNT(*) AS c FROM messages WHERE is_read = 0"
        ).fetchone()["c"]
        comments_count = conn.execute("SELECT COUNT(*) AS c FROM comments").fetchone()["c"]
        hosts_count = conn.execute(
            "SELECT COUNT(*) AS c FROM users WHERE account_type = 'host'"
        ).fetchone()["c"]
        reservations_count = conn.execute(
            "SELECT COUNT(*) AS c FROM reservations WHERE status = 'confirmed'"
        ).fetchone()["c"]
        reservations_total_count = conn.execute(
            "SELECT COUNT(*) AS c FROM reservations"
        ).fetchone()["c"]
        cancelled_count = conn.execute(
            "SELECT COUNT(*) AS c FROM reservations WHERE status = 'cancelled'"
        ).fetchone()["c"]
        reserved_properties_count = conn.execute(
            "SELECT COUNT(*) AS c FROM properties WHERE is_reserved = 1"
        ).fetchone()["c"]
        revenue_row = conn.execute(
            "SELECT COALESCE(SUM(total_price), 0) AS s FROM reservations "
            "WHERE status = 'confirmed'"
        ).fetchone()
        total_revenue = float(revenue_row["s"] or 0)
    return {
        "users": users_count,
        "properties": properties_count,
        "messages": messages_count,
        "unread_messages": unread_count,
        "comments": comments_count,
        "hosts": hosts_count,
        "reservations": reservations_count,
        "reservations_total": reservations_total_count,
        "reservations_cancelled": cancelled_count,
        "reserved_properties": reserved_properties_count,
        "total_revenue": total_revenue,
    }
