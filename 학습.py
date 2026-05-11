# generated file
import os
import subprocess
import time
import shutil

from multiprocessing import Process, freeze_support, Lock

from game.core.map import WALLS, MAP_DATA
from game.core.manager import GameManager


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WIDTH = 900
HEIGHT = 600

TOTAL_GAMES = 1000
DT = 6 / 100

PROCESS_COUNT = 18
MERGE_EVERY = 10

WINNER_PATH = os.path.join(BASE_DIR, "winners.txt")

MODEL_ROOT_DIR = os.path.join(BASE_DIR, "data", "models")
WORKER_MODEL_DIR = os.path.join(MODEL_ROOT_DIR, "workers")
LATEST_MODEL_DIR = os.path.join(MODEL_ROOT_DIR, "latest")


def save_winner(winner_name, winner_lock):

    with winner_lock:
        with open(WINNER_PATH, "a", encoding="utf-8") as f:
            f.write(winner_name + "\n")


def force_save_game(game):

    for character in game.characters:

        brain = getattr(character, "brain", None)

        if brain is None:
            continue

        if hasattr(brain, "force_save"):

            try:
                brain.force_save()

            except Exception as e:
                print("[force_save_game] 실패:", e)


def reload_latest_model(game):

    for character in game.characters:

        brain = getattr(character, "brain", None)

        if brain is None:
            continue

        for attr_name in ["tagger_ai", "runner_ai", "ai"]:

            ai = getattr(brain, attr_name, None)

            if ai is None:
                continue

            if hasattr(ai, "load_model"):

                try:
                    ai.load_model()

                except Exception as e:
                    print(
                        f"[reload_latest_model] {attr_name} 실패:",
                        e
                    )


def merge_models():

    merge_path = os.path.join(
        BASE_DIR,
        "merge_models.py"
    )

    if not os.path.exists(merge_path):
        print("[merge] merge_models.py 없음")
        return False

    result = subprocess.run(
        [
            "python",
            merge_path,
        ],
        cwd=BASE_DIR
    )

    if result.returncode != 0:
        print("[merge] merge_models.py 실행 실패")
        return False

    return True


def sync_worker_models_from_latest(process_id):

    os.makedirs(WORKER_MODEL_DIR, exist_ok=True)
    os.makedirs(LATEST_MODEL_DIR, exist_ok=True)

    pairs = [
        (
            "tagger_model_latest.pt",
            f"tagger_model_{process_id}.pt"
        ),
        (
            "runner_model_latest.pt",
            f"runner_model_{process_id}.pt"
        ),
    ]

    for latest_name, worker_name in pairs:

        latest_path = os.path.join(
            LATEST_MODEL_DIR,
            latest_name
        )

        worker_path = os.path.join(
            WORKER_MODEL_DIR,
            worker_name
        )

        if not os.path.exists(latest_path):
            print(
                f"[P{process_id}] latest 없음:",
                latest_path
            )
            continue

        try:
            shutil.copy2(
                latest_path,
                worker_path
            )

            print(
                f"[P{process_id}] latest -> worker 덮어쓰기 완료:",
                worker_name
            )

        except Exception as e:
            print(
                f"[P{process_id}] worker 동기화 실패:",
                e
            )


def create_game(load_latest=True):

    game = GameManager(
        WIDTH,
        HEIGHT,
        ai_count=4,
        use_player=False
    )

    if load_latest:
        reload_latest_model(game)

    return game


def run_training_chunk(process_id, round_id, games_to_run, winner_lock):

    os.environ["PROCESS_ID"] = str(process_id)

    sync_worker_models_from_latest(process_id)

    completed_games = 0
    game = create_game(load_latest=True)

    while completed_games < games_to_run:

        game.update(
            DT,
            WALLS,
            MAP_DATA
        )

        if not game.game_over:
            continue

        force_save_game(game)

        completed_games += 1

        if game.winner:
            winner_name = game.winner.name
        else:
            winner_name = "없음"

        save_winner(winner_name, winner_lock)

        print(
            f"[ROUND {round_id}] "
            f"[P{process_id}] "
            f"{completed_games}/{games_to_run} "
            f"승자: {winner_name}"
        )

        game = create_game(load_latest=True)

    print(
        f"[ROUND {round_id}] "
        f"[P{process_id}] chunk 종료"
    )


def run_round(round_id, games_to_run, winner_lock):

    print("=" * 60)
    print(f"[ROUND {round_id}] 시작")
    print(f"[ROUND {round_id}] 각 프로세스 {games_to_run}판씩 실행")
    print("=" * 60)

    processes = []

    for i in range(PROCESS_COUNT):

        process_id = i + 1

        p = Process(
            target=run_training_chunk,
            args=(
                process_id,
                round_id,
                games_to_run,
                winner_lock,
            )
        )

        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    print(f"[ROUND {round_id}] 모든 프로세스 학습 완료")
    print(f"[ROUND {round_id}] 모델 병합 시작")

    merged = merge_models()

    if merged:
        print(f"[ROUND {round_id}] 모델 병합 완료")
    else:
        print(f"[ROUND {round_id}] 모델 병합 실패 또는 병합 파일 없음")


if __name__ == "__main__":

    freeze_support()

    os.makedirs(WORKER_MODEL_DIR, exist_ok=True)
    os.makedirs(LATEST_MODEL_DIR, exist_ok=True)

    winner_lock = Lock()

    total_done = 0
    round_id = 1

    while total_done < TOTAL_GAMES:

        remaining_games = TOTAL_GAMES - total_done
        games_to_run = min(MERGE_EVERY, remaining_games)

        run_round(
            round_id,
            games_to_run,
            winner_lock
        )

        total_done += games_to_run

        print(
            f"[MAIN] 라운드 완료: "
            f"{total_done}/{TOTAL_GAMES}"
        )

        round_id += 1
        time.sleep(0.5)

    print("전체 학습 종료")