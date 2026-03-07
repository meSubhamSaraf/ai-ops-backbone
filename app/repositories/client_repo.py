def get_client_from_channel(cur, channel_id):

    cur.execute(
        """
        SELECT client_name
        FROM client_channels
        WHERE platform='slack'
        AND external_id=%s
        """,
        (channel_id,)
    )

    row = cur.fetchone()

    return row[0] if row else None