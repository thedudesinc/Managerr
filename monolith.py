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
database = './newBotDB.db'
INVITE_SCRIPT_PATH = './InviteUser.py'
DB_CONNECTION = None
SERVER = None
ACCOUNT = None
# -------- FOR YOU TO FILL OUT --------
# MY_GUILD_ID = 1004464978696343593  # your discord server guild ID
# PLEX_URL = 'http://192.168.1.9:32400'  # your plex IP and port number
# PLEX_TOKEN = 'ts6CyycZ2tpExnigUWuT'  # your plex token
# ADMINS = ['Mr.Mustard_#2954']  # your discord name, for using admin commands
# BOT_CHAT = "chat-with-the-bot"  # name of your bot chat channel in your discord
# BOT_CHAT_CHANNEL_ID = '1037558436348567642'  # ID of your bot chat channel
# SPEEDTEST_CHANNEL_ID = '873265398722752522' # ID of the speedtest channel
# CHECK_INACTIVITY = False  # set to True to enable removal of users based on inactivity
# -------- If you set CHECK_INACTIVITY to True, update line 522, 523, 526, 528 --------
# Your discord role names, must have all 3 filled out.
# IRname = "Invited"
# QRname = "Queued"
# RRname = "Removed"

# ********static actions********
# disables SSL warnings
if not SESSION.verify:
    # Disable the warning that the request is insecure, we know that...
    from urllib3 import disable_warnings
    from urllib3.exceptions import InsecureRequestWarning
    disable_warnings(InsecureRequestWarning)

# connects to the database
try:
    DB_CONNECTION = sqlite3.connect(database)
except Error as e:
    print(e)

# ********static actions********




# ----defining db functions below

# initialize Plex Server # info
def initializePlexServer(NAME, URL, TOKEN, CHECKS_INACTIVITY, INVITED_DISCORD_ROLE, TAUTULLI_URL, 
TAUTULLI_API_KEY, INACTIVITY_LIMIT, INVITE_ACCEPTANCE_LIMIT):
    try:
        SERVER = PlexServer(baseurl=URL, token=TOKEN, session=SESSION)
        ACCOUNT = SERVER.myPlexAccount()
    except Exception as e:
        print(str(e))

    dateTime = datetime.datetime.now()
    valuesToSend = None
    if (CHECKS_INACTIVITY == "YES"):
        valuesToSend = (NAME, URL, TOKEN, CHECKS_INACTIVITY, INVITED_DISCORD_ROLE, 
        TAUTULLI_URL, TAUTULLI_API_KEY, INACTIVITY_LIMIT, INVITE_ACCEPTANCE_LIMIT)
    else:
        valuesToSend = (NAME, URL, TOKEN, CHECKS_INACTIVITY)

    initializePlexServerInDB(valuesToSend)
    updateBotActionHistory("initialized Plex Server: " + NAME, dateTime, "MANUAL")

    return


def initializePlexServerInDB(values):
    dateTime = datetime.datetime.now()
    if (values.CHECKS_INACTIVITT)
    sql = ''' INSERT INTO CommandHistory(CommandUsed,DiscordServerNickname,DiscordUsername,DateTime,ValuesSent) 
    VALUES(?,?,?,?,?) '''
    cur = DB_CONNECTION.cursor()
    cur.execute(sql, values)
    return


# -----from repeated actions script
def getBotPlexUsers(conn1):
    rDict = {}
    cur1 = conn1.cursor()
    cur1.execute('select PlexEmailAddress, Status from UserTable')
    BotPlexUsers = cur1.fetchall()
    for x in BotPlexUsers:
        # .update function to append the values to the dictionary
        rDict.update({str(x[0]).lower(): x[1]})
    return rDict


def updateStatusForPlexEmailAddress(conn1, emailAddress, statusUpdate):
    date1 = datetime.datetime.now()
    cur = conn1.cursor()
    if statusUpdate == 4:
        cur.execute('UPDATE UserTable set Status =4, DateQueued =(?) WHERE PlexEmailAddress like(?)',
                    (str(date1), str(emailAddress)))
    elif statusUpdate == 2:
        cur.execute('UPDATE UserTable set Status =2, DateInvited =(?) WHERE PlexEmailAddress like(?)',
                    (str(date1), str(emailAddress)))
    elif statusUpdate == 0:
        cur.execute('UPDATE UserTable set Status =0, DateRemoved =(?) WHERE PlexEmailAddress like(?)',
                    (str(date1), str(emailAddress)))
    else:
        cur.execute('UPDATE UserTable set Status =(?) WHERE PlexEmailAddress like(?)',
                    (int(statusUpdate), str(emailAddress)))

    return


def getCurrentStatus(conn1, plexEmailAddress):
    status = 5
    cur = conn1.cursor()
    cur.execute('select Status from UserTable where PlexEmailAddress like(?)', (str(plexEmailAddress),))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        status = rowTuple[0]
    if len(rows) == 0:
        status = 5
    return status


def getCurrentPlexUsername(conn1, plexEmailAddress):
    cur = conn1.cursor()
    cur.execute('select PlexUsername from UserTable where PlexEmailAddress like(?)', (plexEmailAddress,))
    rows = cur.fetchone()
    rowTuple = rows[0]
    userName = str(rowTuple)
    return userName


def updateUsernameForPlexEmailAddress(conn1, pEmailAddress, pUsername):
    cur = conn1.cursor()
    cur.execute('UPDATE UserTable set PlexUsername =(?) WHERE PlexEmailAddress like(?)', (pUsername, pEmailAddress))
    return


def getDateInvited(conn1, plexEmailAddress):
    dateInvited = ""
    cur = conn1.cursor()
    cur.execute('select DateInvited from UserTable where PlexEmailAddress like(?)', (str(plexEmailAddress),))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        dateInvited = rowTuple[0]
    if len(rows) == 0:
        dateInvited = ""
    return dateInvited


def getDateInvitedByUsername(conn1, plexUsername):
    dateInvited = ""
    cur = conn1.cursor()
    cur.execute('select DateInvited from UserTable where PlexUsername like(?)', (str(plexUsername),))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        dateInvited = rowTuple[0]
    if len(rows) == 0:
        dateInvited = ""
    return dateInvited


def getBotPlexUsersQueued(conn1):
    rDict = {}
    cur1 = conn1.cursor()
    cur1.execute('select PlexEmailAddress, Status from UserTable where Status = 4 order by DateQueued')
    BotPlexUsers = cur1.fetchall()
    for x in BotPlexUsers:
        # .update function to append the values to the dictionary
        rDict.update({str(x[0]).lower(): x[1]})
    return rDict


def getBotPlexUsersNoUsername(conn1):
    usrnme = 'ISBLANKJEJ'
    rDict = {}
    cur1 = conn1.cursor()
    cur1.execute('select PlexEmailAddress, PlexUsername from UserTable where PlexUsername =(?)', (usrnme,))
    BotPlexUsers = cur1.fetchall()
    for x in BotPlexUsers:
        # .update function to append the values to the dictionary
        rDict.update({str(x[0]).lower(): x[1]})
    return rDict


def updateCommandUsageHistory(conn1, commandHistoryAdd):
    sql = ''' INSERT INTO CommandHistory(CommandUsed,DiscordServerNickname,DiscordUsername,DateTime,ValuesSent) 
    VALUES(?,?,?,?,?) '''
    cur = conn1.cursor()
    cur.execute(sql, commandHistoryAdd)
    return


def updateBotActionHistory(values):
    sql = ''' INSERT INTO BotActionHistory(action,dateTime,automaticOrManual) 
    VALUES(?,?,?) '''
    cur = DB_CONNECTION.cursor()
    cur.execute(sql, values)
    return


def checkDiscordNicknameExists(conn1, discordNickname):
    cur = conn1.cursor()
    cur.execute('select 1 from UserTable where DiscordServerNickname like(?)', (discordNickname,))
    rows = cur.fetchall()
    if len(rows) >= 1:
        exists = True
    else:
        exists = False
    return exists


def checkStatus(conn1, discordNickname):
    cur = conn1.cursor()
    cur.execute('select Status from UserTable where DiscordServerNickname like(?)', (discordNickname,))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        status = rowTuple[0]
    else:
        status = 5
    return status


def getInactiveRemovalDate(conn1, discordNickname):
    cur = conn1.cursor()
    cur.execute('select DateRemoved from UserTable where DiscordServerNickname like(?)', (discordNickname,))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        removalDate1 = rowTuple[0]
    return removalDate1


def updateQueuedDateAndStatus(conn1, discordNickname, dateTime, newStatus):
    cur = conn1.cursor()
    cur.execute('UPDATE UserTable set DateQueued =(?), Status =(?) WHERE DiscordServerNickname like(?)',
                (dateTime, newStatus, discordNickname))
    return


def updateRemovedDateAndStatus(conn1, discordNickname):
    date1 = datetime.datetime.now()
    newstatus = 1
    cur = conn1.cursor()
    cur.execute('UPDATE UserTable set DateRemoved =(?), Status =(?) WHERE DiscordServerNickname like(?)',
                (date1, newstatus, discordNickname))
    return


def getCurrentQueueDate(conn1, discordNickname):
    cur = conn1.cursor()
    cur.execute('select DateQueued from UserTable where DiscordServerNickname like(?)', (discordNickname,))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        currentQueueDate = rowTuple[0]
    return currentQueueDate


def getNumberQueuedAhead(conn1, dateQueued):
    blankString = ''
    cur = conn1.cursor()
    cur.execute('select count() from UserTable where Status = 4 and DateQueued <(?) and DateQueued !=(?)',
                (dateQueued, blankString,))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        numberAhead = rowTuple[0]
    if len(rows) < 1:
        numberAhead = 0
    return numberAhead


def checkPlexEmailExists(conn1, plexEmailToCheck):
    exists = False
    cur = conn1.cursor()
    cur.execute('select 1 from UserTable where PlexEmailAddress like(?)', (plexEmailToCheck,))
    rows = cur.fetchall()
    if len(rows) >= 1:
        exists = True
    return exists


def getInvitedStatusCount(conn1):
    cur = conn1.cursor()
    cur.execute('select count() from UserTable where Status = 2 or Status = 3')
    rows = cur.fetchall()
    rowTuple = rows[0]
    invitedStatusCount = rowTuple[0]
    return invitedStatusCount


def getOpenSlotsCount(conn1):
    openSlotsCount = 0
    try:
        PLEX_USERS = {user.email: user.friend for user in ACCOUNT.users()}
        plexUserCount = len(PLEX_USERS)
        if plexUserCount < 100:
            openSlotsCount = 100 - plexUserCount
    except Exception as e:
        print(str(e))
    return openSlotsCount


def getPendingInvitesCount(conn1):
    cur = conn1.cursor()
    cur.execute('select count() from UserTable where Status = 4')
    rows = cur.fetchall()
    rowTuple = rows[0]
    queuedStatusCount = rowTuple[0]
    return queuedStatusCount


def addInvitedUser(conn1, addInvitedUserValues):
    sql = ''' INSERT INTO UserTable(DiscordUsername,DiscordServerNickname,PlexEmailAddress,Status,DateInvited)
                  VALUES(?,?,?,2,?) '''
    cur = conn1.cursor()
    cur.execute(sql, addInvitedUserValues)
    return


def addQueuedUser(conn1, addQueuedUserValues):
    sql = ''' INSERT INTO UserTable(DiscordUsername,DiscordServerNickname,PlexEmailAddress,Status,DateQueued)
                      VALUES(?,?,?,4,?) '''
    cur = conn1.cursor()
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


def getPlexEmailForDiscordNickname(conn1, dNicknameToCheck):
    cur = conn1.cursor()
    cur.execute('select PlexEmailAddress from UserTable where DiscordServerNickname like(?)', (dNicknameToCheck,))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        discordNickname = rowTuple[0]
    if len(rows) < 1:
        discordNickname = "DONOT"
    return discordNickname


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


def getDiscordNameForPlexEmail(conn1, pEmail):
    cur = conn1.cursor()
    cur.execute('select DiscordUsername from UserTable where PlexEmailAddress like(?)', (pEmail,))
    rows = cur.fetchall()
    if len(rows) == 1:
        rowTuple = rows[0]
        discordUsername = rowTuple[0]
    if len(rows) < 1:
        discordUsername = "DONOT"
    return discordUsername


def getDiscordNicknameNameForPlexEmail(conn1, pEmail):
    cur = conn1.cursor()
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


# -----conn variable created here, so I didnt have to move the db def above the other variables
conn = create_connection(database)


@client.event
async def on_ready():
    print("The bot is ready!")
    game = discord.Game(name="try !help")
    MY_GUILD1 = client.get_guild(MY_GUILD_ID)
    conn1 = create_connection(database)
    invitedRole = discord.utils.get(MY_GUILD1.roles, name=IRname)
    queuedRole = discord.utils.get(MY_GUILD1.roles, name=QRname)
    removedRole = discord.utils.get(MY_GUILD1.roles, name=RRname)

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
        BOT_PLEX_USERS = getBotPlexUsers(conn1)
        BOT_PLEX_USERS_QUEUED = getBotPlexUsersQueued(conn1)
        BOT_PLEX_USERS_NO_USERNAME = getBotPlexUsersNoUsername(conn1)
        # UPDATE STATUS FROM PLEX VALUES
        if (ifIsTrue):
            for xEmail, xIsFriend in PLEX_USERS.items():
                date1 = datetime.datetime.now()
                # if isFriend is false, then they havent accepted the invite yet.
                # if they are in this list at all, they have obviously been invited.
                # there will be no manual invites as a matter of policy,
                # so they will be in botDB, if they are in this list
                statusInBotDB = getCurrentStatus(conn1, str(xEmail))
                if xIsFriend and statusInBotDB != 3:
                    print("Email: " + str(xEmail) + " is friend and status in botDB is not 3. Update to 3")
                    with conn1:
                        updateStatusForPlexEmailAddress(conn1, str(xEmail), 3)
                        valuesToSend = (
                            "RepeatedActions-StatusUpdate", "PlexInviteBot", "PlexInviteBot", str(date1),
                            "email: " + str(xEmail) + " update status to 3, because they have accepted the invite.")
                        updateCommandUsageHistory(conn1, valuesToSend)
                # if username from plex is not blank, but the status is 2, then they must have accepted the invite
                # and need updated to status of 3
                elif not xIsFriend and statusInBotDB != 2 and statusInBotDB != 5:
                    print("Email: " + str(xEmail) + " is NOT friend and status in botDB is not 2. Update to 2")
                    with conn1:
                        updateStatusForPlexEmailAddress(conn1, str(xEmail), 2)
                        valuesToSend = (
                            "RepeatedActions-StatusUpdate", "PlexInviteBot", "PlexInviteBot", str(date1),
                            "email: " + str(xEmail)
                            + " They have an invite, but they havent accepted yet, make sure status is 2")
                        updateCommandUsageHistory(conn1, valuesToSend)
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
                    with conn1:
                        valuesToSend = (
                            "RepeatedActions-StatusUpdate", "PlexInviteBot", "PlexInviteBot", str(date1),
                            "email: " + str(xEmail)
                            + " was not found in the botDB. Likely a typo email. Remove from plex.")
                        updateCommandUsageHistory(conn1, valuesToSend)

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
                    dName = getDiscordNameForPlexEmail(conn1, str(xEmail))
                    dmmsg = ""
                    if dName != "DONOT":
                        memberR = discord.utils.get(MY_GUILD1.members, name=dName)
                        if memberR is not None:
                            await memberR.remove_roles(invitedRole)
                            await memberR.add_roles(removedRole)
                            await memberR.create_dm()
                            try:
                                await memberR.dm_channel.send(
                                    "Hi + " + str(dName) + "! \n\n"
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
                    with conn1:
                        updateStatusForPlexEmailAddress(conn1, str(xEmail), 0)
                        valuesToSend = (
                            "RepeatedActions-StatusUpdate", "PlexInviteBot", "PlexInviteBot", str(date1),
                            "email: " + str(xEmail) + "Self removed from plex server. Update botDB status to 0, "
                            + "and discord role to Removed. " + "DM Successful/Exception: " + str(dmmsg))
                        updateCommandUsageHistory(conn1, valuesToSend)

        # REMOVE USERS WHO DONT ACCEPT THE INVITE for more than 3 days, and update status to 0
        # DM those discord users that their status has been changed.
        todayMinus3 = (datetime.datetime.now() - datetime.timedelta(days=3))
        if ifIsTrue:
            for xEmail, xIsFriend in PLEX_USERS.items():
                date1 = datetime.datetime.now()
                statusInBotDB = getCurrentStatus(conn1, xEmail)
                invitedDate = getDateInvited(conn1, xEmail)
                if statusInBotDB == 2 and invitedDate < str(todayMinus3):
                    dName = getDiscordNameForPlexEmail(conn1, str(xEmail))
                    dmmsg = ""
                    if dName != "DONOT":
                        memberR = discord.utils.get(MY_GUILD1.members, name=dName)
                        if memberR is not None:
                            await memberR.remove_roles(invitedRole)
                            await memberR.add_roles(removedRole)
                            await memberR.create_dm()
                            try:
                                await memberR.dm_channel.send(
                                    "Hi + " + str(dName) + "! \n\n"
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
                    with conn1:
                        updateStatusForPlexEmailAddress(conn1, str(xEmail), 0)
                        valuesToSend = ("RepeatedActions-Removed", "PlexInviteBot", "PlexInviteBot", str(date1),
                                        "email: " + str(xEmail) + "Removed for not accepting the invite within 3 days."
                                        + " DM message was: " + dmmsg)
                        updateCommandUsageHistory(conn1, valuesToSend)
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
                openSlots = getOpenSlotsCount(conn1)
                if openSlots > 0:
                    pyExecStr = 'python ' + INVITE_SCRIPT_PATH + ' --user ' + xEmail + ' --allLibraries'
                    os.system(pyExecStr)
                    dName = getDiscordNameForPlexEmail(conn1, str(xEmail))
                    dmmsg = ""
                    if dName != "DONOT":
                        memberR = discord.utils.get(MY_GUILD1.members, name=dName)
                    if memberR is not None:
                        await memberR.remove_roles(queuedRole)
                        await memberR.add_roles(invitedRole)
                        await memberR.create_dm()
                        try:
                            await memberR.dm_channel.send(
                                "Hi + " + str(dName) + "! \n\n"
                                + "You were next in line and have been invited to the Plex server!\n"
                                + "Your status has been updated in my DB, "
                                + "and your role in my discord server has been updated to **Invited**\n"
                            )
                            dmmsg = "successful!"
                        except Exception as e:
                            dmmsg = str(e)
                    with conn1:
                        updateStatusForPlexEmailAddress(conn1, str(xEmail), 2)
                        valuesToSend = ("RepeatedActions-AutoInvite", "PlexInviteBot", "PlexInviteBot", str(date1),
                                        str(pyExecStr) + " -- DM Successful/Exception: " + str(dmmsg))
                        updateCommandUsageHistory(conn1, valuesToSend)
                    print("------found queued user that gets invited")

        # update plex username value in botDB if there is one from plex.
        if len(BOT_PLEX_USERS_NO_USERNAME) > 0 and ifIsTrue:
            for xEmail, xUsername in BOT_PLEX_USERS_NO_USERNAME.items():
                if xEmail in PLEX_USERS_USERNAME:
                    xUsernamePlex = PLEX_USERS_USERNAME[xEmail]
                    with conn1:
                        updateUsernameForPlexEmailAddress(conn1, xEmail.lower(), xUsernamePlex.lower())
                        valuesToSend = ("RepeatedActions-UsernameUpdate", "PlexInviteBot", "PlexInviteBot", str(date1),
                                        "user name for email: " + str(xEmail) + " was updated from ISBLANKJEJ to "
                                        + str(xUsernamePlex))
                        updateCommandUsageHistory(conn1, valuesToSend)

    @loop(hours=48)
    async def every_12h_jobs():
        if CHECK_INACTIVITY:
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
                    GET = SESSION.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=PARAMS).json()['response']['data']['data']
                    for user in GET:
                        if user['user_id'] in IGNORED_UIDS:
                            print(str(user['user_id']))
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
                invitedDate = getDateInvitedByUsername(conn1, USERNAME)
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
                        dName = getDiscordNameForPlexEmail(conn1, str(PLEX_USERS_EMAIL[UID]))
                        print("discord name: " + str(dName) + " obtained from email address:" + str(PLEX_USERS_EMAIL[UID]))
                    else:
                        if ifIsTrue1 and ifIsTrue2:
                            try:
                                ACCOUNT.removeFriend(PLEX_USERS[UID])
                            except Exception as e:
                                print("was not a plex account: " + str(e) + " Running no account removal instead")
                                ACCOUNT.removeFriendNoAccount(PLEX_USERS_EMAIL[UID])
                            dName = getDiscordNameForPlexEmail(conn1, str(PLEX_USERS_EMAIL[UID]))
                            dmmsg = ""
                            if dName != "DONOT":
                                memberR = discord.utils.get(MY_GUILD1.members, name=dName)
                                if memberR is not None:
                                    await memberR.remove_roles(invitedRole)
                                    await memberR.add_roles(removedRole)
                                    await memberR.create_dm()
                                    try:
                                        await memberR.dm_channel.send(
                                            "Hi + " + str(dName) + "! \n\n"
                                            + "You were removed for inactivity!\n"
                                            + "Your status has been updated in my DB, "
                                            + "and you role in my discord server has been updated to **Removed**\n"
                                            + "If you would like to be added back to the server try "
                                            + "responding to me with **!invite**"
                                        )
                                        dmmsg = "successful!"
                                    except Exception as e:
                                        dmmsg = str(e)
                            with conn1:
                                updateStatusForPlexEmailAddress(conn1, str(PLEX_USERS_EMAIL[UID]), 0)
                                valuesToSend = (
                                    "InactivityRemoval", "PlexInviteBot", "PlexInviteBot", str(datetime.datetime.now()),
                                    "email: " + str(PLEX_USERS_EMAIL[UID])
                                    + "removed from plex server for inactivity. "
                                    + "Update botDB status to 0, and discord role to Removed. "
                                    + "DM message success/exception: " + str(dmmsg))
                                updateCommandUsageHistory(conn1, valuesToSend)
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

    every_10m_jobs.start()
    every_12h_jobs.start()

    await client.change_presence(activity=game)


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
            + "<#" + BOT_CHAT_CHANNEL_ID + "> channel. You can interact with me there for Plex server invites.\n"
            + "Try replying to me with **!help**, **!rules**, or **!invite** for more information."
        )
        await member.edit(nick=newNick)
        dmSuccess = "DM SUCCESSFUL"
    except Exception as e:
        dmSuccess = "DM UNSUCCESSFUL"
    with conn:
        valuesToSend = ("DiscordJoin", str(member), str(newNick), str(date1), "This user: " + str(member)
                        + " joined the discord server. I updated their nickname to: " + str(newNick)
                        + " and DM'd them with info. " + dmSuccess)
        updateCommandUsageHistory(conn, valuesToSend)


@client.event
async def on_member_remove(member):
    # print(str(member) + " left!")
    # TODO add api call to Tautulli to remove as well
    memberNickname = member.nick
    memberName = member.name
    date1 = datetime.datetime.now()
    statusM = checkStatus(conn, memberNickname)
    pEmail = getPlexEmailForDiscordNickname(conn, str(memberNickname))
    emailExists = checkPlexEmailExists(conn, pEmail)
    if statusM == 2 or statusM == 3 and emailExists:
        try:
            removeFromUserTable(conn, str(memberNickname))
        except Exception as e:
            print("Something went wrong: Error: {}.".format(e))
        try:
            ACCOUNT.removeFriend(pEmail)
        except Exception as e:
            print("was not a plex account: " + str(e) + " Running no account removal instead")
            ACCOUNT.removeFriendNoAccount(pEmail)
    elif emailExists:
        try:
            removeFromUserTable(conn, str(memberNickname))
        except Exception as e:
            print("Something went wrong: Error: {}.".format(e))
    with conn:
        valuesToSend = ("LeftDiscordServer", str(memberNickname), str(memberName), str(date1),
                        "memberName: " + str(memberName)
                        + " They left discord server so they were uninvited from plex and removed from database.")
        updateCommandUsageHistory(conn, valuesToSend)


# ---------once a message is received
@client.event
async def on_message(message):
    # will return either a member or user object
    messageAuthor = message.author
    messageChannel = message.channel
    # manually set here, in case the message doesnt come from bot chat.
    memberNickname = "FromPrivateChannel"
    channelType = messageChannel.type
    channelTypeName = channelType.name
    memberName = messageAuthor.name
    if str(messageChannel) == BOT_CHAT:
        messageGuild = message.guild
        invitedRole = discord.utils.get(messageGuild.roles, name="Invited")
        queuedRole = discord.utils.get(messageGuild.roles, name="Queued")
        removedRole = discord.utils.get(messageGuild.roles, name="Removed")
        memberNickname = messageAuthor.nick
    date1 = datetime.datetime.now()

    # if the bot somehow messages itself, dont do anything
    if message.author == client.user:
        return
    # if message channel type is private or from the wrong text channel
    if (str(messageChannel) != BOT_CHAT) and (message.content.startswith("!inviteme") or
                                              message.content.startswith("!status")):
        with conn:
            valuesToSend = ("WrongSource", str(memberNickname), str(memberName), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        await messageChannel.send("Cannot accept that command from here. Try in <#" + BOT_CHAT_CHANNEL_ID + ">")
    # botchat channel only commands
    if str(messageChannel) == BOT_CHAT:
        # !inviteme
        if message.content.find("@") == -1 and message.content.startswith("!inviteme"):
            with conn:
                valuesToSend = ("inviteme", str(memberNickname), str(memberName), str(date1), str(message.content))
                updateCommandUsageHistory(conn, valuesToSend)
            channel = message.channel
            await channel.send("---INVALID EMAIL ADDRESS--- \nShould look like **!inviteme email@address.com**")
        # !inviteme
        if message.content.find("@") != -1 and message.content.startswith("!inviteme"):
            with conn:
                valuesToSend = ("inviteme", str(memberNickname), str(memberName), str(date1), str(message.content))
                updateCommandUsageHistory(conn, valuesToSend)
            messageArray = message.content.split()
            if "@" in str(messageArray[1]):
                messageEmail = str(messageArray[1]).lower()
            else:
                messageEmail = "DONOT"
            discordNicknameExists = checkDiscordNicknameExists(conn, str(messageAuthor.nick).lower())
            if discordNicknameExists and messageEmail != "DONOT":
                status = checkStatus(conn, str(messageAuthor.nick).lower())
                # status 0 = removed for inactivity
                if status == 0:
                    inactiveRemovalDate = getInactiveRemovalDate(conn, memberNickname)
                    with conn:
                        updateQueuedDateAndStatus(conn, str(memberNickname), str(date1), 4)
                    newQueueDate = getCurrentQueueDate(conn, memberNickname)
                    numberAheadOfYou = getNumberQueuedAhead(conn, newQueueDate)
                    invitememsg = (
                            str(message.author) + ", you were removed on this date: " + str(inactiveRemovalDate) + "\n"
                            + "You have been requeued. There are **" + str(numberAheadOfYou)
                            + "** people queued ahead of you."
                    )
                    memberR = discord.utils.get(messageGuild.members, name=memberName)
                    await memberR.remove_roles(removedRole)
                    await memberR.add_roles(queuedRole)
                # status 1 = removed manually by admin
                elif status == 1:
                    invitememsg = (str(message.author) + ", you were removed manually by an admin. Try !help")
                # status 2 = invited but not yet accepted
                elif status == 2:
                    presentEmail = getPlexEmailForDiscordNickname(conn, str(messageAuthor.nick))
                    invitememsg = (
                            str(memberNickname) + ", you have already been invited using this email address: **"
                            + str(presentEmail) + "** but you haven't accepted the invite yet.\n"
                            + "Check your inbox (including spam) for the invite email."
                    )
                # status 3 = invited and accepted already
                elif status == 3:
                    presentEmail = getPlexEmailForDiscordNickname(conn, str(messageAuthor.nick))
                    invitememsg = (
                            str(memberNickname)
                            + ", an invite has already been sent, and you have accepted it using this email address: "
                            + str(presentEmail)
                    )
                # status 4 = queued for an invite
                elif status == 4:
                    presentEmail = getPlexEmailForDiscordNickname(conn, str(messageAuthor.nick))
                    yourQueueDate = getCurrentQueueDate(conn, memberNickname)
                    numberAheadOfYou = getNumberQueuedAhead(conn, yourQueueDate)
                    invitememsg = (
                            str(memberNickname)
                            + ", you have been queued for an invite to be sent to this email address: "
                            + presentEmail + "\n You were queued at this time: "
                            + str(yourQueueDate) + " and there are: **"
                            + str(numberAheadOfYou)
                            + "** people queued ahead of you."
                    )
                elif status == 5:
                    invitememsg = "Something went wrong, the status came back as 5"
            if not discordNicknameExists and messageEmail != "DONOT":
                plexEmailExists = checkPlexEmailExists(conn, messageEmail)
                openSlots = getOpenSlotsCount(conn)
                numberAheadOfYou = getNumberQueuedAhead(conn, str(date1))
                if not plexEmailExists and openSlots > 0 and numberAheadOfYou == 0:
                    pyExecStr = 'python ' + INVITE_SCRIPT_PATH + ' --user ' + messageEmail + ' --allLibraries'
                    os.system(pyExecStr)
                    with conn:
                        valuesToSend = (str(memberName), str(memberNickname), str(messageEmail), str(date1))
                        addInvitedUser(conn, valuesToSend)
                    invitememsg = ("An invite has been sent to this email address: " + messageEmail)
                    memberR = discord.utils.get(messageGuild.members, name=memberName)
                    await memberR.add_roles(invitedRole)
                if not plexEmailExists and openSlots == 0:
                    with conn:
                        valuesToSend = (str(memberName), str(memberNickname), str(messageEmail), str(date1))
                        addQueuedUser(conn, valuesToSend)
                    yourQueueDate = getCurrentQueueDate(conn, memberNickname)
                    invitememsg = (
                            str(messageAuthor)
                            + ", there were no open slots, but you have been added to the queue.\n"
                            + "There are **" + str(numberAheadOfYou) 
                            + "** people in front of you. \nYour queued date is: **" + str(yourQueueDate) + "**"
                    )
                    memberR = discord.utils.get(messageGuild.members, name=memberName)
                    await memberR.add_roles(queuedRole)
                if not plexEmailExists and openSlots > 0 and numberAheadOfYou != 0:
                    with conn:
                        valuesToSend = (str(memberName), str(memberNickname), str(messageEmail), str(date1))
                        addQueuedUser(conn, valuesToSend)
                    yourQueueDate = getCurrentQueueDate(conn, memberNickname)
                    invitememsg = (
                            str(memberNickname)
                            + ", there were open slots, but there are others ahead of you in queue."
                            + " You have been added to the  queue.\n There are **" + str(numberAheadOfYou)
                            + "** people in front of you."
                            + " Your queued date is: **" + str(yourQueueDate) + "**"
                    )
                    memberR = discord.utils.get(messageGuild.members, name=memberName)
                    await memberR.add_roles(queuedRole)
                if plexEmailExists:
                    invitememsg = (
                            "The email address: " + messageEmail
                            + " has already been used to request an invite. Try !status")
            if messageEmail == "DONOT":
                invitememsg = (
                        "Something went wrong. This is what you sent me: " + str(message.content)
                        + "\n Should look like this **!inviteme email@address.com**"
                )
            await messageChannel.send(invitememsg)
        # !status
        if message.content.find("@") == -1 and message.content.startswith("!status"):
            with conn:
                valuesToSend = ("status", str(memberNickname), str(memberName), str(date1), str(message.content))
                updateCommandUsageHistory(conn, valuesToSend)
            channel = message.channel
            await channel.send("---INVALID EMAIL ADDRESS--- Message should look like: **!status email@address.com**")
        # !status
        if message.content.find("@") != -1 and message.content.startswith("!status"):
            with conn:
                valuesToSend = ("status", str(memberNickname), str(memberName), str(date1), str(message.content))
                updateCommandUsageHistory(conn, valuesToSend)
            # split the array at spaces by default
            messageArray = message.content.split()
            # if the second element in the array contains the @ symbol
            # first element should
            if "@" in str(messageArray[1]):
                messageEmail = str(messageArray[1]).lower()
            else:
                messageEmail = "DONOT"

            plexEmailExists = checkPlexEmailExists(conn, str(messageEmail))
            if plexEmailExists:
                nicknameForPlexEmail = getNicknameForPlexEmail(conn, str(messageEmail))
            else:
                nicknameForPlexEmail = "DONOT"
            if plexEmailExists and memberNickname != nicknameForPlexEmail and messageEmail != "DONOT":
                statusmsg = (
                        "Found the email, **" + str(messageEmail) + "** but it is tied to a discord user **"
                        + str(nicknameForPlexEmail) + "**, which is not you, **" + str(memberNickname)
                        + "**. \n Will not disclose the status."
                )
            elif plexEmailExists and memberNickname == nicknameForPlexEmail and messageEmail != "DONOT":
                status = checkStatus(conn, memberNickname)
                # status 0 = removed for inactivity
                if status == 0:
                    inactiveRemovalDate = getInactiveRemovalDate(conn, memberNickname)
                    statusmsg = (
                            str(memberNickname) + ", you were removed on this date: **"
                            + str(inactiveRemovalDate)
                            + "** You can requeue yourself with the **!inviteme** command."
                    )
                # status 1 = removed manually by admin
                if status == 1:
                    statusmsg = (str(memberNickname) + ", you were removed manually by an admin. Try !help")
                # status 2 = invited but not yet accepted
                if status == 2:
                    presentEmail = getPlexEmailForDiscordNickname(conn, str(messageAuthor.nick))
                    statusmsg = (
                            str(memberNickname) + ", you have already been invited using this email address: **"
                            + str(presentEmail) + "** but you haven't accepted the invite yet.\n"
                            + "Check your inbox (including spam) for the invite email."
                    )
                # status 3 = invited and accepted already
                if status == 3:
                    presentEmail = getPlexEmailForDiscordNickname(conn, str(messageAuthor.nick))
                    statusmsg = (
                            str(memberNickname)
                            + ", an invite has already been sent, and you have accepted it using this email address: "
                            + str(presentEmail)
                    )
                # status 4 = queued for an invite
                if status == 4:
                    presentEmail = getPlexEmailForDiscordNickname(conn, str(messageAuthor.nick))
                    yourQueueDate = getCurrentQueueDate(conn, nicknameForPlexEmail)
                    numberAheadOfYou = getNumberQueuedAhead(conn, yourQueueDate)
                    statusmsg = (
                            str(memberNickname)
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
                        "I did not find you in the DB, " + str(memberName) + ".\n"
                        + "**!status** command will not work for you until you have been invited or queued."
                )
            await messageChannel.send(statusmsg)
    # !openslots
    if message.content.lower() == "!openslots":
        with conn:
            valuesToSend = ("openslots", str(memberNickname), str(memberName), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        openSlotCount = getOpenSlotsCount(conn)
        if openSlotCount > 0:
            openslotsmsg = (
                    "There are **" + str(openSlotCount) + "** open slots. If you are looking for an invite try !invite"
            )
        if openSlotCount == 0:
            openslotsmsg = "There are no open slots, try **!inviteme** to be added to the queue."
        await messageChannel.send(openslotsmsg)
    # !pendinginvites
    if message.content.lower() == "!pendinginvites":
        with conn:
            valuesToSend = (
                "pendinginvites", str(memberNickname), str(memberName), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        pendingInvitesCount = getPendingInvitesCount(conn)
        if pendingInvitesCount > 0:
            pendinginvitesmsg = (
                    "There are **" + str(pendingInvitesCount)
                    + "** pending invites. \nIf you would like to be added to the queue, try **!invite**"
            )
        if pendingInvitesCount == 0:
            pendinginvitesmsg = "There are no pending invites. Try **!invite** if you want to be invited."
        await messageChannel.send(pendinginvitesmsg)
    # !libraries - info
    if message.content.lower() == "!libraries":
        with conn:
            valuesToSend = ("libraries", str(memberNickname), str(memberName), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        librariesmsg = "As of 04/13/2021 - https://i.imgur.com/89EfWvH.png"
        await messageChannel.send(librariesmsg)
    # !currentstreams - info from tautulli
    if message.content.lower() == "!currentstreams":
        with conn:
            valuesToSend = ("currentstreams", str(memberNickname), str(memberName), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        # print("Current Streams!")
        # https://github.com/Tautulli/Tautulli/wiki/Tautulli-API-Reference#get_activity
        TAUTULLI_URL = 'http://192.168.86.5:8181'
        TAUTULLI_APIKEY = '15a2eb6ccdeb49cc9f5871b52b66fdaa'
        # Get the Tautulli history.
        PARAMS = {
            'cmd': 'get_activity',
            'apikey': TAUTULLI_APIKEY
        }
        try:
            GET = SESSION.get(TAUTULLI_URL.rstrip('/') + '/api/v2', params=PARAMS).json()['response']['data']
            # print(str(GET))
            currentstreamsmsg = ("**Stream Count:** " + str(GET['stream_count'])
                                 + "\n**Directly Playing:** " + str(GET['stream_count_direct_play'])
                                 + "\n**Directly Streaming:** " + str(GET['stream_count_direct_stream'])
                                 + "\n**Transcoding:** " + str(GET['stream_count_transcode'])
                                 + "\n**Bandwidth:** " + str(GET['total_bandwidth'] / 1000) + "mbps"
                                 )
        except Exception as e:
            print("Tautulli API 'get_activity' request failed. Error: {}.".format(e))
            currentstreamsmsg = "Something went wrong."
        await messageChannel.send(currentstreamsmsg)
    # !help - info
    if message.content.lower() == "!help":
        with conn:
            valuesToSend = ("help", str(message.author), str(memberName), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        helpmsg = (
                "Try **!commands** for a direct message with the list of commands.\n"
                + "If you are looking for an invite, try **!invite** \n"
                + "Message Jomack16 for anything else."
        )
        await messageChannel.send(helpmsg)
    # !invite - info
    if message.content.lower() == "!invite":
        with conn:
            valuesToSend = ("invite", str(memberNickname), str(messageAuthor), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        await messageAuthor.create_dm()
        await messageAuthor.dm_channel.send(
            "Hi {}! \n\n".format(messageAuthor) + "You've asked for an invite!\n\n"
            + "To be invited to the plex server, please use the **!inviteme** command like this: "
            + "**!inviteme email@address.com**\n"
            + "  --must use command in the <#" + BOT_CHAT_CHANNEL_ID + "> channel.\n"
            + "  --must be an email address for a plex account **that you already have**.\n"
            + "  --If you don't have a plex.tv account already, **make one then come back** and request an invite.\n"
        )
    # !download - info
    if message.content.lower() == "!download":
        with conn:
            valuesToSend = ("download", str(memberNickname), str(memberName), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        await messageAuthor.create_dm()
        await messageAuthor.dm_channel.send(
            "Hi {}! \n\n".format(messageAuthor) + "You've asked about downloading from the plex server!\n"
            + "If you wish to download something from the server, please message Jomack16.\n"
            + "Please do not use any apps/plugins/utilities to download without talking to Jomack16 first."
            + " If this unauthorized is discovered, then you will be administratively **removed** from the plex server"
        )
    # !removeme - info
    if message.content.lower() == "!removeme":
        with conn:
            valuesToSend = ("removeme", str(memberNickname), str(messageAuthor), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        await messageAuthor.create_dm()
        await messageAuthor.dm_channel.send(
            "Hi {}! \n\n".format(messageAuthor) + "You've asked about being removed from the plex server!\n"
            + "If you wished to be removed from the plex server, just leave the discord server.\n"
            + "This will automatically remove you from the plex server."
        )
    # !commands - info
    if message.content.lower() == "!commands":
        with conn:
            valuesToSend = ("commands", str(memberNickname), str(memberName), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        await messageAuthor.create_dm()
        await messageAuthor.dm_channel.send(
            "Hi {}! \n\n".format(messageAuthor) + "Available commands: "
            + "**!invite**, **!inviteme**, **!openslots**, **!pendinginvites**, **!help**, **!status**, "
            + "**!libraries**, **!rules**, **!removeme**, **!download**, **!currentstreams**, and **!commands** \n"
            + "**!invite** will DM you with a message about how to be invited.\n"
            + "**!inviteme email@address.com** will send an invite to that email address.\n"
            + "    --must use command in the <#" + BOT_CHAT_CHANNEL_ID + "> channel.\n"
            + "    --must be an email address for a plex account that you already have.\n"
            + "    --If you don't have a plex.tv account already, make one then request an invite..\n"
            + "**!status email@address.com** will report your current status.\n"
            + "    --must be used in the <#" + BOT_CHAT_CHANNEL_ID + "> channel.\n"
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
    # !rules - info
    if message.content.lower() == "!rules":
        with conn:
            valuesToSend = ("rules", str(memberNickname), str(messageAuthor), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        await messageChannel.send(
            "Hi {}! \n\n".format(messageAuthor) + "These are the rules: \n"
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
            + "--7 NOTE: check your speedtest to the server in the <#" + SPEEDTEST_CHANNEL_ID + "> channel.\n\n"
            + "**Notes:**\nIf you are removed for inactivity, your status and discord role will reflect that, and you "
            + "can add yourself back to the invite queue with **!inviteme**"
        )
    # !speedtest - info
    if message.content.lower() == "!speedtest":
        with conn:
            valuesToSend = ("speedtest", str(memberNickname), str(messageAuthor), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        await messageChannel.send(
            "Hi\n"
            + "This is the url you can use to run a speedtest from you to the server: "
            + "http://jomack16.hopto.org:558/\n"
            + "You might be checking this because you want to play 4K content, or already tried to play 4K content and"
            + " received a message about not transcoding 4K.\n"
            + "If that is the case try **!transcoding** for more info.\n"
        )
    # !transcoding - info
    if message.content.lower() == "!transcoding":
        with conn:
            valuesToSend = ("transcoding", str(memberNickname), str(messageAuthor), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        await messageChannel.send(
            "Hi!\n"
            + "Transcoding IS allowed for MOST content on the server.\n"
            + "There is some 4K content, and because of the resource strain, transcoding 4K is not allowed.\n"
            + "For the highest quality/bitrate 4K content (on the server) it is recommended that you have a "
            + "download speed of 200mbps+.\n **NOTE:** a slower speed connection might work for some content.\n"
            + "To see what your connection speed to the server is, try **!speedtest**\n"
        )
    # !showmedb - info
    if message.content.startswith("!showmedb") and str(message.author) in ADMINS:
        msgArray = message.content.split()
        msgNickD = str(msgArray[1])
        with conn:
            valuesToSend = ("showmedb", "Jomack16", "Mr.Mustard_#2954", str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        everything = getEverythingForDiscordNickname(conn, msgNickD)
        # print(str(everything))
        eList = everything[0]
        if everything != "DONOT":
            await messageChannel.send(
                "**DiscordUsername**: " + str(eList[1])
                + ", **DiscordServerNickname**: " + str(eList[2]) + ", **PlexUsername**: " + str(eList[3])
                + ", **PlexEmailAddress**: " + str(eList[4]) + ", **Status**: " + str(eList[6])
                + ", **DateRemoved**: " + str(eList[7]) + ", **DateInvited**: " + str(eList[8])
                + ", **DateQueued**: " + str(eList[9])
            )
        else:
            await messageChannel.send(str(everything))
    # !adminremoveplex
    if message.content.startswith("!adminremoveplex") and str(message.author) in ADMINS:
        msgMember = message.author
        msgArray = message.content.split()
        msgNickname = str(msgArray[1])
        status = checkStatus(conn, msgNickname)
        pEmail = getPlexEmailForDiscordNickname(conn, str(msgNickname))
        dName = getDiscordNameForDiscordNickname(conn, str(msgNickname))
        with conn:
            valuesToSend = ("adminremoveplex", str(msgNickname), str(msgMember), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
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
            with conn:
                updateRemovedDateAndStatus(conn, msgNickname)
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
        await messageChannel.send(adminremoveplexmsg)
    # !adminremovecomplete
    if message.content.startswith("!adminremovecomplete") and str(message.author) in ADMINS:
        msgArray = message.content.split()
        msgNickname = str(msgArray[1])
        msgMember = message.author
        status = checkStatus(conn, msgNickname)
        pEmail = getPlexEmailForDiscordNickname(conn, str(msgNickname))
        dName = getDiscordNameForDiscordNickname(conn, str(msgNickname))
        with conn:
            valuesToSend = ("adminremovecomplete", str(msgNickname), str(msgMember), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        if status == 2 or status == 3:
            dmmsg = ""
            if dName != "DONOT":
                memberR = discord.utils.get(message.guild.members, name=dName)
            if memberR is not None:
                await memberR.remove_roles(invitedRole)
                try:
                    await memberR.dm_channel.send(
                        "Hi + " + str(dName) + "! \n\n"
                        + "You have been removed by the administrator!\n"
                        + "You have been removed from the Plex server and your information removed from the BotDB."
                    )
                    dmmsg = "Successful!"
                except Exception as e:
                    dmmsg = str(e)
            try:
                ACCOUNT.removeFriend(pEmail)
            except Exception as e:
                print("was not a plex account: " + str(e) + " Running no account removal instead")
                ACCOUNT.removeFriendNoAccount(pEmail)
            with conn:
                removeFromUserTable(conn, msgNickname)
            adminremovecompletemsg = (
                    "Removed the following user from Plex server and from the bot DB: \n"
                    + "memberNickname: " + str(msgNickname) + "\n"
                    + "PlexEmailAddress: " + str(pEmail) + "\n"
                    + "DM Message was: " + dmmsg
            )
        elif status == 0 or status == 1:
            dmmsg = ""
            if dName != "DONOT":
                memberR = discord.utils.get(message.guild.members, name=dName)
            if memberR is not None:
                await memberR.remove_roles(removedRole)
                try:
                    await memberR.dm_channel.send(
                        "Hi + " + str(dName) + "! \n\n"
                        + "You have been removed by the administrator!\n"
                        + "Your were already removed from the plex server and your information "
                        + "has been removed from the BotDB."
                    )
                    dmmsg = "successful!"
                except Exception as e:
                    dmmsg = str(e)
            with conn:
                removeFromUserTable(conn, msgNickname)
            adminremovecompletemsg = (
                    "DiscordNickname: **" + str(msgNickname)
                    + "** had a status of removed. Just removing from bot DB."
                    + "DM message was: " + dmmsg
            )
        elif status == 4:
            dmmsg = ""
            if dName != "DONOT":
                memberR = discord.utils.get(message.guild.members, name=dName)
            if memberR is not None:
                await memberR.remove_roles(queuedRole)
                try:
                    await memberR.dm_channel.send(
                        "Hi + " + str(dName) + "! \n\n"
                        + "You have been removed by the administrator!\n"
                        + "Your were only queued for the plex server and your information "
                        + "has been removed from the BotDB."
                    )
                    dmmsg = "successful!"
                except Exception as e:
                    dmmsg = str(e)
            with conn:
                removeFromUserTable(conn, msgNickname)
            adminremovecompletemsg = (
                    "DiscordNickname: **" + str(msgNickname)
                    + "** had a status of queued. Just removing from bot DB."
                    + "DM Message was: " + dmmsg
            )
        else:
            with conn:
                removeFromUserTable(conn, msgNickname)
            adminremovecompletemsg = (
                    "DiscordNickname: **" + str(msgNickname)
                    + "** does not have a status of invited. Just removing from bot DB."
            )
        await messageChannel.send(adminremovecompletemsg)
    # !admincommands
    if message.content.startswith("!admincommands") and str(message.author) in ADMINS:
        with conn:
            valuesToSend = ("admincommands", str(memberNickname), str(memberName), str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
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
        await messageChannel.send(admincommandsmsg)
    # !listplexusers
    if message.content.startswith("!listplexusers") and str(message.author) in ADMINS:
        try:
            PLEX_USERS = {user.email: user.username for user in ACCOUNT.users()}
        except Exception as e:
            print(str(e))
        with conn:
            valuesToSend = ("listplexusers", "Jomack16", "Mr.Mustard_#2954", str(date1), str(message.content))
            updateCommandUsageHistory(conn, valuesToSend)
        count = 0
        for x, y in PLEX_USERS.items():
            count += 1
            nickname = getDiscordNicknameNameForPlexEmail(conn, x)
            # print("email: " + str(x) + " username: " + str(y))
            listplexusersmsg1 = ("**"+str(count)+"**. **email**: " + str(x) + " **username**: " + str(y)
                                 + " **discordNickname**: " + str(nickname))
            await messageChannel.send(listplexusersmsg1)


client.run("Njk0MjUzODE0NjIyMTkxNjI2.GubGUG.CV7fplMHbquq27Wfn6gwyYzDAruRvqUoTMrhlU")