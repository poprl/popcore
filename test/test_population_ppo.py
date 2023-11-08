import unittest
from popcore import Population
import os
from datetime import datetime

import torch
import torch.nn as nn
from torch.distributions import MultivariateNormal
from torch.distributions import Categorical

import numpy as np

import gym

# This is an example of phylogenetic tree usage in the simple case of a single
# agent using PPO in the Gymnasium cartpole env.
# PPO code from https://github.com/nikhilbarhate99/PPO-PyTorch
# (Look at the link for citation details)


def set_device():
    device = torch.device('cpu')

    if (torch.cuda.is_available()):
        device = torch.device('cuda:0')
        torch.cuda.empty_cache()
        print("Device set to : " + str(torch.cuda.get_device_name(device)))
    else:
        print("Device set to : cpu")

    return device


class RolloutBuffer:
    def __init__(self):
        self.actions = []
        self.states = []
        self.logprobs = []
        self.rewards = []
        self.state_values = []
        self.is_terminals = []

    def clear(self):
        del self.actions[:]
        del self.states[:]
        del self.logprobs[:]
        del self.rewards[:]
        del self.state_values[:]
        del self.is_terminals[:]


class ActorCritic(nn.Module):
    def __init__(self, state_dim, action_dim,
                 has_continuous_action_space,
                 action_std_init,
                 device):
        super(ActorCritic, self).__init__()

        self.device = device
        self.has_continuous_action_space = has_continuous_action_space

        if has_continuous_action_space:
            self.action_dim = action_dim
            self.action_var = torch.full(
                (action_dim,),
                action_std_init * action_std_init).to(self.device)

        # actor
        if has_continuous_action_space:
            self.actor = nn.Sequential(
                            nn.Linear(state_dim, 64),
                            nn.Tanh(),
                            nn.Linear(64, 64),
                            nn.Tanh(),
                            nn.Linear(64, action_dim),
                            nn.Tanh()
                        )
        else:
            self.actor = nn.Sequential(
                            nn.Linear(state_dim, 64),
                            nn.Tanh(),
                            nn.Linear(64, 64),
                            nn.Tanh(),
                            nn.Linear(64, action_dim),
                            nn.Softmax(dim=-1)
                        )

        # critic
        self.critic = nn.Sequential(
                        nn.Linear(state_dim, 64),
                        nn.Tanh(),
                        nn.Linear(64, 64),
                        nn.Tanh(),
                        nn.Linear(64, 1)
                    )

    def set_action_std(self, new_action_std):

        if self.has_continuous_action_space:
            self.action_var = torch.full(
                (self.action_dim,),
                new_action_std * new_action_std).to(self.device)
        else:
            print("--------------------------------------------------")
            print("WARNING : Calling ActorCritic::set_action_std() on "
                  "discrete action space policy")
            print("--------------------------------------------------")

    def forward(self):
        raise NotImplementedError

    def act(self, state):

        if self.has_continuous_action_space:
            action_mean = self.actor(state)
            cov_mat = torch.diag(self.action_var).unsqueeze(dim=0)
            dist = MultivariateNormal(action_mean, cov_mat)
        else:
            action_probs = self.actor(state)
            dist = Categorical(action_probs)

        action = dist.sample()
        action_logprob = dist.log_prob(action)
        state_val = self.critic(state)

        return (action.detach(),
                action_logprob.detach(),
                state_val.detach())

    def evaluate(self, state, action):

        if self.has_continuous_action_space:
            action_mean = self.actor(state)
            action_var = self.action_var.expand_as(action_mean)
            cov_mat = torch.diag_embed(action_var).to(self.device)
            dist = MultivariateNormal(action_mean, cov_mat)

            # for single action continuous environments
            if self.action_dim == 1:
                action = action.reshape(-1, self.action_dim)

        else:
            action_probs = self.actor(state)
            dist = Categorical(action_probs)

        action_logprobs = dist.log_prob(action)
        dist_entropy = dist.entropy()
        state_values = self.critic(state)

        return action_logprobs, state_values, dist_entropy


class PPO:
    def __init__(self, state_dim, action_dim, lr_actor, lr_critic,
                 gamma, K_epochs, eps_clip,
                 has_continuous_action_space, device,
                 action_std_init=0.6):

        self.device = device
        self.has_continuous_action_space = has_continuous_action_space

        if has_continuous_action_space:
            self.action_std = action_std_init

        self.gamma = gamma
        self.eps_clip = eps_clip
        self.K_epochs = K_epochs

        self.buffer = RolloutBuffer()

        self.policy = ActorCritic(state_dim, action_dim,
                                  has_continuous_action_space,
                                  action_std_init,
                                  self.device).to(self.device)
        self.optimizer = torch.optim.Adam([
                        {'params': self.policy.actor.parameters(),
                            'lr': lr_actor},
                        {'params': self.policy.critic.parameters(),
                            'lr': lr_critic}
                    ])

        self.policy_old = ActorCritic(state_dim, action_dim,
                                      has_continuous_action_space,
                                      action_std_init,
                                      self.device).to(self.device)
        self.policy_old.load_state_dict(self.policy.state_dict())

        self.MseLoss = nn.MSELoss()

    def set_action_std(self, new_action_std):

        if self.has_continuous_action_space:
            self.action_std = new_action_std
            self.policy.set_action_std(new_action_std)
            self.policy_old.set_action_std(new_action_std)

        else:
            print("--------------------------------------------------")
            print("WARNING : Calling PPO::set_action_std() on discrete"
                  " action space policy")
            print("--------------------------------------------------")

    def decay_action_std(self, action_std_decay_rate, min_action_std):
        print("------------------------------------------------------")

        if self.has_continuous_action_space:
            self.action_std = self.action_std - action_std_decay_rate
            self.action_std = round(self.action_std, 4)
            if (self.action_std <= min_action_std):
                self.action_std = min_action_std
                print("setting actor output action_std to "
                      "min_action_std : ", self.action_std)
            else:
                print("setting actor output action_std to : ",
                      self.action_std)
            self.set_action_std(self.action_std)

        else:
            print("WARNING : Calling PPO::decay_action_std() on "
                  "discrete action space policy")

        print("------------------------------------------------------")

    def select_action(self, state):

        if self.has_continuous_action_space:
            with torch.no_grad():
                state = torch.FloatTensor(state).to(self.device)
                action, action_logprob, state_val = \
                    self.policy_old.act(state)

            self.buffer.states.append(state)
            self.buffer.actions.append(action)
            self.buffer.logprobs.append(action_logprob)
            self.buffer.state_values.append(state_val)

            return action.detach().cpu().numpy().flatten()

        else:
            with torch.no_grad():
                if not isinstance(state, np.ndarray):
                    state = state[0]
                state = torch.FloatTensor(state).to(self.device)
                action, action_logprob, state_val = \
                    self.policy_old.act(state)

            self.buffer.states.append(state)
            self.buffer.actions.append(action)
            self.buffer.logprobs.append(action_logprob)
            self.buffer.state_values.append(state_val)

            return action.item()

    def update(self):

        # Monte Carlo estimate of returns
        rewards = []
        discounted_reward = 0
        ziprr = zip(reversed(self.buffer.rewards),
                    reversed(self.buffer.is_terminals))
        for reward, is_terminal in ziprr:
            if is_terminal:
                discounted_reward = 0
            discounted_reward = reward + (self.gamma *
                                          discounted_reward)
            rewards.insert(0, discounted_reward)

        # Normalizing the rewards
        rewards = torch.tensor(rewards, dtype=torch.float32).to(self.device)
        rewards = (rewards - rewards.mean()) / (rewards.std() + 1e-7)

        # convert list to tensor
        old_states = torch.squeeze(
            torch.stack(self.buffer.states, dim=0)).detach().to(self.device)
        old_actions = torch.squeeze(
            torch.stack(self.buffer.actions,
                        dim=0)).detach().to(self.device)
        old_logprobs = torch.squeeze(
            torch.stack(self.buffer.logprobs,
                        dim=0)).detach().to(self.device)
        old_state_values = torch.squeeze(
            torch.stack(self.buffer.state_values,
                        dim=0)).detach().to(self.device)

        # calculate advantages
        advantages = rewards.detach() - old_state_values.detach()

        # Optimize policy for K epochs
        for _ in range(self.K_epochs):

            # Evaluating old actions and values
            logprobs, state_values, dist_entropy = \
                self.policy.evaluate(old_states, old_actions)

            # match state_values tensor dimensions with rewards tensor
            state_values = torch.squeeze(state_values)

            # Finding the ratio (pi_theta / pi_theta__old)
            ratios = torch.exp(logprobs - old_logprobs.detach())

            # Finding Surrogate Loss
            surr1 = ratios * advantages
            surr2 = torch.clamp(ratios, 1-self.eps_clip,
                                1+self.eps_clip) * advantages

            # final loss of clipped objective PPO
            loss = -torch.min(surr1, surr2) + 0.5 * \
                self.MseLoss(state_values, rewards) - 0.01 * \
                dist_entropy

            # take gradient step
            self.optimizer.zero_grad()
            loss.mean().backward()
            self.optimizer.step()

        # Copy new weights into old policy
        self.policy_old.load_state_dict(self.policy.state_dict())

        # clear buffer
        self.buffer.clear()

    def save(self, checkpoint_path):
        torch.save(self.policy_old.state_dict(), checkpoint_path)

    def load(self, checkpoint_path):
        self.policy_old.load_state_dict(
            torch.load(checkpoint_path, map_location=lambda storage,
                       loc: storage))
        self.policy.load_state_dict(
            torch.load(checkpoint_path, map_location=lambda storage,
                       loc: storage))


def step_function(parent_parameters, hyperparameters, contributors=[]):
    ppo_agent = parent_parameters
    env = hyperparameters["env"]
    max_ep_len = hyperparameters["max_ep_len"]
    time_step = hyperparameters["time_step"]
    update_timestep = hyperparameters["update_timestep"]
    log_freq = hyperparameters["log_freq"]
    log_running_reward = hyperparameters["log_running_reward"]
    log_running_episodes = hyperparameters["log_running_episodes"]
    i_episode = hyperparameters["i_episode"]
    print_running_reward = hyperparameters["print_running_reward"]
    print_running_episodes = hyperparameters["print_running_episodes"]
    save_model_freq = hyperparameters["save_model_freq"]
    checkpoint_path = hyperparameters["checkpoint_path"]
    start_time = hyperparameters["start_time"]
    log = hyperparameters["log"]
    seed = hyperparameters["seed"]
    print_freq = hyperparameters["print_freq"]

    state = env.reset(seed=seed)
    current_ep_reward = 0

    torch.manual_seed(seed)
    np.random.seed(seed)

    for t in range(1, max_ep_len+1):

        # select action with policy
        action = ppo_agent.select_action(state)
        state, reward, done, _, _ = env.step(action)

        # saving reward and is_terminals
        ppo_agent.buffer.rewards.append(reward)
        ppo_agent.buffer.is_terminals.append(done)

        time_step += 1
        current_ep_reward += reward

        # update PPO agent
        if time_step % update_timestep == 0:
            ppo_agent.update()

        # if continuous action space; then decay action std of ouput
        # action distribution
        """if has_continuous_action_space and \
            time_step % action_std_decay_freq == 0:
            ppo_agent.decay_action_std(action_std_decay_rate,
                                        min_action_std)"""

        # log in logging file
        if time_step % log_freq == 0 and log:
            log_f = hyperparameters["log_f"]

            # log average reward till last episode
            log_avg_reward = log_running_reward / log_running_episodes
            log_avg_reward = round(log_avg_reward, 4)

            log_f.write('{},{},{}\n'.format(i_episode, time_step,
                                            log_avg_reward))
            log_f.flush()

            log_running_reward = 0
            log_running_episodes = 0

        # printing average reward
        if time_step % print_freq == 0:

            # print average reward till last episode
            print_avg_reward = print_running_reward /\
                print_running_episodes
            print_avg_reward = round(print_avg_reward, 2)

            print("Episode : {} \t\t Timestep : {} \t\t Average Reward"
                  " : {}".format(i_episode, time_step,
                                 print_avg_reward))

            print_running_reward = 0
            print_running_episodes = 0

        # save model weights
        if time_step % save_model_freq == 0 and log:
            print("--------------------------------------------------")
            print("saving model at : " + checkpoint_path)
            ppo_agent.save(checkpoint_path)
            print("model saved")
            print("Elapsed Time  : ",
                  datetime.now().replace(microsecond=0) - start_time)
            print("--------------------------------------------------")

        # break; if the episode is over
        if done:
            break

    print_running_reward += current_ep_reward
    print_running_episodes += 1

    log_running_reward += current_ep_reward
    log_running_episodes += 1

    i_episode += 1

    hyperparameters = \
        {"env": env,
            "max_ep_len": max_ep_len,
            "time_step": time_step,
            "update_timestep": update_timestep,
            "log_freq": log_freq,
            "log_running_reward": log_running_reward,
            "log_running_episodes": log_running_episodes,
            "i_episode": i_episode,
            "print_running_reward": print_running_reward,
            "print_running_episodes": print_running_episodes,
            "save_model_freq": save_model_freq,
            "checkpoint_path": checkpoint_path,
            "start_time": start_time,
            "log": log,
            "seed": seed,
            "print_freq": print_freq}

    return ppo_agent, hyperparameters


class TestPopulationPPO(unittest.TestCase):
    def test_PPO(self):
        device = set_device()

        # ################################## Training #########################

        # ###### initialize environment hyperparameters ######

        env_name = "CartPole-v1"
        has_continuous_action_space = False

        max_ep_len = 400                   # max timesteps in one episode
        # break training loop if timeteps > max_training_timesteps
        max_training_timesteps = int(1e5)

        # print avg reward in the interval (in num timesteps)
        print_freq = max_ep_len * 4
        # log avg reward in the interval (in num timesteps)
        log_freq = max_ep_len * 2
        # save model frequency (in num timesteps)
        save_model_freq = int(2e4)

        action_std = None

        #####################################################

        # Note : print/log frequencies should be > than max_ep_len

        # ############### PPO hyperparameters ################

        update_timestep = max_ep_len * 4      # update policy every n timesteps
        K_epochs = 40               # update policy for K epochs
        eps_clip = 0.2              # clip parameter for PPO
        gamma = 0.99                # discount factor

        lr_actor = 0.0003       # learning rate for actor network
        lr_critic = 0.001       # learning rate for critic network

        random_seed = 0     # set random seed if required (0 = no random seed)

        torch.use_deterministic_algorithms(True)
        torch.manual_seed(random_seed)
        np.random.seed(random_seed)

        #####################################################

        print("training environment name : " + env_name)

        env = gym.make(env_name)

        # state space dimension
        state_dim = env.observation_space.shape[0]

        # action space dimension
        if has_continuous_action_space:
            action_dim = env.action_space.shape[0]
        else:
            action_dim = env.action_space.n

        # ##################### logging ######################

        # log files for multiple runs are NOT overwritten
        current_folder = os.path.dirname(__file__)

        log_dir = current_folder + "/PPO_logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        log_dir = log_dir + '/' + env_name + '/'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # get number of log files in log directory
        run_num = 0
        current_num_files = next(os.walk(log_dir))[2]
        run_num = len(current_num_files)

        # create new log file for each run
        log_f_name = log_dir + '/PPO_' + env_name + "_log_" + str(run_num) +\
            ".csv"

        print("current logging run number for " + env_name + " : ", run_num)
        print("logging at : " + log_f_name)

        #####################################################

        # ################## checkpointing ###################

        # change this to prevent overwriting weights in same env_name folder
        run_num_pretrained = 0

        directory = current_folder + "/PPO_preTrained"
        if not os.path.exists(directory):
            os.makedirs(directory)

        directory = directory + '/' + env_name + '/'
        if not os.path.exists(directory):
            os.makedirs(directory)

        checkpoint_path = directory + \
            "PPO_{}_{}_{}.pth".format(env_name, random_seed,
                                      run_num_pretrained)
        print("save checkpoint path : " + checkpoint_path)

        #####################################################

        # ############ print all hyperparameters #############

        print("--------------------------------------------------------------")

        print("max training timesteps : ", max_training_timesteps)
        print("max timesteps per episode : ", max_ep_len)

        print("model saving frequency : " + str(save_model_freq) +
              " timesteps")
        print("log frequency : " + str(log_freq) + " timesteps")
        print("printing average reward over episodes in last : " +
              str(print_freq) + " timesteps")

        print("--------------------------------------------------------------")

        print("state space dimension : ", state_dim)
        print("action space dimension : ", action_dim)

        print("--------------------------------------------------------------")

        print("Initializing a discrete action space policy")

        print("--------------------------------------------------------------")

        print("PPO update frequency : " + str(update_timestep) + " timesteps")
        print("PPO K epochs : ", K_epochs)
        print("PPO epsilon clip : ", eps_clip)
        print("discount factor (gamma) : ", gamma)

        print("--------------------------------------------------------------")

        print("optimizer learning rate actor : ", lr_actor)
        print("optimizer learning rate critic : ", lr_critic)

        #####################################################

        print("==============================================================")

        # ################ training procedure ################

        # initialize a PPO agent
        ppo_agent = PPO(state_dim, action_dim, lr_actor, lr_critic, gamma,
                        K_epochs, eps_clip, has_continuous_action_space,
                        device, action_std)

        # track total training time
        start_time = datetime.now().replace(microsecond=0)
        print("Started training at (GMT) : ", start_time)

        print("==============================================================")

        # logging file
        log_f = open(log_f_name, "w+")
        log_f.write('episode,timestep,reward\n')

        # printing and logging variables
        print_running_reward = 0
        print_running_episodes = 0

        log_running_reward = 0
        log_running_episodes = 0

        time_step = 0
        i_episode = 0

        hyperparameters = {"env": env,
                           "max_ep_len": max_ep_len,
                           "time_step": time_step,
                           "update_timestep": update_timestep,
                           "log_freq": log_freq,
                           "log_running_reward": log_running_reward,
                           "log_running_episodes": log_running_episodes,
                           "i_episode": i_episode,
                           "print_running_reward": print_running_reward,
                           "print_running_episodes": print_running_episodes,
                           "save_model_freq": save_model_freq,
                           "checkpoint_path": checkpoint_path,
                           "start_time": start_time,
                           "log": True,
                           "seed": random_seed,
                           "print_freq": print_freq}

        # ---------- Construct phylogenetic tree ----------- #

        pop = Population()
        pop.branch("agent")
        pop.checkout("agent")
        agents_params = [str(ppo_agent.policy.actor.state_dict())]
        hyperparams = [None, None]
        pop.commit(agents_params[0])

        np.random.seed(random_seed)
        steps = 1

        # training loop
        while time_step <= max_training_timesteps:
            steps += 1
            seed = np.random.randint(2**32 - 1)
            hyperparameters["seed"] = seed

            # Important: IO files cannot be saved as hyperparameters, so if
            # they are passed to the step function in the hyperparameter
            # dictionary (which is, as far as I can tell, the best way to not
            # open and close them constantly, apart from global variables) for
            # logging purposes, they should NOT appear in the
            # hyperparameter_list, and be removed from the hyperparameters
            # before creating the child. This is a bit of a hack, but I don't
            # see any obvious fix right now.

            hyperparameters["log_f"] = log_f
            ppo_agent, new_hyperparameters = step_function(ppo_agent,
                                                           hyperparameters)
            time_step = new_hyperparameters["time_step"]
            hyperparameters.pop("log_f")
            param = str(ppo_agent.policy.actor.state_dict())

            pop.commit(param, hyperparameters)

            agents_params.append(param)
            hyperparams.append(hyperparameters)
            pop._player.hyperparameters["log"] = False
            hyperparameters = new_hyperparameters

        log_f.close()
        env.close()

        # print total training time
        print("==============================================================")
        end_time = datetime.now().replace(microsecond=0)
        print("Started training at (GMT) : ", start_time)
        print("Finished training at (GMT) : ", end_time)
        print("Total training time  : ", end_time - start_time)
        print("==============================================================")

        # Assert that the models were properly saved

        node = pop._nodes["_root"]
        i = -1
        while node.has_descendants():

            self.assertEqual(len(node.descendants), 1)

            if i > -1:
                self.assertEqual(
                    agents_params[i],
                    pop._nodes[node.name].parameters)
            else:
                self.assertIsNone(node.parameters)

            if node.hyperparameters is None:
                self.assertIsNone(hyperparams[i+1])
            else:
                self.assertDictEqual(node.hyperparameters, hyperparams[i+1])
            node = node.descendants[0]
            i += 1

        self.assertEqual(i+1, steps)
