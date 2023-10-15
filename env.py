import logging
from pokerkit import NoLimitTexasHoldem, Automation

# Impostiamo il logging per tenere traccia dell'esecuzione
logging.basicConfig(level=logging.DEBUG)

class PokerEnv:
  def __init__(self, num_players, cash_game=True):

    # Parametrizziamo il numero di giocatori
    self.num_players = num_players

    # Impostiamo se è un cash game o uno spin-n-go
    self.cash_game = cash_game

    # Inizializziamo lo stato della partita
    self.state = NoLimitTexasHoldem.create_state(
      automations=self._get_automations(), 
      big_blind_ante=True,
      ante=None if cash_game else self._get_buyin(), 
      blinds=self._get_blinds(),
      number_of_players=num_players,
      starting_stacks=self._get_starting_stacks()
    )

  def _get_automations(self):
    # Automatizziamo tutto tranne le azioni dei giocatori
    return (Automation.ANTE_POSTING, Automation.BET_COLLECTION, 
            Automation.BLIND_OR_STRADDLE_POSTING, Automation.CARD_BURNING, 
            Automation.HOLE_CARDS_SHOWING_OR_MUCKING, 
            Automation.HAND_KILLING, Automation.CHIPS_PUSHING, 
            Automation.CHIPS_PULLING)

  def _get_buyin(self):
    # Impostiamo il buyin per gli spin-n-go a 1000
    return 1000

  def _get_blinds(self):
    # Blinds standard per cash games
    if self.cash_game:
      return (100, 200)
    # Blinds ridotti per spin-n-go
    else: 
      return (50, 100)

  def _get_starting_stacks(self):
    # Stack standard per cash games
    if self.cash_game:
      return [1000] * self.num_players
    # Stack iniziale pari al buyin per spin-n-go
    else:
      return [1000] * min(3, self.num_players)

  def reset(self):
    logging.debug("Resetting the game state")
    self.state = NoLimitTexasHoldem.create_state(
      automations=self._get_automations(),
      big_blind_ante=True,
      ante=None if self.cash_game else self._get_buyin(),
      blinds=self._get_blinds(), 
      number_of_players=self.num_players,
      starting_stacks=self._get_starting_stacks()
    )
    return self._get_observation()

  def step(self, action):
    logging.debug(f"Applying action: {action}")

    if self.state.can_fold():
      self.state.fold()
    elif self.state.can_check_or_call():    
      self.state.check_or_call()  
    elif self.state.can_complete_bet_or_raise_to():
      self.state.complete_bet_or_raise_to(action)

    reward = self._get_reward()
    observation = self._get_observation()
    done = self.state.is_terminal()

    logging.debug(f"Observation: {observation}")
    logging.debug(f"Reward: {reward}")
    logging.debug(f"Game over: {done}")

    return observation, reward, done, {}

  def _get_observation(self):
    position = self.state.actor_index
    cards = self.state.hole_cards[position]
    amount_to_call = self.state.checking_or_calling_amount
    return [position, cards, amount_to_call]

  def _get_reward(self):
    return self.state.stacks[self.state.actor_index]
