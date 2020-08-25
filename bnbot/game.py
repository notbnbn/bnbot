import enum
from bnbot.cards import Card, Deck
from bnbot.player import Player

class Game_State(enum.Enum):
    pregame = 1
    player_turn = 2
    dealer_turn = 3
    finish = 4

class Game:
    def __init__(self, channelID):
        self.gameID = channelID
        self.game_state = Game_State.pregame
        self.deck = Deck()
        self.current_player = 0
        self.players = []
        self.dealer = Player(729100329181773836)
        self.winners = []
        self.losers = []
        self.draws = []

    def __eq__(self, other_game):
        return self.gameID == other_game.gameID

    def get_gameID(self):
        return self.gameID

    def show_players(self):
        return self.players

    # Adds player into players[]
    def add_player(self, playerID):
        pl = Player(playerID)
        if pl not in self.players:
            self.players.append(pl)

    # Checks if player is in players then removes
    def remove_player(self, playerID):
        bad_player = Player(playerID)
        if bad_player in self.players:
            self.players.remove(bad_player)

    def get_player(self, playerID):
        for player in self.players:
            if player.playerID == playerID:
                return player

    def get_current_player(self):
        return self.players[self.current_player]

    # Recuse until dealer has 16 or more
    def dealer_action(self):
        if self.dealer.total() < 16:
            self.deal(self.dealer.playerID)
            self.dealer_action()

        else:
            self.finish_round()

    # Puts card from deck to specified player
    def deal(self, playerID):
        self.get_player(playerID).give_card(self.deck.deal())

    def detect_bust(self, playerID):
        if self.get_player(playerID).total() > 21:
            return True

        else:
            return False

    # Returns cards in player's hand in the for of a list
    def player_cards(self, playerID):
        return self.get_player(playerID).hand()

    def next_player(self):
        self.current_player += 1
        if self.get_current_player() == self.dealer:
            self.game_state = Game_State.dealer_turn

    # Take in playerID and action
    def player_hit(self):
        self.deal(self.get_current_player().playerID)
        if self.detect_bust(self.get_current_player().playerID):
            self.next_player()

    def player_stay(self):
        self.next_player()

    def start_round(self):
        # Add dealer to the end of the players list and set game in progress
        self.players.append(self.dealer)
        self.game_state = Game_State.player_turn
        
        # Clear players and dealers hands then reset deck
        for player in self.players:
            player.clear_hand()

        self.deck.new()
        self.current_player = 0

        # Reset finished statuses
        self.winners = []
        self.losers = []
        self.draws = []

        # Deal everyone two cards
        for player in self.players:
            self.deal(player.playerID)
            self.deal(player.playerID)

        # Check to see if dealer has 21
        if self.dealer.total() == 21:
            self.finish_round()


    def finish_round(self):
        # Remove dealer from the players list
        self.remove_player(self.dealer.playerID)
        self.game_state = Game_State.finish

        for player in self.players:
            playerTotal = player.total()
            if playerTotal > 21:
                self.losers.append(player)

            elif self.dealer.total() > 21:
                self.winners.append(player)
            
            elif playerTotal == self.dealer.total():
                self.draws.append(player)

            elif playerTotal > self.dealer.total():
                self.winners.append(player)

            else:
                self.losers.append(player)