import re
from firebase_admin import credentials, db
from env_reader import databaseURL
from typing import Any, Dict, Tuple, Optional
import firebase_admin
from .userid_to_from_username import name_to_id, id_to_name

cred: credentials.Certificate = credentials.Certificate("./.firebase_config.json")
firebase_admin.initialize_app(cred, {'databaseURL': databaseURL})

REF: db.Reference = db.reference('/')
IGNORED_DB_REF: db.Reference = REF.child('Ignored')
USERS_DB_REF: db.Reference = REF.child('Users')

# Default values for database:
DEFAULT_COMPLEMENT_CHANCE: float = 10.0 / 3.0
DEFAULT_SHOULD_IGNORE_BOTS: bool = True
DEFAULT_TTS_IGNORE_PREFIX: str = "!"
DEFAULT_COMMAND_COMPLEMENT_ENABLED: bool = True
DEFAULT_RANDOM_COMPLEMENT_ENABLED: bool = True
DEFAULT_COMMAND_COMPLEMENT_MUTED: bool = True
DEFAULT_RANDOM_COMPLEMENT_MUTED: bool = False
DEFAULT_IS_JOINED: bool = True
DEFAULT_DEFAULT_COMPLEMENTS_ENABLED: bool = True
DEFAULT_CUSTOM_COMPLEMENTS_ENABLED: bool = True

# Database keys:
COMPLEMENT_CHANCE: str = "complement_chance"
SHOULD_IGNORE_BOTS: str = "should_ignore_bots"
IS_JOINED: str = "is_joined"
MUTE_PREFIX: str = "tts_ignore_prefix"
COMMAND_COMPLEMENT_ENABLED: str = "command_complement_enabled"
RANDOM_COMPLEMENT_ENABLED: str = "random_complement_enabled"
CUSTOM_COMPLEMENTS: str = "custom_complements"
COMMAND_COMPLEMENT_MUTED: str = "command_complement_muted"
RANDOM_COMPLEMENT_MUTED: str = "random_complement_muted"
DEFAULT_COMPLEMENTS_ENABLED: str = "default_complements_enabled"
CUSTOM_COMPLEMENTS_ENABLED: str = "custom_complements_enabled"

DEFAULT_USER: Dict[str, Any] = {COMPLEMENT_CHANCE: DEFAULT_COMPLEMENT_CHANCE,
                                SHOULD_IGNORE_BOTS: DEFAULT_SHOULD_IGNORE_BOTS,
                                IS_JOINED: DEFAULT_IS_JOINED,
                                COMMAND_COMPLEMENT_ENABLED: DEFAULT_COMMAND_COMPLEMENT_ENABLED,
                                RANDOM_COMPLEMENT_ENABLED: DEFAULT_RANDOM_COMPLEMENT_ENABLED,
                                MUTE_PREFIX: DEFAULT_TTS_IGNORE_PREFIX,
                                COMMAND_COMPLEMENT_MUTED: DEFAULT_COMMAND_COMPLEMENT_MUTED,
                                RANDOM_COMPLEMENT_MUTED: DEFAULT_RANDOM_COMPLEMENT_MUTED,
                                CUSTOM_COMPLEMENTS_ENABLED: DEFAULT_CUSTOM_COMPLEMENTS_ENABLED,
                                DEFAULT_COMPLEMENTS_ENABLED: DEFAULT_DEFAULT_COMPLEMENTS_ENABLED
                                }


def is_user_ignored(username: str = None, userid: str = None) -> bool:
    """
    At least one of 'username' or 'userid' must be specified; userid is preferred whenever possible due to
     being guaranteed to not ever change
    :param username: twitch username which we are checking if they are ignored
    :param userid: twitch user id which we are checking if they are ignored
    :return: whether the specified user is ignored from getting complements or not
    """

    assert username or userid

    users: list[str] = IGNORED_DB_REF.get()
    if users is None:
        # No ignored users exist
        return False

    if not userid:
        userid = name_to_id(username)

    return userid in users


def ignore(username: str = None, userid: str = None) -> None:
    assert username or userid

    def ignore_transaction(data: list[str]):
        if data is None:
            data = []
        data.append(userid)
        return data

    if not userid:
        userid = name_to_id(username)

    IGNORED_DB_REF.transaction(ignore_transaction)


def unignore(username: str = None, userid: str = None) -> None:
    assert username or userid
    def unignore_transaction(data: list[str]) -> list[str]:
        data.remove(userid)
        return data

    if not userid:
        userid = name_to_id(username)

    IGNORED_DB_REF.transaction(unignore_transaction)


def channel_exists(username: str = None, userid: str = None) -> bool:
    assert username or userid
    users = USERS_DB_REF.get(False, True)
    if not userid:
        userid = name_to_id(username)
    return (users is not None) and userid in users


def is_channel_joined(username: str = None, userid: str = None) -> bool:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    if not channel_exists(userid=userid):
        return False

    return USERS_DB_REF.child(userid).child(IS_JOINED).get()


def join_channel(username: str = None, userid: str = None) -> None:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    if not channel_exists(userid=userid):
        USERS_DB_REF.child(userid).set(DEFAULT_USER)
    else:
        USERS_DB_REF.child(userid).child(IS_JOINED).set(True)


def leave_channel(username: str = None, userid: str = None) -> None:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(IS_JOINED).set(False)


def delete_channel(username: str = None, userid: str = None) -> None:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).delete()


def get_joined_channels() -> list[str]:
    all_users = USERS_DB_REF.get(False, True)
    joined_users: list[str] = []
    if all_users is None:
        return joined_users
    for user in all_users:
        if USERS_DB_REF.child(user).child(IS_JOINED).get():
            joined_users.append(user)
    return joined_users


def number_of_joined_channels() -> int:
    return len(get_joined_channels())


def set_tts_ignore_prefix(prefix: str, username: str = None, userid: str = None) -> None:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(MUTE_PREFIX).set(prefix)


def get_tts_ignore_prefix(username: str = None, userid: str = None) -> str:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    tts_ignore_prefix = USERS_DB_REF.child(userid).child(MUTE_PREFIX).get()
    if tts_ignore_prefix is None:
        set_tts_ignore_prefix(DEFAULT_TTS_IGNORE_PREFIX, userid=userid)
        tts_ignore_prefix = DEFAULT_TTS_IGNORE_PREFIX
    return tts_ignore_prefix


def set_complement_chance(chance: float, username: str = None, userid: str = None) -> None:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(COMPLEMENT_CHANCE).set(chance)


def get_complement_chance(username: str = None, userid: str = None) -> float:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    chance = USERS_DB_REF.child(userid).child(COMPLEMENT_CHANCE).get()
    if chance is None:
        set_complement_chance(DEFAULT_COMPLEMENT_CHANCE, userid=userid)
        chance = DEFAULT_COMPLEMENT_CHANCE
    return chance


def set_command_complement_enabled(is_enabled: bool, username: str = None, userid: str = None) -> None:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(COMMAND_COMPLEMENT_ENABLED).set(is_enabled)


def get_cmd_complement_enabled(username: str = None, userid: str = None) -> bool:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    is_enabled = USERS_DB_REF.child(userid).child(COMMAND_COMPLEMENT_ENABLED).get()
    if is_enabled is None:
        set_command_complement_enabled(DEFAULT_COMMAND_COMPLEMENT_ENABLED, userid=userid)
        is_enabled = DEFAULT_COMMAND_COMPLEMENT_ENABLED
    return is_enabled


def disable_cmd_complement(username: str = None, userid: str = None) -> None:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    set_command_complement_enabled(False, userid=userid)


def enable_cmd_complement(username: str = None, userid: str = None) -> None:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    set_command_complement_enabled(True, userid=userid)


def set_random_complement_enabled(is_enabled: bool, username: str = None, userid: str = None) -> None:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(RANDOM_COMPLEMENT_ENABLED).set(is_enabled)


def get_random_complement_enabled(username: str = None, userid: str = None) -> bool:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    is_enabled = USERS_DB_REF.child(userid).child(RANDOM_COMPLEMENT_ENABLED).get()
    if is_enabled is None:
        set_random_complement_enabled(DEFAULT_RANDOM_COMPLEMENT_ENABLED, userid=userid)
        is_enabled = DEFAULT_RANDOM_COMPLEMENT_ENABLED
    return is_enabled


def disable_random_complement(username: str = None, userid: str = None) -> None:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    set_random_complement_enabled(False, userid=userid)


def enable_random_complement(username: str = None, userid: str = None) -> None:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    set_random_complement_enabled(True, userid=userid)


def add_complement(complement: str, username: str = None, userid: str = None) -> None:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    def add_transaction(data):
        if data is None:
            data = []
        data.append(complement)
        return data

    USERS_DB_REF.child(userid).child(CUSTOM_COMPLEMENTS).transaction(add_transaction)


def remove_chars(some_str: str, regex: str = r"[^a-z0-9]") -> str:
    return re.sub(regex, "", some_str.lower())


def complements_to_remove(data: list[str], phrase: str) -> Tuple[list[str], list[str]]:
    if data is None:
        data = []

    leftover_comps = []
    removed_comps = []
    for comp in data:
        comp_edit = remove_chars(comp)
        if phrase in comp_edit:
            removed_comps.append(comp)
        else:
            leftover_comps.append(comp)

    return removed_comps, leftover_comps


def remove_complements(username: str = None, userid: str = None, to_keep: Optional[list[str]] = None, to_remove: Optional[list[str]] = None) -> None:
    # either provide to_remove or to_keep; if both given, to_remove takes precedence
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    def remove_transaction(data):
        if to_remove:
            for comp in to_remove:
                data.remove(comp)
            return data
        return to_keep or []

    USERS_DB_REF.child(userid).child(CUSTOM_COMPLEMENTS).transaction(remove_transaction)


def remove_all_complements(username: str = None, userid: str = None) -> None:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(CUSTOM_COMPLEMENTS).delete()


def get_custom_complements(username: str = None, userid: str = None) -> list[str]:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    complements = USERS_DB_REF.child(userid).child(CUSTOM_COMPLEMENTS).get()
    return complements or []


def set_mute_prefix(prefix: str, username: str = None, userid: str = None) -> None:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(MUTE_PREFIX).set(prefix)


def get_mute_prefix(username: str = None, userid: str = None) -> str:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    prefix = USERS_DB_REF.child(userid).child(MUTE_PREFIX).get()
    if prefix is None:
        return DEFAULT_TTS_IGNORE_PREFIX
    return prefix


def is_cmd_complement_muted(username: str = None, userid: str = None) -> bool:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    is_muted = USERS_DB_REF.child(userid).child(COMMAND_COMPLEMENT_MUTED).get()
    if is_muted is None:
        return DEFAULT_COMMAND_COMPLEMENT_MUTED
    return is_muted


def mute_cmd_complement(username: str = None, userid: str = None) -> None:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(COMMAND_COMPLEMENT_MUTED).set(True)


def unmute_cmd_complement(username: str = None, userid: str = None) -> None:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(COMMAND_COMPLEMENT_MUTED).set(False)


def is_random_complement_muted(username: str = None, userid: str = None) -> bool:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    is_muted = USERS_DB_REF.child(userid).child(RANDOM_COMPLEMENT_MUTED).get()
    if is_muted is None:
        return DEFAULT_RANDOM_COMPLEMENT_MUTED
    return is_muted


def mute_random_complement(username: str = None, userid: str = None) -> None:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(RANDOM_COMPLEMENT_MUTED).set(True)


def unmute_random_complement(username: str = None, userid: str = None) -> None:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(RANDOM_COMPLEMENT_MUTED).set(False)


def are_default_complements_enabled(username: str = None, userid: str = None) -> bool:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    is_enabled = USERS_DB_REF.child(userid).child(DEFAULT_COMPLEMENTS_ENABLED).get()
    if is_enabled is None:
        return DEFAULT_DEFAULT_COMPLEMENTS_ENABLED
    return is_enabled


def enable_default_complements(username: str = None, userid: str = None) -> None:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(DEFAULT_COMPLEMENTS_ENABLED).set(True)


def enable_custom_complements(username: str = None, userid: str = None) -> None:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(CUSTOM_COMPLEMENTS_ENABLED).set(True)


def are_custom_complements_enabled(username: str = None, userid: str = None) -> bool:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    is_enabled = USERS_DB_REF.child(userid).child(CUSTOM_COMPLEMENTS_ENABLED).get()
    if is_enabled is None:
        return DEFAULT_CUSTOM_COMPLEMENTS_ENABLED
    return is_enabled


def disable_custom_complements(username: str = None, userid: str = None) -> None:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(CUSTOM_COMPLEMENTS_ENABLED).set(False)


def disable_default_complements(username: str = None, userid: str = None) -> None:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(DEFAULT_COMPLEMENTS_ENABLED).set(False)


def is_ignoring_bots(username: str = None, userid: str = None) -> bool:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    is_ignoring = USERS_DB_REF.child(userid).child(SHOULD_IGNORE_BOTS).get()
    if is_ignoring is None:
        return DEFAULT_SHOULD_IGNORE_BOTS
    return is_ignoring


def ignore_bots(username: str = None, userid: str = None) -> None:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(SHOULD_IGNORE_BOTS).set(True)


def unignore_bots(username: str = None, userid: str = None) -> None:
    assert username or userid
    if not userid:
        userid = name_to_id(username)
    USERS_DB_REF.child(userid).child(SHOULD_IGNORE_BOTS).set(False)
