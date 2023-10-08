from .PlayerManager import PlayerManager
from .CardManager import CardManager
from .EnvironmentManager import EnvironmentManager
from .RoundManager import RoundManager
from logging import Logger

class GameManager:
    def __init__(self, log:Logger, player_manager:PlayerManager, stack, small_blind, big_blind, max_raising_rounds, ante_amount=0, antes_timer=0):
        self.log = log
        self.initial_stack = stack
        self.player_manager = player_manager
        
        self.card_manager = CardManager(self.log)
        self.environment_manager : EnvironmentManager = EnvironmentManager(self.log, small_blind, big_blind, ante_amount, antes_timer, max_raising_rounds)
        self.round_manager = RoundManager(self.log)

    
    
    def reset(self):
        self.environment_manager.data.reset()
        self.round_manager = RoundManager(self.player_manager.players, dealer_idx=-1, max_steps_after_raiser=len(self.player_manager.players) - 1,
                                        max_steps_after_big_blind=len(self.player_manager.players))
        self.environment_manager.round_manager = self.round_manager
        self.environment_manager.start_new_hand()
        self.environment_manager.update_environment()
        
        return self.environment_manager.is_agent_autoplay() and not self.environment_manager.done
    
    