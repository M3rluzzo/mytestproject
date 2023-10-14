from logging import Logger
from ....classes.enums import Stage
from ....classes.Deck import Deck
from .PlayerCycle import PlayerCycle
from .TableManager import TableManager
from .PlayerManager import PlayerManager
from .EnvData import StageData

class Dealer:
    def __init__(self, log, table):
        self.log: Logger = log
        self.table: TableManager = table
        self.deck: Deck = Deck()
        self.dealer_pos = None  # Posizione del dealer
        self.current_player = None  # Giocatore attuale
        self.player_cycle = None  # Iteratore cíclico dei giocatori
        self.stage = None  # Fase attuale del gioco (es. Flop, Turn, River)
    
    
    def reset(self, players):
        self.dealer_pos = 0
        self.player_cycle = PlayerCycle(self.log, players, dealer_idx=-1, max_steps_after_raiser=len(players) - 1,
                                        max_steps_after_big_blind=len(players))
    
    def get_alive_players(self, player_manager):
        players = player_manager.players
        player_alive = []
        self.player_cycle.new_hand_reset()
        for idx, player in enumerate(players):
            if player.stack > 0:
                player_alive.append(True)
            else:
                player_manager.player_status.append(False)
                self.player_cycle.deactivate_player(idx)

        return sum(player_alive)
    
    def start_new_hand(self, player_manager: PlayerManager):
        n_players = len(player_manager.players)
        self.table.cards = []
        self.deck.create_card_deck()
        self.stage = Stage.PREFLOP

        # preflop round1,2, flop>: round 1,2, turn etc...
        player_manager.stage_data = [StageData(n_players) for _ in range(8)]
        
    def next_dealer(self):
        self.dealer_pos = self.player_cycle.next_dealer().seat
        
    def distribute_cards(self, players):
        self.log.info(f"Dealer is at position {self.dealer_pos}")
        for player in players:
            player.cards = []
            if player.stack <= 0:
                continue
            for _ in range(2):
                player.cards.append(self.deck.pop_cards())
            self.log.info(f"Player {player.seat} got {player.cards} and ${player.stack}")
        
    def end_round(self, n_players):
        """End of preflop, flop, turn or river"""
        self.table.close_round(n_players)
        if self.stage == Stage.PREFLOP:
            self.stage = Stage.FLOP
            self.table.cards.extend(self.deck.distribute_cards_to_table(3))
        elif self.stage == Stage.FLOP:
            self.stage = Stage.TURN
            self.table.cards.extend(self.deck.distribute_cards_to_table(1))
        elif self.stage == Stage.TURN:
            self.stage = Stage.RIVER
            self.table.cards.extend(self.deck.distribute_cards_to_table(1))
        elif self.stage == Stage.RIVER:
            self.stage = Stage.SHOWDOWN
        if self.stage is not Stage.RIVER:
            self.log.info(f"Cards on table: {self.table.cards}")
        self.log.info("--------------------------------")
        self.log.info(f"===ROUND: {self.stage} ===")
        self.table.clean_up_pots(n_players)
        