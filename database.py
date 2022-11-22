from firebase_admin import credentials, db
import firebase_admin
import os

cred = credentials.Certificate("./.firebase_config.json")
databaseURL = os.environ['DATABASE_URL']
firebase_admin.initialize_app(cred, {'databaseURL': databaseURL})

REF = db.reference('/')
IGNORED_DB_REF = REF.child('Ignored')
USERS_DB_REF = REF.child('Users')

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
    IGNORED_DB_REF.child(user).delete()


def channel_exists(user):
    users = USERS_DB_REF.get(False, True)
    return (users is not None) and user in users


def is_channel_joined(user):
    if not channel_exists(user):
        return False

    return USERS_DB_REF.child(user).child(IS_JOINED).get()


def join_channel(user):
    if not channel_exists(user):
        USERS_DB_REF.child(user).set(DEFAULT_USER)
    else:
        USERS_DB_REF.child(user).child(IS_JOINED).set(True)


def leave_channel(user):
    USERS_DB_REF.child(user).child(IS_JOINED).set(False)


def delete_channel(user):
    USERS_DB_REF.child(user).delete()


def get_joined_channels():
    # TODO: make sure to NOT count the ones which have left, but not deleted!
    all_users = USERS_DB_REF.get(False, True)
    joined_users = []
    if all_users is None:
        return joined_users
    for user in all_users:
        if USERS_DB_REF.child(user).child(IS_JOINED).get():
            joined_users.append(user)
    return joined_users


def number_of_joined_channels():
    # TODO: make sure to NOT count the ones which have left, but not deleted!
    return len(get_joined_channels())


def get_tts_ignore_prefix(user):
    return USERS_DB_REF.child(user).child(TTS_IGNORE_PREFIX).get()


def get_chance(user):
    return USERS_DB_REF.child(user).child(COMPLEMENT_CHANCE).get()


def ignore_bots(user):
    USERS_DB_REF.child(user).child(SHOULD_IGNORE_BOTS).get()
