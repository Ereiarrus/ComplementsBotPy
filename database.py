from firebase_admin import credentials, firestore, db
import firebase_admin
import os

cred = credentials.Certificate("./.firebase_config.json")
# firebase_admin.initialize_app(cred)
databaseURL = os.environ['DATABASE_URL']
firebase_admin.initialize_app(cred, {'databaseURL': databaseURL})
ignored_path = "/Ignored"
ignored_ref = db.reference(ignored_path)
users_path = "/Users"
users_ref = db.reference(users_path)


DEFAULT_COMPLEMENT_CHANCE = 10.0 / 3.0
DEFAULT_SHOULD_IGNORE_BOTS = True


def is_user_ignored(user):
    return user in ignored_ref


def ignore(user):
    users_ref.push(user)


def unignore(user):
    db.reference(ignored_path + "/" + user).delete()


def join_channel(user):
    return


def leave_channel(user):
    return


def get_channels():
    return


def number_of_joined_channels():
    # TODO: make sure to NOT count the ones which have left, but not deleted!
    return


def get_tts_ignore_prefix(user):
    return


def get_chance(user):
    return


def ignore_bots(user):
    return
