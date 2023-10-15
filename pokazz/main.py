import random
from env import PokerEnv

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
