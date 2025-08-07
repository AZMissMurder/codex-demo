import pygame

class State:
    def __init__(self, game):
        self.game = game

    def enter(self, **kwargs):
        pass

    def exit(self):
        pass

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, screen):
        pass


class Game:
    def __init__(self, screen, states, start_state):
        self.screen = screen
        self.states = states
        self.current = None
        self.running = True
        self.state_stack = []
        self.time_started_ms = pygame.time.get_ticks()

        self.set_state(start_state)

    def set_state(self, name, **kwargs):
        if self.current:
            self.current.exit()
        self.current = self.states[name]
        self.current.enter(**kwargs)

    def elapsed_minutes(self):
        return max(0.0, (pygame.time.get_ticks() - self.time_started_ms) / 60000.0)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.running = False
        else:
            self.current.handle_event(event)

    def update(self, dt):
        self.current.update(dt)

    def draw(self):
        self.current.draw(self.screen)
