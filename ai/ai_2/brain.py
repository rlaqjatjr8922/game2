# generated file
import os
import pickle
import h5py
import numpy as np
import time

from .common import OnlineRewardAI


AI_DIR = os.path.dirname(os.path.abspath(__file__))

ROOT_DIR = os.path.dirname(
    os.path.dirname(AI_DIR)
)

RAW_DIR = os.path.join(ROOT_DIR, "data", "raw")
MEMORY_DIR = os.path.join(ROOT_DIR, "data", "memory")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(MEMORY_DIR, exist_ok=True)


EVENT_REWARD = 10.0
TIME_REWARD = 0.01


class Brain:

    def __init__(self):

        self.process_id = os.environ.get("PROCESS_ID", "0")

        self.learn_data_path = os.path.join(
            RAW_DIR,
            f"learn_data_{self.process_id}.h5"
        )

        self.memory_path = os.path.join(
            MEMORY_DIR,
            f"memory_{self.process_id}.pkl"
        )

        self.tagger_score = 0
        self.runner_score = 0

        self.memory = self.load_memory()

        self.tagger_steps = []
        self.runner_steps = []

        self.game_id = 0
        self.step_id = 0
        self.dataset_index = 0

        self.tagger_ai = OnlineRewardAI("tagger")
        self.runner_ai = OnlineRewardAI("runner")

        self.pending_tagger_state = None
        self.pending_tagger_action = None

        self.pending_runner_state = None
        self.pending_runner_action = None

        self.prev_is_tagger = None

    def load_memory(self):

        default_memory = {
            "games": 0,
            "event_trains": 0,

            "tagger_total_score": 0,
            "runner_total_score": 0,

            "tagger_best_score": 0,
            "runner_best_score": 0,
        }

        if not os.path.exists(self.memory_path):
            return default_memory

        try:
            with open(self.memory_path, "rb") as f:
                memory = pickle.load(f)

            for key, value in default_memory.items():
                if key not in memory:
                    memory[key] = value

            return memory

        except:
            return default_memory

    def save_memory(self):

        temp_path = self.memory_path + ".tmp"

        with open(temp_path, "wb") as f:
            pickle.dump(self.memory, f)

        last_error = None

        for _ in range(30):
            try:
                os.replace(temp_path, self.memory_path)
                return
            except PermissionError as e:
                last_error = e
                time.sleep(0.1)

        print("[save_memory] 저장 실패:", last_error)

    def add_step(self, step_list, info, action, reward, model_type):

        row = {
            "process_id": self.process_id,
            "game_id": self.game_id,
            "step_id": self.step_id,
            "model_type": model_type,
            "state": info,
            "action": action,
            "reward": reward,

            "tagger_score": self.tagger_score,
            "runner_score": self.runner_score,
        }

        step_list.append(row)
        self.step_id += 1

    def get_next_dataset_name(self, group):

        while str(self.dataset_index) in group:
            self.dataset_index += 1

        name = str(self.dataset_index)
        self.dataset_index += 1

        return name

    def flush_steps(self):

        all_steps = []

        all_steps.extend(self.tagger_steps)
        all_steps.extend(self.runner_steps)

        if not all_steps:
            return

        with h5py.File(self.learn_data_path, "a") as f:

            group = f.require_group("steps")

            for row in all_steps:

                row_binary = pickle.dumps(row)

                row_array = np.frombuffer(
                    row_binary,
                    dtype=np.uint8
                )

                dataset_name = self.get_next_dataset_name(group)

                group.create_dataset(
                    dataset_name,
                    data=row_array,
                )

    def train_tagger_now(self):

        if not self.tagger_steps:
            return

        episode_steps = list(self.tagger_steps)

        self.tagger_ai.learn_from_episode(
            episode_steps,
            gamma=0.995,
        )

        self.tagger_ai.save_model()

        self.tagger_steps.clear()

        self.memory["event_trains"] += 1
        self.save_memory()

        print(
            f"[P{self.process_id}] "
            f"추격자 모델 즉시 학습 완료"
        )

    def train_runner_now(self):

        if not self.runner_steps:
            return

        episode_steps = list(self.runner_steps)

        self.runner_ai.learn_from_episode(
            episode_steps,
            gamma=0.995,
        )

        self.runner_ai.save_model()

        self.runner_steps.clear()

        self.memory["event_trains"] += 1
        self.save_memory()

        print(
            f"[P{self.process_id}] "
            f"도망자 모델 즉시 학습 완료"
        )

    def update_memory_game_end(self):

        self.memory["games"] += 1

        self.memory["tagger_total_score"] += self.tagger_score
        self.memory["runner_total_score"] += self.runner_score

        if self.tagger_score > self.memory["tagger_best_score"]:
            self.memory["tagger_best_score"] = self.tagger_score

        if self.runner_score > self.memory["runner_best_score"]:
            self.memory["runner_best_score"] = self.runner_score

        self.save_memory()

    def add_time_reward(self, current_is_tagger):

        if current_is_tagger:

            self.tagger_score -= TIME_REWARD

            if (
                self.pending_tagger_state is not None
                and self.pending_tagger_action is not None
            ):
                self.add_step(
                    self.tagger_steps,
                    self.pending_tagger_state,
                    self.pending_tagger_action,
                    -TIME_REWARD,
                    "tagger"
                )

        else:

            self.runner_score += TIME_REWARD

            if (
                self.pending_runner_state is not None
                and self.pending_runner_action is not None
            ):
                self.add_step(
                    self.runner_steps,
                    self.pending_runner_state,
                    self.pending_runner_action,
                    TIME_REWARD,
                    "runner"
                )

    def decide(self, info):

        me = info["self"]
        current_is_tagger = me["is_tagger"]

        became_tagger = False
        became_runner = False

        if self.prev_is_tagger is not None:

            if (
                self.prev_is_tagger is False
                and current_is_tagger is True
            ):
                became_tagger = True

            elif (
                self.prev_is_tagger is True
                and current_is_tagger is False
            ):
                became_runner = True

        self.add_time_reward(current_is_tagger)

        if became_runner:

            reward = EVENT_REWARD
            self.tagger_score += EVENT_REWARD

            if (
                self.pending_tagger_state is not None
                and self.pending_tagger_action is not None
            ):
                self.add_step(
                    self.tagger_steps,
                    self.pending_tagger_state,
                    self.pending_tagger_action,
                    reward,
                    "tagger"
                )

            self.flush_steps()
            self.train_tagger_now()

            self.pending_tagger_state = None
            self.pending_tagger_action = None

        if became_tagger:

            reward = -EVENT_REWARD
            self.runner_score -= EVENT_REWARD

            if (
                self.pending_runner_state is not None
                and self.pending_runner_action is not None
            ):
                self.add_step(
                    self.runner_steps,
                    self.pending_runner_state,
                    self.pending_runner_action,
                    reward,
                    "runner"
                )

            self.flush_steps()
            self.train_runner_now()

            self.pending_runner_state = None
            self.pending_runner_action = None

        if current_is_tagger:

            dx, dy, run = self.tagger_ai.choose_action(info)

            if me["sp"] <= 0:
                run = False

            action = {
                "dx": dx,
                "dy": dy,
                "run": run,
            }

            self.pending_tagger_state = info
            self.pending_tagger_action = action

        else:

            dx, dy, run = self.runner_ai.choose_action(info)

            if me["sp"] <= 0:
                run = False

            action = {
                "dx": dx,
                "dy": dy,
                "run": run,
            }

            self.pending_runner_state = info
            self.pending_runner_action = action

        self.prev_is_tagger = current_is_tagger

        return {
            "dx": dx,
            "dy": dy,
            "run": run,

            "tagger_score": self.tagger_score,
            "runner_score": self.runner_score,
        }

    def force_save(self):

        if (
            self.pending_tagger_state is not None
            and self.pending_tagger_action is not None
        ):
            self.add_step(
                self.tagger_steps,
                self.pending_tagger_state,
                self.pending_tagger_action,
                0.0,
                "tagger"
            )

            self.pending_tagger_state = None
            self.pending_tagger_action = None

        if (
            self.pending_runner_state is not None
            and self.pending_runner_action is not None
        ):
            self.add_step(
                self.runner_steps,
                self.pending_runner_state,
                self.pending_runner_action,
                0.0,
                "runner"
            )

            self.pending_runner_state = None
            self.pending_runner_action = None

        self.flush_steps()
        self.update_memory_game_end()

        self.tagger_steps.clear()
        self.runner_steps.clear()

        self.game_id += 1
        self.step_id = 0

        self.tagger_score = 0
        self.runner_score = 0

        self.prev_is_tagger = None