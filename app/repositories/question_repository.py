def insert_question(cur, message_id, client, product, question):

    query = """
    INSERT INTO client_questions (
        message_id,
        client,
        product,
        question
    )
    VALUES (%s, %s, %s, %s)
    """

    cur.execute(
        query,
        (message_id, client, product, question)
    )