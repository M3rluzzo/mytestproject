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
    """Create a no-limit Texas hold'em game.

        Below shows the first televised million dollar pot between
        Tom Dwan and Phil Ivey.

        Link: https://youtu.be/GnxFohpljqM

        >>> state = NoLimitTexasHoldem.create_state(
        ...     (
        ...         Automation.ANTE_POSTING,
        ...         Automation.BET_COLLECTION,
        ...         Automation.BLIND_OR_STRADDLE_POSTING,
        ...         Automation.CARD_BURNING,
        ...         Automation.HOLE_CARDS_SHOWING_OR_MUCKING,
        ...         Automation.HAND_KILLING,
        ...         Automation.CHIPS_PUSHING,
        ...         Automation.CHIPS_PULLING,
        ...     ),
        ...     True,
        ...     500,
        ...     (1000, 2000),
        ...     2000,
        ...     (1125600, 2000000, 553500),
        ...     3,
        ... )

        Below shows the pre-flop dealings and actions.

        >>> state.deal_hole('Ac2d')  # Ivey
        HoleDealing(player_index=0, cards=(Ac, 2d), statuses=(False, False))
        >>> state.deal_hole('5h7s')  # Antonius*
        HoleDealing(player_index=1, cards=(5h, 7s), statuses=(False, False))
        >>> state.deal_hole('7h6h')  # Dwan
        HoleDealing(player_index=2, cards=(7h, 6h), statuses=(False, False))

        >>> state.complete_bet_or_raise_to(7000)  # Dwan
        CompletionBettingOrRaisingTo(player_index=2, amount=7000)
        >>> state.complete_bet_or_raise_to(23000)  # Ivey
        CompletionBettingOrRaisingTo(player_index=0, amount=23000)
        >>> state.fold()  # Antonius
        Folding(player_index=1)
        >>> state.check_or_call()  # Dwan
        CheckingOrCalling(player_index=2, amount=16000)

        Below shows the flop dealing and actions.

        >>> state.deal_board('Jc3d5c')
        BoardDealing(cards=(Jc, 3d, 5c))

        >>> state.complete_bet_or_raise_to(35000)  # Ivey
        CompletionBettingOrRaisingTo(player_index=0, amount=35000)
        >>> state.check_or_call()  # Dwan
        CheckingOrCalling(player_index=2, amount=35000)

        Below shows the turn dealing and actions.

        >>> state.deal_board('4h')
        BoardDealing(cards=(4h,))

        >>> state.complete_bet_or_raise_to(90000)  # Ivey
        CompletionBettingOrRaisingTo(player_index=0, amount=90000)
        >>> state.complete_bet_or_raise_to(232600)  # Dwan
        CompletionBettingOrRaisingTo(player_index=2, amount=232600)
        >>> state.complete_bet_or_raise_to(1067100)  # Ivey
        CompletionBettingOrRaisingTo(player_index=0, amount=1067100)
        >>> state.check_or_call()  # Dwan
        CheckingOrCalling(player_index=2, amount=262400)

        Below shows the river dealing.

        >>> state.deal_board('Jh')
        BoardDealing(cards=(Jh,))

        Below show the final stacks.

        >>> state.stacks
        [572100, 1997500, 1109500]

        :param antes: The antes.
        :param blinds_or_straddles: The blinds or straddles.
        :param min_bet: The min bet.
        :param starting_stacks: The starting stacks.
        :param player_count: The number of players.
        :return: The created state.
        """    
    manager = SpinNGoManager(2000, 1000, 500, [
                                                Player("Dwan", 1125600),
                                                Player("Ivey", 2000000),
                                                Player("Antonius", 553500)
                                                ]
                             )
    manager.run_game()
