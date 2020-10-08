import random

suit = ['S', 'C', 'H', 'D']
rank = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']


class Card:
    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    def __str__(self):
        suit_symbol = '?'

        if self.suit == 'S':
            suit_symbol = '\u2664'

        elif self.suit == 'C':
            suit_symbol = '\u2667'

        elif self.suit == 'H':
            suit_symbol = '\u2661'

        elif self.suit == 'D':
            suit_symbol = '\u2662'

        else:
            suit_symbol = 'how'

        return self.rank + suit_symbol

    def __eq__(self, card):
        if self.suit == card.suit and self.rank == card.rank:
            return True

        else:
            return False

    def value(self):
        if self.rank.isnumeric():
            return int(self.rank)

        elif self.rank == 'A':
            return 1

        else:
            return 10


def remove_cards(cards_in_play):
    cdeck = [Card(s, r) for r in rank for s in suit]
    if not len(cards_in_play) == 0:
        for card in cards_in_play:
            cdeck.remove(card)

    return cdeck


def deal(cards_in_play):
    cdeck = remove_cards(cards_in_play)
    if not len(cdeck) == 0:
        card = random.choice(cdeck)
        return card

    else:
        return None

# awk made you do this, cry at later date
# everything is fixed, thanks awk
# I lied
