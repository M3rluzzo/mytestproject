from logging import Logger
from .CommunityData import CommunityData
from .PlayerData import PlayerData
from .StageData import StageData
from .enums import Action, Stage
from tools.helper import flatten
import numpy as np

class EnvironmentData():
    def __init__(self, log, players, small_blind, big_blind, ante, antes_timer, max_raising_rounds):
        self.log: Logger = log
        self.observation = None
        self.legal_moves = None
        self.array_everything = None
        self.reward = None
        self.info = None
        self.current_round_pot = None
        self.min_call = None
        self.stage = None
        
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.ante = ante
        self.antes_timer = antes_timer
        
        self.max_round_raising = max_raising_rounds
        self.last_player_pot = None
        self.played_in_round = None
        self.first_action_for_hand = None
        
        self.dealer_pos = None
        self.last_caller = None
        self.last_raiser = None
        self.raisers = None
        self.callers = None
        self.community_pot = None
        
        self.current_player = None
        
        # calculator = cppimport.imp("tools.montecarlo_cpp.pymontecarlo")
        # self.get_equity = calculator.montecarlo
        self.players = players
        self.community_data: CommunityData =  CommunityData(len(self.players), small_blind, big_blind)
        self.player_data: PlayerData = PlayerData()
        self.stage_data: StageData = StageData(len(self.players))
        
    def prepare_data(self, player_pots, sum_player_alive, table_cards):
        self.observation = None
        self.reward = 0
        self.info = None
        num_players = len(self.players)
        
        # Community
        self.community_data = CommunityData(num_players, self.small_blind, self.big_blind)
        self.community_data.community_pot = self.community_pot / (self.big_blind * 100)
        self.community_data.current_round_pot = self.current_round_pot / (self.big_blind * 100)
        self.community_data.stage[np.minimum(self.stage.value, 3)] = 1  # pylint: disable= invalid-sequence-index
        self.community_data.legal_moves = [action in self.legal_moves for action in Action]
        
        # Player
        self.player_data = PlayerData()
        self.player_data.stack = [player.stack / (self.big_blind * 100) for player in self.players]
        self.current_player.equity_alive = self.get_equity(set(self.current_player.cards), set(table_cards),
                                                           sum_player_alive, 1000)
        self.player_data.equity_to_river_alive = self.current_player.equity_alive
        
        arr1 = np.array(list(flatten(self.player_data.__dict__.values())))
        arr2 = np.array(list(flatten(self.community_data.__dict__.values())))
        arr3 = np.array([list(flatten(sd.__dict__.values())) for sd in self.stage_data]).flatten()
        # arr_legal_only = np.array(self.community_data.legal_moves).flatten()
        self.array_everything = np.concatenate([arr1, arr2, arr3]).flatten()

        self.observation = self.array_everything
        self.set_legal_moves(player_pots)

        self.info = {'player_data': self.player_data.__dict__,
                     'community_data': self.community_data.__dict__,
                     'stage_data': [stage.__dict__ for stage in self.stage_data],
                     'legal_moves': self.legal_moves}

        self.observation_space = self.array_everything.shape
        
    def set_legal_moves(self, player_pots):
        """Determine what moves are allowed in the current state"""
        self.legal_moves = []
        current_pot = self.current_player.pot
        if current_pot == max(player_pots):
            self.legal_moves.append(Action.CHECK)
        else:
            self.legal_moves.append(Action.CALL)
            self.legal_moves.append(Action.FOLD)

        if self.current_player.stack >= 3 * self.big_blind - current_pot:
            self.legal_moves.append(Action.RAISE_3BB)
            if self.current_player.stack >= ((self.community_pot + self.current_round_pot) / 2) >= self.min_call:
                self.legal_moves.append(Action.RAISE_HALF_POT)
            if self.current_player.stack >= (self.community_pot + self.current_round_pot) >= self.min_call:
                self.legal_moves.append(Action.RAISE_POT)
            if self.current_player.stack >= ((self.community_pot + self.current_round_pot) * 2) >= self.min_call:
                self.legal_moves.append(Action.RAISE_2POT)
            if self.current_player.stack > 0:
                self.legal_moves.append(Action.ALL_IN)
        self.log.debug(f"Community+current round pot pot: {self.community_pot + self.current_round_pot}")
        
    def reset(self):
        self.observation = None
        self.reward = None
        self.info = None
        self.done = None
        self.dealer_pos = 0
        self.first_action_for_hand = [True] * len(self.players)
    
    def new_round(self, new_dealer_pos):
        self.stage = Stage.PREFLOP
        self.stage_data = [StageData(len(self.players)) for _ in range(8)]
        
        self.community_pot = 0
        self.last_player_pot = 0
        self.played_in_round = 0
        self.first_action_for_hand = [True] * len(self.players)
        self.dealer_pos = new_dealer_pos
        self.log.info(f"Dealer is at position {self.dealer_pos}")
    
    def initialize(self):
        self.last_caller = None
        self.last_raiser = None
        self.raisers = []
        self.callers = []
        self.min_call = 0
    
    def next_stage(self):
        n_cards = 0
        if self.stage == Stage.PREFLOP:
            self.stage = Stage.FLOP
            n_cards = 3
        elif self.stage == Stage.FLOP:
            self.stage = Stage.TURN
            n_cards = 1
        elif self.stage == Stage.TURN:
            self.stage = Stage.RIVER
            n_cards = 1
        elif self.stage == Stage.RIVER:
            self.stage = Stage.SHOWDOWN
        return n_cards
    
    def illegal_move(self, action):
        self.log.warning(f"{action} is an Illegal move, try again. Currently allowed: {self.legal_moves}")
        self.reward = self.illegal_move_reward