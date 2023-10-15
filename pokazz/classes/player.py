class Player:
   def __init__(self, starting_stack):
      self.hand = None
      self.starting_stack = starting_stack
      self.current_stack = starting_stack
   
   def reset(self):
      self.hand = None
      self.current_stack = self.starting_stack

class PlayerManager:
   def __init__(self, players):
      self.players = players
      self.current_player = None
      
   def add_player(self, player:Player):
      self.players.append(player)
      
   def reset(self):
      for p in self.players:
         p.reset()