class SpinNGoState:
    def __init__(self, players, board, pot):
        self.players = players  # Lista di oggetti giocatore
        self.board = board  # Carte sul tavolo
        self.pot = pot  # Somma nel piatto

    def valid_actions(self):
        # Restituisce una lista di azioni valide come 'call', 'raise', 'fold'
        return ['call', 'raise', 'fold']

    def take(self, action):
        # Implementa la logica per prendere un'azione e restituire un nuovo stato
        new_state = SpinNGoState(self.players, self.board, self.pot)
        # Aggiorna new_state in base all'azione
        return new_state

    def utility(self, player):
        # Calcola l'utilità dello stato corrente per un determinato giocatore
        return 0  # Sostituire con la logica appropriata
