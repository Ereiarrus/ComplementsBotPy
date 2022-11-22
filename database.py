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
DEFAULT_COMMAND_COMPLEMENT_ENABLED = True
DEFAULT_RANDOM_COMPLEMENT_ENABLED = True

# Database keys:
COMPLEMENT_CHANCE = "complement_chance"
SHOULD_IGNORE_BOTS = "should_ignore_bots"
IS_JOINED = "is_joined"
TTS_IGNORE_PREFIX = "tts_ignore_prefix"
COMMAND_COMPLEMENT_ENABLED = "command_complement_enabled"
RANDOM_COMPLEMENT_ENABLED = "random_complement_enabled"
CUSTOM_COMPLEMENTS = "custom_complements"

DEFAULT_USER = {COMPLEMENT_CHANCE: DEFAULT_COMPLEMENT_CHANCE, SHOULD_IGNORE_BOTS: DEFAULT_SHOULD_IGNORE_BOTS,
                IS_JOINED: True, TTS_IGNORE_PREFIX: DEFAULT_TTS_IGNORE_PREFIX,
                COMMAND_COMPLEMENT_ENABLED: DEFAULT_COMMAND_COMPLEMENT_ENABLED,
                RANDOM_COMPLEMENT_ENABLED: DEFAULT_RANDOM_COMPLEMENT_ENABLED}


def is_user_ignored(user):
    users = IGNORED_DB_REF.get()
    if users is None:
        return False
    return user in users


def ignore(user):
    def ignore_transaction(data):
        if data is None:
            data = []
        data.append(user)
        return data

    IGNORED_DB_REF.transaction(ignore_transaction)


def unignore(user):
    def unignore_transaction(data):
        data.remove(user)
        return data

    IGNORED_DB_REF.transaction(unignore_transaction)


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
    all_users = USERS_DB_REF.get(False, True)
    joined_users = []
    if all_users is None:
        return joined_users
    for user in all_users:
        if USERS_DB_REF.child(user).child(IS_JOINED).get():
            joined_users.append(user)
    return joined_users


def number_of_joined_channels():
    return len(get_joined_channels())


def set_tts_ignore_prefix(user, prefix):
    tts_ignore_prefix = USERS_DB_REF.child(user).child(TTS_IGNORE_PREFIX).set(prefix)


def get_tts_ignore_prefix(user):
    tts_ignore_prefix = USERS_DB_REF.child(user).child(TTS_IGNORE_PREFIX).get()
    if tts_ignore_prefix is None:
        set_tts_ignore_prefix(user, DEFAULT_TTS_IGNORE_PREFIX)
        tts_ignore_prefix = DEFAULT_TTS_IGNORE_PREFIX
    return tts_ignore_prefix


def set_complement_chance(user, chance):
    USERS_DB_REF.child(user).child(COMPLEMENT_CHANCE).set(chance)


def get_complement_chance(user):
    chance = USERS_DB_REF.child(user).child(COMPLEMENT_CHANCE).get()
    if chance is None:
        set_complement_chance(user, DEFAULT_COMPLEMENT_CHANCE)
        chance = DEFAULT_TTS_IGNORE_PREFIX
    return chance


def ignore_bots(user):
    USERS_DB_REF.child(user).child(SHOULD_IGNORE_BOTS).get()


def set_command_complement_enabled(user, is_enabled):
    USERS_DB_REF.child(user).child(COMMAND_COMPLEMENT_ENABLED).set(is_enabled)


def get_cmd_complement_enabled(user):
    is_enabled = USERS_DB_REF.child(user).child(COMMAND_COMPLEMENT_ENABLED).get()
    if is_enabled is None:
        set_command_complement_enabled(user, DEFAULT_COMMAND_COMPLEMENT_ENABLED)
        is_enabled = DEFAULT_COMMAND_COMPLEMENT_ENABLED
    return is_enabled


def disable_cmd_complement(user):
    set_command_complement_enabled(user, False)


def enable_cmd_complement(user):
    set_command_complement_enabled(user, True)


def set_random_complement_enabled(user, is_enabled):
    USERS_DB_REF.child(user).child(RANDOM_COMPLEMENT_ENABLED).set(is_enabled)


def get_random_complement_enabled(user):
    is_enabled = USERS_DB_REF.child(user).child(RANDOM_COMPLEMENT_ENABLED).get()
    if is_enabled is None:
        set_random_complement_enabled(user, DEFAULT_RANDOM_COMPLEMENT_ENABLED)
        is_enabled = DEFAULT_RANDOM_COMPLEMENT_ENABLED
    return is_enabled


def disable_random_complement(user):
    set_random_complement_enabled(user, False)


def enable_random_complement(user):
    set_random_complement_enabled(user, True)


def add_complement(user, complement):
    def add_transaction(data):
        if data is None:
            data = []
        data.append(complement)
        return data

    USERS_DB_REF.child(user).child(CUSTOM_COMPLEMENTS).transaction(add_transaction)


def remove_all_complements(user):
    USERS_DB_REF.child(user).child(CUSTOM_COMPLEMENTS).delete()


def get_custom_complements(user):
    complements = USERS_DB_REF.child(user).child(CUSTOM_COMPLEMENTS).get()
    if complements is None:
        return []
    return complements






