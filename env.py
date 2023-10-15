import logging
from pokerkit import NoLimitTexasHoldem, Automation
from enum import Enum

# Impostiamo il logging per tenere traccia dell'esecuzione
logging.basicConfig(level=logging.DEBUG)

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
    BIG_BLIND = 8,
    RAISE = 9


class Stage(Enum):
    """Allowed actions"""

    PREFLOP = 0
    FLOP = 1
    TURN = 2
    RIVER = 3
    END_HIDDEN = 4
    SHOWDOWN = 5

class PokerEnv:
    def __init__(self, num_players, starting_stack, small_blind, big_blind, ante, starting_stacks=None, cash_game=True):
        self.num_players = num_players
        self.cash_game = cash_game
        self.starting_stack = starting_stack
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.ante = ante
        self.starting_stacks = starting_stacks if starting_stacks is not None else self._get_starting_stacks()
        self._init_new_game_state()
    
    def deal_cards(self, hole_cards):
        for hole in hole_cards:
            self.state.deal_hole(hole)
    
    def deal_board(self, board_cards):
        self.state.deal_board(board_cards)
        
    def take_action(self, action, value = None):
        if action == Action.RAISE:
            self.state.complete_bet_or_raise_to(value)
        elif action in [Action.CALL, Action.CHECK]:
            self.state.check_or_call()
        elif action is Action.FOLD:
            self.state.fold()
    
    def _init_new_game_state(self):
        logging.debug("Init new game state")
        self.state = NoLimitTexasHoldem.create_state(
            automations=self._get_automations(),
            ante_trimming_status=True, # False for big blind ante, True otherwise
            antes=self.ante,
            min_bet=self.big_blind,
            blinds_or_straddles=(self.small_blind, self.big_blind),
            player_count=self.num_players,
            starting_stacks=self.starting_stacks
        )

    def _get_automations(self):
        return (Automation.ANTE_POSTING, Automation.BET_COLLECTION,
            Automation.BLIND_OR_STRADDLE_POSTING, Automation.CARD_BURNING,
            Automation.HOLE_CARDS_SHOWING_OR_MUCKING,
            Automation.HAND_KILLING, Automation.CHIPS_PUSHING,
            Automation.CHIPS_PULLING)
    
    def _get_starting_stacks(self):
        return tuple([self.starting_stack] * self.num_players)

    def reset(self):
        logging.debug("Resetting the game state")
        self._init_new_game_state()
        return self._get_observation()

    def step(self, action: Action, value = None):
        logging.debug(f"Applying action: {action}")

        if action == Action.RAISE:
            self.state.complete_bet_or_raise_to(value)
        elif action in [Action.CALL, Action.CHECK]:
            self.state.check_or_call()
        elif action is Action.FOLD:
            self.state.fold()

        reward = self._get_reward()
        # observation = self._get_observation()
        observation = None

        logging.debug(f"Observation: {observation}")
        logging.debug(f"Reward: {reward}")

        return observation, reward, {}

    def _get_observation(self):
        position = self.state.actor_index
        # print(position)
        cards = self.state.hole_cards[position]
        amount_to_call = self.state.checking_or_calling_amount
        return [position, cards, amount_to_call]

    def _get_reward(self):
        print(self.state.actor_index)
        return self.state.stacks[self.state.actor_index]
