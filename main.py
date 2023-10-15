from env import PokerEnv
import argparse
import test

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", action="store_true", help="Run unit tests")
    args = parser.parse_args()

    if args.test:
        test.run_tests()
    else:
        env = PokerEnv(3, 500, 10, 20, None, False)
        env.reset()
        # Implementare la selezione delle azioni..
        # while not env.done:
        #   env.step()

if __name__ == "__main__":
    main()