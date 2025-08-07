import pygame, sys
from engine import Game
from overworld import Overworld
from battle import Battle

WIDTH, HEIGHT = 800, 600
FPS = 60

def switch_to_overworld(game, ow):
    game.set_state("overworld", overworld=ow)

def boot_new_game(game):
    # Rebuild a fresh overworld and return to it
    ow = Overworld(game)
    game.set_state("overworld", overworld=ow)

class OverworldState:
    def __init__(self, game):
        self.game = game
        self.ow = None

    def enter(self, **kwargs):
        if "overworld" in kwargs and kwargs["overworld"]:
            self.ow = kwargs["overworld"]
        elif not self.ow:
            self.ow = Overworld(self.game)

    def exit(self):
        pass

    def handle_event(self, event):
        self.ow.handle_event(event)

    def update(self, dt):
        self.ow.update(dt)

    def draw(self, screen):
        self.ow.draw(screen)

class BattleState:
    def __init__(self, game):
        self.game = game
        self.battle = None

    def enter(self, **kwargs):
        # kwargs: overworld, party
        self.battle = Battle(self.game, kwargs["overworld"], kwargs["party"], kwargs.get("biome"))

    def exit(self):
        pass

    def handle_event(self, event):
        self.battle.handle_event(event)

    def update(self, dt):
        self.battle.update(dt)

    def draw(self, screen):
        self.battle.draw(screen)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("JRPG Starter")
    clock = pygame.time.Clock()

    states = {
        "overworld": OverworldState(None),
        "battle": BattleState(None),
    }
    # Construct the game without immediately entering a state. We inject the
    # game reference into each state first, then switch to the desired start
    # state. This ensures the overworld is created with a valid game object.
    game = Game(screen, states)
    states["overworld"].game = game
    states["battle"].game = game

    # Boot the game by switching to the overworld state
    game.set_state("overworld")

    while game.running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            game.handle_event(event)

        game.update(dt)
        game.draw()
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
