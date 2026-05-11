# generated file
import os
import time
import torch


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_ROOT_DIR = os.path.join(
    BASE_DIR,
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


def get_model_files(model_type):

    files = []

    if not os.path.exists(WORKER_MODEL_DIR):
        return files

    for filename in os.listdir(WORKER_MODEL_DIR):

        if not filename.endswith(".pt"):
            continue

        if not filename.startswith(
            f"{model_type}_model_"
        ):
            continue

        if "latest" in filename:
            continue

        full_path = os.path.join(
            WORKER_MODEL_DIR,
            filename
        )

        files.append(full_path)

    return files


def average_models(model_type):

    model_files = get_model_files(model_type)

    if not model_files:

        print(
            f"[merge] {model_type} worker 모델 없음"
        )

        return False

    print(
        f"[merge] {model_type} 병합 시작 "
        f"({len(model_files)}개)"
    )

    merged_state = None
    input_size = None
    valid_count = 0

    for path in model_files:

        try:

            data = torch.load(
                path,
                map_location="cpu"
            )

            if "model_state" not in data:

                print(
                    "[merge] model_state 없음:",
                    path
                )

                continue

            current_input_size = data.get(
                "input_size"
            )

            if input_size is None:
                input_size = current_input_size

            if current_input_size != input_size:

                print(
                    "[merge] input_size 다름:",
                    path
                )

                continue

            state = data["model_state"]

            if merged_state is None:

                merged_state = {}

                for key, value in state.items():

                    merged_state[key] = (
                        value.clone().float()
                    )

            else:

                for key, value in state.items():

                    merged_state[key] += (
                        value.clone().float()
                    )

            valid_count += 1

            print(
                f"[merge] 로드 성공: "
                f"{os.path.basename(path)}"
            )

        except Exception as e:

            print(
                f"[merge] 로드 실패: "
                f"{path}"
            )

            print(e)

    if valid_count <= 0:

        print(
            f"[merge] {model_type} "
            f"유효 모델 없음"
        )

        return False

    for key in merged_state:

        merged_state[key] /= valid_count

    latest_path = os.path.join(
        LATEST_MODEL_DIR,
        f"{model_type}_model_latest.pt"
    )

    temp_path = latest_path + ".tmp"

    save_data = {
        "model_state": merged_state,
        "input_size": input_size,
        "model_type": model_type,
        "merged_count": valid_count,
        "merged_time": time.time(),
    }

    try:

        torch.save(
            save_data,
            temp_path
        )

        os.replace(
            temp_path,
            latest_path
        )

        print(
            f"[merge] latest 저장 완료:"
        )

        print(latest_path)

        return True

    except Exception as e:

        print(
            f"[merge] latest 저장 실패:"
        )

        print(e)

        return False


def main():

    os.makedirs(
        WORKER_MODEL_DIR,
        exist_ok=True
    )

    os.makedirs(
        LATEST_MODEL_DIR,
        exist_ok=True
    )

    tagger_ok = average_models("tagger")
    runner_ok = average_models("runner")

    print("=" * 50)

    if tagger_ok:
        print("[merge] tagger 병합 성공")
    else:
        print("[merge] tagger 병합 실패")

    if runner_ok:
        print("[merge] runner 병합 성공")
    else:
        print("[merge] runner 병합 실패")

    print("[merge] 전체 병합 종료")


if __name__ == "__main__":
    main()