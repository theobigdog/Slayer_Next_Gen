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
import math
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
DAMAGE_RED = (255, 72, 60)
HEAL_BLUE = (90, 170, 255)
TAG_COLORS = {'red': (240, 70, 70), 'magenta': (200, 110, 200), 'green': (90, 200, 90), 'white': (255, 255, 255),
              'gold': (212, 166, 64), 'narr': (122, 200, 222)}  # narr: the narrator talking to you, in its own color
TAG = re.compile(r'\[(red|magenta|green|white|gold|narr|/)\]')
DIM_OLDER_TEXT = True  # text from before your last click is drawn a little dimmer, so the new part stands out


# Fonts: New Rocker for everything that isn't narration (names, headings, menus, boxes, numbers);
# a calmer, still-stylized font for the narration so long lines stay easy to read.
NARRATION_FONT, NARRATION_SIZE = 'Fondamento-Regular.ttf', 24  # swap the file name to try another font

def font(size: int, kind: str = 'regular') -> pygame.font.Font:
    files = {'regular': 'DejaVuSans.ttf', 'bold': 'DejaVuSans-Bold.ttf', 'mono': 'DejaVuSansMono-Bold.ttf',
             'fancy': 'NewRocker-Regular.ttf', 'narration': NARRATION_FONT}
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

    chars_per_second = 260  # typewriter speed for the narration (big chunks go faster, see advance_typewriter)

    def __init__(self, headless_fps: int = 60):
        pygame.init()
        flags = 0 if IN_BROWSER else pygame.SCALED | pygame.RESIZABLE
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)
        pygame.display.set_caption('SLAYER')
        self.clock = pygame.time.Clock()
        self.fps = headless_fps
        self.fonts = {
            'text': font(NARRATION_SIZE, 'narration'),
            'menu': font(22, 'fancy'), 'menu_s': font(19, 'fancy'), 'menu_xs': font(16, 'fancy'), 'name': font(20, 'fancy'), 'name_small': font(16, 'fancy'),
            'name_big': font(28, 'fancy'), 'box_big': font(20, 'fancy'),
            'round': font(32, 'fancy'), 'menu_title': font(22, 'fancy'), 'float': font(34, 'fancy'),
            'box': font(17, 'fancy'), 'hp': font(16, 'fancy'),
            'small': font(14), 'title': font(13, 'mono'), 'big': font(30, 'bold'),
        }
        self.mode = 'text'          # 'title', 'text', 'party', 'battle', 'loser', 'end'
        self.party, self.mobs, self.round_num = [], [], 0
        self.lines = []             # narration lines since the last clear (tagged text)
        self.revealed = 0.0         # how many characters of self.lines the typewriter has shown
        self.scroll_back = 0        # lines the player has scrolled up with the mouse wheel
        self.waiting = None         # (kind, future, extra) while the game waits on the player
        self.waiting_since = 0.0    # when the current wait began (a double-click can't skip the next line)
        self.now = pygame.time.get_ticks() / 1000
        self.dt = 0.0
        self.health_seen = {}       # id(entity) -> (entity, hp, max hp) last frame, for the floating numbers
        self.floaters = []          # floating damage/heal numbers on screen
        self.motion = Motion(self)  # the little idle animations
        self.placeholders = {}
        self.buttons = []
        self.typed = ''             # ask_text's input so far
        self.targets = []           # (rect, entity) for clickable sprites during choose_target
        self.sprite_cache = {}
        self.overlay = None         # title / loser animation frame (a function that draws it)
        self.title_draw = None      # the finished title screen, shown until the next clear
        self.sprite_rects = []      # (rect, entity) for every sprite drawn this frame
        self.menu_labels = []
        self.echo_line = None       # which narration line gets the player's answer written after it
        self.fresh_from = 0         # first narration line added since the player's last click/answer
        self.mark_new = False       # the next text added starts a new, separated chunk
        self.text_version = 0       # bumps whenever the narration changes (for the wrap cache)
        self.wrap_cache = (None, [])
        self.num_buffer, self.num_time = '', 0.0  # two-digit menu numbers (10, 11) being typed
        self.error = None

    # ---------- the frame loop -------------------------------------------------

    async def run(self, game):
        """Run the game coroutine alongside the frame loop until the window closes."""
        task = asyncio.ensure_future(self.guarded(game))
        while True:
            if self.fps and not IN_BROWSER:
                self.clock.tick(self.fps)
            now = pygame.time.get_ticks() / 1000
            dt, self.now = min(0.1, now - self.now), now
            self.dt = dt
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    task.cancel()
                    pygame.quit()
                    return
                self.handle(event)
            self.advance_typewriter(dt)
            self.commit_number_if_done()
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
        if event.type == pygame.MOUSEWHEEL:
            self.scroll(event.y * -3)
            return
        if not self.waiting:
            return
        kind, future, extra = self.waiting
        clicked = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
        enter = event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)

        if kind in ('pause', 'close'):
            if (clicked or enter) and self.now - self.waiting_since > 0.15:
                self.revealed = self.total_chars()  # one click finishes any typing AND moves on
                if kind == 'close':
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
                else:
                    self.resolve(None)
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

        if kind != 'yes_no' and event.type == pygame.KEYDOWN and self.num_buffer and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return self.commit_number()
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
                if len(options) < 10:
                    self.pick_number(number)
                else:  # 10 or more choices: '1' might be the start of '10' or '11', so wait a moment
                    self.num_buffer += str(number)
                    self.num_time = self.now
                    if int(self.num_buffer) * 10 > len(options):  # no second digit could still make sense
                        self.commit_number()
            elif event.key == pygame.K_BACKSPACE:
                self.num_buffer = ''

    def pick_number(self, number):
        kind, _, extra = self.waiting
        options = extra['options']
        if 1 <= number <= len(options):
            self.pick(options[number - 1])
        else:
            self.oops(extra)

    def commit_number(self):
        typed, self.num_buffer = self.num_buffer, ''
        if typed and self.waiting and self.menu_open():
            self.pick_number(int(typed))

    def commit_number_if_done(self):
        if self.num_buffer and self.now - self.num_time > 0.8:
            self.commit_number()

    def scroll(self, lines):
        """Mouse wheel: look back at earlier lines (since the last clear). New text snaps back down."""
        most = max(0, self.lines_started() - self.page_capacity())
        self.scroll_back = max(0, min(most, self.scroll_back - lines))

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
        self.add_prompt(pick_line(extra['prompt']))

    def pick(self, value):
        kind, _, extra = self.waiting
        if kind in ('choose', 'choose_target'):
            label = self.menu_labels[extra['options'].index(value)]
            self.echo(label.replace('  (recharging)', ''))
        elif kind == 'yes_no':
            self.echo('Yes' if value else 'No')
        self.buttons, self.targets = [], []
        self.resolve(value)

    def resolve(self, value):
        kind, future, extra = self.waiting
        self.waiting = None
        self.buttons, self.targets = [], []
        self.num_buffer = ''
        self.mark_new = True  # whatever gets said next is a new chunk
        if future and not future.done():
            future.set_result(value)

    def echo(self, answer):
        """Write the player's answer after its question, the way the terminal shows what you typed."""
        if answer and self.echo_line is not None and self.echo_line < len(self.lines):
            self.lines[self.echo_line] = self.lines[self.echo_line].rstrip() + f'  [gold]{answer}[/]'
            self.text_version += 1

    async def wait_for(self, kind, extra=None):
        future = asyncio.get_running_loop().create_future()
        self.waiting = (kind, future, extra)
        self.waiting_since = self.now
        return await future

    # ---------- narration text -------------------------------------------------

    def add_text(self, text):
        self.scroll_back = 0
        if self.mark_new:  # the first text after a click or an answer: leave a gap, and it's the new part
            self.mark_new = False
            if self.lines and self.lines[-1].strip():
                self.lines.append('')
            self.fresh_from = len(self.lines)
        for line in str(text).split('\n'):
            if line.strip() == '' and (not self.lines or self.lines[-1].strip() == ''):
                continue  # no blank line at the top of the box, and never two in a row
            self.lines.append(line)
        self.text_version += 1

    def add_prompt(self, text):
        self.add_text(text)
        self.echo_line = len(self.lines) - 1

    def total_chars(self):
        return sum(len(TAG.sub('', line)) for line in self.lines)

    def typed_out(self):
        return self.revealed >= self.total_chars()

    def wrap_width(self):
        """Always wrap to the narrower box (the one with a menu beside it), so a menu opening never re-splits lines."""
        return (780 if self.mode in ('battle', 'party') else 740) - 40

    def visual_lines(self):
        """Every narration line wrapped to the box: [(runs, chars_in_line, line_number)]."""
        key = (self.text_version, self.wrap_width())
        if self.wrap_cache[0] != key:
            out = []
            for number, line in enumerate(self.lines):
                for runs in wrap_rich(line, self.fonts['text'], self.wrap_width()):
                    out.append((runs, sum(len(t) for t, _ in runs), number))
            self.wrap_cache = (key, out)
        return self.wrap_cache[1]

    def page_capacity(self):
        room = self.text_box().height - 30
        if self.waiting and self.waiting[0] in ('text', 'yes_no'):
            room -= 56  # leave space for the typing field / the Yes and No buttons at the bottom of the box
        return max(1, room // self.line_h)

    def lines_started(self, vis=None):
        """How many wrapped lines the typewriter has reached so far."""
        budget, count = self.revealed, 0
        for _, n, _ in (vis if vis is not None else self.visual_lines()):
            if budget <= 0 and count:
                break
            budget -= n
            count += 1
        return count

    def advance_typewriter(self, dt):
        total = self.total_chars()
        backlog = total - self.revealed
        if backlog > 0:
            speed = max(self.chars_per_second, backlog * 6)  # a big chunk of text finishes in a fraction of a second
            self.revealed = min(total, self.revealed + speed * dt)

    async def until_typed(self):
        while not self.typed_out():
            await asyncio.sleep(0)

    # ---------- the Slayer_UI calls --------------------------------------------

    async def say(self, text=''):
        self.add_text(text)

    async def wait(self, seconds):
        await self.until_typed()
        await asyncio.sleep(seconds)

    async def pause(self):
        if self.mode == 'battle' and not any(line.strip() for line in self.lines):
            return  # the terminal pauses on its status screen; here the battle is always on screen, so nothing to wait for
        await self.wait_for('pause')  # a click while the text is still typing finishes it and moves on

    async def clear(self):
        await self.until_typed()
        self.lines, self.revealed, self.scroll_back = [], 0.0, 0
        self.fresh_from, self.mark_new, self.echo_line = 0, False, None
        self.text_version += 1
        if self.mode == 'title':
            self.mode = 'text'

    async def choose(self, prompt, labels, oops):
        self.add_prompt(pick_line(prompt))
        return await self.menu('choose', list(range(len(labels))), labels, prompt, oops)

    async def choose_target(self, prompt, party, mobs, oops):
        self.add_prompt(pick_line(prompt))
        labels = [f'{t.name}' for t in party + mobs]
        return await self.menu('choose_target', party + mobs, labels, prompt, oops)

    async def menu(self, kind, options, labels, prompt, oops):
        self.menu_labels = labels
        return await self.wait_for(kind, {'options': options, 'prompt': prompt, 'oops': oops})

    async def yes_no(self, prompt):
        self.add_prompt(prompt)
        self.menu_labels = ['Yes', 'No']
        return await self.wait_for('yes_no', {'options': [True, False]})

    async def ask_text(self, prompt):
        self.add_prompt(prompt)
        self.typed = ''
        pygame.key.start_text_input()
        try:
            answer = await self.wait_for('text')
        finally:
            pygame.key.stop_text_input()
        self.echo(answer.strip())
        return answer

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

    line_h = 28  # pixels per narration line

    def text_box(self):
        if self.mode in ('battle', 'party'):
            return pygame.Rect(16, 444, 780 if self.menu_open() else 1248, 264)
        return pygame.Rect(60, 60, 1160 if not self.menu_open() else 740, 600)

    def menu_area(self):
        if self.mode in ('battle', 'party'):
            return pygame.Rect(808, 444, 456, 264)
        return pygame.Rect(812, 60, 408, 600)

    def menu_open(self):
        """A side menu is showing (Yes/No buttons sit inside the text box instead)."""
        return bool(self.waiting) and self.waiting[0] in ('choose', 'choose_target')

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
        if self.menu_open():
            self.draw_menu()
        self.draw_floaters()

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
        end = max(0, self.lines_started(vis) - self.scroll_back)
        top = max(0, end - self.page_capacity())
        if top < end - 1 and vis[top][1] == 0:
            top += 1  # a page never starts with a blank line
        budget = self.revealed - sum(n for _, n, _ in vis[:top])
        y = box.y + 16
        for runs, n, number in vis[top:end]:
            if budget <= 0:
                break
            x = box.x + 20
            older = DIM_OLDER_TEXT and number < self.fresh_from
            for chunk, color in runs:
                shown = chunk[:max(0, int(budget))]
                budget -= len(chunk)
                if shown:
                    if older:
                        color = tuple(int(c * 0.62 + b * 0.38) for c, b in zip(color, BG))
                    surf = self.fonts['text'].render(shown, True, color)
                    self.screen.blit(surf, (x, y))
                    x += surf.get_width()
            y += self.line_h
        kind = self.waiting[0] if self.waiting else None
        if kind == 'text':
            field = pygame.Rect(box.x + 20, box.bottom - 52, box.width - 40, 38)
            pygame.draw.rect(self.screen, BG, field, border_radius=6)
            pygame.draw.rect(self.screen, GOLD, field, 2, border_radius=6)
            caret = '|' if (pygame.time.get_ticks() // 500) % 2 == 0 else ' '
            self.blit_text(self.typed + caret, (field.x + 10, field.y + 6))
        elif kind == 'yes_no':
            self.buttons = []
            mouse = pygame.mouse.get_pos()
            for i, (label, value) in enumerate((('Yes  (Y)', True), ('No  (N)', False))):
                rect = pygame.Rect(box.right - 20 - (2 - i) * 150 + 10, box.bottom - 50, 140, 38)
                hover = rect.collidepoint(mouse)
                pygame.draw.rect(self.screen, (58, 50, 42) if hover else (40, 35, 30), rect, border_radius=6)
                pygame.draw.rect(self.screen, GOLD, rect, 2, border_radius=6)
                self.blit_text(label, rect.center, 'menu', TEXT, center=True)
                self.buttons.append(Button(rect, label, value))
        elif kind in ('pause', 'close') and self.typed_out():
            hint = {'pause': 'click or Enter', 'close': 'click to close'}[kind]
            self.blit_text(f'{hint}  ▼', (box.right - 20 - self.fonts['small'].size(f'{hint}  ▼')[0], box.bottom - 26), 'small', GOLD)

    def draw_menu(self):
        kind, _, extra = self.waiting
        labels = self.menu_labels
        area = self.menu_area()
        self.panel(area, GOLD)
        title = {'choose': 'Choose', 'choose_target': 'Target'}[kind]
        if self.num_buffer:
            title += f'   {self.num_buffer}_'  # a two-digit number being typed
        self.blit_text(title, (area.x + 16, area.y + 10), 'menu_title', GOLD)
        columns = 1 if (area.height - 50) // max(1, len(labels)) >= 30 else 2  # a long list (say 11 targets) goes in two columns
        per_column = -(-len(labels) // columns)
        row_h = min(34, (area.height - 50) // max(1, per_column))
        col_w = (area.width - 20 - (columns - 1) * 8) // columns
        self.buttons = []
        mouse = pygame.mouse.get_pos()
        for i, label in enumerate(labels):
            col, row = divmod(i, per_column)  # numbers run down the first column, then the second
            rect = pygame.Rect(area.x + 10 + col * (col_w + 8), area.y + 44 + row * row_h, col_w, row_h - 4)
            hover = rect.collidepoint(mouse)
            pygame.draw.rect(self.screen, (58, 50, 42) if hover else (40, 35, 30), rect, border_radius=6)
            self.draw_menu_label(rect, str(i + 1), label)
            self.buttons.append(Button(rect, label, extra['options'][i]))
        if kind == 'choose_target':
            self.targets = [(rect, ent) for rect, ent in self.sprite_rects if ent in extra['options']]
            for rect, _ in self.targets:
                pygame.draw.rect(self.screen, GOLD, rect.inflate(10, 10), 3, border_radius=8)

    def draw_menu_label(self, rect, key, label):
        """One menu row: its number, then the label in the biggest size that fits. A special weapon
        that's recharging is red and crossed out, with 'Recharging' after it."""
        recharging = label.endswith('  (recharging)')
        base = label.replace('  (recharging)', '')
        room = rect.width - 16
        for name in ('menu', 'menu_s', 'menu_xs'):
            fnt = self.fonts[name]
            parts = [(f'{key}   ', TEXT, False), (base, (220, 80, 70) if recharging else TEXT, recharging)]
            if recharging:
                parts.append(('   Recharging', GOLD, False))
            if sum(fnt.size(t)[0] for t, _, _ in parts) <= room:
                break
        x, y = rect.x + 8, rect.centery - fnt.get_height() // 2
        for text, color, strike in parts:
            while fnt.size(text)[0] > rect.right - 8 - x and len(text) > 4:
                text = text[:-4] + '...'
            surf = fnt.render(text, True, color)
            self.screen.blit(surf, (x, y))
            if strike:
                pygame.draw.line(self.screen, color, (x, rect.centery + 1), (x + surf.get_width(), rect.centery + 1), 2)
            x += surf.get_width()

    # battle scene

    def draw_battle(self):
        self.blit_text(f'Round {self.round_num}', (24, 16), 'round', GOLD)
        self.sprite_rects = []
        self.draw_party_row(self.party, top=64)
        self.draw_mobs()
        self.motion.draw_effects()
        self.motion.draw_particles()

    def draw_party_row(self, party, top):
        slot_w, sprite = 150, 104
        for i, heroine in enumerate(party):
            col, row = i % 4, i // 4
            x = 24 + col * slot_w
            y = top + row * 190
            rect = pygame.Rect(x + (slot_w - sprite) // 2 - 6, y, sprite, sprite)
            self.draw_sprite(heroine, rect, heroine.hero_class, HERO_BOX)
            self.draw_health_bar(heroine, rect, slot_w - 12)
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
            self.draw_health_bar(mob, rect, max(w, 130))
            self.sprite_rects.append((rect, mob))
            x += w + gap

    def draw_sprite(self, entity, rect, label, box_color):
        dead = entity.is_dead
        image = self.sprite_for(entity, rect.size)
        art = image is not None
        kind = class_key(entity)
        if image is None:
            share = max(0.0, min(1.0, entity.health / entity.starting_health))
            if kind == 'shifter' and not dead:
                image = self.motion.shifter_box(rect.size, box_color, share)
            else:
                image = self.placeholder(rect.size, box_color, dead, share)
        else:
            image = image.copy()
            if dead:
                image.fill((90, 90, 90, 255), special_flags=pygame.BLEND_RGBA_MULT)
        image = image.copy()
        status = ('in pieces' if getattr(entity, 'blown_up', False) else 'dead') if dead else None
        labels = self.box_labels(rect.size, entity.name, label, status, art)
        image.blit(labels, labels.get_rect(midbottom=(image.get_width() // 2, image.get_height())))  # her name inside the box, her class under it
        pose = Pose() if dead else self.motion.pose(entity, kind, rect)
        if pose.sx != 1 or pose.sy != 1:
            image = pygame.transform.smoothscale(image, (max(1, round(image.get_width() * pose.sx)), max(1, round(image.get_height() * pose.sy))))
        if pose.angle:
            image = pygame.transform.rotate(image, pose.angle)
        self.screen.blit(image, image.get_rect(midbottom=(rect.centerx + pose.dx, rect.bottom + pose.dy)))
        if not dead:
            self.motion.effects(entity, kind, rect)
        self.track_health(entity, rect)

    def placeholder(self, size, color, dead, share=1.0):
        """The stand-in box until there's art: an outline filled from the bottom up to the HP left
        (half health = half full). The name and class go on top of it (box_labels)."""
        percent = round(share * 100)
        key = (size, color, dead, percent)
        if key not in self.placeholders:
            box = pygame.Surface(size, pygame.SRCALPHA)
            edge = tuple(c // 3 for c in color) if dead else color
            pygame.draw.rect(box, (*edge, 70), box.get_rect(), border_radius=8)  # the empty part, faint
            fill_h = round(size[1] * percent / 100)
            if fill_h > 0:
                fill = pygame.Surface(size, pygame.SRCALPHA)
                pygame.draw.rect(fill, edge, fill.get_rect(), border_radius=8)
                box.blit(fill, (0, size[1] - fill_h), pygame.Rect(0, size[1] - fill_h, size[0], fill_h))
            pygame.draw.rect(box, edge, box.get_rect(), 2, border_radius=8)
            self.placeholders[key] = box
        return self.placeholders[key]

    def box_labels(self, size, name, label, status, art=False):
        """What's written inside a combatant's box: her name (two smaller lines if it's long), her class
        on the line under it, and 'dead' under that once she's down. Drawn over art too, once there is some."""
        key = ('labels', size, name, label, status, art)
        dead = status is not None
        if key not in self.placeholders:
            surf = pygame.Surface(size, pygame.SRCALPHA)
            rows = []  # (text, font, color)
            big = size[0] >= 180  # Happy's box gets bigger lettering
            names, name_font = self.name_lines(name, size[0] - 10, 3, 'name_big' if big else 'name', 'name' if big else 'name_small')
            rows += [(line, name_font, DIM if dead else TEXT) for line in names]
            for i, part in enumerate(label.replace('_', ' ').split(' (')):
                rows.append((part if i == 0 else '(' + part, 'box_big' if big else 'box', DIM if dead else (205, 220, 214)))
            if dead:
                rows.append((status, 'name', HP_CRIT))  # 'dead', or 'in pieces' for a Sapper after her Big Badda Boom
            heights = [self.fonts[f].get_linesize() - 2 for _, f, _ in rows]
            y = size[1] - sum(heights) - 6 if art else size[1] * 0.42 - sum(heights) / 2  # over art: along the bottom, off her face
            for (text, fnt, color), h in zip(rows, heights):
                rendered = self.fonts[fnt].render(text, True, color)
                shadow = self.fonts[fnt].render(text, True, (0, 0, 0))
                shadow.set_alpha(150)
                spot = rendered.get_rect(midtop=(size[0] // 2, round(y)))
                surf.blit(shadow, spot.move(1, 1))  # a soft shadow keeps it readable on any fill (or art)
                surf.blit(rendered, spot)
                y += h
            self.placeholders[key] = surf
        return self.placeholders[key]

    # floating numbers: the window notices HP changes by itself, so the game code needs nothing new

    def track_health(self, entity, rect):
        hp, top = int(round(entity.health)), entity.starting_health
        seen = self.health_seen.get(id(entity))
        if seen and seen[0] is entity and seen[2] == top and seen[1] != hp: # a new max HP (Happy's enrage) isn't a heal
            delta = hp - seen[1]
            stacked = sum(1 for f in self.floaters if f['entity'] is entity)
            self.floaters.append({'entity': entity, 'text': f'{delta:+d}', 'color': HEAL_BLUE if delta > 0 else DAMAGE_RED,
                                  'x': rect.centerx, 'y': rect.y + rect.height * 0.62 - stacked * 28, 'born': self.now})  # rises up through the box, clear of the Round heading
        self.health_seen[id(entity)] = (entity, hp, top)

    def draw_floaters(self):
        life = 1.4
        self.floaters = [f for f in self.floaters if self.now - f['born'] < life]
        for f in self.floaters:
            age = self.now - f['born']
            rise = 50 * (1 - (1 - age / life) ** 2)  # fast at first, then easing off
            alpha = 255 if age < life / 2 else int(255 * (1 - (age - life / 2) / (life / 2)))
            fnt = self.fonts['float']
            text = fnt.render(f['text'], True, f['color'])
            edge = fnt.render(f['text'], True, (0, 0, 0))
            surf = pygame.Surface((text.get_width() + 4, text.get_height() + 4), pygame.SRCALPHA)
            for ox, oy in ((0, 2), (4, 2), (2, 0), (2, 4)):
                surf.blit(edge, (ox, oy))
            surf.blit(text, (2, 2))
            surf.set_alpha(alpha)
            self.screen.blit(surf, surf.get_rect(center=(f['x'], f['y'] - rise)))

    def sprite_for(self, entity, size):
        """assets/sprites/<class>_<pose>.png, e.g. warrior_idle.png, disgruntled_dwarf_enraged.png."""
        slug = class_key(entity)
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

    def name_lines(self, name, width, max_lines=2, big='name', small='name_small'):
        """A name that fits its slot: one line if it can, else up to max_lines smaller lines, trimmed with ... if needed."""
        if self.fonts[big].size(name)[0] <= width:
            return [name], big
        fnt, lines, line = self.fonts[small], [], ''
        for word in name.split():
            trial = (line + ' ' + word).strip()
            if fnt.size(trial)[0] <= width or not line:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)
        if len(lines) > max_lines:
            lines = lines[:max_lines - 1] + [' '.join(lines[max_lines - 1:])]
        while fnt.size(lines[-1])[0] > width and len(lines[-1]) > 3:
            lines[-1] = lines[-1][:-4].rstrip() + '...'
        return lines, small

    def draw_health_bar(self, entity, rect, width):
        """The HP bar and numbers under a combatant's box (her name is inside the box now)."""
        bar = pygame.Rect(0, 0, width - 20, 9)
        bar.midtop = (rect.centerx, rect.bottom + 12)
        pygame.draw.rect(self.screen, (55, 50, 45), bar, border_radius=4)
        share = max(0.0, entity.health / entity.starting_health)
        color = HP_CRIT if share <= 0.1 else HP_LOW if share <= 0.5 else HP_GOOD
        if share > 0:
            pygame.draw.rect(self.screen, color, (bar.x, bar.y, max(4, int(bar.width * share)), bar.height), border_radius=4)
        self.blit_text(f'{int(round(entity.health))}/{entity.starting_health}', (rect.centerx, bar.bottom + 11), 'hp', DIM, center=True)

    def draw_party_lineup(self):
        self.sprite_rects = []
        self.blit_text('Your party', (24, 16), 'round', GOLD)
        self.draw_party_row(self.party, top=64)
        self.motion.draw_effects()
        self.motion.draw_particles()


def class_key(entity) -> str:
    """'Battle_Mage' -> 'battle_mage', 'Disgruntled Dwarf' -> 'disgruntled_dwarf'."""
    return (getattr(entity, 'hero_class', None) or entity.mob_class).lower().replace(' ', '_')


def pick_line(lines):
    return lines if isinstance(lines, str) else random.choice(lines)


# ---------- little idle animations -------------------------------------------------

class Pose:
    """How to draw a sprite this frame: nudged by dx/dy, tilted by angle, squashed by sx/sy."""
    def __init__(self, dx=0.0, dy=0.0, angle=0.0, sx=1.0, sy=1.0):
        self.dx, self.dy, self.angle, self.sx, self.sy = dx, dy, angle, sx, sy


# Outlines in a -1..1 box for the Shifter's morph (the circle is worked out separately).
SHAPES = {
    'triangle': [(0, -1), (1, 1), (-1, 1)],
    'square': [(-1, -1), (1, -1), (1, 1), (-1, 1)],
    'trapezoid': [(-0.5, -1), (0.5, -1), (1, 1), (-1, 1)],
    'circle': None,
    'diamond': [(0, -1), (1, 0), (0, 1), (-1, 0)],
    'star': [(math.cos(math.pi * k / 5 - math.pi / 2) * (1 if k % 2 == 0 else 0.45),
              math.sin(math.pi * k / 5 - math.pi / 2) * (1 if k % 2 == 0 else 0.45)) for k in range(10)],
    'hexagon': [(math.cos(math.pi * k / 3), math.sin(math.pi * k / 3)) for k in range(6)],
}
SHIFT_ORDER = ['triangle', 'square', 'trapezoid', 'circle', 'diamond', 'star', 'hexagon']
RAYS = 72  # points around each outline; morphing slides each point from one shape to the next


def ray_radius(polygon, angle):
    """How far from the middle a ray at this angle meets the polygon's edge."""
    dx, dy = math.cos(angle), math.sin(angle)
    best = None
    for (x1, y1), (x2, y2) in zip(polygon, polygon[1:] + polygon[:1]):
        ex, ey = x2 - x1, y2 - y1
        det = ex * dy - dx * ey
        if abs(det) < 1e-9:
            continue
        t = (ex * y1 - x1 * ey) / det
        u = (dx * y1 - dy * x1) / det
        if t > 0 and -1e-9 <= u <= 1 + 1e-9:
            best = t if best is None else min(best, t)
    return best or 0.0


def bezier(points, t):
    """A point along a curve through four control points (t from 0 to 1)."""
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = points
    a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3
    return (a * x0 + b * x1 + c * x2 + d * x3, a * y0 + b * y1 + c * y2 + d * y3)


def smooth(u):
    return u * u * (3 - 2 * u)


class Motion:
    """Per-class idle animations. They move whatever gets drawn (the boxes now, real art later),
    plus effects drawn on top of everything: a dagger, a staff, an arrow and bullseye, a fuse,
    a halo, sparkles, steam. The Shifter's box itself changes shape."""

    def __init__(self, window):
        self.window = window
        self.particles = []  # [x, y, vx, vy, age, life, size, grow, color]
        self.next_play = {}  # (id(entity), effect) -> when that effect next starts
        self.later = []      # effects to draw after every sprite and nameplate (so they land on top)
        self.popped = {}     # id(sapper) -> which fuse burn already went pop
        self.radii = {name: [1.0] * RAYS if poly is None else [ray_radius(poly, self.ray_angle(i)) for i in range(RAYS)]
                      for name, poly in SHAPES.items()}

    @staticmethod
    def ray_angle(i):
        return -math.pi / 2 + 2 * math.pi * i / RAYS  # starting at the top, going clockwise

    def phase(self, entity):
        return (id(entity) % 997) / 997 * 6.283  # so two of the same class don't move in lockstep

    def playing(self, entity, effect, every, length):
        """For an effect that plays now and then: its progress 0..1 while playing, else None."""
        now, key = self.window.now, (id(entity), effect)
        start = self.next_play.setdefault(key, now + random.uniform(0.3, every))
        if now < start:
            return None
        progress = (now - start) / length
        if progress >= 1:
            self.next_play[key] = now + random.uniform(every * 0.6, every * 1.4)
            return None
        return progress

    def pose(self, entity, kind, rect):
        t = self.window.now + self.phase(entity)
        if kind == 'shifter':     # drifts while its outline changes (see shifter_box)
            return Pose(3 * math.sin(t * 1.3), 2 * math.sin(t * 2.1))
        if kind == 'warrior':     # slow, heavy breathing
            return Pose(sy=1 + 0.018 * math.sin(t * 1.9))
        if kind in ('witch', 'cleric'):
            return Pose(dy=-3 - 3 * math.sin(t * 1.5))  # floats a little
        if kind == 'drunk_dwarf': # sways
            return Pose(3 * math.sin(t * 0.8), 0, 5 * math.sin(t * 1.1))
        if kind == 'disgruntled_dwarf':
            if entity.enraged:    # shaking with rage
                return Pose(random.uniform(-2.5, 2.5), random.uniform(-1.5, 1.5))
            return Pose(dy=2 * math.sin(t * 1.4))
        if kind == 'battle_mage' and self.smacked(entity):  # her staff just smacked her name: the box jolts
            return Pose(random.uniform(-3, 3), 3)
        return Pose(dy=1.5 * math.sin(t * 1.6))  # battle mage, hunter, sapper, anything new

    def smacked(self, entity):
        """True for the moment the Battle Mage's staff lands on her own name."""
        smack = self.next_play.get((id(entity), 'staff'))
        return smack is not None and 0.22 <= (self.window.now - smack) / 1.1 < 0.32

    def shifter_box(self, size, color, share):
        """The Shifter's placeholder: triangle -> square -> trapezoid -> circle -> diamond -> star -> hexagon,
        holding each shape a moment, then melting into the next. Filled up to her HP like the other boxes."""
        w, h = size
        t = self.window.now
        hold, morph = 1.0, 0.7
        step = int(t // (hold + morph))
        within = t % (hold + morph)
        a = self.radii[SHIFT_ORDER[step % len(SHIFT_ORDER)]]
        b = self.radii[SHIFT_ORDER[(step + 1) % len(SHIFT_ORDER)]]
        mix = 0.0 if within < hold else smooth((within - hold) / morph)
        cx, cy, hw, hh = w / 2, h / 2, w / 2 - 2, h / 2 - 2
        points = []
        for i in range(RAYS):
            r = a[i] * (1 - mix) + b[i] * mix
            angle = self.ray_angle(i)
            points.append((cx + r * math.cos(angle) * hw, cy + r * math.sin(angle) * hh))
        box = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.polygon(box, (*color, 70), points)
        fill_h = round(h * share)
        if fill_h > 0:
            fill = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.polygon(fill, color, points)
            box.blit(fill, (0, h - fill_h), pygame.Rect(0, h - fill_h, w, fill_h))
        pygame.draw.polygon(box, color, points, 2)
        return box

    def effects(self, entity, kind, rect):
        now, dt = self.window.now, self.window.dt
        if kind == 'warrior':     # a dagger thunks into her box and sticks for a bit
            stab = self.playing(entity, 'stab', 5.0, 1.8)
            if stab is not None:
                self.later.append(lambda r=rect.copy(), p=stab: self.draw_dagger(r, p))
        elif kind == 'battle_mage':  # her battle staff smacks her own name
            smack = self.playing(entity, 'staff', 4.5, 1.1)
            if smack is not None:
                self.later.append(lambda r=rect.copy(), p=smack: self.draw_staff(r, p))
        elif kind == 'hunter':    # an arrow lands in a bullseye on her box and quivers
            shot = self.playing(entity, 'arrow', 5.0, 2.2)
            if shot is not None:
                self.later.append(lambda r=rect.copy(), p=shot: self.draw_stuck_arrow(r, p))
        elif kind == 'sapper':    # a fuse that burns down, pops, and grows back
            self.later.append(lambda r=rect.copy(), e=entity: self.draw_fuse(e, r))
        elif kind == 'cleric':    # a soft halo
            glow = 150 + 80 * math.sin(now * 2.2 + self.phase(entity))
            def halo(r=rect.copy(), g=glow):
                ring = pygame.Surface((r.width, 24), pygame.SRCALPHA)
                pygame.draw.ellipse(ring, (255, 220, 120, int(g)), ring.get_rect().inflate(-r.width * 0.35, -6), 3)
                self.window.screen.blit(ring, (r.x, r.y - 22))
            self.later.append(halo)
        elif kind == 'witch':     # sparkles drifting up
            if random.random() < dt * 5:
                x = rect.x + random.uniform(0.15, 0.85) * rect.width
                self.particles.append([x, rect.y + 10, random.uniform(-8, 8), random.uniform(-40, -20), 0, 1.0, 3, 0,
                                       random.choice([(200, 120, 255), (255, 170, 60)])])
        elif kind == 'disgruntled_dwarf' and entity.enraged:  # steam venting off the top
            for side in (-1, 1):
                if random.random() < dt * 3:
                    x = rect.centerx + side * rect.width * 0.38
                    self.particles.append([x, rect.y + 30, side * random.uniform(15, 40), random.uniform(-50, -30), 0, 1.4, 7, 14, (210, 210, 210)])

    def draw_effects(self):
        for draw in self.later:
            draw()
        self.later = []

    def fade(self, progress, fade_at=0.85):
        return 255 if progress < fade_at else max(0, int(255 * (1 - (progress - fade_at) / (1 - fade_at))))

    def draw_dagger(self, rect, p):
        fly = 0.1
        tip = (rect.x + rect.width * 0.72, rect.y + rect.height * 0.3)
        back = (math.cos(math.radians(-40)), math.sin(math.radians(-40)))  # from the tip toward the handle: up and right
        perp = (-back[1], back[0])
        shift, wobble = 0.0, 0.0
        if p < fly:
            shift = (1 - p / fly) * 90  # still flying in
        else:
            wobble = math.sin(self.window.now * 70) * 3 * max(0.0, 1 - (p - fly) / 0.15)  # quivers when it lands
        at = lambda s, side=0.0: (tip[0] + back[0] * (s + shift) + perp[0] * (side + wobble),
                                  tip[1] + back[1] * (s + shift) + perp[1] * (side + wobble))
        surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        if p >= fly:  # the slit where it went in
            pygame.draw.line(surf, (0, 0, 0, 170), at(8, -5), at(8, 5), 3)
        pygame.draw.polygon(surf, (205, 210, 222), [at(8, -2.5), at(8, 2.5), at(32, 4.5), at(32, -4.5)])  # blade (tip buried)
        pygame.draw.line(surf, (150, 155, 170), at(9), at(31), 1)
        pygame.draw.line(surf, (190, 150, 60), at(32, -10), at(32, 10), 5)   # crossguard
        pygame.draw.line(surf, (110, 70, 40), at(33), at(48), 7)             # grip
        pygame.draw.circle(surf, (190, 150, 60), [round(v) for v in at(51)], 5)  # pommel
        surf.set_alpha(self.fade(p))
        self.window.screen.blit(surf, (0, 0))

    def draw_staff(self, rect, p):
        pivot = (rect.right + 26, rect.y - 6)       # where the Battle Mage would be holding it
        target = (rect.centerx + 14, rect.y + rect.height * 0.32)   # her name, inside her box
        hit = math.atan2(target[1] - pivot[1], target[0] - pivot[0])
        raised = hit - math.radians(150)
        length = math.dist(pivot, target) + 4
        if p < 0.22:
            angle = raised + (hit - raised) * (p / 0.22) ** 2   # speeding up as it comes down
        elif p < 0.5:
            angle = hit
        else:
            angle = hit + (raised - hit) * smooth(min(1.0, (p - 0.5) / 0.3))
        end = (pivot[0] + math.cos(angle) * length, pivot[1] + math.sin(angle) * length)
        surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.line(surf, (120, 80, 45), pivot, end, 6)
        pygame.draw.line(surf, (160, 115, 70), pivot, end, 2)
        pygame.draw.circle(surf, (150, 80, 240), [round(v) for v in end], 8)
        pygame.draw.circle(surf, (215, 180, 255), [round(v) for v in end], 4)
        if 0.22 <= p < 0.4:  # the smack
            burst = (p - 0.22) / 0.18
            for k in range(8):
                a = k * math.pi / 4
                r1, r2 = 10 + 14 * burst, 18 + 20 * burst
                pygame.draw.line(surf, (255, 220, 120, int(255 * (1 - burst))),
                                 (target[0] + math.cos(a) * r1, target[1] + math.sin(a) * r1),
                                 (target[0] + math.cos(a) * r2, target[1] + math.sin(a) * r2), 3)
        surf.set_alpha(self.fade(p, 0.7))
        self.window.screen.blit(surf, (0, 0))

    def draw_stuck_arrow(self, rect, p):
        fly = 0.12
        bull = (rect.x + rect.width * 0.62, rect.y + rect.height * 0.84)  # low in the box, under her name and class
        surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for radius, color in ((15, (240, 235, 225)), (11, (200, 50, 50)), (7, (240, 235, 225)), (3, (200, 50, 50))):
            pygame.draw.circle(surf, color, [round(v) for v in bull], radius)
        if p < fly:
            start = rect.x - 90
            tip = (start + (bull[0] - start) * (p / fly), bull[1])
            tilt, buried = 0.0, 0
        else:
            tip = bull
            tilt = math.radians(4) * math.sin(self.window.now * 60) * max(0.0, 1 - (p - fly) / 0.25)
            buried = 6
        back = (-math.cos(tilt), -math.sin(tilt))
        shaft_from = (tip[0] + back[0] * buried, tip[1] + back[1] * buried)
        tail = (tip[0] + back[0] * 48, tip[1] + back[1] * 48)
        pygame.draw.line(surf, (190, 160, 110), shaft_from, tail, 3)
        if not buried:
            pygame.draw.polygon(surf, (225, 225, 225), [(tip[0] + 9, tip[1]), (tip[0], tip[1] - 5), (tip[0], tip[1] + 5)])
        for k in (0, 6):
            fx, fy = tail[0] - back[0] * k, tail[1] - back[1] * k
            pygame.draw.line(surf, (210, 60, 60), (fx, fy), (fx + back[0] * 7 - back[1] * 6, fy + back[1] * 7 + back[0] * 6), 2)
            pygame.draw.line(surf, (210, 60, 60), (fx, fy), (fx + back[0] * 7 + back[1] * 6, fy + back[1] * 7 - back[0] * 6), 2)
        surf.set_alpha(self.fade(p))
        self.window.screen.blit(surf, (0, 0))

    def draw_fuse(self, entity, rect):
        screen, now, dt = self.window.screen, self.window.now, self.window.dt
        cycle, burn = 6.0, 5.0
        t = now + self.phase(entity)
        within = t % cycle
        base = (rect.right - 18, rect.y + 2)
        curve = [base, (base[0] + 16, base[1] - 14), (base[0] - 12, base[1] - 30), (base[0] + 8, base[1] - 46)]
        if within < burn:
            left = 1 - within / burn  # how much fuse is still unburnt
            steps = max(2, int(24 * left))
            points = [bezier(curve, left * k / steps) for k in range(steps + 1)]
            pygame.draw.lines(screen, (90, 70, 45), False, points, 6)     # a rope fuse: dark edge...
            pygame.draw.lines(screen, (215, 185, 130), False, points, 3)  # ...light middle, so it shows on the dark background
            sx, sy = points[-1]
            pygame.draw.circle(screen, random.choice([(255, 200, 60), (255, 120, 30)]), (round(sx), round(sy)), random.randint(3, 6))
            if random.random() < dt * 12:
                self.particles.append([sx, sy, random.uniform(-40, 40), random.uniform(-60, -10), 0, 0.35, 2, 0, (255, 220, 120)])
        else:
            burn_number = int(t // cycle)
            if self.popped.get(id(entity)) != burn_number:  # pop! once per burn, then the fuse grows back
                self.popped[id(entity)] = burn_number
                for _ in range(10):
                    self.particles.append([base[0], base[1], random.uniform(-50, 50), random.uniform(-70, -10), 0, 0.6, 5, 10, (190, 190, 190)])

    def draw_particles(self):
        dt, screen = self.window.dt, self.window.screen
        alive = []
        for p in self.particles:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[4] += dt
            if p[4] < p[5]:
                alive.append(p)
                size = int(p[6] + p[7] * p[4])
                fade = int(200 * (1 - p[4] / p[5]))
                dot = pygame.Surface((size * 2 + 2, size * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(dot, (*p[8], fade), (size + 1, size + 1), size)
                screen.blit(dot, (p[0] - size, p[1] - size))
        self.particles = alive[-300:]


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
