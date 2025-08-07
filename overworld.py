import pygame, random
from dialogue import DialogueBox
from mapgen import generate_map, BIOME_COLORS, SAFE_BIOMES
from entities import Character, Party, NPC_NAMES, hp_by_elapsed_minutes
from quests import QuestManager

TILE = 24
VIEW_W, VIEW_H = 32, 20  # in tiles
MAP_W, MAP_H = 64, 64

class Overworld:
    def __init__(self, game):
        self.game = game
        self.map = generate_map(MAP_W, MAP_H, seed=1337)
        self.player_pos = [MAP_W//2, MAP_H//2]
        self.party = Party([Character("You", level=1, max_hp=60)], max_size=4)

        # Quests
        self.quests = QuestManager(self)
        self.quest_nodes = self.quests.generate_world_nodes(self.map, count=8)

        # NPCs spawn mostly in towns/cities
        self.npcs = self._spawn_npcs(40)
        self.font = pygame.font.SysFont(None, 22)
        self.bigfont = pygame.font.SysFont(None, 28)
        self.help = False
        self.dialogue = DialogueBox((self.game.screen.get_width(), self.game.screen.get_height()))
        self.shown_intro = False
        self.message = None
        self.message_timer = 0

        self.steps_since_last_encounter = 0
        self.encounter_base = 0.05  # per step probability

    def _spawn_npcs(self, count):
        out = []
        tries = 0
        while len(out) < count and tries < 2000:
            tries += 1
            x = random.randrange(MAP_W)
            y = random.randrange(MAP_H)
            if self.map[y][x] in ("town", "city"):
                out.append({"x": x, "y": y, "name": random.choice(NPC_NAMES)})
        return out

    def enter(self):
        # Intro dialogue once at start
        if not self.shown_intro:
            self.shown_intro = True
            intro_lines = [
                "Hometown, dawn.",
                "The kingdom reels from the king's murder.",
                "You set out to find the truth—if you survive the wilds...",
                "Tip: Recruit allies in towns/cities (press E when adjacent)."
            ]
            self.dialogue.open(intro_lines)


    def exit(self):
        pass

    def _tile_at(self, x, y):
        if 0 <= x < MAP_W and 0 <= y < MAP_H:
            return self.map[y][x]
        return "plains"

    def _move_player(self, dx, dy):
        nx = max(0, min(MAP_W-1, self.player_pos[0] + dx))
        ny = max(0, min(MAP_H-1, self.player_pos[1] + dy))
        if [nx, ny] != self.player_pos:
            self.player_pos = [nx, ny]
            biome = self._tile_at(nx, ny)
            # Main quest city trigger
            if biome == "city":
                desc = self.quests.trigger_main_on_city_enter(nx, ny)
                if desc:
                    self.dialogue.open(desc)
            # REACH quest checks
            msgs = self.quests.on_enter_tile(nx, ny, biome)
            if msgs:
                self.dialogue.open(msgs)
            self._check_random_encounter()

    def _adjacent_npc(self):
        for npc in self.npcs:
            if abs(npc["x"] - self.player_pos[0]) + abs(npc["y"] - self.player_pos[1]) == 1:
                return npc
        return None

        
    def _adjacent_quest_node(self):
        for qn in self.quest_nodes:
            if qn.get('taken'):
                continue
            if abs(qn["x"] - self.player_pos[0]) + abs(qn["y"] - self.player_pos[1]) == 1:
                return qn
        return None

    def _check_random_encounter(self):
        self.steps_since_last_encounter += 1
        biome = self._tile_at(*self.player_pos)
        if biome in SAFE_BIOMES:
            return
        # Slightly rising encounter odds with time and steps
        minutes = self.game.elapsed_minutes()
        chance = self.encounter_base + min(0.25, minutes * 0.01) + self.steps_since_last_encounter * 0.003
        if random.random() < chance:
            self.steps_since_last_encounter = 0
            # Trigger encounter
            biome = biome
            from battle import Battle
            self.game.set_state("battle", overworld=self, party=self.party, biome=biome)

    def handle_event(self, event):
        # If dialogue is active, it consumes input
        if self.dialogue.active:
            self.dialogue.handle_event(event)
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                # Show quest log
                lines = self.quests.list_active_lines() + [""] + self.quests.list_completed_lines()
                self.dialogue.open(lines)
                return
            if event.key == pygame.K_h:
                self.help = not self.help
            if event.key == pygame.K_e:
                # 1) Quest node nearby?
                qn = self._adjacent_quest_node()
                if qn and not qn.get('taken'):
                    quest = self.quests.create_side_quest_at(qn)
                    def accept():
                        self.quests.accept_quest(quest)
                        qn['taken'] = True
                    self.dialogue.open([
                        "You found a quest giver!",
                        quest.title,
                        quest.description,
                        "(Quest accepted)"
                    ], on_close=accept)
                    return
                # 2) NPC recruit
                npc = self._adjacent_npc()
                if npc:
                    if len(self.party.members) >= self.party.max_size:
                        self.dialogue.open(["Party full (max 4)."], on_close=None)
                    else:
                        minutes = self.game.elapsed_minutes()
                        hp = hp_by_elapsed_minutes(50 + random.randint(-10, 10), minutes)
                        new_join = Character(npc["name"], level=max(1, int(minutes)//4 + 1), max_hp=hp)
                        def do_join():
                            self.party.add(new_join)
                            self.npcs.remove(npc)
                            msgs = self.quests.on_recruit(new_join.name)
                            if msgs:
                                self.dialogue.open(msgs)
                        self.dialogue.open([
                            f"{new_join.name}: The road is dangerous...",
                            f"I'll travel with you.",
                            f"(Joined: HP {new_join.max_hp}, Lv {new_join.level})"
                        ], on_close=do_join)

            if event.key in (pygame.K_UP, pygame.K_w):
                self._move_player(0, -1)
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self._move_player(0, 1)
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self._move_player(-1, 0)
            if event.key in (pygame.K_RIGHT, pygame.K_d):
                self._move_player(1, 0)

    def update(self, dt):
        # Dialogue typewriter update
        self.dialogue.update(dt)
        if self.message:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = None

        # Lose condition: if party wiped outside battle (shouldn't happen), reset
        if self.party.is_wiped():
            # Reset the whole game
            from main import boot_new_game
            boot_new_game(self.game)

    def _set_message(self, text, seconds=2.5):
        self.message = text
        self.message_timer = seconds

    def draw(self, screen):
        screen.fill((0,0,0))
        # camera
        cam_x = self.player_pos[0] - VIEW_W//2
        cam_y = self.player_pos[1] - VIEW_H//2
        for ty in range(VIEW_H):
            for tx in range(VIEW_W):
                wx = cam_x + tx
                wy = cam_y + ty
                biome = self._tile_at(wx, wy)
                color = (20,20,20) if biome is None else BIOME_COLORS.get(biome, (255,255,255))
                pygame.draw.rect(screen, color, (tx*TILE, ty*TILE, TILE-1, TILE-1))

        # draw NPCs in view
        for npc in self.npcs:
            tx = npc["x"] - cam_x
            ty = npc["y"] - cam_y
            if 0 <= tx < VIEW_W and 0 <= ty < VIEW_H:
                pygame.draw.circle(screen, (255, 200, 80), (tx*TILE + TILE//2, ty*TILE + TILE//2), TILE//3)

        # draw quest nodes
        for qn in self.quest_nodes:
            if qn.get('taken'):
                continue
            tx = qn['x'] - cam_x
            ty = qn['y'] - cam_y
            if 0 <= tx < VIEW_W and 0 <= ty < VIEW_H:
                pygame.draw.rect(screen, (200, 60, 200), (tx*TILE+6, ty*TILE+6, TILE-12, TILE-12))

        # draw active REACH targets as stars
        for q in self.quests.active:
            if q.type == 'reach' and q.pos:
                tx = q.pos[0] - cam_x
                ty = q.pos[1] - cam_y
                if 0 <= tx < VIEW_W and 0 <= ty < VIEW_H:
                    pygame.draw.polygon(screen, (255, 215, 0), [
                        (tx*TILE+TILE//2, ty*TILE+4),
                        (tx*TILE+TILE-4, ty*TILE+TILE//2),
                        (tx*TILE+TILE//2, ty*TILE+TILE-4),
                        (tx*TILE+4, ty*TILE+TILE//2)
                    ], 0)

        # draw player
        px = (self.player_pos[0] - cam_x) * TILE
        py = (self.player_pos[1] - cam_y) * TILE
        pygame.draw.rect(screen, (80, 200, 255), (px+4, py+4, TILE-8, TILE-8))

        # HUD
        y = 5
        for mem in self.party.members:
            txt = f"{mem.name} Lv{mem.level} HP {mem.hp}/{mem.max_hp} XP {mem.xp}/{mem.xp_to_next()}"
            img = self.font.render(txt, True, (255,255,255))
            screen.blit(img, (5, y))
            y += 20

        biome = self._tile_at(*self.player_pos)
        loc = self.font.render(f"Tile: {biome}", True, (240,240,240))
        screen.blit(loc, (5, y + 5))

        if self.help:
            lines = [
                "Arrows/WASD: Move  E: Interact  H: Help  ESC: Quit",
                "Recruit NPCs in towns/cities (adjacent). Random encounters elsewhere.",
            ]
            for i, line in enumerate(lines):
                img = self.bigfont.render(line, True, (255,255,255))
                screen.blit(img, (20, 460 + i*28))

        # Dialogue box on top of everything
        self.dialogue.draw(screen)

        if self.message:
            banner = self.bigfont.render(self.message, True, (255,255,255))
            rect = banner.get_rect(center=(screen.get_width()//2, 20))
            screen.blit(banner, rect)
