import numpy as np

class Deck:
    def __init__(self):
        self.deck = None
    
    def create_card_deck(self):
        values = "23456789TJQKA"
        suites = "CDHS"
        self.deck = []  # contains cards in the deck
        _ = [self.deck.append(x + y) for x in values for y in suites]
        
    def pop_cards(self):
        return self.deck.pop(np.random.randint(0, len(self.deck)))
    
    def distribute_cards_to_table(self, n_cards):
        cards = []
        for _ in range(n_cards):
            card = np.random.randint(0, len(self.deck))
            cards.append(self.deck.pop(card))
        return cards