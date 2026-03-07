def insert_action_item(
    cur,
    client,
    description,
    owner,
    due_date,
    priority,
    source_message_id
):

    cur.execute(
        """
        INSERT INTO action_items
        (client, description, owner, due_date, priority, source_message_id)
        VALUES (%s,%s,%s,%s,%s,%s)
        """,
        (
            client,
            description,
            owner,
            due_date,
            priority,
            source_message_id
        )
    )