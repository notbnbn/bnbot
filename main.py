import discord
import bnbot
from bnbot.cards import Card, Deck
from bnbot.game import Game, Game_State
from bnbot.player import Player
import yaml
import psycopg2
import psycopg2.extras

properties = yaml.load(open('bnbot/properties.yml'), Loader=yaml.FullLoader)
token = properties.get('token')
client = discord.Client()
currentGames = []

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

# Converts an ID into an @ 
def mention_user(userID):
    return '<@' + str(userID) + '>'

def player_cards_to_string(gameID, playerID):
    cards = ''
    hand = get_game(gameID).get_player(playerID).hand()
    
    for c in hand:
        cards += str(c) + ', '
    return cards.strip(', ')

async def playerlist_to_display_names(msg_channel, plist):
    liststr = ""

    if not len(plist) == 0:
        for player in plist:
            liststr += str(msg_channel.guild.get_member(player.playerID).display_name) + '\n'
        return liststr.strip('\n')

    else:
        return 'N/A'

### Acting on current Games ###
def create_game(gameID):
    currentGames.append(Game(gameID))

def get_game(gameID):
    for game in currentGames:
        if game.gameID == gameID:
            return game

    else:
        return None

def player_in_game(gameID, playerID):
    if not channel_has_game(gameID):
        return False
    
    else:
        g = get_game(gameID)

        if not g.get_player(playerID) == None:
            return g.get_player(playerID) in g.players

        else:
            return False

def get_players(gameID):
    if not channel_has_game(gameID):
        return []

    else:
        return get_game(gameID).players

def end_game(gameID):
    if channel_has_game(gameID):
        currentGames.remove(Game(gameID))

def channel_has_game(gameID):
    return Game(gameID) in currentGames

def join_game(gameID, playerID):
    if channel_has_game(gameID):
            get_game(gameID).add_player(playerID)

    else:
        create_game(gameID)
        get_game(gameID).add_player(playerID)

def leave_game(gameID, playerID):
    if channel_has_game(gameID):
        get_game(gameID).remove_player(playerID)

    if get_players(gameID) == []:
        end_game(gameID)

### Blackjack Actions ###
async def blackjack_action(message, channelID, playerID):
    msg = ((message.content.lstrip('b.')).strip(' ')).casefold()
    g = get_game(channelID)

    if msg == 'start':
        await process_start(message.channel, g, playerID)

    elif g.game_state == Game_State.player_turn:
        
        if msg == 'hit' and g.get_current_player().playerID == playerID:
            await process_hit(message.channel, g, playerID)

        elif msg == 'stay' and g.get_current_player().playerID == playerID:
            await process_stay(message.channel, g, playerID)

async def process_start(msg_channel, game, playerID):
    if game.game_state == Game_State.pregame:
        if player_in_game(msg_channel.id, playerID):
            game.start_round()
            if not game.dealer.total() == 21:
                await msg_channel.send(f"The dealer has {game.dealer.cards[0]}\nIt is {mention_user(game.get_current_player())}'s turn, you have {player_cards_to_string(msg_channel.id, game.get_current_player().playerID)}")
                await display_card_table(msg_channel, game)

            else:
                await finish_round(msg_channel, game)

    else:
        await msg_channel.send('Game is already started')

async def process_hit(msg_channel, game, playerID):
    game.player_hit()
    await msg_channel.send(f'{client.get_user(playerID).display_name} has {player_cards_to_string(msg_channel.id, playerID)}')

    if game.get_player(playerID).total() > 21:
        nxt = game.get_current_player().playerID
        await msg_channel.send(f"{client.get_user(playerID).display_name} has bust.")
        if game.game_state == Game_State.dealer_turn:
            await finish_round(msg_channel, game)

        else:
            await msg_channel.send(f"It is {mention_user(nxt)} 's turn. They have {player_cards_to_string(msg_channel.id, nxt)}")

async def process_stay(msg_channel, game, playerID):
    await msg_channel.send(f'{msg_channel.guild.get_member(playerID).display_name} stays with {player_cards_to_string(msg_channel.id, playerID)}')
    game.player_stay()
    nxt = game.get_current_player().playerID

    if game.game_state == Game_State.dealer_turn:
        await finish_round(msg_channel, game)

    else:
        await msg_channel.send(f"It is {mention_user(nxt)} 's turn. They have {player_cards_to_string(msg_channel.id, nxt)}")

async def finish_round(msg_channel, game):
    needs_cards = game.dealer.total() < 16
    game.dealer_action()
    starting_cards = str(game.dealer.cards[0]) + ', ' + str(game.dealer.cards[1])

    drawn_str = ""
    if needs_cards: 
        drawn_str = " and draws "
        drawn = game.dealer.hand()[2:len(game.dealer.hand())]
        for card in drawn:
            drawn_str += str(card) + ', '

    await msg_channel.send(f"It is now the dealer's turn\nThe dealer has {starting_cards}{drawn_str}\nThe dealer has {game.dealer.total()}")

### Displaying W/L/D in an embed ###
    winners = await playerlist_to_display_names(msg_channel, game.winners)
    losers = await playerlist_to_display_names(msg_channel, game.losers)
    draws = await playerlist_to_display_names(msg_channel, game.draws)
    
    embed = discord.Embed(title='Hand Over' , color=0xffed66)
    embed.add_field(name="Winners", value=winners, inline=True)
    embed.add_field(name="Losers", value=losers, inline=True)
    embed.add_field(name="Draws", value=draws, inline=True)
    embed.set_footer(text="sampletext.txt")
    await msg_channel.send(embed=embed)

    game.game_state = Game_State.pregame

async def display_card_table(msg_channel, game):
    embed = discord.Embed(title='Current hands' , color=0xFFFFF)
    embed.add_field(name='Dealer', value=game.dealer.cards[0], inline=False)

    for player in game.players:
        embed.add_field(name=msg_channel.guild.get_member(player.playerID).display_name, value=player.hand_string('\n'), inline=True)
    embed.remove_field(len(game.players))

    await msg_channel.send(embed=embed)

### Currency Actions ###
def check_for_user(playerID):
    with conn.cursor() as cur:
        cur.execute("""
        SELECT * FROM players 
        WHERE playerid = %(playerID)s
        """, {'playerID':playerID})
        if not cur.rowcount == 0:
            return True

        else:
            cur.execute("""
            INSERT INTO players (playerid, money)
            VALUES(%(playerID)s, 1000)
            """, {'playerID':playerID})
            return False

def get_balance(playerID):
    with conn.cursor() as cur:
        cur.execute("""
        SELECT * FROM players 
        WHERE playerid = %(playerID)s
        """, {'playerID':playerID})

        currow = cur.fetchone()
        print(currow)
        return currow['money']

def adjust_balance(playerID, amount):
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM players WHERE playerid = %(playerID)s', {'playerID':playerID})
        bal = cur.fetchone()['money']
        newbal = bal + amount
        cur.execute("""
        UPDATE players
        SET money = %(newbal)s
        WHERE playerid = %(playerID)s
        """, {'newbal':newbal, 'playerID':playerID})

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

bj_commands = ['start','hit','stay']

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('id'):
        await message.channel.send('userID: ' + str(message.author.id) + '\nchnnlID: ' + str(message.channel.id) + '\nguildID: ' + str(message.guild.id))

    if message.content.startswith('whome'):
        await message.channel.send(mention_user(message.author.id))

    ### Gambling Commands ###
    if message.content.startswith('b.'):
        msg = ((message.content.lstrip('b.')).strip(' ')).casefold()
        channelID = message.channel.id
        playerID = message.author.id

        if msg == 'cheat' and message.author.id == 83794466820849664:
            await message.channel.send(get_game(channelID).deck.next())

        elif msg in bj_commands:
            if channel_has_game(channelID) and player_in_game(channelID, playerID):
                await blackjack_action(message, channelID, playerID)

            else:
                await message.channel.send("Game is either not in progress or you are not in it.")

        ## Player to game ##
        elif msg == 'join':
            if not player_in_game(channelID, playerID):
                join_game(channelID, playerID)
                await message.channel.send('Joined game')

            else:
                await message.channel.send('You are in a game')

        elif msg == 'leave':
            if player_in_game(channelID, playerID):
                leave_game(channelID, playerID)

                if not channel_has_game(channelID):
                    await message.channel.send('Game left and ended')

                else:
                    await message.channel.send(f'{message.author.display_name} Left game')

            else:
                await message.channel.send('You are not in a game')

        ## Player to money ##
        elif msg == 'bal':
            if check_for_user(playerID):
                await message.channel.send(f'You have {get_balance(playerID)}')

            else:
                await message.channel.send('User created, you have benn given 1000 Dollars.')

        elif msg == 'ubi':
            if check_for_user(playerID):
                if get_balance(playerID) < 1000:
                    adjust_balance(playerID, 1000)
                    await message.channel.send('You have been given 1000 Dollars. Commie.')

                else:
                    await message.channel.send('You have too much money to recieve ubi')    

            else:
                await message.channel.send('User created, you have been given 1000 Dollars.')

        ## Debug ##
        elif msg == 'ingame':
            if channel_has_game(channelID) and player_in_game(channelID, playerID):
                await message.channel.send('Ye')

            else:
                await message.channel.send('Ne')
        
        elif msg == 'hasgame':
            await message.channel.send(channel_has_game(channelID))

        elif msg == 'help':
            await message.channel.send('contact <@83794466820849664>')
        
        else:
            await message.channel.send('Invalid command')

client.run(token)