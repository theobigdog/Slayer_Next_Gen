"""Slayer_Window: the Pygame backend for Slayer_UI.

The game logic never imports this file. main.py picks it with ui.use(WindowUI()),
and from then on every ui.say / ui.choose / ui.show_battle ... lands here.

How the two halves share time: the game logic runs as one asyncio task, and the
frame loop in run() runs alongside it. When the game awaits something that needs
the player (pause, choose, ask_text...), it waits on a Future that the frame loop
completes when the player clicks or presses a key. The frame loop hands control
back every frame (await asyncio.sleep(0)), which is what pygbag needs in a browser.

Art: drop PNGs into assets/sprites/ (see assets/README.md) and they replace the
placeholder boxes automatically.
"""
import asyncio
import random
import re
import sys
import traceback
from pathlib import Path

import pygame

import Slayer_Accessory as acc

SCREEN_W, SCREEN_H = 1280, 720
ASSETS = Path(__file__).parent / 'assets'
IN_BROWSER = sys.platform == 'emscripten'

# Placeholder colors until there's art and a real palette.
BG = (16, 14, 13)
PANEL = (30, 26, 23)
PANEL_EDGE = (82, 70, 58)
TEXT = (232, 224, 208)
DIM = (140, 130, 118)
GOLD = (212, 166, 64)
HERO_BOX = (38, 84, 76)
MOB_BOX = (106, 46, 36)
ENRAGED_BOX = (160, 24, 24)
HP_GOOD = (80, 176, 80)
HP_LOW = (192, 96, 192)    # the terminal's magenta, at 50% and below
HP_CRIT = (224, 64, 64)    # the terminal's red, at 10% and below
TAG_COLORS = {'red': (240, 70, 70), 'magenta': (200, 110, 200), 'green': (90, 200, 90), 'white': (255, 255, 255)}
TAG = re.compile(r'\[(red|magenta|green|white|/)\]')


def font(size: int, kind: str = 'regular') -> pygame.font.Font:
    files = {'regular': 'DejaVuSans.ttf', 'bold': 'DejaVuSans-Bold.ttf', 'mono': 'DejaVuSansMono-Bold.ttf'}
    return pygame.font.Font(ASSETS / 'fonts' / files[kind], size)


def rich_runs(text: str) -> list:
    """'You\'re on [red]The List[/].' -> [("You're on ", TEXT), ('The List', red), ('.', TEXT)]"""
    runs, color, pos = [], TEXT, 0
    for match in TAG.finditer(text):
        if match.start() > pos:
            runs.append((text[pos:match.start()], color))
        color = TEXT if match.group(1) == '/' else TAG_COLORS[match.group(1)]
        pos = match.end()
    if pos < len(text):
        runs.append((text[pos:], color))
    return runs


def wrap_rich(text: str, fnt: pygame.font.Font, width: int) -> list:
    """Word-wrap one line of tagged text to a pixel width. Returns visual lines, each a list of (text, color)."""
    words = []  # (word_with_trailing_space, color)
    for chunk, color in rich_runs(text):
        for word in re.findall(r'\S+\s*|\s+', chunk):
            words.append((word, color))
    lines, line, line_w = [], [], 0
    for word, color in words:
        w = fnt.size(word.rstrip())[0]
        if line and line_w + w > width:
            lines.append(line)
            line, line_w = [], 0
            word = word.lstrip()
        line.append((word, color))
        line_w += fnt.size(word)[0]
    lines.append(line)
    return lines


class Button:
    def __init__(self, rect, label, value, key=None):
        self.rect, self.label, self.value, self.key = pygame.Rect(rect), label, value, key


class WindowUI:
    """Plays Slayer in a 1280x720 Pygame window (scaled to fit whatever window it's in)."""

    chars_per_second = 90  # typewriter speed for the narration

    def __init__(self, headless_fps: int = 60):
        pygame.init()
        flags = 0 if IN_BROWSER else pygame.SCALED | pygame.RESIZABLE
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)
        pygame.display.set_caption('SLAYER')
        self.clock = pygame.time.Clock()
        self.fps = headless_fps
        self.fonts = {
            'text': font(21), 'menu': font(19), 'name': font(17, 'bold'), 'name_small': font(14, 'bold'), 'small': font(14),
            'round': font(26, 'bold'), 'title': font(13, 'mono'), 'big': font(30, 'bold'),
        }
        self.mode = 'text'          # 'title', 'text', 'party', 'battle', 'loser', 'end'
        self.party, self.mobs, self.round_num = [], [], 0
        self.lines = []             # narration lines since the last clear (tagged text)
        self.revealed = 0.0         # how many characters of self.lines the typewriter has shown
        self.page_start = 0         # first visual line of the current page in the narration box
        self.scroll_back = 0        # lines the player has scrolled up with the mouse wheel
        self.waiting = None         # (kind, future, extra) while the game waits on the player
        self.buttons = []
        self.typed = ''             # ask_text's input so far
        self.targets = []           # (rect, entity) for clickable sprites during choose_target
        self.sprite_cache = {}
        self.overlay = None         # title / loser animation frame (a function that draws it)
        self.title_draw = None      # the finished title screen, shown until the next clear
        self.sprite_rects = []      # (rect, entity) for every sprite drawn this frame
        self.menu_labels = []
        self.error = None

    # ---------- the frame loop -------------------------------------------------

    async def run(self, game):
        """Run the game coroutine alongside the frame loop until the window closes."""
        task = asyncio.ensure_future(self.guarded(game))
        while True:
            dt = self.clock.tick(self.fps) / 1000 if (self.fps and not IN_BROWSER) else 1 / 60
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    task.cancel()
                    pygame.quit()
                    return
                self.handle(event)
            self.advance_typewriter(dt)
            if task.done() and self.mode != 'end':
                self.finish(task)
            self.draw()
            pygame.display.flip()
            await asyncio.sleep(0)

    async def guarded(self, game):
        """acc.end() calls sys.exit(). Inside asyncio that would kill the window before
        "The End." is ever drawn, so it's caught here and the frame loop ends things instead."""
        try:
            await game
        except SystemExit:
            pass

    def finish(self, task):
        """The game function returned (or called sys.exit in acc.end): show the last text, then 'click to close'."""
        error = None if task.cancelled() else task.exception()
        if error is not None and not isinstance(error, SystemExit):
            self.error = ''.join(traceback.format_exception(error))
            print(self.error, file=sys.stderr)
            self.lines = ['[red]The game crashed:[/]'] + self.error.strip().splitlines()[-6:]
            self.revealed = self.total_chars()
        self.mode = 'end'
        self.waiting = ('close', None, None)

    # ---------- input ----------------------------------------------------------

    def handle(self, event):
        if event.type == pygame.MOUSEWHEEL and self.typed_out():
            self.scroll(event.y * -3)
            return
        if not self.waiting:
            return
        kind, future, extra = self.waiting
        clicked = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
        enter = event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)

        if kind in ('pause', 'more', 'close'):
            if clicked or enter:
                if not self.typed_out():
                    self.revealed = self.page_end_chars()  # first click finishes the typing
                elif kind == 'more':
                    vis = self.visual_lines()
                    self.page_start = max(self.page_start + 1, min(self.page_turn_line, len(vis) - self.page_capacity()))
                    self.waiting = extra
                elif kind == 'close':
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                else:
                    self.resolve(None)
            return

        if not self.typed_out():  # menus wait until the prompt has been typed out
            if clicked or enter:
                self.revealed = self.page_end_chars()
            return

        if kind == 'text':
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.resolve(self.typed)
                elif event.key == pygame.K_BACKSPACE:
                    self.typed = self.typed[:-1]
            elif event.type == pygame.TEXTINPUT and len(self.typed) < 40:
                self.typed += event.text
            return

        # menus: choose, choose_target, yes_no
        if clicked:
            for button in self.buttons:
                if button.rect.collidepoint(event.pos):
                    return self.pick(button.value)
            for rect, entity in self.targets:
                if rect.collidepoint(event.pos):
                    return self.pick(entity)
        if event.type == pygame.KEYDOWN:
            if kind == 'yes_no':
                if event.key in (pygame.K_y, pygame.K_n):
                    self.pick(event.key == pygame.K_y)
                return
            number = self.number_key(event)
            if number is not None:
                options = extra['options']
                if 1 <= number <= len(options):
                    self.pick(options[number - 1])
                else:
                    self.oops(extra)

    def scroll(self, lines):
        """Mouse wheel: look back at earlier lines (since the last clear). New text snaps back down."""
        self.scroll_back = max(0, min(self.page_start, self.scroll_back - lines))

    def number_key(self, event):
        if pygame.K_1 <= event.key <= pygame.K_9:
            return event.key - pygame.K_0
        if pygame.K_KP1 <= event.key <= pygame.K_KP9:
            return event.key - pygame.K_KP1 + 1
        if event.key in (pygame.K_0, pygame.K_KP0):
            return 0
        return None

    def oops(self, extra):
        """A number that isn't on the menu: show the oops line and ask again, like the terminal does."""
        self.add_text(pick_line(extra['oops']))
        self.add_text(pick_line(extra['prompt']))

    def pick(self, value):
        self.buttons, self.targets = [], []
        self.resolve(value)

    def resolve(self, value):
        kind, future, extra = self.waiting
        self.waiting = None
        self.buttons, self.targets = [], []
        if future and not future.done():
            future.set_result(value)

    async def wait_for(self, kind, extra=None):
        future = asyncio.get_running_loop().create_future()
        self.waiting = (kind, future, extra)
        return await future

    # ---------- narration text -------------------------------------------------

    def add_text(self, text):
        self.scroll_back = 0
        for line in str(text).split('\n'):
            if line.strip() == '' and (not self.lines or self.lines[-1].strip() == ''):
                continue  # no blank line at the top of the box, and never two in a row
            self.lines.append(line)

    def total_chars(self):
        return sum(len(TAG.sub('', line)) for line in self.lines)

    def typed_out(self):
        return self.revealed >= self.page_end_chars()

    def visual_lines(self):
        """Every narration line wrapped to the box: [(runs, chars_in_line)]."""
        width = self.text_box().width - 40
        out = []
        for line in self.lines:
            for runs in wrap_rich(line, self.fonts['text'], width):
                out.append((runs, sum(len(t) for t, _ in runs)))
        return out

    def page_capacity(self):
        room = self.text_box().height - 30
        if self.waiting and self.waiting[0] == 'text':
            room -= 56  # leave space for the typing field at the bottom of the box
        return max(1, room // self.line_h)

    def page_end_chars(self):
        """Characters up to the end of what fits on the current page."""
        vis = self.visual_lines()
        end = min(len(vis), self.page_start + self.page_capacity())
        return sum(n for _, n in vis[:end])

    def advance_typewriter(self, dt):
        if self.waiting and self.waiting[0] == 'more':
            return
        self.revealed = min(self.revealed + self.chars_per_second * dt, self.page_end_chars())
        vis = self.visual_lines()
        page_end = self.page_start + self.page_capacity()
        if self.revealed >= self.page_end_chars() and page_end < len(vis):
            # the box is full and there's more to say: stop and wait for a click
            self.page_turn_line = page_end
            self.waiting = ('more', None, self.waiting)

    async def until_typed(self):
        while not self.typed_out() or (self.waiting and self.waiting[0] == 'more'):
            await asyncio.sleep(0)

    # ---------- the Slayer_UI calls --------------------------------------------

    async def say(self, text=''):
        self.add_text(text)

    async def wait(self, seconds):
        await self.until_typed()
        await asyncio.sleep(seconds)

    async def pause(self):
        await self.until_typed()
        await self.wait_for('pause')

    async def clear(self):
        await self.until_typed()
        self.lines, self.revealed, self.page_start, self.scroll_back = [], 0.0, 0, 0
        if self.mode == 'title':
            self.mode = 'text'

    async def choose(self, prompt, labels, oops):
        self.add_text(pick_line(prompt))
        return await self.menu('choose', list(range(len(labels))), labels, prompt, oops)

    async def choose_target(self, prompt, party, mobs, oops):
        self.add_text(pick_line(prompt))
        labels = [f'{t.name}' for t in party + mobs]
        return await self.menu('choose_target', party + mobs, labels, prompt, oops)

    async def menu(self, kind, options, labels, prompt, oops):
        self.menu_labels = labels
        return await self.wait_for(kind, {'options': options, 'prompt': prompt, 'oops': oops})

    async def yes_no(self, prompt):
        self.add_text(prompt)
        self.menu_labels = ['Yes', 'No']
        return await self.wait_for('yes_no', {'options': [True, False]})

    async def ask_text(self, prompt):
        self.add_text(prompt)
        self.typed = ''
        pygame.key.start_text_input()
        try:
            return await self.wait_for('text')
        finally:
            pygame.key.stop_text_input()

    async def show_battle(self, party, mobs, round_num):
        await self.clear()
        self.mode, self.party, self.mobs, self.round_num = 'battle', party, mobs, round_num

    async def show_party(self, party):
        await self.until_typed()
        self.mode, self.party = 'party', party

    async def title_screen(self):
        await TitleAnimation(self).play()

    async def loser_banner(self):
        await LoserAnimation(self).play()
        self.mode = 'text'

    # ---------- drawing --------------------------------------------------------

    line_h = 26  # pixels per narration line

    def text_box(self):
        if self.mode in ('battle', 'party'):
            return pygame.Rect(16, 444, 780 if self.menu_open() else 1248, 264)
        return pygame.Rect(60, 60, 1160 if not self.menu_open() else 740, 600)

    def menu_area(self):
        if self.mode in ('battle', 'party'):
            return pygame.Rect(808, 444, 456, 264)
        return pygame.Rect(812, 60, 408, 600)

    def menu_open(self):
        return bool(self.waiting) and self.waiting[0] in ('choose', 'choose_target', 'yes_no')

    def draw(self):
        self.screen.fill(BG)
        if self.overlay:
            self.overlay()
            return
        self.targets, self.sprite_rects = [], []
        if self.mode == 'title':
            self.title_draw()
            if self.waiting and self.waiting[0] == 'pause':
                self.blit_text('click or Enter  \u25bc', (SCREEN_W // 2, SCREEN_H - 60), 'menu', GOLD, center=True)
            return
        if self.mode == 'battle':
            self.draw_battle()
        elif self.mode == 'party':
            self.draw_party_lineup()
        self.draw_text_box()
        if self.menu_open() and self.typed_out():
            self.draw_menu()

    def panel(self, rect, edge=PANEL_EDGE):
        pygame.draw.rect(self.screen, PANEL, rect, border_radius=10)
        pygame.draw.rect(self.screen, edge, rect, 2, border_radius=10)

    def blit_text(self, text, pos, fnt='text', color=TEXT, center=False):
        surf = self.fonts[fnt].render(text, True, color)
        rect = surf.get_rect(center=pos) if center else surf.get_rect(topleft=pos)
        self.screen.blit(surf, rect)
        return rect

    def draw_text_box(self):
        box = self.text_box()
        self.panel(box)
        vis = self.visual_lines()
        top = self.page_start - self.scroll_back
        budget = self.revealed - sum(n for _, n in vis[:top])
        y = box.y + 16
        for runs, n in vis[top:top + self.page_capacity()]:
            if budget <= 0:
                break
            x = box.x + 20
            for chunk, color in runs:
                shown = chunk[:max(0, int(budget))]
                budget -= len(chunk)
                if shown:
                    surf = self.fonts['text'].render(shown, True, color)
                    self.screen.blit(surf, (x, y))
                    x += surf.get_width()
            y += self.line_h
        kind = self.waiting[0] if self.waiting else None
        if kind == 'text' and self.typed_out():
            field = pygame.Rect(box.x + 20, box.bottom - 52, box.width - 40, 38)
            pygame.draw.rect(self.screen, BG, field, border_radius=6)
            pygame.draw.rect(self.screen, GOLD, field, 2, border_radius=6)
            caret = '|' if (pygame.time.get_ticks() // 500) % 2 == 0 else ' '
            self.blit_text(self.typed + caret, (field.x + 10, field.y + 6))
        elif kind in ('pause', 'more', 'close') and self.typed_out():
            hint = {'pause': 'click or Enter', 'more': 'more', 'close': 'click to close'}[kind]
            self.blit_text(f'{hint}  ▼', (box.right - 20 - self.fonts['small'].size(f'{hint}  ▼')[0], box.bottom - 26), 'small', GOLD)

    def draw_menu(self):
        kind, _, extra = self.waiting
        labels = self.menu_labels
        area = self.menu_area()
        self.panel(area, GOLD)
        title = {'choose': 'Choose', 'choose_target': 'Target', 'yes_no': 'Yes or no?'}[kind]
        self.blit_text(title, (area.x + 16, area.y + 12), 'name', GOLD)
        row_h = min(34, (area.height - 50) // max(1, len(labels)))
        self.buttons = []
        mouse = pygame.mouse.get_pos()
        for i, label in enumerate(labels):
            rect = pygame.Rect(area.x + 10, area.y + 44 + i * row_h, area.width - 20, row_h - 4)
            hover = rect.collidepoint(mouse)
            pygame.draw.rect(self.screen, (58, 50, 42) if hover else (40, 35, 30), rect, border_radius=6)
            key = ('Y' if label == 'Yes' else 'N') if kind == 'yes_no' else str(i + 1)
            text = f'{key}   {label}'
            fnt = self.fonts['menu']
            while fnt.size(text)[0] > rect.width - 16 and len(text) > 4:
                text = text[:-2]
            self.blit_text(text, (rect.x + 8, rect.centery - fnt.get_height() // 2), 'menu')
            self.buttons.append(Button(rect, label, extra['options'][i]))
        if kind == 'choose_target':
            self.targets = [(rect, ent) for rect, ent in self.sprite_rects if ent in extra['options']]
            for rect, _ in self.targets:
                pygame.draw.rect(self.screen, GOLD, rect.inflate(10, 10), 3, border_radius=8)

    # battle scene

    def draw_battle(self):
        self.blit_text(f'Round {self.round_num}', (24, 16), 'round', GOLD)
        self.sprite_rects = []
        self.draw_party_row(self.party, top=64)
        self.draw_mobs()

    def draw_party_row(self, party, top):
        slot_w, sprite = 150, 104
        for i, heroine in enumerate(party):
            col, row = i % 4, i // 4
            x = 24 + col * slot_w
            y = top + row * 190
            rect = pygame.Rect(x + (slot_w - sprite) // 2 - 6, y, sprite, sprite)
            self.draw_sprite(heroine, rect, heroine.hero_class, HERO_BOX)
            self.draw_nameplate(heroine, rect, slot_w - 12)
            self.sprite_rects.append((rect, heroine))

    def draw_mobs(self):
        bosses = [m for m in self.mobs if getattr(m, 'is_boss', False)]
        others = [m for m in self.mobs if m not in bosses]
        order = others[:len(others) // 2] + bosses + others[len(others) // 2:]
        sizes = []
        for mob in order:
            if getattr(mob, 'is_boss', False):
                sizes.append((250, 300) if mob.enraged else (200, 240))
            else:
                sizes.append((120, 150))
        gap = 36
        total = sum(w for w, _ in sizes) + gap * (len(sizes) - 1)
        x = 660 + (600 - total) // 2
        floor = 360
        for mob, (w, h) in zip(order, sizes):
            rect = pygame.Rect(x, floor - h, w, h)
            label = mob.mob_class + (' (enraged)' if mob.enraged else '')
            self.draw_sprite(mob, rect, label, ENRAGED_BOX if mob.enraged else MOB_BOX)
            self.draw_nameplate(mob, rect, max(w, 130))
            self.sprite_rects.append((rect, mob))
            x += w + gap

    def draw_sprite(self, entity, rect, label, box_color):
        image = self.sprite_for(entity, rect.size)
        dead = entity.is_dead
        if image:
            if dead:
                image = image.copy()
                image.fill((90, 90, 90, 255), special_flags=pygame.BLEND_RGBA_MULT)
            self.screen.blit(image, image.get_rect(midbottom=rect.midbottom))
        else:
            color = tuple(c // 3 for c in box_color) if dead else box_color
            pygame.draw.rect(self.screen, color, rect, border_radius=8)
            for i, part in enumerate(label.replace('_', ' ').split(' (')):
                part = part if i == 0 else '(' + part
                self.blit_text(part, (rect.centerx, rect.centery - 8 + i * 18), 'small', DIM if dead else TEXT, center=True)
        if dead:
            self.blit_text('dead', (rect.centerx, rect.y + 14), 'name', HP_CRIT, center=True)

    def sprite_for(self, entity, size):
        """assets/sprites/<class>_<pose>.png, e.g. warrior_idle.png, disgruntled_dwarf_enraged.png."""
        kind = getattr(entity, 'hero_class', None) or entity.mob_class
        slug = kind.lower().replace(' ', '_')
        pose = 'enraged' if getattr(entity, 'enraged', False) else 'idle'
        key = (slug, pose, size)
        if key not in self.sprite_cache:
            image = None
            for name in (f'{slug}_{pose}.png', f'{slug}_idle.png'):
                path = ASSETS / 'sprites' / name
                if path.exists():
                    image = pygame.image.load(str(path)).convert_alpha()
                    scale = min(size[0] / image.get_width(), size[1] / image.get_height())
                    image = pygame.transform.smoothscale(image, (int(image.get_width() * scale), int(image.get_height() * scale)))
                    break
            self.sprite_cache[key] = image
        return self.sprite_cache[key]

    def name_lines(self, name, width):
        """A name that fits its slot: one line if it can, else two smaller lines, trimmed with ... if needed."""
        if self.fonts['name'].size(name)[0] <= width:
            return [name], 'name'
        fnt, lines, line = self.fonts['name_small'], [], ''
        for word in name.split():
            trial = (line + ' ' + word).strip()
            if fnt.size(trial)[0] <= width or not line:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)
        if len(lines) > 2:
            lines = [lines[0], ' '.join(lines[1:])]
        while fnt.size(lines[-1])[0] > width and len(lines[-1]) > 3:
            lines[-1] = lines[-1][:-4].rstrip() + '...'
        return lines, 'name_small'

    def draw_nameplate(self, entity, rect, width):
        lines, fnt = self.name_lines(entity.name, width)
        y = rect.bottom + 14
        for line in lines:
            self.blit_text(line, (rect.centerx, y), fnt, TEXT, center=True)
            y += self.fonts[fnt].get_linesize()
        bar = pygame.Rect(0, 0, width - 20, 9)
        bar.midtop = (rect.centerx, y - 4)
        pygame.draw.rect(self.screen, (55, 50, 45), bar, border_radius=4)
        share = max(0.0, entity.health / entity.starting_health)
        color = HP_CRIT if share <= 0.1 else HP_LOW if share <= 0.5 else HP_GOOD
        if share > 0:
            pygame.draw.rect(self.screen, color, (bar.x, bar.y, max(4, int(bar.width * share)), bar.height), border_radius=4)
        self.blit_text(f'{int(round(entity.health))}/{entity.starting_health}', (rect.centerx, bar.bottom + 11), 'small', DIM, center=True)

    def draw_party_lineup(self):
        self.sprite_rects = []
        self.blit_text('Your party', (24, 16), 'round', GOLD)
        self.draw_party_row(self.party, top=64)


def pick_line(lines):
    return lines if isinstance(lines, str) else random.choice(lines)


# ---------- the chunky ASCII openings, drawn in the window ----------------------

class AsciiArt:
    """Draws Slayer_Graphics' letter art with a monospace font, one color per letter."""

    def __init__(self, window):
        import Slayer_Graphics as gr  # the letter art and color sequences
        self.gr, self.window = gr, window
        self.font = window.fonts['title']
        self.cell_w, self.cell_h = self.font.size('M')[0], self.font.get_linesize()
        self.palette = {gr.r: (230, 30, 30), gr.g: (60, 220, 60), gr.b: (22, 20, 20)}

    def draw_word(self, word, letters, colors, x, y):
        for letter in word:
            rows = letters[letter]
            color = self.palette.get(colors[letter], TEXT)
            for i, row in enumerate(rows):
                self.window.screen.blit(self.font.render(row, True, color), (x, y + i * self.cell_h))
            x += len(rows[0]) * self.cell_w

    def word_width(self, word, letters):
        return sum(len(letters[ch][0]) for ch in word) * self.cell_w


class TitleAnimation(AsciiArt):
    """Slayer_Graphics.slayer_opening, frame for frame: letters flicker red at random, faster and faster."""

    async def play(self):
        gr, window = self.gr, self.window
        dev = acc.dev_mode()
        gap, divisor = (0.05, 2) if dev else (0.15, 1.01)
        word, letters = gr.slayer, gr.slayer_letters
        x = (SCREEN_W - self.word_width(word, letters)) // 2
        y = 150
        state = {'colors': gr.letter_colors_sl['a'], 'version': False, 'dare': False}

        def draw():
            self.draw_word(word, letters, state['colors'], x, y)
            if state['version']:
                window.blit_text('v 2.0', (x + self.word_width(word, letters) - 40, y + 14 * self.cell_h + 10), 'small', TEXT)
            if state['dare']:
                dare = ' WE DARE YOU TO ENTER!!  MUA HA-HA HA-HA!!! '.center(80, '*')
                window.blit_text(dare, (SCREEN_W // 2, y + 14 * self.cell_h + 90), 'menu', (230, 30, 30), center=True)

        window.overlay = draw
        for top_end, colors_list in ((40, gr.colors_), (25, gr.colors_s), (27, gr.colors_sl), (31, gr.colors_sla), (27, gr.colors_slay), (25, gr.colors_slaye)):
            for _ in range(1, top_end):
                state['colors'] = random.choice(colors_list)
                await asyncio.sleep(gap)
                gap = gap / (0.0125 + divisor)
                divisor = divisor + 0.0005
        state['colors'] = gr.colors_slayer[0]
        await asyncio.sleep(0.35)
        state['version'] = True
        await asyncio.sleep(0.85)
        state['dare'] = True
        window.overlay = None
        window.title_draw = draw  # the finished title stays up until the next clear
        window.mode = 'title'


class LoserAnimation(AsciiArt):
    """Slayer_Graphics.loser_banner: LOSER jumps around the screen, letters lighting up green."""

    async def play(self):
        gr, window = self.gr, self.window
        gap, divisor = (0.05, 2) if acc.dev_mode() else (0.45, 1.1)
        word, letters = gr.loser, gr.loser_letters
        window.mode = 'loser'
        state = {'colors': gr.letter_colors_loser[0], 'pos': (0, 0)}
        window.overlay = lambda: self.draw_word(word, letters, state['colors'], *state['pos'])
        width, height = self.word_width(word, letters), 14 * self.cell_h

        def jump():
            state['pos'] = (random.randint(0, SCREEN_W - width), random.randint(0, SCREEN_H - height))

        for _ in range(1, 10):
            for version in range(6):
                jump()
                state['colors'] = gr.letter_colors_loser[version]
                await asyncio.sleep(gap)
                gap = gap / divisor
            await asyncio.sleep(gap)
            gap = gap / divisor
        jump()
        state['colors'] = gr.letter_colors_loser[6]
        await asyncio.sleep(0.75)
        window.overlay = None
