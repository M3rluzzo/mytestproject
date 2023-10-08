"""Groupier functions"""
import logging
from gym import Env
from classes.PlayerManager import PlayerManager
from classes.CardManager import CardManager
from classes.EnvironmentManager import EnvironmentManager
from classes.RoundManager import RoundManager
from classes.models.CommunityData import CommunityData
from classes.models.PlayerData import PlayerData
from classes.models.StageData import StageData
from classes.models.enums import Action
# pylint: disable=import-outside-toplevel

log = logging.getLogger(__name__)

winner_in_episodes = []

class HoldemTable(Env):
    """Pokergame environment"""

    def __init__(self, initial_stack=100, small_blind=1, big_blind=2, ante=0, antes_timer=None, funds_plot=True, max_raising_rounds=2, use_cpp_montecarlo = False):
        """
        The table needs to be initialized once at the beginning

        Args:
            num_of_players (int): number of players that need to be added
            initial_stacks (real): initial stacks per placyer
            small_blind (real)
            big_blind (real)
            render (bool): render table after each move in graphical format
            funds_plot (bool): show plot of funds history at end of each episode
            max_raising_rounds (int): max raises per round per player

        """
        self.initial_stacks = initial_stack
        self.funds_plot = funds_plot
        
        self.action: Action = None
        self.round_manager: RoundManager = None  # cycle iterator
        self.player_data: PlayerData = PlayerData()
        self.player_manager: PlayerManager = PlayerManager(log)
        self.card_manager: CardManager = CardManager(log)
        self.stage_data: StageData = StageData(len(self.player_manager.players))
        self.community_data: CommunityData =  CommunityData(len(self.player_manager.players), small_blind, big_blind)
        
        self.environment_manager : EnvironmentManager = EnvironmentManager(log,
                                                                           self.player_manager, self.card_manager, self.round_manager,
                                                                           small_blind, big_blind, ante, antes_timer, max_raising_rounds)
        
        # calculator = cppimport.imp("tools.montecarlo_cpp.pymontecarlo")
        # self.environment_manager.data.get_equity = calculator.montecarlo
        if use_cpp_montecarlo:
            import cppimport
            calculator = cppimport.imp("tools.montecarlo_cpp.pymontecarlo")
            get_equity = calculator.montecarlo
        else:
            from tools.montecarlo_python import get_equity
        self.environment_manager.data.get_equity = get_equity

    def reset(self):
        """Reset after game over."""
        self.player_manager.reset()
        self.environment_manager.data.reset()
        self.environment_manager.round_manager = RoundManager(self.player_manager.players, dealer_idx=-1, max_steps_after_raiser=len(self.player_manager.players) - 1,
                                        max_steps_after_big_blind=len(self.player_manager.players))
        self.environment_manager.start_new_hand()
        self.environment_manager.update_environment()
        
        is_autoplay = self.environment_manager.is_agent_autoplay() and not self.environment_manager.done
        # auto play for agents where autoplay is set
        if is_autoplay:
            self.step('initial_player_autoplay')  # kick off the first action after bb by an autoplay agent
        return self.environment_manager.data.array_everything

    def step(self, action):  # pylint: disable=arguments-differ
        return self.environment_manager.perform_action_and_step_forward(action)
