import numpy as np
from logging import Logger

class CardManager:
  
    def __init__(self, log : Logger):
        self.log = log
        self.table_cards = None
        
        values = "23456789TJQKA"
        suites = "CDHS"
        self.deck = [x + y for x in values for y in suites]

    def distribute_cards(self, players):
        for player in players:
            player.cards = []
            if player.stack <= 0:
                continue
            for _ in range(2):
                card = np.random.randint(0, len(self.deck))
                player.cards.append(self.deck.pop(card))
            self.log.info(f"Player {player.seat} got {player.cards} and ${player.stack}")
            
    def distribute_cards_to_table(self, amount_of_cards):
        if amount_of_cards < 1:
            return
        for _ in range(amount_of_cards):
            card = np.random.randint(0, len(self.deck))
            self.table_cards.append(self.deck.pop(card))
        self.log.info(f"Cards on table: {self.table_cards}")
    
    def new_card_deck(self):
        values = "23456789TJQKA"
        suites = "CDHS"
        self.deck = []
        self.table_cards = []
        _ = [self.deck.append(x + y) for x in values for y in suites]
        