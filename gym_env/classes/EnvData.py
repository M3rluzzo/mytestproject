from ....classes.enums import Action

class CommunityData:
    """Data available to everybody"""

    def __init__(self, num_players):
        """data"""
        self.current_player_position = [False] * num_players  # ix[0] = dealer
        self.stage = [False] * 4  # one hot: preflop, flop, turn, river
        self.community_pot = None
        self.current_round_pot = None
        self.active_players = [False] * num_players  # one hot encoded, 0 = dealer
        self.big_blind = 0
        self.small_blind = 0
        self.legal_moves = [0 for action in Action]


class StageData:
    """Preflop, flop, turn and river"""

    def __init__(self, num_players):
        """data"""
        self.calls = [False] * num_players  # ix[0] = dealer
        self.raises = [False] * num_players  # ix[0] = dealer
        self.min_call_at_action = [0] * num_players  # ix[0] = dealer
        self.contribution = [0] * num_players  # ix[0] = dealer
        self.stack_at_action = [0] * num_players  # ix[0] = dealer
        self.community_pot_at_action = [0] * num_players  # ix[0] = dealer


class PlayerData:
    "Player specific information"

    def __init__(self):
        """data"""
        self.position = None
        self.equity_to_river_alive = 0
        self.equity_to_river_2plr = 0
        self.equity_to_river_3plr = 0
        self.stack = None