import pandas as pd
import matplotlib.pyplot as plt
from logging import Logger
winner_in_episodes = []

class PlayerManager:
    def __init__(self, log, initial_stacks, funds_plot, max_raising_rounds):
        self.log: Logger = log
        self.num_of_players = 0  # Numero di giocatori
        self.players = []  # Lista dei giocatori
        self.player_status = []  # Status dei giocatori (es. one-hot encoded)
        self.last_caller = None  # Ultimo giocatore che ha chiamato
        self.last_raiser = None  # Ultimo giocatore che ha rialzato
        self.raisers = []  # Lista dei giocatori che hanno rialzato nel round corrente
        self.callers = []  # Lista dei giocatori che hanno chiamato nel round corrente
        self.player_data = None  # Dati specifici dei giocatori
        self.stage_data = None  # Dati specifici dello stage
        self.action = None  # Azione corrente
        self.winner_ix = None  # Indice del vincitore
        self.initial_stacks = initial_stacks  # Stack iniziale
        self.acting_agent = None  # Agente attualmente in azione
        self.funds_plot = funds_plot  # Opzione per il grafico dei fondi
        self.max_round_raising = max_raising_rounds  # Massimi rialzi per round
        self.funds_history = None  # Storico dei fondi
        self.first_action_for_hand = None  # Prima azione della mano

    def reset(self):
        self.funds_history = pd.DataFrame()
        self.first_action_for_hand = [True] * len(self.players)
        
        for player in self.players:
            player.stack = self.initial_stacks
    
    def save_funds_history(self):
        """Keep track of player funds history"""
        funds_dict = {i: player.stack for i, player in enumerate(self.players)}
        self.funds_history = pd.concat([self.funds_history, pd.DataFrame(funds_dict, index=[0])])    
    
    def execute_game_over(self):
        player_names = [f"{i} - {player.name}" for i, player in enumerate(self.players)]
        self.funds_history.columns = player_names
        if self.funds_plot:
            self.funds_history.reset_index(drop=True).plot()
        self.log.info(self.funds_history)
        plt.show()
        
        winner_in_episodes.append(self.winner_ix)
        league_table = pd.Series(winner_in_episodes).value_counts()
        best_player = league_table.index[0]
        self.log.info(league_table)
        self.log.info(f"Best Player: {best_player}")
    
    def start_new_hand(self):
        self.first_action_for_hand = [True] * len(self.players)
        for player in self.players:
            player.cards = []
            
    def initiate_round(self):
        self.last_caller = None
        self.last_raiser = None
        self.raisers = []
        self.callers = []
        
        for player in self.players:
            player.last_action_in_stage = ''