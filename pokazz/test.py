import unittest
from env import PokerEnv, Action, Stage
from classes.player import Player
class TestPokerEnv(unittest.TestCase):
    def test_game(self):
        # Creiamo l'ambiente
        players = [Player("Ivey", 1125600), Player("Antonius", 2000000), Player("Dwan", 553500)]
        env = PokerEnv(players, starting_stack=1000000, small_blind=1000, big_blind=2000, ante=500)

        # Distribuiamo le carte
        env.deal_cards(["Ac2d", "5h7s", "7h6h"])

        # Azioni pre-flop
        env.step(Action.RAISE, 7000)
        env.step(Action.RAISE, 23000) 
        env.step(Action.FOLD)
        env.step(Action.CALL)

        # Distribuiamo il flop
        env.deal_board("Jc3d5c")

        # Azioni flop
        env.step(Action.RAISE, 35000)
        env.step(Action.CALL)  

        # Distribuiamo il turn
        env.deal_board("4h")

        # Azioni turn
        env.step(Action.RAISE, 90000)
        env.step(Action.RAISE, 232600)
        env.step(Action.RAISE, 1067100)
        env.step(Action.CALL)

        # Distribuiamo il river  
        env.deal_board("Jh")

        # Controlliamo le chip finali
        stacks = env.state.stacks
        self.assertEqual(stacks, [572100, 1997500, 1109500])

if __name__ == '__main__':
    unittest.main()