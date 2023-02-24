import requests
import threading
from env_reader import CLIENT_ID, CLIENT_SECRET


app_access_token: str = ""
app_access_token_lock = threading.RLock()
MAX_RETRIES = 5


def renew_app_access_token() -> None:
    global app_access_token

    app_access_token_lock.acquire()
    try:
        x = requests.post(f"https://id.twitch.tv/oauth2/token?"
                          f"client_id={CLIENT_ID}"
                          f"&client_secret={CLIENT_SECRET}"
                          f"&grant_type=client_credentials")
        app_access_token = x.json()["access_token"]
    finally:
        app_access_token_lock.release()

    return app_access_token


def from_one_to_other(one: str, one_literal: str, other_literal: str) -> str:
    global app_access_token

    x = None
    retries = 0
    headers = {"Authorization": "", "Client-Id": f"{CLIENT_ID}"}
    app_access_token_lock.acquire()
    try:
        headers["Authorization"] = f"Bearer {app_access_token}"
        x = requests.get(f"https://api.twitch.tv/helix/users?{one_literal}={one}", headers=headers)
        while x.status_code == 401 and retries < MAX_RETRIES:
            renew_app_access_token()
            headers["Authorization"] = f"Bearer {app_access_token}"
            x = requests.get(f"https://api.twitch.tv/helix/users?{one_literal}={one}", headers=headers)
            retries += 1
    finally:
        app_access_token_lock.release()

    return x.json()["data"][0][f"{other_literal}"]


def name_to_id(name: str) -> str:
    return from_one_to_other(name, 'login', 'id')


def id_to_name(id: str) -> str:
    return from_one_to_other(name, 'id', 'login')

print(name_to_id("ereiarrus"))
