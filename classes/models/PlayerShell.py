class PlayerShell:
    """Player shell"""

    def __init__(self, stack_size, name):
        """Initiaization of an agent"""
        self.stack = stack_size
        self.initial_stack = stack_size
        self.seat = None
        self.equity_alive = 0
        self.actions = []
        self.last_action_in_stage = ''
        self.temp_stack = []
        self.name = name
        self.agent_obj = None