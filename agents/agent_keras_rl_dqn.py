import logging
import time
import numpy as np
import tensorflow as tf
import json
from tensorflow.keras.models import Sequential, model_from_json
from tensorflow.keras.callbacks import TensorBoard
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam
from rl.policy import BoltzmannQPolicy
from rl.memory import SequentialMemory
from rl.agents import DQNAgent
from rl.core import Processor

autoplay = True
window_length = 1
nb_max_start_steps = 1
train_interval = 100
nb_steps_warmup = 50
nb_steps = 100000
memory_limit = int(nb_steps / 2)
batch_size = 500
enable_double_dqn = False
log = logging.getLogger(__name__)

class Player:
    def __init__(self, name='DQN', load_model=None, env=None):
        self.equity_alive = 0
        self.actions = []
        self.last_action_in_stage = ''
        self.temp_stack = []
        self.name = name
        self.autoplay = True
        self.dqn = None
        self.model = None
        self.env = env
        if load_model:
            self.load(load_model)
    def initiate_agent(self, env):
        tf.compat.v1.disable_eager_execution()
        self.env = env
        nb_actions = self.env.table.action_space.n
        self.model = Sequential()
        self.model.add(Dense(512, activation='relu', input_shape=env.observation_space))
        self.model.add(Dropout(0.2))
        self.model.add(Dense(512, activation='relu'))
        self.model.add(Dropout(0.2))
        self.model.add(Dense(512, activation='relu'))
        self.model.add(Dropout(0.2))
        self.model.add(Dense(nb_actions, activation='linear'))
        memory = SequentialMemory(limit=memory_limit, window_length=window_length)
        policy = TrumpPolicy()
        nb_actions = env.table.action_space.n
        self.dqn = DQNAgent(model=self.model, nb_actions=nb_actions, memory=memory, nb_steps_warmup=nb_steps_warmup,
                            target_model_update=1e-2, policy=policy,
                            processor=CustomProcessor(),
                            batch_size=batch_size, train_interval=train_interval, enable_double_dqn=enable_double_dqn)
        self.dqn.compile(Adam(lr=1e-3), metrics=['mae'])
    def start_step_policy(self, observation):
        log.info("Random action")
        _ = observation
        action = self.env.action_space.sample()
        return action
    def train(self, env_name):
        timestr = time.strftime("%Y%m%d-%H%M%S") + "_" + str(env_name)
        tensorboard = TensorBoard(log_dir='./Graph/{}'.format(timestr), histogram_freq=0, write_graph=True,
                                  write_images=False)
        self.dqn.fit(self.env, nb_max_start_steps=nb_max_start_steps, nb_steps=nb_steps, visualize=False, verbose=2,
                     start_step_policy=self.start_step_policy, callbacks=[tensorboard])
        dqn_json = self.model.to_json()
        with open("dqn_{}_json.json".format(env_name), "w") as json_file:
            json.dump(dqn_json, json_file)
        self.dqn.save_weights('dqn_{}_weights.h5'.format(env_name), overwrite=True)
        self.dqn.test(self.env, nb_episodes=5, visualize=False)
    def load(self, env_name):
        with open('dqn_{}_json.json'.format(env_name), 'r') as architecture_json:
            dqn_json = json.load(architecture_json)
        self.model = model_from_json(dqn_json)
        self.model.load_weights('dqn_{}_weights.h5'.format(env_name))
    def play(self, nb_episodes=5, render=False):
        memory = SequentialMemory(limit=memory_limit, window_length=window_length)
        policy = TrumpPolicy()
        class CustomProcessor(Processor):  # pylint: disable=redefined-outer-name
            def process_state_batch(self, batch):
                return np.squeeze(batch, axis=1)
            def process_info(self, info):
                processed_info = info['player_data']
                if 'stack' in processed_info:
                    processed_info = {'x': 1}
                return processed_info
        nb_actions = self.env.action_space.n
        self.dqn = DQNAgent(model=self.model, nb_actions=nb_actions, memory=memory, nb_steps_warmup=nb_steps_warmup,
                            target_model_update=1e-2, policy=policy,
                            processor=CustomProcessor(),
                            batch_size=batch_size, train_interval=train_interval, enable_double_dqn=enable_double_dqn)
        self.dqn.compile(Adam(lr=1e-3), metrics=['mae'])  # pylint: disable=no-member
        self.dqn.test(self.env, nb_episodes=nb_episodes, visualize=render)
    def action(self, action_space, observation, info):  # pylint: disable=no-self-use
        _ = observation  # not using the observation for random decision
        _ = info
        this_player_action_space = {Action.FOLD, Action.CHECK, Action.CALL, Action.RAISE_POT, Action.RAISE_HALF_POT,
                                    Action.RAISE_2POT}
        _ = this_player_action_space.intersection(set(action_space))
        action = None
        return action
class TrumpPolicy(BoltzmannQPolicy):
    def select_action(self, q_values):
        """Return the selected action
        # Arguments
            q_values (np.ndarray): List of the estimations of Q for each action
        # Returns
            Selection action
        """
        assert q_values.ndim == 1
        q_values = q_values.astype('float64')
        nb_actions = q_values.shape[0]
        exp_values = np.exp(np.clip(q_values / self.tau, self.clip[0], self.clip[1]))
        probs = exp_values / np.sum(exp_values)
        action = np.random.choice(range(nb_actions), p=probs)
        log.info(f"Chosen action by keras-rl {action} - probabilities: {probs}")
        return action
class CustomProcessor(Processor):
    def __init__(self):
        self.legal_moves_limit = None

    def process_state_batch(self, batch):
        """Remove second dimension to make it possible to pass it into cnn"""
        return np.squeeze(batch, axis=1)
    def process_info(self, info):
        if 'legal_moves' in info.keys():
            self.legal_moves_limit = info['legal_moves']
        else:
            self.legal_moves_limit = None
        return {'x': 1}
    def process_action(self, action):
        if 'legal_moves_limit' in self.__dict__ and self.legal_moves_limit is not None:
            self.legal_moves_limit = [move.value for move in self.legal_moves_limit]
            if action not in self.legal_moves_limit:
                for i in range(5):
                    action += i
                    if action in self.legal_moves_limit:
                        break
                    action -= i * 2
                    if action in self.legal_moves_limit:
                        break
                    action += i
        return action