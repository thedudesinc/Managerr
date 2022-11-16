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
        ("u_PK" INTEGER NOT NULL UNIQUE, "discordID" TEXT NOT NULL UNIQUE, "discordUsername" TEXT, 
        "discordServerNickname"	TEXT, "plexUsername" TEXT DEFAULT 'NEEDSUPDATED', 
        "plexEmailAddress" TEXT NOT NULL UNIQUE, "serverName" TEXT, "dateRemoved" TEXT, "dateInvited" TEXT, 
        "dateQueued" TEXT, "status" INTEGER, PRIMARY KEY("u_PK" AUTOINCREMENT)); '''
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


def recordBotActionHistory(conn, values):
    sql = ''' INSERT INTO BotActionHistory(action,dateTime,automaticOrManual) VALUES(?,?,?) '''
    try:
        cur = conn.cursor()
        cur.execute(sql, values)
    except Exception as e:
        print('error from recordBotActionHistory' + str(e))
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
        PLEX_USERS = {user.email: user.username for user in Account.users()}
        pendingInvites = Account.pendingInvites(includeSent=True, includeReceived=False)
        pendingInvitesCount = len(pendingInvites)
        # print('pending invites count: ' + str(pendingInvitesCount))
        userCountForPlexServerName = (len(PLEX_USERS) + pendingInvitesCount)

    else:
        print('didnt get back a whole row from plex server config info')
    return userCountForPlexServerName


def getFirstPlexServerNameWithOpenSpots(conn):
    firstPlexServerNameWithOpenSpots = ""
    plexServers = getListOfPlexServers(conn)
    for server in plexServers:
        userCount = getUserCountForPlexServerName(conn, str(server[1]))
        if userCount < 100:
            firstPlexServerNameWithOpenSpots = str(server[1])
            break
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
            Server = PlexServer(baseurl=str(plexServerInfo[2]), token=str(plexServerInfo[3]), session=localSession)
            Account = Server.myPlexAccount()
            pendingInvites = Account.pendingInvites(includeSent=True, includeReceived=False)
            for invite in pendingInvites:
                if invite.createdAt < datetime.datetime.now() - datetime.timedelta(days=days):
                    Account.cancelInvite(invite)
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
            Server = PlexServer(baseurl=str(plexServerInfo[2]), token=str(plexServerInfo[3]), session=localSession)
            Account = Server.myPlexAccount()
            pendingInvites = Account.pendingInvites(includeSent=True, includeReceived=False)
            for invite in pendingInvites:
                allPendingInvites.append(invite)
        else:
            print("didnt get a whole row from the database for that serverName")
    return allPendingInvites


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


def getStatusForDiscordID(conn, discordID):
    statusForDiscordID = ""
    cur = conn.cursor()
    cur.execute('select status from Users where discordID = (?)', str(discordID))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        statusForDiscordID = str(rowTuple[0])
    return statusForDiscordID


def getEmailForDiscordID(conn, discordID):
    emailForDiscordID = ''
    cur = conn.cursor()
    cur.execute('select plexEmailAddress from Users where discordID = (?)', str(discordID))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        emailForDiscordID = str(rowTuple[0])
    return emailForDiscordID


def getTotalOpenSpots(conn):
    totalOpenSpotsCount = 0
    plexServers = getListOfPlexServers(conn)
    for server in plexServers:
        userCount = getUserCountForPlexServerName(conn, str(server[1]))
        totalOpenSpotsCount += (100 - userCount)
    return totalOpenSpotsCount


def checkDiscordIDExists(conn, discordID):
    discordIDExists = False
    cur = conn.cursor()
    cur.execute('select * from Users where discordID = (?)', (str(discordID),))
    rows = cur.fetchall()
    if len(rows) == 1:
        discordIDExists = True
    else:
        discordIDExists = False
    return discordIDExists


def insertInvitedUser(conn, values):
    sql = ''' INSERT INTO Users(discordID,discordUsername,discordServerNickname,plexUsername,plexEmailAddress,
        serverName,dateInvited,status) VALUES(?,?,?,?,?,?,?,?) '''
    try:
        cur = conn.cursor()
        cur.execute(sql, values)
    except Exception as e:
        print('error from insertInvitedUser' + str(e))
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
    return
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
                if message.content.startswith(commandPrefix + 'inviteme'):
                    if len(messageArray) == 2 and "@" in str(messageArray[1]):
                        with DB_CONNECTION:
                            values = ("inviteme", "fromPrivateDM", str(message.author.name),
                                      str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                            existsAlready = checkDiscordIDExists(DB_CONNECTION, str(message.author.id))
                            if existsAlready:
                                statusForMember = getStatusForDiscordID(DB_CONNECTION, str(message.author.id))
                                emailForMember = getEmailForDiscordID(DB_CONNECTION, str(message.author.id))
                        if not existsAlready:
                            if getTotalOpenSpots(DB_CONNECTION) > 0:
                                serverName = getFirstPlexServerNameWithOpenSpots(DB_CONNECTION)
                                userValues = (str(message.author.id), str(message.author.name), "fromDMNoNickname",
                                              serverName)
                                inviteEmailToPlex(DB_CONNECTION, str(messageArray[1]), userValues)
                                if message.author.dm_channel is not None:
                                    await message.author.dm_channel.send('You have been invited to ' + serverName
                                                                         + '. If you do not see an invite, make sure '
                                                                           'to check spam')
                            else:
                                with DB_CONNECTION:
                                    qValues = (str(message.author.id), str(message.author.name), str(messageArray[1]),
                                               str(date1), '4')
                                    insertQueuedUser(DB_CONNECTION, qValues)
                                await message.author.dm_channel.send('There are currently no open slots, but you have '
                                                                     'been added to the queue. To see your place in the'
                                                                     ' queue, try ' + commandPrefix + 'status')
                        else:
                            if statusForMember == '0' and getTotalOpenSpots(DB_CONNECTION) > 0:
                                serverName = getFirstPlexServerNameWithOpenSpots(DB_CONNECTION)
                                userValues = (str(message.author.id), str(message.author.name), "fromDMNoNickname",
                                              serverName)
                                inviteEmailToPlex(DB_CONNECTION, str(messageArray[1]), userValues)
                                if message.author.dm_channel is not None:
                                    await message.author.dm_channel.send('You were removed for inactivity, however '
                                                                         'there are open spots now, so you have been '
                                                                         're-invited. \n You have been invited to '
                                                                         + serverName
                                                                         + '. If you do not see an invite make sure to '
                                                                           'check spam/junk')
                            elif statusForMember == '0' and getTotalOpenSpots(DB_CONNECTION) == 0:
                                if message.author.dm_channel is not None:
                                    await message.author.dm_channel.send('You were removed for inactivity and there '
                                                                         'are currently no spots open. You have been '
                                                                         'added to the queue for an invite')
                            elif statusForMember == '1':
                                if message.author.dm_channel is not None:
                                    await message.author.dm_channel.send('You were manually removed by an admin. '
                                                                         'Please message the admin with any questions')
                            elif statusForMember == '2' and emailForMember == str(messageArray[1]):
                                if message.author.dm_channel is not None:
                                    await message.author.dm_channel.send('An invite has already been sent for that '
                                                                         'email address, but it has not been accepted '
                                                                         'yet. Please accept the invite and do not '
                                                                         'forget to check your spam if you cannot '
                                                                         'find it.')
                            elif statusForMember == '2' and emailForMember != str(messageArray[1]):
                                if message.author.dm_channel is not None:
                                    await message.author.dm_channel.send('An invite has already been sent for you, '
                                                                         'but for a different email address. \nIf you '
                                                                         'made a typo when you first used the '
                                                                         + commandPrefix
                                                                         + 'inviteme command you can leave the discord '
                                                                           'server to be removed from my memory. '
                                                                           'Then you can DM me the '
                                                                         + commandPrefix
                                                                         + 'inviteme command again with the correct '
                                                                           'info. This will place you at the bottom '
                                                                           'of the invite queue.')
                            elif statusForMember == '3' and emailForMember != str(messageArray[1]):
                                if message.author.dm_channel is not None:
                                    await message.author.dm_channel.send('You have already accepted an invite for a '
                                                                         'different email address. If you are trying '
                                                                         'to get an invite for someone else, please '
                                                                         'have them join the discord server and DM me '
                                                                         'the ' + commandPrefix + 'inviteme command')
                            elif statusForMember == '3' and emailForMember == str(messageArray[1]):
                                if message.author.dm_channel is not None:
                                    await message.author.dm_channel.send('You have already accepted an invite for that '
                                                                         'email address. If you are having an '
                                                                         'problems please message the admin.')
                            elif statusForMember == '4' and emailForMember == str(messageArray[1]):
                                if message.author.dm_channel is not None:
                                    await message.author.dm_channel.send('You have already been queued for an invite '
                                                                         'to that email address. If you want to see '
                                                                         'your place in the queue, try the '
                                                                         + commandPrefix
                                                                         + 'status email@address.com')
                            elif statusForMember == '4' and emailForMember != str(messageArray[1]):
                                if message.author.dm_channel is not None:
                                    await message.author.dm_channel.send('You have already been added to the queue, '
                                                                         'but for a different email address. \nIf this '
                                                                         'is because of a typo when you first used the '
                                                                         'command, leave the discord and rejoin. \nThis'
                                                                         ' will clear you from my memory and you can '
                                                                         'DM me the inviteme command with the correct '
                                                                         'address. \nThis will reset your position in '
                                                                         'the queue. If you are trying to get an '
                                                                         'invite for someone else, have them join '
                                                                         'the discord server and DM me the inviteme '
                                                                         'command. \nIf you are ok with possibly '
                                                                         'waiting, you can message the admin that '
                                                                         'you made a typo, and they can correct it '
                                                                         'without losing your place in the queue.')
                            else:
                                if message.author.dm_channel is not None:
                                    await message.author.dm_channel.send('Something went wrong, and I could not get '
                                                                         'your status from memory.')
                    else:
                        if message.author.dm_channel is not None:
                            await message.author.dm_channel.send('Incorrect command usage. It should look like this: '
                                                                 '**' + commandPrefix + 'inviteme email@address.com**')
                if message.content.startswith(commandPrefix + 'status'):
                    with DB_CONNECTION:
                        memberStatus = getStatusForDiscordID(DB_CONNECTION, str(message.author.id))
                        values = ("status", "fromPrivateDM", str(message.author.name),
                                  str(message.author.id), str(date1), str(message.content))
                        recordCommandHistory(DB_CONNECTION, values)
                    if memberStatus != "":
                        statusForMember = getStatusForDiscordID(DB_CONNECTION, str(message.author.id))
                        if statusForMember == '0':
                            await message.reply('You have been removed for inactivity', mention_author=False)
                        if statusForMember == '1':
                            await message.reply('You have been manually removed by an admin', mention_author=False)
                        if statusForMember == '2':
                            await message.reply('You have been invited but you have not accepted yet',
                                                mention_author=False)
                        if statusForMember == '3':
                            await message.reply('You have already accepted an invite.', mention_author=False)
                        if statusForMember == '4':
                            await message.reply('You have been queued for an invite.', mention_author=False)
                    else:
                        thing = 'you dont have a status.'
                if message.content.startswith(commandPrefix + 'help'):
                    with DB_CONNECTION:
                        values = ("help", "fromPrivateDM", str(message.author.name),
                                  str(message.author.id), str(date1), str(message.content))
                        recordCommandHistory(DB_CONNECTION, values)
                    if message.author.dm_channel is not None:
                        await message.author.dm_channel.send('Hello! I am the Plex Manager Bot for this discord. '
                                                             'For a list of my commands try **'
                                                             + commandPrefix
                                                             + 'listcommands**. Note that the available commands are '
                                                               'context dependent, so whether you are messaging me '
                                                               'directly, or in one of the public channels, '
                                                               'you can always **'
                                                             + commandPrefix
                                                             + 'listcommands** to see what I can do for you.')

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
                    if message.content.startswith(commandPrefix + 'clearpendinginvites'):
                        with DB_CONNECTION:
                            values = ("clearpendinginvites", "privateNoNickname", str(message.author.name),
                                      str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        if len(messageArray) == 2:
                            if message.author.dm_channel is not None:
                                try:
                                    cancelPendingInvitesOverXDays(int(messageArray[1]))
                                    await message.author.dm_channel.send('Pending invites older than **'
                                                                         + str(messageArray[1])
                                                                         + '** have been cleared')
                                except Exception as e:
                                    await message.author.dm_channel.send('exception occurred ' + str(e))
                        else:
                            await message.author.dm_channel.send('missing number of days param, or too many params')
                    if message.content.startswith(commandPrefix + 'listallpendinginvites'):
                        with DB_CONNECTION:
                            values = ("listallpendinginvites", "privateNoNickname", str(message.author.name),
                                      str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        if message.author.dm_channel is not None:
                            try:
                                pendingInviteList = listAllPendingInvites()
                                for invite in pendingInviteList:
                                    await message.author.dm_channel.send('**inviteSent:** ' + str(invite.createdAt)
                                                                         + '\n**email:** ' + invite.email
                                                                         + '\n**isFriend:** ' + str(invite.friend)
                                                                         + '\n**serverShare:** '
                                                                         + str(invite.servers[0])
                                                                         + '\n**username:** ' + invite.username
                                                                         + '\n**friendlyName:** ' + invite.friendlyName)
                            except Exception as e:
                                await message.author.dm_channel.send('exception occurred ' + str(e))
                    if message.content.startswith(commandPrefix + 'listcommands'):
                        with DB_CONNECTION:
                            values = ("listalladmincommands", "privateNoNickname", str(message.author.name),
                                      str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        if message.author.dm_channel is not None:
                            await message.author.dm_channel.send('updatebotchannelid \nupdatecommandprefix '
                                                                 '\ninitplexserver \nlistplexservers '
                                                                 '\nclearpendinginvites \nlistallpendinginvites '
                                                                 '\nlistalladmincommands \nhelp')
                    if message.content.startswith(commandPrefix + 'help'):
                        with DB_CONNECTION:
                            values = ("help", "fromPrivateDM", str(message.author.name),
                                      str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        if message.author.dm_channel is not None:
                            await message.author.dm_channel.send('Hello! I am the Plex Manager Bot for this discord. '
                                                                 'I recognize you as the admin of this server. For a '
                                                                 'list of my commands try **'
                                                                 + commandPrefix
                                                                 + 'listcommands**. Note that the available commands '
                                                                   'are context dependent, so whether you are '
                                                                   'messaging me directly, or in one of the public '
                                                                   'channels, you can always **'
                                                                 + commandPrefix
                                                                 + 'listcommands** to see what I can do for you.')
                # endregion
                # endregion
            else:
                # if messages come from public bot channel
                if str(message.channel.id) == str(botChannelID):
                    # region BotChannel Only Messages
                    if message.content == commandPrefix + 'ping':
                        await message.channel.send('bot channel pong!')
                        with DB_CONNECTION:
                            values = ("bot channel ping", str(message.author.nick), str(message.author.name),
                                      str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                    if message.content.startswith(commandPrefix + 'inviteme') and "@" in str(messageArray[1]):
                        if message.author.dm_channel is None:
                            try:
                                await message.author.create_dm()
                            except Exception as e:
                                print("From bot channel inviteme command logic. some issue with creating DM" + str(e))
                        if message.author.dm_channel is not None:
                            await message.author.dm_channel.send('Please do not use the inviteme command in any public '
                                                                 'channels. DM me (or respond to this) instead.')
                        try:
                            message.delete()
                        except Exception as e:
                            print('exception when deleting message from bot channel inviteme command logic' + str(e))
                        with DB_CONNECTION:
                            baValues = ('found public inviteme command with email address. Deleting for privacy in '
                                        'discord server', str(date1), 'AUTOMATIC')
                            recordBotActionHistory(DB_CONNECTION, baValues)
                    if message.content.startswith(commandPrefix + 'status'):
                        with DB_CONNECTION:
                            memberStatus = getStatusForDiscordID(DB_CONNECTION, str(message.author.id))
                        if memberStatus != "":
                            statusForMember = getStatusForDiscordID(DB_CONNECTION, str(message.author.id))
                            if statusForMember == '0':
                                await message.reply('You have been removed for inactivity', mention_author=False)
                            if statusForMember == '1':
                                await message.reply('You have been manually removed by an admin', mention_author=False)
                            if statusForMember == '2':
                                await message.reply('You have been invited but you have not accepted yet',
                                                    mention_author=False)
                            if statusForMember == '3':
                                await message.reply('You have already accepted an invite.', mention_author=False)
                            if statusForMember == '4':
                                await message.reply('You have been queued for an invite.', mention_author=False)
                        else:
                            thing = 'you dont have a status.'
                    if message.content.startswith(commandPrefix + 'help'):
                        with DB_CONNECTION:
                            values = ("help", "fromBotChannel", str(message.author.name),
                                      str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        await message.channel.send('Hello! I am the Plex Manager Bot for this discord. For a list of '
                                                   'my commands try **'
                                                   + commandPrefix
                                                   + 'listcommands**. Note that the available commands are context '
                                                     'dependent, so whether you are messaging me directly, or in one '
                                                     'of the public channels, you can always **'
                                                   + commandPrefix
                                                   + 'listcommands** to see what I can do for you.')
                    # endregion
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
                    if message.content.startswith(commandPrefix + 'inviteme') and "@" in str(messageArray[1]):
                        if message.author.dm_channel is None:
                            try:
                                await message.author.create_dm()
                            except Exception as e:
                                print("From public inviteme command logic. some issue with creating DM" + str(e))
                        if message.author.dm_channel is not None:
                            await message.author.dm_channel.send('Please do not use the inviteme command in any public '
                                                                 'channels. DM me (or respond to this) instead.')
                        try:
                            message.delete()
                        except Exception as e:
                            print('exception when deleting message from public inviteme command logic' + str(e))
                        with DB_CONNECTION:
                            baValues = ('found public inviteme command with email address. Deleting for privacy in '
                                        'discord server', str(date1), 'AUTOMATIC')
                            recordBotActionHistory(DB_CONNECTION, baValues)
                    if message.content.startswith(commandPrefix + 'status'):
                        with DB_CONNECTION:
                            memberStatus = getStatusForDiscordID(DB_CONNECTION, str(message.author.id))
                        if memberStatus != "":
                            statusForMember = getStatusForDiscordID(DB_CONNECTION, str(message.author.id))
                            if statusForMember == '0':
                                await message.reply('You have been removed for inactivity', mention_author=False)
                            if statusForMember == '1':
                                await message.reply('You have been manually removed by an admin', mention_author=False)
                            if statusForMember == '2':
                                await message.reply('You have been invited but you have not accepted yet',
                                                    mention_author=False)
                            if statusForMember == '3':
                                await message.reply('You have already accepted an invite.', mention_author=False)
                            if statusForMember == '4':
                                await message.reply('You have been queued for an invite.', mention_author=False)
                        else:
                            thing = 'you dont have a status.'
                    if message.content.startswith(commandPrefix + 'help'):
                        with DB_CONNECTION:
                            values = ("help", "fromAnyChannel", str(message.author.name),
                                      str(message.author.id), str(date1), str(message.content))
                            recordCommandHistory(DB_CONNECTION, values)
                        await message.channel.send('Hello! I am the Plex Manager Bot for this discord. For a list of '
                                                   'my commands try **'
                                                   + commandPrefix
                                                   + 'listcommands**. Note that the available commands are context '
                                                     'dependent, so whether you are messaging me directly, or in one '
                                                     'of the public channels, you can always **'
                                                   + commandPrefix
                                                   + 'listcommands** to see what I can do for you.')
                    # endregion

    # endregion

# endregion

client.run("Njk0MjUzODE0NjIyMTkxNjI2.GubGUG.CV7fplMHbquq27Wfn6gwyYzDAruRvqUoTMrhlU")
