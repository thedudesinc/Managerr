import datetime
import sqlite3
from sqlite3 import Error
from discord.ext.tasks import loop
from requests import Session
from plexapi.server import PlexServer
from datetime import timedelta
import logging

database = r"BotDB.db"
logging.basicConfig(filename='updateactivityfromplex.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)

def getListOfPlexServers(conn):
    try:
        cur = conn.cursor()
        cur.execute('select * from PlexServerConfiguration')
        listOfPlexServers = cur.fetchall()
    except Exception as e:
        logging.error('Exception from getListOfPlexServers: ' + str(e))
    return listOfPlexServers


def updateActiveToFalseForPlexEmailAddress(conn, email):
    activeText = "FALSE"
    try:
        cur = conn.cursor()
        cur.execute('UPDATE Users SET active =(?) WHERE plexEmailAddress =(?)', (activeText, email,))
    except Exception as e:
        logging.error('error from updateCommandPrefix: ' + str(e))
    return


def updateActiveToTrueForPlexEmailAddress(conn, email):
    activeText = "TRUE"
    try:
        cur = conn.cursor()
        cur.execute('UPDATE Users SET active =(?) WHERE plexEmailAddress =(?)', (activeText, email,))
    except Exception as e:
        logging.error('error from updateCommandPrefix: ' + str(e))
    return


try:
    DB_CONNECTION = sqlite3.connect(database)
except Error as e:
    logging.debug(f"error from creating DB_CONNECTION: {str(e)}")

with DB_CONNECTION:
    plexServers = getListOfPlexServers(DB_CONNECTION)
for server in plexServers:
    localSession = Session()
    localSession.verify = False
    if not localSession.verify:
        # Disable the warning that the request is insecure, we know that...
        from urllib3 import disable_warnings
        from urllib3.exceptions import InsecureRequestWarning
        disable_warnings(InsecureRequestWarning)

    try:
        SERVER = PlexServer(baseurl=server[2], token=server[3], session=localSession)
        ACCOUNT = SERVER.myPlexAccount()
    except Exception as e:
        logging.error('error getting server object: ' + str(e))

    UserObjects = ACCOUNT.users()

    dateForMinDate = datetime.datetime.now() - timedelta(days=int(server[8]))
    # print("Now: " + str(datetime.datetime.now()) + " and 14 days ago: " + str(dateForMinDate))

    logging.debug("Start time for this process: " + str(datetime.datetime.now()))
    for user in UserObjects:
        userHistory = user.history(maxresults=1, mindate=dateForMinDate)
        if len(userHistory) <= 0:
            print(user.username + ", " + str(user.email) + ", has not watched anything within the last 14 days and should be removed")
            with DB_CONNECTION:
                updateActiveToFalseForPlexEmailAddress(DB_CONNECTION, user.email)
        if len(userHistory) > 0:
            with DB_CONNECTION:
                updateActiveToTrueForPlexEmailAddress(DB_CONNECTION, user.email)
    logging.debug("end time for this process: " + str(datetime.datetime.now()))


