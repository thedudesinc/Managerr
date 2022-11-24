import datetime
import os
import sqlite3
from sqlite3 import Error
import discord
from discord.ext.tasks import loop
from requests import Session
from plexapi.server import PlexServer

# ----setting static variable values.
SESSION = Session()
SESSION.verify = False
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

# Script values
database = r"BotDB.db"
# INVITE_SCRIPT_PATH = './InviteUser.py'
DB_CONNECTION = None
SERVER = None
ACCOUNT = None
CONFIGURED = False
# End Script values

# Discord Values
GUILD_ID = 1004464978696343593
# End Discord Values

# ********static actions********

# connects to the database


# region defined methods
def create_connection(db):
    conn = None
    try:
        conn = sqlite3.connect(db)
    except Error as e:
        print(e)
    return conn


def getConfiguredValue(conn):
    configuredValue = False
    cur = conn.cursor()
    # print("I am trying to get the value for the configuration colum in the BotConfiguration table.")
    cur.execute('select configured from BotConfiguration')
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        # print(str(rowTuple[0]))
        returnedValue = str(rowTuple[0])
        if returnedValue == 'False':
            configuredValue = False
        if returnedValue == 'True':
            configuredValue = True
    if len(rows) == 0:
        configuredValue = False
    return configuredValue


def updateConfiguredValue(conn, value):
    cur = conn.cursor()
    cur.execute('UPDATE BotConfiguration et configured =(?)', str(value))
    return


def createDBTables(db):
    sqlBAH = ''' CREATE TABLE IF NOT EXISTS "BotActionHistory" 
    ("action" TEXT, "dateTime" TEXT, "automaticOrManual" TEXT); '''
    sqlBCommand = ''' CREATE TABLE IF NOT EXISTS "BotCommands" 
    ( "commandName" TEXT UNIQUE, "commandReturnMessage" TEXT, "isAdminCommand" INTEGER); '''
    sqlBConfig = ''' CREATE TABLE IF NOT EXISTS "BotConfiguration" 
    ("administratorDiscordID" TEXT, "botAdminDiscordRole" TEXT, "botChannelID" TEXT, "queuedRole" TEXT, 
    "removedRole" TEXT, "commandPrefix" TEXT NOT NULL DEFAULT '!!!', "configured" TEXT DEFAULT 'False'); '''
    sqlCH = ''' CREATE TABLE IF NOT EXISTS "CommandHistory" 
    ("commandName" TEXT NOT NULL, "discordServerNickname" TEXT NOT NULL, "discordUsername" TEXT NOT NULL, 
    "discordID" TEXT NOT NULL, "dateTime" TEXT NOT NULL, "valueSent" TEXT); '''
    sqlPSC = ''' CREATE TABLE IF NOT EXISTS "PlexServerConfiguration" 
    ("psc_PK" INTEGER NOT NULL UNIQUE, "serverName" TEXT NOT NULL UNIQUE, "serverURL" TEXT NOT NULL UNIQUE, 
    "serverToken" TEXT NOT NULL UNIQUE, "checksInactivity" TEXT, "invitedDiscordRole" TEXT, "tautulliURL" TEXT, 
    "tautulliAPIKey" TEXT, "inactivityLimit" TEXT, "inviteAcceptanceLimit" TEXT, PRIMARY KEY("psc_PK" AUTOINCREMENT)); 
    '''
    sqlU = ''' CREATE TABLE IF NOT EXISTS "Users" 
    ("u_PK" INTEGER NOT NULL UNIQUE, "discordID" TEXT NOT NULL UNIQUE, "discordUsername" TEXT NOT NULL, 
    "discordServerNickname"	TEXT, "plexUsername" TEXT DEFAULT 'NEEDSUPDATED', "plexEmailAddress" TEXT, 
    "serverName" TEXT, "dateRemoved" TEXT, "dateInvited" INTEGER, "dateQueued" TEXT, "status" INTEGER, 
    PRIMARY KEY("u_PK" AUTOINCREMENT) ); '''
    conn = create_connection(db)
    createTable(conn, sqlBAH)
    conn.close()
    conn = create_connection(db)
    createTable(conn,sqlBCommand)
    conn.close()
    conn = create_connection(db)
    createTable(conn, sqlBConfig)
    conn.close()
    conn = create_connection(db)
    createTable(conn, sqlCH)
    conn.close()
    conn = create_connection(db)
    createTable(conn, sqlPSC)
    conn.close()
    conn = create_connection(db)
    createTable(conn, sqlU)
    conn.close()
    return


def createTable(conn, sql):
    try:
        cur = conn.cursor()
        cur.execute(sql)
    except Error as e:
        print("from running cursor.execute() for the given SQL: " + str(sql) + " error: " + str(e))
    return


# gets configured true or false from Database.
try:
    conn = create_connection(database)
    CONFIGURED = getConfiguredValue(conn)
    conn.close()
except Error as e:
    print(e)

if not CONFIGURED:
    try:
        createDBTables(database)
    except Error as e:
        print("Error from calling createDBTables function: " + str(e))


# ********end static actions********


# ----defining db functions below
def configureBot(conn, dbValues):
    sql = ''' INSERT INTO BotConfiguration(administratorDiscordID,botAdminDiscordRole,botChannelID,queuedRole,
            removedRole,commandPrefix,configured) 
            VALUES(?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, dbValues)
    return


def getCommandPrefix(conn):
    cur = conn.cursor()
    cur.execute('select commandPrefix from BotConfiguration')
    commandPrefixReturn = str(cur.fetchall())
    return commandPrefixReturn


# initialize Plex Server info
def initializePlexServer(name, url, token, checks_inactivity, invited_discord_role, tautulli_url,
                         tautulli_api_key, inactivity_limit, invite_acceptance_limit):
    dateTime = datetime.datetime.now()
    if str(checks_inactivity) == "YES":
        valuesToSend = (str(name), str(url), str(token), str(checks_inactivity), str(invited_discord_role),
                        str(tautulli_url), str(tautulli_api_key), str(inactivity_limit), str(invite_acceptance_limit))
        conn = create_connection(database)
        initializePlexServerInDB(conn,valuesToSend)
        conn.close()
        botActionValues = ("initialized Plex Server: " + name, dateTime, "MANUAL")
        conn = create_connection(database)
        updateBotActionHistory(conn,botActionValues)
        conn.close()
    else:
        valuesToSend = (str(name), str(url), str(token), str(checks_inactivity))
        conn = create_connection(database)
        initializePlexServerInDB(conn,valuesToSend)
        conn.close()
        botActionValues = ("initialized Plex Server: " + name, dateTime, "MANUAL")
        conn = create_connection(database)
        updateBotActionHistory(conn,botActionValues)
        conn.close()
    return


def initializePlexServerInDB(conn, values):
    if str(values[3]) == "YES":
        sql = ''' INSERT INTO PlexServerConfiguration(serverName,serverURL,serverToken,checksInactivity,
        invitedDiscordRole,tautulliURL,tautulliAPIKey,inactivityLimit,inviteAcceptanceLimit) 
        VALUES(?,?,?,?,?,?,?,?,?) '''
    else:
        sql = ''' INSERT INTO PlexServerConfiguration(serverName,serverURL,serverToken,checksInactivity) 
        VALUES(?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, values)
    return


# -----from repeated actions script
def getBotPlexUsers(conn):
    rDict = {}
    cur = conn.cursor()
    cur.execute('select plexEmailAddress, status from Users')
    BotPlexUsers = cur.fetchall()
    for x in BotPlexUsers:
        # .update function to append the values to the dictionary
        rDict.update({str(x[0]).lower(): x[1]})
    return rDict


def updateStatusForDiscordID(conn, discordID, statusUpdate):
    date1 = datetime.datetime.now()
    cur = conn.cursor()
    if statusUpdate == 4:
        cur.execute('UPDATE Users set status =4, dateQueued =(?) WHERE discordID like(?)',
                    (str(date1), str(discordID)))
    elif statusUpdate == 2:
        cur.execute('UPDATE Users set status =2, dateInvited =(?) WHERE discordID like(?)',
                    (str(date1), str(discordID)))
    elif statusUpdate == 0:
        cur.execute('UPDATE Users set status =0, dateRemoved =(?) WHERE discordID like(?)',
                    (str(date1), str(discordID)))
    else:
        cur.execute('UPDATE Users set status =(?) WHERE discordID like(?)',
                    (int(statusUpdate), str(discordID)))
    return


def getCurrentStatus(conn, discordID):
    status = 5
    cur = conn.cursor()
    cur.execute('select status from Users where discordID like(?)', (str(discordID),))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        status = rowTuple[0]
    if len(rows) == 0:
        status = 5
    return status


def getCurrentPlexUsername(conn, plexEmailAddress):
    cur = conn.cursor()
    cur.execute('select plexUsername from Users where plexEmailAddress like(?)', (plexEmailAddress,))
    rows = cur.fetchone()
    rowTuple = rows[0]
    userName = str(rowTuple)
    return userName


def updateUsernameForPlexEmailAddress(conn, pEmailAddress, pUsername):
    cur = conn.cursor()
    cur.execute('UPDATE Users set plexUsername =(?) WHERE plexEmailAddress like(?)', (pUsername, pEmailAddress))
    return


def getDateInvited(conn, discordID):
    dateInvited = ""
    cur = conn.cursor()
    cur.execute('select dateInvited from Users where discordID like(?)', (str(discordID),))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        dateInvited = rowTuple[0]
    if len(rows) == 0:
        dateInvited = ""
    return dateInvited


def getDateInvitedByUsername(conn, plexUsername):
    dateInvited = ""
    cur = conn.cursor()
    cur.execute('select dateInvited from Users where plexUsername like(?)', (str(plexUsername),))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        dateInvited = rowTuple[0]
    if len(rows) == 0:
        dateInvited = ""
    return dateInvited


def getBotPlexUsersQueued(conn):
    rDict = {}
    cur = conn.cursor()
    cur.execute('select plexEmailAddress, status from Users where status = 4 order by dateQueued')
    BotPlexUsers = cur.fetchall()
    for x in BotPlexUsers:
        # .update function to append the values to the dictionary
        rDict.update({str(x[0]).lower(): x[1]})
    return rDict


def getBotPlexUsersNoUsername(conn):
    username = 'NEEDSUPDATED'
    rDict = {}
    cur = conn.cursor()
    cur.execute('select plexEmailAddress, plexUsername from Users where plexUsername =(?)', (username,))
    BotPlexUsers = cur.fetchall()
    for x in BotPlexUsers:
        # .update function to append the values to the dictionary
        rDict.update({str(x[0]).lower(): x[1]})
    return rDict


def updateCommandUsageHistory(conn, commandHistoryAdd):
    sql = ''' INSERT INTO CommandHistory(commandName,discordServerNickname,discordUsername,discordID,dateTime,
    valuesSent) 
    VALUES(?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, commandHistoryAdd)
    return


def updateBotActionHistory(values):
    sql = ''' INSERT INTO BotActionHistory(action,dateTime,automaticOrManual) 
    VALUES(?,?,?) '''
    cur = DB_CONNECTION.cursor()
    cur.execute(sql, values)
    return


def checkDiscordIDExists(conn, discordID):
    cur = conn.cursor()
    cur.execute('select 1 from Users where discordID like(?)', (discordID,))
    rows = cur.fetchall()
    if len(rows) >= 1:
        exists = True
    else:
        exists = False
    return exists


def checkStatus(conn, discordID):
    cur = conn.cursor()
    cur.execute('select status from Users where discordID like(?)', (discordID,))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        status = rowTuple[0]
    else:
        status = 5
    return status


def getInactiveRemovalDate(conn, discordID):
    cur = conn.cursor()
    cur.execute('select dateRemoved from Users where discordID like(?)', (discordID,))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        removalDate1 = rowTuple[0]
    return removalDate1


def updateQueuedDateAndStatus(conn, discordID, dateTime, newStatus):
    cur = conn.cursor()
    cur.execute('UPDATE Users set dateQueued =(?), status =(?) WHERE discordID like(?)',
                (dateTime, newStatus, discordID))
    return


def updateRemovedDateAndStatus(conn, discordNickname):
    date1 = datetime.datetime.now()
    newstatus = 1
    cur = conn.cursor()
    cur.execute('UPDATE UserTable set DateRemoved =(?), Status =(?) WHERE DiscordServerNickname like(?)',
                (date1, newstatus, discordNickname))
    return


def getCurrentQueueDate(conn, discordID):
    cur = conn.cursor()
    cur.execute('select dateQueued from Users where discordID like(?)', (discordID,))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        currentQueueDate = str(rowTuple[0])
    return currentQueueDate


def getNumberQueuedAhead(conn, dateQueued):
    blankString = ''
    cur = conn.cursor()
    cur.execute('select count() from Users where status = 4 and dateQueued <(?) and dateQueued !=(?)',
                (dateQueued, blankString,))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        numberAhead = rowTuple[0]
    if len(rows) < 1:
        numberAhead = 0
    return numberAhead


def checkPlexEmailExists(conn, plexEmailToCheck):
    exists = False
    cur = conn.cursor()
    cur.execute('select 1 from Users where plexEmailAddress like(?)', (plexEmailToCheck,))
    rows = cur.fetchall()
    if len(rows) >= 1:
        exists = True
    return exists


def getInvitedStatusCount(conn):
    cur = conn.cursor()
    cur.execute('select count() from Users where status = 2 or Status = 3')
    rows = cur.fetchall()
    rowTuple = rows[0]
    invitedStatusCount = rowTuple[0]
    return invitedStatusCount


def inviteUser(conn, serverName, email):
    localSession = Session()
    localSession.verify = False
    if not localSession.verify:
        # Disable the warning that the request is insecure, we know that...
        from urllib3 import disable_warnings
        from urllib3.exceptions import InsecureRequestWarning
        disable_warnings(InsecureRequestWarning)
    cur = conn.cursor()
    cur.execute('select 1 from PlexServerConfiguration where serverName like(?)', (serverName,))
    rows = cur.fetchall()
    rowTuple = rows[0]
    plex = PlexServer(rowTuple[2], rowTuple[3], localSession)
    sections_lst = [x.title for x in plex.library.sections()]
    plex.myPlexAccount().inviteFriend(user=email, server=plex, sections=sections_lst, allowSync=None,
                                      allowCameraUpload=None, allowChannels=None, filterMovies=None,
                                      filterTelevision=None, filterMusic=None)
    return


def getTotalOpenSlotsCount():
    Accounts = getPlexAccounts()
    openSlotsCount = 0
    for account in Accounts:
        try:
            PLEX_USERS = {user.email: user.friend for user in account.users()}
            plexUserCount = len(PLEX_USERS)
            if plexUserCount < 100:
                openSlotsCount += 100 - plexUserCount
        except Exception as e:
            print(str(e))
    return openSlotsCount


def getPlexAccounts(conn):
    localSession = Session()
    localSession.verify = False
    if not localSession.verify:
        # Disable the warning that the request is insecure, we know that...
        from urllib3 import disable_warnings
        from urllib3.exceptions import InsecureRequestWarning
        disable_warnings(InsecureRequestWarning)
    accountsReturned = []
    cur = conn.cursor()
    cur.execute('select * from PlexServerConfiguration')
    rows = cur.fetchall()
    for row in rows:
        try:
            Server = PlexServer(baseurl=str(row[2]), token=str(row[3]), session=localSession)
            Account = Server.myPlexAccount()
            accountsReturned.append(Account)
        except Exception as e:
            print(str(e))
    return accountsReturned


def getOpenSlotsCountForServer(Server):
    openSlotsCount = 0
    Account = Server.myPlexAccount()
    try:
        PLEX_USERS = {user.email: user.friend for user in Account.users()}
        plexUserCount = len(PLEX_USERS)
        if plexUserCount < 100:
            openSlotsCount += 100 - plexUserCount
    except Exception as e:
        print(str(e))
    return openSlotsCount


def getFirstPlexServerNameWithOpenSlots(conn):
    localSession = Session()
    localSession.verify = False
    if not localSession.verify:
        # Disable the warning that the request is insecure, we know that...
        from urllib3 import disable_warnings
        from urllib3.exceptions import InsecureRequestWarning
        disable_warnings(InsecureRequestWarning)
    serverNameToUse = ""
    cur = conn.cursor()
    cur.execute('select * from PlexServerConfiguration')
    rows = cur.fetchall()
    for row in rows:
        Server = PlexServer(baseurl=str(row[2]), token=str(row[3]), session=localSession)
        Account = Server.myPlexAccount()
        PLEX_USERS = {user.email: user.friend for user in Account.users()}
        plexUserCount = len(PLEX_USERS)
        if plexUserCount < 100:
            serverNameToUse = (str(row[1]))
            break
    return serverNameToUse


def getPendingInvitesCount(conn1):
    cur = conn1.cursor()
    cur.execute('select count() from UserTable where Status = 4')
    rows = cur.fetchall()
    rowTuple = rows[0]
    queuedStatusCount = rowTuple[0]
    return queuedStatusCount


def addInvitedUser(conn, addInvitedUserValues):
    sql = ''' INSERT INTO Users(discordID,discordUsername,discordServerNickname,plexEmailAddress,status,dateInvited)
                  VALUES(?,?,?,2,?) '''
    cur = conn.cursor()
    cur.execute(sql, addInvitedUserValues)
    return


def addQueuedUser(conn, addQueuedUserValues):
    sql = ''' INSERT INTO UserTable(discordID,discordUsername,discordServerNickname,plexEmailAddress,Status,dateQueued)
                      VALUES(?,?,?,4,?) '''
    cur = conn.cursor()
    cur.execute(sql, addQueuedUserValues)
    return


def getNicknameForPlexEmail(conn1, plexEmailToCheck):
    cur = conn1.cursor()
    cur.execute('select DiscordServerNickname from UserTable where PlexEmailAddress like(?)', (plexEmailToCheck,))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        discordNickname = rowTuple[0]
    if len(rows) < 1:
        discordNickname = "DONOT"
    return discordNickname


def getPlexEmailForDiscordID(conn, discordID):
    discordIDReturn = ""
    cur = conn.cursor()
    cur.execute('select plexEmailAddress from Users where discordID like(?)', (discordID,))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        discordIDReturn = rowTuple[0]
    if len(rows) < 1:
        discordIDReturn = "DONOT"
    return discordIDReturn


def getDiscordNameForDiscordNickname(conn1, dNicknameToCheck):
    cur = conn1.cursor()
    cur.execute('select DiscordUsername from UserTable where DiscordServerNickname like(?)', (dNicknameToCheck,))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        discordUsername = rowTuple[0]
    if len(rows) < 1:
        discordUsername = "DONOT"
    return discordUsername


def getDiscordIDForPlexEmail(conn, pEmail):
    discordID = ""
    cur = conn.cursor()
    cur.execute('select discordID from Users where plexEmailAddress like(?)', (pEmail,))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        discordID = rowTuple[0]
    if len(rows) < 1:
        discordID = "DONOT"
    return discordID


def getDiscordNicknameNameForPlexEmail(conn, pEmail):
    cur = conn.cursor()
    cur.execute('select DiscordServerNickname from UserTable where PlexEmailAddress like(?)', (pEmail,))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        dNickname = rowTuple[0]
    if len(rows) < 1:
        dNickname = "DONOT"
    return dNickname


def getEverythingForDiscordNickname(conn1, dNickname):
    cur = conn1.cursor()
    cur.execute('select * from UserTable where DiscordServerNickname like(?)', (dNickname,))
    rows = cur.fetchall()
    everythingR = rows
    if len(rows) == 0:
        everythingR = "DONOT"
    return everythingR


def getQueuedRoleName(conn):
    queuedRoleName = ""
    cur = conn.cursor()
    cur.execute('select queuedRole from BotConfiguration')
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        queuedRoleName = rowTuple[0]
    return queuedRoleName


def getRemovedRoleName(conn):
    removedRoleName = ""
    cur = conn.cursor()
    cur.execute('select removedRole from BotConfiguration')
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        removedRoleName = rowTuple[0]
    return removedRoleName


def getServerNameForUser(conn, discordID):
    serverNameForUser = ""
    cur = conn.cursor()
    cur.execute('select serverName from Users where discordID like(?)', (str(discordID),))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        serverNameForUser = rowTuple[0]
    return serverNameForUser


def getServerInvitedRoleName(conn, serverName):
    serverInvitedRoleName = ""
    cur = conn.cursor()
    cur.execute('select invitedDiscordRole from PlexServerConfiguration where serveName like(?)', (serverName,))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        serverInvitedRoleName = rowTuple[0]
    return serverInvitedRoleName


def removeFromUserTable(conn1, memberNicknameToRemove):
    cur = conn1.cursor()
    cur.execute('delete from UserTable where DiscordServerNickname =(?)', (memberNicknameToRemove,))
    return


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

# endregion


# -----conn variable created here, so I didnt have to move the db def above the other variables
# conn = create_connection(database)


@client.event
async def on_ready():
    # ********Variables for this event ********
    configureMeMessage = 'I need configured. Please start with !configure'
    MY_GUILD = client.get_guild(GUILD_ID)
    conn = create_connection(database)
    queuedRole = discord.utils.get(MY_GUILD.roles, name=str(getQueuedRoleName(conn)))
    removedRole = discord.utils.get(MY_GUILD.roles, name=str(getRemovedRoleName(conn)))
    conn.close()
    # ********End Variables for this event ********
    print("The bot is ready!")
    # configure later, should pull prefix from db config.
    # game = discord.Game(name="try !help")
    MY_GUILD = client.get_guild(GUILD_ID)
    if CONFIGURED is False:
        owner = MY_GUILD.owner
        # check if dm exists, if not create it
        if owner.dm_channel is None:
            await owner.create_dm()
        # if creation of dm successful
        if owner.dm_channel is not None:
            await owner.dm_channel.send(configureMeMessage)
        # message general channel as well
        for channel in MY_GUILD.channels:
            if channel.name == 'general':
                await channel.send(configureMeMessage)

    @loop(minutes=10)
    async def every_10m_jobs():
        print("10m task run " + str(datetime.datetime.now()))
        try:
            PLEX_USERS = {user.email.lower(): user.friend for user in ACCOUNT.users()}
            PLEX_USERS_USERNAME = {user.email.lower(): user.username for user in ACCOUNT.users()}
            ifIsTrue = True
        except Exception as e:
            print(str(e))
            ifIsTrue = False
        conn = create_connection(database)
        BOT_PLEX_USERS = getBotPlexUsers(conn)
        conn.close()
        conn = create_connection(database)
        BOT_PLEX_USERS_QUEUED = getBotPlexUsersQueued(conn)
        conn.close()
        conn = create_connection(database)
        BOT_PLEX_USERS_NO_USERNAME = getBotPlexUsersNoUsername(conn)
        conn.close()
        # UPDATE STATUS FROM PLEX VALUES
        if ifIsTrue:
            for xEmail, xIsFriend in PLEX_USERS.items():
                date1 = datetime.datetime.now()
                # if isFriend is false, then they havent accepted the invite yet.
                # if they are in this list at all, they have obviously been invited.
                # there will be no manual invites as a matter of policy,
                # so they will be in botDB, if they are in this list
                conn = create_connection(database)
                discordID = getDiscordIDForPlexEmail(conn, xEmail)
                conn.close()
                conn = create_connection(database)
                statusInBotDB = getCurrentStatus(conn, str(xEmail))
                conn.close()
                if xIsFriend and statusInBotDB != 3:
                    print("Email: " + str(xEmail) + " is friend and status in botDB is not 3. Update to 3")
                    conn = create_connection(database)
                    with conn:
                        updateStatusForDiscordID(conn, str(discordID), 3)
                        valuesToSend = ("update status to 3, because they -" + xEmail + " - have accepted the invite",
                                        str(date1), "AUTOMATIC")
                        updateBotActionHistory(conn, valuesToSend)
                    conn.close()
                # if username from plex is not blank, but the status is 2, then they must have accepted the invite
                # and need updated to status of 3
                elif not xIsFriend and statusInBotDB != 2 and statusInBotDB != 5:
                    print("Email: " + str(xEmail) + " is NOT friend and status in botDB is not 2. Update to 2")
                    conn = create_connection(database)
                    with conn:
                        updateStatusForDiscordID(conn, str(discordID), 2)
                        valuesToSend = (str(xEmail) + " has an unaccepted invite, but status is not 2. Make it 2",
                                        str(date1), "AUTOMATIC")
                        updateBotActionHistory(conn, valuesToSend)
                    conn.close()
                elif not xIsFriend and statusInBotDB == 5:
                    print("Email: " + str(xEmail)
                          + " was not found in the botDB. Likely a typo email. Remove from plex")
                    tryAgain1 = 0
                    try:
                        ACCOUNT.removeFriend(xEmail)
                    except Exception as e:
                        print("was not a plex account: " + str(e) + " Running no account removal instead")
                        tryAgain1 = 1
                    if tryAgain1 == 1:
                        try:
                            ACCOUNT.removeFriendNoAccount(xEmail)
                        except Exception as e:
                            print("Tried no account removal, that did not work. " + str(e))
                            tryAgain1 = 2
                    if tryAgain1 == 2:
                        try:
                            ACCOUNT.removeFriendNoAccount(xEmail)
                        except Exception as e:
                            print("Tried no server friend removal, that did not work " + str(e))
                    conn = create_connection(database)
                    with conn:
                        valuesToSend = (xEmail + " was not found in the botDB. Likely typo email, remove from plex.",
                                        str(date1), "AUTOMATIC")
                        updateBotActionHistory(conn, valuesToSend)
                    conn.close()

        # update based on the return of values from Plex ^^^^^
        # update based on return of values from Plex has to run before the check for self-removal section
        # check for self-removal vvvvvvv

        # CHECK FOR USER SELF REMOVAL FROM PLEX SERVER
        # DM discord user that their status has changed.
        if len(BOT_PLEX_USERS) > 0 and ifIsTrue:
            for xEmail, xStatus in BOT_PLEX_USERS.items():
                date1 = datetime.datetime.now()
                if str(xEmail) not in PLEX_USERS and (xStatus == 2 or xStatus == 3):
                    # if found in the DB and not in plex, and status is invited or invitedAccepted then it should be 0
                    conn = create_connection(database)
                    discordID = getDiscordIDForPlexEmail(conn, str(xEmail))
                    serverName = getServerNameForUser(conn, discordID)
                    invitedRoleName = getServerInvitedRoleName(conn, serverName)
                    invitedRole = discord.utils.get(MY_GUILD.roles, name=invitedRoleName)
                    conn.close()
                    dmmsg = ""
                    if discordID != "DONOT":
                        member = discord.utils.get(MY_GUILD.members, id=discordID)
                        if member is not None:
                            await member.remove_roles(invitedRole)
                            await member.add_roles(removedRole)
                            await member.create_dm()
                            try:
                                await member.dm_channel.send(
                                    "Hi + " + str(discordID) + "! \n\n"
                                    + "It seems you left the Plex server!\n"
                                    + "Your status has been updated in my DB, "
                                    + "and your role in my discord server has been updated to **Removed**\n"
                                    + "If you would like to be added back to the server try "
                                    + "responding to me with **!invite**"
                                )
                                dmmsg = "successful!"
                            except Exception as e:
                                # print(str(e))
                                dmmsg = str(e)
                    conn = create_connection(database)
                    with conn:
                        updateStatusForDiscordID(conn, str(discordID), 0)
                        valuesToSend = (xEmail +
                                        "must have left the plex server, remove from botDB and set discord Role to "
                                        "removed" + "dmmsg" + dmmsg, str(date1), "AUTOMATIC")
                        updateBotActionHistory(conn, valuesToSend)
                    conn.close()

        # REMOVE USERS WHO DONT ACCEPT THE INVITE for more than 3 days, and update status to 0
        # DM those discord users that their status has been changed.
        todayMinus3 = (datetime.datetime.now() - datetime.timedelta(days=3))
        if ifIsTrue:
            for xEmail, xIsFriend in PLEX_USERS.items():
                date1 = datetime.datetime.now()
                conn = create_connection(database)
                statusInBotDB = getCurrentStatus(conn, xEmail)
                conn.close()
                conn = create_connection(database)
                invitedDate = getDateInvited(conn, xEmail)
                conn.close()
                if statusInBotDB == 2 and invitedDate < str(todayMinus3):
                    conn = create_connection(database)
                    discordID = getDiscordIDForPlexEmail(conn, str(xEmail))
                    conn.close()
                    dmmsg = ""
                    if discordID != "DONOT":
                        member = discord.utils.get(MY_GUILD.members, id=discordID)
                        if member is not None:
                            await member.remove_roles(invitedRole)
                            await member.add_roles(removedRole)
                            await member.create_dm()
                            try:
                                await member.dm_channel.send(
                                    "Hi + " + str(discordID) + "! \n\n"
                                    + "You were invited to my Plex server, "
                                    + "but you didn't accept the invite for more than 3 days. \n"
                                    + "Your status has been updated in my DB, "
                                    + "and your role in my discord server has been updated to **Removed**\n"
                                    + "If you would like to be added back to the plex server try "
                                    + "responding to me with **!invite**"
                                )
                                dmmsg = "successful!"
                            except Exception as e:
                                dmmsg = str(e)
                    conn = create_connection(database)
                    with conn:
                        updateStatusForDiscordID(conn, str(discordID), 0)
                        valuesToSend = (str(discordID) + " removed for not accepting invite within 3 days. dmmsg: "
                                        + dmmsg, str(date1), "AUTOMATIC")
                        updateBotActionHistory(conn, valuesToSend)
                    conn.close()
                    tryAgain = 0
                    try:
                        ACCOUNT.removeFriend(xEmail)
                    except Exception as e:
                        print("was not a plex account: " + str(e) + " Running no account removal instead")
                        tryAgain = 1
                    if tryAgain == 1:
                        try:
                            ACCOUNT.removeFriendNoAccount(xEmail)
                        except Exception as e:
                            print("Tried no account removal, that did not work." + str(e))
                    print("------found one that didnt accept the invite for more than 3 days")

        # should run invite action last, after updating status and removing users who havent accepted invites.

        # RUN INVITE ACTION (should only apply if someone left the server, but still be run periodically)
        # BOT_PLEX_USERS_QUEUED returns only users in a status of 4, ordered by DateQueued ASC (oldest first)
        # if invited, DM them that they have been invited and the role has changed.
        if len(BOT_PLEX_USERS_QUEUED) > 0:
            for xEmail, xStatus in BOT_PLEX_USERS_QUEUED.items():
                date1 = datetime.datetime.now()
                openSlots = getTotalOpenSlotsCount()
                if openSlots > 0:
                    # change to use invite method later.
                    # pyExecStr = 'python ' + INVITE_SCRIPT_PATH + ' --user ' + xEmail + ' --allLibraries'
                    # os.system(pyExecStr)
                    conn = create_connection(database)
                    discordID = getDiscordIDForPlexEmail(conn, str(xEmail))
                    conn.close()
                    dmmsg = ""
                    if discordID != "DONOT":
                        member = discord.utils.get(MY_GUILD.members, id=discordID)
                    if member is not None:
                        await member.remove_roles(queuedRole)
                        await member.add_roles(invitedRole)
                        await member.create_dm()
                        try:
                            await member.dm_channel.send(
                                "Hi + " + str(discordID) + "! \n\n"
                                + "You were next in line and have been invited to the Plex server!\n"
                                + "Your status has been updated in my DB, "
                                + "and your role in my discord server has been updated to **Invited**\n"
                            )
                            dmmsg = "successful!"
                        except Exception as e:
                            dmmsg = str(e)
                    conn = create_connection(database)
                    with conn:
                        updateStatusForDiscordID(conn, str(discordID), 2)
                        valuesToSend = ("sent invite to queued user " + str(discordID) + " --DM Successful/Exception: "
                                        + str(dmmsg), str(date1), "AUTOMATIC")
                        updateBotActionHistory(conn, valuesToSend)
                    conn.close()
                    # print("------found queued user that gets invited")

        # update plex username value in botDB if there is one from plex.
        if len(BOT_PLEX_USERS_NO_USERNAME) > 0 and ifIsTrue:
            for xEmail, xUsername in BOT_PLEX_USERS_NO_USERNAME.items():
                if xEmail in PLEX_USERS_USERNAME:
                    xUsernamePlex = PLEX_USERS_USERNAME[xEmail]
                    conn = create_connection(database)
                    with conn:
                        updateUsernameForPlexEmailAddress(conn, xEmail.lower(), xUsernamePlex.lower())
                        valuesToSend = ("updated plex username" + str(xUsernamePlex) + " in db for " + xEmail,
                                        str(date1), "AUTOMATIC")
                        updateBotActionHistory(conn, valuesToSend)
                    conn.close()

    @loop(hours=48)
    async def every_12h_jobs():
        # update to get all plex servers and check activity on the ones that say yes for check inactivity
        print("48h task run " + str(datetime.datetime.now()))
        TAUTULLI_URL = 'http://192.168.86.5:8181'
        TAUTULLI_APIKEY = '15a2eb6ccdeb49cc9f5871b52b66fdaa'
        USERNAME_IGNORE = ['bbock727', 'iainm27']
        USERNAME_IGNORE = [username.lower() for username in USERNAME_IGNORE]

        try:
            SECTIONS = [section.title for section in SERVER.library.sections()]
            PLEX_USERS = {user.id: user.title for user in ACCOUNT.users()}
            PLEX_USERS.update({int(ACCOUNT.id): ACCOUNT.title})
            IGNORED_UIDS = [uid for uid, username in PLEX_USERS.items() if username.lower() in USERNAME_IGNORE]
            IGNORED_UIDS.extend((int(ACCOUNT.id), 0))
            ifIsTrue1 = True
        except Exception as e:
            print(str(e))
            ifIsTrue1 = False
        REMOVE_LIMIT = 8  # Days to allow inactivity before removing.
        UNSHARE_LIMIT = 30  # Days
        IGNORE_NEVER_SEEN = False
        DRY_RUN = False  # set to True to see console output of what users would be removed for inactivity.
        try:
            PLEX_USERS_EMAIL = {user.id: user.email for user in ACCOUNT.users()}
            ifIsTrue2 = True
        except Exception as e:
            print(str(e))
            ifIsTrue2 = False
        # Get the Tautulli history.
        PARAMS = {
            'cmd': 'get_users_table',
            'order_column': 'last_seen',
            'order_dir': 'asc',
            'length': 600,
            'apikey': TAUTULLI_APIKEY
        }
        TAUTULLI_USERS = []
        if (ifIsTrue1):
            try:
                GET = SESSION.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=PARAMS).json()['response']['data'][
                    'data']
                for user in GET:
                    if user['user_id'] in IGNORED_UIDS:
                        # print(str(user['user_id']))
                        continue
                    elif IGNORE_NEVER_SEEN and not user['last_seen']:
                        continue
                    TAUTULLI_USERS.append(user)
            except Exception as e:
                exit("Tautulli API 'get_users_table' request failed. Error: {}.".format(e))

        todayMinusRL = (datetime.datetime.now() - datetime.timedelta(days=REMOVE_LIMIT))
        NOW = datetime.datetime.today()
        for user in TAUTULLI_USERS:
            OUTPUT = []
            USERNAME = user['friendly_name']
            UID = user['user_id']
            conn = create_connection(database)
            invitedDate = getDateInvitedByUsername(conn, USERNAME)
            conn.close()
            inviteLessThanRLOLD = False
            noInvitedDate = True
            if invitedDate is not None:
                # if they have an invite date
                noInvitedDate = False
                # print('Username: ' + str(USERNAME) + ', Invited Date from botDB: ' + str(invitedDate)
                #       + ', Today Minus Removal Limit: '
                #       + str(todayMinusRL))
                if str(invitedDate) > str(todayMinusRL):
                    # if that invite date is less than REMOVE_LIMIT (8days) old
                    inviteLessThanRLOLD = True
            else:
                noInvitedDate = True
            if not user['last_seen']:
                TOTAL_SECONDS = None
                OUTPUT = '{} has never used the server'.format(USERNAME)
            else:
                TOTAL_SECONDS = int((NOW - datetime.datetime.fromtimestamp(user['last_seen'])).total_seconds())
                OUTPUT = '{} was last seen {} ago'.format(USERNAME, time_format(TOTAL_SECONDS))

            if UID not in PLEX_USERS.keys():
                continue

            TOTAL_SECONDS = TOTAL_SECONDS or 86400 * UNSHARE_LIMIT
            if TOTAL_SECONDS >= (REMOVE_LIMIT * 86400) and (not inviteLessThanRLOLD and not noInvitedDate):
                if DRY_RUN:
                    print('{}, and would be removed.'.format(OUTPUT))
                    conn = create_connection(database)
                    discordID = getDiscordIDForPlexEmail(conn, str(PLEX_USERS_EMAIL[UID]))
                    conn.close()
                    print("discord name: " + str(discordID) + " obtained from email address:" + str(
                        PLEX_USERS_EMAIL[UID]))
                else:
                    if ifIsTrue1 and ifIsTrue2:
                        try:
                            ACCOUNT.removeFriend(PLEX_USERS[UID])
                        except Exception as e:
                            print("was not a plex account: " + str(e) + " Running no account removal instead")
                            ACCOUNT.removeFriendNoAccount(PLEX_USERS_EMAIL[UID])
                        conn = create_connection(database)
                        discordID = getDiscordIDForPlexEmail(conn, str(PLEX_USERS_EMAIL[UID]))
                        serverName = getServerNameForUser(conn, discordID)
                        invitedRoleName = getServerInvitedRoleName(conn, serverName)
                        conn.close()
                        invitedRole = discord.utils.get(MY_GUILD.roles, name=invitedRoleName)
                        dmmsg = ""
                        if discordID != "DONOT":
                            member = discord.utils.get(MY_GUILD.members, id=discordID)
                            if member is not None:
                                await member.remove_roles(invitedRole)
                                await member.add_roles(removedRole)
                                await member.create_dm()
                                try:
                                    await member.dm_channel.send(
                                        "Hi + " + str(discordID) + "! \n\n"
                                        + "You were removed for inactivity!\n"
                                        + "Your status has been updated in my DB, "
                                        + "and you role in my discord server has been updated to **Removed**\n"
                                        + "If you would like to be added back to the server try "
                                        + "responding to me with **!invite**"
                                    )
                                    dmmsg = "successful!"
                                except Exception as e:
                                    dmmsg = str(e)
                        conn = create_connection(database)
                        with conn:
                            updateStatusForDiscordID(conn, str(discordID), 0)
                            valuesToSend = ("Inactivity removal. dmmsg" + dmmsg, str(datetime.datetime.now()),
                                            "AUTOMATIC")
                            updateBotActionHistory(conn, valuesToSend)
                        conn.close()
                        # run tautulli command to delete user.
                        uidString = str(UID)
                        PARAMS1 = {
                            'cmd': 'delete_user',
                            'user_id': uidString,
                            'apikey': TAUTULLI_APIKEY
                        }
                        # SESSION.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=PARAMS).json()
                        try:
                            SESSION.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=PARAMS1).json()
                        except Exception as e:
                            print("Tautulli API 'delete_user' request failed. Error: {}.".format(e))
            elif TOTAL_SECONDS >= (UNSHARE_LIMIT * 86400):
                if DRY_RUN:
                    print('{}, and would unshare libraries.'.format(OUTPUT))
                else:
                    for server in ACCOUNT.user(PLEX_USERS[UID]).servers:
                        if server.machineIdentifier == SERVER.machineIdentifier and server.sections():
                            print('{}, and has reached their inactivity limit. Unsharing.'.format(OUTPUT))
                            ACCOUNT.updateFriend(PLEX_USERS[UID], SERVER, SECTIONS, removeSections=True)
                        else:
                            print("{}, has already been unshared, but has not reached their shareless threshold."
                                  "Skipping.".format(OUTPUT))

    # every_10m_jobs.start()
    # every_12h_jobs.start()


@client.event
async def on_member_join(member):
    date1 = datetime.datetime.now()
    newNick = str(member).replace(" ", "")
    # print(str(newNick))
    try:
        await member.create_dm()
        await member.dm_channel.send(
            "Hi " + str(member) + "! \n\n"
            + "Thanks for joining my discord server!\n"
            + "The discord invite link you followed put you in the "
            # + "<#" + BOT_CHAT_CHANNEL_ID + "> channel. You can interact with me there for Plex server invites.\n"
            + "Try replying to me with **!help**, **!rules**, or **!invite** for more information."
        )
        await member.edit(nick=newNick)
        dmSuccess = "DM SUCCESSFUL"
    except Exception as e:
        dmSuccess = "DM UNSUCCESSFUL"
    conn = create_connection(database)
    with conn:
        valuesToSend = ("DiscordJoin member" + str(member) + "newNickname " + str(newNick) + dmSuccess, str(date1),
                        "AUTOMATIC")
        updateBotActionHistory(conn, valuesToSend)
    conn.close()


@client.event
async def on_member_remove(member):
    # TODO add api call to Tautulli to remove as well
    memNickname = member.nick
    memName = member.name
    memID = member.id
    date1 = datetime.datetime.now()
    conn = create_connection(database)
    memDBStatus = checkStatus(conn, memID)
    conn.close()
    conn = create_connection(database)
    pEmail = getPlexEmailForDiscordID(conn, str(memID))
    conn.close()
    conn = create_connection(database)
    emailExists = checkPlexEmailExists(conn, pEmail)
    conn.close()
    # replace with if 2, if 3. use new pendingInvite method
    # https://python-plexapi.readthedocs.io/en/latest/modules/myplex.html#plexapi.myplex.MyPlexUser
    # if memDBStatus == 2 or memDBStatus == 3 and emailExists:
    #     try:
    #         removeFromUserTable(DB_CONNECTION, str(memID))
    #     except Exception as e:
    #         print("Something went wrong: Error: {}.".format(e))
    #     try:
    #         ACCOUNT.removeFriend(pEmail)
    #     except Exception as e:
    #         print("was not a plex account: " + str(e) + " Running no account removal instead")
    #         ACCOUNT.removeFriendNoAccount(pEmail)
    # elif emailExists:
    #     try:
    #         removeFromUserTable(DB_CONNECTION, str(memNickname))
    #     except Exception as e:
    #         print("Something went wrong: Error: {}.".format(e))
    conn = create_connection(database)
    with conn:
        valuesToSend = ("member left discord so removed from plex and DB " + str(memNickname) + " " + str(memName) + " "
                        + str(memID), str(date1), "AUTOMATIC")
        updateBotActionHistory(conn, valuesToSend)
    conn.close()


# ---------once a message is received
@client.event
async def on_message(message):
    # ********Variables for this event ********
    conn = create_connection(database)
    commandPrefix = str(getCommandPrefix(conn))
    conn.close()
    # print(commandPrefix)
    # will return either a member or user object
    mesAuthor = message.author
    mesChannel = message.channel
    mesChannelType = mesChannel.type
    # manually set here, in case the message doesnt come from bot chat.
    memNickname = "FromPrivateChannel"
    channelType = mesChannel.type
    channelTypeName = channelType.name
    memName = mesAuthor.name
    memID = mesAuthor.id
    date1 = datetime.datetime.now()
    MY_GUILD = client.get_guild(GUILD_ID)
    conn = create_connection(database)
    queuedRole = discord.utils.get(MY_GUILD.roles, name=str(getQueuedRoleName(conn)))
    removedRole = discord.utils.get(MY_GUILD.roles, name=str(getRemovedRoleName(conn)))
    conn.close()
    # ********End Variables for this event ********

    # if the bot somehow messages itself, dont do anything
    if message.author.bot:
        # print("you are a bot!!")
        return

    if message.content.startswith("!configure") and (message.author == MY_GUILD.owner):
        # print("running !configure Logic!")
        conn = create_connection(database)
        localConfigured = getConfiguredValue(conn)
        conn.close()
        if not localConfigured:
            messageArray = message.content.split()
            # have to account for the initial command word
            if len(messageArray) == 7:
                valuesToSend = (str(messageArray[1]), str(messageArray[2]), str(messageArray[3]), str(messageArray[4]),
                                str(messageArray[5]), str(messageArray[6]), 'True')
                print("values sent to configureBot" + str(valuesToSend))
                try:
                    conn = create_connection(database)
                    configureBot(conn, valuesToSend)
                    conn.close()
                    game = discord.Game(name="try " + str(messageArray[6]) + "help")
                    configureMessage = "Successfully configured. Command prefix is now: **" + messageArray[6] + "**"
                    # set it now that its configured so it can listen to other commands.
                    await mesChannel.send(configureMessage)
                    await client.change_presence(activity=game)
                except Error as e:
                    print(e)
            else:
                configureMessage = "incorrect number of parameters. Should have adminDiscordID, botAdminDiscordRole, " \
                                   "botChannelID, queuedRoleName, removedRoleName, and commandPrefix"
                await mesChannel.send(configureMessage)
        else:
            configureMessage = "DB says the bot is already configured. Try updating an individual value instead"
            await mesChannel.send(configureMessage)
    conn = create_connection(database)
    commandPrefix = str(getCommandPrefix(conn))
    conn.close()

    # if message channel type is NOT private then DM the message author and then delete the message.
    if (str(mesChannelType) != "private" or str(mesChannelType) != "group") and \
            (message.content.startswith(commandPrefix + "inviteme") or
             message.content.startswith(commandPrefix + "status")):
        messageArray = message.content.split()
        nonPrivateMessage = "Please don't use the **inviteme** or **status** commands in the public channel. This is " \
                            "for the privacy of your email address. Direct message me with either of those " \
                            "commands."
        conn = create_connection(database)
        with conn:
            valuesBotAction = ("removed status or inviteme message from public channel", str(date1), "AUTOMATIC")
            updateBotActionHistory(conn, valuesBotAction)
            valuesCommandHistory = (str(messageArray[0]), str(memNickname), str(memName), str(memID), str(date1),
                                    str(message.content))
            updateCommandUsageHistory(conn, valuesCommandHistory)
        conn.close()
        if message.author.dm_channel is None:
            await message.author.create_dm()
        # if creation of dm successful
        if message.author.dm_channel is not None:
            await message.author.dm_channel.send(nonPrivateMessage)
        await message.delete()

    # inviteme
    if message.content.find("@") == -1 and message.content.startswith(commandPrefix + "inviteme"):
        conn = create_connection(database)
        with conn:
            valuesToSend = ("inviteme", str(memNickname), str(memName), str(memID), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        conn.close()
        await mesChannel.send("---INVALID EMAIL ADDRESS--- \nShould look like **" + commandPrefix +
                              "inviteme email@address.com**")
    # inviteme
    if message.content.find("@") != -1 and message.content.startswith(commandPrefix + "inviteme"):
        conn = create_connection(database)
        with conn:
            valuesToSend = ("inviteme", str(memNickname), str(memName), str(memID), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        conn.close()
        messageArray = message.content.split()
        if "@" in str(messageArray[1]):
            messageEmail = str(messageArray[1]).lower()
        else:
            messageEmail = "DONOT"
        conn = create_connection(database)
        discordIDExists = checkDiscordIDExists(conn, str(mesAuthor.nick).lower())
        conn.close()
        if discordIDExists and messageEmail != "DONOT":
            conn = create_connection(database)
            status = checkStatus(conn, str(memID))
            conn.close()
            # status 0 = removed for inactivity
            if status == 0:
                inactiveRemovalDate = getInactiveRemovalDate(DB_CONNECTION, memID)
                conn = create_connection(database)
                with conn:
                    updateQueuedDateAndStatus(conn, str(memID), str(date1), 4)
                conn.close()
                conn = create_connection(database)
                newQueueDate = getCurrentQueueDate(conn, memID)
                numberAheadOfYou = getNumberQueuedAhead(conn, newQueueDate)
                conn.close()
                invitememsg = (
                        str(message.author) + ", you were removed for inactivity on this date: "
                        + str(inactiveRemovalDate) + "\n"
                        + ". You have been re-queued. There are **" + str(numberAheadOfYou)
                        + "** people queued ahead of you."
                )
                member = discord.utils.get(MY_GUILD.members, name=memName)
                await member.remove_roles(removedRole)
                await member.add_roles(queuedRole)
            # status 1 = removed manually by admin
            elif status == 1:
                invitememsg = (str(message.author) + ", you were removed manually by an admin. Try sending them a "
                                                     "direct message")
            # status 2 = invited but not yet accepted
            elif status == 2:
                conn = create_connection(database)
                presentEmail = getPlexEmailForDiscordID(conn, str(memID))
                invitememsg = (
                        str(memNickname) + ", you have already been invited using this email address: **"
                        + str(presentEmail) + "** but you haven't accepted the invite yet.\n"
                        + "Check your inbox (including spam) for the invite email."
                )
                conn.close()
            # status 3 = invited and accepted already
            elif status == 3:
                conn = create_connection(database)
                presentEmail = getPlexEmailForDiscordID(conn, str(memID))
                invitememsg = (
                        str(memNickname)
                        + ", an invite has already been sent, and you have accepted it using this email address: "
                        + str(presentEmail)
                )
                conn.close()
            # status 4 = queued for an invite
            elif status == 4:
                conn = create_connection(database)
                presentEmail = getPlexEmailForDiscordID(conn, str(memID))
                yourQueueDate = getCurrentQueueDate(conn, str(memID))
                numberAheadOfYou = getNumberQueuedAhead(conn, yourQueueDate)
                conn.close()
                invitememsg = (
                        str(memNickname)
                        + ", you have been queued for an invite to be sent to this email address: "
                        + presentEmail + "\n You were queued at this time: "
                        + str(yourQueueDate) + " and there are: **"
                        + str(numberAheadOfYou)
                        + "** people queued ahead of you."
                )
            elif status == 5:
                invitememsg = "Something went wrong, the status came back as 5"
        if not discordIDExists and messageEmail != "DONOT":
            # visual break
            conn = create_connection(database)
            plexEmailExists = checkPlexEmailExists(conn, messageEmail)
            plexAccounts = getPlexAccounts(conn)
            openSlots = getTotalOpenSlotsCount()
            numberAheadOfYou = getNumberQueuedAhead(conn, str(date1))
            plexServerToInvite = getFirstPlexServerNameWithOpenSlots(conn)
            conn.close()
            # visual break
            if not plexEmailExists and openSlots > 0 and numberAheadOfYou == 0:
                conn = create_connection(database)
                inviteUser(conn, plexServerToInvite, messageEmail)
                conn.close()
                # replace with call to inviteUser(plexServerToInvite, messageEmail)
                # pyExecStr = 'python ' + INVITE_SCRIPT_PATH + ' --user ' + messageEmail + ' --allLibraries'
                # os.system(pyExecStr)
                conn = create_connection(database)
                with conn:
                    valuesToSend = (str(memID), str(memName), str(memNickname), str(messageEmail), str(date1))
                    addInvitedUser(conn, valuesToSend)
                conn.close()
                invitememsg = ("An invite has been sent to this email address: " + messageEmail)
                member = discord.utils.get(MY_GUILD.members, name=memName)
                conn = create_connection(database)
                invitedRole = discord.utils.get(MY_GUILD.roles, name=str(getServerInvitedRoleName(conn,
                                                                                                  plexServerToInvite)))
                conn.close()
                await member.add_roles(invitedRole)
            if not plexEmailExists and openSlots == 0:
                conn = create_connection(database)
                with conn:
                    valuesToSend = (str(memID), str(memName), str(memNickname), str(messageEmail), str(date1))
                    addQueuedUser(conn, valuesToSend)
                conn.close()
                conn = create_connection(database)
                yourQueueDate = getCurrentQueueDate(conn, memNickname)
                conn.close()
                invitememsg = (
                        str(memNickname)
                        + ", there were no open slots, but you have been added to the queue.\n"
                        + "There are **" + str(numberAheadOfYou)
                        + "** people in front of you. \nYour queued date is: **" + str(yourQueueDate) + "**"
                )
                member = discord.utils.get(MY_GUILD.members, name=memName)
                await member.add_roles(queuedRole)
            if not plexEmailExists and openSlots > 0 and numberAheadOfYou != 0:
                conn = create_connection(database)
                with conn:
                    valuesToSend = (str(memID), str(memName), str(memNickname), str(messageEmail), str(date1))
                    addQueuedUser(conn, valuesToSend)
                conn.close()
                conn = create_connection(database)
                yourQueueDate = getCurrentQueueDate(conn, memNickname)
                conn.close()
                invitememsg = (
                        str(memNickname)
                        + ", there were open slots, but there are others ahead of you in queue."
                        + " You have been added to the  queue.\n There are **" + str(numberAheadOfYou)
                        + "** people in front of you."
                        + " Your queued date is: **" + str(yourQueueDate) + "**"
                )
                member = discord.utils.get(MY_GUILD.members, name=memName)
                await member.add_roles(queuedRole)
            if plexEmailExists:
                invitememsg = (
                        "The email address: " + messageEmail
                        + " has already been used to request an invite. Try " + commandPrefix + "status")
        if messageEmail == "DONOT":
            invitememsg = (
                    "Something went wrong. This is what you sent me: " + str(message.content)
                    + "\n Should look like this **" + commandPrefix + "inviteme email@address.com**"
            )
        await mesChannel.send(invitememsg)
    # status
    if message.content.find("@") == -1 and message.content.startswith(commandPrefix + "status"):
        conn = create_connection(database)
        with conn:
            valuesToSend = ("status", str(memNickname), str(memName), str(memID), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        conn.close()
        channel = message.channel
        await channel.send("---INVALID EMAIL ADDRESS--- Message should look like: **!status email@address.com**")
    # status
    if message.content.find("@") != -1 and message.content.startswith(commandPrefix + "status"):
        conn = create_connection(database)
        with conn:
            valuesToSend = ("status", str(memNickname), str(memName), str(memID), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        conn.close()
        # split the array at spaces by default
        messageArray = message.content.split()
        # if the second element in the array contains the @ symbol
        # first element should
        if "@" in str(messageArray[1]):
            messageEmail = str(messageArray[1]).lower()
        else:
            messageEmail = "DONOT"

        conn = create_connection(database)
        plexEmailExists = checkPlexEmailExists(DB_CONNECTION, str(messageEmail))
        conn.close()
        if plexEmailExists:
            conn = create_connection(database)
            nicknameForPlexEmail = getNicknameForPlexEmail(DB_CONNECTION, str(messageEmail))
            conn.close()
        else:
            nicknameForPlexEmail = "DONOT"
        if plexEmailExists and memNickname != nicknameForPlexEmail and messageEmail != "DONOT":
            statusmsg = (
                    "Found the email, **" + str(messageEmail) + "** but it is tied to a discord user **"
                    + str(nicknameForPlexEmail) + "**, which is not you, **" + str(memNickname)
                    + "**. \n Will not disclose the status."
            )
        elif plexEmailExists and memNickname == nicknameForPlexEmail and messageEmail != "DONOT": \
            conn = create_connection(database)
            status = checkStatus(conn, memID)
            conn.close()
            # status 0 = removed for inactivity
            if status == 0:
                conn = create_connection(database)
                inactiveRemovalDate = getInactiveRemovalDate(conn, memID)
                conn.close()
                statusmsg = (
                        str(memNickname) + ", you were removed on this date: **"
                        + str(inactiveRemovalDate)
                        + "** You can requeue yourself with the **!inviteme** command."
                )
            # status 1 = removed manually by admin
            if status == 1:
                statusmsg = (str(memNickname) + ", you were removed manually by an admin. Try !help")
            # status 2 = invited but not yet accepted
            if status == 2:
                conn = create_connection(database)
                presentEmail = getPlexEmailForDiscordID(conn, str(memID))
                statusmsg = (
                        str(memNickname) + ", you have already been invited using this email address: **"
                        + str(presentEmail) + "** but you haven't accepted the invite yet.\n"
                        + "Check your inbox (including spam) for the invite email."
                )
                conn.close()
            # status 3 = invited and accepted already
            if status == 3:
                conn = create_connection(database)
                presentEmail = getPlexEmailForDiscordID(conn, str(memID))
                statusmsg = (
                        str(memNickname)
                        + ", an invite has already been sent, and you have accepted it using this email address: "
                        + str(presentEmail)
                )
                conn.close()
            # status 4 = queued for an invite
            if status == 4:
                conn = create_connection(database)
                presentEmail = getPlexEmailForDiscordID(conn, str(memID))
                yourQueueDate = getCurrentQueueDate(conn, nicknameForPlexEmail)
                numberAheadOfYou = getNumberQueuedAhead(conn, yourQueueDate)
                conn.close()
                statusmsg = (
                        str(memNickname)
                        + ", you have been queued for an invite to be sent to this email address: "
                        + str(presentEmail) + "\n You were queued at this time: **"
                        + str(yourQueueDate) + "** and there are **"
                        + str(numberAheadOfYou) + "** people queued ahead of you."
                )
        elif messageEmail == "DONOT":
            statusmsg = ("Something about the way you used the command was wrong.\n"
                         + "This is what I got from you: --" + str(message.content) + "--\n"
                         + "Message should look like: **!status email@address.com**")
        elif nicknameForPlexEmail == "DONOT":
            statusmsg = (
                    "I did not find you in the DB, " + str(memName) + ".\n"
                    + "**!status** command will not work for you until you have been invited or queued."
            )
        await mesChannel.send(statusmsg)
    # openslots
    if message.content.lower() == commandPrefix + "openslots":
        conn = create_connection(database)
        with conn:
            valuesToSend = ("openslots", str(memNickname), str(memName), str(memID), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        conn.close()
        openSlotCount = getTotalOpenSlotsCount()
        if openSlotCount > 0:
            openslotsmsg = (
                    "There are **" + str(openSlotCount) + "** open slots. If you are looking for an invite try !invite"
            )
        if openSlotCount == 0:
            openslotsmsg = "There are no open slots, try **!inviteme** to be added to the queue."
        await mesChannel.send(openslotsmsg)
    # pendinginvites
    if message.content.lower() == commandPrefix + "pendinginvites":
        conn = create_connection(database)
        with conn:
            valuesToSend = (
                "pendinginvites", str(memNickname), str(memName), str(memID), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        conn.close()
        conn = create_connection(database)
        pendingInvitesCount = getPendingInvitesCount(conn)
        conn.close()
        if pendingInvitesCount > 0:
            pendinginvitesmsg = (
                    "There are **" + str(pendingInvitesCount)
                    + "** pending invites. \nIf you would like to be added to the queue, try **!invite**"
            )
        if pendingInvitesCount == 0:
            pendinginvitesmsg = "There are no pending invites. Try **!invite** if you want to be invited."
        await mesChannel.send(pendinginvitesmsg)
    # libraries - info
    if message.content.lower() == commandPrefix + "libraries":
        conn = create_connection(database)
        with conn:
            valuesToSend = ("libraries", str(memNickname), str(memName), str(memID), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        conn.close()
        librariesmsg = "As of 04/13/2021 - https://i.imgur.com/89EfWvH.png"
        await mesChannel.send(librariesmsg)
    # currentstreams - info from tautulli
    # NEEDS UPDATED TO SUM ACROSS ALL TAUTULLIS
    # if message.content.lower() == commandPrefix + "currentstreams":
    #     with conn:
    #         valuesToSend = ("currentstreams", str(memNickname), str(memName), str(memID), str(date1),
    #                         str(message.content))
    #         updateCommandUsageHistory(DB_CONNECTION, valuesToSend)
    #     # print("Current Streams!")
    #     # https://github.com/Tautulli/Tautulli/wiki/Tautulli-API-Reference#get_activity
    #     TAUTULLI_URL = 'http://192.168.86.5:8181'
    #     TAUTULLI_APIKEY = '15a2eb6ccdeb49cc9f5871b52b66fdaa'
    #     # Get the Tautulli history.
    #     PARAMS = {
    #         'cmd': 'get_activity',
    #         'apikey': TAUTULLI_APIKEY
    #     }
    #     try:
    #         GET = SESSION.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=PARAMS).json()['response']['data']
    #         # print(str(GET))
    #         currentstreamsmsg = ("**Stream Count:** " + str(GET['stream_count'])
    #                              + "\n**Directly Playing:** " + str(GET['stream_count_direct_play'])
    #                              + "\n**Directly Streaming:** " + str(GET['stream_count_direct_stream'])
    #                              + "\n**Transcoding:** " + str(GET['stream_count_transcode'])
    #                              + "\n**Bandwidth:** " + str(GET['total_bandwidth'] / 1000) + "mbps"
    #                              )
    #     except Exception as e:
    #         print("Tautulli API 'get_activity' request failed. Error: {}.".format(e))
    #         currentstreamsmsg = "Something went wrong."
    #     await mesChannel.send(currentstreamsmsg)
    # help - info
    if message.content.lower() == commandPrefix + "help":
        conn = create_connection(database)
        with conn:
            valuesToSend = ("help", str(message.author), str(memName), str(date1), str(memID), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        conn.close()
        helpmsg = (
                "Try **!commands** for a direct message with the list of commands.\n"
                + "If you are looking for an invite, try **!invite** \n"
                + "Message Jomack16 for anything else."
        )
        await mesChannel.send(helpmsg)
    # invite - info
    if message.content.lower() == commandPrefix + "invite":
        conn = create_connection(database)
        with conn:
            valuesToSend = ("invite", str(memNickname), str(mesAuthor), str(memID), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        conn.close()
        await mesAuthor.create_dm()
        await mesAuthor.dm_channel.send(
            "Hi {}! \n\n".format(mesAuthor) + "You've asked for an invite!\n\n"
            + "To be invited to the plex server, please use the **!inviteme** command like this: "
            + "**!inviteme email@address.com**\n"
            # + "  --must use command in the <#" + BOT_CHAT_CHANNEL_ID + "> channel.\n"
            + "  --must be an email address for a plex account **that you already have**.\n"
            + "  --If you don't have a plex.tv account already, **make one then come back** and request an invite.\n"
        )
    # download - info
    if message.content.lower() == commandPrefix + "download":
        conn = create_connection(database)
        with conn:
            valuesToSend = ("download", str(memNickname), str(memName), str(memID), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        conn.close()
        await mesAuthor.create_dm()
        await mesAuthor.dm_channel.send(
            "Hi {}! \n\n".format(mesAuthor) + "You've asked about downloading from the plex server!\n"
            + "If you wish to download something from the server, please message Jomack16.\n"
            + "Please do not use any apps/plugins/utilities to download without talking to Jomack16 first."
            + " If this unauthorized is discovered, then you will be administratively **removed** from the plex server"
        )
    # removeme - info
    if message.content.lower() == commandPrefix + "removeme":
        conn = create_connection(database)
        with conn:
            valuesToSend = ("removeme", str(memNickname), str(mesAuthor), str(memID), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        conn.close()
        await mesAuthor.create_dm()
        await mesAuthor.dm_channel.send(
            "Hi {}! \n\n".format(mesAuthor) + "You've asked about being removed from the plex server!\n"
            + "If you wished to be removed from the plex server, just leave the discord server.\n"
            + "This will automatically remove you from the plex server."
        )
    # commands - info
    if message.content.lower() == commandPrefix + "commands":
        conn = create_connection(database)
        with conn:
            valuesToSend = ("commands", str(memNickname), str(memName), str(memID), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        conn.close()
        await mesAuthor.create_dm()
        await mesAuthor.dm_channel.send(
            "Hi {}! \n\n".format(mesAuthor) + "Available commands: "
            + "**!invite**, **!inviteme**, **!openslots**, **!pendinginvites**, **!help**, **!status**, "
            + "**!libraries**, **!rules**, **!removeme**, **!download**, **!currentstreams**, and **!commands** \n"
            + "**!invite** will DM you with a message about how to be invited.\n"
            + "**!inviteme email@address.com** will send an invite to that email address.\n"
            # + "    --must use command in the <#" + BOT_CHAT_CHANNEL_ID + "> channel.\n"
            + "    --must be an email address for a plex account that you already have.\n"
            + "    --If you don't have a plex.tv account already, make one then request an invite..\n"
            + "**!status email@address.com** will report your current status.\n"
            # + "    --must be used in the <#" + BOT_CHAT_CHANNEL_ID + "> channel.\n"
            + "**!openslots** will respond with the number of open slots on the server.\n"
            + "**!pendinginvites** will respond with the number of pending invites to the server.\n"
            + "**!help** will respond with info to help.\n"
            + "**!libraries** will respond with a link to library stats.\n"
            + "**!commands** will will DM you this same list again.\n"
            + "**!rules** will respond with the list of server rules.\n"
            + "**!removeme** will repond with how to remove yourself from the plex server.\n"
            + "**!download** will respond with how we feel about downloading from the plex server.\n"
            + "**!speedtest** - speedtest to server information.\n"
            + "**!transcoding** - information about transcoding.\n"
            + "**!currentstreams** will respond with the current number of streams and info about them.\n\n"
            + "If you think of a helpful command, please let Jomack16 know about it!\n\n\n"
        )
    # rules - info
    if message.content.lower() == commandPrefix + "rules":
        conn = create_connection(database)
        with conn:
            valuesToSend = ("rules", str(memNickname), str(mesAuthor), str(memID), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        conn.close()
        await mesChannel.send(
            "Hi {}! \n\n".format(mesAuthor) + "These are the rules: \n"
            + "**1**. You can only get 1 invite. Account sharing is fine, there is no limit on the number of "
            + "simultaneous streams, other than the capability of the server and its bandwidth\n"
            + "**2**. Stay active on Plex, right now the inactivity period is 8 days. If you are inactive for more than"
            + " 192 hours, you will be removed from the Plex server.\n"
            + "**3**. You MUST stay in the discord server. If you leave, the bot will notice and will remove you from "
            + "the Plex server\n"
            + "--3 NOTE: if you come back into the discord server, you can request a new invite with !inviteme\n"
            + "**4**. No downloading directly from the server with any apps or plugins. Try !download\n"
            + "**5**. No spamming or self-promoting in any of the channels. No bullying or unkind behavior to others.\n"
            + "**6**. Remember that this is free. It will not have guaranteed uptime, or any guarantee of any kind.\n"
            + "**7**. No Transcoding 4K video.\n"
            + "--7 NOTE: this does not result in a ban, its just a limit of the server based on resources.\n"
           #  + "--7 NOTE: check your speedtest to the server in the <#" + SPEEDTEST_CHANNEL_ID + "> channel.\n\n"
            + "**Notes:**\nIf you are removed for inactivity, your status and discord role will reflect that, and you "
            + "can add yourself back to the invite queue with **!inviteme**"
        )
    # speedtest - info
    if message.content.lower() == commandPrefix + "speedtest":
        conn = create_connection(database)
        with conn:
            valuesToSend = ("speedtest", str(memNickname), str(mesAuthor), str(memID), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        conn.close()
        await mesChannel.send(
            "Hi\n"
            + "This is the url you can use to run a speedtest from you to the server: "
            + "http://jomack16.hopto.org:558/\n"
            + "You might be checking this because you want to play 4K content, or already tried to play 4K content and"
            + " received a message about not transcoding 4K.\n"
            + "If that is the case try **!transcoding** for more info.\n"
        )
    # transcoding - info
    if message.content.lower() == commandPrefix + "transcoding":
        conn = create_connection(database)
        with conn:
            valuesToSend = ("transcoding", str(memNickname), str(mesAuthor), str(memID), str(date1),
                            str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        conn.close()
        await mesChannel.send(
            "Hi!\n"
            + "Transcoding IS allowed for MOST content on the server.\n"
            + "There is some 4K content, and because of the resource strain, transcoding 4K is not allowed.\n"
            + "For the highest quality/bitrate 4K content (on the server) it is recommended that you have a "
            + "download speed of 200mbps+.\n **NOTE:** a slower speed connection might work for some content.\n"
            + "To see what your connection speed to the server is, try **!speedtest**\n"
        )
    # showmedb - info
    # CHANGE TO CHECK FOR OWNER OR ADMIN ROLE. PULL ADMIN ROLE FROM STRING IN DB.
    # if message.content.startswith(commandPrefix + "showmedb") and str(message.author) in ADMINS:
    #     msgArray = message.content.split()
    #     msgNickD = str(msgArray[1])
    #     with DB_CONNECTION:
    #         valuesToSend = ("showmedb", "Jomack16", "Mr.Mustard_#2954", str(date1), str(message.content))
    #         updateCommandUsageHistory(DB_CONNECTION, valuesToSend)
    #     everything = getEverythingForDiscordNickname(DB_CONNECTION, msgNickD)
    #     # print(str(everything))
    #     eList = everything[0]
    #     if everything != "DONOT":
    #         await messageChannel.send(
    #             "**DiscordUsername**: " + str(eList[1])
    #             + ", **DiscordServerNickname**: " + str(eList[2]) + ", **PlexUsername**: " + str(eList[3])
    #             + ", **PlexEmailAddress**: " + str(eList[4]) + ", **Status**: " + str(eList[6])
    #             + ", **DateRemoved**: " + str(eList[7]) + ", **DateInvited**: " + str(eList[8])
    #             + ", **DateQueued**: " + str(eList[9])
    #         )
    #     else:
    #         await mesChannel.send(str(everything))
    # adminremoveplex
    if message.content.startswith(commandPrefix + "adminremoveplex"):
        msgMember = message.author
        msgArray = message.content.split()
        msgNickname = str(msgArray[1])
        msgID = msgMember.id
        conn = create_connection(database)
        status = checkStatus(conn, msgNickname)
        pEmail = getPlexEmailForDiscordID(conn, str(msgNickname))
        dName = getDiscordNameForDiscordNickname(conn, str(msgNickname))
        conn.close()
        conn = create_connection(database)
        with conn:
            valuesToSend = ("adminremoveplex", str(msgNickname), str(msgMember), str(memID), str(date1),
                            str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        conn.close()
        # change to status 2, status 3. use new pendingInvite method from plexAPI.
        if status == 2 or status == 3:
            dmmsg = ""
            if dName != "DONOT":
                memberR = discord.utils.get(message.guild.members, name=dName)
            if memberR is not None:
                await memberR.remove_roles(invitedRole)
                await memberR.add_roles(removedRole)
                await memberR.create_dm()
                try:
                    await memberR.dm_channel.send(
                        "Hi + " + str(dName) + "! \n\n"
                        + "You have been removed by the administrator!\n"
                        + "Your status has been updated in my DB, "
                        + "and your role in my discord server has been updated to **Removed**\n"
                        + "Try messaging Jomack16 to find out why you were removed"
                    )
                    dmmsg = "successful!"
                except Exception as e:
                    dmmsg = str(e)

            try:
                ACCOUNT.removeFriend(pEmail)
            except Exception as e:
                print("was not a plex account: " + str(e) + " Running no account removal instead")
                ACCOUNT.removeFriendNoAccount(pEmail)
            conn = create_connection(database)
            with conn:
                updateRemovedDateAndStatus(DB_CONNECTION, msgNickname)
            conn.close()
            adminremoveplexmsg = (
                    "Removed the following user from Plex server: \n"
                    + "memberNickname: " + str(msgNickname) + "\n"
                    + "PlexEmailAddress: " + str(pEmail) + "\n"
                    + "DM message was: " + dmmsg
            )
        else:
            adminremoveplexmsg = (
                    "DiscordNickname: \n**" + str(msgNickname)
                    + "** does not have a status of invited."
            )
        await mesChannel.send(adminremoveplexmsg)
    # adminremovecomplete
    # if message.content.startswith(commandPrefix + "adminremovecomplete"):
    #     msgArray = message.content.split()
    #     memNickname = str(msgArray[1])
    #     msgMember = message.author
    #     status = checkStatus(conn, msgNickname)
    #     pEmail = getPlexEmailForDiscordID(DB_CONNECTION, str(msgNickname))
    #     dName = getDiscordNameForDiscordNickname(DB_CONNECTION, str(msgNickname))
    #     with DB_CONNECTION:
    #         valuesToSend = ("adminremovecomplete", str(memNickname), str(msgMember), str(memID), str(date1),
    #                         str(message.content))
    #         updateCommandUsageHistory(DB_CONNECTION, valuesToSend)
    #     if status == 2 or status == 3:
    #         dmmsg = ""
    #         if dName != "DONOT":
    #             memberR = discord.utils.get(message.guild.members, name=dName)
    #         if memberR is not None:
    #             await memberR.remove_roles(invitedRole)
    #             try:
    #                 await memberR.dm_channel.send(
    #                     "Hi + " + str(dName) + "! \n\n"
    #                     + "You have been removed by the administrator!\n"
    #                     + "You have been removed from the Plex server and your information removed from the BotDB."
    #                 )
    #                 dmmsg = "Successful!"
    #             except Exception as e:
    #                 dmmsg = str(e)
    #         try:
    #             ACCOUNT.removeFriend(pEmail)
    #         except Exception as e:
    #             print("was not a plex account: " + str(e) + " Running no account removal instead")
    #             ACCOUNT.removeFriendNoAccount(pEmail)
    #         with conn:
    #             removeFromUserTable(conn, msgNickname)
    #         adminremovecompletemsg = (
    #                 "Removed the following user from Plex server and from the bot DB: \n"
    #                 + "memberNickname: " + str(msgNickname) + "\n"
    #                 + "PlexEmailAddress: " + str(pEmail) + "\n"
    #                 + "DM Message was: " + dmmsg
    #         )
    #     elif status == 0 or status == 1:
    #         dmmsg = ""
    #         if dName != "DONOT":
    #             memberR = discord.utils.get(message.guild.members, name=dName)
    #         if memberR is not None:
    #             await memberR.remove_roles(removedRole)
    #             try:
    #                 await memberR.dm_channel.send(
    #                     "Hi + " + str(dName) + "! \n\n"
    #                     + "You have been removed by the administrator!\n"
    #                     + "Your were already removed from the plex server and your information "
    #                     + "has been removed from the BotDB."
    #                 )
    #                 dmmsg = "successful!"
    #             except Exception as e:
    #                 dmmsg = str(e)
    #         with conn:
    #             removeFromUserTable(conn, msgNickname)
    #         adminremovecompletemsg = (
    #                 "DiscordNickname: **" + str(msgNickname)
    #                 + "** had a status of removed. Just removing from bot DB."
    #                 + "DM message was: " + dmmsg
    #         )
    #     elif status == 4:
    #         dmmsg = ""
    #         if dName != "DONOT":
    #             memberR = discord.utils.get(message.guild.members, name=dName)
    #         if memberR is not None:
    #             await memberR.remove_roles(queuedRole)
    #             try:
    #                 await memberR.dm_channel.send(
    #                     "Hi + " + str(dName) + "! \n\n"
    #                     + "You have been removed by the administrator!\n"
    #                     + "Your were only queued for the plex server and your information "
    #                     + "has been removed from the BotDB."
    #                 )
    #                 dmmsg = "successful!"
    #             except Exception as e:
    #                 dmmsg = str(e)
    #         with conn:
    #             removeFromUserTable(conn, msgNickname)
    #         adminremovecompletemsg = (
    #                 "DiscordNickname: **" + str(msgNickname)
    #                 + "** had a status of queued. Just removing from bot DB."
    #                 + "DM Message was: " + dmmsg
    #         )
    #     else:
    #         with conn:
    #             removeFromUserTable(conn, msgNickname)
    #         adminremovecompletemsg = (
    #                 "DiscordNickname: **" + str(msgNickname)
    #                 + "** does not have a status of invited. Just removing from bot DB."
    #         )
    #     await messageChannel.send(adminremovecompletemsg)
    # admincommands
    if message.content.startswith(commandPrefix + "admincommands") and str(message.author):
        conn = create_connection(database)
        with conn:
            valuesToSend = ("admincommands", str(memNickname), str(memName), str(memID), str(date1),
                            str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        conn.close()
        admincommandsmsg = (
                "Administrator Commands are: \n"
                + "**!admincommands**"
                + " This will send you this list again.\n"
                + "**!adminremovecomplete**"
                + " Give this a DiscordServerNickname to remove someone from Plex and the bot DB\n"
                + "**!adminremoveplex**"
                + " Give this a DiscordServerNickname to remove someone JUST from plex.\n"
                + "**!showmedb**"
                + " Just informational. Accepts discord nickname value to show info from bot DB\n"
                + "**!listplexusers**"
                + " Just informational. Lists the email and username of all users/friends associated to the server\n"
        )
        await mesChannel.send(admincommandsmsg)
    # listplexusers
    # if message.content.startswith(commandPrefix + "listplexusers") and str(message.author):
    #     try:
    #         PLEX_USERS = {user.email: user.username for user in ACCOUNT.users()}
    #     except Exception as e:
    #         print(str(e))
    #     with DB_CONNECTION:
    #         valuesToSend = ("listplexusers", "Jomack16", "Mr.Mustard_#2954", str(date1), str(message.content))
    #         updateCommandUsageHistory(DB_CONNECTION, valuesToSend)
    #     count = 0
    #     for x, y in PLEX_USERS.items():
    #         count += 1
    #         nickname = getDiscordNicknameNameForPlexEmail(conn, x)
    #         # print("email: " + str(x) + " username: " + str(y))
    #         listplexusersmsg1 = ("**" + str(count) + "**. **email**: " + str(x) + " **username**: " + str(y)
    #                              + " **discordNickname**: " + str(nickname))
    #         await messageChannel.send(listplexusersmsg1)


client.run("Njk0MjUzODE0NjIyMTkxNjI2.GubGUG.CV7fplMHbquq27Wfn6gwyYzDAruRvqUoTMrhlU")
