import discord
import bnbot
import bnbot.cards as cards
from bnbot.cards import Card
import bnbot.schema as sql
import yaml
import psycopg2
import psycopg2.extras
import random

properties = yaml.load(open('bnbot/properties.yml'), Loader=yaml.FullLoader)
token = properties.get('token')
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
dealerID = 0

# Connection to postgresql #
pg_prop = properties.get('postgres')
try:    
    conn = psycopg2.connect(dbname = pg_prop.get('dbname'),
                                  user = pg_prop.get('user'),
                                  password = pg_prop.get('password'),
                                  host = pg_prop.get('host'),
                                  port = pg_prop.get('port'),
                                  cursor_factory=psycopg2.extras.RealDictCursor)
    conn.autocommit = True

    # Print PostgreSQL Connection properties
    print (f'Connected to {conn.get_dsn_parameters()["dbname"]}')

except (Exception, psycopg2.Error) as error :
    print ("Error while connecting to PostgreSQL", error)

### General Helpers ###
# Converts an ID into an @ 
def mention_user(userID):
    return '<@' + str(userID) + '>'

def cards_to_string(card_list, splitter):
    card_string = ''
    for card in card_list:
        card_string += str(card) + splitter

    return card_string

def player_cards_to_string(gameID, playerID, splitter):
    return cards_to_string(get_player_cards(gameID, playerID), splitter)

def get_display_name(msg_channel, playerID):
    return msg_channel.guild.get_member(playerID).display_name

async def playerlist_to_display_names(msg_channel, plist):
    liststr = ""

    if not len(plist) == 0:
        for player in plist:
            liststr += str(msg_channel.guild.get_member(player).display_name) + '\n'
        return liststr.strip('\n')

    else:
        return 'N/A'

### Acting on current Games ###
def get_game_players(gameID):
    with conn.cursor() as cur:
        cur.execute(sql.get_game_players, {'gameid':gameID})
        plist = []
        for row in cur:
            plist.append(row['playerid'])
        return plist

def player_in_game(gameID, playerID):
    pgID = f"{playerID}:{gameID}"
    with conn.cursor() as cur:
        cur.execute(sql.check_for_pgid, {'pgid':pgID})
        if not cur.rowcount == 0:
            return True

        else:
            return False

def get_players(gameID):
    with conn.cursor() as cur:
        cur.execute(sql.get_game_players, {'gameid':gameID})
        plistdict = cur.fetchall()
        result = []
        for pdict in plistdict:
            result.append(pdict['playerid'])
        return result

def get_pgid(gameID, playerID):
    with conn.cursor() as cur:
        cur.execute(sql.get_pgid, {'pgid':f'{playerID}:{gameID}'})
        return cur.fetchone()

def get_current_turn(gameID):
    with conn.cursor() as cur:
        cur.execute(sql.get_game, {'gameid':gameID})
        return cur.fetchone()['current_player']

def get_current_playerID(gameID):
    with conn.cursor() as cur:
        current_turn = get_current_turn(gameID)
        cur.execute(sql.get_game_players, {'gameid':gameID})
        for row in cur:
            if row['turn_pos'] == current_turn:
                return row['playerid']

def set_current_turn(gameID, turn):
    with conn.cursor() as cur:
        cur.execute(sql.set_turn, {'new_turn':turn, 'gameid':gameID})

def progress_turn(gameID):
    with conn.cursor() as cur:
        cur.execute(sql.get_current_turn, {'gameid':gameID})
        current_turn = cur.fetchone()['current_player']
        cur.execute(sql.get_turn_list, {'gameid':gameID})
        new_turn = 0
        for row in cur:
            if row['turn_pos'] == current_turn:
              new_turn = cur.fetchone()['turn_pos']

        cur.execute(sql.set_turn, {'new_turn':new_turn, 'gameid':gameID})
        global dealerID
        if get_current_playerID == dealerID:
            update_game_state(gameID, 'dealer_turn')

def get_player_cards(gameID, playerID):
    pgID = f"{playerID}:{gameID}"
    with conn.cursor() as cur:
        cur.execute(sql.get_player_cards, {'pgid':pgID})
        cdictlist = cur.fetchall()
        cardlist = []
        for card in cdictlist:
            cardlist.append(Card(card['suit'], card['rank']))
        
        return cardlist

def get_player_total(gameID, playerID):
    pcards = get_player_cards(gameID, playerID)
    has_ace = False
    sum = 0
    for card in pcards:
        sum += card.value()
        if card.value() == 1:
            has_ace = True
    
    if sum <= 11 and has_ace:
        sum += 10

    return sum

def is_current_player(gameID, playerID):
    player_turn = get_pgid(gameID, playerID)['turn_pos']
    current_turn = get_current_turn(gameID)

    return player_turn == current_turn

def get_first_turn(gameID):
    with conn.cursor() as cur:
        cur.execute(sql.get_ordered_turns, {'gameid':gameID})
        return cur.fetchone()['turn_pos']

def update_game_state(gameID, game_state):
    with conn.cursor() as cur:
        cur.execute(sql.update_game_state, {'game_state':game_state, 'gameid':gameID})

def join_game(gameID, playerID):
    pgID = f"{playerID}:{gameID}"
    with conn.cursor() as cur:
        cur.execute(sql.get_next_turn, {'gameid':gameID})
        pturn = 0
        if not cur.rowcount == 0:
            pturn = int(cur.fetchone()['turn_pos']) + 1

        else:
            pturn = 1

        cur.execute(sql.add_pgid, {'playerid':playerID, 'gameid':gameID, 'pgid':pgID, 'turn_pos':pturn})
        cur.execute(sql.check_for_game, {'gameid':gameID})
        if cur.rowcount == 0:
            cur.execute(sql.create_game, {'gameid':gameID})

def leave_game(gameID, playerID):
    pgID = f"{playerID}:{gameID}"
    with conn.cursor() as cur:
        cur.execute(sql.remove_pgid, {'pgid':pgID})
        remove_empty_game(gameID)

def leave_all(playerID):
    with conn.cursor() as cur:
        cur.execute(sql.get_current_games, {'playerid':playerID})
        pcurgame = cur.fetchall()
        cur.execute(sql.remove_pgid_all, {'playerid':playerID})
        for gdict in pcurgame:
            remove_empty_game(gdict['gameid'])

def remove_empty_game(gameID):
    with conn.cursor() as cur:
        cur.execute(sql.get_game_players, {'gameid':gameID})
        if cur.rowcount == 0:
            cur.execute(sql.remove_game, {'gameid':gameID})

### Blackjack Actions ###
def get_game_state(gameID):
    with conn.cursor() as cur:
        cur.execute(sql.get_game_state, {'gameid':gameID})

def get_cards_in_play(gameID):
    with conn.cursor() as cur:
        cur.execute(sql.get_cards_in_play, {'gameid':gameID})
        cards_in_play = []
        for row in cur:
            card = Card(row['suit'], row['rank'])
            cards_in_play.append(card)
        return cards_in_play

def deal_card(gameID, playerID):
    with conn.cursor() as cur:
        card = cards.deal(get_cards_in_play(gameID))
        cur.execute(sql.assign_card, {'pgid':f'{playerID}:{gameID}', 'suit':card.suit, 'rank':card.rank})

def remove_game_cards(gameID):
    with conn.cursor() as cur:
        cur.execute(sql.remove_game_cards, {'gameid':gameID})

async def blackjack_action(message, channelID, playerID):
    lmsg = message.content.lstrip('b.').casefold().split()
    msg = lmsg[0]
    with conn.cursor() as cur:
        if not player_in_game(channelID, playerID):
            await message.channel.send('You are not in the game')
            return

        cur.execute(sql.get_game_state, {'gameid':channelID})
        gstate = cur.fetchone()['game_state']

        if msg == 'bet':
            try:
                amount = int(lmsg[1])
            except ValueError:
                await message.channel.send("Not a valid amount")
                return
            except IndexError:
                await message.channel.send("Missing bet amount")
                return

            await process_bet(message.channel, channelID, playerID, amount)

        elif msg == 'start':
            if not gstate == 'pregame':
                await message.channel.send('Game is already started')
            
            else:
                await process_start(message.channel)

        elif not is_current_player(channelID, playerID):
            await message.channel.send('It is not your turn')
            return

        elif gstate == 'player_turn':
            if msg == 'hit':
                await process_hit(message.channel, channelID, playerID)

            elif msg == 'stay':
                await process_stay(message.channel, channelID, playerID)

async def process_bet(msg_channel, gameID, playerID, amount):
    if amount > get_balance(playerID):
        await msg_channel.send('You do not have enough money for that bet')
        return

    with conn.cursor() as cur:
        cur.execute(sql.add_bet, {'pgid':f'{playerID}:{gameID}', 'amount':amount})
        adjust_balance(playerID, -amount)
        await msg_channel.send(f'**Bet Placed**: ₽{amount}')

def process_payout(gameID):
    with conn.cursor() as cur:
        cur.execute(sql.get_result_bet, {'result':'W', 'gameid':gameID})
        winners = {}
        for row in cur:
            winners[row['playerid']] = row['amount']

        cur.execute(sql.get_result_bet, {'result':'D', 'gameid':gameID})
        draws = {}
        for row in cur:
            draws[row['playerid']] = row['amount']

        for player in winners:
            adjust_balance(player, winners[player] * 2)

        for player in draws:
            adjust_balance(player, draws[player])

def process_winloss(gameID):
    global dealerID
    dtotal = get_player_total(gameID, dealerID)
    players = get_players(gameID)
    with conn.cursor() as cur:
        for player in players:
            ptotal = get_player_total(gameID, player)
            
            if ptotal > 21:
                cur.execute(sql.update_player_result, {'result':'L', 'playerid':player})

            elif dtotal > 21:
                cur.execute(sql.update_player_result, {'result':'W', 'playerid':player})

            elif ptotal == dtotal:
                cur.execute(sql.update_player_result, {'result':'D', 'playerid':player})

            elif ptotal > dtotal:
                cur.execute(sql.update_player_result, {'result':'W', 'playerid':player})

            else:
                cur.execute(sql.update_player_result, {'result':'L', 'playerid':player})
                

def get_players_by_result(gameID, result):
    with conn.cursor() as cur:
        cur.execute(sql.get_result_players, {'result':result, 'gameid':gameID})
        plist = []
        for row in cur:
            plist.append(row['playerid'])
        return plist

async def process_start(msg_channel):
    global dealerID
    join_game(msg_channel.id, dealerID)
    update_game_state(msg_channel.id, 'player_turn')
    set_current_turn(msg_channel.id, get_first_turn(msg_channel.id))
    plist = get_players(msg_channel.id)
    remove_game_cards(msg_channel.id)
    for i in range(2):
        for player in plist:
            deal_card(msg_channel.id, player)
        i += 1

    await display_card_table(msg_channel)
    # Get dealer amount check for 21. If dealer has 21 then end game
    if get_player_total(msg_channel.id, dealerID) == 21:
        return # Go to finish game

    current_player = get_current_playerID(msg_channel.id)
    await msg_channel.send(f"It is {mention_user(current_player)}'s turn. You have {player_cards_to_string(msg_channel.id, current_player, ' ')}")

async def process_hit(msg_channel, gameID, playerID):
    deal_card(gameID, playerID)
    await msg_channel.send(f"{get_display_name(msg_channel, playerID)} has {player_cards_to_string(msg_channel.id, playerID, ' ')}")

    # Bust detect
    global dealerID
    if get_player_total(gameID, playerID) > 21:
        bustmsg = f"{get_display_name(msg_channel, playerID)} has **bust**.\n"
        progress_turn(gameID)
        if get_current_playerID(gameID) == dealerID:
            await msg_channel.send(bustmsg)
            await finish_round(msg_channel, gameID)
        
        else:
            current_player = get_current_playerID(gameID)
            await msg_channel.send(bustmsg + f"It is {mention_user(current_player)} 's turn. They have {player_cards_to_string(msg_channel.id, current_player, ' ')}")

async def process_stay(msg_channel, gameID, playerID):
    stay_player = get_current_playerID(gameID)
    staymsg = (f"{get_display_name(msg_channel, stay_player)} stays with {player_cards_to_string(msg_channel.id, stay_player, ' ')}\n")
    progress_turn(gameID)
    if get_current_playerID(gameID) == dealerID:
        await msg_channel.send(staymsg)
        await finish_round(msg_channel, gameID)

    else:
        current_player = get_current_playerID(gameID)
        await msg_channel.send(staymsg + f"It is {mention_user(current_player)} 's turn. They have {player_cards_to_string(msg_channel.id, current_player, ' ')}")

async def finish_round(msg_channel, gameID):
    global dealerID
    needs_cards = get_player_total(gameID, dealerID) < 16
    dealerhand = get_player_cards(gameID, dealerID)
    starting_cards = str(dealerhand[0]) + ', ' + str(dealerhand[1])

    drawn_str = ""
    if needs_cards: 
        while get_player_total(gameID, dealerID) < 16:
            deal_card(gameID, dealerID)
        dealerhand = get_player_cards(gameID, dealerID)
        drawn_str = " and draws "
        drawn = dealerhand[2:len(dealerhand)]
        for card in drawn:
            drawn_str += str(card) + ', '

    await msg_channel.send(f"It is now the dealer's turn\nThe dealer has {starting_cards}{drawn_str}\nThe dealer has {get_player_total(gameID, dealerID)}")

### Displaying W/L/D in an embed ###
    process_winloss(gameID)
    leave_game(gameID, dealerID)
    winners = await playerlist_to_display_names(msg_channel, get_players_by_result(gameID, 'W'))
    losers = await playerlist_to_display_names(msg_channel, get_players_by_result(gameID, 'L'))
    draws = await playerlist_to_display_names(msg_channel, get_players_by_result(gameID, 'D'))
    
    embed = discord.Embed(title='Hand Over' , color=0xffed66)
    embed.add_field(name="Winners", value=winners, inline=True)
    embed.add_field(name="Losers", value=losers, inline=True)
    embed.add_field(name="Draws", value=draws, inline=True)
    embed.set_footer(text="sampletext.txt")
    await msg_channel.send(embed=embed)

    process_payout(gameID)
    set_current_turn(gameID, 0)
    update_game_state(gameID, 'pregame')

async def display_card_table(msg_channel):
    global dealerID
    embed = discord.Embed(title='Current hands' , color=0xFFFFF)
    embed.add_field(name='Dealer', value=get_player_cards(msg_channel.id, dealerID)[0], inline=False)

    p_in_g = get_game_players(msg_channel.id)
    p_in_g.remove(dealerID)
    for player in p_in_g:
        embed.add_field(name=get_display_name(msg_channel, player), value=cards_to_string(get_player_cards(msg_channel.id, player), '\n'), inline=True)

    await msg_channel.send(embed=embed)

### Currency Actions ###
def create_user(playerID):
    if not check_for_user(playerID):
        with conn.cursor() as cur:
            cur.execute("""
            INSERT INTO player (playerid, money)
            VALUES(%(playerID)s, 1000)
            """, {'playerID':playerID})
            return True

def check_for_user(playerID):
    with conn.cursor() as cur:
        cur.execute("""
        SELECT * FROM player 
        WHERE playerid = %(playerID)s
        """, {'playerID':playerID})
        if not cur.rowcount == 0:
            return True

        else:
            return False

def get_balance(playerID):
    with conn.cursor() as cur:
        cur.execute("""
        SELECT * FROM player 
        WHERE playerid = %(playerID)s
        """, {'playerID':playerID})

        return cur.fetchone()['money']

def adjust_balance(playerID, amount):
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM player WHERE playerid = %(playerID)s', {'playerID':playerID})
        bal = cur.fetchone()['money']
        newbal = bal + amount
        cur.execute("""
        UPDATE player
        SET money = %(newbal)s
        WHERE playerid = %(playerID)s
        """, {'newbal':newbal, 'playerID':playerID})

def exchange_money(payer, payee, amount):
    adjust_balance(payer, -amount)
    adjust_balance(payee, amount)

async def process_pay(message):
    payer = message.author.id
    bal = get_balance(payer)
    
    try:
        payee = message.mentions[0].id
        amount = int((message.content.lstrip('b.')).split()[2])
    except ValueError:
        await message.channel.send("Not a valid amount")
        return
    except IndexError:
        await message.channel.send("Missing amount or payee")
        return

    if not check_for_user(payee):
        await message.channel.send("User does not exist in the bank, tell them to type `b. ubi`")
        return

    elif bal < 10000 or bal < amount:
        await message.channel.send("You either do not have enough to pay or have less than 10,000")
        return 

    exchange_money(payer, payee, amount)

    embed = discord.Embed(title='₽ *bnbank* ₽', color=0x008c15)
    embedplayers = f'\n**{get_display_name(message.channel, payer)}**\n**{get_display_name(message.channel, payee)}**'
    embedamounts = f'{get_balance(payer)}\n{get_balance(payee)}'
    embed.add_field(name='Account', value=embedplayers, inline=True)
    embed.add_field(name='₽', value=embedamounts, inline=True)
    embed.set_footer(text=f"Transaction amount: ₽ {amount}")
    await message.channel.send(embed=embed)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    global dealerID
    dealerID = client.user.id

bj_commands = ['start','hit','stay','bet']

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('whome'):
        await message.channel.send(mention_user(message.author.id))

    ### Gambling Commands ###
    if message.content.startswith('b.'):
        msg = message.content.lstrip('b.').casefold()
        msg = msg.split()[0]
        channelID = message.channel.id
        playerID = message.author.id

        if msg in bj_commands:
           await blackjack_action(message, channelID, playerID)

        elif msg == 'players':
            await message.channel.send(get_players(message.channel))

        ## Player to game ##
        elif msg == 'join':
            if not player_in_game(channelID, playerID):
                join_game(channelID, playerID)
                await message.channel.send('Joined game')

            else:
                await message.channel.send('You are in the game')

        elif msg == 'leave':
            if player_in_game(channelID, playerID):
                leave_game(channelID, playerID)
                await message.channel.send(f'{message.author.display_name} Left game')

            else:
                await message.channel.send('You are not in this game')

        elif msg == 'leaveall':
            leave_all(playerID)
            await message.channel.send('All games left')

        ## Player to money ##
        elif msg == 'bal':
            if check_for_user(playerID):
                await message.channel.send(f'You have {get_balance(playerID)}')

            else:
                create_user(playerID)
                await message.channel.send('User created, you have been given 1000 Dollars.')

        elif msg == 'ubi':
            if check_for_user(playerID):
                if get_balance(playerID) < 100:
                    adjust_balance(playerID, 100)
                    await message.channel.send('You have been given 100 Dollars. Commie.')

                else:
                    await message.channel.send('You have too much money to recieve ubi')    

            else:
                create_user(playerID)
                await message.channel.send('User created, you have been given 1000 Dollars.')

        # b. pay (user to be paid) (amount to be paid)
        elif msg == 'pay':
            await process_pay(message)

        ## Debug ##
        elif msg == 'help':
            await message.channel.send('contact <@83794466820849664>')

        elif msg == 'cf' and playerID == 83794466820849664:
            with conn.cursor() as cur:
                ids = [1000, 2000, 3000]
                for id in ids:
                    join_game(1234, id)
                for i in range(52):
                    deal_card(1234, random.choice(ids))
                    i += 1

                cur.execute(sql.remove_game_cards, {'gameid':1234})
                cur.execute("DELETE FROM player_game WHERE gameid = 1234")
                cur.execute(sql.remove_game, {'gameid':1234})
                await message.channel.send('cf.')

        elif msg == 'w' and playerID == 83794466820849664:
            with conn.cursor() as cur:
                cur.execute("delete from game")
                cur.execute("delete from card")
                cur.execute("delete from player_game")
                await message.channel.send('wipe.')
        
        else:
            await message.channel.send('Invalid command')

client.run(token)