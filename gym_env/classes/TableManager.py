from gym.spaces import Discrete
import numpy as np
from logging import Logger
from .enums import Action
from .EnvData import CommunityData

class TableManager:
    def __init__(self, log: Logger, small_blind, big_blind, render):
        self.small_blind = small_blind  # Piccolo buio
        self.big_blind = big_blind  # Grande buio
        self.render_switch = render  # Switch per il rendering grafico
        self.viewer = None  # Visualizzatore (probabilmente grafico)
        self.community_data: CommunityData = None  # Dati riguardanti l'intera comunità dei giocatori (potrebbe includere il pot comune)
        self.community_pot = 0  # Pot comune
        self.current_round_pot = 9  # Pot del round corrente
        self.player_pots = None  # Pot individuali dei giocatori
        self.min_call = None  # Chiamata minima
        self.last_player_pot = None  # Ultimo pot del giocatore
        self.player_max_win = None  # Massima vincita per i giocatori (usato per i pot secondari/side pots)
        self.legal_moves = None  # Mosse legali disponibili
        self.illegal_move_reward = -1  # Ricompensa per una mossa illegale
        self.action_space = Discrete(len(Action) - 2)  # Spazio delle azioni
        self.played_in_round = None  # Giocatori che hanno giocato nel round corrente
        self.cards = None  # Carte comunitarie sul tavolo
        
    def start_new_hand(self, n_players):
        self.community_pot = 0
        self.current_round_pot = 0
        self.player_pots = [0] * n_players
        self.player_max_win = [0] * n_players
        self.last_player_pot = 0
        self.played_in_round = 0
    
    def update_table_state(self, contribution, player, action):
        self.player_pots[player.seat] += contribution
        self.current_round_pot += contribution
        self.last_player_pot = self.player_pots[player.seat]
        self.min_call = max(self.min_call, contribution)
        self.player_max_win[player.seat] += contribution  

    def log_player_action(self, player, action, contribution, pos, rnd):
        self.stage_data[rnd].calls[pos] = action == Action.CALL
        self.stage_data[rnd].raises[pos] = action in [Action.RAISE_2POT, Action.RAISE_HALF_POT, Action.RAISE_POT]
        self.stage_data[rnd].min_call_at_action[pos] = self.min_call / (self.big_blind * 100)
        self.stage_data[rnd].community_pot_at_action[pos] = self.community_pot / (self.big_blind * 100)
        self.stage_data[rnd].contribution[pos] += contribution / (self.big_blind * 100)
        self.stage_data[rnd].stack_at_action[pos] = player.stack / (self.big_blind * 100)
    
    def clean_up_pots(self, n_players):
        self.community_pot += self.current_round_pot
        self.current_round_pot = 0
        self.player_pots = [0] * n_players
        
    def close_round(self, n_players):
        """put player_pots into community pots"""
        self.community_pot += sum(self.player_pots)
        self.player_pots = [0] * n_players
        self.played_in_round = 0