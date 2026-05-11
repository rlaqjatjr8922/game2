# generated file
import random


class ItemSystem:
    def __init__(self):
        pass

    # 일반 상자: SP 회복만
    def apply_normal_box(self, character):
        character.sp += 60

        if character.sp > character.max_sp:
            character.sp = character.max_sp

    # 저주 상자: HP저주 / SP저주
    def apply_curse_box(self, opener, characters):
        roll = random.random()

        # HP저주 50%
        if roll < 0.5:
            for character in characters:
                if character == opener:
                    continue

                character.hp -= 10

                if character.hp < 0:
                    character.hp = 0

        # SP저주 50%
        else:
            for character in characters:
                if character == opener:
                    continue

                character.sp -= 50

                if character.sp < 0:
                    character.sp = 0