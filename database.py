from firebase_admin import credentials, firestore, db
import firebase_admin
import os

cred = credentials.Certificate("./.firebase_config.json")
# firebase_admin.initialize_app(cred)
databaseURL = os.environ['DATABASE_URL']
firebase_admin.initialize_app(cred, {'databaseURL': databaseURL})
PATH_SEPERATOR = "/"

IGNORED_PATH_DB = PATH_SEPERATOR + "Ignored"
IGNORED_DB_REF = db.reference(IGNORED_PATH_DB)
USERS_PATH_DB = PATH_SEPERATOR + "Users"
USERS_DB_REF = db.reference(USERS_PATH_DB)

DEFAULT_COMPLEMENT_CHANCE = 10.0 / 3.0
DEFAULT_SHOULD_IGNORE_BOTS = True
DEFAULT_TTS_IGNORE_PREFIX = "!"

# Database keys:
COMPLEMENT_CHANCE = "complement_chance"
SHOULD_IGNORE_BOTS = "should_ignore_bots"
IS_JOINED = "is_joined"
TTS_IGNORE_PREFIX = "tts_ignore_prefix"

DEFAULT_USER = {COMPLEMENT_CHANCE: DEFAULT_COMPLEMENT_CHANCE, SHOULD_IGNORE_BOTS: DEFAULT_SHOULD_IGNORE_BOTS,
                IS_JOINED: True, TTS_IGNORE_PREFIX: DEFAULT_TTS_IGNORE_PREFIX}


def is_user_ignored(user):
    return user in IGNORED_DB_REF.get(False, True)


def ignore(user):
    USERS_DB_REF.push(user)


def unignore(user):
    db.reference(IGNORED_PATH_DB + PATH_SEPERATOR + user).delete()


def channel_exists(user):
    return user in USERS_DB_REF.get(False, True)


def is_channel_joined(user):
    if not channel_exists(user):
        return False

    user_is_joined_path = USERS_PATH_DB + PATH_SEPERATOR + user + PATH_SEPERATOR + IS_JOINED
    user_is_joined_ref = db.reference(user_is_joined_path)
    return user_is_joined_ref.get()


def join_channel(user):
    if not channel_exists:
        USERS_DB_REF.push({user: DEFAULT_USER})
        return

    user_is_joined_path = USERS_PATH_DB + PATH_SEPERATOR + user + PATH_SEPERATOR + IS_JOINED
    user_is_joined_ref = db.reference(user_is_joined_path)
    user_is_joined_ref.set(True)


def leave_channel(user):
    user_is_joined_path = USERS_PATH_DB + PATH_SEPERATOR + user + PATH_SEPERATOR + IS_JOINED
    user_is_joined_ref = db.reference(user_is_joined_path)
    user_is_joined_ref.set(False)


def delete_channel(user):
    user_path = USERS_PATH_DB + PATH_SEPERATOR + user
    user_ref = db.reference(user_path)
    user_ref.delete()


def get_joined_channels():
    # TODO: make sure to NOT count the ones which have left, but not deleted!
    all_users = USERS_DB_REF.get(False, True)
    joined_users = []
    for user in all_users:
        user_is_joined_path = USERS_PATH_DB + PATH_SEPERATOR + user + PATH_SEPERATOR + IS_JOINED
        user_is_joined_ref = db.reference(user_is_joined_path)
        if user_is_joined_ref.get():
            joined_users.append(user)
    return joined_users


def number_of_joined_channels():
    # TODO: make sure to NOT count the ones which have left, but not deleted!
    return


def get_tts_ignore_prefix(user):
    return


def get_chance(user):
    user_chance_path = USERS_PATH_DB + PATH_SEPERATOR + user + PATH_SEPERATOR + COMPLEMENT_CHANCE
    user_chance_ref = db.reference(user_chance_path)
    print(user)
    print(user_chance_ref.get())
    return user_chance_ref.get()


def ignore_bots(user):
    return
