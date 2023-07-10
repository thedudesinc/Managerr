import discord
from discord.ext import commands, tasks
import datetime
from datetime import timedelta
import asyncio
from requests import Session
from plexapi.server import PlexServer
import logging
import sqlite3
from sqlite3 import Error
import sys
import os
import io
from io import StringIO
import configparser

# region PREBOT
# region VARIABLES
config = configparser.ConfigParser()
config.read("bot.config")
# GUILD_ID = int(config.get("botconfig", "guildid"))
GUILD_ID = 1045433182822072390
ANNOUNCEMENT_CHANNEL_ID = 1045449645876334724
# ANNOUNCEMENT_CHANNEL_ID = int(config.get("botconfig", "announcementchannelid"))
database = r"BotDB.db"
# database = config.get("botconfig", "databasename")
DB_CONNECTION = None
botConfigured = None
# endregion

# region METHODS
def createDB(conn):
    try:
        sqlBotActionHistory = ''' CREATE TABLE IF NOT EXISTS "BotActionHistory" 
            ("action" TEXT, "dateTime" TEXT, "automaticOrManual" TEXT); '''
        cur1 = conn.cursor()
        cur1.execute(sqlBotActionHistory)
        sqlBotCommand = ''' CREATE TABLE IF NOT EXISTS "BotCommands" 
            ( "commandName" TEXT UNIQUE, "commandReturnMessage" TEXT, "isAdminCommand" INTEGER); '''
        cur2 = conn.cursor()
        cur2.execute(sqlBotCommand)
        sqlBotConfig = ''' CREATE TABLE IF NOT EXISTS "BotConfiguration" 
            ("administratorDiscordID" TEXT, "botAdminDiscordRole" TEXT, "botChannelID" TEXT, "queuedRole" TEXT, 
            "removedRole" TEXT, "commandPrefix" TEXT NOT NULL DEFAULT '!!!', "configured" TEXT DEFAULT 'False', 
            "botNotificationsChannelID" TEXT); '''
        cur3 = conn.cursor()
        cur3.execute(sqlBotConfig)
        sqlCommandHistory = ''' CREATE TABLE IF NOT EXISTS "CommandHistory" 
            ("commandName" TEXT NOT NULL, "discordServerNickname" TEXT NOT NULL, "discordUsername" TEXT NOT NULL, 
            "discordID" TEXT NOT NULL, "dateTime" TEXT NOT NULL, "valueSent" TEXT); '''
        cur4 = conn.cursor()
        cur4.execute(sqlCommandHistory)
        sqlPlexServerConfiguration = ''' CREATE TABLE IF NOT EXISTS "PlexServerConfiguration" 
            ("psc_PK" INTEGER NOT NULL UNIQUE, "serverName" TEXT NOT NULL UNIQUE, "serverURL" TEXT NOT NULL UNIQUE, 
            "serverToken" TEXT NOT NULL UNIQUE, "checksInactivity" TEXT, "invitedDiscordRole" TEXT, "tautulliURL" TEXT, 
            "tautulliAPIKey" TEXT, "inactivityLimit" TEXT, "inviteAcceptanceLimit" TEXT, 
            PRIMARY KEY("psc_PK" AUTOINCREMENT)); 
            '''
        cur5 = conn.cursor()
        cur5.execute(sqlPlexServerConfiguration)
        sqlUsers = ''' CREATE TABLE IF NOT EXISTS "Users" 
            ("u_PK" INTEGER NOT NULL UNIQUE, "discordID" TEXT NOT NULL UNIQUE, "discordUsername" TEXT, "discordServerNickname"	TEXT, "plexUsername" TEXT DEFAULT 'UNKNOWN', "plexEmailAddress" TEXT NOT NULL UNIQUE, "serverName" TEXT, "dateRemoved" TEXT, "dateInvited" TEXT, "dateQueued" TEXT, "status" TEXT, "plexUserID" TEXT DEFAULT 'UNKNOWN', "active" TEXT DEFAULT 'TRUE', PRIMARY KEY("u_PK" AUTOINCREMENT)); '''
        cur6 = conn.cursor()
        cur6.execute(sqlUsers)
    except Exception as e:
        logging.error('Exception from createDBTables: ' + str(e))
    return


def restart_bot():
    os.execv(sys.executable, ['python'] + sys.argv)


def getBotChannelID(conn):
    try:
        botChannelID = ""
        cur = conn.cursor()
        cur.execute('select botChannelID from BotConfiguration')
        rows = cur.fetchall()
        if len(rows) == 1:
            rowTuple = rows[0]
            botChannelID = str(rowTuple[0])
    except Exception as e:
        logging.error('Exception from getBotChannelID: ' + str(e))
    return botChannelID


def getBotConfiguredBool(conn):
    try:
        botConfiguredBool = False
        cur = conn.cursor()
        cur.execute('select configured from BotConfiguration')
        rows = cur.fetchall()
        if len(rows) == 1:
            rowTuple = rows[0]
            value = str(rowTuple[0])
            if str(value) == 'TRUE':
                botConfiguredBool = True
            else:
                botConfiguredBool = False
    except Exception as e:
        logging.error('Exception from getBotConfiguredBool: ' + str(e))
    return botConfiguredBool


def getCommandPrefix(conn):
    try:
        commandPrefix = ""
        cur = conn.cursor()
        cur.execute('select commandPrefix from BotConfiguration')
        rows = cur.fetchall()
        if len(rows) == 1:
            rowTuple = rows[0]
            commandPrefix = str(rowTuple[0])
    except Exception as e:
        logging.error('Exception from getCommandPrefix: ' + str(e))
    return commandPrefix


def configureBot(conn, values):
    sql = ''' INSERT INTO BotConfiguration(administratorDiscordID,botAdminDiscordRole,botChannelID,queuedRole,
                removedRole,commandPrefix,configured,botNotificationsChannelID) 
                VALUES(?,?,?,?,?,?,?,?) '''
    try:
        cur = conn.cursor()
        cur.execute(sql, values)
    except Exception as e:
        logging.error('Error from configureBot: ' + str(e))
    return


def recordCommandHistory(conn, values):
    sql = ''' INSERT INTO CommandHistory(commandName,discordServerNickname,discordUsername,discordID,dateTime,valueSent) 
                    VALUES(?,?,?,?,?,?) '''
    try:
        cur = conn.cursor()
        cur.execute(sql, values)
    except Exception as e:
        logging.error('error from recordCommandHistory ' + str(e))
    return


def recordBotActionHistory(conn, actionText, autoOrMan):
    date1 = str(datetime.datetime.now())
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO BotActionHistory(action,dateTime,automaticOrManual) VALUES(?,?,?)',
                    (actionText, date1, autoOrMan,))
    except Exception as e:
        logging.error('error from recordBotActionHistory: ' + str(e))
    return


def recordPlexServerEntry(conn, values):
    sql = ''' INSERT INTO PlexServerConfiguration(serverName,serverURL,serverToken,checksInactivity,invitedDiscordRole,
    tautulliURL,tautulliAPIKey,inactivityLimit,inviteAcceptanceLimit) VALUES(?,?,?,?,?,?,?,?,?) '''
    try:
        cur = conn.cursor()
        cur.execute(sql, values)
    except Exception as e:
        logging.error('error from recordCommandHistory' + str(e))
    return


def getAdminDiscordID(conn):
    try:
        adminDiscordID = ""
        cur = conn.cursor()
        cur.execute('select administratorDiscordID from BotConfiguration')
        rows = cur.fetchall()
        if len(rows) == 1:
            rowTuple = rows[0]
            adminDiscordID = str(rowTuple[0])
    except Exception as e:
        logging.error('Exception from getAdminDiscordID: ' + str(e))
    return adminDiscordID


def getNewestPlexServer(conn):
    try:
        newestPlexServer = ""
        cur = conn.cursor()
        cur.execute('select 1 serverName from PlexServerConfiguration order by psc_PK')
        rows = cur.fetchall()
        if len(rows) == 1:
            rowTuple = rows[0]
            newestPlexServer = str(rowTuple[0])
    except Exception as e:
        logging.error('Exception from getNewestPlexServer: ' + str(e))
    return newestPlexServer


def getListOfPlexServers(conn):
    try:
        cur = conn.cursor()
        cur.execute('select * from PlexServerConfiguration')
        listOfPlexServers = cur.fetchall()
    except Exception as e:
        logging.error('Exception from getListOfPlexServers: ' + str(e))
    return listOfPlexServers


def getUsersListFromDB(conn):
    try:
        cur = conn.cursor()
        cur.execute('select * from Users')
        listOfUsers = cur.fetchall()
    except Exception as e:
        logging.error('Exception from getUsersListFromDB: ' + str(e))
    return listOfUsers


def getPlexServerConfigInfoForName(conn, serverName):
    try:
        plexServerConfigInfo = []
        cur = conn.cursor()
        cur.execute('select * from PlexServerConfiguration where serverName =(?)', (str(serverName),))
        rows = cur.fetchall()
        if len(rows) == 1:
            plexServerConfigInfo = rows[0]
    except Exception as e:
        logging.error('Exception from getPlexServerConfigInfoForName: ' + str(e))
    return plexServerConfigInfo


def getBotConfigurationInfo(conn):
    try:
        botConfigInfo = []
        cur = conn.cursor()
        cur.execute('select * from BotConfiguration')
        rows = cur.fetchall()
        if len(rows) == 1:
            botConfigInfo = rows[0]
    except Exception as e:
        logging.error('Exception from getBotConfigurationInfo: ' + str(e))
    return botConfigInfo


def getDBInfoForDiscordID(conn, discordID):
    try:
        dbInfo = []
        cur = conn.cursor()
        cur.execute('select * from Users where discordID =(?)', (str(discordID),))
        rows = cur.fetchall()
        if len(rows) == 1:
            dbInfo = rows[0]
    except Exception as e:
        logging.error('Exception from getDBInfoForDiscordID: ' + str(e))
    return dbInfo


def getUserCountForPlexServerName(conn, serverName):
    userCountForPlexServerName = 9000
    localSession = Session()
    localSession.verify = False
    if not localSession.verify:
        # Disable the warning that the request is insecure, we know that...
        from urllib3 import disable_warnings
        from urllib3.exceptions import InsecureRequestWarning
        disable_warnings(InsecureRequestWarning)
    plexServerInfo = getPlexServerConfigInfoForName(conn, str(serverName))
    if len(plexServerInfo) == 10:
        try:
            Server = PlexServer(baseurl=str(plexServerInfo[2]), token=str(plexServerInfo[3]), session=localSession)
            Account = Server.myPlexAccount()
            # dont need to upper email here since it is used for a count.
            PLEX_USERS = {user.email: user.username for user in Account.users()}
            pendingInvites = Account.pendingInvites(includeSent=True, includeReceived=False)
            pendingInvitesCount = len(pendingInvites)
            userCountForPlexServerName = (len(PLEX_USERS) + pendingInvitesCount)
        except Exception as e:
            logging.debug('Exception from getUserCountForPlexServerName: ' + str(e))

    else:
        print('didnt get back a whole row from plex server config info')
    return userCountForPlexServerName


def getFirstPlexServerNameWithOpenSpots(conn):
    try:
        firstPlexServerNameWithOpenSpots = ""
        plexServers = getListOfPlexServers(conn)
        for server in plexServers:
            userCount = getUserCountForPlexServerName(conn, str(server[1]))
            if userCount < 100 and userCount < 9000:
                firstPlexServerNameWithOpenSpots = str(server[1])
                break
    except Exception as e:
        logging.error('Exception from getFirstPlexServerNameWithOpenSpots: ' + str(e))
    return firstPlexServerNameWithOpenSpots


def cancelPendingInvitesOverXDays(days):
    localSession = Session()
    localSession.verify = False
    if not localSession.verify:
        # Disable the warning that the request is insecure, we know that...
        from urllib3 import disable_warnings
        from urllib3.exceptions import InsecureRequestWarning
        disable_warnings(InsecureRequestWarning)
    for server in getListOfPlexServers(DB_CONNECTION):
        plexServerInfo = getPlexServerConfigInfoForName(DB_CONNECTION, str(server[1]))
        if len(plexServerInfo) == 10:
            try:
                Server = PlexServer(baseurl=str(plexServerInfo[2]), token=str(plexServerInfo[3]), session=localSession)
                Account = Server.myPlexAccount()
                pendingInvites = Account.pendingInvites(includeSent=True, includeReceived=False)
                try:
                    for invite in pendingInvites:
                        if str(invite) != '<MyPlexInvite:nan>':
                            if invite.createdAt < datetime.datetime.now() - datetime.timedelta(days=days):
                                # dont need to upper email here because it is being pulled directly from the invite object.
                                Account.cancelInvite(str(invite.email))
                except Exception as e:
                    # dont need to upper email here because it is being printed directly from invite object.
                    logging.debug('Exception from cancelPendingInvitesOverXDays for invite email: '
                          + str(invite.email) + ', server:' + str(invite.servers) + ', error: ' + str(e))
                    continue
            except Exception as e:
                logging.debug('Exception from server loop of cancelPendingInvitesOverXDays' + str(e))
                continue
        else:
            print("didnt get a whole row from the database")
    return


def cancelPendingInviteForDiscordID(conn, discordID):
    localSession = Session()
    localSession.verify = False
    if not localSession.verify:
        # Disable the warning that the request is insecure, we know that...
        from urllib3 import disable_warnings
        from urllib3.exceptions import InsecureRequestWarning
        disable_warnings(InsecureRequestWarning)
    userInfo = getDBInfoForDiscordID(conn, discordID)
    serverName = userInfo[6]
    plexServerInfo = getPlexServerConfigInfoForName(DB_CONNECTION, serverName)
    if len(plexServerInfo) == 10:
        try:
            Server = PlexServer(baseurl=str(plexServerInfo[2]), token=str(plexServerInfo[3]), session=localSession)
            Account = Server.myPlexAccount()
            pendingInvites = Account.pendingInvites(includeSent=True, includeReceived=False)
            for invite in pendingInvites:
                # upper invite here because we are comparing it to the value from the database which is stored upper.
                if invite.email == userInfo[5]:
                    Account.cancelInvite(invite)
                    break
        except Exception as e:
            logging.debug('Exception from cancelPendingInviteForDiscordID: ' + str(e))
    else:
        print("didnt get a whole row from the database")
    return


def listAllPendingInvites():
    allPendingInvites = []
    localSession = Session()
    localSession.verify = False
    if not localSession.verify:
        # Disable the warning that the request is insecure, we know that...
        from urllib3 import disable_warnings
        from urllib3.exceptions import InsecureRequestWarning
        disable_warnings(InsecureRequestWarning)
    for server in getListOfPlexServers(DB_CONNECTION):
        plexServerInfo = getPlexServerConfigInfoForName(DB_CONNECTION, str(server[1]))
        if len(plexServerInfo) == 10:
            try:
                Server = PlexServer(baseurl=str(plexServerInfo[2]), token=str(plexServerInfo[3]), session=localSession)
                Account = Server.myPlexAccount()
                pendingInvites = Account.pendingInvites(includeSent=True, includeReceived=False)
                for invite in pendingInvites:
                    allPendingInvites.append(invite)
            except Exception as e:
                logging.debug('Exception from listAllPendingInvites: ' + str(e))
        else:
            print("didnt get a whole row from the database for that serverName")
    return allPendingInvites


def updateBotChannelID(conn, values):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE BotConfiguration SET botChannelID =(?) WHERE administratorDiscordID =(?)', values)
    except Exception as e:
        logging.error(f"exception from updatebotchannelid: {str(e)}")
    return


def updateCommandPrefix(conn, values):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE BotConfiguration SET commandPrefix =(?) WHERE administratorDiscordID =(?)', values)
    except Exception as e:
        logging.error(f"Exception from updatecommandprefix: {str(e)}")
    return


def updateInactivityForServerName(conn, serverName, days):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE PlexServerConfiguration SET inactivityLimit =(?) WHERE serverName =(?)',
                    (str(days), str(serverName),))
    except Exception as e:
        logging.error(f"Exception from updateInactivityForServerName: {str(e)}")
    return


def updateInviteAcceptanceLimitForServerName(conn, serverName, days):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE PlexServerConfiguration SET inviteAcceptanceLimit =(?) WHERE serverName =(?)',
                    (str(days), str(serverName),))
    except Exception as e:
        logging.error(f"Exception from updateInviteAcceptanceLimitForServerName: {str(e)}")
    return


def updateTautulliURLForServerName(conn, serverName, url):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE PlexServerConfiguration SET tautulliURL =(?) WHERE serverName =(?)',
                    (str(url), str(serverName),))
    except Exception as e:
        logging.error('Exception from updateTautulliURLForServerName: ' + str(e))
    return


def updateTautulliAPIKeyForServerName(conn, serverName, apikey):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE PlexServerConfiguration SET tautulliAPIKey =(?) WHERE serverName =(?)',
                    (str(apikey), str(serverName),))
    except Exception as e:
        logging.error('Exception from updateTautulliAPIKeyForServerName: ' + str(e))
    return


def updateServerURLForServerName(conn, serverName, serverURL):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE PlexServerConfiguration SET serverURL =(?) WHERE serverName =(?)',
                    (str(serverURL), str(serverName),))
    except Exception as e:
        logging.error('Exception from updateServerURLForServerName: ' + str(e))
    return


def updateServerTokenForServerName(conn, serverName, serverToken):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE PlexServerConfiguration SET serverToken =(?) WHERE serverName =(?)',
                    (str(serverToken), str(serverName),))
    except Exception as e:
        logging.error('Exception from updateServerTokenForServerName: ' + str(e))
    return


def getListOfPlexThatChecks(conn):
    try:
        yesString = 'YES'
        cur = conn.cursor()
        cur.execute('select * from PlexServerConfiguration where checksInactivity = (?)', (yesString,))
        plexChecksList = cur.fetchall()
    except Exception as e:
        logging.error('Exception from getListOfPlexThatChecks: ' + str(e))
    return plexChecksList


def getInactiveUsersPlexIDS(conn):
    try:
        trueString = 'FALSE'
        rDict = {}
        cur = conn.cursor()
        cur.execute('select plexUserID, plexEmailAddress from Users where active = (?)', (trueString,))
        inactiveUsersPlexIDS = cur.fetchall()
        for x in inactiveUsersPlexIDS:
            # .update function to append the values to the dictionary
            rDict.update({str(x[0]): x[1]})
    except Exception as e:
        logging.error(f"Exception from getInactiveUsersPlexIDS: {str(e)}")
    return rDict


def updateChecksInactivityForServerName(conn, serverName, checks):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE PlexServerConfiguration SET checksInactivity =(?) WHERE serverName =(?)',
                    (str(checks), str(serverName),))
    except Exception as e:
        logging.error('Exception from updateChecksInactivityForServerName: ' + str(e))
    return


def updateEmailForDiscordID(conn, discordID, newEmail):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE Users SET plexEmailAddress =(?) WHERE discordID =(?)', (str(newEmail), str(discordID),))
    except Exception as e:
        logging.error('Exception from updateEmailForDiscordID: ' + str(e))
    return


def updateStatusForDiscordID(conn, discordID, status):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE Users SET status =(?) WHERE discordID =(?)', (str(status), str(discordID),))
    except Exception as e:
        logging.error('Exception from updateStatusForDiscordID: ' + str(e))
    return


def setRemovalDateForDiscordID(conn, discordID):
    dateNowString = str(datetime.datetime.now())
    try:
        cur = conn.cursor()
        cur.execute('UPDATE Users SET dateRemoved =(?) WHERE discordID =(?)', (dateNowString, str(discordID),))
    except Exception as e:
        logging.error('Exception from setRemovalDateForDiscordID: ' + str(e))
    return


def updateBotActionHistory(conn, values):
    sql = ''' INSERT INTO BotActionHistory(action,dateTime,automaticOrManual) VALUES(?,?,?) '''
    cur = conn.cursor()
    try:
        cur.execute(sql, values)
    except Exception as e:
        logging.error('Exception from updateBotActionHistory: ' + str(e))
    return


def updateUsernameForPlexEmailAddress(conn, email, username):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE Users SET plexUsername =(?) WHERE plexEmailAddress =(?)', (str(username), str(email),))
    except Exception as e:
        logging.error('Exception from updateUsernameForPlexEmailAddress: ' + str(e))
    return


def updatePlexIDForPlexEmailAddress(conn, email, plexID):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE Users SET plexUserID =(?) WHERE plexEmailAddress =(?)', (str(plexID), str(email),))
    except Exception as e:
        logging.error('Exception from updatePlexIDForPlexEmailAddress: ' + str(e))
    return


def updateQueuedUserToInvited(conn, values):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE Users SET serverName =(?), dateInvited =(?), status =(?) WHERE discordID =(?)',
                    (str(values[1]), str(values[2]), str(values[3]), str(values[0]),))
    except Exception as e:
        logging.error('Exception from updateQueuedUserToInvited: ' + str(e))
    return


def getStatusForDiscordID(conn, discordID):
    try:
        statusForDiscordID = ''
        cur = conn.cursor()
        cur.execute('select status from Users where discordID = (?)', (str(discordID),))
        rows = cur.fetchall()
        if len(rows) == 1:
            rowTuple = rows[0]
            statusForDiscordID = str(rowTuple[0])
    except Exception as e:
        logging.error('Exception from getStatusForDiscordID: ' + str(e))
    return statusForDiscordID


def getEmailForDiscordID(conn, discordID):
    try:
        emailForDiscordID = ''
        cur = conn.cursor()
        cur.execute('select plexEmailAddress from Users where discordID = (?)', (str(discordID),))
        rows = cur.fetchall()
        if len(rows) == 1:
            rowTuple = rows[0]
            emailForDiscordID = str(rowTuple[0])
    except Exception as e:
        logging.error('Exception from getEmailForDiscordID: ' + str(e))
    return emailForDiscordID


def getTotalOpenSpots(conn):
    try:
        totalOpenSpotsCount = 0
        plexServers = getListOfPlexServers(conn)
        for server in plexServers:
            userCount = getUserCountForPlexServerName(conn, str(server[1]))
            if userCount < 101:
                totalOpenSpotsCount += (100 - userCount)
            else:
                totalOpenSpotsCount = 9000
    except Exception as e:
        logging.error('Exception from getTotalOpenSpots: ' + str(e))
    return totalOpenSpotsCount


def checkDiscordIDExists(conn, discordID):
    try:
        cur = conn.cursor()
        cur.execute('select * from Users where discordID = (?)', (str(discordID),))
        rows = cur.fetchall()
        if len(rows) == 1:
            discordIDExists = True
        else:
            discordIDExists = False
    except Exception as e:
        logging.error('Exception from checkDiscordIDExists: ' + str(e))
    return discordIDExists


def insertInvitedUser(conn, values):
    sql = ''' INSERT INTO Users(discordID,discordUsername,discordServerNickname,plexUsername,plexEmailAddress,
        serverName,dateInvited,status) VALUES(?,?,?,?,?,?,?,?) '''
    try:
        cur = conn.cursor()
        cur.execute(sql, values)
    except Exception as e:
        logging.error('Exception from insertInvitedUser' + str(e) + " values: " + str(values))
    return


def insertQueuedUser(conn, values):
    sql = ''' INSERT INTO Users(discordID,discordUsername,plexEmailAddress,dateQueued,status) VALUES(?,?,?,?,?) '''
    try:
        cur = conn.cursor()
        cur.execute(sql, values)
    except Exception as e:
        logging.error('Exception from insertQueuedUser' + str(e))
    return


def inviteEmailToPlex(conn, email, values):
    localSession = Session()
    localSession.verify = False
    if not localSession.verify:
        # Disable the warning that the request is insecure, we know that...
        from urllib3 import disable_warnings
        from urllib3.exceptions import InsecureRequestWarning
        disable_warnings(InsecureRequestWarning)
    cur = conn.cursor()
    cur.execute('select * from PlexServerConfiguration where serverName like(?)', (str(values[3]),))
    rows = cur.fetchall()
    rowTuple = rows[0]
    plex = PlexServer(rowTuple[2], rowTuple[3], localSession)
    sections_lst = [x.title for x in plex.library.sections()]
    inviteSuccess = False
    date1 = datetime.datetime.now()
    try:
        plex.myPlexAccount().inviteFriend(user=email, server=plex, sections=sections_lst, allowSync=None,
                                          allowCameraUpload=None, allowChannels=None, filterMovies=None,
                                          filterTelevision=None, filterMusic=None)
        inviteSuccess = True
    except Exception as e:
        logging.error('Exception from inviteEmailToPlex: ' + str(e))
        inviteSuccess = False
    if inviteSuccess:
        try:
            with DB_CONNECTION:
                uValues = (str(values[0]), str(values[1]), str(values[2]), 'UNKNOWN', email, str(values[3]),
                           str(date1), '2')
                insertInvitedUser(DB_CONNECTION, uValues)
        except Exception as e:
            logging.debug('Exception from within invite success: ' + str(e))
    else:

        print("invite success is not true for some reason")
    return inviteSuccess


async def inviteQueuedEmailToPlex(conn, discordID, serverName, email, guildID):
    localSession = Session()
    localSession.verify = False
    if not localSession.verify:
        # Disable the warning that the request is insecure, we know that...
        from urllib3 import disable_warnings
        from urllib3.exceptions import InsecureRequestWarning
        disable_warnings(InsecureRequestWarning)
    cur = conn.cursor()
    cur.execute('select * from PlexServerConfiguration where serverName like(?)', (serverName,))
    rows = cur.fetchall()
    rowTuple = rows[0]
    plex = PlexServer(rowTuple[2], rowTuple[3], localSession)
    sections_lst = [x.title for x in plex.library.sections()]
    inviteSuccess = False
    date1 = datetime.datetime.now()
    try:
        plex.myPlexAccount().inviteFriend(user=email, server=plex, sections=sections_lst, allowSync=None,
                                          allowCameraUpload=None, allowChannels=None, filterMovies=None,
                                          filterTelevision=None, filterMusic=None)
        inviteSuccess = True
    except Exception as e:
        logging.error('Exception from inviteQueuedEmailToPlex: ' + str(e))
        inviteSuccess = False
    if inviteSuccess:
        try:
            serverDiscordRole = rowTuple[5]
            with DB_CONNECTION:
                uValues = (discordID, serverName, str(date1), '2')
                updateQueuedUserToInvited(DB_CONNECTION, uValues)
                # await addRoleForDiscordID(DB_CONNECTION, serverDiscordRole, discordID, guildID, bot)
        except Exception as e:
            logging.debug('Exception from within invite success: ' + str(e))
    else:
        print("invite success is not true for some reason")
    return inviteSuccess


async def addRoleForDiscordID(conn, discordRoleName, discordID, guildID, bot):
    # thisGuild = bot.get_guild(int(guildID))
    if bot == None:
        logging.error(f"bot i was given is None Type")
        return
    else:
        guild = await bot.fetch_guild(int(guildID))
        try:
            print(f"this is the guild ID I was given: {guildID}")
            print(f"This is the guild I got: {str(guild)}")

            member = discord.utils.get(guild.members, id=int(discordID))

            roleToAdd = discord.utils.get(guild.roles, name=discordRoleName)
            if member is not None:
                # await member.add_roles(roleToAdd)
                await member.create_dm()
                # await member.dm_channel.send(discordRoleName + ' role has been added to you.')
                with conn:
                    recordBotActionHistory(conn, 'added role: '
                                        + discordRoleName + ' to discord member: ' + str(member.name), 'AUTOMATIC')
        except Exception as e:
            logging.error('Exception from addRoleForDiscordID: ' + str(e))
        return


async def removeRoleForDiscordID(conn, discordRoleName, discordID, guildID, bot):
    # thisGuild = bot.get_guild(int(guildID))
    if bot == None:
        logging.error(f"guild came back as None type")
        return
    else:
        guild = await bot.fetch_guild(int(guildID))
        try:
            # thisGuild = discord.utils.get_guild(guildID)
            # thisGuild = discord.Object(id=int(guildID))
            member = discord.utils.get(guild.members, id=int(discordID))
            roleToRemove = discord.utils.get(guild.roles, name=discordRoleName)
            if member is not None:
                # await member.remove_roles(roleToRemove)
                await member.create_dm()
                # await member.dm_channel.send(discordRoleName + ' role has been removed from you')
                with conn:
                    recordBotActionHistory(conn, 'removed role: '
                                        + discordRoleName + ' from discord member: ' + str(member.name), 'AUTOMATIC')
            else:
                print('member was None. Probably because they left the server.')
        except Exception as e:
            logging.error('Exception from removeRoleForDiscordID: ' + str(e))
        return


def getDateQueuedForDiscordID(conn, discordID):
    try:
        dateQueued = ""
        cur = conn.cursor()
        cur.execute('select dateQueued from Users where discordID = (?)', (str(discordID),))
        rows = cur.fetchall()
        if len(rows) == 1:
            rowTuple = rows[0]
            dateQueued = str(rowTuple[0])
    except Exception as e:
        logging.error('Exception from getDateQueuedForDiscordID: ' + str(e))
    return dateQueued


def getStatusForEmail(conn, email):
    try:
        statusForEmail = '5'
        cur = conn.cursor()
        cur.execute('select status from Users where plexEmailAddress = (?)', (str(email),))
        rows = cur.fetchall()
        if len(rows) == 1:
            rowTuple = rows[0]
            statusForEmail = str(rowTuple[0])
    except Exception as e:
        logging.error('Exception from getStatusForEmail: ' + str(e))
    return statusForEmail


def getDiscordIDForEmail(conn, email):
    try:
        discordIDForEmail = ""
        cur = conn.cursor()
        cur.execute('select discordID from Users where plexEmailAddress = (?)', (str(email),))
        rows = cur.fetchall()
        if len(rows) == 1:
            rowTuple = rows[0]
            discordIDForEmail = str(rowTuple[0])
    except Exception as e:
        logging.error('Exception from getDiscordIDForEmail: ' + str(e))
    return discordIDForEmail


def getCountQueuedAheadOfDate(conn, dateQueued):
    countQueuedAhead = 0
    cur = conn.cursor()
    try:
        cur.execute('select count() from Users where status = 4 and dateQueued < (?)', (str(dateQueued),))
    except Exception as e:
        logging.error('Exception from getCountQueuedAheadOfDate: ' + str(e))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        countQueuedAhead = rowTuple[0]
    return countQueuedAhead


def getUsersNoUsername(conn):
    try:
        username = 'UNKNOWN'
        rDict = {}
        cur = conn.cursor()
        cur.execute('select plexEmailAddress, plexUsername from Users where plexUsername =(?)', (username,))
        BotPlexUsers = cur.fetchall()
        for x in BotPlexUsers:
            # .update function to append the values to the dictionary
            rDict.update({str(x[0]): x[1]})
    except Exception as e:
        logging.error('Exception from getUsersNoUsername: ' + str(e))
    return rDict


def getUsersNoPlexID(conn):
    try:
        plexID = 'UNKNOWN'
        rDict = {}
        cur = conn.cursor()
        cur.execute('select plexEmailAddress, plexUserID from Users where plexUserID =(?)', (plexID,))
        BotPlexUsers = cur.fetchall()
        for x in BotPlexUsers:
            # .update function to append the values to the dictionary
            rDict.update({str(x[0]): x[1]})
    except Exception as e:
        logging.error('Exception from getUsersNoPlexID: ' + str(e))
    return rDict


def getUsersQueued(conn):
    try:
        rDict = {}
        cur = conn.cursor()
        cur.execute('select discordID, plexEmailAddress from Users where status = 4 order by dateQueued')
        users = cur.fetchall()
        for x in users:
            # .update function to append the values to the dictionary
            rDict.update({str(x[0]): x[1]})
    except Exception as e:
        logging.error('Exception from getUsersQueued: ' + str(e))
    return rDict


def getDiscordIDForOldestQueuedUser(conn):
    try:
        discordIDForOldestQueuedUser = ''
        cur = conn.cursor()
        cur.execute('SELECT discordID FROM Users where status = 4 ORDER BY dateQueued ASC LIMIT 1')
        rows = cur.fetchall()
        if len(rows) == 1:
            rowTuple = rows[0]
            discordIDForOldestQueuedUser = str(rowTuple[0])
    except Exception as e:
        logging.error('Exception from getDiscordIDForOldestQueuedUser: ' + str(e))
    return discordIDForOldestQueuedUser


def getUsernameForDiscordID(conn, discordID):
    try:
        username = ""
        cur = conn.cursor()
        cur.execute('select discordUsername from Users where discordID = (?)', (str(discordID),))
        rows = cur.fetchall()
        if len(rows) == 1:
            rowTuple = rows[0]
            username = str(rowTuple[0])
    except Exception as e:
        logging.error('Exception from getUsernameForDiscordID: ' + str(e))
    return username


def getDateInvitedByEmail(conn, email):
    try:
        dateInvited = ''
        cur = conn.cursor()
        cur.execute('select dateInvited from Users where plexEmailAddress = (?)', (str(email),))
        rows = cur.fetchall()
        if len(rows) == 1:
            rowTuple = rows[0]
            dateInvited = str(rowTuple[0])
    except Exception as e:
        logging.error('Exception from getDateInvitedByEmail: ' + str(e))
    return dateInvited


def time_format(total_seconds):
    # Display user's last history entry
    days = total_seconds // 86400
    hours = (total_seconds - days * 86400) // 3600
    minutes = (total_seconds - days * 86400 - hours * 3600) // 60
    seconds = total_seconds - days * 86400 - hours * 3600 - minutes * 60
    result = ("{} day{}, ".format(days, "s" if days != 1 else "") if days else "") + \
             ("{} hour{}, ".format(hours, "s" if hours != 1 else "") if hours else "") + \
             ("{} minute{}, ".format(minutes, "s" if minutes != 1 else "") if minutes else "") + \
             ("{} second{}, ".format(seconds, "s" if seconds != 1 else "") if seconds else "")
    return result.strip().rstrip(',')


def removeServerNameForDiscordID(conn, discordID):
    try:
        cur = conn.cursor()
        cur.execute('update Users set serverName = NULL where discordID = (?)', (str(discordID),))
    except Exception as e:
        logging.error('Exception from removeServerNameForDiscordID: ' + str(e))
    return


def updateRemovalDateForDiscordID(conn, discordID):
    now = str(datetime.datetime.now())
    try:
        cur = conn.cursor()
        cur.execute('update Users set dateRemoved = (?) where discordID = (?)', (now, str(discordID),))
    except Exception as e:
        logging.error('Exception from updateRemovalDateForDiscordID: ' + str(e))
    return


def getQueueStatusForDiscordID(conn, discordID):
    try:
        dateQueued = getDateQueuedForDiscordID(conn, discordID)
        queuedAhead = getCountQueuedAheadOfDate(conn, dateQueued)
    except Exception as e:
        logging.error('Exception from getQueueStatusForDiscordID: ' + str(e))
    return queuedAhead


def getInvitedDiscordRoleNameForServerName(conn, serverName):
    invitedDiscordRoleName = ''
    try:
        cur = conn.cursor()
        cur.execute('select invitedDiscordRole from PlexServerConfiguration where serverName = (?)', (serverName,))
        rows = cur.fetchall()
        if len(rows) == 1:
            rowTuple = rows[0]
            invitedDiscordRoleName = str(rowTuple[0])
    except Exception as e:
        logging.error('Exception from getInvitedDiscordRoleNameForServerName: ' + str(e))
    return invitedDiscordRoleName


def deleteFromDBForDiscordID(conn, discordID):
    try:
        cur = conn.cursor()
        cur.execute('delete from Users where discordID = (?)', (discordID,))
        recordBotActionHistory(conn, 'deleted from users table by discordID: ' + str(discordID), 'AUTOMATIC')
    except Exception as e:
        logging.error('Exception from deleteFromDBForDiscordID: ' + str(e))
    return


def getPlexUserIDForDiscordID(conn, discordID):
    return


def removeFriendFromPlexByDiscordID(discordID):
    try:
        localSession = Session()
        localSession.verify = False
        if not localSession.verify:
            # Disable the warning that the request is insecure, we know that...
            from urllib3 import disable_warnings
            from urllib3.exceptions import InsecureRequestWarning
            disable_warnings(InsecureRequestWarning)
        with DB_CONNECTION:
            userInfo = getDBInfoForDiscordID(DB_CONNECTION, discordID)
            serverName = userInfo[6]
            plex = getPlexServerConfigInfoForName(DB_CONNECTION, serverName)
            recordBotActionHistory(DB_CONNECTION, 'Removed Friend from Plex by email: ' + str(userInfo[5]), 'AUTOMATIC')
        SERVER = PlexServer(baseurl=str(plex[2]), token=str(plex[3]), session=localSession)
        ACCOUNT = SERVER.myPlexAccount()
        ACCOUNT.removeFriend(userInfo[5])
    except Exception as e:
        logging.error('Exception from removeFriendFromPlex: ' + str(e))
    return


def removeFromTautulliByDiscordID(discordID):
    with DB_CONNECTION:
        userInfo = getDBInfoForDiscordID(DB_CONNECTION, discordID)
        plex = getPlexServerConfigInfoForName(DB_CONNECTION, userInfo[6])
        TAUTULLI_APIKEY = plex[7]
        TAUTULLI_URL = plex[6]
        plexUserID = userInfo[11]
        recordBotActionHistory(DB_CONNECTION, 'Removed user from Tautulli by ID: ' + str(userInfo[11]), 'AUTOMATIC')
    localSession = Session()
    localSession.verify = False
    if not localSession.verify:
        # Disable the warning that the request is insecure, we know that...
        from urllib3 import disable_warnings
        from urllib3.exceptions import InsecureRequestWarning
        disable_warnings(InsecureRequestWarning)
    PARAMS1 = {
        'cmd': 'delete_all_user_history',
        'user_id': plexUserID,
        'apikey': TAUTULLI_APIKEY
    }
    # SESSION.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=PARAMS).json()
    try:
        localSession.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=PARAMS1).json()
    except Exception as e:
        print("Tautulli API 'delete_user' request failed. Error: {}.".format(e))
    return


async def deleteFromPlexTautulliAndDB(conn, discordID):
    try:
        # remove from plex
        removeFriendFromPlexByDiscordID(discordID)
        # remove watch history from tautulli
        removeFromTautulliByDiscordID(discordID)
        # remove invited role and add removed role
        userinfo = getDBInfoForDiscordID(conn, discordID)
        invitedrolename = getInvitedDiscordRoleNameForServerName(conn, userinfo[6])
        # await removeRoleForDiscordID(conn, invitedrolename, discordID, GUILD_ID, bot)
        botinfo = getBotConfigurationInfo(conn)
        # await addRoleForDiscordID(conn, botinfo[4], discordID, GUILD_ID, bot)
        # remove from bot database
        deleteFromDBForDiscordID(conn, discordID)
        # record the action in bot database
        recordBotActionHistory(conn, 'deleted removed from Plex, Tautulli, and DB for discordID: '
                               + str(discordID), 'AUTOMATIC')
    except Exception as e:
        logging.error('Exception from deleteFromPlexAndDB: ' + str(e))
    return


def getWatchTimeForDiscordID(conn, discordID):
    watchTimeForDiscordID = 0
    try:
        userInfo = getDBInfoForDiscordID(conn, discordID)
        if userInfo:
            plexInfo = getPlexServerConfigInfoForName(conn, userInfo[6])
            if plexInfo:
                TAUTULLI_URL = plexInfo[6]
                TAUTULLI_API_KEY = plexInfo[7]
                userID = userInfo[11]
                queryDays = plexInfo[8]
                localSession = Session()
                localSession.verify = False
                if not localSession.verify:
                    # Disable the warning that the request is insecure, we know that...
                    from urllib3 import disable_warnings
                    from urllib3.exceptions import InsecureRequestWarning
                    disable_warnings(InsecureRequestWarning)
                PARAMS = {
                    'cmd': 'get_user_watch_time_stats',
                    'user_id': userID,
                    'query_days': queryDays,
                    'apikey': TAUTULLI_API_KEY
                }
                GET = localSession.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=PARAMS).json()['response']['data']
                getList = GET[0]
                watchTimeForDiscordID = getList['total_time']
                # print(str(getList))
        else:
            watchTimeForDiscordID = 0
    except Exception as e:
        logging.error('Exception from getWatchTimeForDiscordID: ' + str(e))
    return watchTimeForDiscordID


def getCurrentStreams(conn):
    currentStreams = []
    try:
        servers = getListOfPlexServers(conn)
        for server in servers:
            stream = []
            tautulli_url = server[6]
            tautulli_apikey = server[7]
            PARAMS = {
                'cmd': 'get_activity',
                'apikey': tautulli_apikey
            }
            localSession = Session()
            localSession.verify = False
            if not localSession.verify:
                # Disable the warning that the request is insecure, we know that...
                from urllib3 import disable_warnings
                from urllib3.exceptions import InsecureRequestWarning
            GET = localSession.get(tautulli_url.rstrip('/') + '/api/v2', params=PARAMS).json()['response']['data']
            if GET:
                stream.append(server[1])
                stream.append(GET['stream_count'])
                stream.append(GET['stream_count_direct_play'])
                stream.append(GET['stream_count_direct_stream'])
                stream.append(GET['stream_count_transcode'])
                stream.append(GET['total_bandwidth'])
                currentStreams.append(stream)
    except Exception as e:
        logging.error('Exception from getCurrentStreams: ' + str(e))

    return currentStreams


def getCurrentDetailedStreams(conn):
    currentStreams = []
    try:
        servers = getListOfPlexServers(conn)
        for server in servers:
            stream = []
            sessionlist = []
            tautulli_url = server[6]
            tautulli_apikey = server[7]
            PARAMS = {
                'cmd': 'get_activity',
                'apikey': tautulli_apikey
            }
            localSession = Session()
            localSession.verify = False
            if not localSession.verify:
                # Disable the warning that the request is insecure, we know that...
                from urllib3 import disable_warnings
                from urllib3.exceptions import InsecureRequestWarning
            GET = localSession.get(tautulli_url.rstrip('/') + '/api/v2', params=PARAMS).json()['response']['data']
            if GET:
                sessions = GET['sessions']
                if len(sessions) != 0:
                    for session in sessions:
                        sessiontoappend = []
                        sessiontoappend.append(session['friendly_name']) # username
                        sessiontoappend.append(session['full_title']) # title of thing they are watching
                        sessiontoappend.append(session['media_type']) # will show movie/episode
                        sessiontoappend.append(session['year']) #
                        sessiontoappend.append(session['device']) # device they are watching on (ex. Windows)
                        sessiontoappend.append(session['player']) # play they are using (ex. Firefox)
                        sessiontoappend.append(session['product']) # product of plex handling playback (ex. Plex Web)
                        sessiontoappend.append(session['quality_profile']) # example: "1.5 Mbps 480p"
                        sessiontoappend.append(session['bandwidth']) # bandwidth of the playback/stream that is happening
                        sessiontoappend.append(session['video_decision']) # video decision (will say transcode if transcoding)
                        sessiontoappend.append(session['transcode_hw_decoding']) # if hw decoding, will be 1
                        sessiontoappend.append(session['transcode_hw_encoding']) # if hw encoding, will be 1
                        sessiontoappend.append(session['transcode_speed']) # how fast it is being transcoded, probably only has value before buffering stops.
                        sessionlist.append(sessiontoappend)
                stream.append(server[1])
                stream.append(sessionlist)
                stream.append(GET['stream_count'])
                stream.append(GET['stream_count_direct_play'])
                stream.append(GET['stream_count_direct_stream'])
                stream.append(GET['stream_count_transcode'])
                stream.append(GET['total_bandwidth'])
                currentStreams.append(stream)
    except Exception as e:
        logging.error('Exception from getCurrentStreams: ' + str(e))

    return currentStreams


def listPendingInvitesForServer(server):
    listPendingInvites = []
    localSession = Session()
    localSession.verify = False
    if not localSession.verify:
        # Disable the warning that the request is insecure, we know that...
        from urllib3 import disable_warnings
        from urllib3.exceptions import InsecureRequestWarning
        disable_warnings(InsecureRequestWarning)
    try:
        Server = PlexServer(baseurl=str(server[2]), token=str(server[3]), session=localSession)
        Account = Server.myPlexAccount()
        pendingInvites = Account.pendingInvites(includeSent=True, includeReceived=False)
        for invite in pendingInvites:
            listPendingInvites.append(invite)
    except Exception as e:
        logging.error('Exception from listPendingInvitesForServer: ' + str(e))
    return listPendingInvites


def checkForMatchingPendingInvite(conn, servername, email):
    matchingPendingInvite = False
    server = getPlexServerConfigInfoForName(conn, servername)
    pendingInvites = listPendingInvitesForServer(server)
    for invite in pendingInvites:
        if invite.email == email:
            matchingPendingInvite = True
            break
        else:
            matchingPendingInvite = False
    return matchingPendingInvite
# endregion
# region ACTIONS
logging.basicConfig(filename='managerr.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.ERROR)

try:
    DB_CONNECTION = sqlite3.connect(database)
except Error as e:
    logging.debug(f"error from creating DB_CONNECTION: {str(e)}")
try:
    createDB(DB_CONNECTION)
except Error as e:
    logging.debug(f"error from calling createDB: {str(e)}")

with DB_CONNECTION:
    botConfigured = getBotConfiguredBool(DB_CONNECTION)
# endregion
# endregion

# region BOT VARIABLES
# TOKEN = "tokenvalue"
TOKEN = config['botconfig']['bottoken']
intents = discord.Intents.all()
intents.members = True
if botConfigured:
    commandPrefix = getCommandPrefix(DB_CONNECTION)
    bot = commands.Bot(command_prefix=commandPrefix, intents=intents, help_command=None)
else:
    bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
# endregion


# region frequent loop action
@tasks.loop(minutes=30)
async def frequent():
    dtString = str(datetime.datetime.now())
    # if frequent loop is being blocked by infrequent loop, then i shouldnt have to adjust the time of exceution.
    # print(f'frequent loop is Started: {dtString}')
    logging.debug(f'frequent loop is Started: {dtString}')
    with DB_CONNECTION:
        plexServers = getListOfPlexServers(DB_CONNECTION)
        databaseUsersNoPlexUsername = getUsersNoUsername(DB_CONNECTION)
        databaseUsersNoPlexID = getUsersNoPlexID(DB_CONNECTION)
        discordUsersList = getUsersListFromDB(DB_CONNECTION)
        inactiveUserPlexIDS = getInactiveUsersPlexIDS(DB_CONNECTION)
    for plex in plexServers:
        localSession = Session()
        localSession.verify = False
        if not localSession.verify:
            # Disable the warning that the request is insecure, we know that...
            from urllib3 import disable_warnings
            from urllib3.exceptions import InsecureRequestWarning
            disable_warnings(InsecureRequestWarning)
        try:
            SERVER = PlexServer(baseurl=str(plex[2]), token=str(plex[3]), session=localSession)
            ACCOUNT = SERVER.myPlexAccount()
        except Exception as e:
            logging.debug(f"error getting server object. Error: {str(e)}")
        try:
            usersList = ACCOUNT.users()
            pendingInvites = ACCOUNT.pendingInvites(includeSent=True, includeReceived=False)
            emailUserNameDictionary = {str(user.email).lower(): str(user.username).lower() for user in usersList}
            emailUserIDDictionary = {str(user.email).lower(): user.id for user in usersList}
            # gotServerUsersSuccess = True
        except Exception as e:
            # gotServerUsersSuccess = False
            with DB_CONNECTION:
                recordBotActionHistory(DB_CONNECTION, 'error from trying to get plex users for plex server: ' + str(plex[1]) + '. Error: ' + str(e), 'AUTOMATIC')
            logging.debug(f"Error from trying to get plex users for plex server: {str(plex[1])}. Error: {str(e)}")
        # if gotServerUsersSuccess:
        if True:
            date1 = datetime.datetime.now()
            # region UPDATE STATUS FOR PLEX USER IN DATABASE
            for xEmail, xUsername in emailUserNameDictionary.items():
                with DB_CONNECTION:
                    userStatus = getStatusForEmail(DB_CONNECTION, xEmail)
                    discordID = getDiscordIDForEmail(DB_CONNECTION, xEmail)
                if userStatus != '3' and userStatus != '5':
                    with DB_CONNECTION:
                        updateStatusForDiscordID(DB_CONNECTION, str(discordID), '3')
                        valuesToSend = ("update status to 3, because they - " + xEmail + " - have accepted the invite", str(date1), "AUTOMATIC")
                        updateBotActionHistory(DB_CONNECTION, valuesToSend)
                elif userStatus == '5':
                    # print("found email " + str(xEmail) + " in plex, that does not line up with email in database. this should not be possible. username:" + str(xUsername))
                    # with DB_CONNECTION:
                        # recordBotActionHistory(DB_CONNECTION, 'found email in plex, that does not line up with email in database. This should not be possible. Email:' + xEmail, 'AUTOMATIC')
                    logging.debug('found email in plex, that does not line up with email in database. This should not be possible. Email:' + xEmail)
            # endregion
            # region UPDATE USERNAME IN DATABASE IF UNKNOWN
            if len(databaseUsersNoPlexUsername) > 0:
                for xEmail1, xUsername1 in databaseUsersNoPlexUsername.items():
                    if xEmail1 in emailUserNameDictionary:
                        xUsernamePlex = emailUserNameDictionary[xEmail1]
                        with DB_CONNECTION:
                            updateUsernameForPlexEmailAddress(DB_CONNECTION, xEmail1, xUsernamePlex)
                            valuesToSend = ("updated plex username " + str(xUsernamePlex) + " in db for " + xEmail1, str(date1), "AUTOMATIC")
                            updateBotActionHistory(DB_CONNECTION, valuesToSend)
            if len(databaseUsersNoPlexID) > 0:
                for xEmail2, xPlexID in databaseUsersNoPlexID.items():
                    if xEmail2 in emailUserIDDictionary:
                        xIDFromPlex = emailUserIDDictionary[xEmail2]
                        with DB_CONNECTION:
                            updatePlexIDForPlexEmailAddress(DB_CONNECTION, xEmail2, str(xIDFromPlex))
                            valuesToSend = ("updated plex ID " + str(xIDFromPlex) + " in db for " + xEmail2, str(date1), "AUTOMATIC")
                            updateBotActionHistory(DB_CONNECTION, valuesToSend)
            # endregion
            # region CANCEL TOO OLD PENDING INVITES
            # cancelPendingInvitesOverXDays(int(plex[9]))
            # endregion
            # region INVITE QUEUED USERS IF OPEN SPOTS
            with DB_CONNECTION:
                openSpots = getTotalOpenSpots(DB_CONNECTION)
                usersQueued = getUsersQueued(DB_CONNECTION)
            if openSpots > 0 and openSpots < 9000 and len(usersQueued) > 0:
                serverName = plex[1]
                openSpotCountForServer = (100 - (getUserCountForPlexServerName(DB_CONNECTION, serverName)))
                i = 1
                while i < openSpotCountForServer:
                    i += 1
                    try:
                        with DB_CONNECTION:
                            discordIDForOldestQueued = getDiscordIDForOldestQueuedUser(DB_CONNECTION)
                            emailForOldestQueued = getEmailForDiscordID(DB_CONNECTION, discordIDForOldestQueued)
                        if discordIDForOldestQueued != '':
                            member = discord.utils.get(thisGuild.members, id=int(discordIDForOldestQueued))
                            if member is not None:
                                await member.create_dm()
                                successBool = await inviteQueuedEmailToPlex(DB_CONNECTION, discordIDForOldestQueued, serverName, emailForOldestQueued, GUILD_ID)
                                thisGuild = bot.get_guild(GUILD_ID)
                                if successBool:
                                    # member = discord.utils.get(thisGuild.members, id=int(discordID))
                                    member.dm_channel.send(f"There were open spots and you have been invited to server: {serverName}")
                                # else DM them/admin that something went wrong.
                                else:
                                    ownerID = discord.Guild.owner_id
                                    # member = discord.utils.get(thisGuild.members, id=ownerID)
                                    member.dm_channel.send(f"Tried to invite this queued email: {emailForOldestQueued}, for this discordID: {discordIDForOldestQueued}. But something went wrong.")
                                # if DMing the admin include discord ID and email address value
                    except Exception as e:
                        with DB_CONNECTION:
                            recordBotActionHistory(DB_CONNECTION, 'something went wrong inviting user: ' + discordIDForOldestQueued + ' email: ' + emailForOldestQueued + ' error: ' + str(e), 'AUTOMATIC')
                        logging.debug(f"something went wrong inviting user: {str(discordIDForOldestQueued)}, email: {str(emailForOldestQueued)}, error: {str(e)}")
            # endregion
    logging.debug(f'frequent loop is Finished: ' + str(datetime.datetime.now()))
# endregion


# region infrequent loop action
@tasks.loop(hours=48)
async def infrequent():
    logging.debug(f'infrequent loop is Started: ' + str(datetime.datetime.now()))
    # region Check for Inactive Users and Remove
    thisGuild = bot.get_guild(GUILD_ID)
    with DB_CONNECTION:
        checksList = getListOfPlexThatChecks(DB_CONNECTION)
    listofusersremoved = []
    for plex in checksList:
        localSession = Session()
        localSession.verify = False
        if not localSession.verify:
            # Disable the warning that the request is insecure, we know that...
            from urllib3 import disable_warnings
            from urllib3.exceptions import InsecureRequestWarning
            disable_warnings(InsecureRequestWarning)
        TAUTULLI_URL = plex[6]
        TAUTULLI_APIKEY = plex[7]
        REMOVE_LIMIT = int(plex[8])  # Days to allow inactivity before removing.
        UNSHARE_LIMIT = 30  # Days
        try:
            SERVER = PlexServer(baseurl=str(plex[2]), token=str(plex[3]), session=localSession)
            ACCOUNT = SERVER.myPlexAccount()
        except Exception as e:
            print('error getting server object: ' + plex[1] + ' ' + str(e))
        DRY_RUN = False  # set to True to see console output of what users would be removed for inactivity.
        IGNORE_NEVER_SEEN = False

        # get users id and email into a dictionary
        try:
            PLEX_USERS_EMAIL = {user.id: user.email for user in ACCOUNT.users()}
            getUserIDAndEmailDictionarySuccess = True
        except Exception as e:
            print("error getting list of users id and email. Exception:" + str(e))
            getUserIDAndEmailDictionarySuccess = False
        
        # Get the Tautulli history.
        PARAMS = {
            'cmd': 'get_users_table',
            'order_column': 'last_seen',
            'order_dir': 'asc',
            'length': 600,
            'apikey': TAUTULLI_APIKEY
        }
        TAUTULLI_USERS = []
        try:
            GET = localSession.get(TAUTULLI_URL.rstrip('/')
                                    + '/api/v2', params=PARAMS).json()['response']['data']['data']
            for user in GET:
                TAUTULLI_USERS.append(user)
        except Exception as e:
            logging.error("Tautulli API 'get_users_table' request failed. Error: {}.".format(e))

        # gets a numerical value to measure against INACTIVITY TIME.
        todayMinusRemoveLimit = (datetime.datetime.now() - datetime.timedelta(days=REMOVE_LIMIT))
        NOW = datetime.datetime.today()

        for user in TAUTULLI_USERS:
            OUTPUT = []
            UID = user['user_id']
            USERNAME = user['friendly_name']
            email = user['email']
            isactive = user['is_active']
            if email is not None and isactive == 1:
                # get invited date for user
                with DB_CONNECTION:
                    invitedDate = getDateInvitedByEmail(DB_CONNECTION, email)
                # preset invite less than remove limit to false and no invited date to true.
                # invite less than remove limit means they have been invited sooner than the inactive remove limit amount of time.
                # ex invited 8 days ago with remove limit of 14 days.
                inviteLessThanRemoveLimitOLD = False
                noInvitedDate = True
                if invitedDate != '':
                    # if they have an invite date
                    noInvitedDate = False
                    # a date being greater than another date means it is newer, as time only piles up.
                    # print(f"if string of invited date {str(invitedDate)} greater than the string of today minus the remove limit {str(todayMinusRemoveLimit)}....")
                    if str(invitedDate) > str(todayMinusRemoveLimit):
                        # if that invite date is less than REMOVE_LIMIT old
                        inviteLessThanRemoveLimitOLD = True

                # region Get total seconds since last seen for the user.
                # if the user doesnt have a last seen then they have never been seen before.
                if not user['last_seen']:
                    TOTAL_SECONDS = 2592000
                    OUTPUT = '{} has never used the server'.format(USERNAME)
                else:
                    # set total seconds since the user was last seen. Will be used to determine removal.
                    TOTAL_SECONDS = int((NOW - datetime.datetime.fromtimestamp(user['last_seen'])).total_seconds())
                    OUTPUT = '{} was last seen {} ago'.format(USERNAME, time_format(TOTAL_SECONDS))
                # print(OUTPUT)
                # endregion

                # TOTAL_SECONDS = TOTAL_SECONDS or 86400 * UNSHARE_LIMIT
                if TOTAL_SECONDS >= (REMOVE_LIMIT * 86400):
                    logging.debug("total seconds since last seen, longer than remove limit: " + str(USERNAME) + ", " + str(TOTAL_SECONDS))
                    if inviteLessThanRemoveLimitOLD == False:
                        # dont remove them if they havent accepted the invite yet, and it hasnt been REMOVE_LIMIT # of days.
                        logging.debug("invite date is not smaller than the remove limit. invitedate, todayminusremovelimit: " + str(invitedDate) + ", " + str(todayMinusRemoveLimit) )
                        logging.debug("They do have an invited date. Invitedate: " + str(invitedDate))
                        if DRY_RUN == True:
                            print('{}, and would be removed.'.format(OUTPUT))
                            # try:
                            #     with DB_CONNECTION:
                            #         # print("should be email from array at UID " + str(UID) + " spot: " + str(PLEX_USERS_EMAIL[UID]))
                            #         discordID = getDiscordIDForEmail(DB_CONNECTION, str(PLEX_USERS_EMAIL[UID]))
                            #         print("This user")
                            #     # print("discord ID: " + str(discordID) + " obtained from email address:" + str(
                            #     #     PLEX_USERS_EMAIL[UID]))
                            # except Exception as e:
                            #     print("error from searching for discord ID by plex id: " + str(e))
                            #     print("error at this email address: " + str(UID))
                        else:
                            if getUserIDAndEmailDictionarySuccess:
                                try:
                                    user = []
                                    ACCOUNT.removeFriend(UID)
                                    user.append(str(UID))
                                    user.append(str(USERNAME))
                                    user.append(str(email))
                                    listofusersremoved.append(user)
                                    print("removed person Username, Email: " + str(USERNAME) + ", " + str(email))
                                    logging.debug("removed person Username, Email: " + str(USERNAME) + ", " + str(email))
                                except Exception as e1:
                                    logging.error("Error removing friend: " + str(e1))
                                mismatch = False
                                try:
                                    with DB_CONNECTION:
                                        discordID = getDiscordIDForEmail(DB_CONNECTION, str(PLEX_USERS_EMAIL[UID]))
                                        dbInfoForDiscordID = getDBInfoForDiscordID(DB_CONNECTION, discordID)
                                        serverName = dbInfoForDiscordID[6]
                                        plexServerConfigInfo = getPlexServerConfigInfoForName(DB_CONNECTION, serverName)
                                        # invitedRoleName = plexServerConfigInfo[5]
                                        botConfigInfo = getBotConfigurationInfo(DB_CONNECTION)
                                        # removedRoleName = botConfigInfo[4]
                                except Exception as e2:
                                    mismatch = True
                                    logging.error(f"probably had an issue where tautulli was out of date with Plex. should restart tautullis. Exception: " + str(e2))

                                if mismatch == False:
                                    guild = await bot.fetch_guild(GUILD_ID)
                                    dmmsg = ''
                                    member = await guild.fetch_member(int(discordID))
                                    # member = discord.utils.get(thisGuild.members, id=int(discordID))
                                    if member is not None:
                                        await member.create_dm()
                                        try:
                                            await member.dm_channel.send(
                                                "Hi " + member.name + "! \n\n"
                                                + "You were removed for inactivity.\n"
                                                + "Your status has been updated accordingly"
                                            )
                                            dmmsg = "successful!"
                                        except Exception as e:
                                            logging.error(f"Error trying to send direct message to removed member. {str(e)}")
                                    with DB_CONNECTION:
                                        updateStatusForDiscordID(DB_CONNECTION, str(discordID), 0)
                                        valuesToSend = ("Inactivity removal. dmmsg" + dmmsg, str(datetime.datetime.now()),
                                                        "AUTOMATIC")
                                        updateBotActionHistory(DB_CONNECTION, valuesToSend)
                                        removeServerNameForDiscordID(DB_CONNECTION, discordID)
                                        updateRemovalDateForDiscordID(DB_CONNECTION, discordID)
                                    # run tautulli command to delete user.
                                    uidString = str(UID)
                                    PARAMS1 = {
                                        'cmd': 'delete_all_user_history',
                                        'user_id': uidString,
                                        'apikey': TAUTULLI_APIKEY
                                    }
                                    # SESSION.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=PARAMS).json()
                                    try:
                                        localSession.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=PARAMS1).json()
                                    except Exception as e:
                                        logging.error("Tautulli API 'delete_all_user_history' request failed. Error: {}.".format(e))
                                else:
                                    # print("mismatch was true so on to the next one.")
                                    logging.debug(f"mismatch was true so on to the next one.")
    # endregion
    try:
        announcementchannel = thisGuild.get_channel(ANNOUNCEMENT_CHANNEL_ID)
        embed = discord.Embed(title="Inactive User Removal Complete", color=discord.Color.random())
        embed.set_author(name=f"Managerr", icon_url="https://assets.thepebbles.tech/pics/managerricon.jpg")
        embed.set_thumbnail(url="https://assets.thepebbles.tech/pics/managerricon.jpg")
        embed.add_field(name="Inactive users removed: ", value=f"{str(len(listofusersremoved))}", inline=True)
        await announcementchannel.send(embed=embed)
    except Exception as e:
        logging.error(f"Error sending user removal count announcement message. Exception: {str(e)}")
    logging.debug(f'infrequent loop is Finished: ' + str(datetime.datetime.now()))
# endregion

# region bot events
# region on_ready event
if botConfigured:
    @bot.event
    async def on_ready():
        print(f"Bot is online with a {round(bot.latency * 1000)}ms ping")
        logging.debug(f"Bot is online with a {round(bot.latency * 1000)}ms ping")
        with DB_CONNECTION:
            commandPrefix = getCommandPrefix(DB_CONNECTION)
        game = discord.Game(name="DM me with " + commandPrefix + "help")
        thisGuild = bot.get_guild(GUILD_ID)
        await bot.change_presence(activity=game)
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
else:
    @bot.event
    async def on_ready():
        print(f"Bot is online with a {round(bot.latency * 1000)}ms ping")
        logging.debug(f"Bot is online with a {round(bot.latency * 1000)}ms ping")
        logging.debug(f"Bot is not configured, admin needs to configure.")
# endregion
# region on_member_remove event
if botConfigured:
    @bot.event
    async def on_member_remove(member):
        with DB_CONNECTION:
            status = getStatusForDiscordID(DB_CONNECTION, str(member.id))
        if status == '0':
            # removed for inactivity, delete them
            with DB_CONNECTION:
                deleteFromDBForDiscordID(DB_CONNECTION, str(member.id))
                recordBotActionHistory(DB_CONNECTION, 'from on_member_remove status 0: deleted user from database discordID: ' + str(member.id), 'AUTOMATIC')
        elif status == '1':
            # removed by admin, delete them
            with DB_CONNECTION:
                deleteFromDBForDiscordID(DB_CONNECTION, str(member.id))
                recordBotActionHistory(DB_CONNECTION, 'from on_member_remove status 1: deleted user from database discordID: ' + str(member.id), 'AUTOMATIC')
        elif status == '2':
            # invited but not accepted
            with DB_CONNECTION:
                cancelPendingInviteForDiscordID(DB_CONNECTION, str(member.id))
                deleteFromDBForDiscordID(DB_CONNECTION, str(member.id))
                recordBotActionHistory(DB_CONNECTION, 'from on_member_remove status 2: Canceled Pending invite and deleted from database for discordID: ' + str(member.id), 'AUTOMATIC')
        elif status == '3':
            # invited and accepted
            with DB_CONNECTION:
                await deleteFromPlexTautulliAndDB(DB_CONNECTION, str(member.id))
                recordBotActionHistory(DB_CONNECTION, 'from on_member_remove status 3: Removed Friend from Plex, Tautulli, and database by discordID: ' + str(member.id), 'AUTOMATIC')
        elif status == '4':
            # queued for an invite
            with DB_CONNECTION:
                deleteFromDBForDiscordID(DB_CONNECTION, str(member.id))
                recordBotActionHistory(DB_CONNECTION, 'from on_member_remove status 4: Removed queued user from database by discordID: ' + str(member.id), 'AUTOMATIC')
        else:
            with DB_CONNECTION:
                recordBotActionHistory(DB_CONNECTION, 'member left that had no status. Nothing to do except record it ' + str(member.id), 'AUTOMATIC')
            logging.debug('member left. I dont care.')
# endregion
# endregion

# region bot commands
if botConfigured:
    @bot.command(description="PUBLIC")
    async def amiadmin(ctx):
        with DB_CONNECTION:
            values = (f"{bot.command_prefix}amiadmin", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message.content))
            recordCommandHistory(DB_CONNECTION, values)
        adminID = getAdminDiscordID(DB_CONNECTION)
        if adminID == str(ctx.author.id):
            await ctx.send(f"you are admin.")
        else:
            await ctx.send(f"You are NOT admin.")

    @bot.command(description="PUBLIC")
    async def listcommands(ctx):
        with DB_CONNECTION:
            values = (f"{bot.command_prefix}listcommands", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message.content))
            recordCommandHistory(DB_CONNECTION, values)
        helptext = "```"
        helptext+=f"\nPUBLIC\n"
        publiclist = []
        dmlist = []
        for command in bot.commands:
            if command.description == "PUBLIC":
                publiclist.append(f"{str(bot.command_prefix)}{command}\n")
                # helptext+=f"{str(bot.command_prefix)}{command}\n"
        sortedpubliclist = sorted(publiclist)
        for publiccommand in sortedpubliclist:
            helptext+=publiccommand
        helptext+=f"\nDM ONLY\n"
        for command in bot.commands:
            if command.description == "DM ONLY":
                dmlist.append(f"{str(bot.command_prefix)}{command}\n")
                # helptext+=f"{str(bot.command_prefix)}{command}\n"
        sorteddmlist = sorted(dmlist)
        for dmcommand in sorteddmlist:
            helptext+=dmcommand        
        helptext+="```"
        await ctx.reply(helptext)

    @bot.command(description="PUBLIC")
    async def help(ctx):
        with DB_CONNECTION:
            values = (f"{bot.command_prefix}help", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message.content))
            recordCommandHistory(DB_CONNECTION, values)
        # await ctx.reply(f"The command prefix is ```{str(bot.command_prefix)}```\nFor a list of commands use **{str(bot.command_prefix)}listcommands**\nFor questions check the following channels:\n**rules**\n**announcements**\n**up-down**\n**problems**")
        await ctx.reply(f"For a list of commands use **{str(bot.command_prefix)}listcommands**\nFor questions check the following channels:\n**rules**\n**announcements**\n**up-down**\n**problems**")

    @bot.command(description="PUBLIC")
    async def mystatus(ctx):
        with DB_CONNECTION:
            values = (f"{bot.command_prefix}status", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message.content))
            recordCommandHistory(DB_CONNECTION, values)
            memberstatus = getStatusForDiscordID(DB_CONNECTION, str(ctx.author.id))
        if memberstatus == "":
            await ctx.reply(f"No status for you.")
        elif memberstatus == '0':
            await ctx.reply(f"You have been removed for inactivity")
        elif memberstatus == '1':
            await ctx.reply(f"You have been manually removed by an admin")
        elif memberstatus == '2':
            await ctx.reply(f"You have been invited, but you haven't accepted yet.")
        elif memberstatus == '3':
            await ctx.reply(f"You have already accepted an invite.")
        elif memberstatus == '4':
            await ctx.reply(f"You are queued for an open spot.")
        else:
            await ctx.reply(f"Something went wrong, please let an admin know if you see this message. Alternatively post in the **problems** channel.")

    @bot.command(description="PUBLIC")
    async def myqueuestatus(ctx):
        with DB_CONNECTION:
            values = (f"{bot.command_prefix}queuestatus", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message.content))
            recordCommandHistory(DB_CONNECTION, values)
            statusformember = getStatusForDiscordID(DB_CONNECTION, str(ctx.author.id))
        if statusformember == '4':
            with DB_CONNECTION:
                datequeued = getDateQueuedForDiscordID(DB_CONNECTION, str(ctx.author.id))
                countahead = getCountQueuedAheadOfDate(DB_CONNECTION, datequeued)
            if countahead == 0:
                await ctx.reply(f"There is no one queued ahead of you, you should get the next available spot.")
            else:
                await ctx.reply(f"There are {str(countahead)} queued ahead of you.")
        else:
            await ctx.reply(f"You are not currently queued for an invite")

    @bot.command(description="PUBLIC")
    async def openspots(ctx):
        with DB_CONNECTION:
            values = (f"{bot.command_prefix}openspots", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message.content))
            recordCommandHistory(DB_CONNECTION, values)
            openspotscount = getTotalOpenSpots(DB_CONNECTION)
        if openspotscount < 9000:
            await ctx.reply(f"There are {str(openspotscount)} spots open.")
        else:
            await ctx.reply(f"Cannot count open spots right now. Try again later.")

    @bot.command(description="PUBLIC")
    async def mywatchtime(ctx):
        with DB_CONNECTION:
            values = (f"{bot.command_prefix}mywatchtime", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message.content))
            recordCommandHistory(DB_CONNECTION, values)
            userinfo = getDBInfoForDiscordID(DB_CONNECTION, str(ctx.author.id))
        if userinfo == []:
            await ctx.reply(f"You have not been invited to any server, so no watch time for you.")
        else:
            if userinfo[10] == "3":
                with DB_CONNECTION:
                    watchtime = getWatchTimeForDiscordID(DB_CONNECTION, str(ctx.author.id))
                    plexinfo = getPlexServerConfigInfoForName(DB_CONNECTION, userinfo[6])
                if watchtime != 0:
                    prettytime = time_format(watchtime)
                    await ctx.reply(f"Your watch time is {prettytime} within the last {plexinfo[8]} days.")
                else:
                    await ctx.reply(f"No watch time recorded for you.")
            elif userinfo[10] == 2:
                await ctx.reply(f"You have been invited, but haven't accepted the invite. So no watch time for you.")
            
    @bot.command(description="PUBLIC")
    async def libraries(ctx):
        with DB_CONNECTION:
            values = (f"{bot.command_prefix}libraries", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message.content))
            recordCommandHistory(DB_CONNECTION, values)
        await ctx.reply(f"https://medialist.thepebbles.tech")

    @bot.command(description="PUBLIC")
    async def howmanyqueued(ctx):
        with DB_CONNECTION:
            values = (f"{bot.command_prefix}howmanyqueued", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message.content))
            recordCommandHistory(DB_CONNECTION, values)
            numberqueued = getUsersQueued(DB_CONNECTION)
        await ctx.reply(f"There are {str(len(numberqueued))} people queued for an invite right now.")

    @bot.command(description="PUBLIC")
    async def speedtest(ctx):
        with DB_CONNECTION:
            values = (f"{bot.command_prefix}speedtest", str(ctx.channel), str(ctx.author.name), str(ctx.author.id),
                      str(datetime.datetime.now()), str(ctx.message.content))
            recordCommandHistory(DB_CONNECTION, values)
        await ctx.reply(f"Test the speed of your connection to the servers: https://speedtest.thepebbles.tech")
    
    @bot.command(description="PUBLIC")
    async def overflow(ctx):
        with DB_CONNECTION:
            values = ("overflow", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message.content))
            recordCommandHistory(DB_CONNECTION, values)
        embed = discord.Embed(title="Overflow info for JellyBelly", description="", color=discord.Color.random())
        embed.set_author(name=f"JellyBelly", url="https://discord.gg/Tnue6KQ7th", icon_url="https://assets.thepebbles.tech/pics/jellybellydiscordiconbold.jpg")
        embed.set_thumbnail(url=f"https://assets.thepebbles.tech/pics/jellybellydiscordiconbold.jpg")
        embed.add_field(name="1: ", value="There is a jellyfin based discord server available here: https://discord.gg/Tnue6KQ7th", inline=False)
        embed.add_field(name="2: ", value="That discord server has its own rules, but an important note is that jellyfin doesn't have a limit on the number of users/shares.", inline=False)
        embed.set_footer(text=f"JellyBelly")
        await ctx.reply(embed=embed)
        # can build and send embed here.
        # await ctx.reply(f"There is a jellyfin based discord server available here: https://discord.gg/Tnue6KQ7th \nThat discord server has its own rules, but an important note is that jellyfin doesn't have a limit on the number of users/shares.")

    @bot.command(description="PUBLIC")
    async def streams(ctx):
        with DB_CONNECTION:
            values = (f"{bot.command_prefix}currentstreams", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message.content))
            recordCommandHistory(DB_CONNECTION, values)
            streamlist = getCurrentStreams(DB_CONNECTION)
        if streamlist != []:
            embed = discord.Embed(title="Current Streams", color=discord.Color.orange())
            embed.set_author(name=f"Tautulli", icon_url="https://assets.thepebbles.tech/pics/tautulliicon.jpg")
            # embed.set_thumbnail(url="https://assets.thepebbles.tech/pics/tautulliicon.jpg")
            for stream in streamlist:
                embed.add_field(name="Server: ", value=f"{str(stream[0])}", inline=True)
                embed.add_field(name="Stream Count: ", value=f"{str(stream[1])}", inline=True)
                embed.add_field(name=f"**Direct Play:** {str(stream[2])}\n**Direct Stream:** {str(stream[3])}\n**Transcode:** {str(stream[4])}", value="", inline=False)
                embed.add_field(name=f"**Total Bandwidth:** {str(stream[5]/1000)}mbps", value="", inline=False)
                embed.add_field(name="", value="\n", inline=False)
            await ctx.reply(embed=embed)
        else:
            await ctx.reply(f"Currently no streams playing")

    @bot.command(description="PUBLIC")
    async def detailedstreams(ctx):
        with DB_CONNECTION:
            values = (f"{bot.command_prefix}currentdetailedstreams", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message.content))
            recordCommandHistory(DB_CONNECTION, values)
            streamlist = getCurrentDetailedStreams(DB_CONNECTION)
        if streamlist != []:
            for stream in streamlist:
                embed = discord.Embed(title=f"**Server:** {str(stream[0])}", color=discord.Color.orange())
                embed.set_author(name=f"Tautulli", icon_url="https://assets.thepebbles.tech/pics/tautulliicon.jpg")
                embed.set_thumbnail(url="https://assets.thepebbles.tech/pics/tautulliicon.jpg")
                embed.add_field(name="Stream Count: ", value=f"{str(stream[2])}")
                embed.add_field(name="Total Bandwidth: ", value=f"{str(stream[6] / 1000)}mbps")
                sessionlist = stream[1]
                for session in sessionlist:
                    if session[2] == 'movie':
                        embed.add_field(name=f"{str(sessionlist.index(session)+1)}: {str(session[1])} ({str(session[3])})", value=f"👤**{str(session[0])}**\n📺**{str(session[5])}** ({str(session[6])})\n⚙️**{str(session[7])}** ({str(int(session[8])/1000)}mbps)({str(session[9])})", inline=False)
                    else:
                        embed.add_field(name=f"{str(sessionlist.index(session)+1)}: {str(session[1])}", value=f"👤**{str(session[0])}**\n📺**{str(session[5])}** ({str(session[6])})\n⚙️**{str(session[7])}** ({str(int(session[8])/1000)}mbps)({str(session[9])})", inline=False)
                embed.add_field(name="--------\n", value="", inline=False)
                await ctx.reply(embed=embed)
        else:
            await ctx.reply(f"Currently no streams")

    @bot.command(description="PUBLIC")
    async def currentgoal(ctx):
        with DB_CONNECTION:
            values = (f"{bot.command_prefix}currentgoal", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message.content))
            recordCommandHistory(DB_CONNECTION, values)
        goals = ['https://ko-fi.com/jomack16/goal?g=0']
        if goals != []:
            embed = discord.Embed(title="Goals", color=discord.Color.random())
            embed.set_author(name=f"Ko-Fi", icon_url="https://assets.thepebbles.tech/pics/kofiicon.png")
            for goal in goals:
                embed.add_field(name="Current Goal: ", value=f"{str(goal)}", inline=True)
            await ctx.reply(embed=embed)
        else:
            await ctx.reply(f"Currently NO financial goals for the server")

    @bot.command(description="PUBLIC")
    async def donate(ctx):
        with DB_CONNECTION:
            values = (f"{bot.command_prefix}donate", str(ctx.channel), str(ctx.author.name), str(ctx.author.id),
                      str(datetime.datetime.now()), str(ctx.message.content))
            recordCommandHistory(DB_CONNECTION, values)
        donatelink = 'https://ko-fi.com/jomack16'
        if donatelink != '':
            embed = discord.Embed(title="Donate", color=discord.Color.random())
            embed.set_author(name=f"Ko-Fi", icon_url="https://assets.thepebbles.tech/pics/kofiicon.png")
            embed.add_field(name=f"If you are interested in donating to improve the general capacity/capability of the server, you can do that here: {donatelink}", value=f"Note: Donations are not required for any reason.\nThey will exclusively be used to improve the capacity, capability, and/or quantity of the server(s)", inline=True)
            await ctx.reply(embed=embed)
        else:
            await ctx.reply(f"No donations being accepted.")

    @bot.command(description="PUBLIC")
    async def uptime(ctx):
        with DB_CONNECTION:
            values = (f"{bot.command_prefix}uptime", str(ctx.channel), str(ctx.author.name), str(ctx.author.id),
                      str(datetime.datetime.now()), str(ctx.message.content))
            recordCommandHistory(DB_CONNECTION, values)
        await ctx.reply(f"https://uptime.thejones.tech/status/pmbp")
    # region user Direct message commands
    @bot.command(description="DM ONLY")
    async def inviteme(ctx, email=None):
        dmChannel = await ctx.author.create_dm()
        if str(ctx.channel.type.name) == "private":
            with DB_CONNECTION:
                values = (f"{bot.command_prefix}inviteme", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message))
                recordCommandHistory(DB_CONNECTION, values)
            if email == None or "@" not in str(email):
                await ctx.author.send(f"Something is wrong with the way you sent that. Your message should look like ```{str(bot.command_prefix)}inviteme email@address.com```")
            else:
                with DB_CONNECTION:
                    exists = checkDiscordIDExists(DB_CONNECTION, str(ctx.author.id))
                    if exists:
                        status = getStatusForDiscordID(DB_CONNECTION, str(ctx.author.id))
                        emailformember = getEmailForDiscordID(DB_CONNECTION, str(ctx.author.id))
                openspots = getTotalOpenSpots(DB_CONNECTION)
                if not exists: 
                    if openspots > 0 and openspots < 9000:
                        servername = getFirstPlexServerNameWithOpenSpots(DB_CONNECTION)
                        uservalues = (str(ctx.author.id), str(ctx.author.name), "fromDMNoNickName", servername)
                        successbool = inviteEmailToPlex(DB_CONNECTION, str(email).lower(), uservalues)
                        if successbool:
                            rolename = getInvitedDiscordRoleNameForServerName(DB_CONNECTION, servername)
                            # await addRoleForDiscordID(DB_CONNECTION, rolename, str(ctx.author.id), GUILD_ID, bot)
                            await dmChannel.send(f"You have been invited to Plex server **{servername}**. \nIf you do not see the invite email shortly, make sure to check spam.")
                        else:
                            await dmChannel.send(f"Something went wrong trying to invite you with that email address **{str(email)}**.\nPlease make sure you entered it correctly.\nLet the admin know via the **problems** channel if still experiencing issues.")
                            logging.debug(f"Error inviting user to plex. discordid: {ctx.author.id}, email used: {str(email)}, invited server name: {servername}, user values sent: {str(uservalues)}, message: {str(ctx.message)}")
                    else:
                        with DB_CONNECTION:
                            queuevalues = (str(ctx.message.author.id), str(ctx.author.name), str(email).lower(), str(datetime.datetime.now()), '4')
                            insertQueuedUser(DB_CONNECTION, queuevalues)
                            currentlyqueued = getUsersQueued(DB_CONNECTION)
                        await dmChannel.send(f"There are curently no open spots, but you have been queued for a spot.\nThere are currently {len(currentlyqueued)} queued for a spot.\nTo see your status in the queue at anytime, try {bot.command_prefix}queuestatus")
                else:
                    with DB_CONNECTION:
                        botconfiginfo = getBotConfigurationInfo(DB_CONNECTION)
                    if status == '0' and openspots > 0 and openspots < 9000:
                        servername = getFirstPlexServerNameWithOpenSpots(DB_CONNECTION)
                        uservalues = (str(ctx.author.id), str(ctx.author.name), "fromDMNoNickName", servername)
                        successbool = inviteEmailToPlex(DB_CONNECTION, str(email).lower(), uservalues)
                        if successbool:
                            rolenametoremove = botconfiginfo[4]
                            # await removeRoleForDiscordID(DB_CONNECTION, rolenametoremove, str(ctx.author.id), GUILD_ID, bot)
                            rolenametoadd = getInvitedDiscordRoleNameForServerName(DB_CONNECTION, servername)
                            # await addRoleForDiscordID(DB_CONNECTION, rolenametoadd, str(ctx.author.id), GUILD_ID, bot)
                            await dmChannel.send(f"You were previously removed for inactivity, but there are open spots now, so you have been reinvited.\n You have been invited to plex server **{servername}**")
                        else:
                            await dmChannel.send(f"You were in a status of removed/inactive but there were open spots so you should have been added. Something went wrong.\nPlease try again and if the issue persists let the admin know in the **problems** channel.")
                            logging.error(f"Inviting this user with a removed status was unsuccessful {str(email).lower()}, {str(uservalues)}")
                    elif status == '0' and (openspots == 0 or openspots == 9000):
                        rolenametoremove = botconfiginfo[4]
                        # await removeRoleForDiscordID(DB_CONNECTION, rolenametoremove, str(ctx.author.id), GUILD_ID, bot)
                        rolenametoadd = botconfiginfo[3]
                        # await addRoleForDiscordID(DB_CONNECTION, rolenametoadd, str(ctx.author.id), GUILD_ID, bot)
                        await dmChannel.send(f"You were previously removed for inactivity, and there are currently NO spots available.\nYou have been queued for an open spot.\nYou can check your queue status with {bot.command_prefix}queuestatus")
                    elif status == '1':
                        await dmChannel.send(f"You were manually removed by an admin. You will need to contact them to change your status.")
                    elif status == '2' and emailformember == str(email).lower():
                        await dmChannel.send(f"An invite has already been sent to that email address, but it is not seen as accepted yet.\nPlease accept the invite, and check spam if you cannot find the email.")
                    elif status == '2' and emailformember != str(email).lower():
                        await dmChannel.send(f"An invite has already been sent to you, but for a different email address. \nIf you made a typo when you first used the **{bot.command_prefix}inviteme** command you can leave the discord server to be removed from the bot database.\nThen you can rejoin the discord server and DM me the **{bot.command_prefix}inviteme** command again with the correct info. \nThis will place you at the bottom of the invite queue.")
                    elif status == '3' and emailformember != str(email).lower():
                        await dmChannel.send(f"You have already accepted an invite for a different email address.\nIf you are trying to get an invite for someone else, please have them join the discord server.")
                    elif status == '3' and emailformember == str(email).lower():
                        await dmChannel.send(f"You have already accepted an invite for that email address.\nIf you are having problems, please message the admin or post in the **problems** channel")
                    elif status == '4' and emailformember == str(email).lower():
                        await dmChannel.send(f"You have already been queued for an invite to that email address.\nTo see your place in the queue try **{bot.command_prefix}queuestatus**")
                    elif status == '4' and emailformember != str(email).lower():
                        await dmChannel.send(f"You have already been added to the queue but for a different email address.\nIf this was caused by a typo, leave the discord server, then rejoin and use the **{bot.command_prefix}inviteme** command again.\nThis will reset your position in the queue.\nIf you are trying to queue someone else, instead have them join the discord server and do it themselves.")
                    else:
                        await dmChannel.send(f"Something went wrong. Please try again later.\nIf the problem persists, please conact the admin or post in the **problems** channel.")
                        logging.error(f"Something went wrong getting the status of the users and handling the invite. message: {str(ctx.message)}")
        else:
            await ctx.author.send(f"Please do not use the inviteme command in public channels.")
            try:
                await ctx.message.delete()
            except Exception as e:
                logging.error(f"issue deleting message. Exception: {str(e)}\n message: {str(ctx.message)}")
    
    @bot.command(description="DM ONLY")
    async def mydatabaseinfo(ctx):
        if str(ctx.channel.type.name) == "private":
            dmChannel = await ctx.author.create_dm()
            with DB_CONNECTION:
                values = (f"{bot.command_prefix}mydatabaseinfo", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message))
                recordCommandHistory(DB_CONNECTION, values)
                userinfo = getDBInfoForDiscordID(DB_CONNECTION, str(ctx.author.id))
            if userinfo:
                pfp = ctx.author.display_avatar
                embed = discord.Embed(title=f"Database info for {ctx.author.name}", description="", color=discord.Color.random())
                embed.set_author(name=f"{bot.user.display_name}", icon_url="https://assets.thepebbles.tech/pics/managerricon.png")
                embed.set_thumbnail(url=f"{pfp}")
                embed.add_field(name="Discord ID: ", value=f"{str(userinfo[1])}", inline=False)
                embed.add_field(name="Discord Username: ", value=f"{str(userinfo[2])}", inline=False)
                embed.add_field(name="Plex ID: ", value=f"{str(userinfo[11])}", inline=False)
                embed.add_field(name="Plex Username: ", value=f"{str(userinfo[4])}", inline=False)
                embed.add_field(name="Email: ", value=f"{str(userinfo[5])}", inline=False)
                embed.add_field(name="Server Name: ", value=f"{str(userinfo[6])}", inline=False)
                embed.add_field(name="Status: ", value=f"{str(userinfo[10])}", inline=False)
                embed.add_field(name="Date Removed: ", value=f"{str(userinfo[7])}", inline=False)
                embed.add_field(name="Date Invited: ", value=f"{str(userinfo[8])}", inline=False)
                embed.add_field(name="Date Queued: ", value=f"{str(userinfo[9])}", inline=False)
                embed.set_footer(text=f"from PlexManager ({str(datetime.datetime.now())})")
                await dmChannel.send(embed=embed)
            else:
                await dmChannel.send(f"You have no database info.")        
        else:
            await ctx.reply(f"You have to use this command in a DM with the bot")
    # endregion
    # region admin commands
    @bot.command(description="ADMIN")
    async def listadmincommands(ctx):
        # check admin id from bot db against ctx.author.id.
        adminID = getAdminDiscordID(DB_CONNECTION)
        if adminID == str(ctx.author.id):
            helptext = "```"
            commandlist = []
            for command in bot.commands:
                if command.description == "ADMIN":
                    commandlist.append(f"{str(bot.command_prefix)}{command}\n")
                    # helptext+=f"{str(bot.command_prefix)}{command}\n"
            sortedcommandlist = sorted(commandlist)
            for sortedcommand in sortedcommandlist:
                helptext+=sortedcommand
            helptext+="```"
            # await ctx.send(helptext)
            dmChannel = await ctx.author.create_dm()
            await dmChannel.send(helptext)
    
    @bot.command(description="ADMIN")
    async def restart(ctx):
        dmChannel = await ctx.author.create_dm()
        adminID = getAdminDiscordID(DB_CONNECTION)
        if adminID == str(ctx.author.id):
            await dmChannel.send(f"Restarting the bot...")
            restart_bot()

    @bot.command(description="ADMIN")
    async def updatebotchannelid(ctx, newchannelid=None):
        dmChannel = await ctx.author.create_dm()
        adminID = getAdminDiscordID(DB_CONNECTION)
        if adminID == str(ctx.author.id):
            with DB_CONNECTION:
                values = (f"{bot.command_prefix}updatebotchannelid", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message))
                recordCommandHistory(DB_CONNECTION, values)
            if newchannelid == None:
                await dmChannel.send(f"You are missing the new channel id")
            else:
                with DB_CONNECTION:
                    updateValues = (str(newchannelid), str(adminID))
                    updateBotChannelID(DB_CONNECTION, updateValues)
                await dmChannel.send(f"Bot channel ID is updated!")
    
    @bot.command(description="ADMIN")
    async def updatecommandprefix(ctx, newcommandprefix=None):
        dmChannel = await ctx.author.create_dm()
        adminID = getAdminDiscordID(DB_CONNECTION)
        if adminID == str(ctx.author.id):
            with DB_CONNECTION:
                values = (f"{bot.command_prefix}updatecommandprefix", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message))
                recordCommandHistory(DB_CONNECTION, values)
            if newcommandprefix == None:
                await dmChannel.send(f"You are missing the new command prefix")
            else:
                bot.command_prefix = str(newcommandprefix)
                with DB_CONNECTION:
                    updateValues = (str(newcommandprefix), str(adminID))
                    updateCommandPrefix(DB_CONNECTION, updateValues)
                game = discord.Game(name=f"DM me with {str(getCommandPrefix(DB_CONNECTION))}help")
                await bot.change_presence(activity=game)
                await dmChannel.send(f"Command prefix has been updated to {str(newcommandprefix)}")
        
    @bot.command(description="ADMIN")
    async def initplexserver(ctx, servername=None, serverurl=None, servertoken=None, checksinactivity=None, inviteddiscordrolename=None, tautulliurl=None, tautulliapikey=None, inactivitylimit=None, inviteacceptancelimit=None):
        dmChannel = await ctx.author.create_dm()
        adminID = getAdminDiscordID(DB_CONNECTION)
        if adminID == str(ctx.author.id):
            with DB_CONNECTION:
                values = (f"{bot.command_prefix}initplexserver", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message))
                recordCommandHistory(DB_CONNECTION, values)
            if (servername==None or serverurl==None or servertoken==None or checksinactivity==None or inviteddiscordrolename==None or tautulliurl==None or tautulliapikey==None or inactivitylimit==None or inviteacceptancelimit==None):
                await dmChannel.send(f"you are missing a parameter. should have: name, url, token, checksinactivity, inviteddiscordrolename, tautulliurl, tautulliapikey, inactivitylimit, inviteacceptanelimit")
            else:
                with DB_CONNECTION:
                    initializationValues = (str(servername), str(serverurl), str(servertoken), str(checksinactivity), str(inviteddiscordrolename), str(tautulliurl), str(tautulliapikey), str(inactivitylimit), str(inviteacceptancelimit))
                    recordPlexServerEntry(DB_CONNECTION, initializationValues)
                await dmChannel.send(f"plex server {servername} has been initialized!")

    @bot.command(description="ADMIN")
    async def listplexservers(ctx):
        dmChannel = await ctx.author.create_dm()
        adminID = getAdminDiscordID(DB_CONNECTION)
        if adminID == str(ctx.author.id):
            with DB_CONNECTION:
                values = (f"{bot.command_prefix}listplexservers", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message))
                recordCommandHistory(DB_CONNECTION, values)
                plexServers = getListOfPlexServers(DB_CONNECTION)
            for server in plexServers:
                userCount = getUserCountForPlexServerName(DB_CONNECTION, str(server[1]))
                if userCount < 9000:
                    await dmChannel.send(f"**ServerName:** {str(server[1])}\n**ServerURL:** {str(server[2])}\n**ServerToken:** {str(server[3])}\n**ChecksInactivity:** {str(server[4])}\n**InvitedDiscordRoleName:** {str(server[5])}\n**TautulliURL:** {str(server[6])}\n**TautulliAPIKey:** {str(server[7])}\n**InactivityLimit:** {str(server[8])}\n**InviteAcceptanceLimit:** {str(server[9])}\n**UserCount:** {str(userCount)}\n--------")
                else:
                    await dmChannel.send(f"**ServerName:** {str(server[1])}\n**ServerURL:** {str(server[2])}\n**ServerToken:** {str(server[3])}\n**ChecksInactivity:** {str(server[4])}\n**InvitedDiscordRoleName:** {str(server[5])}\n**TautulliURL:** {str(server[6])}\n**TautulliAPIKey:** {str(server[7])}\n**InactivityLimit:** {str(server[8])}\n**InviteAcceptanceLimit:** {str(server[9])}\n**UserCount:** cannot be counted right now.\n--------")
        
    @bot.command(description="ADMIN")
    async def listplexserverswithoutcount(ctx):
        dmChannel = await ctx.author.create_dm()
        adminID = getAdminDiscordID(DB_CONNECTION)
        if adminID == str(ctx.author.id):
            with DB_CONNECTION:
                values = (f"{bot.command_prefix}listplexserverswithoutcount", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message))
                recordCommandHistory(DB_CONNECTION, values)
                plexServers = getListOfPlexServers(DB_CONNECTION)
            for server in plexServers:
                await dmChannel.send(f"**ServerName:** {str(server[1])}\n**ServerURL:** {str(server[2])}\n**ServerToken:** {str(server[3])}\n**ChecksInactivity:** {str(server[4])}\n**InvitedDiscordRoleName:** {str(server[5])}\n**TautulliURL:** {str(server[6])}\n**TautulliAPIKey:** {str(server[7])}\n**InactivityLimit:** {str(server[8])}\n**InviteAcceptanceLimit:** {str(server[9])}\n--------")

    @bot.command(description="ADMIN")
    async def clearpendinginvites(ctx, numberofdays=None):
        dmChannel = await ctx.author.create_dm()
        adminID = getAdminDiscordID(DB_CONNECTION)
        if adminID == str(ctx.author.id):
            with DB_CONNECTION:
                values = (f"{bot.command_prefix}clearpendinginvites", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message))
                recordCommandHistory(DB_CONNECTION, values)
            if numberofdays==None:
                await dmChannel.send(f"You are missing the number of days.")
            else:
                cancelPendingInvitesOverXDays(numberofdays)
                await dmChannel.send(f"Pending invites older than **{str(numberofdays)}** have been cleared")
    
    @bot.command(description="ADMIN")
    async def listallpendinginvites(ctx):
        dmChannel = await ctx.author.create_dm()
        adminID = getAdminDiscordID(DB_CONNECTION)
        if adminID == str(ctx.author.id):
            with DB_CONNECTION:
                values = (f"{bot.command_prefix}listallpendinginvites", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message))
                recordCommandHistory(DB_CONNECTION, values)
            try:
                pendingInviteList = listAllPendingInvites()
                if pendingInviteList != []:
                    for invite in pendingInviteList:
                        await dmChannel.send(f"**Is nan?:** {str(invite)}\n**inviteSent:** {str(invite.createdAt)}\n**email:** {invite.email}\n**isFriend:** {str(invite.friend)}\n**serverShare:** {str(invite.servers[0])}\n**username:** {invite.username}\n**friendlyName:** {invite.friendlyName}\n--------")
                else:
                    await dmChannel.send(f"There are no pending invites.")
            except Exception as e:
                logging.error(f"Error from listallpendinginvites {str(e)}")
    
    @bot.command(description="ADMIN")
    async def dbinfodiscordid(ctx, discordid=None):
        dmChannel = await ctx.author.create_dm()
        adminID = getAdminDiscordID(DB_CONNECTION)
        if adminID == str(ctx.author.id):
            with DB_CONNECTION:
                values = (f"{bot.command_prefix}dbinfodiscordid", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message))
                recordCommandHistory(DB_CONNECTION, values)
            if discordid == None:
                await dmChannel.send(f"You are missing the discord id")
            else:
                dbinfo = getDBInfoForDiscordID(DB_CONNECTION, discordid)
                if dbinfo == []:
                    await dmChannel.send(f"There is no info for that discord id")
                else:
                    await dmChannel.send(f"**discordID:**  {str(dbinfo[1])}\n**discordUsername:**  {str(dbinfo[2])}\n**discordServerNickname:**  {str(dbinfo[3])}\n**plexUsername:**  {str(dbinfo[4])}\n**plexEmailAddress:**  {str(dbinfo[5])}\n**serverName:**  {str(dbinfo[6])}\n**dateRemoved:**  {str(dbinfo[7])}\n**dateInvited:**  {str(dbinfo[8])}\n**dateQueued:**  {str(dbinfo[9])}\n**status:**  {str(dbinfo[10])}\n**plexUserID:**  {str(dbinfo[11])}")

    @bot.command(description="ADMIN")
    async def updateinactivitydays(ctx, servername=None, numberdays=None):
        dmChannel = await ctx.author.create_dm()
        adminID = getAdminDiscordID(DB_CONNECTION)
        if adminID == str(ctx.author.id):
            with DB_CONNECTION:
                values = (f"{bot.command_prefix}updateinactivitydays", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message))
                recordCommandHistory(DB_CONNECTION, values)
            if servername == None or numberdays == None:
                await dmChannel.send(f"you are missing servername, numberofdays, or both.")
            else:
                with DB_CONNECTION:
                    updateInactivityForServerName(DB_CONNECTION, str(servername), str(numberdays))
                    serverConfig = getPlexServerConfigInfoForName(DB_CONNECTION, str(servername))
                await dmChannel.send(f"Inactivity updated to {str(serverConfig[8])} days for server: {str(serverConfig[1])}")

    @bot.command(description="ADMIN")
    async def updateinviteacceptancelimit(ctx, servername=None, limitdays=None):
        dmChannel = await ctx.author.create_dm()
        adminID = getAdminDiscordID(DB_CONNECTION)
        if adminID == str(ctx.author.id):
            with DB_CONNECTION:
                values = (f"{bot.command_prefix}updateinviteacceptancelimit", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message))
                recordCommandHistory(DB_CONNECTION, values)
            if servername == None or limitdays == None:
                await dmChannel.send(f"you are missing servername, limitdays, or both.")
            else:
                with DB_CONNECTION:
                    updateInviteAcceptanceLimitForServerName(DB_CONNECTION, str(servername), str(limitdays))
                    serverConfig = getPlexServerConfigInfoForName(DB_CONNECTION, str(servername))
                await dmChannel.send(f"Invite acceptance limit updated to {str(serverConfig[9])} days for server: {str(serverConfig[1])}")

    @bot.command(description="ADMIN")
    async def updatetautulliurl(ctx, servername=None, newurl=None):
        dmChannel = await ctx.author.create_dm()
        adminID = getAdminDiscordID(DB_CONNECTION)
        if adminID == str(ctx.author.id):
            with DB_CONNECTION:
                values = (f"{bot.command_prefix}updatetautulliurl", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message))
                recordCommandHistory(DB_CONNECTION, values)
            if servername == None or newurl == None:
                await dmChannel.send(f"you are missing servername, newurl, or both.")
            else:
                with DB_CONNECTION:
                    updateTautulliURLForServerName(DB_CONNECTION, str(servername), str(newurl))
                    serverConfig = getPlexServerConfigInfoForName(DB_CONNECTION, str(servername))
                await dmChannel.send(f"Tautulli URL updated to {str(serverConfig[6])} for server: {str(serverConfig[1])}")
    
    @bot.command(description="ADMIN")
    async def updatetautulliapikey(ctx, servername=None, newapikey=None):
        dmChannel = await ctx.author.create_dm()
        adminID = getAdminDiscordID(DB_CONNECTION)
        if adminID == str(ctx.author.id):
            with DB_CONNECTION:
                values = (f"{bot.command_prefix}updatetautulliapikey", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message))
                recordCommandHistory(DB_CONNECTION, values)
            if servername == None or newapikey == None:
                await dmChannel.send(f"you are missing servername, newapikey, or both.")
            else:
                with DB_CONNECTION:
                    updateTautulliAPIKeyForServerName(DB_CONNECTION, str(servername), str(newapikey))
                    serverConfig = getPlexServerConfigInfoForName(DB_CONNECTION, str(servername))
                await dmChannel.send(f"Tautulli API key updated to {str(serverConfig[7])} for server: {str(serverConfig[1])}")
    
    @bot.command(description="ADMIN")
    async def updateserverurl(ctx, servername=None, url=None):
        dmChannel = await ctx.author.create_dm()
        adminID = getAdminDiscordID(DB_CONNECTION)
        if adminID == str(ctx.author.id):
            with DB_CONNECTION:
                values = (f"{bot.command_prefix}updateserverurl", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message))
                recordCommandHistory(DB_CONNECTION, values)
            if servername == None or url == None:
                await dmChannel.send(f"you are missing servername, url, or both.")
            else:
                with DB_CONNECTION:
                    updateServerURLForServerName(DB_CONNECTION, str(servername), str(url))
                    serverConfig = getPlexServerConfigInfoForName(DB_CONNECTION, str(servername))
                await dmChannel.send(f"URL updated to {str(serverConfig[2])} for server: {str(serverConfig[1])}")

    @bot.command(description="ADMIN")
    async def updateservertoken(ctx, servername=None, token=None):
        dmChannel = await ctx.author.create_dm()
        adminID = getAdminDiscordID(DB_CONNECTION)
        if adminID == str(ctx.author.id):
            with DB_CONNECTION:
                values = (f"{bot.command_prefix}updateservertoken", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message))
                recordCommandHistory(DB_CONNECTION, values)
            if servername == None or token == None:
                await dmChannel.send(f"you are missing servername, token, or both.")
            else:
                with DB_CONNECTION:
                    updateServerTokenForServerName(DB_CONNECTION, str(servername), str(token))
                    serverConfig = getPlexServerConfigInfoForName(DB_CONNECTION, str(servername))
                await dmChannel.send(f"Token updated to {str(serverConfig[3])} for server: {str(serverConfig[1])}")

    @bot.command(description="ADMIN")
    async def updatechecksinactivity(ctx, servername=None, checks=None):
        dmChannel = await ctx.author.create_dm()
        adminID = getAdminDiscordID(DB_CONNECTION)
        if adminID == str(ctx.author.id):
            with DB_CONNECTION:
                values = (f"{bot.command_prefix}updatechecksinactivity", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message))
                recordCommandHistory(DB_CONNECTION, values)
            if servername == None or checks == None:
                await dmChannel.send(f"you are missing servername, checksvalue, or both.")
            else:
                with DB_CONNECTION:
                    updateChecksInactivityForServerName(DB_CONNECTION, str(servername), str(checks))
                    serverConfig = getPlexServerConfigInfoForName(DB_CONNECTION, str(servername))
                await dmChannel.send(f"Activity check updated to {str(serverConfig[4])} for server: {str(serverConfig[1])}")

    @bot.command(description="ADMIN")
    async def updateemailfordiscordid(ctx, discordid=None, newemail=None):
        dmChannel = await ctx.author.create_dm()
        adminID = getAdminDiscordID(DB_CONNECTION)
        if adminID == str(ctx.author.id):
            with DB_CONNECTION:
                values = (f"{bot.command_prefix}updateemailfordiscordid", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message))
                recordCommandHistory(DB_CONNECTION, values)
            if discordid == None or newemail == None:
                await dmChannel.send(f" you are missing discord id, new email, or both.")
            else:
                with DB_CONNECTION:
                    updateEmailForDiscordID(DB_CONNECTION, str(discordid), str(newemail))
                    userinfo = getDBInfoForDiscordID(DB_CONNECTION, str(discordid))
                await dmChannel.send(f"Email updated to {str(userinfo[5])} for user: {str(userinfo[1])}")

    @bot.command(description="ADMIN")
    async def watchtimefordiscordid(ctx, discordid=None):
        dmChannel = await ctx.author.create_dm()
        adminID = getAdminDiscordID(DB_CONNECTION)
        if adminID == str(ctx.author.id):
            with DB_CONNECTION:
                values = (f"{bot.command_prefix}watchtimefordiscordid", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message))
                recordCommandHistory(DB_CONNECTION, values)
            if discordid == None:
                await dmChannel.send(f" you are missing discord id.")
            else:
                with DB_CONNECTION:
                    watchtime = getWatchTimeForDiscordID(DB_CONNECTION, str(discordid))
                prettytime = time_format(watchtime)
                if watchtime == 0:
                    await dmChannel.send(f"no tautulli watch time for that discord id")
                else:
                    await dmChannel.send(f"watch time for that discord id is: {prettytime}")
    
    @bot.command(description="ADMIN")
    async def removeuser(ctx, discordid=None):
        dmChannel = await ctx.author.create_dm()
        adminID = getAdminDiscordID(DB_CONNECTION)
        if adminID == str(ctx.author.id):
            with DB_CONNECTION:
                values = (f"{bot.command_prefix}removeuser", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message))
                recordCommandHistory(DB_CONNECTION, values)
            if discordid == None:
                await dmChannel.send(f"You are missing the discord id")
            else:
                success = True
                with DB_CONNECTION:
                    try:
                        await deleteFromPlexTautulliAndDB(DB_CONNECTION, discordid)
                        success = True
                    except Exception as e:
                        success = False
                        logging.error(f"Error removing user. Exception: {str(e)}")
                if success:
                    await dmChannel.send(f"User Removed")
                else:
                    await dmChannel.send(f"Unable to remove user. Exception occurred: {str(e)}")
    
    @bot.command(description="ADMIN")
    async def deleteuserfromdb(ctx, discordid):
        dmChannel = await ctx.author.create_dm()
        adminID = getAdminDiscordID(DB_CONNECTION)
        if adminID == str(ctx.author.id):
            with DB_CONNECTION:
                values = (f"{bot.command_prefix}deleteuserfromdb", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message))
                recordCommandHistory(DB_CONNECTION, values)
            success = True
            if discordid == None:
                await dmChannel.send(f"You are missing the discord id")
            else:
                with DB_CONNECTION:
                    try:
                        deleteFromDBForDiscordID(DB_CONNECTION, discordid)
                        success = True
                    except Exception as e:
                        logging.error(f"Exception deleting user from Bot DB. Exception: {str(e)}")
                        success = False
                if success:
                    await dmChannel.send(f"User deleted from Bot DB")
                else:
                    await dmChannel.send(f"Error removing the user from bot DB.")
    
    @bot.command(description="ADMIN")
    async def cleartautullihistory(ctx, discordid=None):
        dmChannel = await ctx.author.create_dm()
        adminID = getAdminDiscordID(DB_CONNECTION)
        if adminID == str(ctx.author.id):
            with DB_CONNECTION:
                values = (f"{bot.command_prefix}cleartautullihistory", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message))
                recordCommandHistory(DB_CONNECTION, values)
            success = True
            if discordid == None:
                await dmChannel.send(f"Missing discord id.")
            else:
                try:
                    removeFromTautulliByDiscordID(DB_CONNECTION, discordid)
                    success = True
                except Exception as e:
                    success = False
                    logging.error(f"Exception clearing users tautulli history. Exception: {str(e)}")
                if success:
                    await dmChannel.send(f"cleared users tautulli history.")
                else:
                    await dmChannel.send(f"Issue clearing users tautulli history. check logs.")
    
    @bot.command(description="ADMIN")
    async def listusers(ctx):
        dmChannel = await ctx.author.create_dm()
        adminID = getAdminDiscordID(DB_CONNECTION)
        if adminID == str(ctx.author.id):
            with DB_CONNECTION:
                values = (f"{bot.command_prefix}listusers", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message))
                recordCommandHistory(DB_CONNECTION, values)
            success = True
            try:
                users = getUsersListFromDB(DB_CONNECTION)
                success = True
            except Exception as e:
                success = False
                logging.error(f"Exception getting users list from DB. Exception: {str(e)}")
            if success and len(users) > 0:
                userlist = "```"
                for user in users:
                    userlist += f"ID: {user[1]}, UN: {user[2]}\npID: {user[11]}, pUN: {user[4]}\nemail: {user[5]}, server: {user[6]}, status: {user[10]}\n"
                userlist += "```"
                if len(userlist) > 2000:
                    userlistforfile = ""
                    userlistforfile += f"DiscordID, DiscordUsername, PlexID, PlexUsername, Email, PlexServer, Status, DateRemoved, DateInvited, DateQueued\n"
                    for user in users:
                        userlistforfile += f"{user[1]}, {user[2]}, {user[11]}, {user[4]}, {user[5]}, {user[6]}, {user[10]}, {str(user[7])}, {str(user[8])}, {str(user[9])}\n"
                    buffer = StringIO(userlistforfile)
                    f = discord.File(buffer, filename="userlist.txt")
                    await dmChannel.send(f"Length of message is too long, sending txt file instead\n")
                    await dmChannel.send(file=f)
                else:
                    await dmChannel.send(f"length of coming message: {str(len(userlist))}")
                    await dmChannel.send(f"{userlist}")
            else:
                await dmChannel.send(f"issue getting user list. check logs.")
    
    # to do
    # @bot.command(description="ADMIN")
    # async def listusers(ctx):
    # endregion

    
else:
    @bot.command()
    async def help(ctx):
        await ctx.send(f"Bot is not configured. Try {bot.command_prefix}configure")
    
    @bot.command(description="ADMIN")
    @commands.has_permissions(administrator=True)
    async def configure(ctx, adminid=None, adminrolename=None, botchannelid=None, queuedrolename=None, removedrolename=None, commandprefix=None, notificationschannelid=None):
        with DB_CONNECTION:
            values = (f"{bot.command_prefix}configure", str(ctx.channel), str(ctx.author.name), str(ctx.author.id), str(datetime.datetime.now()), str(ctx.message))
            recordCommandHistory(DB_CONNECTION, values)
        if (adminid==None or adminrolename==None or botchannelid==None or queuedrolename==None or removedrolename==None or commandprefix==None or notificationschannelid==None):
            await ctx.send(f"You are missing a required parameter.\nYou need administratorDiscordID, botAdminDiscordRole, botChannelID, queuedRoleName, removedRoleName, commandPrefix, botNotificationsChannelID")
        else:
            valuesToSend = (str(adminid), str(adminrolename), str(botchannelid), str(queuedrolename), str(removedrolename), str(commandprefix), "TRUE", str(notificationschannelid))
            with DB_CONNECTION:
                configureBot(DB_CONNECTION, valuesToSend)
            game = discord.Game(name=f"DM me with {commandprefix}help")
            await bot.change_presence(activity=game)
            await ctx.send(f"Bot is now configured! Restarting the bot for changes to take affect...")
            restart_bot()

# endregion


async def main():
    frequent.start()
    infrequent.start()
    await bot.start(TOKEN)

asyncio.run(main())
