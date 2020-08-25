class Player:
    def __init__(self, playerID):
        self.cards = []
        self.playerID = playerID

    def give_card(self, card):
        self.cards.append(card)

    def hand(self):
        return self.cards

    def clear_hand(self):
        self.cards.clear()

    def total(self):
        sum = 0
        for x in self.hand():
            sum += x.value()

        if sum <= 11:
            for x in self.hand():
                if x.value() == 1:
                    sum += 10
                    break

        return sum

    def __str__(self):
        return str(self.playerID)

    def __eq__(self, other_player):
        if other_player == None:
            return None
        
        else:
            return self.playerID == other_player.playerID