import random
from collections import defaultdict

class QuestStatus:
    ACTIVE = "active"
    COMPLETED = "completed"

class QuestType:
    HUNT = "hunt"       # defeat N of target in biome
    REACH = "reach"     # reach (x,y) tile
    RECRUIT = "recruit" # recruit any NPC (or specific name)

class Quest:
    def __init__(self, qid, title, description, qtype, reward_xp=50, target=None, biome=None, count=0, pos=None, is_main=False, main_step=None):
        self.id = qid
        self.title = title
        self.description = description
        self.type = qtype
        self.reward_xp = reward_xp
        self.target = target        # monster name (HUNT) or npc name (RECRUIT)
        self.biome = biome          # biome constraint (optional, mostly for HUNT)
        self.required = count       # count needed for HUNT
        self.progress = 0
        self.pos = pos              # (x,y) for REACH
        self.status = QuestStatus.ACTIVE
        self.is_main = is_main
        self.main_step = main_step  # 1..4

    def short_line(self):
        if self.type == QuestType.HUNT:
            s = f"{self.title} — {self.progress}/{self.required} {self.target}s in {self.biome or 'any'}"
        elif self.type == QuestType.REACH:
            s = f"{self.title} — Travel to {self.pos}"
        elif self.type == QuestType.RECRUIT:
            s = f"{self.title} — Recruit {'any ally' if not self.target else self.target}"
        else:
            s = self.title
        return s + (" [COMPLETED]" if self.status == QuestStatus.COMPLETED else "")

class QuestManager:
    def __init__(self, overworld):
        self.ow = overworld
        self.active = []
        self.completed = []
        self.side_nodes = []  # [{'x':, 'y':, 'taken':False}]
        self.main_started = False
        self.main_completed = False
        self.main_step = 0
        self.main_target = None  # step-specific coordinate

    def generate_world_nodes(self, grid, count=8):
        # Spawn quest nodes as '!' markers in safe and unsafe areas
        import random
        H, W = len(grid), len(grid[0])
        tries = 0
        nodes = []
        preferred = {"town", "city", "forest", "plains", "desert", "swamp", "mountain"}
        startx, starty = self.ow.player_pos
        while len(nodes) < count and tries < count * 200:
            tries += 1
            x = random.randrange(W)
            y = random.randrange(H)
            if grid[y][x] in preferred:
                if abs(x - startx) + abs(y - starty) > 6:
                    nodes.append({"x": x, "y": y, "taken": False})
        self.side_nodes = nodes
        return nodes

    # ----- Helpers -----
    def _nearest_tile_of_type(self, start, target_biome):
        grid = self.ow.map
        H, W = len(grid), len(grid[0])
        sx, sy = start
        best = None
        best_d = 10**9
        for y in range(H):
            for x in range(W):
                if grid[y][x] == target_biome:
                    d = abs(x - sx) + abs(y - sy)
                    if d < best_d:
                        best_d, best = d, (x, y)
        return best or (W//2, H//2)

    def _new_id(self):
        return f"Q{len(self.active) + len(self.completed) + 1:03d}"

    # ----- Main Quest Chain -----
    def trigger_main_on_city_enter(self, x, y):
        if self.main_started or self.main_completed:
            return []
        self.main_started = True
        self.main_step = 1
        # Step 1: Reach nearest dungeon (catacombs)
        dungeon_pos = self._nearest_tile_of_type((x, y), "dungeon")
        self.main_target = dungeon_pos
        title = "Main 1: Whispers of Regicide"
        desc_lines = [
            "City Rumor: The royal scribe fled with evidence the night the king died.",
            "A witness swears the scribe hid in the nearby catacombs.",
            f"Reach the catacombs at {dungeon_pos} and search for clues."
        ]
        q = Quest(self._new_id(), title, "Investigate the catacombs.", QuestType.REACH, reward_xp=120, pos=dungeon_pos, is_main=True, main_step=1)
        self.active.append(q)
        return desc_lines

    def _advance_main_after(self, step):
        # Returns dialogue lines for the next step (and adds new quest).
        lines = []
        if step == 1:
            # Step 2: Hunt dungeon foes to recover pages
            target = random.choice(["Ghoul", "Mimic", "Warg"])
            need = random.randint(3, 5)
            title = "Main 2: Shadows in the Catacombs"
            desc = f"Recover the torn journal pages. Defeat {need} {target}(s) in the dungeon."
            q = Quest(self._new_id(), title, desc, QuestType.HUNT, reward_xp=140, target=target, biome="dungeon", count=need, is_main=True, main_step=2)
            self.active.append(q)
            self.main_step = 2
            lines = [
                "You discover a sealed chamber and a trail of shredded parchment.",
                "Whatever took the scribe left pieces behind… guarded by something foul.",
                f"New Objective: {desc}"
            ]
        elif step == 2:
            # Step 3: Return to a city to decode the cipher
            city_pos = self._nearest_tile_of_type(self.ow.player_pos, "city")
            title = "Main 3: The Archivist's Cipher"
            desc = f"Bring the torn pages to the city archivist at {city_pos}."
            q = Quest(self._new_id(), title, desc, QuestType.REACH, reward_xp=160, pos=city_pos, is_main=True, main_step=3)
            self.active.append(q)
            self.main_step = 3
            lines = [
                "Among the pages is a ciphered note sealed with the royal crest.",
                "Only an archivist could decode this.",
                f"Return to the archivist at {city_pos}."
            ]
        elif step == 3:
            # Step 4: Final confrontation at a mountain lookout
            mount_pos = self._nearest_tile_of_type(self.ow.player_pos, "mountain")
            title = "Main 4: Confrontation at the Heights"
            desc = f"The cipher names the Captain of the Guard. Confront them at the mountain pass {mount_pos}."
            q = Quest(self._new_id(), title, desc, QuestType.REACH, reward_xp=220, pos=mount_pos, is_main=True, main_step=4)
            self.active.append(q)
            self.main_step = 4
            lines = [
                "Decoded: The scribe named the Captain of the Guard as the conspirator.",
                "A rendezvous is set at the mountain pass for the 'handoff'.",
                f"Final Objective: Confront the Captain at {mount_pos}."
            ]
        elif step == 4:
            # Epilogue
            self.main_completed = True
            lines = [
                "At the pass, the Captain arrives alone—blade drawn, confession whispered.",
                "Twist: The scribe forged the first letter; the Captain destroyed it to frame the court.",
                "With the true scheme exposed, the realm braces for the fallout.",
                "Main Quest Complete."
            ]
        return lines

    # ----- Side Quests -----
    def create_side_quest_at(self, node):
        biome = self.ow._tile_at(node['x'], node['y'])
        qtype = random.choices(
            [QuestType.HUNT, QuestType.REACH, QuestType.RECRUIT],
            weights=[5, 3, 2],
            k=1
        )[0]

        if qtype == QuestType.HUNT:
            from battle import Battle
            pool = Battle.ENEMY_TABLE.get(biome, Battle.ENEMY_TABLE["plains"])
            names, weights = zip(*pool)
            target = random.choices(names, weights=weights, k=1)[0]
            need = random.randint(3, 6)
            title = f"Hunt: {target} Trouble"
            desc = f"Defeat {need} {target}(s) in the {biome}."
            return Quest(self._new_id(), title, desc, QuestType.HUNT, reward_xp=80, target=target, biome=biome, count=need)

        if qtype == QuestType.REACH:
            goal_biome = random.choice(["mountain", "forest", "desert", "swamp", "plains", "city", "town", "dungeon"])
            goal_pos = self._nearest_tile_of_type((node['x'], node['y']), goal_biome)
            title = f"Scout: Reach the {goal_biome} marker"
            desc = f"Travel to {goal_pos} and report back (it'll auto-complete on arrival)."
            return Quest(self._new_id(), title, desc, QuestType.REACH, reward_xp=60, pos=goal_pos)

        # RECRUIT
        title = f"Safety in Numbers"
        desc = f"Recruit an ally in a nearby town or city."
        return Quest(self._new_id(), title, desc, QuestType.RECRUIT, reward_xp=50)

    # ----- Event Hooks -----
    def on_enemy_defeated_batch(self, enemies, biome):
        msgs = []
        name_counts = defaultdict(int)
        for e in enemies:
            if not e.alive:
                name_counts[e.name] += 1

        for q in list(self.active):
            if q.status != QuestStatus.ACTIVE:
                continue
            if q.type == QuestType.HUNT:
                if q.biome and (biome != q.biome):
                    continue
                if q.target in name_counts:
                    q.progress += name_counts[q.target]
                    if q.progress >= q.required:
                        msgs += self._complete(q)
                        # If this was a main step, advance chain
                        if q.is_main:
                            msgs += self._advance_main_after(q.main_step)
                    else:
                        msgs.append(f"Quest progress — {q.title}: {q.progress}/{q.required}")
        return msgs

    def on_enter_tile(self, x, y, biome):
        msgs = []
        # REACH quests
        for q in list(self.active):
            if q.status != QuestStatus.ACTIVE:
                continue
            if q.type == QuestType.REACH and q.pos and (x, y) == q.pos:
                msgs += self._complete(q)
                if q.is_main:
                    msgs += self._advance_main_after(q.main_step)
        return msgs

    def on_recruit(self, npc_name):
        msgs = []
        for q in list(self.active):
            if q.status != QuestStatus.ACTIVE:
                continue
            if q.type == QuestType.RECRUIT and (q.target is None or q.target == npc_name):
                msgs += self._complete(q)
                if q.is_main:
                    msgs += self._advance_main_after(q.main_step)
        return msgs

    # ----- API -----
    def accept_quest(self, quest):
        self.active.append(quest)

    def list_active_lines(self):
        if not self.active:
            return ["No active quests. Explore towns and '!' markers to find some."]
        lines = ["Active Quests:"]
        lines += [f" - {q.short_line()}" for q in self.active]
        return lines

    def list_completed_lines(self):
        if not self.completed:
            return ["No completed quests yet."]
        lines = ["Completed Quests:"]
        lines += [f" - {q.title}" for q in self.completed]
        return lines

    # ----- Internals -----
    def _complete(self, quest):
        quest.status = QuestStatus.COMPLETED
        if quest in self.active:
            self.active.remove(quest)
        self.completed.append(quest)
        # Reward party XP
        reward = quest.reward_xp
        leveled_any = False
        for m in self.ow.party.alive_members():
            if m.gain_xp(reward):
                leveled_any = True
        msg = [f"Quest Complete — {quest.title}! +{reward} XP to living members."]
        if leveled_any:
            msg.append("Level up!")
        return msg
