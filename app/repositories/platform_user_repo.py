def get_platform_user(cur, platform, external_user_id):

    cur.execute(
        """
        SELECT real_name
        FROM platform_users
        WHERE platform=%s
        AND external_user_id=%s
        """,
        (platform, external_user_id)
    )

    row = cur.fetchone()

    return row[0] if row else None


def insert_platform_user(cur, platform, external_user_id, real_name, display_name, email=None):

    cur.execute(
        """
        INSERT INTO platform_users
        (platform, external_user_id, real_name, display_name, email)
        VALUES (%s,%s,%s,%s,%s)
        ON CONFLICT (platform, external_user_id) DO NOTHING
        """,
        (platform, external_user_id, real_name, display_name, email)
    )