import requests
import threading
from env_reader import CLIENT_ID, CLIENT_SECRET


app_access_token: str = ""
app_access_token_lock = threading.RLock()


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


def name_to_id(name: str) -> str:
    global app_access_token

    app_access_token_lock.acquire()
    try:
        headers = {"Authorization": f"Bearer {app_access_token}", "Client-Id": f"{CLIENT_ID}"}
        x = requests.get(f"https://api.twitch.tv/helix/users?login={name}", headers=headers)
        while x.status_code == 401:
            renew_app_access_token()
            headers = {"Authorization": f"Bearer {app_access_token}", "Client-Id": f"{CLIENT_ID}"}
            x = requests.get(f"https://api.twitch.tv/helix/users?login={name}", headers=headers)
    finally:
        app_access_token_lock.release()

    return x.json()["data"][0]["id"]


def id_to_name(id: str) -> str:
    global app_access_token

    app_access_token_lock.acquire()
    try:
        headers = {"Authorization": f"Bearer {app_access_token}", "Client-Id": f"{CLIENT_ID}"}
        x = requests.get(f"https://api.twitch.tv/helix/users?id={id}", headers=headers)
        while x.status_code == 401:
            renew_app_access_token()
            headers = {"Authorization": f"Bearer {app_access_token}", "Client-Id": f"{CLIENT_ID}"}
            x = requests.get(f"https://api.twitch.tv/helix/users?id={id}", headers=headers)
    finally:
        app_access_token_lock.release()

    return x.json()["data"][0]["login"]
