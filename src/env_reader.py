"""
Loads all environment variables to be used throughout
"""

import os


def is_env_read(var_str) -> str:
    """
    Tries to read from the environment the given variable; if it doesn't exist, it looks for it in the .env file. If
    not found in either, returns an empty string.

    :param var_str: the environment variable we are looking for
    :return: the value of the environment variable, or empty string if it doesn't exist
    """

    try:
        return os.environ[var_str]
    except KeyError:
        with open("./.env", "r", encoding="utf-8") as env_file:
            for line in env_file:
                split_line = line.strip().split("=", 1)
                if var_str == split_line[0]:
                    to_set = split_line[1].strip()
                    if to_set[0] == '"':
                        to_set = to_set[1:-1]
                    return to_set
            return ""


TMI_TOKEN: str = is_env_read('TMI_TOKEN')
CLIENT_SECRET: str = is_env_read('CLIENT_SECRET')
databaseURL: str = is_env_read('DATABASE_URL')
