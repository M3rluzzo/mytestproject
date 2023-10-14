"""Groupier functions"""
import logging

import numpy as np
from gym import Env
from ...classes.Deck import Deck
from .classes.PlayerShell import PlayerShell
from .classes.Dealer import Dealer
from .classes.TableManager import TableManager
from .classes.PlayerManager import PlayerManager
from ...classes.enums import Stage, Action
from .classes.EnvData import CommunityData, PlayerData
from gym_env.rendering import PygletWindow, WHITE, RED, GREEN, BLUE
from tools.hand_evaluator import get_winner
from tools.helper import flatten

# pylint: disable=import-outside-toplevel

log = logging.getLogger(__name__)


class TexasHoldemEnv(Env):
    """Pokergame environment"""
    def __init__(self, initial_stacks=100, small_blind=1, big_blind=2, render=False, funds_plot=True,
                 max_raising_rounds=2, use_cpp_montecarlo=False):
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
        if use_cpp_montecarlo:
            import cppimport
            calculator = cppimport.imp("tools.montecarlo_cpp.pymontecarlo")
            get_equity = calculator.montecarlo
        else:
            from tools.montecarlo_python import get_equity
        self.current_step = 0
        self.get_equity = get_equity
        self.use_cpp_montecarlo = use_cpp_montecarlo
        self.second_round = False
        
        self.get_equity = get_equity  # Metodo per il calcolo dell'equity
        self.observation = None  # Osservazione dell'ambiente
        self.reward = None  # Ricompensa attuale
        self.done = False  # Stato di completamento del gioco
        self.info = None  # Informazioni aggiuntive
        self.array_everything = None  # [Non chiaro cosa sia, ma sembra generale abbastanza per stare qui]

        self.deck: Deck = Deck()
        self.table: TableManager = TableManager(log, small_blind, big_blind, render)
        self.dealer: Dealer = Dealer(log, self.table)
        self.player_manager: PlayerManager = PlayerManager(log, initial_stacks, funds_plot, max_raising_rounds)

    def reset(self):
        """Reset after game over."""
        self.observation = None
        self.reward = None
        self.info = None
        self.done = False
        self.player_manager.reset()
        self.dealer.reset(self.player_manager.players)
        
        self.start_new_hand()
        self.get_environment()
        # auto play for agents where autoplay is set
        if self.agent_is_autoplay() and not self.done:
            self.step('initial_player_autoplay')  # kick off the first action after bb by an autoplay agent

        return self.array_everything

#region New Hand Behaviour
    def start_new_hand(self):
        self.current_step += 1
        """Deal new cards to players and reset table states."""
        self.player_manager.save_funds_history()

        """Check if only one player has money left"""
        remaining_players = self.dealer.get_alive_players(self.player_manager)
        if remaining_players < 2:
            """End of an episode."""
            log.info("Game over.")
            self.done = True
            self.player_manager.execute_game_over()
            return 
    
        log.info("++++++++++++++++++++++++++")
        log.info(f"Starting new hand ({self.current_step})")
        log.info("++++++++++++++++++++++++++")
        
        n_players = len(self.player_manager.players)
        self.dealer.start_new_hand(self.player_manager)
        
        self.table.start_new_hand(n_players)
        self.player_manager.start_new_hand()
        self.dealer.next_dealer()

        self.dealer.distribute_cards(self.player_manager.players)
            
        self.initiate_round()

    def initiate_round(self):
        """A new round (flop, turn, river) is initiated"""
        self.player_manager.initiate_round()
        self.table.min_call = 0
        
        self.dealer.player_cycle.new_round_reset()
        if self.dealer.stage == Stage.PREFLOP:
            log.info("")
            log.info("===Round: Stage: PREFLOP")
            # max steps total will be adjusted again at bb
            self.dealer.player_cycle.max_steps_total = len(self.player_manager.players) * self.player_manager.max_round_raising + 2

            self.next_player()
            self.process_decision(Action.SMALL_BLIND)
            self.next_player()
            self.process_decision(Action.BIG_BLIND)
            self.next_player()

        elif self.dealer.stage in [Stage.FLOP, Stage.TURN, Stage.RIVER]:
            self.dealer.player_cycle.max_steps_total = len(self.player_manager.players) * self.player_manager.max_round_raising

            self.next_player()

        elif self.dealer.stage == Stage.SHOWDOWN:
            log.info("Showdown")

        else:
            raise RuntimeError()

    def next_player(self):
        """Move to the next player"""
        self.dealer.current_player = self.dealer.player_cycle.next_player()
        if not self.dealer.current_player:
            if sum(self.dealer.player_cycle.alive) < 2:
                log.info("Only one player remaining in round")
                self.dealer.stage = Stage.END_HIDDEN
            else:
                log.info("End round - no current player returned")
                self.dealer.end_round(len(self.player_manager.players))
                # todo: in some cases no new round should be initialized bc only one player is playing only it seems
                self.initiate_round()

        elif self.dealer.current_player in ['max_steps_total', 'max_steps_after_raiser']:
            log.debug(self.dealer.current_player)
            log.info("End of round ")
            self.dealer.end_round(len(self.player_manager.players))
            return

    def process_decision(self, action):  # pylint: disable=too-many-statements
        """Process the decisions that have been made by an agent."""
        if action not in [Action.SMALL_BLIND, Action.BIG_BLIND]:
            assert action in set(self.table.legal_moves), "Illegal decision"

        if action == Action.FOLD:
            self.dealer.player_cycle.deactivate_current()
            self.dealer.player_cycle.mark_folder()

        else:

            if action == Action.CALL:
                contribution = min(self.table.min_call - self.table.player_pots[self.dealer.current_player.seat],
                                   self.dealer.current_player.stack)
                self.player_manager.callers.append(self.dealer.current_player.seat)
                self.player_manager.last_caller = self.dealer.current_player.seat

            # verify the player has enough in his stack
            elif action == Action.CHECK:
                contribution = 0
                self.dealer.player_cycle.mark_checker()

            elif action == Action.RAISE_3BB:
                contribution = 3 * self.table.big_blind - self.table.player_pots[self.dealer.current_player.seat]
                self.player_manager.raisers.append(self.dealer.current_player.seat)

            elif action == Action.RAISE_HALF_POT:
                contribution = (self.table.community_pot + self.table.current_round_pot) / 2
                self.player_manager.raisers.append(self.dealer.current_player.seat)

            elif action == Action.RAISE_POT:
                contribution = (self.table.community_pot + self.table.current_round_pot)
                self.player_manager.raisers.append(self.dealer.current_player.seat)

            elif action == Action.RAISE_2POT:
                contribution = (self.table.community_pot + self.table.current_round_pot) * 2
                self.player_manager.raisers.append(self.dealer.current_player.seat)

            elif action == Action.ALL_IN:
                contribution = self.dealer.current_player.stack
                self.player_manager.raisers.append(self.dealer.current_player.seat)

            elif action == Action.SMALL_BLIND:
                contribution = np.minimum(self.table.small_blind, self.dealer.current_player.stack)

            elif action == Action.BIG_BLIND:
                contribution = np.minimum(self.table.big_blind, self.dealer.current_player.stack)
                self.dealer.player_cycle.mark_bb()
            else:
                raise RuntimeError("Illegal action.")

            if contribution > self.table.min_call:
                self.dealer.player_cycle.mark_raiser()

            self.dealer.current_player.stack -= contribution
            self.table.player_pots[self.dealer.current_player.seat] += contribution
            self.table.current_round_pot += contribution
            self.table.last_player_pot = self.table.player_pots[self.dealer.current_player.seat]

            if self.dealer.current_player.stack == 0 and contribution > 0:
                self.dealer.player_cycle.mark_out_of_cash_but_contributed()

            self.table.min_call = max(self.table.min_call, contribution)

            self.dealer.current_player.actions.append(action)
            self.dealer.current_player.last_action_in_stage = action.name
            self.dealer.current_player.temp_stack.append(self.dealer.current_player.stack)

            self.table.player_max_win[self.dealer.current_player.seat] += contribution  # side pot

            pos = self.dealer.player_cycle.idx
            rnd = self.dealer.stage.value + self.second_round
            self.player_manager.stage_data[rnd].calls[pos] = action == Action.CALL
            self.player_manager.stage_data[rnd].raises[pos] = action in [Action.RAISE_2POT, Action.RAISE_HALF_POT, Action.RAISE_POT]
            self.player_manager.stage_data[rnd].min_call_at_action[pos] = self.table.min_call / (self.table.big_blind * 100)
            self.player_manager.stage_data[rnd].community_pot_at_action[pos] = self.table.community_pot / (self.table.big_blind * 100)
            self.player_manager.stage_data[rnd].contribution[pos] += contribution / (self.table.big_blind * 100)
            self.player_manager.stage_data[rnd].stack_at_action[pos] = self.dealer.current_player.stack / (self.table.big_blind * 100)

        self.dealer.player_cycle.update_alive()

        log.info(
            f"Seat {self.dealer.current_player.seat} ({self.dealer.current_player.name}): {action} - Remaining stack: {self.dealer.current_player.stack}, "
            f"Round pot: {self.table.current_round_pot}, Community pot: {self.table.community_pot}, "
            f"player pot: {self.table.player_pots[self.dealer.current_player.seat]}")
#endregion

#region Get Environment Behaviour
    def get_environment(self):
            """Observe the environment"""
            if not self.done:
                self.get_legal_moves()

            self.observation = None
            self.reward = 0
            self.info = None
            self.table.community_data = CommunityData(len(self.player_manager.players))
            self.table.community_data.community_pot = self.table.community_pot / (self.table.big_blind * 100)
            self.table.community_data.current_round_pot = self.table.current_round_pot / (self.table.big_blind * 100)
            self.table.community_data.small_blind = self.table.small_blind
            self.table.community_data.big_blind = self.table.big_blind
            self.table.community_data.stage[np.minimum(self.dealer.stage.value, 3)] = 1  # pylint: disable= invalid-sequence-index
            self.table.community_data.legal_moves = [action in self.table.legal_moves for action in Action]
            # self.cummunity_data.active_players

            self.player_manager.player_data = PlayerData()
            self.player_manager.player_data.stack = [player.stack / (self.table.big_blind * 100) for player in self.player_manager.players]

            if not self.dealer.current_player:  # game over
                self.dealer.current_player = self.player_manager.players[self.player_manager.winner_ix]

            self.player_manager.player_data.position = self.dealer.current_player.seat
            self.dealer.current_player.equity_alive = self.get_equity(set(self.dealer.current_player.cards), set(self.table.cards),
                                                            sum(self.dealer.player_cycle.alive), 1000)
            self.player_manager.player_data.equity_to_river_alive = self.dealer.current_player.equity_alive

            arr1 = np.array(list(flatten(self.player_manager.player_data.__dict__.values())))
            arr2 = np.array(list(flatten(self.table.community_data.__dict__.values())))
            arr3 = np.array([list(flatten(sd.__dict__.values())) for sd in self.player_manager.stage_data]).flatten()
            # arr_legal_only = np.array(self.community_data.legal_moves).flatten()

            self.array_everything = np.concatenate([arr1, arr2, arr3]).flatten()

            self.observation = self.array_everything
            self.get_legal_moves()

            self.info = {'player_data': self.player_manager.player_data.__dict__,
                        'community_data': self.table.community_data.__dict__,
                        'stage_data': [stage.__dict__ for stage in self.player_manager.stage_data],
                        'legal_moves': self.table.legal_moves}

            self.observation_space = self.array_everything.shape

            if self.table.render_switch:
                self.render()
    def get_legal_moves(self):
        """Determine what moves are allowed in the current state"""
        self.table.legal_moves = []
        if self.table.player_pots[self.dealer.current_player.seat] == max(self.table.player_pots):
            self.table.legal_moves.append(Action.CHECK)
        else:
            self.table.legal_moves.append(Action.CALL)
            self.table.legal_moves.append(Action.FOLD)

        if self.dealer.current_player.stack >= 3 * self.table.big_blind - self.table.player_pots[self.dealer.current_player.seat]:
            self.table.legal_moves.append(Action.RAISE_3BB)

            if self.dealer.current_player.stack >= ((self.table.community_pot + self.table.current_round_pot) / 2) >= self.table.min_call:
                self.table.legal_moves.append(Action.RAISE_HALF_POT)

            if self.dealer.current_player.stack >= (self.table.community_pot + self.table.current_round_pot) >= self.table.min_call:
                self.table.legal_moves.append(Action.RAISE_POT)

            if self.dealer.current_player.stack >= ((self.table.community_pot + self.table.current_round_pot) * 2) >= self.table.min_call:
                self.table.legal_moves.append(Action.RAISE_2POT)

            if self.dealer.current_player.stack > 0:
                self.table.legal_moves.append(Action.ALL_IN)

        log.debug(f"Community+current round pot pot: {self.table.community_pot + self.table.current_round_pot}")

    def render(self, mode='human', current_step=-1, training_mode=True):
        """Render the current state"""
        screen_width = 600
        screen_height = 400
        table_radius = 200
        face_radius = 10

        if self.table.viewer is None:
            self.table.viewer = PygletWindow(screen_width + 50, screen_height + 50)
        self.table.viewer.reset()
        self.table.viewer.circle(screen_width / 2, screen_height / 2, table_radius, color=BLUE,
                           thickness=0)

        for i in range(len(self.player_manager.players)):
            degrees = i * (360 / len(self.player_manager.players))
            radian = (degrees * (np.pi / 180))
            x = (face_radius + table_radius) * np.cos(radian) + screen_width / 2
            y = (face_radius + table_radius) * np.sin(radian) + screen_height / 2
            if self.dealer.player_cycle.alive[i]:
                color = GREEN
            else:
                color = RED
            self.table.viewer.circle(x, y, face_radius, color=color, thickness=2)

            try:
                if i == self.dealer.current_player.seat:
                    self.table.viewer.rectangle(x - 60, y, 150, -50, (255, 0, 0, 10))
            except AttributeError:
                pass
            self.table.viewer.text(f"{self.player_manager.players[i].name}", x - 60, y - 15,
                             font_size=10,
                             color=WHITE)
            self.table.viewer.text(f"Player {self.player_manager.players[i].seat}: {self.player_manager.players[i].cards}", x - 60, y,
                             font_size=10,
                             color=WHITE)
            equity_alive = int(round(float(self.player_manager.players[i].equity_alive) * 100))

            self.table.viewer.text(f"${self.player_manager.players[i].stack} (EQ: {equity_alive}%)", x - 60, y + 15, font_size=10,
                             color=WHITE)
            try:
                self.table.viewer.text(self.player_manager.players[i].last_action_in_stage, x - 60, y + 30, font_size=10, color=WHITE)
            except IndexError:
                pass
            x_inner = (-face_radius + table_radius - 60) * np.cos(radian) + screen_width / 2
            y_inner = (-face_radius + table_radius - 60) * np.sin(radian) + screen_height / 2
            self.table.viewer.text(f"${self.table.player_pots[i]}", x_inner, y_inner, font_size=10, color=WHITE)
            self.table.viewer.text(f"{self.table.cards}", screen_width / 2 - 40, screen_height / 2, font_size=10,
                             color=WHITE)
            self.table.viewer.text(f"${self.table.community_pot}", screen_width / 2 - 15, screen_height / 2 + 30, font_size=10,
                             color=WHITE)
            self.table.viewer.text(f"${self.table.current_round_pot}", screen_width / 2 - 15, screen_height / 2 + 50,
                             font_size=10,
                             color=WHITE)

            # Check if in training mode and display the step if true
            if training_mode and current_step is not None:
                self.table.viewer.text(f"Step: {current_step}", screen_width - 100, 30, font_size=10, color=WHITE)
            

            x_button = (-face_radius + table_radius - 20) * np.cos(radian) + screen_width / 2
            y_button = (-face_radius + table_radius - 20) * np.sin(radian) + screen_height / 2
            try:
                if i == self.dealer.player_cycle.dealer_idx:
                    self.table.viewer.circle(x_button, y_button, 5, color=BLUE, thickness=2)
            except AttributeError:
                pass
        self.table.viewer.update()
#endregion

#region Step Behaviour
    def step(self, action):  # pylint: disable=arguments-differ
        """
        Next player makes a move and a new environment is observed.

        Args:
            action: Used for testing only. Needs to be of Action type

        """
        # loop over step function, calling the agent's action method
        # until either the env id sone, or an agent is just a shell and
        # and will get a call from to the step function externally (e.g. via
        # keras-rl
        self.reward = 0
        self.player_manager.acting_agent = self.dealer.player_cycle.idx
        if self.agent_is_autoplay():
            while self.agent_is_autoplay() and not self.done:
                log.debug("Autoplay agent. Call action method of agent.")
                self.get_environment()
                # call agent's action method
                print(self.table.legal_moves)
                action = self.dealer.current_player.agent_obj.action(self.table.legal_moves, self.observation, self.info)
                if Action(action) not in self.table.legal_moves:
                    self.illegal_move(action)
                else:
                    self.execute_step(Action(action))
                    if self.player_manager.first_action_for_hand[self.player_manager.acting_agent] or self.done:
                        self.player_manager.first_action_for_hand[self.player_manager.acting_agent] = False
                        self.calculate_reward(action)

        else:  # action received from player shell (e.g. keras rl, not autoplay)
            self.get_environment()  # get legal moves
            if Action(action) not in self.table.legal_moves:
                self.illegal_move(action)
            else:
                self.execute_step(Action(action))
                if self.player_manager.first_action_for_hand[self.player_manager.acting_agent] or self.done:
                    self.player_manager.first_action_for_hand[self.player_manager.acting_agent] = False
                    self.calculate_reward(action)

            log.info(f"Previous action reward for seat {self.player_manager.acting_agent}: {self.reward}")
        return self.array_everything, self.reward, self.done, self.info

    def agent_is_autoplay(self, idx=None):
        if not idx:
            return hasattr(self.dealer.current_player.agent_obj, 'autoplay')
        return hasattr(self.player_manager.players[idx].agent_obj, 'autoplay')
    
    def execute_step(self, action):
        self.process_decision(action)

        self.next_player()

        if self.dealer.stage in [Stage.END_HIDDEN, Stage.SHOWDOWN]:
            self.end_hand()
            self.start_new_hand()

        self.get_environment()
        
    def end_hand(self):
        self.table.clean_up_pots(len(self.player_manager.players))
        self.player_manager.winner_ix = self.get_winner()
        self.award_winner(self.player_manager.winner_ix)
        
    def get_winner(self):
        """Determine which player has won the hand"""
        potential_winners = self.dealer.player_cycle.get_potential_winners()

        potential_winner_idx = [i for i, potential_winner in enumerate(potential_winners) if potential_winner]
        if sum(potential_winners) == 1:
            winner_ix = [i for i, active in enumerate(potential_winners) if active][0]
            winning_card_type = 'Only remaining player in round'

        else:
            assert self.dealer.stage == Stage.SHOWDOWN
            remaining_player_winner_ix, winning_card_type = get_winner([player.cards
                                                                        for ix, player in enumerate(self.player_manager.players) if
                                                                        potential_winners[ix]],
                                                                       self.table.cards)
            winner_ix = potential_winner_idx[remaining_player_winner_ix]
        log.info(f"Player {winner_ix} won: {winning_card_type}")
        return winner_ix
    
    def award_winner(self, winner_ix):
        """Hand the pot to the winner and handle side pots"""
        max_win_per_player_for_winner = self.table.player_max_win[winner_ix]
        total_winnings = sum(np.minimum(max_win_per_player_for_winner, self.table.player_max_win))
        remains = np.maximum(0, np.array(self.table.player_max_win) - max_win_per_player_for_winner)  # to be returned

        self.player_manager.players[winner_ix].stack += total_winnings
        self.player_manager.winner_ix = winner_ix
        if total_winnings < sum(self.table.player_max_win):
            log.info("Returning side pots")
            for i, player in enumerate(self.player_manager.players):
                player.stack += remains[i]
    def illegal_move(self, action):
        log.warning(f"{action} is an Illegal move, try again. Currently allowed: {self.table.legal_moves}")
        self.reward = self.table.illegal_move_reward
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
            won = 1 if not self.agent_is_autoplay(idx=self.player_manager.winner_ix) else -1
            self.reward = self.player_manager.initial_stacks * len(self.player_manager.players) * won
            log.debug(f"Keras-rl agent has reward {self.reward}")

        elif len(self.player_manager.funds_history) > 1:
            self.reward = self.player_manager.funds_history.iloc[-1, self.player_manager.acting_agent] - self.player_manager.funds_history.iloc[
                -2, self.player_manager.acting_agent]

        else:
            pass
#endregion

    def add_player(self, agent):
        """Add a player to the table. Has to happen at the very beginning"""
        self.player_manager.num_of_players += 1
        player = PlayerShell(stack_size=self.player_manager.initial_stacks, name=agent.name)
        player.agent_obj = agent
        player.seat = len(self.player_manager.players)  # assign next seat number to player
        player.stack = self.player_manager.initial_stacks
        self.player_manager.players.append(player)
        self.player_manager.player_status = [True] * len(self.player_manager.players)
        self.table.player_pots = [0] * len(self.player_manager.players)
