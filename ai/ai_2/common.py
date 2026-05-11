# generated file
import os
import math
import random
import time

import torch
import torch.nn as nn
import torch.optim as optim


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ROOT_DIR = os.path.dirname(
    os.path.dirname(BASE_DIR)
)

MODEL_ROOT_DIR = os.path.join(
    ROOT_DIR,
    "data",
    "models"
)

WORKER_MODEL_DIR = os.path.join(
    MODEL_ROOT_DIR,
    "workers"
)

LATEST_MODEL_DIR = os.path.join(
    MODEL_ROOT_DIR,
    "latest"
)

os.makedirs(WORKER_MODEL_DIR, exist_ok=True)
os.makedirs(LATEST_MODEL_DIR, exist_ok=True)


ACTIONS = [
    (0, 0, False),

    (-1, 0, False),
    (1, 0, False),
    (0, -1, False),
    (0, 1, False),
    (-1, -1, False),
    (1, -1, False),
    (-1, 1, False),
    (1, 1, False),

    (-1, 0, True),
    (1, 0, True),
    (0, -1, True),
    (0, 1, True),
    (-1, -1, True),
    (1, -1, True),
    (-1, 1, True),
    (1, 1, True),
]


class RewardNet(nn.Module):

    def __init__(self, input_size):
        super().__init__()

        self.net = nn.Sequential(
            nn.Linear(input_size, 512),
            nn.ReLU(),

            nn.Linear(512, 256),
            nn.ReLU(),

            nn.Linear(256, 128),
            nn.ReLU(),

            nn.Linear(128, 64),
            nn.ReLU(),

            nn.Linear(64, 1),
        )

    def forward(self, x):
        return self.net(x)


def safe_float(value, default=0.0):
    try:
        return float(value)
    except:
        return default


def safe_bool(value):
    return 1.0 if bool(value) else 0.0


def make_dummy_state():

    return {
        "map": [["0"] * 15 for _ in range(10)],

        "self": {
            "name": "AI",
            "center_x": 0,
            "center_y": 0,
            "hp": 100,
            "sp": 50,
            "is_tagger": False,
        },

        "players": [
            {
                "name": f"AI {i}",
                "center_x": 0,
                "center_y": 0,
                "hp": 100,
                "sp": 50,
                "is_tagger": False,
            }
            for i in range(4)
        ],

        "catch_player": False,
        "catched": False,
    }


def normalize_tile(tile):
    try:
        return float(tile) / 5.0
    except:
        return 0.0


def add_player_features(features, me, p):
    my_x = safe_float(me.get("center_x", 0))
    my_y = safe_float(me.get("center_y", 0))

    px = safe_float(p.get("center_x", 0))
    py = safe_float(p.get("center_y", 0))

    diff_x = px - my_x
    diff_y = py - my_y
    dist = math.hypot(diff_x, diff_y)

    features += [
        px / 1000.0,
        py / 1000.0,

        safe_float(p.get("hp", 100)) / 100.0,
        safe_float(p.get("sp", 50)) / 100.0,

        safe_bool(p.get("is_tagger", False)),

        diff_x / 1000.0,
        diff_y / 1000.0,
        dist / 1000.0,
    ]


def add_empty_player_features(features):
    features += [
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
    ]


def get_nearest_player(me, players, want_tagger=None):
    my_x = safe_float(me.get("center_x", 0))
    my_y = safe_float(me.get("center_y", 0))
    my_name = me.get("name", None)

    nearest = None
    nearest_dist = 999999.0

    for p in players:
        if my_name is not None and p.get("name") == my_name:
            continue

        if want_tagger is not None:
            if bool(p.get("is_tagger", False)) != want_tagger:
                continue

        px = safe_float(p.get("center_x", 0))
        py = safe_float(p.get("center_y", 0))

        dist = math.hypot(px - my_x, py - my_y)

        if dist < nearest_dist:
            nearest_dist = dist
            nearest = p

    return nearest, nearest_dist


def state_to_features(state, action):

    features = []

    game_map = state.get("map", [])

    for row in game_map:
        for tile in row:
            features.append(normalize_tile(tile))

    me = state.get("self", {})

    features += [
        safe_float(me.get("center_x", 0)) / 1000.0,
        safe_float(me.get("center_y", 0)) / 1000.0,
        safe_float(me.get("hp", 100)) / 100.0,
        safe_float(me.get("sp", 50)) / 100.0,
        safe_bool(me.get("is_tagger", False)),
    ]

    players = list(state.get("players", []))

    used = 0
    for p in players:
        if used >= 4:
            break

        add_player_features(features, me, p)
        used += 1

    while used < 4:
        add_empty_player_features(features)
        used += 1

    nearest, _ = get_nearest_player(
        me,
        players,
        want_tagger=None
    )

    if nearest is not None:
        add_player_features(features, me, nearest)
    else:
        add_empty_player_features(features)

    nearest_tagger, _ = get_nearest_player(
        me,
        players,
        want_tagger=True
    )

    if nearest_tagger is not None:
        add_player_features(features, me, nearest_tagger)
    else:
        add_empty_player_features(features)

    nearest_runner, _ = get_nearest_player(
        me,
        players,
        want_tagger=False
    )

    if nearest_runner is not None:
        add_player_features(features, me, nearest_runner)
    else:
        add_empty_player_features(features)

    features += [
        safe_bool(state.get("catch_player", False)),
        safe_bool(state.get("catched", False)),
    ]

    dx, dy, run = action

    features += [
        float(dx),
        float(dy),
        safe_bool(run),
    ]

    return features


class OnlineRewardAI:

    def __init__(self, model_type):

        self.model_type = model_type

        self.process_id = os.environ.get(
            "PROCESS_ID",
            "0"
        )

        self.worker_model_path = os.path.join(
            WORKER_MODEL_DIR,
            f"{model_type}_model_{self.process_id}.pt"
        )

        self.latest_model_path = os.path.join(
            LATEST_MODEL_DIR,
            f"{model_type}_model_latest.pt"
        )

        dummy_features = state_to_features(
            make_dummy_state(),
            ACTIONS[0],
        )

        self.input_size = len(dummy_features)

        self.model = RewardNet(self.input_size)

        self.optimizer = optim.Adam(
            self.model.parameters(),
            lr=0.0001,
        )

        self.loss_fn = nn.MSELoss()

        self.replay_X = []
        self.replay_y = []

        self.batch_size = 512
        self.max_replay = 30000

        self.temperature = 1.0

        self.load_model()

    def load_model(self):

        load_path = None

        if os.path.exists(self.latest_model_path):
            load_path = self.latest_model_path

        elif os.path.exists(self.worker_model_path):
            load_path = self.worker_model_path

        if load_path is None:
            print(
                f"[{self.model_type}] 모델 없음:",
                self.latest_model_path,
                self.worker_model_path
            )
            return

        try:
            data = torch.load(
                load_path,
                map_location="cpu"
            )

            if data.get("input_size") != self.input_size:
                print(
                    f"[{self.model_type}] 입력 크기 다름. "
                    "기존 pt 삭제 필요:",
                    load_path
                )
                return

            self.model.load_state_dict(
                data["model_state"]
            )

            print(
                f"[{self.model_type}] 모델 로드 완료:",
                load_path
            )

        except Exception as e:
            print(
                f"[{self.model_type}] 모델 로드 실패:",
                e
            )

    def save_model(self):

        temp_path = self.worker_model_path + ".tmp"

        torch.save(
            {
                "model_state": self.model.state_dict(),
                "input_size": self.input_size,
                "model_type": self.model_type,
            },
            temp_path,
        )

        last_error = None

        for _ in range(30):

            try:
                os.replace(
                    temp_path,
                    self.worker_model_path
                )
                return

            except PermissionError as e:
                last_error = e
                time.sleep(0.1)

        print(
            f"[{self.model_type}] 모델 저장 실패:",
            last_error
        )

    def choose_action(self, info):

        scores = []

        self.model.eval()

        with torch.no_grad():

            for action in ACTIONS:

                features = state_to_features(
                    info,
                    action
                )

                x = torch.tensor(
                    [features],
                    dtype=torch.float32,
                )

                score = self.model(x).item()

                scores.append(score)

        scores_tensor = torch.tensor(
            scores,
            dtype=torch.float32,
        )

        probs = torch.softmax(
            scores_tensor / self.temperature,
            dim=0
        ).numpy()

        action_index = random.choices(
            range(len(ACTIONS)),
            weights=probs,
            k=1,
        )[0]

        return ACTIONS[action_index]

    def remember_feature(
        self,
        info,
        action,
        target_reward
    ):

        features = state_to_features(
            info,
            action
        )

        self.replay_X.append(features)

        self.replay_y.append([
            target_reward
        ])

        if len(self.replay_X) > self.max_replay:
            self.replay_X.pop(0)
            self.replay_y.pop(0)

    def learn_from_episode(
        self,
        episode_steps,
        gamma=0.98
    ):

        if not episode_steps:
            return

        future_reward = 0.0

        for row in reversed(episode_steps):

            reward = float(row["reward"])

            future_reward = reward + gamma * future_reward

            future_reward = max(
                -300,
                min(300, future_reward)
            )

            action = row["action"]

            action_tuple = (
                action["dx"],
                action["dy"],
                action["run"],
            )

            self.remember_feature(
                row["state"],
                action_tuple,
                future_reward,
            )

        self.train_online()

    def train_online(self):

        if len(self.replay_X) < 1:
            return

        batch_size = min(
            self.batch_size,
            len(self.replay_X),
        )

        indexes = random.sample(
            range(len(self.replay_X)),
            batch_size,
        )

        X = [
            self.replay_X[i]
            for i in indexes
        ]

        y = [
            self.replay_y[i]
            for i in indexes
        ]

        X = torch.tensor(
            X,
            dtype=torch.float32
        )

        y = torch.tensor(
            y,
            dtype=torch.float32
        )

        self.model.train()

        pred = self.model(X)

        loss = self.loss_fn(
            pred,
            y
        )

        self.optimizer.zero_grad()
        loss.backward()

        torch.nn.utils.clip_grad_norm_(
            self.model.parameters(),
            0.5
        )

        self.optimizer.step()

        print(
            f"[{self.model_type} P{self.process_id}] "
            f"loss = {round(loss.item(), 4)}"
        )

        self.save_model()

        self.replay_X.clear()
        self.replay_y.clear()