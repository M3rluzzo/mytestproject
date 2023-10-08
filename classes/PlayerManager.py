from logging import Logger
from .RoundManager import RoundManager
from .models.PlayerShell import PlayerShell
import pandas as pd

class PlayerManager:
    def __init__(self, log:Logger):
        self.log = log
        self.players = []
        self.player_status = []  # one hot encoded
        self.funds_history = None
        self.num_of_players = 0
    
    @property
    def player_pots(self):
        return [player.pot for player in self.players]

    @property
    def max_player_pot(self):
        return [player.pot for player in self.players]

    @property   
    def player_max_wins(self):
        return [player.max_win for player in self.players]
    
    def set_all_pots(self, value):
        for player in self.players:
            player.pot = value
    
    def set_all_action_in_stage(self, value):
        for player in self.players:
            player.last_action_in_stage = value
    
    def set_all_max_wins(self, value):
        for player in self.players:
            player.max_win = value

    def add_player(self, agent):
        """Add a player to the table. Has to happen at the very beginning"""
        self.num_of_players += 1
        player = PlayerShell(stack_size=self.initial_stacks, name=agent.name)
        player.agent_obj = agent
        player.seat = len(self.players)  # assign next seat number to player
        player.stack = self.initial_stacks
        self.players.append(player)
        self.player_status = [True] * len(self.players)
        self.player_pots = [0] * len(self.players)
            
    def add_player(self, agent, stack_size):
        """Add a player to the table. Has to happen at the very beginning"""
        self.num_of_players += 1
        player = PlayerShell(stack_size=stack_size, name=agent.name)
        player.agent_obj = agent
        player.seat = len(self.players)
        
        self.players.append(player)
        
        self.set_all_pots(0)
        
        self.player_status = [True] * len(self.players)
    
    def check_alive_players(self, _round_manager:RoundManager):
        player_alive = []
        _round_manager.new_hand_reset()
        for idx, player in enumerate(self.players):
            if player.stack > 0:
                player_alive.append(True)
            else:
                self.player_status.append(False)
                _round_manager.deactivate_player(idx)
        return sum(player_alive)
    
    def collect_funds_history(self):
        player_names = [f"{i} - {player.name}" for i, player in enumerate(self.players)]
        self.funds_history.columns = player_names
        self.log.info(self.funds_history)
    
    def reset(self, stack = None):
        self.funds_history = pd.DataFrame()
        for player in self.players:
            if (stack is None):
                stack = player.initial_stack
            player.stack = stack
            player.cards = []