import os


def is_env_read(var, var_str):
    if var != "":
        return var
    with open(".env", "r") as f:
        for line in f:
            split_line = line.strip().split("=", 1)
            if var_str == split_line[0]:
                to_set = split_line[1].strip()
                if to_set[0] == '"':
                    to_set = to_set[1:-1]
                return to_set
        return ""


CLIENT_ID = is_env_read(os.environ['CLIENT_ID'], 'CLIENT_ID')
TOKEN = is_env_read(os.environ['TMI_TOKEN'], 'TMI_TOKEN')
databaseURL = is_env_read(os.environ['DATABASE_URL'], 'DATABASE_URL')
