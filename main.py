import discord
import bnbot
from bnbot.cards import Card, Deck
from bnbot.game import Game, Game_State
from bnbot.player import Player
import bnbot.gamble as gamble
import yaml

properties = yaml.load(open('bnbot/properties.yml'), Loader=yaml.FullLoader)
token = properties.get('token')

client = discord.Client()

# Converts an ID into an @ 
def mention_user(userID):
    return '<@' + str(userID) + '>'

def player_cards_to_string(gameID, playerID):
    cards = ''
    hand = gamble.get_game(gameID).get_player(playerID).hand()
    
    for c in hand:
        cards += str(c) + ', '
    return cards.strip(', ')

async def playerlist_to_display_names(msg_channel, plist):
    liststr = ""

    if not len(plist) == 0:
        for player in plist:
            liststr += str(msg_channel.guild.get_member(player.playerID).display_name) + ', '
        return liststr.strip(', ')

    else:
        return 'N/A'

async def blackjack_action(message, channelID, playerID):
    msg = ((message.content.lstrip('bj!')).strip(' ')).casefold()
    g = gamble.get_game(channelID)

    if msg == 'start':
        await process_start(message.channel, g, playerID)

    elif g.game_state == Game_State.player_turn:
        
        if msg == 'hit' and g.get_current_player().playerID == playerID:
            await process_hit(message.channel, g, playerID)

        elif msg == 'stay' and g.get_current_player().playerID == playerID:
            await process_stay(message.channel, g, playerID)

async def process_start(msg_channel, game, playerID):
    if game.game_state == Game_State.pregame:
        if gamble.player_in_game(msg_channel.id, playerID):
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

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('id'):
        await message.channel.send('userID: ' + str(message.author.id) + '\nchnnlID: ' + str(message.channel.id) + '\nguildID: ' + str(message.guild.id))

    if message.content.startswith('whome'):
        await message.channel.send(mention_user(message.author.id))

    ##### Gambling Commands #####
    if message.content.startswith('bn!'):
        # Take off bn! and make lowercase
        msg = ((message.content.lstrip('bn!')).strip(' ')).casefold()
        channelID = message.channel.id
        playerID = message.author.id

        if msg == 'cheat' and message.author.id == 83794466820849664:
            await message.channel.send(gamble.get_game(channelID).deck.next())

        ## Player to game ##
        elif msg == 'join':
            if not gamble.player_in_game(channelID, playerID):
                gamble.join_game(channelID, playerID)
                await message.channel.send('Joined game')

            else:
                await message.channel.send('You are in a game')

        elif msg == 'players':
            pls = gamble.get_players(channelID)

            if len(pls) == 0:
                await message.channel.send('No current game')

            else:
                player_message = 'Players:\n'
                for player in pls:
                    memb = message.author.display_name
                    player_message += memb + '\n'

                await message.channel.send(player_message)

        elif msg == 'leave':
            if gamble.player_in_game(channelID, playerID):
                gamble.leave_game(channelID, playerID)
                await message.channel.send('Left game')

            else:
                await message.channel.send('You are not in a game')

        ## Debug ##
        elif msg == 'ingame':
            if gamble.channel_has_game(channelID) and gamble.player_in_game(channelID, playerID):
                await message.channel.send('Ye')

            else:
                await message.channel.send('Ne')
        
        elif msg == 'hasgame':
            await message.channel.send(gamble.channel_has_game(channelID))

        elif msg == 'help':
            await message.channel.send('contact <@83794466820849664>')

        else:
            await message.channel.send('Invalid command')

    if message.content.startswith('bj!'):
        channelID = message.channel.id
        playerID = message.author.id
        
        if gamble.channel_has_game(channelID) and gamble.player_in_game(channelID, playerID):
            await blackjack_action(message, channelID, playerID)

        else:
            await message.channel.send("Game is either not in progress or you are not in it.")

client.run(token)