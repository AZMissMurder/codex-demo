import random

class Ability:
    def __init__(self, name, power, target="enemy", heal=False):
        self.name = name
        self.power = power
        self.target = target  # 'enemy' or 'ally'
        self.heal = heal

BASIC_ABILITIES = [
    Ability("Strike", power=10, target="enemy"),
    Ability("Fireball", power=16, target="enemy"),
    Ability("Pierce", power=12, target="enemy"),
    Ability("Heal", power=12, target="ally", heal=True),
]

LEARN_SET = [
    (2, Ability("Power Strike", power=18, target="enemy")),
    (3, Ability("Blaze", power=24, target="enemy")),
    (4, Ability("Greater Heal", power=22, target="ally", heal=True)),
]

def hp_by_elapsed_minutes(base, minutes):
    # Scale HP as time passes to reflect difficulty curve.
    # e.g., +5 HP per minute, +/- small randomness
    return int(base + minutes * 5 + random.randint(-3, 3))

class Combatant:
    def __init__(self, name, level, max_hp, abilities=None, is_player=False):
        self.name = name
        self.level = level
        self.max_hp = max_hp
        self.hp = max_hp
        self.abilities = abilities[:] if abilities else []
        self.is_player = is_player

    @property
    def alive(self):
        return self.hp > 0

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

class Character(Combatant):
    def __init__(self, name, level=1, max_hp=60, abilities=None):
        super().__init__(name, level, max_hp, abilities or BASIC_ABILITIES[:2], is_player=True)
        self.xp = 0

    def xp_to_next(self):
        # Quadratic-ish curve
        return self.level * self.level * 25

    def gain_xp(self, amount):
        self.xp += amount
        leveled = False
        while self.xp >= self.xp_to_next():
            self.xp -= self.xp_to_next()
            self.level += 1
            self.max_hp += 6
            self.hp = self.max_hp  # heal on level up
            # Learn abilities at thresholds
            for req, ability in LEARN_SET:
                if self.level == req and all(a.name != ability.name for a in self.abilities):
                    self.abilities.append(ability)
            leveled = True
        return leveled

class Monster(Combatant):
    pass

class Party:
    def __init__(self, members=None, max_size=4):
        self.members = members[:] if members else []
        self.max_size = max_size

    def alive_members(self):
        return [m for m in self.members if m.alive]

    def add(self, char):
        if len(self.members) < self.max_size:
            self.members.append(char)
            return True
        return False

    def is_wiped(self):
        return len(self.alive_members()) == 0

# Simple name pools
NPC_NAMES = [
    "Ari", "Reeve", "Mila", "Taro", "Soren", "Nyx", "Wren", "Kael", "Lina", "Bram",
    "Rhea", "Orrin", "Vale", "Eira", "Cass", "Ivo", "Nox", "Luca", "Skye", "Pax",
]

MONSTER_NAMES = [
    "Slime", "Wisp", "Boar", "Kobold", "Imp", "Ghoul", "Warg", "Golem", "Mimic",
]
