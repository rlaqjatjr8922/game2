# generated file
import random


class Brain:

    def __init__(self):

        self.dx = random.choice([-1, 0, 1])
        self.dy = random.choice([-1, 0, 1])

        self.timer = random.uniform(0.2, 0.8)

        if self.dx == 0 and self.dy == 0:
            self.dx = 1

    def decide(self, info):
        self.timer -= 0.15

        # 방향 다시 결정
        if self.timer <= 0:

            self.dx = random.choice([-1, 0, 1])
            self.dy = random.choice([-1, 0, 1])

            # 완전 정지 방지
            if self.dx == 0 and self.dy == 0:
                self.dx = random.choice([-1, 1])

            self.timer = random.uniform(0.2, 0.8)

        run = False

        # 랜덤 달리기
        if (
            info["self"]["sp"] > 0
            and random.random() < 0.15
        ):
            run = True

        return {
            "dx": self.dx,
            "dy": self.dy,
            "run": run,
        }