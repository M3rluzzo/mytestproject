from enum import Enum
class Action(Enum):
    """Allowed actions"""

    FOLD = 0
    CHECK = 1
    CALL = 2
    RAISE_3BB = 3
    RAISE_HALF_POT = 3
    RAISE_POT = 4
    RAISE_2POT = 5
    ALL_IN = 6
    SMALL_BLIND = 7
    BIG_BLIND = 8

class Stage(Enum):
    """Allowed actions"""

    PREFLOP = 0
    FLOP = 1
    TURN = 2
    RIVER = 3
    END_HIDDEN = 4
    SHOWDOWN = 5

from pokerkit import NoLimitTexasHoldem, Automation
from random import choice
class Player:
    def __init__(self, name, starting_stack):
        self.name = name
        self.starting_stack = starting_stack

class SpinNGoManager:
    @property
    def player_stacks(self):
        return tuple(x.starting_stack for x in self.players)
    
    def __init__(self, big_blind, small_blind, antes, players):
        self.state = None
        self.blinds = (small_blind, big_blind)
        self.antes = antes
        self.players = players
        self.reset_game()

    def reset_game(self):
        self.state = NoLimitTexasHoldem.create_state(
            (
                Automation.ANTE_POSTING,
                Automation.BET_COLLECTION,
                Automation.BLIND_OR_STRADDLE_POSTING,
                Automation.CARD_BURNING,
                Automation.HOLE_CARDS_SHOWING_OR_MUCKING,
                Automation.HAND_KILLING,
                Automation.CHIPS_PUSHING,
                Automation.CHIPS_PULLING,
            ),
            True,
            self.antes,
            self.blinds,
            self.blinds[1],
            self.player_stacks,
            len(self.players),
        )

    def simulate_action(self, action: Action):
        # TODO: Implementare logica

    def run_game(self):
        # Distribuisci le hole cards a tutti i giocatori (attualmente sono hardcodate, poi saranno random)
        test_cards = ['Ac2d', '5h7s', '7h6h']
        for hole_cards in test_cards:
            self.state.deal_hole(hole_cards)
        
        self.state.complete_bet_or_raise_to(7000)  # Dwan
        self.state.complete_bet_or_raise_to(23000)  # Ivey
        self.state.fold()  # Antonius
        self.state.check_or_call()  # Dwan
        # Flop dealing
        self.state.deal_board('Jc3d5c')

        self.state.complete_bet_or_raise_to(35000)  # Ivey
        self.state.check_or_call()  # Dwan
        # Turn dealing
        self.state.deal_board('4h')
        
        self.state.complete_bet_or_raise_to(90000)  # Ivey
        self.state.complete_bet_or_raise_to(232600)  # Dwan
        self.state.complete_bet_or_raise_to(1067100)  # Ivey
        self.state.check_or_call()  # Dwan
        # River dealing
        self.state.deal_board('Jh')

if __name__ == "__main__":
    manager = SpinNGoManager(2000, 1000, 500, [
                                                Player("Dwan", 1125600),
                                                Player("Ivey", 2000000),
                                                Player("Antonius", 553500)
                                                ]
                             )
    manager.run_game()
