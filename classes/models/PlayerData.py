class PlayerData:
    "Player specific information"
    def __init__(self):
        self.position = None
        self.equity_to_river_alive = 0
        self.equity_to_river_2plr = 0
        self.equity_to_river_3plr = 0
        self.stack = None