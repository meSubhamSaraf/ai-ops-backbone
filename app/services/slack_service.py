import requests
from app.config import SLACK_BOT_TOKEN


def fetch_slack_user(user_id):

    url = "https://slack.com/api/users.info"

    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
    }

    params = {
        "user": user_id
    }

    response = requests.get(url, headers=headers, params=params)

    data = response.json()

    if not data.get("ok"):
        return None

    user = data["user"]

    return {
        "real_name": user.get("real_name"),
        "display_name": user["profile"].get("display_name"),
        "email": user["profile"].get("email")
    }