import typing
from itertools import chain
import requests
from enum import Enum
from typing import Callable
import threading
from env_reader import CLIENT_ID, CLIENT_SECRET

app_access_token: str = ""
app_access_token_lock = threading.RLock()
MAX_RETRIES = 5
T = typing.TypeVar('T')


def req_with_app_access_token(req_func: Callable[[str], requests.Response],
                              prepend_bearer: bool = True,
                              extraction: Callable[[requests.Response], T] = (lambda x: x)) -> T:
    global app_access_token

    resp = req_func((prepend_bearer and f"Bearer {app_access_token}") or app_access_token)
    tries = 0
    while resp.status_code != 200 and tries < MAX_RETRIES:
        app_access_token_lock.acquire()
        try:
            x = requests.post(f"https://id.twitch.tv/oauth2/token?"
                              f"client_id={CLIENT_ID}"
                              f"&client_secret={CLIENT_SECRET}"
                              f"&grant_type=client_credentials")
            app_access_token = x.json()["access_token"]
            resp = req_func((prepend_bearer and f"Bearer {app_access_token}") or app_access_token)
        finally:
            app_access_token_lock.release()
        tries += 1

    return extraction(resp)


def from_one_to_other(ones: list[str], one_literal: str, other_literal: str) -> list[str]:
    """
    :param ones: the actual usernames/user ids
    :param one_literal: login or id
    :param other_literal: login or id (opposite of one_literal)
    :return: actual id/name only on success
    """
    assert len(ones) > 0

    all_names = []
    for i in range((len(ones) // 100) + 1):
        all_params = f"{one_literal}=" + f"&{one_literal}=".join(ones[i * 100:min(len(ones), (i + 1) * 100)])
        resp = req_with_app_access_token(
            lambda aatoken: requests.get(f"https://api.twitch.tv/helix/users?{all_params}",
                                         headers={"Authorization": aatoken, "Client-Id": f"{CLIENT_ID}"}))

        if resp.status_code == 200:
            data = resp.json()["data"]
            all_names.append([item[f"{other_literal}"] for item in data])
        if resp.status_code == 400:
            raise requests.RequestException(
                resp.json()["message"] +
                "\nThe id or login query parameter is required unless the request uses a user access token; "
                "The request exceeded the maximum allowed number of id and/or login query parameters. "
                "(see https://dev.twitch.tv/docs/api/reference/#get-users)",
                response=resp)
        if resp.status_code == 401:
            raise requests.RequestException(
                resp.json()["message"] +
                "\nThe Authorization header is required and must contain an app access token or user access token; "
                "The access token is not valid; "
                "The ID specified in the Client-Id header does not match the client ID specified in the access token."
                "(see https://dev.twitch.tv/docs/api/reference/#get-users)",
                response=resp)

    return list(chain.from_iterable(all_names))


def names_to_ids(names: list[str]) -> list[str]:
    """
    :param name: the users' usernames
    :return: the userids of the specified users
    """
    return from_one_to_other(names, 'login', 'id')


def name_to_id(name: str) -> str:
    """
    :param name: the user's username
    :return: the userid of the specified user
    """
    ids = names_to_ids([name])
    if len(ids) == 0:
        raise IndexError("The specified user could not be found")
    return ids[0]


def ids_to_names(ids: list[str]) -> list[str]:
    """
    :param ids: the users' ids
    :return: the usernames of the specified users
    """
    return from_one_to_other(ids, 'id', 'login')


def id_to_name(id: str) -> str:
    """
    :param id: the user's id
    :return: the username of the specified user
    """
    names = ids_to_names([id])
    if len(names) == 0:
        raise IndexError("The specified id could not be found")
    return names[0]
