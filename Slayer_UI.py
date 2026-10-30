"""Slayer_UI: the one place the game talks to the player.

Game code never calls print(), input(), pause(), cls() or time.sleep() directly.
It calls these instead, and every one of them is awaited:

    await ui.say("Muffy slams Gassy for 8 hp.")       # print a line
    await ui.wait(0.5)                                 # dramatic pause (was time.sleep)
    await ui.pause()                                   # wait for Enter / a click
    await ui.clear()                                   # clear the screen (was cls)
    index = await ui.choose(prompt, labels, oops)      # pick from a numbered list
    target = await ui.choose_target(prompt, party, mobs, oops)
    answer = await ui.yes_no(prompt)                   # True / False
    text = await ui.ask_text(prompt)                   # free typing (names, numbers)
    await ui.show_battle(party, mobs, round_num)       # the round status screen
    await ui.show_party(party)                         # the party lineup
    await ui.title_screen()                            # the SLAYER opening
    await ui.loser_banner()                            # the LOSER banner

say(), choose() and choose_target() take one line or a list of lines for the
text, prompt and oops; with a list, one line is picked at random each time.

Colors go inside the text as tags, so no colorama codes end up in game code:
    await ui.say("You're not on [red]The List[/].")
Tags: [red], [magenta], [green], [white], and [/] to go back to normal.

Which screen all of this lands on is picked once, at startup:
    ui.use(ui.TerminalUI())    # the command-prompt game
    ui.use(WindowUI())         # the Pygame window (coming later)
"""
import asyncio
import random
import re

_backend = None  # set by use(); every call below hands off to it


def use(backend):
    global _backend
    _backend = backend


# ---------- the calls the game makes ------------------------------------------

async def say(text=''):
    await _backend.say(_pick(text))

async def wait(seconds: float):
    await _backend.wait(seconds)

async def pause():
    await _backend.pause()

async def clear():
    await _backend.clear()

async def choose(prompt, labels: list, oops=None) -> int:
    """Show a numbered list and return the 0-based index of the pick.
    oops is shown after a bad pick."""
    return await _backend.choose(prompt, labels, _or_default(oops))

async def choose_target(prompt, party: list, mobs: list, oops=None) -> object:
    """Pick one combatant. party and mobs are the living choices on each side."""
    return await _backend.choose_target(prompt, party, mobs, _or_default(oops))

async def yes_no(prompt: str) -> bool:
    return await _backend.yes_no(prompt)

async def ask_text(prompt: str) -> str:
    return await _backend.ask_text(prompt)

async def show_battle(party: list, mobs: list, round_num: int):
    await _backend.show_battle(party, mobs, round_num)

async def show_party(party: list):
    await _backend.show_party(party)

async def title_screen():
    await _backend.title_screen()

async def loser_banner():
    await _backend.loser_banner()


def _or_default(oops):
    if oops is None:
        return "Let's try that again.  One of the listed numbers, please.  "
    return oops

def _pick(lines) -> str:
    """A string is used as-is; a list gets a random.choice, exactly like the old
    code did, so seeded test runs match the print()/input() version roll for roll."""
    if isinstance(lines, str):
        return lines
    return random.choice(lines)


# ---------- terminal backend: the command-prompt game -------------------------

class TerminalUI:
    """Plays in the Windows terminal, exactly like the game did before Slayer_UI."""

    yes = ['YES', 'Y']
    no = ['NO', 'N']

    def __init__(self):
        from colorama import init, Fore, Style
        init()
        self.Fore = Fore
        self.Style = Style
        self.colors = {
            'red': Fore.RED + Style.BRIGHT,
            'magenta': Fore.MAGENTA,
            'green': Fore.GREEN + Style.BRIGHT,
            'white': Fore.WHITE + Style.BRIGHT,
            '/': Style.RESET_ALL,
        }

    def paint(self, text: str) -> str:
        """Turn [red]...[/] tags into terminal color codes."""
        return re.sub(r'\[(red|magenta|green|white|/)\]', lambda m: self.colors[m.group(1)], text)

    async def say(self, text=''):
        print(self.paint(text))

    async def wait(self, seconds):
        await asyncio.sleep(seconds)

    async def pause(self):
        from msvcrt import kbhit, getch  # Windows-only, so it's only imported here
        while True:
            if kbhit() and ord(getch()) == 13:  # 13 = Enter
                print()
                return
            await asyncio.sleep(0.02)  # keeps the CPU from spinning while it waits

    async def clear(self):
        from colorama.winterm import WinTerm
        WinTerm().erase_screen(mode=2)
        print()
        print()

    async def choose(self, prompt, labels, oops):
        for number, label in enumerate(labels, start=1):
            print(self.paint(f'{number}:  {label}'))
        return await self._read_number(prompt, len(labels), oops) - 1

    async def choose_target(self, prompt, party, mobs, oops):
        targets = party + mobs
        if party:
            print('\nParty Members:')
            for number, heroine in enumerate(party, start=1):
                print(f'{number}: {heroine.name}')
        if mobs:
            print('\nMobs:')
            for number, mob in enumerate(mobs, start=len(party) + 1):
                print(f'{number}: {mob.name}')
        return targets[await self._read_number(prompt, len(targets), oops) - 1]

    async def _read_number(self, prompt, count, oops) -> int:
        valid = [str(n) for n in range(1, count + 1)]
        answer = input(self.paint(_pick(prompt)))
        while answer not in valid:
            print(self.paint(_pick(oops)))
            answer = input(self.paint(_pick(prompt)))
        return int(answer)

    async def yes_no(self, prompt):
        response = input(self.paint(prompt)).strip().upper()
        while response not in self.yes and response not in self.no:
            response = input("Let's pretend you didn't type that and try again.  Yes or No?:  ").strip().upper()
        return response in self.yes

    async def ask_text(self, prompt):
        return input(self.paint(prompt))

    # Status screens. These are the old show_current_status / display_party_summary
    # / format_health from Slayer_Combat, moved here because they're screen layout:
    # the window version draws sprites and HP bars instead.

    def health_text(self, entity) -> str:
        health = int(round(entity.health, 0))
        if entity.health <= entity.starting_health * 0.1:
            return f"{self.Fore.RED}{health}{self.Style.RESET_ALL}/{entity.starting_health}"
        elif entity.health <= entity.starting_health * 0.5:
            return f"{self.Fore.MAGENTA}{health}{self.Style.RESET_ALL}/{entity.starting_health}"
        return f"{health}/{entity.starting_health}"

    async def show_party(self, party):
        print()
        for heroine in party:
            print(f"{heroine.name}:  {heroine.hero_class}, {self.health_text(heroine)}")

    async def show_battle(self, party, mobs, round_num):
        await self.clear()
        print(f'Round:{round_num}\n\n')
        print('Enemy')
        for mob in mobs:
            print()
            print(f"Name: {mob.name}")
            print(f"Class: {mob.mob_class}")
            print(f"Current Health: {self.health_text(mob)}")
        print()
        print('Party')
        await self.show_party(party)

    # The ASCII art openings live in Slayer_Graphics and stay terminal-only.

    async def title_screen(self):
        import Slayer_Graphics
        Slayer_Graphics.slayer_opening()

    async def loser_banner(self):
        import Slayer_Graphics
        Slayer_Graphics.loser_banner()
