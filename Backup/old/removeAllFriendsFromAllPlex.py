import datetime
import sqlite3
from sqlite3 import Error
import discord
from discord.ext.tasks import loop
from requests import Session
from plexapi.server import PlexServer

plexBaseURL = 'http://192.168.1.137:32400/'
plexToken = 'o2TBVzGonCtHjfcMpKvZ'

localSession = Session()
localSession.verify = False
if not localSession.verify:
    # Disable the warning that the request is insecure, we know that...
    from urllib3 import disable_warnings
    from urllib3.exceptions import InsecureRequestWarning
    disable_warnings(InsecureRequestWarning)

try:
    SERVER = PlexServer(baseurl=plexBaseURL, token=plexToken, session=localSession)
    ACCOUNT = SERVER.myPlexAccount()
except Exception as e:
    print('error getting server object: ' + str(e))

# get list of all users for this plex server
PLEX_USERS_EMAIL = {user.email: user.username for user in ACCOUNT.users()}
PLEX_USERS_ID = {user.email: user.id for user in ACCOUNT.users()}

# remove all users in while loop
listLength = len(PLEX_USERS_EMAIL)
incrementMe = 0
while incrementMe < listLength:
    try:
        # ACCOUNT.removeFriend(list(PLEX_USERS_EMAIL)[incrementMe])
        # print("removed user ID, email: " + str(list(PLEX_USERS_EMAIL)[incrementMe]) + ", "
        #      + str(list(PLEX_USERS_EMAIL.values())[incrementMe]))
        thingEmail = str(list(PLEX_USERS_EMAIL)[incrementMe])
        thingUsername = str(list(PLEX_USERS_EMAIL.values())[incrementMe])
        thingID = str(list(PLEX_USERS_ID.values())[incrementMe])
        print("email: " + thingEmail + ", username: " + thingUsername + ", ID: " + thingID)
        incrementMe += 1
    except Exception as e:
        incrementMe += 1
        # print("Exception removing user id, email. " + str(list(PLEX_USERS_EMAIL)[incrementMe]) + ", "
        #      + str(list(PLEX_USERS_EMAIL.values())[incrementMe]) + " Exception: " + str(e))

