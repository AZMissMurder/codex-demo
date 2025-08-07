import pygame
from utils.assets import load_sprite_for, scale_to_fit


class MainMenu:
    def __init__(self, game):
        self.game = game
        self.title_font = pygame.font.SysFont(None, 64)
        self.button_font = pygame.font.SysFont(None, 36)
        self.tip_font = pygame.font.SysFont(None, 22)
        # Background image expected at assets/ui/menu_bg.png
        self.bg = load_sprite_for("ui", "menu_bg")
        self.button_rect = None

    def enter(self, **kwargs):
        pass

    def exit(self):
        pass

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            from main import boot_new_game
            boot_new_game(self.game)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.button_rect and self.button_rect.collidepoint(event.pos):
                from main import boot_new_game
                boot_new_game(self.game)

    def update(self, dt):
        pass

    def draw(self, screen):
        # Draw background image or gradient fallback
        if self.bg:
            bg_scaled = scale_to_fit(self.bg, screen.get_width(), screen.get_height())
            # center
            x = (screen.get_width() - bg_scaled.get_width()) // 2
            y = (screen.get_height() - bg_scaled.get_height()) // 2
            screen.blit(bg_scaled, (x, y))
        else:
            screen.fill((30, 60, 90))
            for i in range(screen.get_height()):
                c = 90 + int(60 * i / max(1, screen.get_height()))
                pygame.draw.line(screen, (c, c, c), (0, i), (screen.get_width(), i))

        # Title
        title = self.title_font.render("Cursor RPG", True, (255, 255, 255))
        title_rect = title.get_rect(center=(screen.get_width() // 2, screen.get_height() // 3))
        screen.blit(title, title_rect)

        # New Game button
        btn_w, btn_h = 220, 56
        btn_x = (screen.get_width() - btn_w) // 2
        btn_y = int(screen.get_height() * 0.58)
        self.button_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        pygame.draw.rect(screen, (20, 20, 30), self.button_rect)
        pygame.draw.rect(screen, (255, 255, 255), self.button_rect, 2)
        label = self.button_font.render("New Game (Enter)", True, (240, 240, 240))
        lr = label.get_rect(center=self.button_rect.center)
        screen.blit(label, lr)

        # Tip text
        tip = self.tip_font.render("Place a background at assets/ui/menu_bg.png", True, (220, 220, 220))
        screen.blit(tip, (10, screen.get_height() - tip.get_height() - 10))


