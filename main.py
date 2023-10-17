import random
from env.poker_env import PokerEnv
from pokerkit import Poker
from data_collection.collect_data import collect_hand_data, collect_betting_data
from preprocessing.preprocess_data import preprocess_hand_data, preprocess_betting_data
from decision_model.make_decision import make_decision
from adaptation.adapt_strategy import adapt_strategy

def main():
   env = PokerEnv()

   done = False
   while not done:
      obs = env.reset()

      while True:
         action = random.randint(0,4) 
         obs, reward, done, info = env.step(action)

         if done:
            break
            
   print("Game over")
   
if __name__ == '__main__':
   main()
