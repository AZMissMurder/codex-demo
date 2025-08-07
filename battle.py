import pygame, random
from utils.assets import load_sprite_for, scale_to_fit
from entities import Monster, Ability, BASIC_ABILITIES, hp_by_elapsed_minutes
from dialogue import DialogueBox

class Battle:
    ENEMY_TABLE = {
        "plains": [("Boar", 3), ("Slime", 4), ("Warg", 2)],
        "forest": [("Warg", 3), ("Kobold", 3), ("Wisp", 2)],
        "desert": [("Scarab", 3), ("Sand Wisp", 3), ("Jackal", 2)],
        "swamp": [("Ghoul", 3), ("Wisp", 3), ("Sludge", 2)],
        "water": [("Piranha", 3), ("Mud Crab", 3), ("Wisp", 1)],
        "mountain": [("Golem", 2), ("Kobold", 3), ("Griff", 1)],
        "town": [("Rowdy", 1)],
        "city": [("Mugger", 1)],
        "dungeon": [("Mimic", 2), ("Ghoul", 3), ("Warg", 2)],
    }

    def __init__(self, game, overworld, party, biome=None):
        self.game = game
        self.overworld = overworld
        self.party = party
        self.font = pygame.font.SysFont(None, 22)
        self.bigfont = pygame.font.SysFont(None, 28)

        # Turn system: one actor acts at a time; a round is everyone acting once
        self.phase = "turn"  # "turn" or "message"
        self.turn_queue = []
        self.turn_index = 0
        self.action_index = 0   # kept for backward-compat with some UI logic (unused in new flow)
        self.ability_choice = None
        self.target_index = 0
        self.message = None

        self.biome = biome
        self.enemies = self._spawn_enemies()
        # Preload sprites
        for e in self.enemies:
            e.sprite = load_sprite_for("enemies", e.name)
        for m in self.party.members:
            if not hasattr(m, 'sprite') or m.sprite is None:
                m.sprite = load_sprite_for("characters", m.name)
        self.victory = None  # True/False when over
        self.dialogue = DialogueBox((self.game.screen.get_width(), self.game.screen.get_height()))
        # Build initial round order
        self._build_turn_queue()

    def enter(self, **kwargs):
        pass

    def exit(self):
        pass

    def _spawn_enemies(self):
        minutes = self.game.elapsed_minutes()
        biome = (self.biome or "plains")
        pool = self.ENEMY_TABLE.get(biome, self.ENEMY_TABLE["plains"])
        size = random.randint(1, 2 if biome in ("plains", "forest") else 3)
        enemies = []
        names, weights = zip(*pool)
        for i in range(size):
            name = random.choices(names, weights=weights, k=1)[0]
            base_hp = random.randint(38, 72)
            hp = hp_by_elapsed_minutes(base_hp, minutes)
            level = max(1, int(minutes//5) + 1)
            abilities = [Ability("Claw", power=8), Ability("Bite", power=12)]
            enemies.append(Monster(name, level, hp, abilities=abilities, is_player=False))
        return enemies

    def _build_turn_queue(self):
        # Interleave party and enemies so actions alternate when possible
        party_alive = [m for m in self.party.members if m.alive]
        enemies_alive = [e for e in self.enemies if e.alive]
        self.turn_queue = []
        for i in range(max(len(party_alive), len(enemies_alive))):
            if i < len(party_alive):
                self.turn_queue.append(party_alive[i])
            if i < len(enemies_alive):
                self.turn_queue.append(enemies_alive[i])
        self.turn_index = 0

    def _current_actor(self):
        # Skip dead actors and advance as needed
        while self.turn_index < len(self.turn_queue) and not self.turn_queue[self.turn_index].alive:
            self.turn_index += 1
        if self.turn_index >= len(self.turn_queue):
            return None
        return self.turn_queue[self.turn_index]

    def _advance_turn(self):
        self.turn_index += 1
        # End of round → rebuild queue for next round
        if self.turn_index >= len(self.turn_queue):
            self._build_turn_queue()
        # Reset per-turn selection
        self.ability_choice = None
        self.target_index = 0

    def _advance_or_enemy_phase(self):
        # Legacy helper kept for compatibility; forward to new turn system
        self._advance_turn()

    def _give_xp_reward(self):
        minutes = self.game.elapsed_minutes()
        base = sum(max(5, e.level*6 + random.randint(-2, 6)) for e in self.enemies)
        reward = int(base * (1.0 + min(1.5, minutes*0.05)))
        leveled_any = False
        for m in self.party.alive_members():
            if m.gain_xp(reward):
                leveled_any = True
        return reward, leveled_any

    def _check_over(self):
        if all(not e.alive for e in self.enemies):
            self.victory = True
            self.phase = "message"
            reward, leveled = self._give_xp_reward()
            msg = f"Victory! +{reward} XP to living members."
            if leveled:
                msg += " Level up!"
            # Quest progress based on defeated enemies
            qmsgs = self.overworld.quests.on_enemy_defeated_batch(self.enemies, self.biome)
            self.message = msg
            self.dialogue.open([self.message] + qmsgs if qmsgs else [self.message])
        elif self.party.is_wiped():
            self.victory = False
            self.phase = "message"
            self.message = "Your party has fallen... Restarting."
            self.dialogue.open([self.message])

    def _do_enemy_turn(self, enemy_actor):
        targets = [m for m in self.party.alive_members()]
        if not targets:
            self._check_over()
            return
        t = random.choice(targets)
        ability = random.choice(enemy_actor.abilities)
        dmg = max(1, ability.power + enemy_actor.level * 2 + random.randint(-3, 3))
        t.take_damage(dmg)
        # Show a quick dialogue message
        self.phase = "message"
        self.message = f"{enemy_actor.name} used {ability.name} on {t.name} (-{dmg})."
        self.dialogue.open([self.message])
        self._check_over()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            # Allow immediate quit in battle too
            pass

        # Dialogue consumes input during message phase
        if self.phase == "message" and self.dialogue.active:
            self.dialogue.handle_event(event)
            # if dialogue just closed, continue flow
            if not self.dialogue.active:
                if self.victory is not None:
                    if self.victory:
                        from main import switch_to_overworld
                        switch_to_overworld(self.game, self.overworld)
                    else:
                        from main import boot_new_game
                        boot_new_game(self.game)
                else:
                    # continue battle flow to next actor
                    if any(e.alive for e in self.enemies) and any(m.alive for m in self.party.members):
                        self.phase = "turn"
                        self._advance_turn()
            return

        if event.type == pygame.KEYDOWN:
            if self.phase == "turn":
                actor = self._current_actor()
                if not actor:
                    # End of round; queue rebuilt automatically
                    return

                if not getattr(actor, 'is_player', False):
                    return  # player input only applies to player-controlled turns

                if self.ability_choice is None:
                    # Choose ability via number keys
                    if pygame.K_1 <= event.key <= pygame.K_9:
                        idx = event.key - pygame.K_1
                        if idx < len(actor.abilities):
                            self.ability_choice = actor.abilities[idx]
                            # Default target index resets
                            self.target_index = 0
                    return

                # Choose target with arrows, ENTER to confirm
                if self.ability_choice.target == "enemy":
                    targets = [x for x in self.enemies if x.alive]
                else:
                    targets = [x for x in self.party.alive_members()]

                if event.key in (pygame.K_UP, pygame.K_w):
                    self.target_index = (self.target_index - 1) % len(targets)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.target_index = (self.target_index + 1) % len(targets)
                elif event.key in (pygame.K_RETURN,):
                    target = targets[self.target_index]
                    if self.ability_choice.heal:
                        amount = max(1, self.ability_choice.power + actor.level*2)
                        target.heal(amount)
                        self.phase = "message"
                        self.message = f"{actor.name} cast {self.ability_choice.name} on {target.name} (+{amount})."
                        self.dialogue.open([self.message])
                    else:
                        dmg = max(1, self.ability_choice.power + actor.level*3 + random.randint(-4, 4))
                        target.take_damage(dmg)
                        self.phase = "message"
                        self.message = f"{actor.name} used {self.ability_choice.name} on {target.name} (-{dmg})."
                        self.dialogue.open([self.message])

                    # Clear choice and advance
                    self.ability_choice = None
                    self._check_over()

    def update(self, dt):
        self.dialogue.update(dt)
        if self.phase != "message":
            actor = self._current_actor()
            if actor and not getattr(actor, 'is_player', False):
                # Auto-execute AI turn
                self._do_enemy_turn(actor)

    def draw(self, screen):
        screen.fill((10, 10, 20))

        # Draw enemies (right side)
        ex = screen.get_width() - 260
        ey = 40
        for i, e in enumerate(self.enemies):
            color = (200, 120, 120) if e.alive else (90, 50, 50)
            rect = pygame.Rect(ex, ey + i*80, 220, 60)
            pygame.draw.rect(screen, color, rect)
            if getattr(e, 'sprite', None):
                sprite = scale_to_fit(e.sprite, rect.width-20, rect.height-20)
                screen.blit(sprite, (rect.x + (rect.width - sprite.get_width())//2, rect.y + (rect.height - sprite.get_height())//2))
            self._draw_bar(screen, ex+10, ey + i*80 + 35, 200, 12, e.hp, e.max_hp)
            label = f"{e.name} Lv{e.level} HP {e.hp}/{e.max_hp}"
            img = self.font.render(label, True, (255,255,255))
            screen.blit(img, (ex+10, ey + i*80 + 8))

        # Draw party (left side)
        px = 40
        py = 40
        alive_party = [m for m in self.party.members]
        for i, m in enumerate(alive_party):
            color = (120, 160, 220) if m.alive else (50, 60, 90)
            rect = pygame.Rect(px, py + i*80, 220, 60)
            pygame.draw.rect(screen, color, rect)
            if getattr(m, 'sprite', None):
                sprite = scale_to_fit(m.sprite, rect.width-20, rect.height-20)
                screen.blit(sprite, (rect.x + (rect.width - sprite.get_width())//2, rect.y + (rect.height - sprite.get_height())//2))
            self._draw_bar(screen, px+10, py + i*80 + 35, 200, 12, m.hp, m.max_hp)
            label = f"{m.name} Lv{m.level} HP {m.hp}/{m.max_hp}"
            img = self.font.render(label, True, (255,255,255))
            screen.blit(img, (px+10, py + i*80 + 8))

        # Ability panel for current player-controlled actor
        actor = self._current_actor()
        if self.phase != "message" and actor and getattr(actor, 'is_player', False):
                panel_y = screen.get_height() - 180
                pygame.draw.rect(screen, (30, 30, 45), (0, panel_y, screen.get_width(), 180))
                title = self.bigfont.render(f"{actor.name}'s turn — choose ability (1-9)", True, (255,255,255))
                screen.blit(title, (20, panel_y + 10))

                for i, ab in enumerate(actor.abilities):
                    line = f"{i+1}. {ab.name} ({'heal' if ab.heal else 'dmg'} {ab.power})"
                    img = self.font.render(line, True, (220,220,220))
                    screen.blit(img, (40, panel_y + 50 + i*22))

                if self.ability_choice is not None:
                    targets = [x for x in (self.enemies if self.ability_choice.target=='enemy' else self.party.members) if x.alive]
                    info = self.font.render("Use Up/Down to select target, Enter to confirm.", True, (255,255,255))
                    screen.blit(info, (20, panel_y + 130))

                    # highlight target block
                    if targets:
                        target = targets[self.target_index % len(targets)]
                        # find rect to highlight
                        if target in self.enemies:
                            idx = self.enemies.index(target)
                            rect = (screen.get_width() - 260, 40 + idx*80, 220, 60)
                        else:
                            idx = self.party.members.index(target)
                            rect = (40, 40 + idx*80, 220, 60)
                        pygame.draw.rect(screen, (255,255,0), rect, 3)

        # Dialogue/message overlay
        self.dialogue.draw(screen)

    def _draw_bar(self, screen, x, y, w, h, value, max_value):
        ratio = 0 if max_value <= 0 else value / max_value
        pygame.draw.rect(screen, (80,80,80), (x, y, w, h))
        pygame.draw.rect(screen, (100, 220, 120), (x, y, int(w*ratio), h))
