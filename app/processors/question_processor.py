from app.repositories.question_repository import insert_question


def process_question(message_id, client_name, product, message_text, cur):

    insert_question(
        cur,
        message_id,
        client_name,
        product,
        message_text
    )