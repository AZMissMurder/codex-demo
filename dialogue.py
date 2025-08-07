import pygame, textwrap

class DialogueBox:
    """Reusable dialogue box with typewriter effect and multi-page text.
    Call open(lines, on_close=None) to start; handle_event() to advance; draw() each frame.
    While active, you should pause player movement/inputs besides advancing dialogue.
    """
    def __init__(self, screen_size, font=None, margin=16):
        self.screen_w, self.screen_h = screen_size
        self.font = font or pygame.font.SysFont(None, 24)
        self.margin = margin
        self.active = False
        self.pages = []  # list of strings (one per page)
        self.page_idx = 0
        self.char_idx = 0
        self.chars_per_tick = 2
        self.on_close = None
        self.box_height = int(self.screen_h * 0.32)
        self.tick_accum = 0.0

    def _wrap_into_pages(self, lines):
        # Wrap text to box width and split into pages that fit ~8 lines.
        max_width = self.screen_w - self.margin*2 - 20
        wrapped = []
        for line in lines:
            wrapped += textwrap.wrap(line, width=60) if len(line) > 0 else [""]
        # group lines into pages
        lines_per_page = 7
        pages = []
        for i in range(0, len(wrapped), lines_per_page):
            page_lines = wrapped[i:i+lines_per_page]
            pages.append("\n".join(page_lines))
        return pages or [""]

    def open(self, lines, on_close=None):
        if isinstance(lines, str):
            lines = [lines]
        self.pages = self._wrap_into_pages(lines)
        self.page_idx = 0
        self.char_idx = 0
        self.active = True
        self.on_close = on_close

    def handle_event(self, event):
        if not self.active:
            return
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
            page = self.pages[self.page_idx]
            if self.char_idx < len(page):
                # fast-forward current page
                self.char_idx = len(page)
            else:
                # next page or close
                if self.page_idx < len(self.pages) - 1:
                    self.page_idx += 1
                    self.char_idx = 0
                else:
                    self.active = False
                    if self.on_close:
                        cb = self.on_close
                        self.on_close = None
                        cb()

    def update(self, dt):
        if not self.active:
            return
        # typewriter
        self.tick_accum += dt
        speed = 60  # cps baseline
        step = int(self.tick_accum * speed * (self.chars_per_tick/2))
        if step > 0:
            self.tick_accum = 0.0
            page = self.pages[self.page_idx]
            if self.char_idx < len(page):
                self.char_idx = min(len(page), self.char_idx + step)

    def draw(self, screen):
        if not self.active:
            return
        # box
        w, h = self.screen_w, self.box_height
        x, y = 0, self.screen_h - h
        # background
        pygame.draw.rect(screen, (15, 15, 25), (x, y, w, h))
        pygame.draw.rect(screen, (255, 255, 255), (x+6, y+6, w-12, h-12), 2)

        # text
        page = self.pages[self.page_idx]
        shown = page[:self.char_idx]
        lines = shown.split("\n")
        ty = y + 18
        for line in lines:
            img = self.font.render(line, True, (235,235,235))
            screen.blit(img, (x + 20, ty))
            ty += self.font.get_height() + 4

        # continue tip
        tip = self.font.render("Space/Enter to continue", True, (200,200,200))
        screen.blit(tip, (w - tip.get_width() - 24, y + h - tip.get_height() - 10))
