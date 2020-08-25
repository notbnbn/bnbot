import discord
from bnbot.cards import Card, Deck
from bnbot.game import Game

currentGames = []

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