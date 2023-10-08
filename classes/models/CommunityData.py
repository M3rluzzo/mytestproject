from .enums import Action
from .StageData import StageData

class CommunityData:
    """Data available to everybody"""

    def __init__(self, num_players, small_blind, big_blind):
        """data"""
        self.current_player_position = [False] * num_players  # ix[0] = dealer
        self.stage = [False] * 4  # one hot: preflop, flop, turn, river
        self.community_pot = None
        self.current_round_pot = None
        self.active_players = [False] * num_players  # one hot encoded, 0 = dealer
        self.big_blind = big_blind
        self.small_blind = small_blind
        self.legal_moves = [0 for action in Action]