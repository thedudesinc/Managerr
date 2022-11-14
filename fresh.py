import datetime
import sqlite3
from sqlite3 import Error
import discord
from discord.ext.tasks import loop
from requests import Session
from plexapi.server import PlexServer

# region static variable
intents = discord.Intents.all()
intents.members = True
client = discord.Client(intents=intents)
GUILD_ID = 1004464978696343593
MY_GUILD = client.get_guild(GUILD_ID)
database = r"BotDB.db"
DB_CONNECTION = None
botConfigured = None
# endregion


# region Methods
def createDBTables(conn):
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
        "removedRole" TEXT, "commandPrefix" TEXT NOT NULL DEFAULT '!!!', "configured" TEXT DEFAULT 'False'); '''
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
        ("u_PK" INTEGER NOT NULL UNIQUE, "discordID" TEXT NOT NULL UNIQUE, "discordUsername" TEXT NOT NULL, 
        "discordServerNickname"	TEXT, "plexUsername" TEXT DEFAULT 'NEEDSUPDATED', "plexEmailAddress" TEXT, 
        "serverName" TEXT, "dateRemoved" TEXT, "dateInvited" INTEGER, "dateQueued" TEXT, "status" INTEGER, 
        PRIMARY KEY("u_PK" AUTOINCREMENT) ); '''
    cur6 = conn.cursor()
    cur6.execute(sqlU)
    return


def getBotChannelID(conn):
    botChannelID = ""
    cur = conn.cursor()
    cur.execute('select botChannelID from BotConfiguration')
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        botChannelID = str(rowTuple[0])
    return botChannelID


def getBotConfiguredBool(conn):
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
    return botConfiguredBool


def getCommandPrefix(conn):
    commandPrefix = ""
    cur = conn.cursor()
    cur.execute('select commandPrefix from BotConfiguration')
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        commandPrefix = str(rowTuple[0])
    return commandPrefix


def configureBot(conn, values):
    sql = ''' INSERT INTO BotConfiguration(administratorDiscordID,botAdminDiscordRole,botChannelID,queuedRole,
                removedRole,commandPrefix,configured) 
                VALUES(?,?,?,?,?,?,?) '''
    try:
        cur = conn.cursor()
        cur.execute(sql, values)
    except Exception as e:
        print(str(e))
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
    adminDiscordID = ""
    cur = conn.cursor()
    cur.execute('select administratorDiscordID from BotConfiguration')
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        adminDiscordID = str(rowTuple[0])
    return adminDiscordID


def getNewestPlexServer(conn):
    newestPlexServer = ""
    cur = conn.cursor()
    cur.execute('select 1 serverName from PlexServerConfiguration order by psc_PK')
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        newestPlexServer = str(rowTuple[0])
    return newestPlexServer


def getListOfPlexServers(conn):
    cur = conn.cursor()
    cur.execute('select * from PlexServerConfiguration')
    listOfPlexServers = cur.fetchall()
    return listOfPlexServers


def getPlexServerConfigInfoForName(conn, serverName):
    plexServerConfigInfo = []
    cur = conn.cursor()
    cur.execute('select * from PlexServerConfiguration where serverName =(?)', (str(serverName),))
    rows = cur.fetchall()
    if len(rows) == 1:
        plexServerConfigInfo = rows[0]
    return plexServerConfigInfo


def getUserCountForPlexServerName(conn, serverName):
    userCountForPlexServerName = 0
    localSession = Session()
    localSession.verify = False
    if not localSession.verify:
        # Disable the warning that the request is insecure, we know that...
        from urllib3 import disable_warnings
        from urllib3.exceptions import InsecureRequestWarning
        disable_warnings(InsecureRequestWarning)
    plexServerInfo = getPlexServerConfigInfoForName(conn, str(serverName))
    if len(plexServerInfo) == 10:
        Server = PlexServer(baseurl=str(plexServerInfo[2]), token=str(plexServerInfo[3]), session=localSession)
        Account = Server.myPlexAccount()
        PLEX_USERS = {user.email: user.friend for user in Account.users()}
        userCountForPlexServerName = len(PLEX_USERS)
    else:
        print('didnt get back a whole row from plex server config info')
    return userCountForPlexServerName


# region update Bot config methods
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
# endregion


def getBotChannelID(conn):
    botChannelID = ""
    cur = conn.cursor()
    cur.execute('select botChannelID from BotConfiguration')
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        botChannelID = str(rowTuple[0])
    return botChannelID


def getTotalOpenSpots(conn):
    totalOpenSpotsCount = 0
    plexServers = getListOfPlexServers(conn)
    for server in plexServers:
        userCount = getUserCountForPlexServerName(conn, str(server[1]))
        totalOpenSpotsCount += (100 - userCount)
    return totalOpenSpotsCount
# endregion


# region pre-discord client actions
try:
    DB_CONNECTION = sqlite3.connect(database)
except Error as e:
    print(e)
try:
    createDBTables(DB_CONNECTION)
except Error as e:
    print(e)
# endregion

with DB_CONNECTION:
    botConfigured = getBotConfiguredBool(DB_CONNECTION)


# region Client Events
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
        game = discord.Game(name="try " + commandPrefix + "help")
        await client.change_presence(activity=game)
        # endregion
        print("The bot is ready!")
    # endregion


if not botConfigured:
    # region bot NOT configured on_message event
    @client.event
    async def on_message(message):
        MY_GUILD = client.get_guild(GUILD_ID)
        owner = MY_GUILD.owner
        if message.author.bot:
            print("you are a bot!!")
            return
        elif (message.channel.type.name == "private" or message.channel.type.name == "group") and \
                message.content.startswith("!configure"):
            messageArray = message.content.split()
            date1 = datetime.datetime.now()
            if len(messageArray) == 7:
                valuesToSend = (str(messageArray[1]), str(messageArray[2]), str(messageArray[3]),
                                str(messageArray[4]), str(messageArray[5]), str(messageArray[6]), 'True')
                with DB_CONNECTION:
                    configureBot(DB_CONNECTION, valuesToSend)
                    values = ("!configure", str(message.author.nick), str(message.author.name), str(message.author.id),
                              str(date1), str(message.content))
                    recordCommandHistory(DB_CONNECTION, values)
                game = discord.Game(name="try " + str(messageArray[6]) + "help")
                configureMessage = ("Successfully configured. Command prefix is now: **" + messageArray[6] + "**")
                await message.channel.send(configureMessage)
                await client.change_presence(activity=game)
            else:
                configureMessage = ("incorrect number of parameters. Should have adminDiscordID, "
                                    "botAdminDiscordRole, botChannelID, queuedRoleName, removedRoleName, "
                                    "and commandPrefix")
                await message.Channel.send(configureMessage)
        else:
            await message.channel.send("Bot not configured. Please DM me with !configure")
    # endregion
else:
    # region bot configured on_message event
    @client.event
    async def on_message(message):
        # print("I am evaluating from Bot configured on message")
        if message.author.bot:
            print("you are a bot!!")
            return
        else:
            # region on_message not bot variables\
            date1 = datetime.datetime.now()
            with DB_CONNECTION:
                botChannelID = getBotChannelID(DB_CONNECTION)
                commandPrefix = getCommandPrefix(DB_CONNECTION)
                adminDiscordID = getAdminDiscordID(DB_CONNECTION)
            messageArray = message.content.split()
            # endregion
            if message.channel.type.name == "private" or message.channel.type.name == "group":
                # print("got a private message")
                # region create DM to author
                if message.author.dm_channel is None:
                    await message.author.create_dm()
                # endregion
                # region Private Message Actions
                if message.content == commandPrefix + 'ping':
                    with DB_CONNECTION:
                        values = ("private ping", "privateNoNickname", str(message.author.name),
                                  str(message.author.id), str(date1), str(message.content))
                        recordCommandHistory(DB_CONNECTION, values)
                    if message.author.dm_channel is not None:
                        await message.author.dm_channel.send('private pong')
                # region private message admin actions
                if str(message.author.id) == adminDiscordID:
                    if message.content.startswith(commandPrefix + 'updatebotchannelid'):
                        if len(messageArray) == 2:
                            with DB_CONNECTION:
                                values = ("updatebotchannelid", "privateNoNickname", str(message.author.name),
                                          str(message.author.id), str(date1), str(message.content))
                                recordCommandHistory(DB_CONNECTION, values)
                                uValues = (str(messageArray[1]), adminDiscordID)
                                updateBotChannelID(DB_CONNECTION, uValues)
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('Bot Channel ID updated to: '
                                                                     + str(getBotChannelID(DB_CONNECTION)))
                        else:
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('missing ID parameter')
                    if message.content.startswith(commandPrefix + 'updatecommandprefix'):
                        if len(messageArray) == 2:
                            with DB_CONNECTION:
                                values = ("updatecommandprefix", "privateNoNickname", str(message.author.name),
                                          str(message.author.id), str(date1), str(message.content))
                                recordCommandHistory(DB_CONNECTION, values)
                                uValues = (str(messageArray[1]), adminDiscordID)
                                updateCommandPrefix(DB_CONNECTION, uValues)
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('Bot Command Prefix updated to: '
                                                                     + str(getCommandPrefix(DB_CONNECTION)))
                            game = discord.Game(name="try " + str(getCommandPrefix(DB_CONNECTION)) + "help")
                            await client.change_presence(activity=game)
                        else:
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('missing command prefix parameter')
                    if message.content.startswith(commandPrefix + 'initplexserver'):
                        if len(messageArray) == 10:
                            with DB_CONNECTION:
                                values = ("initplexserver", "privateNoNickname", str(message.author.name),
                                          str(message.author.id), str(date1), str(message.content))
                                recordCommandHistory(DB_CONNECTION, values)
                                iValues = (str(messageArray[1]), str(messageArray[2]), str(messageArray[3]),
                                           str(messageArray[4]), str(messageArray[5]), str(messageArray[6]),
                                           str(messageArray[7]), str(messageArray[8]), str(messageArray[9]))
                                recordPlexServerEntry(DB_CONNECTION, iValues)
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('Server Added: **'
                                                                     + str(getNewestPlexServer(DB_CONNECTION)) + '**')
                        else:
                            if message.author.dm_channel is not None:
                                await message.author.dm_channel.send('not enough parameters. Should have: serverName '
                                                                     'serverURL serverToken checksInactivity '
                                                                     'invitedDiscordRole tautulliURL tautulliAPIKey '
                                                                     'inactivityLimit inviteAcceptanceLimit')
                    if message.content.startswith(commandPrefix + 'listplexservers'):
                        with DB_CONNECTION:
                            values = ("listplexservers", "privateNoNickname", str(message.author.name),
                                      str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                            plexServers = getListOfPlexServers(DB_CONNECTION)
                        if message.author.dm_channel is not None:
                            for server in plexServers:
                                userCount = getUserCountForPlexServerName(DB_CONNECTION, str(server[1]))
                                await message.author.dm_channel.send('**ServerName:** ' + str(server[1])
                                                                     + '\n**ServerURL:** ' + str(server[2])
                                                                     + '\n**ServerToken:** ' + str(server[3])
                                                                     + '\n**ChecksInactivity:** ' + str(server[4])
                                                                     + '\n**InvitedDiscordRole:** ' + str(server[5])
                                                                     + '\n**TautulliURL:** ' + str(server[6])
                                                                     + '\n**TautulliAPIKey:** ' + str(server[7])
                                                                     + '\n**InactivityLimit:** ' + str(server[8])
                                                                     + '\n**InviteAcceptanceLimit:** ' + str(server[9])
                                                                     + '\n**UserCount:** ' + str(userCount)
                                                                     + '\n')
                # endregion
                # endregion
            else:
                # print("got a public message")
                # if messages come from public bot channel
                if str(message.channel.id) == str(botChannelID):
                    if message.content == commandPrefix + 'ping':
                        await message.channel.send('bot channel pong!')
                        with DB_CONNECTION:
                            values = ("bot channel ping", str(message.author.nick), str(message.author.name),
                                      str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                else:
                    # region public anywhere actions
                    if message.content == commandPrefix + 'ping':
                        await message.channel.send('public pong!')
                        with DB_CONNECTION:
                            values = ("public ping", str(message.author.nick), str(message.author.name),
                                      str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                    if message.content.startswith(commandPrefix + 'openspots'):
                        with DB_CONNECTION:
                            values = ("openspots", str(message.author.nick), str(message.author.name),
                                      str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                            openspotsCount = getTotalOpenSpots(DB_CONNECTION)
                        await message.reply('There are **' + str(openspotsCount) + '** spots open.',
                                            mention_author=False)
                    # endregion

    # endregion

# endregion

client.run("Njk0MjUzODE0NjIyMTkxNjI2.GubGUG.CV7fplMHbquq27Wfn6gwyYzDAruRvqUoTMrhlU")
