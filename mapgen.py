import random

BIOMES = [
    ("plains", 0.25),
    ("desert", 0.15),
    ("swamp", 0.10),
    ("water", 0.10),
    ("mountain", 0.15),
    ("forest", 0.10),
    ("town", 0.07),
    ("city", 0.05),
    ("dungeon", 0.03),
]

SAFE_BIOMES = {"town", "city"}

BIOME_COLORS = {
    "plains": (80, 200, 120),
    "desert": (230, 220, 120),
    "swamp": (40, 120, 80),
    "water": (70, 130, 200),
    "mountain": (150, 150, 150),
    "forest": (30, 160, 60),
    "town": (160, 110, 60),
    "city": (60, 60, 60),
    "dungeon": (130, 60, 160),
}

def weighted_choice(weights):
    r = random.random() * sum(w for _, w in weights)
    upto = 0
    for item, w in weights:
        if upto + w >= r:
            return item
        upto += w
    assert False

def generate_map(width, height, seed=None):
    rnd = random.Random(seed)
    grid = [[None for _ in range(width)] for _ in range(height)]

    # Simple region seeding for smoother patches
    for y in range(height):
        for x in range(width):
            if x % 6 == 0 and y % 6 == 0:
                base = weighted_choice(BIOMES)
                for dy in range(6):
                    for dx in range(6):
                        if 0 <= y+dy < height and 0 <= x+dx < width:
                            if rnd.random() < 0.85:
                                grid[y+dy][x+dx] = base
                            else:
                                grid[y+dy][x+dx] = weighted_choice(BIOMES)

    # Guarantee at least one town and one dungeon
    grid[rnd.randrange(height)][rnd.randrange(width)] = "town"
    grid[rnd.randrange(height)][rnd.randrange(width)] = "dungeon"
    grid[rnd.randrange(height)][rnd.randrange(width)] = "city"

    return grid
