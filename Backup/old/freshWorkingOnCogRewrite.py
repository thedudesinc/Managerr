import datetime
import sqlite3
from sqlite3 import Error
import discord
from discord.ext import commands
from discord.ext.tasks import loop
from requests import Session
from plexapi.server import PlexServer
from datetime import date, timedelta
import threading, time

# region static variable
intents = discord.Intents.all()
intents.members = True
client = discord.Client(intents=intents)
GUILD_ID = 1045433182822072390
MY_GUILD = client.get_guild(GUILD_ID)
database = r"BotDB.db"
DB_CONNECTION = None
botConfigured = None
CLIENT_TOKEN = "MTA0NTQzNTMyMjkxMTE3ODgzMg.G8sx3m.WJRT222gc2DKbra_9jZE3UtZbkq_njnx9tAThE"


# endregion


# region Methods
def createDBTables(conn):
    try:
        sqlBAH = ''' CREATE TABLE IF NOT EXISTS "BotActionHistory" 
            ("action" TEXT, "dateTime" TEXT, "automaticOrManual" TEXT); '''
        cur1 = conn.cursor()
        cur1.execute(sqlBAH)
        sqlBCommand = ''' CREATE TABLE IF NOT EXISTS "BotCommands" 
            ( "commandName" TEXT UNIQUE, "commandReturnMessage" TEXT, "isAdminCommand" INTEGER); '''
        cur2 = conn.cursor()
        cur2.execute(sqlBCommand)
        sqlBConfig = ''' CREATE TABLE IF NOT EXISTS "BotConfiguration" 
            ("administratorDiscordID" TEXT, "botAdminDiscordRole" TEXT, "botChannelID" TEXT, "queuedRole" TEXT, 
            "removedRole" TEXT, "commandPrefix" TEXT NOT NULL DEFAULT '!!!', "configured" TEXT DEFAULT 'False', 
            "botNotificationsChannelID" TEXT); '''
        cur3 = conn.cursor()
        cur3.execute(sqlBConfig)
        sqlCH = ''' CREATE TABLE IF NOT EXISTS "CommandHistory" 
            ("commandName" TEXT NOT NULL, "discordServerNickname" TEXT NOT NULL, "discordUsername" TEXT NOT NULL, 
            "discordID" TEXT NOT NULL, "dateTime" TEXT NOT NULL, "valueSent" TEXT); '''
        cur4 = conn.cursor()
        cur4.execute(sqlCH)
        sqlPSC = ''' CREATE TABLE IF NOT EXISTS "PlexServerConfiguration" 
            ("psc_PK" INTEGER NOT NULL UNIQUE, "serverName" TEXT NOT NULL UNIQUE, "serverURL" TEXT NOT NULL UNIQUE, 
            "serverToken" TEXT NOT NULL UNIQUE, "checksInactivity" TEXT, "invitedDiscordRole" TEXT, "tautulliURL" TEXT, 
            "tautulliAPIKey" TEXT, "inactivityLimit" TEXT, "inviteAcceptanceLimit" TEXT, 
            PRIMARY KEY("psc_PK" AUTOINCREMENT)); 
            '''
        cur5 = conn.cursor()
        cur5.execute(sqlPSC)
        sqlU = ''' CREATE TABLE IF NOT EXISTS "Users" 
            ("u_PK" INTEGER NOT NULL UNIQUE, "discordID" TEXT NOT NULL UNIQUE, "discordUsername" TEXT, 
            "discordServerNickname"	TEXT, "plexUsername" TEXT DEFAULT 'UNKNOWN', 
            "plexEmailAddress" TEXT NOT NULL UNIQUE, "serverName" TEXT, "dateRemoved" TEXT, "dateInvited" TEXT, 
            "dateQueued" TEXT, "status" TEXT, "plexUserID" TEXT DEFAULT 'UNKNOWN', PRIMARY KEY("u_PK" AUTOINCREMENT)); '''
        cur6 = conn.cursor()
        cur6.execute(sqlU)
    except Exception as e:
        print('Exception from createDBTables: ' + str(e))
    return


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
        print('Exception from getBotChannelID: ' + str(e))
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
            if str(value) == 'True':
                botConfiguredBool = True
            else:
                botConfiguredBool = False
    except Exception as e:
        print('Exception from getBotConfiguredBool: ' + str(e))
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
        print('Exception from getCommandPrefix: ' + str(e))
    return commandPrefix


def configureBot(conn, values):
    sql = ''' INSERT INTO BotConfiguration(administratorDiscordID,botAdminDiscordRole,botChannelID,queuedRole,
                removedRole,commandPrefix,configured,botNotificationsChannelID) 
                VALUES(?,?,?,?,?,?,?,?) '''
    try:
        cur = conn.cursor()
        cur.execute(sql, values)
    except Exception as e:
        print('Error from configureBot: ' + str(e))
    return


def recordCommandHistory(conn, values):
    sql = ''' INSERT INTO CommandHistory(commandName,discordServerNickname,discordUsername,discordID,dateTime,valueSent) 
                    VALUES(?,?,?,?,?,?) '''
    try:
        cur = conn.cursor()
        cur.execute(sql, values)
    except Exception as e:
        print('error from recordCommandHistory' + str(e))
    return


def recordBotActionHistory(conn, actionText, autoOrMan):
    date1 = str(datetime.datetime.now())
    try:
        cur = conn.cursor()
        cur.execute('INSERT INTO BotActionHistory(action,dateTime,automaticOrManual) VALUES(?,?,?)',
                    (actionText, date1, autoOrMan,))
    except Exception as e:
        print('error from recordBotActionHistory: ' + str(e))
    return


def recordPlexServerEntry(conn, values):
    sql = ''' INSERT INTO PlexServerConfiguration(serverName,serverURL,serverToken,checksInactivity,invitedDiscordRole,
    tautulliURL,tautulliAPIKey,inactivityLimit,inviteAcceptanceLimit) VALUES(?,?,?,?,?,?,?,?,?) '''
    try:
        cur = conn.cursor()
        cur.execute(sql, values)
    except Exception as e:
        print('error from recordCommandHistory' + str(e))
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
        print('Exception from getAdminDiscordID: ' + str(e))
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
        print('Exception from getNewestPlexServer: ' + str(e))
    return newestPlexServer


def getListOfPlexServers(conn):
    try:
        cur = conn.cursor()
        cur.execute('select * from PlexServerConfiguration')
        listOfPlexServers = cur.fetchall()
    except Exception as e:
        print('Exception from getListOfPlexServers: ' + str(e))
    return listOfPlexServers


def getUsersListFromDB(conn):
    try:
        cur = conn.cursor()
        cur.execute('select * from Users')
        listOfUsers = cur.fetchall()
    except Exception as e:
        print('Exception from getUsersListFromDB: ' + str(e))
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
        print('Exception from getPlexServerConfigInfoForName: ' + str(e))
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
        print('Exception from getBotConfigurationInfo: ' + str(e))
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
        print('Exception from getDBInfoForDiscordID: ' + str(e))
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
            print('exception from getUserCountForPlexServerName: ' + str(e))

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
        print('Exception from getFirstPlexServerNameWithOpenSpots: ' + str(e))
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
                    print('Exception from cancelPendingInvitesOverXDays for invite email: '
                          + str(invite.email) + ', server:' + str(invite.servers) + ', error: ' + str(e))
                    continue
            except Exception as e:
                print('Exception from server loop of cancelPendingInvitesOverXDays' + str(e))
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
            print('exception from cancelPendingInviteForDiscordID: ' + str(e))
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
                print('Exception from listAllPendingInvites: ' + str(e))
        else:
            print("didnt get a whole row from the database for that serverName")
    return allPendingInvites


def updateBotChannelID(conn, values):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE BotConfiguration SET botChannelID =(?) WHERE administratorDiscordID =(?)', values)
    except Exception as e:
        print('error from updateBotChannelID: ' + str(e))
    return


def updateCommandPrefix(conn, values):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE BotConfiguration SET commandPrefix =(?) WHERE administratorDiscordID =(?)', values)
    except Exception as e:
        print('error from updateCommandPrefix: ' + str(e))
    return


def updateInactivityForServerName(conn, serverName, days):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE PlexServerConfiguration SET inactivityLimit =(?) WHERE serverName =(?)',
                    (str(days), str(serverName),))
    except Exception as e:
        print('error from updateInactivityForServerName: ' + str(e))
    return


def updateInviteAcceptanceLimitForServerName(conn, serverName, days):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE PlexServerConfiguration SET inviteAcceptanceLimit =(?) WHERE serverName =(?)',
                    (str(days), str(serverName),))
    except Exception as e:
        print('error from updateInviteAcceptanceLimitForServerName: ' + str(e))
    return


def updateTautulliURLForServerName(conn, serverName, url):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE PlexServerConfiguration SET tautulliURL =(?) WHERE serverName =(?)',
                    (str(url), str(serverName),))
    except Exception as e:
        print('error from updateTautulliURLForServerName: ' + str(e))
    return


def updateTautulliAPIKeyForServerName(conn, serverName, apikey):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE PlexServerConfiguration SET tautulliAPIKey =(?) WHERE serverName =(?)',
                    (str(apikey), str(serverName),))
    except Exception as e:
        print('error from updateTautulliAPIKeyForServerName: ' + str(e))
    return


def updateServerURLForServerName(conn, serverName, serverURL):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE PlexServerConfiguration SET serverURL =(?) WHERE serverName =(?)',
                    (str(serverURL), str(serverName),))
    except Exception as e:
        print('error from updateServerURLForServerName: ' + str(e))
    return


def updateServerTokenForServerName(conn, serverName, serverToken):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE PlexServerConfiguration SET serverToken =(?) WHERE serverName =(?)',
                    (str(serverToken), str(serverName),))
    except Exception as e:
        print('error from updateServerTokenForServerName: ' + str(e))
    return


def getListOfPlexThatChecks(conn):
    try:
        yesString = 'YES'
        cur = conn.cursor()
        cur.execute('select * from PlexServerConfiguration where checksInactivity = (?)', (yesString,))
        plexChecksList = cur.fetchall()
    except Exception as e:
        print('Exception from getListOfPlexThatChecks: ' + str(e))
    return plexChecksList


def updateChecksInactivityForServerName(conn, serverName, checks):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE PlexServerConfiguration SET checksInactivity =(?) WHERE serverName =(?)',
                    (str(checks), str(serverName),))
    except Exception as e:
        print('error from updateChecksInactivityForServerName: ' + str(e))
    return


def updateEmailForDiscordID(conn, discordID, newEmail):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE Users SET plexEmailAddress =(?) WHERE discordID =(?)', (str(newEmail), str(discordID),))
    except Exception as e:
        print('error from updateEmailForDiscordID: ' + str(e))
    return


def updateStatusForDiscordID(conn, discordID, status):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE Users SET status =(?) WHERE discordID =(?)', (str(status), str(discordID),))
    except Exception as e:
        print('error from updateStatusForDiscordID: ' + str(e))
    return


def setRemovalDateForDiscordID(conn, discordID):
    dateNowString = str(datetime.datetime.now())
    try:
        cur = conn.cursor()
        cur.execute('UPDATE Users SET dateRemoved =(?) WHERE discordID =(?)', (dateNowString, str(discordID),))
    except Exception as e:
        print('error from setRemovalDateForDiscordID: ' + str(e))
    return

def updateBotActionHistory(conn, values):
    sql = ''' INSERT INTO BotActionHistory(action,dateTime,automaticOrManual) VALUES(?,?,?) '''
    cur = conn.cursor()
    try:
        cur.execute(sql, values)
    except Exception as e:
        print('error from updateBotActionHistory: ' + str(e))
    return


def updateUsernameForPlexEmailAddress(conn, email, username):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE Users SET plexUsername =(?) WHERE plexEmailAddress =(?)', (str(username), str(email),))
    except Exception as e:
        print('error from updateUsernameForPlexEmailAddress: ' + str(e))
    return


def updatePlexIDForPlexEmailAddress(conn, email, plexID):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE Users SET plexUserID =(?) WHERE plexEmailAddress =(?)', (str(plexID), str(email),))
    except Exception as e:
        print('error from updatePlexIDForPlexEmailAddress: ' + str(e))
    return


def updateQueuedUserToInvited(conn, values):
    try:
        cur = conn.cursor()
        cur.execute('UPDATE Users SET serverName =(?), dateInvited =(?), status =(?) WHERE discordID =(?)',
                    (str(values[1]), str(values[2]), str(values[3]), str(values[0]),))
    except Exception as e:
        print('error from updateQueuedUserToInvited: ' + str(e))
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
        print('Exception from getStatusForDiscordID: ' + str(e))
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
        print('Exception from getEmailForDiscordID: ' + str(e))
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
        print('Exception from getTotalOpenSpots: ' + str(e))
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
        print('Exception from checkDiscordIDExists: ' + str(e))
    return discordIDExists


def insertInvitedUser(conn, values):
    sql = ''' INSERT INTO Users(discordID,discordUsername,discordServerNickname,plexUsername,plexEmailAddress,
        serverName,dateInvited,status) VALUES(?,?,?,?,?,?,?,?) '''
    try:
        cur = conn.cursor()
        cur.execute(sql, values)
    except Exception as e:
        print('error from insertInvitedUser' + str(e) + " values: " + str(values))
    return


def insertQueuedUser(conn, values):
    sql = ''' INSERT INTO Users(discordID,discordUsername,plexEmailAddress,dateQueued,status) VALUES(?,?,?,?,?) '''
    try:
        cur = conn.cursor()
        cur.execute(sql, values)
    except Exception as e:
        print('error from insertQueuedUser' + str(e))
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
        print('error from inviteEmailToPlex: ' + str(e))
        inviteSuccess = False
    if inviteSuccess:
        try:
            with DB_CONNECTION:
                uValues = (str(values[0]), str(values[1]), str(values[2]), 'UNKNOWN', email, str(values[3]),
                           str(date1), '2')
                insertInvitedUser(DB_CONNECTION, uValues)
        except Exception as e:
            print('error from within invite success: ' + str(e))
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
        print('error from inviteQueuedEmailToPlex: ' + str(e))
        inviteSuccess = False
    if inviteSuccess:
        try:
            serverDiscordRole = rowTuple[5]
            with DB_CONNECTION:
                uValues = (discordID, serverName, str(date1), '2')
                updateQueuedUserToInvited(DB_CONNECTION, uValues)
                await addRoleForDiscordID(DB_CONNECTION, serverDiscordRole, discordID, guildID)
        except Exception as e:
            print('error from within invite success: ' + str(e))
    else:
        print("invite success is not true for some reason")
    return inviteSuccess


async def addRoleForDiscordID(conn, discordRoleName, discordID, guildID):
    try:
        thisGuild = client.get_guild(guildID)
        member = discord.utils.get(thisGuild.members, id=int(discordID))
        roleToAdd = discord.utils.get(thisGuild.roles, name=discordRoleName)
        if member is not None:
            await member.add_roles(roleToAdd)
            await member.create_dm()
            await member.dm_channel.send(discordRoleName + ' role has been added to you.')
            with conn:
                recordBotActionHistory(conn, 'added role: '
                                       + discordRoleName + ' to discord member: ' + str(member.name), 'AUTOMATIC')
    except Exception as e:
        print('error from addRoleForDiscordID: ' + str(e))
    return


async def removeRoleForDiscordID(conn, discordRoleName, discordID, guildID):
    try:
        thisGuild = client.get_guild(guildID)
        member = discord.utils.get(thisGuild.members, id=int(discordID))
        roleToRemove = discord.utils.get(thisGuild.roles, name=discordRoleName)
        if member is not None:
            await member.remove_roles(roleToRemove)
            await member.create_dm()
            await member.dm_channel.send(discordRoleName + ' role has been removed from you')
            with conn:
                recordBotActionHistory(conn, 'removed role: '
                                       + discordRoleName + ' from discord member: ' + str(member.name), 'AUTOMATIC')
        else:
            print('member was None. Probably because they left the server.')
    except Exception as e:
        print('exception from removeRoleForDiscordID: ' + str(e))
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
        print('Exception from getDateQueuedForDiscordID: ' + str(e))
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
        print('Exception from getStatusForEmail: ' + str(e))
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
        print('Exception from getDiscordIDForEmail: ' + str(e))
    return discordIDForEmail


def getCountQueuedAheadOfDate(conn, dateQueued):
    countQueuedAhead = 0
    cur = conn.cursor()
    try:
        cur.execute('select count() from Users where status = 4 and dateQueued < (?)', (str(dateQueued),))
    except Exception as e:
        print('error from getCountQueuedAheadOfDate: ' + str(e))
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
        print('Exception from getUsersNoUsername: ' + str(e))
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
        print('Exception from getUsersNoPlexID: ' + str(e))
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
        print('Exception from getUsersQueued: ' + str(e))
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
        print('Exception from getDiscordIDForOldestQueuedUser: ' + str(e))
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
        print('Exception from getUsernameForDiscordID: ' + str(e))
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
        print('Exception from getDateInvitedByEmail: ' + str(e))
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
        print('Exception from removeServerNameForDiscordID: ' + str(e))
    return


def getQueueStatusForDiscordID(conn, discordID):
    try:
        dateQueued = getDateQueuedForDiscordID(conn, discordID)
        queuedAhead = getCountQueuedAheadOfDate(conn, dateQueued)
    except Exception as e:
        print('Exception from getQueueStatusForDiscordID: ' + str(e))
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
        print('Exception from getInvitedDiscordRoleNameForServerName: ' + str(e))
    return invitedDiscordRoleName


def deleteFromDBForDiscordID(conn, discordID):
    try:
        cur = conn.cursor()
        cur.execute('delete from Users where discordID = (?)', (discordID,))
        recordBotActionHistory(conn, 'deleted from users table by discordID: ' + str(discordID), 'AUTOMATIC')
    except Exception as e:
        print('exception from deleteFromDBForDiscordID: ' + str(e))
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
        print('exception from removeFriendFromPlex: ' + str(e))
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
        'cmd': 'delete_user',
        'user_id': plexUserID,
        'apikey': TAUTULLI_APIKEY
    }
    # SESSION.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=PARAMS).json()
    try:
        localSession.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=PARAMS1).json()
    except Exception as e:
        print("Tautulli API 'delete_user' request failed. Error: {}.".format(e))
    return


def deleteFromPlexTautulliAndDB(conn, discordID):
    try:
        removeFriendFromPlexByDiscordID(discordID)
        removeFromTautulliByDiscordID(discordID)
        deleteFromDBForDiscordID(conn, discordID)
        recordBotActionHistory(conn, 'deleted removed from Plex, Tautulli, and DB for discordID: '
                               + str(discordID), 'AUTOMATIC')
    except Exception as e:
        print('exception from deleteFromPlexTautulliAndDB: ' + str(e))
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
        print('exception from getWatchTimeForDiscordID: ' + str(e))
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
        print('exception from getCurrentStreams: ' + str(e))

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
        print('Exception from listPendingInvitesForServer: ' + str(e))
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


# region pre-discord client actions
try:
    DB_CONNECTION = sqlite3.connect(database)
except Error as e:
    print('error from creating DB_CONNECTION' + str(e))
try:
    createDBTables(DB_CONNECTION)
except Error as e:
    print('error from calling createDBTables' + str(e))
# endregion

with DB_CONNECTION:
    botConfigured = getBotConfiguredBool(DB_CONNECTION)

# region Client Events
# onready event
if not botConfigured:
    # region bot NOT configured on_ready event
    @client.event
    async def on_ready():
        # region on_ready variables
        # endregion
        print("The bot is ready!")
    # endregion
else:
    # region bot configured on_ready event
    @client.event
    async def on_ready():
        # region on_ready variables
        with DB_CONNECTION:
            commandPrefix = getCommandPrefix(DB_CONNECTION)
        game = discord.Game(name="DM me with " + commandPrefix + "help")
        thisGuild = client.get_guild(GUILD_ID)
        await client.change_presence(activity=game)

        # endregion

        # region repeated actions by the bot
        @loop(hours=6)
        async def frequent():
            # if frequent loop is being blocked by infrequent loop, then i shouldnt have to adjust the time of exceution.
            print('frequent loop is Started: ' + str(datetime.datetime.now()))
            with DB_CONNECTION:
                plexServers = getListOfPlexServers(DB_CONNECTION)
                databaseUsersNoPlexUsername = getUsersNoUsername(DB_CONNECTION)
                databaseUsersNoPlexID = getUsersNoPlexID(DB_CONNECTION)
                discordUsersList = getUsersListFromDB(DB_CONNECTION)
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
                    print('Error getting server object. Error: ' + str(e))
                try:
                    usersList = ACCOUNT.users()
                    pendingInvites = ACCOUNT.pendingInvites(includeSent=True, includeReceived=False)
                    emailUserNameDictionary = {user.email.lower(): user.username.lower() for user in usersList}
                    emailUserIDDictionary = {user.email.lower(): user.id for user in usersList}
                    gotServerUsersSuccess = True
                except Exception as e:
                    gotServerUsersSuccess = False
                    with DB_CONNECTION:
                        recordBotActionHistory(DB_CONNECTION, 'error from trying to get plex users for plex server: ' + str(plex[1]) + ' error: ' + str(e), 'AUTOMATIC')
                    print('error from trying to get plex users for plex server: ' + str(plex[1]) + ' error: ' + str(e))
                if gotServerUsersSuccess:
                    date1 = datetime.datetime.now()
                    # region update status for plex user in database
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
                            print("found email " + str(xEmail) + " in plex, that does not line up with email in database. this should not be possible. username:" + str(xUsername))
                            with DB_CONNECTION:
                                recordBotActionHistory(DB_CONNECTION, 'found email in plex, that does not line up with email in database. This should not be possible.' + xEmail, 'AUTOMATIC')
                    # endregion
                    # region update Username in database if UNKNOWN
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
                    # region cancel pending invites over (server number) days
                    # cancelPendingInvitesOverXDays(int(plex[9]))
                    # endregion
                    # region invite queued users if openspots
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
                                    successBool = await inviteQueuedEmailToPlex(DB_CONNECTION, discordIDForOldestQueued, serverName, emailForOldestQueued, GUILD_ID)
                                    if successBool:
                                        member = discord.utils.get(MY_GUILD.members, id=int(discordID))
                                        member.dm_channel.send(f"There were open spots and you have been invited to server: {serverName}")
                                    # else DM them/admin that something went wrong.
                                    else:
                                        ownerID = discord.Guild.owner_id
                                        member = discord.utils.get(MY_GUILD.members, id=ownerID)
                                        member.dm_channel.send(f"Tried to invite this queued email: {emailForOldestQueued}, for this discordID: {discordIDForOldestQueued}. But something went wrong.")
                                    # if DMing the admin include discord ID and email address value
                            except Exception as e:
                                with DB_CONNECTION:
                                    recordBotActionHistory(DB_CONNECTION, 'something went wrong inviting user: ' + discordIDForOldestQueued + ' email: ' + emailForOldestQueued + ' error: ' + str(e), 'AUTOMATIC')
                                print('something went wrong inviting user: ' + discordIDForOldestQueued + ' email: ' + emailForOldestQueued + ' error: ' + str(e))
                    # endregion
            # region check If DB user is member of discord guild and act
            #     for user in discordUsersList:
            #         member = discord.utils.get(thisGuild.members, id=int(user[1]))
            #         if member is not None:  # if they are a member of the guild
            #             if user[10] == '2':  # pending invite acceptance
            #                 matchingPendingInvite = checkForMatchingPendingInvite(DB_CONNECTION, user[6], user[5])
            #                 if not matchingPendingInvite:  # if there is NOT a matching pending invite
            #                     # updateToRemovedForInvitedDiscordID(DB_Connection, discordID, serverName)
            #                     # DM the user that their status has been changed.
            #                     print('user: ' + user[2] + ' status of pending invite, but didnt match any pending invites. update status to 0 and dm the user about it.')
            #             elif user[10] == '4':  # queued for invite
            #                 with DB_CONNECTION:
            #                     numOpenSpots = getTotalOpenSpots(DB_CONNECTION)
            #                 if numOpenSpots > 0 and numOpenSpots < 9000:
            #                     with DB_CONNECTION:
            #                         serverName = getFirstPlexServerNameWithOpenSpots(DB_CONNECTION)
            #                         # inviteQueuedEmailToPlex(DB_CONNECTION, user[1], serverName, user[5], GUILD_ID)
            #                         print('user in DB and in guild: found a queued user and there were open spots, sending them an invite.')
            #         else:  # if not a member of the discord guild.
            #             if user[10] == '3':
            #                 print('user is in database but not in guild, and they are listed as accepting an invite. Remove from plex, tautulli, and DB')
            #             elif user[10] == '2':
            #                 matchingPendingInvite = checkForMatchingPendingInvite(DB_CONNECTION, user[6], user[5])
            #                 if matchingPendingInvite:
            #                     with DB_CONNECTION:
            #                         thing = ''
            #                         # cancelPendingInviteForDiscordID(DB_CONNECTION, user[1])
            #                         # deleteFromDBForDiscordID(DB_CONNECTION, user[1])
            #                     print('user in db but not guild, found a matching pending invite, so canceled it, and removed them from database')
            #                 else:
            #                     with DB_CONNECTION:
            #                         thing = ''
            #                         # deleteFromDBForDiscordID(DB_CONNECTION, user[1])
            #                     print('user in db but not guild, no matching pending invite, just delete from database')
            #             else:
            #                 with DB_CONNECTION:
            #                     thing = ''
            #                     # deleteFromDBForDiscordID(DB_CONNECTION, user[1])
            #                 print('user was in db but not in Guild, not invited or pending invite so just remove from database.')
            # endregion

            # for user in discordUsersList:
            #     member = discord.utils.get(thisGuild.members, id=int(user[1]))
            #     if member is not None:
            #         # print('there is nothing to do. db entry for member matches member in guild')
            #         thing = ''
            #     else:
            #         with DB_CONNECTION:
            #             recordBotActionHistory(DB_CONNECTION, 'record for discordID: '
            #                                    + user[1] + ' in database but they are not a member of the guild. '
            #                                                'Delete from everywhere', 'AUTOMATIC')
            #         if user[10] == '0':
            #             # if removed for inactivity
            #             with DB_CONNECTION:
            #                 recordBotActionHistory(DB_CONNECTION, 'from frequent task. Check if discordID: '
            #                                        + user[10] + ' in database is in list of guild members. '
            #                                                     'Status 0', 'AUTOMATIC')
            #                 print('would delete here. status 0, db DiscordID: ' + user[1] + ' member ' + str(member))
            #                 # deleteFromDBForDiscordID(DB_CONNECTION, user[1])
            #         elif user[10] == '1':
            #             # if manualy removed
            #             with DB_CONNECTION:
            #                 recordBotActionHistory(DB_CONNECTION, 'from frequent task. Check if discordID: '
            #                                        + user[10] + ' in database is in list of guild members. '
            #                                                     'Status 1', 'AUTOMATIC')
            #                 print('would delete here. status 1, db DiscordID: ' + user[1] + ' member ' + str(member))
            #                 # deleteFromDBForDiscordID(DB_CONNECTION, user[1])
            #         elif user[10] == '2':
            #             # invited but not accepted yet
            #             with DB_CONNECTION:
            #                 # cancelPendingInviteForDiscordID(DB_CONNECTION, user[1])
            #                 # deleteFromDBForDiscordID(DB_CONNECTION, user[1])
            #                 print('would delete here. status 2, db DiscordID: ' + user[1] + ' member ' + str(member))
            #                 recordBotActionHistory(DB_CONNECTION, 'from frequent task. Check if discordID: '
            #                                        + user[1] + ' in database is in list of guild members. member id:'
            #                                        + str(member.id) +
            #                                        ' Status 2', 'AUTOMATIC')
            #                 recordBotActionHistory(DB_CONNECTION, 'Canceled Pending invite and deleted from database '
            #                                                       'for discordID: ' + user[1], 'AUTOMATIC')
            #         elif user[10] == '3':
            #             # invited and accepted
            #             with DB_CONNECTION:
            #                 # deleteFromPlexTautulliAndDB(DB_CONNECTION, user[1])
            #                 print('would delete here. status 3, db DiscordID: ' + user[1] + ' member ' + str(member))
            #                 recordBotActionHistory(DB_CONNECTION, 'from frequent task. Check if discordID: '
            #                                        + user[10] + ' in database is in list of guild members. '
            #                                                     'Status 3', 'AUTOMATIC')
            #                 recordBotActionHistory(DB_CONNECTION, 'Removed Friend from Plex, Tautulli, and database by '
            #                                                       'discordID: ' + user[1], 'AUTOMATIC')
            #         elif user[10] == '4':
            #             # queued for an invite
            #             with DB_CONNECTION:
            #                 # deleteFromDBForDiscordID(DB_CONNECTION, user[1])
            #                 print('would delete here. status 4, db DiscordID: ' + user[1] + ' member ' + str(member))
            #                 recordBotActionHistory(DB_CONNECTION, 'from frequent task. Check if discordID: '
            #                                        + user[10] + ' in database is in list of guild members. '
            #                                                     'Status 4', 'AUTOMATIC')
            #                 recordBotActionHistory(DB_CONNECTION, 'Removed queued user from database by '
            #                                                       'discordID: ' + user[1], 'AUTOMATIC')
            print('frequent loop is Finished: ' + str(datetime.datetime.now()))

        @loop(hours=48)
        async def infrequent():
            announcementsChannelID = 1045449645876334724
            channel = MY_GUILD.get_channel(announcementsChannelID)
            name = MY_GUILD.owner.display_name
            pfp = MY_GUILD.owner.display_avatar
            embed = discord.Embed(title="Inactive User Removal Started", description="This could take a couple hours", color=discord.Color.random())
            embed.set_author(name=f"{name}", url="https://discord.com/channels/1045433182822072390/1045434186825203713", icon_url=pfp.url)
            embed.add_field(name="The bot will not respond to commands during this time")
            embed.set_footer(text=str(datetime.datetime.now()))
            await channel.send(embed=embed)
            print('infrequent loop is Started: ' + str(datetime.datetime.now()))
            # replace this print with a message to announcements.
            # region Check for Inactive Users and Remove
            with DB_CONNECTION:
                # get list of plex servers that check for inactivity
                checksList = getListOfPlexThatChecks(DB_CONNECTION)
            for plex in checksList:
                localSession = Session()
                localSession.verify = False
                if not localSession.verify:
                    # Disable the warning that the request is insecure, we know that...
                    from urllib3 import disable_warnings
                    from urllib3.exceptions import InsecureRequestWarning
                    disable_warnings(InsecureRequestWarning)
                # set incativity limit from the db value for the plex server object
                inactivity_limit = int(plex[8])  # Days to allow inactivity before removing.
                try:
                    # get the server and account object from plex server db values
                    SERVER = PlexServer(baseurl=str(plex[2]), token=str(plex[3]), session=localSession)
                    ACCOUNT = SERVER.myPlexAccount()
                except Exception as e:
                    print('error getting server object: ' + plex[1] + ' ' + str(e))

                # set the date used for searching against plex activity logs.
                dateForMinDate = datetime.datetime.now() - timedelta(days=inactivity_limit)
                UserObjects = ACCOUNT.users()
                for user in UserObjects:
                    # get activity history for user. This is very slow and blocking
                    userHistory = user.history(maxresults=1, mindate=dateForMinDate)
                    with DB_CONNECTION:
                      invitedDate = getDateInvitedByEmail(DB_CONNECTION, user.email)
                    if invitedDate != '':
                        # if the invited date is smaller (older) than the allowed inactivity date and the amount of activity within that allowed window is 0
                        if str(invitedDate) < str(dateForMinDate) and len(userHistory) <= 0:
                            try:
                                ACCOUNT.removeFriend(user)
                                print("removed person Username, email: " + str(user.username) + ", " + str(user.email))
                            except Exception as e1:
                                print("Error removing friend: " + str(e1))
                            try:
                                with DB_CONNECTION:
                                    discordID = getDiscordIDForEmail(DB_CONNECTION, str(user.email))
                                    dbInfoForDiscordID = getDBInfoForDiscordID(DB_CONNECTION, discordID)
                                    serverName = dbInfoForDiscordID[6]
                                    plexServerConfigInfo = getPlexServerConfigInfoForName(DB_CONNECTION, serverName)
                                    invitedRoleName = plexServerConfigInfo[5]
                                    botConfigInfo = getBotConfigurationInfo(DB_CONNECTION)
                                    removedRoleName = botConfigInfo[4]
                            except Exception as e2:
                                print("Exception from getting info from database: " + str(e2))
                            # get the invited and removed roles from discord based on db info
                            invitedRole = discord.utils.get(thisGuild.roles, name=invitedRoleName)
                            removedRole = discord.utils.get(thisGuild.roles, name=removedRoleName)
                            dmmsg = ''
                            # get member object based on discord ID from db info.
                            member = discord.utils.get(thisGuild.members, id=int(discordID))
                            if member is not None:
                                # remove their invited role, add the removed role, and message them about it.
                                await member.remove_roles(invitedRole)
                                await member.add_roles(removedRole)
                                await member.create_dm()
                                try:
                                    await member.dm_channel.send(
                                        "Hi + " + member.name + "! \n\n"
                                        + "You were removed for inactivity!\n"
                                        + "Your status has been updated in my memory, "
                                        + "and your role in my discord server has been updated to **Removed**\n"
                                        + "If you would like to be added back to a share try "
                                        + "responding to me with **" + commandPrefix + "inviteme**"
                                    )
                                    dmmsg = "successful!"
                                except Exception as e:
                                    dmmsg = str(e)
                            with DB_CONNECTION:
                                # record the action in the data base with either removal or exception message.
                                updateStatusForDiscordID(DB_CONNECTION, str(discordID), 0)
                                setRemovalDateForDiscordID(DB_CONNECTION, str(discordID))
                                valuesToSend = ("Inactivity removal. dmmsg" + dmmsg, str(datetime.datetime.now()), "AUTOMATIC")
                                updateBotActionHistory(DB_CONNECTION, valuesToSend)
                                removeServerNameForDiscordID(DB_CONNECTION, discordID)
            # endregion
            print('infrequent loop is Finished: ' + str(datetime.datetime.now()))
            embed2 = discord.Embed(title="Inactive User Removal Finished", color=discord.Color.random())
            embed2.set_author(name=f"{name}", url="https://discord.com/channels/1045433182822072390/1045434186825203713", icon_url=pfp.url)
            embed2.add_field(name="The bot shoudl now respond to commands")
            embed2.set_footer(text=str(datetime.datetime.now()))
            await channel.send(embed=embed2)
            # replace this with finished message to announcements.

        frequent.start()
        infrequent.start()
        print("The bot is ready!")
        # endregion
    # endregion

# onmessage event
if not botConfigured:
    # region bot NOT configured on_message event
    @client.event
    async def on_message(message):
        MY_GUILD = client.get_guild(GUILD_ID)
        owner = MY_GUILD.owner
        if message.author.bot:
            # print("you are a bot!!")
            return
        elif (message.channel.type.name == "private" or message.channel.type.name == "group") and message.content.startswith("!configure"):
            messageArray = message.content.split()
            date1 = datetime.datetime.now()
            if len(messageArray) == 8:
                valuesToSend = (str(messageArray[1]), str(messageArray[2]), str(messageArray[3]), str(messageArray[4]), str(messageArray[5]), str(messageArray[6]), 'True', str(messageArray[7]))
                with DB_CONNECTION:
                    configureBot(DB_CONNECTION, valuesToSend)
                    values = ("!configure", "fromDirectMessage", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                    recordCommandHistory(DB_CONNECTION, values)
                game = discord.Game(name="DM me with " + str(messageArray[6]) + "help")
                configureMessage = ("Successfully configured. Command prefix is now: **" + str(getCommandPrefix(DB_CONNECTION)) + "**" + "\n Restart bot to begin using.")
                await message.reply(configureMessage)
                await client.change_presence(activity=game)
            else:
                configureMessage = ("incorrect number of parameters. Should have **adminDiscordID**, **botAdminDiscordRole**, **botChannelID**, **queuedRoleName**, **removedRoleName**, **commandPrefix**, and **botNotificationsChannelID**\nDO NOT INCLUDE THE COMMAS")
                await message.reply(configureMessage)
        else:
            await message.reply("Bot not configured. Please DM me with !configure")
    # endregion
else:
    # region bot configured on_message event
    @client.event
    async def on_message(message):
        # print("I am evaluating from Bot configured on message")
        if message.author.bot:
            # print("you are a bot!!")
            return
        else:
            # region on_message not bot variables
            date1 = datetime.datetime.now()
            with DB_CONNECTION:
                botChannelID = getBotChannelID(DB_CONNECTION)
                commandPrefix = getCommandPrefix(DB_CONNECTION)
                adminDiscordID = getAdminDiscordID(DB_CONNECTION)
            messageArray = message.content.split()
            # endregion
            if message.channel.type.name == "private" or message.channel.type.name == "group":
                # region create DM to author
                if message.author.dm_channel is None:
                    await message.author.create_dm()
                # endregion
                # region private message admin actions
                if str(message.author.id) == adminDiscordID:
                    if message.content.startswith(commandPrefix + 'updatebotchannelid'):
                        if len(messageArray) == 2:
                            with DB_CONNECTION:
                                values = ("updatebotchannelid", "fromAdminDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                                recordCommandHistory(DB_CONNECTION, values)
                                uValues = (str(messageArray[1]), adminDiscordID)
                                updateBotChannelID(DB_CONNECTION, uValues)
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('Bot Channel ID updated to: ' + str(getBotChannelID(DB_CONNECTION)))
                        else:
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('missing ID parameter')
                    elif message.content.startswith(commandPrefix + 'updatecommandprefix'):
                        if len(messageArray) == 2:
                            with DB_CONNECTION:
                                values = ("updatecommandprefix", "fromAdminDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                                recordCommandHistory(DB_CONNECTION, values)
                                uValues = (str(messageArray[1]), adminDiscordID)
                                updateCommandPrefix(DB_CONNECTION, uValues)
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('Bot Command Prefix updated to: ' + str(getCommandPrefix(DB_CONNECTION)))
                            game = discord.Game(name="DM me with " + str(getCommandPrefix(DB_CONNECTION)) + "help")
                            await client.change_presence(activity=game)
                        else:
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('missing command prefix parameter')
                    elif message.content.startswith(commandPrefix + 'initplexserver'):
                        if len(messageArray) == 10:
                            with DB_CONNECTION:
                                values = ("initplexserver", "fromAdminDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                                recordCommandHistory(DB_CONNECTION, values)
                                iValues = (str(messageArray[1]), str(messageArray[2]), str(messageArray[3]), str(messageArray[4]), str(messageArray[5]), str(messageArray[6]), str(messageArray[7]), str(messageArray[8]), str(messageArray[9]))
                                recordPlexServerEntry(DB_CONNECTION, iValues)
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('Server Added: **' + str(getNewestPlexServer(DB_CONNECTION)) + '**')
                        else:
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('not enough parameters. Should have: serverName serverURL serverToken checksInactivity invitedDiscordRole tautulliURL tautulliAPIKey inactivityLimit inviteAcceptanceLimit')
                    elif message.content == (commandPrefix + 'listplexservers'):
                        with DB_CONNECTION:
                            values = ("listplexservers", "fromAdminDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                            plexServers = getListOfPlexServers(DB_CONNECTION)
                        if message.author.dm_channel is not None:
                            for server in plexServers:
                                userCount = getUserCountForPlexServerName(DB_CONNECTION, str(server[1]))
                                if userCount < 9000:
                                    await message.author.dm_channel.send('**ServerName:** ' + str(server[1]) + '\n**ServerURL:** ' + str(server[2]) + '\n**ServerToken:** ' + str(server[3]) + '\n**ChecksInactivity:** ' + str(server[4]) + '\n**InvitedDiscordRole:** ' + str(server[5]) + '\n**TautulliURL:** ' + str(server[6]) + '\n**TautulliAPIKey:** ' + str(server[7]) + '\n**InactivityLimit:** ' + str(server[8]) + '\n**InviteAcceptanceLimit:** ' + str(server[9]) + '\n**UserCount:** ' + str(userCount) + '\n--------')
                                else:
                                    await message.author.dm_channel.send('**ServerName:** ' + str(server[1]) + '\n**ServerURL:** ' + str(server[2]) + '\n**ServerToken:** ' + str(server[3]) + '\n**ChecksInactivity:** ' + str(server[4]) + '\n**InvitedDiscordRole:** ' + str(server[5]) + '\n**TautulliURL:** ' + str(server[6]) + '\n**TautulliAPIKey:** ' + str(server[7]) + '\n**InactivityLimit:** ' + str(server[8]) + '\n**InviteAcceptanceLimit:** ' + str(server[9]) + '\n**UserCount:** ' + 'cannot be counted right now.\n--------')
                    elif message.content == (commandPrefix + 'listplexserverswithoutcount'):
                        with DB_CONNECTION:
                            values = ("listplexserverswithoutcount", "fromAdminDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                            plexServers = getListOfPlexServers(DB_CONNECTION)
                        if message.author.dm_channel is not None:
                            for server in plexServers:
                                await message.author.dm_channel.send('**ServerName:** ' + str(server[1]) + '\n**ServerURL:** ' + str(server[2]) + '\n**ServerToken:** ' + str(server[3]) + '\n**ChecksInactivity:** ' + str(server[4]) + '\n**InvitedDiscordRole:** ' + str(server[5]) + '\n**TautulliURL:** ' + str(server[6]) + '\n**TautulliAPIKey:** ' + str(server[7]) + '\n**InactivityLimit:** ' + str(server[8]) + '\n**InviteAcceptanceLimit:** ' + str(server[9]) + '\n--------')
                    elif message.content.startswith(commandPrefix + 'clearpendinginvites'):
                        with DB_CONNECTION:
                            values = ("clearpendinginvites", "fromAdminDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        if len(messageArray) == 2:
                            if message.author.dm_channel is not None:
                                try:
                                    cancelPendingInvitesOverXDays(int(messageArray[1]))
                                    await message.author.dm_channel.send('Pending invites older than **' + str(messageArray[1]) + '** have been cleared')
                                except Exception as e:
                                    await message.author.dm_channel.send('exception occurred ' + str(e))
                        else:
                            await message.author.dm_channel.send('missing number of days param, or too many params')
                    elif message.content == (commandPrefix + 'listallpendinginvites'):
                        with DB_CONNECTION:
                            values = ("listallpendinginvites", "fromAdminDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        if message.author.dm_channel is not None:
                            try:
                                pendingInviteList = listAllPendingInvites()
                                for invite in pendingInviteList:
                                    await message.author.dm_channel.send('**Is nan?:** ' + str(invite) + '\n**inviteSent:** ' + str(invite.createdAt) + '\n**email:** ' + invite.email + '\n**isFriend:** ' + str(invite.friend) + '\n**serverShare:** ' + str(invite.servers[0]) + '\n**username:** ' + invite.username + '\n**friendlyName:** ' + invite.friendlyName + '\n--------')
                            except Exception as e:
                                await message.author.dm_channel.send('exception occurred ' + str(e))
                    elif message.content == (commandPrefix + 'help'):
                        with DB_CONNECTION:
                            values = ("help", "fromAdminDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        if message.author.dm_channel is not None:
                            await message.author.dm_channel.send('Hello! I am the Plex Manager Bot for this discord. I recognize you as the admin of this server. For a list of my commands try **' + commandPrefix + 'listcommands**. Note that the available commands are context dependent, so whether you are messaging me directly, or in one of the public channels, you can always **' + commandPrefix + 'listcommands** to see what I can do for you.')
                    elif message.content.startswith(commandPrefix + 'dbinfodiscordid'):
                        with DB_CONNECTION:
                            values = ("dbinfodiscordid", "fromAdminDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        if len(messageArray) == 2:
                            dbInfo = getDBInfoForDiscordID(DB_CONNECTION, str(messageArray[1]))
                            if message.author.dm_channel is not None:
                                if dbInfo != []:
                                    await message.author.dm_channel.send('**discordID:**  ' + str(dbInfo[1]) + '\n**discordUsername:**  ' + str(dbInfo[2]) + '\n**discordServerNickname:**  ' + str(dbInfo[3]) + '\n**plexUsername:**  ' + str(dbInfo[4]) + '\n**plexEmailAddress:**  ' + str(dbInfo[5]) + '\n**serverName:**  ' + str(dbInfo[6]) + '\n**dateRemoved:**  ' + str(dbInfo[7]) + '\n**dateInvited:**  ' + str(dbInfo[8]) + '\n**dateQueued:**  ' + str(dbInfo[9]) + '\n**status:**  ' + str(dbInfo[10]) + '\n**plexUserID:**  ' + str(dbInfo[11]))
                                else:
                                    await message.author.dm_channel.send('Did not find anything for that discord id')
                    elif message.content.startswith(commandPrefix + 'updateinactivitydays'):
                        with DB_CONNECTION:
                            values = ("updateinactivitydays", "fromAdminDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        if len(messageArray) == 3:
                            with DB_CONNECTION:
                                updateInactivityForServerName(DB_CONNECTION, str(messageArray[1]), str(messageArray[2]))
                                serverConfig = getPlexServerConfigInfoForName(DB_CONNECTION, str(messageArray[1]))
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('Inactivity updated to ' + str(serverConfig[8]) + ' days for server: ' + str(serverConfig[1]))
                        else:
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('misuse of command, should look like **' + commandPrefix + 'updateinactivitydays serverName days**')
                    elif message.content.startswith(commandPrefix + 'updateinviteacceptancelimit'):
                        with DB_CONNECTION:
                            values = ("updateinviteacceptancelimit", "fromAdminDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        if len(messageArray) == 3:
                            with DB_CONNECTION:
                                updateInviteAcceptanceLimitForServerName(DB_CONNECTION, str(messageArray[1]), str(messageArray[2]))
                                serverConfig = getPlexServerConfigInfoForName(DB_CONNECTION, str(messageArray[1]))
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('Invite acceptance limit updated to ' + str(serverConfig[9]) + ' days for server: ' + str(serverConfig[1]))
                        else:
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('misuse of command, should look like **' + commandPrefix + 'updateinviteacceptancelimit serverName days**')
                    elif message.content.startswith(commandPrefix + 'updatetautulliurl'):
                        with DB_CONNECTION:
                            values = ("updatetautulliurl", "fromAdminDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        if len(messageArray) == 3:
                            with DB_CONNECTION:
                                updateTautulliURLForServerName(DB_CONNECTION, str(messageArray[1]), str(messageArray[2]))
                                serverConfig = getPlexServerConfigInfoForName(DB_CONNECTION, str(messageArray[1]))
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('Tautulli URL updated to ' + str(serverConfig[6]) + ' for server: ' + str(serverConfig[1]))
                        else:
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('misuse of command, should look like **' + commandPrefix + 'updatetautulliurl serverName url**')
                    elif message.content.startswith(commandPrefix + 'updatetautulliapikey'):
                        with DB_CONNECTION:
                            values = ("updatetautulliapikey", "fromAdminDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        if len(messageArray) == 3:
                            with DB_CONNECTION:
                                updateTautulliAPIKeyForServerName(DB_CONNECTION, str(messageArray[1]), str(messageArray[2]))
                                serverConfig = getPlexServerConfigInfoForName(DB_CONNECTION, str(messageArray[1]))
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('Tautulli API Key updated to ' + str(serverConfig[7]) + ' for server: ' + str(serverConfig[1]))
                        else:
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('misuse of command, should look like **' + commandPrefix + 'updatetautulliapikey serverName apikey**')
                    elif message.content.startswith(commandPrefix + 'updateserverurl'):
                        with DB_CONNECTION:
                            values = ("updateserverurl", "fromAdminDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        if len(messageArray) == 3:
                            with DB_CONNECTION:
                                updateServerURLForServerName(DB_CONNECTION, str(messageArray[1]), str(messageArray[2]))
                                serverConfig = getPlexServerConfigInfoForName(DB_CONNECTION, str(messageArray[1]))
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('URL updated to ' + str(serverConfig[2]) + ' for server: ' + str(serverConfig[1]))
                        else:
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('misuse of command, should look like **' + commandPrefix + 'updateserverurl serverName serverurl**')
                    elif message.content.startswith(commandPrefix + 'updateservertoken'):
                        with DB_CONNECTION:
                            values = ("updateservertoken", "fromAdminDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        if len(messageArray) == 3:
                            with DB_CONNECTION:
                                updateServerTokenForServerName(DB_CONNECTION, str(messageArray[1]), str(messageArray[2]))
                                serverConfig = getPlexServerConfigInfoForName(DB_CONNECTION, str(messageArray[1]))
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('Token updated to ' + str(serverConfig[3]) + ' for server: ' + str(serverConfig[1]))
                        else:
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('misuse of command, should look like **' + commandPrefix + 'updateservertoken serverName servertoken**')
                    elif message.content.startswith(commandPrefix + 'updatechecksinactivity'):
                        with DB_CONNECTION:
                            values = ("updatechecksinactivity", "fromAdminDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        if len(messageArray) == 3:
                            with DB_CONNECTION:
                                updateChecksInactivityForServerName(DB_CONNECTION, str(messageArray[1]), str(messageArray[2]))
                                serverConfig = getPlexServerConfigInfoForName(DB_CONNECTION, str(messageArray[1]))
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('Activity check updated to ' + str(serverConfig[4]) + ' for server: ' + str(serverConfig[1]))
                        else:
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('misuse of command, should look like **' + commandPrefix + 'updatechecksinactivity serverName YES/NO**')
                    elif message.content.startswith(commandPrefix + 'updateemailforuser'):
                        with DB_CONNECTION:
                            values = ("updateemailforuser", "fromAdminDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        if len(messageArray) == 3:
                            with DB_CONNECTION:
                                updateEmailForDiscordID(DB_CONNECTION, str(messageArray[1]), str(messageArray[2]))
                                userInfo = getDBInfoForDiscordID(DB_CONNECTION, str(messageArray[1]))
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('Email updated to ' + str(userInfo[5]) + ' for user: ' + str(userInfo[1]))
                        else:
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('misuse of command, should look like **' + commandPrefix + 'updateemailforuser discordid email**')
                    elif message.content == (commandPrefix + 'openspots'):
                        with DB_CONNECTION:
                            values = ("openspots", "fromAdminDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                            openspotsCount = getTotalOpenSpots(DB_CONNECTION)
                        if openspotsCount < 9000:
                            await message.reply('There are **' + str(openspotsCount) + '** spots open.', mention_author=False)
                        else:
                            await message.reply('Cannot count open spots right now', mention_author=False)
                    elif message.content.startswith(commandPrefix + 'watchtimediscordid'):
                        with DB_CONNECTION:
                            values = ("watchtimediscordid", "fromAdminDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        if len(messageArray) == 2:
                            with DB_CONNECTION:
                                watchTime = getWatchTimeForDiscordID(DB_CONNECTION, str(messageArray[1]))
                            prettyTime = time_format(watchTime)
                            if message.author.dm_channel is not None:
                                if watchTime != 0:
                                    await message.author.dm_channel.send('Watch Time for that discord ID is : ' + prettyTime)
                                else:
                                    await message.author.dm_channel.send('No watch time for that discord ID')
                        else:
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('misuse of command, should look like **'
                                                                     + commandPrefix
                                                                     + 'watchtimediscordid discordid**')
                    elif message.content == (commandPrefix + 'currentstreams'):
                        with DB_CONNECTION:
                            values = ("currentstreams", "fromAdminDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                            streamList = getCurrentStreams(DB_CONNECTION)
                        if message.author.dm_channel is not None:
                            for stream in streamList:
                                await message.author.dm_channel.send('**Server:** ' + str(stream[0]) + '\n**Stream Count:** ' + str(stream[1]) + '\n--**Direct Play:** ' + str(stream[2]) + '\n--**Direct Stream:** ' + str(stream[3]) + '\n--**Transcode:** ' + str(stream[4]) + '\n**Total Bandwidth:** ' + str(stream[5] / 1000) + 'mbps')
                    elif message.content == (commandPrefix + 'listcommands'):
                        with DB_CONNECTION:
                            values = ("listcommands", "privateNoNickname", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        if message.author.dm_channel is not None:
                            await message.author.dm_channel.send('Command prefix is: **' + commandPrefix + '**\n' + commandPrefix + 'updatebotchannelid **channelid**\n--------\n' + commandPrefix + 'updatecommandprefix **newprefix**\n--------\n' + commandPrefix + 'initplexserver **serverName serverURL serverToken checksInactivity invitedDiscordRole tautulliURL tautulliAPIKey inactivityLimit inviteacceptanceLimit**\n--------\n' + commandPrefix + 'listplexservers\n--------\n' + commandPrefix + 'listplexserverswithoutcount\n--------\n' + commandPrefix + 'clearpendinginvites **days**\n--------\n' + commandPrefix + 'listallpendinginvites\n--------\n' + commandPrefix + 'help\n--------\n' + commandPrefix + 'dbinfodiscordid **discordid**\n--------\n' + commandPrefix + 'updateinactivitydays **serverName days**\n--------\n' + commandPrefix + 'updateinviteacceptancelimit **serverName days**\n--------\n' + commandPrefix + 'updatetautulliurl **serverName tautulliurl**\n--------\n' + commandPrefix + 'updatetautulliapikey **serverName apikey**\n--------\n' + commandPrefix + 'updateserverurl **serverName serverURL**\n--------\n' + commandPrefix + 'updateservertoken **serverName serverToken**\n--------\n' + commandPrefix + 'updatechecksinactivity **serverName YES/NO**\n--------\n' + commandPrefix + 'updateemailforuser **discordid email**\n--------\n' + commandPrefix + 'openspots\n--------\n' + commandPrefix + 'watchtimediscordid **discordid**\n--------\n' + commandPrefix + 'currentstreams\n--------\n' + commandPrefix + 'listcommands\n--------')
                    elif message.content.startswith(commandPrefix):
                        if message.author.dm_channel is not None:
                            await message.author.dm_channel.send('I did not understand that. Try ' + commandPrefix + 'listcommands')
                # endregion
                else:
                    # region direct messages USER actions
                    if message.content == commandPrefix + 'ping':
                        with DB_CONNECTION:
                            values = ("private ping", "fromUserDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        if message.author.dm_channel is not None:
                            await message.author.dm_channel.send('private pong')
                    elif message.content.startswith(commandPrefix + 'inviteme'):
                        if len(messageArray) == 2 and "@" in str(messageArray[1]):
                            with DB_CONNECTION:
                                values = ("inviteme", "fromUserDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                                recordCommandHistory(DB_CONNECTION, values)
                                existsAlready = checkDiscordIDExists(DB_CONNECTION, str(message.author.id))
                                if existsAlready:
                                    statusForMember = getStatusForDiscordID(DB_CONNECTION, str(message.author.id))
                                    emailForMember = getEmailForDiscordID(DB_CONNECTION, str(message.author.id))
                            if not existsAlready:
                                if getTotalOpenSpots(DB_CONNECTION) > 0 and getTotalOpenSpots(DB_CONNECTION) < 9000:
                                    serverName = getFirstPlexServerNameWithOpenSpots(DB_CONNECTION)
                                    userValues = (str(message.author.id), str(message.author.name), "fromDMNoNickname", serverName)
                                    successBool = inviteEmailToPlex(DB_CONNECTION, str(messageArray[1]).lower(), userValues)
                                    if message.author.dm_channel is not None:
                                        if successBool:
                                            await message.author.dm_channel.send('You have been invited to ' + serverName + '. If you do not see an invite, make sure to check spam')
                                            roleNameToAdd = getInvitedDiscordRoleNameForServerName(DB_CONNECTION, serverName)
                                            await addRoleForDiscordID(DB_CONNECTION, roleNameToAdd, str(message.author.id), GUILD_ID)
                                        else:
                                            await message.author.dm_channel.send('Something went wrong with your invite. This is what you sent me (without the double dash): --' + str(message.content) + '--. This is what it should look like ' + commandPrefix + 'inviteme email@address.com')
                                else:
                                    with DB_CONNECTION:
                                        qValues = (str(message.author.id), str(message.author.name), str(messageArray[1]).lower(), str(date1), '4')
                                        insertQueuedUser(DB_CONNECTION, qValues)
                                    await message.author.dm_channel.send('There are currently no open slots, but you have been added to the queue. To see your place in the queue, try ' + commandPrefix + 'status')
                            else:
                                with DB_CONNECTION:
                                    botConfigInfo = getBotConfigurationInfo(DB_CONNECTION)
                                if statusForMember == '0' and getTotalOpenSpots(DB_CONNECTION) > 0 and getTotalOpenSpots(DB_CONNECTION) < 9000:
                                    serverName = getFirstPlexServerNameWithOpenSpots(DB_CONNECTION)
                                    userValues = (str(message.author.id), str(message.author.name), "fromDMNoNickname", serverName)
                                    inviteEmailToPlex(DB_CONNECTION, str(messageArray[1]).lower(), userValues)
                                    roleNameToRemove = botConfigInfo[4]
                                    await removeRoleForDiscordID(DB_CONNECTION, roleNameToRemove, str(message.author.id), GUILD_ID)
                                    if message.author.dm_channel is not None:
                                        await message.author.dm_channel.send('You were removed for inactivity, however there are open spots now, so you have been re-invited. \n You have been invited to ' + serverName + '\n. If you do not see an invite make sure to check spam/junk')
                                    roleNameToAdd = getInvitedDiscordRoleNameForServerName(DB_CONNECTION, serverName)
                                    await addRoleForDiscordID(DB_CONNECTION, roleNameToAdd, str(message.author.id), GUILD_ID)
                                elif statusForMember == '0' and (getTotalOpenSpots(DB_CONNECTION) == 0 or getTotalOpenSpots(DB_CONNECTION) == 9000):
                                    if message.author.dm_channel is not None:
                                        await message.author.dm_channel.send('You were removed for inactivity and there are currently no spots open. \nYou have been added to the queue for an invite')
                                    roleNameToRemove = botConfigInfo[4]
                                    await removeRoleForDiscordID(DB_CONNECTION, roleNameToRemove, str(message.author.id), GUILD_ID)
                                    roleNameToAdd = botConfigInfo[3]
                                    await addRoleForDiscordID(DB_CONNECTION, roleNameToAdd, str(message.author.id), GUILD_ID)
                                elif statusForMember == '1':
                                    if message.author.dm_channel is not None:
                                        await message.author.dm_channel.send('You were manually removed by an admin. \nPlease message the admin with any questions')
                                elif statusForMember == '2' and emailForMember == str(messageArray[1]):
                                    if message.author.dm_channel is not None:
                                        await message.author.dm_channel.send('An invite has already been sent for that email address, but it has not been accepted yet. \nPlease accept the invite and do not forget to check your spam if you cannot find it.')
                                elif statusForMember == '2' and emailForMember != str(messageArray[1]):
                                    if message.author.dm_channel is not None:
                                        await message.author.dm_channel.send('An invite has already been sent for you, but for a different email address. \nIf you made a typo when you first used the ' + commandPrefix + 'inviteme command you can leave the discord server to be removed from my memory. \nThen you can DM me the ' + commandPrefix + 'inviteme command again with the correct info. \nThis might place you at the bottom of the invite queue.')
                                elif statusForMember == '3' and emailForMember != str(messageArray[1]):
                                    if message.author.dm_channel is not None:
                                        await message.author.dm_channel.send('You have already accepted an invite for a different email address. \nIf you are trying to get an invite for someone else, please have them join the discord server and DM me the ' + commandPrefix + 'inviteme command')
                                elif statusForMember == '3' and emailForMember == str(messageArray[1]):
                                    if message.author.dm_channel is not None:
                                        await message.author.dm_channel.send('You have already accepted an invite for that email address. \nIf you are having any problems please message the admin.')
                                elif statusForMember == '4' and emailForMember == str(messageArray[1]):
                                    if message.author.dm_channel is not None:
                                        await message.author.dm_channel.send('You have already been queued for an invite to that email address. \nIf you want to see your place in the queue, try the ' + commandPrefix + 'queuestatus command')
                                elif statusForMember == '4' and emailForMember != str(messageArray[1]):
                                    if message.author.dm_channel is not None:
                                        await message.author.dm_channel.send('You have already been added to the queue, but for a different email address. \nIf this is because of a typo when you first used the command, leave the discord and rejoin. \nThis will clear you from my memory and you can DM me the ' + commandPrefix + 'inviteme command with the correct address. \nThis will reset your position in the queue. \nIf you are trying to get an invite for someone else, have them join the discord server and DM me the inviteme command.')
                                else:
                                    if message.author.dm_channel is not None:
                                        await message.author.dm_channel.send('Something went wrong, and I could not get your status from memory.')
                        else:
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('Incorrect command usage. It should look like this: **' + commandPrefix + 'inviteme email@address.com**')
                    elif message.content == (commandPrefix + 'status'):
                        with DB_CONNECTION:
                            memberStatus = getStatusForDiscordID(DB_CONNECTION, str(message.author.id))
                            values = ("status", "fromUserDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        if memberStatus != "":
                            statusForMember = getStatusForDiscordID(DB_CONNECTION, str(message.author.id))
                            if statusForMember == '0':
                                await message.reply('You have been removed for inactivity')
                            if statusForMember == '1':
                                await message.reply('You have been manually removed by an admin')
                            if statusForMember == '2':
                                await message.reply('You have been invited but you have not accepted yet')
                            if statusForMember == '3':
                                await message.reply('You have already accepted an invite.')
                            if statusForMember == '4':
                                await message.reply('You have been queued for an invite.')
                        else:
                            await message.reply('You do not have a status.')
                    elif message.content == (commandPrefix + 'help'):
                        with DB_CONNECTION:
                            values = ("help", "fromUserDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        if message.author.dm_channel is not None:
                            await message.author.dm_channel.send('Hello! I am the Plex Manager Bot for this discord. For a list of my commands try **' + commandPrefix + 'listcommands**. PLEASE NOTE that the commands available in a DM are different than the commands available in a public channel.')
                    elif message.content == (commandPrefix + 'queuestatus'):
                        with DB_CONNECTION:
                            values = ("queuestatus", "fromUserDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                            statusForMember = getStatusForDiscordID(DB_CONNECTION, str(message.author.id))
                        if statusForMember == '4':
                            with DB_CONNECTION:
                                dateQueued = getDateQueuedForDiscordID(DB_CONNECTION, str(message.author.id))
                                countAhead = getCountQueuedAheadOfDate(DB_CONNECTION, dateQueued)
                            if countAhead == 0:
                                if message.author.dm_channel is not None:
                                    await message.author.dm_channel.send('There is no one queued ahead of you, you should recieve the next available invite.')
                            else:
                                if message.author.dm_channel is not None:
                                    await message.author.dm_channel.send('There are **' + str(countAhead) + '**  users queued ahead of you.')
                        else:
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('You are not currently queued for an invite. Try the ' + commandPrefix + 'inviteme command')
                    elif message.content == (commandPrefix + 'openspots'):
                        with DB_CONNECTION:
                            values = ("openspots", "fromUserDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                            openspotsCount = getTotalOpenSpots(DB_CONNECTION)
                        if message.author.dm_channel is not None:
                            if openspotsCount < 9000:
                                await message.author.dm_channel.send('There are **' + str(openspotsCount) + '**  spots open.')
                            else:
                                await message.author.dm_channel.send('cannot count open spots right now.')
                    elif message.content == (commandPrefix + 'yourmemoryofme'):
                        with DB_CONNECTION:
                            values = ("yourmemoryofme", "fromUserDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                            userInfo = getDBInfoForDiscordID(DB_CONNECTION, str(message.author.id))
                        if message.author.dm_channel is not None:
                            if userInfo:
                                await message.author.dm_channel.send('**discordID:**  ' + str(userInfo[1]) + '\n**discordUsername:**  ' + str(userInfo[2]) + '\n**discordServerNickname:**  ' + str(userInfo[3]) + '\n**plexUsername:**  ' + str(userInfo[4]) + '\n**plexEmailAddress:**  ' + str(userInfo[5]) + '\n**serverName:**  ' + str(userInfo[6]) + '\n**dateRemoved:**  ' + str(userInfo[7]) + '\n**dateInvited:**  ' + str(userInfo[8]) + '\n**dateQueued:**  ' + str(userInfo[9]) + '\n**status:**  ' + str(userInfo[10]) + '\n**plexUserID:**  ' + str(userInfo[11]))
                            else:
                                await message.author.dm_channel.send('I do not remember you.')
                    elif message.content == (commandPrefix + 'mywatchtime'):
                        with DB_CONNECTION:
                            values = ("mywatchtime", "fromUserDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                            userInfo = getDBInfoForDiscordID(DB_CONNECTION, str(message.author.id))
                        if message.author.dm_channel is not None:
                            if userInfo:
                                with DB_CONNECTION:
                                    watchTime = getWatchTimeForDiscordID(DB_CONNECTION, message.author.id)
                                    plexInfo = getPlexServerConfigInfoForName(DB_CONNECTION, userInfo[6])
                                if watchTime != 0:
                                    prettyTime = time_format(watchTime)
                                    if message.author.dm_channel is not None:
                                        await message.author.dm_channel.send('Your watch time is: ' + prettyTime + ' within the last ' + plexInfo[8] + ' days')
                                else:
                                    await message.author.dm_channel.send('You do not have any watch time recorded')
                            else:
                                await message.author.dm_channel.send('You do not have any watch time recorded')
                    elif message.content == (commandPrefix + 'listcommands'):
                        with DB_CONNECTION:
                            values = ("listcommands", "fromUserDM", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        if message.author.dm_channel is not None:
                            await message.author.dm_channel.send('Command prefix is: **' + commandPrefix + '**\n\n' + commandPrefix + 'inviteme **email@address.com**\n---------------------------------------------------\n' + commandPrefix + 'status\n---------------------------------------------------\n' + commandPrefix + 'help\n---------------------------------------------------\n' + commandPrefix + 'openspots\n---------------------------------------------------\n' + commandPrefix + 'queuestatus\n---------------------------------------------------\n' + commandPrefix + 'yourmemoryofme\n---------------------------------------------------\n' + commandPrefix + 'mywatchtime\n---------------------------------------------------\n' + commandPrefix + 'listcommands\n---------------------------------------------------')
                    elif message.content.startswith(commandPrefix):
                        if message.author.dm_channel is not None:
                            await message.author.dm_channel.send('I did not understand that. Try ' + commandPrefix + 'listcommands')
                    # endregion
            else:
                # if messages come from public bot channel
                if str(message.channel.id) == str(botChannelID):
                    # region BotChannel Only Messages
                    if message.content == commandPrefix + 'ping':
                        await message.channel.send('bot channel pong!')
                        with DB_CONNECTION:
                            values = ("bot channel ping", "fromBotChannel", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                    elif message.content == (commandPrefix + 'openspots'):
                        with DB_CONNECTION:
                            values = ("openspots", "fromBotChannel", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                            openspotsCount = getTotalOpenSpots(DB_CONNECTION)
                        if openspotsCount < 9000:
                            await message.reply('There are **' + str(openspotsCount) + '** spots open.')
                        else:
                            await message.reply('unable to count open spots right now.')
                    elif message.content.startswith(commandPrefix + 'inviteme') and "@" in str(messageArray[1]):
                        if message.author.dm_channel is None:
                            try:
                                await message.author.create_dm()
                            except Exception as e:
                                print("From bot channel inviteme command logic. some issue with creating DM" + str(e))
                        if message.author.dm_channel is not None:
                            await message.author.dm_channel.send('Please do not use the inviteme command in any public channels. DM me (or respond to this) instead.')
                        try:
                            await message.delete()
                        except Exception as e:
                            print('exception when deleting message from bot channel inviteme command logic' + str(e))
                        with DB_CONNECTION:
                            recordBotActionHistory(DB_CONNECTION, 'found public inviteme command with email address. Deleting for privacy in discord server', 'AUTOMATIC')
                    # elif message.content.contains()
                    elif message.content == (commandPrefix + 'status'):
                        with DB_CONNECTION:
                            memberStatus = getStatusForDiscordID(DB_CONNECTION, str(message.author.id))
                            values = ("status", "fromBotChannel", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        if memberStatus != "":
                            statusForMember = getStatusForDiscordID(DB_CONNECTION, str(message.author.id))
                            if statusForMember == '0':
                                await message.reply('You have been removed for inactivity')
                            if statusForMember == '1':
                                await message.reply('You have been manually removed by an admin')
                            if statusForMember == '2':
                                await message.reply('You have been invited but you have not accepted yet')
                            if statusForMember == '3':
                                await message.reply('You have already accepted an invite.')
                            if statusForMember == '4':
                                await message.reply('You have been queued for an invite.')
                        else:
                            await message.reply('You do not have a status.')
                    elif message.content == (commandPrefix + 'help'):
                        with DB_CONNECTION:
                            values = ("help", "fromBotChannel", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        await message.reply('Hello! I am the Plex Manager Bot for this discord. For a list of my commands try **' + commandPrefix + 'listcommands**. Note that commands available in a DM are different than the ones in the public channel.')
                    elif message.content.startswith(commandPrefix + 'mywatchtime'):
                        with DB_CONNECTION:
                            values = ("mywatchtime", "fromBotChannel", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                            watchTime = getWatchTimeForDiscordID(DB_CONNECTION, str(message.author.id))
                            userInfo = getDBInfoForDiscordID(DB_CONNECTION, str(message.author.id))
                        prettyTime = time_format(watchTime)
                        if userInfo:
                            with DB_CONNECTION:
                                plexInfo = getPlexServerConfigInfoForName(DB_CONNECTION, userInfo[6])
                            if watchTime != 0:
                                await message.reply('Your watch time is : ' + prettyTime + ' over the last ' + plexInfo[8] + ' days')
                            else:
                                await message.reply('No watch time recorded for you')
                        else:
                            await message.reply('No watch time recorded for you')
                    elif message.content == (commandPrefix + 'listcommands'):
                        with DB_CONNECTION:
                            values = ("listcommands", "fromBotChannel", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        await message.reply('Command prefix is **' + commandPrefix + '**\n\n' + commandPrefix + 'ping \n--------\n' + commandPrefix + 'openspots \n--------\n' + commandPrefix + 'status \n--------\n' + commandPrefix + 'help \n--------\n' + commandPrefix + 'mywatchtime \n--------\n' + commandPrefix + 'listcommands\n--------\nDM me with ' + commandPrefix + 'listcommands for additional commands\n--------')
                    elif message.content.startswith(commandPrefix):
                        await message.reply('I did not understand that. Try ' + commandPrefix + 'listcommands')
                    # endregion
                else:
                    # region public anywhere actions
                    if message.content == commandPrefix + 'ping':
                        await message.reply('public pong!')
                        with DB_CONNECTION:
                            values = ("public ping", "fromPublicChannel", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                    elif message.content == (commandPrefix + 'openspots'):
                        with DB_CONNECTION:
                            values = ("openspots", "fromPublicChannel", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                            openspotsCount = getTotalOpenSpots(DB_CONNECTION)
                        if openspotsCount < 9000:
                            await message.reply('There are **' + str(openspotsCount) + '** spots open.')
                        else:
                            await message.reply('unable to count openspots right now.')
                    elif message.content.startswith(commandPrefix + 'inviteme') and "@" in str(messageArray[1]):
                        if message.author.dm_channel is None:
                            try:
                                await message.author.create_dm()
                            except Exception as e:
                                print("From public inviteme command logic. some issue with creating DM" + str(e))
                        if message.author.dm_channel is not None:
                            await message.author.dm_channel.send('Please do not use the inviteme command in any public channels. DM me (or respond to this) instead.')
                        try:
                            await message.delete()
                        except Exception as e:
                            print('exception when deleting message from public inviteme command logic' + str(e))
                        with DB_CONNECTION:
                            recordBotActionHistory(DB_CONNECTION, 'found public inviteme command with email address. Deleting for privacy in discord server', 'AUTOMATIC')
                    elif message.content == (commandPrefix + 'status'):
                        with DB_CONNECTION:
                            memberStatus = getStatusForDiscordID(DB_CONNECTION, str(message.author.id))
                            values = ("status", "fromPublicChannel", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        if memberStatus != "":
                            statusForMember = getStatusForDiscordID(DB_CONNECTION, str(message.author.id))
                            if statusForMember == '0':
                                await message.reply('You have been removed for inactivity')
                            if statusForMember == '1':
                                await message.reply('You have been manually removed by an admin')
                            if statusForMember == '2':
                                await message.reply('You have been invited but you have not accepted yet')
                            if statusForMember == '3':
                                await message.reply('You have already accepted an invite.')
                            if statusForMember == '4':
                                await message.reply('You have been queued for an invite.')
                        else:
                            await message.reply('You do not have a status.')
                    elif message.content == (commandPrefix + 'help'):
                        with DB_CONNECTION:
                            values = ("help", "fromPublicChannel", str(message.author.name),
                                      str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        await message.reply('Hello! I am the Plex Manager Bot for this discord. For a list of my commands try **' + commandPrefix + 'listcommands**. PLEASE NOTE that the commands available in a DM ar different from the commands available in a public channel.')
                    elif message.content == (commandPrefix + 'queuestatus'):
                        with DB_CONNECTION:
                            values = ("queuestatus", "fromPublicChannel", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                            currentStatus = getStatusForDiscordID(DB_CONNECTION, str(message.author.id))
                            queueStatus = getQueueStatusForDiscordID(DB_CONNECTION, str(message.author.id))
                        if currentStatus == '4':
                            await message.reply('There are **' + str(queueStatus) + '** queued ahead of you.')
                        else:
                            await message.reply('You are not currently queued.')
                    elif message.content.startswith(commandPrefix + 'mywatchtime'):
                        with DB_CONNECTION:
                            values = ("mywatchtime", "fromPublicChannel", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                            watchTime = getWatchTimeForDiscordID(DB_CONNECTION, str(message.author.id))
                            userInfo = getDBInfoForDiscordID(DB_CONNECTION, str(message.author.id))
                        prettyTime = time_format(watchTime)
                        if userInfo:
                            with DB_CONNECTION:
                                plexInfo = getPlexServerConfigInfoForName(DB_CONNECTION, userInfo[6])
                            if watchTime != 0:
                                await message.reply('Your watch time is : ' + prettyTime + ' over the last ' + plexInfo[8] + ' days')
                            else:
                                await message.reply('No watch time recorded for you')
                        else:
                            await message.reply('No watch time recorded for you')
                    elif message.content == (commandPrefix + 'listcommands'):
                        with DB_CONNECTION:
                            values = ("listcommands", "fromPublicChannel", str(message.author.name), str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        await message.channel.send('Command prefix is: **' + commandPrefix + '**\n\n' + commandPrefix + 'ping\n--------\n' + commandPrefix + 'openspots\n--------\n' + commandPrefix + 'status\n--------\n' + commandPrefix + 'help\n--------\n' + commandPrefix + 'queuestatus\n--------\n' + commandPrefix + 'mywatchtime\n--------\n' + commandPrefix + 'listcommands\n--------\nDM me with ' + commandPrefix + 'listcommands for additional commands\n--------')
                    elif message.content.startswith(commandPrefix):
                        await message.reply('I did not understand that. Try ' + commandPrefix + 'listcommands')
                    # endregion
    # endregion

# onmemberremove event
if not botConfigured:
    # region bot NOT configured on_member_remove event
    @client.event
    async def on_member_remove(member):
        print('bot not configured so doing nothing about ' + str(member.id) + ' leaving')
    # endregion
else:
    # region bot configured on_member_remove event
    @client.event
    async def on_member_remove(member):
        with DB_CONNECTION:
            statusForMember = getStatusForDiscordID(DB_CONNECTION, str(member.id))
            recordBotActionHistory(DB_CONNECTION, 'this is the status i found for the person that just left: ' + str(statusForMember), 'AUTOMATIC')
        if statusForMember == '0':
            # removed for inactivity, delete them
            with DB_CONNECTION:
                deleteFromDBForDiscordID(DB_CONNECTION, str(member.id))
                recordBotActionHistory(DB_CONNECTION, 'from on_member_remove status 0: deleted user from database discordID: ' + str(member.id), 'AUTOMATIC')
        elif statusForMember == '1':
            # removed by admin, delete them
            with DB_CONNECTION:
                deleteFromDBForDiscordID(DB_CONNECTION, str(member.id))
                recordBotActionHistory(DB_CONNECTION, 'from on_member_remove status 1: deleted user from database discordID: ' + str(member.id), 'AUTOMATIC')
        elif statusForMember == '2':
            # invited but not accepted
            with DB_CONNECTION:
                cancelPendingInviteForDiscordID(DB_CONNECTION, str(member.id))
                deleteFromDBForDiscordID(DB_CONNECTION, str(member.id))
                recordBotActionHistory(DB_CONNECTION, 'from on_member_remove status 2: Canceled Pending invite and deleted from database for discordID: ' + str(member.id), 'AUTOMATIC')
        elif statusForMember == '3':
            # invited and accepted
            with DB_CONNECTION:
                deleteFromPlexTautulliAndDB(DB_CONNECTION, str(member.id))
                recordBotActionHistory(DB_CONNECTION, 'from on_member_remove status 3: Removed Friend from Plex, Tautulli, and database by discordID: ' + str(member.id), 'AUTOMATIC')
        elif statusForMember == '4':
            # queued for an invite
            with DB_CONNECTION:
                deleteFromDBForDiscordID(DB_CONNECTION, str(member.id))
                recordBotActionHistory(DB_CONNECTION, 'from on_member_remove status 4: Removed queued user from database by discordID: ' + str(member.id), 'AUTOMATIC')
        else:
            with DB_CONNECTION:
                recordBotActionHistory(DB_CONNECTION, 'member left that had no status. Nothing to do except record it ' + str(member.id), 'AUTOMATIC')
            print('member left. I dont care.')
    # endregion
# endregion

client.run(CLIENT_TOKEN)
