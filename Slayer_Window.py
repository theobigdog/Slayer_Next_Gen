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
POISON_BOX = (92, 112, 28)     # a poisoned heroine's box: a sickly yellow-green instead of her healthy teal
POISON_EDGE = (184, 226, 62)   # the ring round her HP bar, her HP numbers, and the bubbles coming off her
HP_GOOD = (80, 176, 80)
HP_LOW = (192, 96, 192)    # the terminal's magenta, at 50% and below
HP_CRIT = (224, 64, 64)    # the terminal's red, at 10% and below
DAMAGE_RED = (255, 72, 60)
HEAL_BLUE = (90, 170, 255)
TAG_COLORS = {'red': (240, 70, 70), 'magenta': (200, 110, 200), 'green': (90, 200, 90), 'white': (255, 255, 255),
              'gold': (212, 166, 64), 'narr': (122, 200, 222),  # narr: the narrator talking to you, in its own color
              'thelist': (240, 70, 71)}  # The List: looks red, and clicking it shows every saved party
LIST_RED = TAG_COLORS['thelist']
TAG = re.compile(r'\[(red|magenta|green|white|gold|narr|thelist|/)\]')
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

    chars_per_second = 140  # typewriter speed for the narration (a long page speeds up a little, see advance_typewriter)
    catch_up = 2.5          # how much a long page speeds the typewriter up (it types backlog * catch_up chars a second)

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
            'name_big': font(28, 'fancy'), 'box_big': font(20, 'fancy'), 'keg': font(96, 'fancy'),
            'round': font(32, 'fancy'), 'menu_title': font(22, 'fancy'), 'float': font(34, 'fancy'),
            'box': font(17, 'fancy'), 'hp': font(16, 'fancy'),
            'small': font(14), 'title': font(13, 'mono'), 'big': font(30, 'bold'),
        }
        self.mode = 'text'          # 'title', 'text', 'party', 'battle', 'loser', 'end'
        self.party, self.mobs, self.round_num = [], [], 0
        self.menu_width_cache = (None, 0)  # (the labels it was worked out for, the width)
        self.active = None  # whoever's turn it is: her box gets a gold frame
        self.lines = []             # narration lines since the last clear (tagged text)
        self.revealed = 0.0         # how many characters of self.lines the typewriter has shown
        self.scroll_back = 0        # lines the player has scrolled up with the mouse wheel
        self.read_vis = 0           # wrapped lines before this one have been seen; text never scrolls past it unread
        self.more = False           # the box is full of unread text: 'more' until a click shows the next page
        self.links = []             # (rect, what) for clickable words in the narration (The List)
        self.list_open = False      # The List's panel of saved parties is showing
        self.list_rects = []        # (rect, name) rows in that panel
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
        self.ink_cache = {}         # (font, text, colour) -> that text already drawn (see ink)
        self.whole_boxes = {}       # a combatant's box with her name already on it (see draw_sprite)
        self.frame_rate = 0.0       # frames a second, smoothed (shown in the corner in dev mode)
        self.overlay = None         # title / loser animation frame (a function that draws it)
        self.effect_overlay = None  # a quick effect drawn on top of everything (the Big Badda Boom keg)
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
        self.restart = False        # in the browser, 'The End' offers a new game instead of closing the window
        self.touch_seen = False     # a finger touched the screen: show the on-screen keyboard for typing
        self.kb_choice = None       # the Keyboard button's choice: None = automatic (on after a touch)
        self.caps = True            # the on-screen keyboard's next letter is a capital
        self.key_rects = []         # (rect, key) for the on-screen keyboard
        self.kb_button = None       # the Keyboard button in the typing field

    # ---------- the frame loop -------------------------------------------------

    async def run(self, game):
        """Run the game coroutine alongside the frame loop until the window closes."""
        task = asyncio.ensure_future(self.guarded(game))
        while True:
            if self.fps and not IN_BROWSER:
                self.clock.tick(self.fps)
            now = pygame.time.get_ticks() / 1000
            if now > self.now:
                self.frame_rate += (1 / (now - self.now) - self.frame_rate) * 0.05  # smoothed, so the number is readable
            dt, self.now = min(0.1, now - self.now), now
            self.dt = dt
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    task.cancel()
                    pygame.quit()
                    return
                self.handle(event)
            if self.restart:
                task.cancel()
                return 'restart'  # main.py starts a fresh game (the browser has no window to close)
            self.advance_typewriter(dt)
            self.commit_number_if_done()
            if task.done() and self.mode != 'end':
                self.finish(task)
            self.draw()
            if acc.dev_mode():  # frames a second, top right: how smoothly this device is running the game
                self.blit_text(f'{self.frame_rate:.0f} fps', (SCREEN_W - 58, 4), 'small', DIM)
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
        if event.type == pygame.FINGERDOWN:
            self.touch_seen = True  # a phone or tablet: typing gets the on-screen keyboard (the tap itself arrives as a click)
            return
        clicked = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
        enter = event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
        if self.more and (enter or (clicked and not self.on_control(event.pos))):
            return self.next_page()  # the box is full: a click, tap or Enter shows the next page
        if not self.waiting:
            return
        kind, future, extra = self.waiting
        if self.more and kind in ('choose', 'choose_target', 'yes_no'):
            return  # the question is still on the next page: read it first

        if kind in ('pause', 'close'):
            if (clicked or enter) and self.now - self.waiting_since > 0.15:
                if self.total_chars() > self.page_limit():  # more than this box can hold: finish the page first
                    self.revealed = max(self.revealed, self.page_limit())
                    self.more = True
                    return
                self.revealed = self.total_chars()  # one click finishes any typing AND moves on
                if kind == 'close':
                    if IN_BROWSER:
                        self.restart = True
                    else:
                        pygame.event.post(pygame.event.Event(pygame.QUIT))
                else:
                    self.resolve(None)
            return

        if kind == 'text':
            if clicked and self.kb_button and self.kb_button.collidepoint(event.pos):
                self.kb_choice = not self.keyboard_on()  # the Keyboard button shows or hides it
                return
            if clicked and self.keyboard_on():
                for rect, key in self.key_rects:
                    if rect.collidepoint(event.pos):
                        return self.press_key(key)
            if clicked:
                for rect, name in (self.list_rects if self.list_open else []):
                    if rect.collidepoint(event.pos):
                        self.typed, self.list_open = name, False  # a saved name, typed in for you
                        return
                if any(rect.collidepoint(event.pos) for rect, _ in self.links):
                    self.list_open = not self.list_open
                    return
                self.list_open = False
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

    def keyboard_on(self):
        """The on-screen keyboard shows while typing, after a touch (or when the Keyboard button says so)."""
        wanted = self.kb_choice if self.kb_choice is not None else self.touch_seen
        return bool(wanted) and bool(self.waiting) and self.waiting[0] == 'text'

    def press_key(self, key):
        if key == 'ENTER':
            return self.resolve(self.typed)
        if key == 'BACK':
            self.typed = self.typed[:-1]
        elif key == 'SHIFT':
            self.caps = not self.caps
        elif len(self.typed) < 40:
            char = ' ' if key == 'SPACE' else (key.upper() if self.caps else key.lower())
            self.typed += char
            self.caps = char == ' '  # capital after a space, like a phone does for names

    def on_control(self, pos):
        return any(b.rect.collidepoint(pos) for b in self.buttons) or any(r.collidepoint(pos) for r, _ in self.targets)

    def next_page(self):
        """Show the next page of narration, keeping the last line of this one at the top for context."""
        shown = min(self.lines_started(), self.page_end())
        self.read_vis = max(self.read_vis + 1, shown - 1)
        self.more = False
        self.scroll_back = 0

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
        most = max(0, min(self.lines_started(), self.page_end()) - self.page_capacity())
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
            self.echo(label.replace('  (recharging)', '').partition('\t')[0])
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
        self.list_open = False
        self.read_vis = max(self.read_vis, min(self.lines_started(), self.page_end()))  # everything on screen has been seen
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

    def page_end(self):
        """The wrapped line the box can show up to without pushing unread text off the top."""
        return self.read_vis + self.page_capacity()

    def page_limit(self):
        """How many characters the typewriter may show before the player has to click for the next page."""
        return sum(n for _, n, _ in self.visual_lines()[:self.page_end()])

    def wrap_width(self):
        """Always wrap to the narrower box (the one with a menu beside it), so a menu opening never re-splits lines.
        The one exception: an item menu that had to widen for a long label (menu_width) narrows the box a bit more
        while it's open."""
        if self.mode in ('battle', 'party'):
            return 780 - (self.menu_width() - self.MENU_W) - 40
        return 740 - 40

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
        if self.keyboard_on():
            room -= self.keyboard_rect().height + 8
        return max(1, room // self.line_h)

    KB_ROWS = ['1234567890', 'QWERTYUIOP', "ASDFGHJKL'", 'ZXCVBNM-.!']
    KB_KEY_H, KB_GAP = 50, 6

    def keyboard_rect(self):
        box = self.text_box()
        height = 5 * self.KB_KEY_H + 4 * self.KB_GAP
        return pygame.Rect(box.x + 20, box.bottom - 14 - height, box.width - 40, height)

    def draw_keyboard(self):
        kb = self.keyboard_rect()
        gap, key_h = self.KB_GAP, self.KB_KEY_H
        key_w = (kb.width - 9 * gap) / 10
        self.key_rects = []
        rows = [[(ch, 1) for ch in row] for row in self.KB_ROWS]
        rows.append([('SHIFT', 1.5), ('SPACE', 5), ('BACK', 1.5), ('ENTER', 2)])
        labels = {'SHIFT': 'Shift', 'SPACE': 'Space', 'BACK': 'Back', 'ENTER': 'Enter'}
        mouse = pygame.mouse.get_pos()
        for r, row in enumerate(rows):
            total = sum(w * key_w + (w - 1) * gap for _, w in row) + (len(row) - 1) * gap
            x = kb.x + (kb.width - total) / 2
            y = kb.y + r * (key_h + gap)
            for key, w in row:
                rect = pygame.Rect(round(x), y, round(w * key_w + (w - 1) * gap), key_h)
                lit = rect.collidepoint(mouse) or (key == 'SHIFT' and self.caps)
                pygame.draw.rect(self.screen, (66, 56, 46) if lit else (40, 35, 30), rect, border_radius=6)
                pygame.draw.rect(self.screen, PANEL_EDGE, rect, 1, border_radius=6)
                text = labels.get(key) or (key if self.caps or not key.isalpha() else key.lower())
                self.blit_text(text, rect.center, 'menu', TEXT, center=True)
                self.key_rects.append((rect, key))
                x += w * key_w + w * gap

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
        limit = min(total, self.page_limit())  # never past a full box of unread text
        backlog = limit - self.revealed
        if backlog > 0:
            speed = max(self.chars_per_second, backlog * self.catch_up)
            self.revealed = min(limit, self.revealed + speed * dt)
        self.more = self.revealed >= limit and total > limit

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
        self.read_vis, self.more = 0, False
        self.list_open, self.links = False, []
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
        self.caps = True
        pygame.key.start_text_input()
        try:
            answer = await self.wait_for('text')
        finally:
            pygame.key.stop_text_input()
        self.echo(answer.strip())
        return answer

    async def show_battle(self, party, mobs, round_num, active=None):
        await self.clear()
        self.mode, self.party, self.mobs, self.round_num, self.active = 'battle', party, mobs, round_num, active

    async def show_party(self, party, active=None):
        await self.until_typed()
        self.mode, self.party, self.active = 'party', party, active

    async def title_screen(self):
        await TitleAnimation(self).play()

    async def loser_banner(self):
        await LoserAnimation(self).play()
        self.mode = 'text'

    async def effect(self, name):
        if name == 'boom':
            await self.until_typed()      # let 'lights the fuse...' finish first
            await asyncio.sleep(0.3)
            await KegFlash(self).play()

    # ---------- drawing --------------------------------------------------------

    line_h = 28  # pixels per narration line

    def text_box(self):
        if self.mode in ('battle', 'party'):
            return pygame.Rect(16, 444, self.menu_area().x - 28 if self.menu_open() else 1248, 264)
        return pygame.Rect(60, 60, 1160 if not self.menu_open() else 740, 600)

    MENU_ROW = 30  # pixels per menu row

    def menu_area(self):
        """In a battle or party screen the menu sits bottom right. A long one (more than 7 choices) grows upward
        over the enemies' side instead of splitting into two cramped columns, so every row stays one full line
        (Ted, Nov 8: names were getting cut to 'Thea (Wa...')."""
        if self.mode in ('battle', 'party'):
            rows = len(self.menu_labels) if self.menu_open() and not self.short_labels() else 0
            height = min(708 - 64, max(264, 50 + rows * self.MENU_ROW + 6))
            width = self.menu_width()
            return pygame.Rect(1264 - width, 708 - height, width, height)
        return pygame.Rect(812, 60, 408, 600)

    MENU_W, MENU_W_MAX = 456, 600

    def menu_width(self):
        """The menu is MENU_W wide, and widens (up to MENU_W_MAX, taking the room from the text box) when an item
        label is too long for it, so the end of a row is never cut off: that's where a potion's doses are
        (Ted, Nov 10: 'Happy's Hangover Cure (12 - 22 healing, 2/6 doses)'). Rows with a right-hand side
        ('Thea  (Warrior)\tbag 4/6') already keep that side whole, so they don't widen it."""
        if not self.menu_open():
            return self.MENU_W
        key = tuple(self.menu_labels)
        if self.menu_width_cache[0] != key:
            fnt = self.fonts['menu_s']
            longest = max([fnt.size(f'00   {label}')[0] for label in self.menu_labels if '\t' not in label], default=0)
            self.menu_width_cache = (key, max(self.MENU_W, min(self.MENU_W_MAX, longest + 36)))
        return self.menu_width_cache[1]

    def short_labels(self):
        """Every label fits half a menu (target names do): two columns are fine, no need to grow."""
        fnt = self.fonts['menu_s']
        return all(fnt.size(f'00   {label}')[0] <= 196 for label in self.menu_labels)

    def menu_font(self, labels, width):
        """The biggest menu font every row fits in, so the rows all match (the smallest if none fits)."""
        def short(label): # a long name may lose a few letters ('Brumhilda (Battl...'), rather than every row shrinking
            name, tab, side = label.replace('  (recharging)', '   Recharging').partition('\t')
            if not tab:
                return name # an item row: measured whole, so its end (damage, doses left) stays readable
            return (name if len(name) <= 18 else name[:15] + '...') + '   ' + side
        for name in ('menu', 'menu_s', 'menu_xs'):
            fnt = self.fonts[name]
            if all(fnt.size(f'00   ' + short(label))[0] <= width - 16 for label in labels):
                return name
        return 'menu_xs'

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
        if self.list_open and self.waiting and self.waiting[0] == 'text':
            self.draw_the_list()
        if self.menu_open() and not self.more:  # the menu shows once its question is on screen
            self.draw_menu()
        elif self.more:
            self.buttons, self.targets = [], []
        self.draw_floaters()
        if self.effect_overlay:
            self.effect_overlay()

    def panel(self, rect, edge=PANEL_EDGE):
        pygame.draw.rect(self.screen, PANEL, rect, border_radius=10)
        pygame.draw.rect(self.screen, edge, rect, 2, border_radius=10)

    def ink(self, fnt, text, color):
        """A piece of text as a picture, drawn once and kept, since turning letters into pixels is slow and most
        of what's on screen is the same from one frame to the next (Nov 11: the tablet was stuttering).
        fnt: a name in self.fonts, or a Font. The cache empties itself when it gets big."""
        key = (fnt, text, tuple(color))
        surf = self.ink_cache.get(key)
        if surf is None:
            if len(self.ink_cache) > 500:
                self.ink_cache.clear()
            surf = self.ink_cache[key] = (self.fonts[fnt] if isinstance(fnt, str) else fnt).render(text, True, color)
        return surf

    def blit_text(self, text, pos, fnt='text', color=TEXT, center=False):
        surf = self.ink(fnt, text, color)
        rect = surf.get_rect(center=pos) if center else surf.get_rect(topleft=pos)
        self.screen.blit(surf, rect)
        return rect

    def draw_text_box(self):
        box = self.text_box()
        self.panel(box)
        vis = self.visual_lines()
        end = max(0, min(self.lines_started(vis), self.page_end()) - self.scroll_back)
        top = max(0, end - self.page_capacity())
        if top < end - 1 and vis[top][1] == 0:
            top += 1  # a page never starts with a blank line
        budget = self.revealed - sum(n for _, n, _ in vis[:top])
        y = box.y + 16
        self.links = []
        mouse = pygame.mouse.get_pos()
        for runs, n, number in vis[top:end]:
            if budget <= 0:
                break
            x = box.x + 20
            older = DIM_OLDER_TEXT and number < self.fresh_from
            for chunk, color in runs:
                shown = chunk[:max(0, int(budget))]
                budget -= len(chunk)
                if shown:
                    link = color == LIST_RED
                    if older:
                        color = tuple(int(c * 0.62 + b * 0.38) for c, b in zip(color, BG))
                    # a finished piece of a line is kept (ink); the piece still typing out changes every frame
                    surf = self.ink('text', shown, color) if shown == chunk else self.fonts['text'].render(shown, True, color)
                    self.screen.blit(surf, (x, y))
                    if link:
                        rect = surf.get_rect(topleft=(x, y))
                        self.links.append((rect, 'the list'))
                        if rect.collidepoint(mouse):  # a hint that it's clickable, only while hovering
                            pygame.draw.line(self.screen, color, (rect.x, rect.bottom - 3), (rect.right, rect.bottom - 3), 1)
                    x += surf.get_width()
            y += self.line_h
        kind = self.waiting[0] if self.waiting else None
        if kind == 'text':
            keyboard = self.keyboard_on()
            bottom = self.keyboard_rect().top - 8 if keyboard else box.bottom - 14
            field = pygame.Rect(box.x + 20, bottom - 38, box.width - 40, 38)
            pygame.draw.rect(self.screen, BG, field, border_radius=6)
            pygame.draw.rect(self.screen, GOLD, field, 2, border_radius=6)
            label = 'Hide keyboard' if keyboard else 'Keyboard'  # for tablets (and remote desktop): tap to type with the screen
            width = self.fonts['small'].size(label)[0] + 20
            self.kb_button = pygame.Rect(field.right - width - 6, field.y + 6, width, field.height - 12)
            pygame.draw.rect(self.screen, (40, 35, 30), self.kb_button, border_radius=5)
            pygame.draw.rect(self.screen, PANEL_EDGE, self.kb_button, 1, border_radius=5)
            self.blit_text(label, self.kb_button.center, 'small', GOLD, center=True)
            if keyboard:
                self.draw_keyboard()
            caret = '|' if (pygame.time.get_ticks() // 500) % 2 == 0 else ' '
            self.blit_text(self.typed + caret, (field.x + 10, field.y + 6))
        elif kind == 'yes_no' and not self.more:  # the buttons show once the question is on screen
            self.buttons = []
            mouse = pygame.mouse.get_pos()
            for i, (label, value) in enumerate((('Yes  (Y)', True), ('No  (N)', False))):
                rect = pygame.Rect(box.right - 20 - (2 - i) * 150 + 10, box.bottom - 50, 140, 38)
                hover = rect.collidepoint(mouse)
                pygame.draw.rect(self.screen, (58, 50, 42) if hover else (40, 35, 30), rect, border_radius=6)
                pygame.draw.rect(self.screen, GOLD, rect, 2, border_radius=6)
                self.blit_text(label, rect.center, 'menu', TEXT, center=True)
                self.buttons.append(Button(rect, label, value))
        if self.more:
            hint = 'more  (click or Enter)'
            lift = 56 if kind in ('text', 'yes_no') else 0  # above the typing field / Yes and No buttons
            self.blit_text(f'{hint}  ▼', (box.right - 20 - self.fonts['small'].size(f'{hint}  ▼')[0], box.bottom - 26 - lift), 'small', GOLD)
        elif kind in ('pause', 'close') and self.typed_out():
            hint = {'pause': 'click or Enter', 'close': 'click to play again' if IN_BROWSER else 'click to close'}[kind]
            self.blit_text(f'{hint}  ▼', (box.right - 20 - self.fonts['small'].size(f'{hint}  ▼')[0], box.bottom - 26), 'small', GOLD)

    def draw_the_list(self):
        """The List: every saved party, newest first. Clicking a name types it in."""
        area = self.menu_area()
        area.height -= 66  # stops above the typing field
        if self.keyboard_on():
            area.height = self.keyboard_rect().top - 60 - area.y  # and above the on-screen keyboard
        self.panel(area, LIST_RED)
        self.blit_text('The List', (area.x + 16, area.y + 10), 'menu_title', LIST_RED)
        self.list_rects = []
        names = acc.saved_party_names()
        if not names:
            self.blit_text('Nobody yet.', (area.x + 16, area.y + 50), 'menu', DIM)
        mouse = pygame.mouse.get_pos()
        for i, name in enumerate(names[:(area.height - 50) // 34]):
            rect = pygame.Rect(area.x + 10, area.y + 44 + i * 34, area.width - 20, 30)
            pygame.draw.rect(self.screen, (58, 50, 42) if rect.collidepoint(mouse) else (40, 35, 30), rect, border_radius=6)
            self.blit_text(name, (rect.x + 10, rect.y + 3), 'menu', TEXT)
            self.list_rects.append((rect, name))

    def draw_menu(self):
        kind, _, extra = self.waiting
        labels = self.menu_labels
        area = self.menu_area()
        self.panel(area, GOLD)
        title = {'choose': 'Choose', 'choose_target': 'Target'}[kind]
        if self.num_buffer:
            title += f'   {self.num_buffer}_'  # a two-digit number being typed
        self.blit_text(title, (area.x + 16, area.y + 10), 'menu_title', GOLD)
        columns = 1 if (area.height - 50) // max(1, len(labels)) >= self.MENU_ROW else 2  # only if even the tall menu can't fit them
        per_column = -(-len(labels) // columns)
        row_h = min(34, (area.height - 50) // max(1, per_column))
        col_w = (area.width - 20 - (columns - 1) * 8) // columns
        self.buttons = []
        mouse = pygame.mouse.get_pos()
        font_name = self.menu_font(labels, col_w)
        for i, label in enumerate(labels):
            col, row = divmod(i, per_column)  # numbers run down the first column, then the second
            rect = pygame.Rect(area.x + 10 + col * (col_w + 8), area.y + 44 + row * row_h, col_w, row_h - 4)
            hover = rect.collidepoint(mouse)
            pygame.draw.rect(self.screen, (58, 50, 42) if hover else (40, 35, 30), rect, border_radius=6)
            self.draw_menu_label(rect, str(i + 1), label, font_name)
            self.buttons.append(Button(rect, label, extra['options'][i]))
            if hover:
                self.frame_who(label, extra['options'][i])
        if kind == 'choose_target':
            self.targets = [(rect, ent) for rect, ent in self.sprite_rects if ent in extra['options']]
            for rect, _ in self.targets:
                if not rect.colliderect(area): # never draw a target's outline over the menu itself
                    pygame.draw.rect(self.screen, GOLD, rect.inflate(10, 10), 3, border_radius=8)

    def frame_who(self, label, option):
        """Hovering a menu row about a heroine (or a target) frames her box up top, so 'Who gets it?' is never
        a guess about which Warrior is which."""
        who = option if hasattr(option, 'name') else next(
            (h for h in self.party if label.startswith(h.name + '  (') or label == h.name), None)
        for rect, entity in self.sprite_rects:
            if entity is who and not rect.colliderect(self.menu_area()):
                pygame.draw.rect(self.screen, GOLD, rect.inflate(16, 16), 4, border_radius=12)

    def draw_menu_label(self, rect, key, label, font_name=None):
        """One menu row: its number, then the label in the biggest size that fits. A special weapon
        that's recharging is red and crossed out, with 'Recharging' after it. A label with a tab in it
        ('Xena  (Warrior)\tbag 4/6') keeps the part after the tab on the right edge, always whole:
        a long name gets trimmed instead."""
        recharging = label.endswith('  (recharging)')
        base = label.replace('  (recharging)', '')
        base, _, side = base.partition('\t')
        room = rect.width - 16
        for name in ((font_name,) if font_name else ('menu', 'menu_s', 'menu_xs')):
            fnt = self.fonts[name]
            tail = [('   Recharging', GOLD)] if recharging else []
            if side:
                tail.append(('   ' + side, (200, 186, 150)))
            needed = fnt.size(f'{key}   ' + base)[0] + sum(fnt.size(t)[0] for t, _ in tail)
            if needed <= room:
                break
        x, y = rect.x + 8, rect.centery - fnt.get_height() // 2
        tail_w = sum(fnt.size(t)[0] for t, _ in tail)
        number = self.ink(fnt, f'{key}   ', TEXT)
        self.screen.blit(number, (x, y))
        x += number.get_width()
        if side and x + fnt.size(base[:8])[0] + tail_w > rect.right - 8: # the tail would run over the name: trim the tail too
            side_text = tail[-1][0]
            while x + fnt.size(base[:8])[0] + fnt.size(side_text)[0] > rect.right - 8 and len(side_text) > 6:
                side_text = side_text[:-4].rstrip() + '...'
            tail[-1] = (side_text, tail[-1][1])
            tail_w = sum(fnt.size(t)[0] for t, _ in tail)
        text = base
        while fnt.size(text)[0] > rect.right - 8 - tail_w - x and len(text) > 4:
            text = text[:-4].rstrip() + '...'  # trim the name before the tail
        color = (220, 80, 70) if recharging else TEXT
        surf = self.ink(fnt, text, color)
        self.screen.blit(surf, (x, y))
        if recharging:
            pygame.draw.line(self.screen, color, (x, rect.centery + 1), (x + surf.get_width(), rect.centery + 1), 2)
        x += surf.get_width()
        if recharging:
            surf = self.ink(fnt, tail[0][0], tail[0][1])
            self.screen.blit(surf, (x, y))
        if side:
            surf = self.ink(fnt, tail[-1][0], tail[-1][1])
            self.screen.blit(surf, (rect.right - 8 - surf.get_width(), y))  # right edge

    # battle scene

    def draw_battle(self):
        if self.round_num:  # round 0 = the fight's over (Happy's scenes after the tavern fight): no round counter
            self.blit_text(f'Round {self.round_num}', (24, 16), 'round', GOLD)
        self.sprite_rects = []
        self.draw_party_row(self.party, top=78)  # room for a Cleric halo under the Round heading
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
            self.draw_sprite(heroine, rect, heroine.hero_class, POISON_BOX if poisoned(heroine) else HERO_BOX)
            self.draw_health_bar(heroine, rect, slot_w - 12)
            self.sprite_rects.append((rect, heroine))

    def mob_label(self, mob):
        return getattr(mob, 'label', mob.mob_class) + (' (enraged)' if mob.enraged else '')

    def draw_mobs(self):
        bosses = [m for m in self.mobs if getattr(m, 'is_boss', False)]
        others = [m for m in self.mobs if m not in bosses]
        if not bosses and len(others) > 4:  # a big pack (the Krazy Kobolds, up to 8): two rows
            self.draw_mob_rows(others)
            return
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
            self.draw_sprite(mob, rect, self.mob_label(mob), ENRAGED_BOX if mob.enraged else MOB_BOX)
            self.draw_health_bar(mob, rect, max(w, 130))
            self.sprite_rects.append((rect, mob))
            x += w + gap

    def draw_mob_rows(self, mobs):
        """Up to 8 mobs in two rows on the right half, each box 104 x 112 with its HP bar under it."""
        w, h, gap = 104, 112, 30
        per_row = -(-len(mobs) // 2)
        for row, group in enumerate((mobs[:per_row], mobs[per_row:])):
            total = len(group) * w + (len(group) - 1) * gap
            x = 660 + (600 - total) // 2
            for mob in group:
                rect = pygame.Rect(x, 52 + row * 188, w, h)
                if getattr(mob, 'mini_boss', False):  # the pack's mini-boss: a bigger box (same feet on the floor) with a gold edge
                    rect = rect.inflate(22, 0)
                    rect.height, rect.bottom = h + 24, 52 + row * 188 + h
                    if not mob.is_dead:
                        pygame.draw.rect(self.screen, GOLD, rect.inflate(8, 8), 2, border_radius=11)
                self.draw_sprite(mob, rect, self.mob_label(mob), ENRAGED_BOX if mob.enraged else MOB_BOX)
                self.draw_health_bar(mob, rect, 130)
                self.sprite_rects.append((rect, mob))
                x += w + gap

    def draw_sprite(self, entity, rect, label, box_color):
        dead = entity.is_dead
        art_image = self.sprite_for(entity, rect.size)
        art = art_image is not None
        kind = class_key(entity)
        share = max(0.0, min(1.0, entity.health / entity.starting_health))
        status = ('in pieces' if getattr(entity, 'blown_up', False) else 'dead') if dead else None
        labels = self.box_labels(rect.size, entity.name, label, status, art)
        if not art and kind == 'shifter' and not dead:
            image = self.motion.shifter_box(rect.size, box_color, share)  # a new picture every frame (she never holds still)
            image.blit(labels, labels.get_rect(midbottom=(image.get_width() // 2, image.get_height())))
        else:
            # The box with her name on it only changes when her HP, colour or status does, so it's put together
            # once and kept, not rebuilt every frame.
            key = (id(art_image) if art else None, rect.size, box_color, dead, round(share * 100), entity.name, label, status)
            image = self.whole_boxes.get(key)
            if image is None:
                if len(self.whole_boxes) > 250:
                    self.whole_boxes.clear()
                if art:
                    image = art_image.copy()
                    if dead:
                        image.fill((90, 90, 90, 255), special_flags=pygame.BLEND_RGBA_MULT)
                else:
                    image = self.placeholder(rect.size, box_color, dead, share).copy()
                image.blit(labels, labels.get_rect(midbottom=(image.get_width() // 2, image.get_height())))  # her name inside the box, her class under it
                self.whole_boxes[key] = image
        pose = Pose() if dead else self.motion.pose(entity, kind, rect)
        if pose.sx != 1 or pose.sy != 1:
            image = pygame.transform.smoothscale(image, (max(1, round(image.get_width() * pose.sx)), max(1, round(image.get_height() * pose.sy))))
        if pose.angle:
            image = pygame.transform.rotate(image, pose.angle)
        if entity is self.active and not dead:  # whose turn it is: a gold frame that breathes a little
            glow = 150 + int(80 * math.sin(pygame.time.get_ticks() / 250))
            frame = pygame.Surface((rect.width + 16, rect.height + 16), pygame.SRCALPHA)
            pygame.draw.rect(frame, (*GOLD, glow), frame.get_rect(), 4, border_radius=12)
            self.screen.blit(frame, frame.get_rect(center=rect.center))
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
            surf = f.get('picture')
            if surf is None:  # the number with its black edge, built once per floater
                fnt = self.fonts['float']
                text = fnt.render(f['text'], True, f['color'])
                edge = fnt.render(f['text'], True, (0, 0, 0))
                surf = f['picture'] = pygame.Surface((text.get_width() + 4, text.get_height() + 4), pygame.SRCALPHA)
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
        sick = poisoned(entity)
        if sick:  # the bar keeps its colour (it still says how hurt she is); a poison-green ring goes round it
            pygame.draw.rect(self.screen, POISON_EDGE, bar.inflate(8, 8), 2, border_radius=7)
        self.blit_text(f'{int(round(entity.health))}/{entity.starting_health}', (rect.centerx, bar.bottom + 11), 'hp', POISON_EDGE if sick else DIM, center=True)

    def draw_party_lineup(self):
        self.sprite_rects = []
        self.blit_text('Your party', (24, 16), 'round', GOLD)
        self.draw_party_row(self.party, top=78)  # room for a Cleric halo under the Round heading
        self.motion.draw_effects()
        self.motion.draw_particles()


def poisoned(entity) -> bool:
    """She's carrying Kobold poison right now (Slayer_Combat keeps it in her status until it wears off or is healed)."""
    return bool(getattr(entity, 'status', None)) and bool(entity.status.get('poisoned')) and not entity.is_dead


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
        self.patches = {}    # size -> a reusable see-through scrap for the dagger, staff and arrow (see patch)
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
        if kind == 'krazy_kobolds' and entity.enraged:  # hopping mad: fast, high bounces with a jitter, and a size bigger
            return Pose(random.uniform(-1.5, 1.5), -abs(9 * math.sin(t * 9)), sx=1.08, sy=1.08)
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
        if poisoned(entity) and random.random() < dt * 5:  # sickly green bubbles drifting up off a poisoned heroine
            x = rect.x + random.uniform(0.1, 0.9) * rect.width
            self.particles.append([x, rect.bottom - 6, random.uniform(-6, 6), random.uniform(-34, -18), 0, 1.3, 3, 2, POISON_EDGE])
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
        elif kind == 'krazy_kobolds' and entity.enraged:  # little puffs of steam off an enraged Kobold
            for side in (-1, 1):
                if random.random() < dt * 2.5:
                    x = rect.centerx + side * rect.width * 0.36
                    self.particles.append([x, rect.y + 12, side * random.uniform(10, 26), random.uniform(-42, -24), 0, 1.0, 4, 8, (210, 210, 210)])
        elif kind == 'disgruntled_dwarf' and entity.enraged:  # steam venting off the top
            for side in (-1, 1):
                if random.random() < dt * 3:
                    x = rect.centerx + side * rect.width * 0.38
                    self.particles.append([x, rect.y + 30, side * random.uniform(15, 40), random.uniform(-50, -30), 0, 1.4, 7, 14, (210, 210, 210)])

    def draw_effects(self):
        for draw in self.later:
            draw()
        self.later = []

    def patch(self, area):
        """A see-through scrap just big enough for one little animation (area: where it goes on the screen), wiped
        and reused. These used to be drawn on a brand-new see-through layer the size of the whole screen, every
        frame, which is a lot of work for a tablet (Ted, Nov 11: jittery animations). Returns the scrap and where
        its top-left corner sits on the screen: take that off every point drawn on it."""
        area = pygame.Rect(area).clip(pygame.Rect(0, 0, SCREEN_W, SCREEN_H))
        size = (max(1, area.width), max(1, area.height))
        if size not in self.patches:
            self.patches[size] = pygame.Surface(size, pygame.SRCALPHA)
        surf = self.patches[size]
        surf.fill((0, 0, 0, 0))
        return surf, area.x, area.y

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
        surf, ox, oy = self.patch((tip[0] - 20, tip[1] - 125, 170, 150))  # it flies in from up and to the right of the tip
        tip = (tip[0] - ox, tip[1] - oy)
        at = lambda s, side=0.0: (tip[0] + back[0] * (s + shift) + perp[0] * (side + wobble),
                                  tip[1] + back[1] * (s + shift) + perp[1] * (side + wobble))
        if p >= fly:  # the slit where it went in
            pygame.draw.line(surf, (0, 0, 0, 170), at(8, -5), at(8, 5), 3)
        pygame.draw.polygon(surf, (205, 210, 222), [at(8, -2.5), at(8, 2.5), at(32, 4.5), at(32, -4.5)])  # blade (tip buried)
        pygame.draw.line(surf, (150, 155, 170), at(9), at(31), 1)
        pygame.draw.line(surf, (190, 150, 60), at(32, -10), at(32, 10), 5)   # crossguard
        pygame.draw.line(surf, (110, 70, 40), at(33), at(48), 7)             # grip
        pygame.draw.circle(surf, (190, 150, 60), [round(v) for v in at(51)], 5)  # pommel
        surf.set_alpha(self.fade(p))
        self.window.screen.blit(surf, (ox, oy))

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
        reach = length + 12  # the staff swings round its pivot, and the smack bursts round her name
        area = pygame.Rect(pivot[0] - reach, pivot[1] - reach, 2 * reach, 2 * reach).union(pygame.Rect(target[0] - 42, target[1] - 42, 84, 84))
        surf, ox, oy = self.patch(area)
        pivot, target = (pivot[0] - ox, pivot[1] - oy), (target[0] - ox, target[1] - oy)
        end = (pivot[0] + math.cos(angle) * length, pivot[1] + math.sin(angle) * length)
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
        self.window.screen.blit(surf, (ox, oy))

    def draw_stuck_arrow(self, rect, p):
        fly = 0.12
        bull = (rect.x + rect.width * 0.62, rect.y + rect.height * 0.84)  # low in the box, under her name and class
        start = rect.x - 90  # where the arrow flies in from
        surf, ox, oy = self.patch((start - 70, bull[1] - 24, bull[0] - start + 100, 48))
        bull, start = (bull[0] - ox, bull[1] - oy), start - ox
        for radius, color in ((15, (240, 235, 225)), (11, (200, 50, 50)), (7, (240, 235, 225)), (3, (200, 50, 50))):
            pygame.draw.circle(surf, color, [round(v) for v in bull], radius)
        if p < fly:
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
        self.window.screen.blit(surf, (ox, oy))

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
                self.window.screen.blit(self.window.ink(self.font, row, color), (x, y + i * self.cell_h))
            x += len(rows[0]) * self.cell_w

    def word_width(self, word, letters):
        return sum(len(letters[ch][0]) for ch in word) * self.cell_w

    def start_beats(self):
        self.due = pygame.time.get_ticks() / 1000

    async def beat(self, gap):
        """Wait for the next step of the animation. Each step is due a set time after the one before was DUE,
        not after it was drawn, so a device that draws slowly skips a flicker here and there but the whole
        animation lasts as long as it does on a fast PC (Nov 11: on the tablet the title took about twice as
        long). PC_LAG is what a 60-frames-a-second PC has always added to every step (about two and a half
        frames; measured Nov 11), kept so the timing on the PC stays what it was."""
        self.due += gap + self.PC_LAG
        wait = self.due - pygame.time.get_ticks() / 1000
        if wait > 0:
            await asyncio.sleep(wait)

    PC_LAG = 0.042


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
        self.start_beats()
        for top_end, colors_list in ((40, gr.colors_), (25, gr.colors_s), (27, gr.colors_sl), (31, gr.colors_sla), (27, gr.colors_slay), (25, gr.colors_slaye)):
            for _ in range(1, top_end):
                state['colors'] = random.choice(colors_list)
                await self.beat(gap)
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

        self.start_beats()
        for _ in range(1, 10):
            for version in range(6):
                jump()
                state['colors'] = gr.letter_colors_loser[version]
                await self.beat(gap)
                gap = gap / divisor
            await self.beat(gap)
            gap = gap / divisor
        jump()
        state['colors'] = gr.letter_colors_loser[6]
        await asyncio.sleep(0.75)
        window.overlay = None


class KegFlash:
    """Right before a Big Badda Boom: the whole screen goes dark, a keg of explosives slides in, its fuse
    burns down, and everything goes white. About a second and a half. (Ted could swap in his own keg art
    later; for now it's drawn with shapes.)"""

    length = 1.6

    def __init__(self, window):
        self.window = window
        self.start = window.now
        self.sparks = []  # [x, y, vx, vy, age, life]
        self.shade = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)  # one see-through colour over everything (the dark veil, the white flash)
        self.ring = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)   # the blast ring; both made once and reused, not made new every frame

    async def play(self):
        self.start = self.window.now
        self.window.effect_overlay = self.draw
        while self.window.now - self.start < self.length:
            await asyncio.sleep(0)
        self.window.effect_overlay = None

    def draw(self):
        w = self.window
        screen = w.screen
        p = min(1.0, (w.now - self.start) / self.length)
        blast = 0.78  # when the fuse reaches the keg
        self.shade.fill((8, 4, 2, int(215 * min(1.0, p / 0.12))))
        screen.blit(self.shade, (0, 0))
        if p < blast:
            slide = smooth(min(1.0, p / 0.18))
            scale = 1 + 0.14 * smooth(min(1.0, p / blast))
            shake = max(0.0, (p - 0.45) / (blast - 0.45)) * 9
            cx = -220 + (SCREEN_W // 2 + 220) * slide + random.uniform(-shake, shake)
            cy = SCREEN_H // 2 + 75 + random.uniform(-shake, shake)
            top = self.draw_keg(screen, cx, cy, 320 * scale, 400 * scale)
            burned = max(0.0, min(1.0, (p - 0.12) / (blast - 0.12)))
            self.draw_fuse(screen, cx, top, scale, burned)
        else:
            q = (p - blast) / (1 - blast)  # 0..1 through the blast
            self.ring.fill((0, 0, 0, 0))
            radius = int(60 + 900 * q)
            pygame.draw.circle(self.ring, (255, 170, 40, int(230 * (1 - q))), (SCREEN_W // 2, SCREEN_H // 2), radius, max(4, int(70 * (1 - q))))
            screen.blit(self.ring, (0, 0))
            self.shade.fill((255, 250, 235, int(255 * (1 - q) ** 1.5)))
            screen.blit(self.shade, (0, 0))
        self.draw_sparks(screen)

    def draw_keg(self, screen, cx, cy, kw, kh):
        """A wooden keg with iron hoops and a TNT plaque. Returns the y of its lid."""
        top, steps = cy - kh / 2, 24
        half = lambda t: kw / 2 * (0.80 + 0.20 * math.sin(math.pi * t))  # bulges in the middle
        left = [(cx - half(i / steps), top + kh * i / steps) for i in range(steps + 1)]
        right = [(cx + half(i / steps), top + kh * i / steps) for i in range(steps + 1)]
        body = left + right[::-1]
        pygame.draw.polygon(screen, (126, 76, 38), body)
        for k in (-0.6, -0.2, 0.2, 0.6):  # stave lines, following the bulge
            pygame.draw.lines(screen, (92, 54, 26), False, [(cx + k * half(i / steps), top + kh * i / steps) for i in range(steps + 1)], 3)
        for t in (0.1, 0.36, 0.64, 0.9):  # iron hoops
            y = top + kh * t
            pygame.draw.line(screen, (64, 64, 72), (cx - half(t) - 2, y), (cx + half(t) + 2, y), max(6, int(kh * 0.035)))
            pygame.draw.line(screen, (120, 120, 130), (cx - half(t), y - 3), (cx + half(t), y - 3), 2)
        pygame.draw.polygon(screen, (60, 34, 16), body, 4)
        lid = pygame.Rect(0, 0, half(0) * 2, kh * 0.09)
        lid.center = (cx, top)
        pygame.draw.ellipse(screen, (150, 96, 52), lid)
        pygame.draw.ellipse(screen, (60, 34, 16), lid, 3)
        plaque = pygame.Rect(0, 0, kw * 0.62, kh * 0.24)
        plaque.center = (cx, cy + kh * 0.01)
        pygame.draw.rect(screen, (236, 224, 192), plaque, border_radius=8)
        pygame.draw.rect(screen, (150, 30, 24), plaque, 4, border_radius=8)
        label = self.window.fonts['keg'].render('TNT', True, (190, 28, 22))
        screen.blit(label, label.get_rect(center=plaque.center))
        return top

    def draw_fuse(self, screen, cx, top, scale, burned):
        """The fuse curls up from the lid; it burns from its tip down toward the keg."""
        points = [(cx + 260 * scale, top - 140 * scale), (cx + 190 * scale, top - 20 * scale),
                  (cx + 30 * scale, top - 100 * scale), (cx, top - 4)]
        left = [bezier(points, burned + (1 - burned) * i / 30) for i in range(31)]
        if len(left) > 1:
            pygame.draw.lines(screen, (50, 38, 26), False, left, 7)
            pygame.draw.lines(screen, (110, 90, 60), False, left, 2)
        spark = bezier(points, burned)
        glow = 14 + 6 * math.sin(self.window.now * 40)
        pygame.draw.circle(screen, (255, 150, 30), [round(v) for v in spark], round(glow))
        pygame.draw.circle(screen, (255, 245, 180), [round(v) for v in spark], round(glow * 0.5))
        for _ in range(3):
            self.sparks.append([spark[0], spark[1], random.uniform(-220, 220), random.uniform(-260, 60), 0.0, random.uniform(0.25, 0.5)])

    def draw_sparks(self, screen):
        dt = self.window.dt
        alive = []
        for s in self.sparks:
            s[0] += s[2] * dt; s[1] += s[3] * dt; s[3] += 500 * dt; s[4] += dt
            if s[4] < s[5]:
                alive.append(s)
                fade = 1 - s[4] / s[5]
                pygame.draw.circle(screen, (255, int(160 + 90 * fade), 60), (round(s[0]), round(s[1])), max(1, round(3 * fade)))
        self.sparks = alive

