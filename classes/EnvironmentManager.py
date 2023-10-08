from logging import Logger
import numpy as np
import pandas as pd
from .CardManager import CardManager
from .models.StageData import StageData
from .RoundManager import RoundManager
from .models.EnvironmentData import EnvironmentData
from .models.enums import Action, Stage
from gym.spaces import Discrete
from .PlayerManager import PlayerManager
from tools.hand_evaluator import get_winner
winner_in_episodes = []
class EnvironmentManager:
    def __init__(self, log, player_manager, card_manager, round_manager, small_blind, big_blind, ante, antes_timer, max_raising_rounds):
        self.log: Logger = log
        self.second_round = False
        self.action_space = Discrete(len(Action) - 2)
        self.done = False
        self.illegal_move_reward = -1
        self.winner_ix = None
        self.acting_agent = None        
        self.player_manager: PlayerManager = player_manager
        self.round_manager: RoundManager = round_manager
        self.card_manager: CardManager = card_manager
        self.data: EnvironmentData = EnvironmentData(log,
            self.player_manager.players, small_blind, big_blind, ante, antes_timer, max_raising_rounds)    
    def start_new_round(self):
        """A new round (flop, turn, river) is initiated"""
        self.data.initialize()
        self.player_manager.set_all_action_in_stage('')
        self.round_manager.new_round_reset()
        if self.data.stage == Stage.PREFLOP:
            self.log.info("")
            self.log.info("===Round: Stage: PREFLOP")
            # max steps total will be adjusted again at bb
            self.round_manager.max_steps_total = len(self.player_manager.players) * self.data.max_round_raising + 2
            for action in [Action.SMALL_BLIND, Action.BIG_BLIND]:
                self.next_player()
                self.handle_player_action(action)
            self.next_player()
        elif self.data.stage in [Stage.FLOP, Stage.TURN, Stage.RIVER]:
            self.round_manager.max_steps_total = len(self.player_manager.players) * self.data.max_round_raising
            self.next_player()
        elif self.data.stage == Stage.SHOWDOWN:
            self.log.info("Showdown")
        else:
            raise RuntimeError()
    def next_player(self):
        """Move to the next player"""
        self.data.current_player = self.round_manager.next_player()
        if not self.data.current_player:
            if sum(self.round_manager.alive) < 2:
                self.log.info("Only one player remaining in round")
                self.data.stage = Stage.END_HIDDEN
            else:
                self.log.info("End round - no current player returned")
                self.end_round()
                # todo: in some cases no new round should be initialized bc only one player is playing only it seems
                self.start_new_round()
        elif self.data.current_player in ['max_steps_total', 'max_steps_after_raiser']:
            self.log.debug(self.data.current_player)
            self.log.info("End of round ")
            self.end_round()
            return
    def end_round(self):
        """End of preflop, flop, turn or river"""
        self.close_round()
        self.card_manager.distribute_cards_to_table(self.data.next_stage())
        self.log.info(f"=== ROUND: {self.data.stage} ===")
        self.reset_pots()
    def reset_for_new_round(self):
        self.player_manager.set_all_pots(0) 
        self.player_manager.set_all_max_wins(0)
        self.data.new_round(self.round_manager.next_dealer().seat)
    def perform_step(self, action):
        self.handle_player_action(action)
        self.next_player()
        if self.data.stage in [Stage.END_HIDDEN, Stage.SHOWDOWN]:
            self.end_hand()
            self.start_new_hand()
        self.update_environment()
    def end_hand(self):
        self.reset_pots()
        self.winner_ix = self.get_winner()
        self.award_winner(self.winner_ix)
    def get_winner(self):
        """Determine which player has won the hand"""
        potential_winners = self.round_manager.get_potential_winners()

        potential_winner_idx = [i for i, potential_winner in enumerate(potential_winners) if potential_winner]
        if sum(potential_winners) == 1:
            winner_ix = [i for i, active in enumerate(potential_winners) if active][0]
            winning_card_type = 'Only remaining player in round'

        else:
            assert self.data.stage == Stage.SHOWDOWN
            remaining_player_winner_ix, winning_card_type = get_winner([player.cards
                                                                        for ix, player in enumerate(self.player_manager.players) if
                                                                        potential_winners[ix]],
                                                                       self.card_manager.table_cards)
            winner_ix = potential_winner_idx[remaining_player_winner_ix]
        self.log.info(f"Player {winner_ix} won: {winning_card_type}")
        return winner_ix
    def award_winner(self, winner_ix):
        """Hand the pot to the winner and handle side pots"""
        max_wins = self.player_manager.player_max_wins
        max_win_per_player_for_winner = max_wins[winner_ix]
        total_winnings = sum(np.minimum(max_win_per_player_for_winner, max_wins))
        remains = np.maximum(0, np.array(max_wins) - max_win_per_player_for_winner)  # to be returned

        self.player_manager.players[winner_ix].stack += total_winnings
        self.winner_ix = winner_ix
        if total_winnings < sum(max_wins):
            self.log.info("Returning side pots")
            for i, player in enumerate(self.player_manager.players):
                player.stack += remains[i]
    def start_new_hand(self):
        """Deal new cards to players and reset table states."""
        """Keep track of player funds history"""
        funds_dict = {i: player.stack for i, player in enumerate(self.player_manager.players)}
        self.player_manager.funds_history = pd.concat([self.player_manager.funds_history, pd.DataFrame(funds_dict, index=[0])])

        if self.check_game_over():
            return

        self.log.info("")
        self.log.info("++++++++++++++++++ Starting new hand ++++++++++++++++++")
        
        self.card_manager.new_card_deck()
        self.data.stage = Stage.PREFLOP

        # preflop round1,2, flop>: round 1,2, turn etc...
        self.data.stage_data = [StageData(len(self.player_manager.players)) for _ in range(8)]

        # pots
        self.player_manager.set_all_pots(0) 
        self.player_manager.set_all_max_wins(0)
        self.data.community_pot = 0
        self.data.current_round_pot = 0
        
        self.data.last_player_pot = 0
        self.data.played_in_round = 0
        self.data.first_action_for_hand = [True] * len(self.player_manager.players)

        for player in self.player_manager.players:
            player.cards = []

        self.data.dealer_pos = self.round_manager.next_dealer().seat

        self.log.info(f"Dealer is at position {self.data.dealer_pos}")
        self.card_manager.distribute_cards(self.player_manager.players)
        self.start_new_round()
    def check_game_over(self):
        """Check if only one player has money left"""
        remaining_players = self.player_manager.check_alive_players(self.round_manager)
        if remaining_players < 2:
            self.game_over()
            return True
        return False
    def game_over(self):
        """End of an episode."""
        self.log.info("Game over.")
        self.done = True
        player_names = [f"{i} - {player.name}" for i, player in enumerate(self.player_manager.players)]
        self.player_manager.funds_history.columns = player_names
        self.log.info(self.player_manager.funds_history)
        winner_in_episodes.append(self.winner_ix)
        league_table = pd.Series(winner_in_episodes).value_counts()
        best_player = league_table.index[0]
        self.log.info(league_table)
        self.log.info(f"Best Player: {best_player}")
    def close_round(self):
        """Put player_pots into community pots"""
        self.data.community_pot += sum(self.player_manager.player_pots)
        self.player_manager.set_all_pots(0)
        self.data.played_in_round = 0
    def handle_player_action(self, action):  # pylint: disable=too-many-statements
        """Process the decisions that have been made by an agent."""
        if action not in [Action.SMALL_BLIND, Action.BIG_BLIND]:
            assert action in set(self.data.legal_moves), "Illegal decision"
        if action == Action.FOLD:
            self.round_manager.deactivate_current()
            self.round_manager.mark_folder()
        else:
            if action == Action.CALL:
                contribution = min(self.data.min_call - self.data.current_player.pot,
                                   self.data.current_player.stack)
                self.data.callers.append(self.data.current_player.seat)
                self.data.last_caller = self.data.current_player.seat
            # verify the player has enough in his stack
            elif action == Action.CHECK:
                contribution = 0
                self.round_manager.mark_checker()
            elif action == Action.RAISE_3BB:
                contribution = 3 * self.data.big_blind - self.data.current_player.pot
                self.data.raisers.append(self.data.current_player.seat)
            elif action == Action.RAISE_HALF_POT:
                contribution = (self.data.community_pot + self.data.current_round_pot) / 2
                self.data.raisers.append(self.data.current_player.seat)
            elif action == Action.RAISE_POT:
                contribution = (self.data.community_pot + self.data.current_round_pot)
                self.data.raisers.append(self.data.current_player.seat)
            elif action == Action.RAISE_2POT:
                contribution = (self.data.community_pot + self.data.current_round_pot) * 2
                self.data.raisers.append(self.data.current_player.seat)
            elif action == Action.ALL_IN:
                contribution = self.data.current_player.stack
                self.data.raisers.append(self.data.current_player.seat)
            elif action == Action.SMALL_BLIND:
                contribution = np.minimum(self.data.small_blind, self.data.current_player.stack)
            elif action == Action.BIG_BLIND:
                contribution = np.minimum(self.data.big_blind, self.data.current_player.stack)
                self.round_manager.mark_bb()
            else:
                raise RuntimeError("Illegal action.")
            if contribution > self.data.min_call:
                self.round_manager.mark_raiser()
            self.data.current_player.stack -= contribution
            self.data.current_player.pot += contribution
            self.data.current_round_pot += contribution
            self.data.last_player_pot = self.data.current_player.pot
            if self.data.current_player.stack == 0 and contribution > 0:
                self.round_manager.mark_out_of_cash_but_contributed()
            self.data.min_call = max(self.data.min_call, contribution)
            self.data.current_player.actions.append(action)
            self.data.current_player.last_action_in_stage = action.name
            self.data.current_player.temp_stack.append(self.data.current_player.stack)
            
            self.data.current_player.max_win += contribution
            # self.player_max_win[self.data.current_player.seat] += contribution  # side pot
            pos = self.round_manager.idx
            rnd = self.data.stage.value + self.second_round
            self.data.stage_data[rnd].calls[pos] = action == Action.CALL
            self.data.stage_data[rnd].raises[pos] = action in [Action.RAISE_2POT, Action.RAISE_HALF_POT, Action.RAISE_POT]
            self.data.stage_data[rnd].min_call_at_action[pos] = self.data.min_call / (self.data.big_blind * 100)
            self.data.stage_data[rnd].community_pot_at_action[pos] = self.data.community_pot / (self.data.big_blind * 100)
            self.data.stage_data[rnd].contribution[pos] += contribution / (self.data.big_blind * 100)
            self.data.stage_data[rnd].stack_at_action[pos] = self.data.current_player.stack / (self.data.big_blind * 100)
        self.round_manager.update_alive()
        self.log.info(
            f"Seat {self.data.current_player.seat} ({self.data.current_player.name}): {action} - Remaining stack: {self.data.current_player.stack}, "
            f"Round pot: {self.data.current_round_pot}, Community pot: {self.data.community_pot}, "
            f"player pot: {self.data.current_player.pot}")
    def is_agent_autoplay(self, idx=None):
        if not idx:
            return hasattr(self.data.current_player.agent_obj, 'autoplay')
        return hasattr(self.player_manager.players[idx].agent_obj, 'autoplay')
    def perform_action_and_step_forward(self, action):
        """
        Next player makes a move and a new environment is observed.

        Args:
            action: Used for testing only. Needs to be of Action type

        """
        # loop over step function, calling the agent's action method
        # until either the env id sone, or an agent is just a shell and
        # and will get a call from to the step function externally (e.g. via
        # keras-rl
        self.data.reward = 0
        self.acting_agent = self.round_manager.idx
        if self.is_agent_autoplay():
            while self.is_agent_autoplay() and not self.done:
                self.log.debug("Autoplay agent. Call action method of agent.")
                self.update_environment()
                # call agent's action method
                action = self.data.current_player.agent_obj.action(self.data.legal_moves, self.data.observation, self.data.info)
                if Action(action) not in self.data.legal_moves:
                    self.data.illegal_move(action)
                else:
                    self.perform_step(Action(action))
                    if self.data.first_action_for_hand[self.acting_agent] or self.done:
                        self.data.first_action_for_hand[self.acting_agent] = False
                        self.calculate_reward(action)
        else:  # action received from player shell (e.g. keras rl, not autoplay)
            self.update_environment()  # get legal moves
            if Action(action) not in self.legal_moves:
                self.data.illegal_move(action)
            else:
                self.perform_step(Action(action))
                if self.data.first_action_for_hand[self.acting_agent] or self.done:
                    self.data.first_action_for_hand[self.acting_agent] = False
                    self.calculate_reward(action)
            self.log.info(f"Previous action reward for seat {self.acting_agent}: {self.data.reward}")
        return self.data.array_everything, self.data.reward, self.done, self.data.info
    def calculate_reward(self, last_action):
        """
        Preliminiary implementation of reward function
        - Currently missing potential additional winnings from future contributions
        """
        # if last_action == Action.FOLD:
        #     self.reward = -(
        #             self.community_pot + self.current_round_pot)
        # else:
        #     self.reward = self.player_data.equity_to_river_alive * (self.community_pot + self.current_round_pot) - \
        #                   (1 - self.player_data.equity_to_river_alive) * self.player_pots[self.current_player.seat]
        _ = last_action
        if self.done:
            won = 1 if not self.is_agent_autoplay(idx=self.winner_ix) else -1
            # self.reward = self.initial_stacks * len(self.players) * won
            total_initial_stacks = sum(player.initial_stack for player in self.player_manager.players)
            self.reward = total_initial_stacks * won
            self.log.debug(f"Keras-rl agent has reward {self.reward}")

        elif len(self.player_manager.funds_history) > 1:
            self.reward = self.player_manager.funds_history.iloc[-1, self.acting_agent] - self.player_manager.funds_history.iloc[
                -2, self.acting_agent]

        else:
            pass
    def reset_pots(self):
        self.data.community_pot += self.data.current_round_pot
        self.data.current_round_pot = 0
        self.player_manager.set_all_pots(0) 
    def update_environment(self):
        """Observe the environment"""
        player_pots = self.player_manager.player_pots
        if not self.done:
            self.data.set_legal_moves(player_pots)
        if not self.data.current_player:  # game over
            self.data.current_player = self.player_manager.players[self.winner_ix]
        self.data.prepare_data(player_pots, sum(self.round_manager.alive), self.card_manager.table_cards)
