def insert_raw_message(cur, source, external_id, content, metadata):

    cur.execute(
        """
        INSERT INTO raw_messages (source, external_id, content, metadata)
        VALUES (%s,%s,%s,%s)
        ON CONFLICT (external_id) DO NOTHING
        RETURNING id;
        """,
        (source, external_id, content, metadata)
    )

    return cur.fetchone()