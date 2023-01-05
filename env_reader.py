import os


def is_env_read(var_str):
    try:
        return os.environ[var_str]
    except:
        with open(".env", "r") as f:
            for line in f:
                split_line = line.strip().split("=", 1)
                if var_str == split_line[0]:
                    to_set = split_line[1].strip()
                    if to_set[0] == '"':
                        to_set = to_set[1:-1]
                    return to_set
            return ""


CLIENT_ID = is_env_read('CLIENT_ID')
TMI_TOKEN = is_env_read('TMI_TOKEN')
databaseURL = is_env_read('DATABASE_URL')
