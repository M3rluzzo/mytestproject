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
    
# state = NoLimitTexasHoldem.create_state(
#      (
#          Automation.ANTE_POSTING,
#          Automation.BET_COLLECTION,
#          Automation.BLIND_OR_STRADDLE_POSTING,
#          Automation.CARD_BURNING,
#          Automation.HOLE_CARDS_SHOWING_OR_MUCKING,
#          Automation.HAND_KILLING,
#          Automation.CHIPS_PUSHING,
#          Automation.CHIPS_PULLING,
#      ),
#      True,
#      3000,
#      {-1: 3000},
#      3000,
#      (495000, 232000, 362000, 403000, 301000, 204000),
#      6,
# )
# # Below shows the pre-flop dealings and actions.
 

# state.check_or_call()  # Badziakouski
# state.check_or_call()  # Zhong
# state.complete_bet_or_raise_to(35000)  # Xuan
# state.fold()  # Jun
# state.complete_bet_or_raise_to(298000)  # Phua

# state.fold()  # Koon
# state.fold()  # Badziakouski
# state.fold()  # Zhong
# state.check_or_call()  # Xuan
# state.deal_board('9h6cKc')
# state.deal_board('Jh')
# state.deal_board('Ts')
# state.stacks

from pokerkit import Poker, NoLimitTexasHoldem, Automation
from random import choice
class Player:
    def __init__(self, name, starting_stack):
        self.name = name
        self.starting_stack = starting_stack

class SpinNGoManager:
    @property
    def player_stacks(self):
        return tuple(x.starting_stack for x in self.players)
    
    def __init__(self, big_blind, small_blind, antes):
        self.state = None
        self.blinds = (small_blind, big_blind)
        self.antes = antes
        self.players = [Player("Badziakouski", 495000),
                        Player("Zhong", 232000),
                        Player("Xuan", 362000),
                        Player("Jun", 403000),
                        Player("Phua", 301000),
                        Player("Koon", 204000)]
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
        

        actions = ['check_or_call', 'complete_bet_or_raise_to', 'fold']
        for _ in range(3):
            action = choice(actions)
            print(action)
            if action == 'check_or_call':
                self.state.check_or_call()
            elif action == 'complete_bet_or_raise_to':
                self.state.complete_bet_or_raise_to(choice(range(1000, 50000)))
            else:
                self.state.fold()

        # Simula il board
        self.state.deal_board('9h6cKc')
        self.state.deal_board('Jh')
        self.state.deal_board('Ts')

    def run_game(self):
        # Distribuisci le hole cards a tutti i giocatori (attualmente sono hardcodate, poi saranno random)
        test_cards = ['Th8h', 'QsJd', 'QhQd', '8d7c', 'KhKs', '8c7h']
        for hole_cards in test_cards:
            self.state.deal_hole(hole_cards)
        
        self.state.check_or_call()  # Badziakouski
        self.state.check_or_call()  # Zhong
        self.state.complete_bet_or_raise_to(35000)  # Xuan
        self.state.fold()  # Jun
        self.state.complete_bet_or_raise_to(298000)  # Phua
        self.state.fold()  # Koon
        self.state.fold()  # Badziakouski
        self.state.fold()  # Zhong
        self.state.check_or_call()  # Xuan
        
        self.state.deal_board('9h6cKc')
        self.state.deal_board('Jh')
        self.state.deal_board('Ts')


if __name__ == "__main__":
    manager = SpinNGoManager(3000, 1500, 3000)
    manager.run_game()
