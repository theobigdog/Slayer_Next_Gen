"""The wolf pack: the second fight in the dungeon, after the Krazy Kobolds. An Alpha and his Pack Wolves.

How the pack works (Ted and Claude, Nov 12-15):
  - One Pack Wolf per heroine (never fewer than WOLVES_MIN or more than WOLVES_MAX), plus the Alpha.
  - Kill the Alpha and the fight is over: whatever wolves are left run for it. Wolves that ran drop no loot, so
    it's a gamble: go straight for him, or thin the pack first for more drops.
  - The pack protects him. Every wolf still standing gives a GUARD_EACH% chance (GUARD_MAX% at most) that a hit
    aimed at the Alpha lands on a wolf that threw itself in the way. Area attacks, poison and bleeding get through.
  - The Hunt. At the end of every other round the Alpha picks a heroine and everybody can see who; next round up
    to HUNTERS wolves go for her, whatever else is going on. That's the warning: heal her, hide her, or kill wolves.
  - They smell blood. With no Hunt on, a heroine under BLOOD of her HP draws them the same way.
  - Once half his wolves are dead the Alpha enrages (the enraged_ columns in mobs.csv), and from then on he
    calls a Hunt every round.
Their attacks are in mob_equipment.csv: Bite and Pounce for the wolves; Savage Snap, Lock Jaw, Mega Pounce (the
front line only) and a Howl (no damage; a scared heroine loses her next turn) for the Alpha.
The lines in here are Claude's DRAFTS: Ted, rewrite freely.
"""
import random
import Slayer_Accessory as acc
from Slayer_UI import say, pause

WOLVES_MIN, WOLVES_MAX = 2, 6
GUARD_EACH, GUARD_MAX = 15, 60 # % chance, per wolf standing, that a hit meant for the Alpha lands on a wolf
HUNTERS = 3   # how many wolves pile onto the hunted heroine in a round
BLOOD = 0.25  # under this share of her HP, the pack smells blood

# How tough the pack is, by party size: (the Alpha's HP, the wolves' HP, damage), each a multiplier on mobs.csv.
# Tuned by simulation so every party size has about the same chance (see the commit that added this).
PARTY_SCALE = {1: (0.45, 0.6, 0.35), 2: (0.7, 0.8, 0.5), 3: (0.85, 0.9, 0.6), 4: (1.0, 1.0, 0.6), 5: (1.1, 1.0, 0.66), 6: (1.2, 1.0, 0.65), 7: (1.35, 1.1, 0.68), 8: (1.55, 1.2, 0.7)}

# Ted: rename these freely (one per wolf, no repeats, so keep at least 6).
WOLF_NAMES = ['Mange', 'Scab', 'Drool', 'Fleabag', 'Snaggle', 'Gristle', 'Chewie', 'Ripper', 'Mutt', 'Yowler']
ALPHA_NAMES = ['Old Greymaw', 'Bonecruncher', 'Mister Fluffy', 'The Big Bad']

mobs_table = acc.get_mobs()


class Pack:
    """What the wolves share: who's who, who they're hunting, and how many have gone for her this round."""

    def __init__(self, alpha, wolves : list):
        self.alpha, self.wolves = alpha, wolves
        self.mark = None      # the heroine the Alpha picked at the end of last round
        self.hunters = 0      # wolves that have gone for the hunted heroine this round
        self.called = False   # the narrator has said so this round

    def standing(self) -> list:
        return [w for w in self.wolves if not w.is_dead]

    def prey(self, heroines : list):
        """Who the wolves pile onto right now: the marked heroine, else whoever's bleeding worst (under BLOOD)."""
        if self.mark and not self.mark.is_dead and self.mark in heroines:
            return self.mark
        weak = [h for h in heroines if h.health < BLOOD * h.starting_health]
        return min(weak, key=lambda h: h.health) if weak else None


class Pack_Wolf:

    def __init__(self, name : str):
        self.name = name
        self.mob_class = 'Pack Wolf' # its row in mobs.csv and mob_equipment.csv
        acc.initialize_mob(self, mobs_table)
        self.label = 'Pack Wolf'
        self.is_boss = self.mini_boss = False
        self.fled = False # ran off when the Alpha died: counts as out of the fight, but drops nothing
        self.pack = None

    async def pick_target(self, heroines : list, item : dict):
        """Slayer_Combat asks every time a wolf attacks one heroine: the hunted one, for the first HUNTERS wolves
        each round. None = pick as usual."""
        pack = self.pack
        prey = pack.prey(heroines)
        if not prey or pack.hunters >= HUNTERS:
            return None
        pack.hunters += 1
        if not pack.called:
            pack.called = True
            if prey is pack.mark:
                await say(f"[red]The Hunt is on![/]  The pack closes in on {prey.name}.")
            else:
                await say(f"[red]The pack smells blood.[/]  Every nose swings toward {prey.name}.")
        return prey

    async def on_death(self, mobs : list):
        """Slayer_Combat calls this when it dies: once half the wolves are down, the Alpha enrages."""
        pack = self.pack
        alpha = pack.alpha
        if alpha.is_dead or alpha.enraged or len(pack.standing()) * 2 > len(pack.wolves):
            return
        alpha.enraged = True
        shook = acc.clear_head(alpha)
        await say(f"{alpha.name} looks over what's left of his pack, throws back his head, and ROARS.  [red]{alpha.name} is enraged![/]  [narr]Oh good.  He's taking it personally.  Expect a Hunt every round now.[/]")
        if shook: # DRAFT line
            await say(f"[narr]And whatever you'd put on him?  Gone.  Rage is one hell of a hangover cure.[/]")


class Alpha_Wolf:

    def __init__(self, name : str):
        self.name = name
        self.mob_class = 'Alpha Wolf'
        acc.initialize_mob(self, mobs_table)
        self.label = 'Alpha Wolf'
        self.is_boss = False   # Happy's kind of boss gets one huge box; in a pack the big one is the mini_boss (a gold edge)
        self.mini_boss = True  # so Fungal Infection and Confusion slide off him
        self.hex_proof = True  # ...and Intoxication below rank 3, like a boss
        self.fled = False
        self.pack = None

    async def guard(self, heroine : object):
        """Slayer_Combat calls this when a heroine aims a single hit at him: returns who it actually lands on,
        him or a wolf that jumped in the way."""
        wolves = self.pack.standing()
        if not wolves or not acc.roll_percent(min(GUARD_MAX, GUARD_EACH * len(wolves))):
            return self
        wolf = random.choice(wolves)
        await say(f"{heroine.name} goes for {self.name}, but {wolf.name} hurls itself into the way!  [narr]Loyal little bastard.[/]")
        return wolf

    async def on_death(self, mobs : list):
        """The Alpha's down: the fight's over, and whoever's left runs (no loot from those)."""
        runners = self.pack.standing()
        for wolf in runners:
            wolf.is_dead, wolf.fled, wolf.label = True, True, 'Pack Wolf (ran off)'
        if runners:
            one = len(runners) == 1
            await say(f"{self.name} hits the dirt and doesn't get up.  The {'last wolf' if one else f'other {len(runners)} wolves'} {'takes' if one else 'take'} one look, {'tucks its tail' if one else 'tuck their tails'}, and {'bolts' if one else 'bolt'} into the dark.  [narr]And stay out!  ...they took their loot with them, though.[/]")


def party_scale(party_size : int) -> tuple:
    return PARTY_SCALE[max(min(PARTY_SCALE), min(max(PARTY_SCALE), party_size))]

def make_pack(party_size : int) -> list:
    """The Alpha first, then his wolves, sized for this party (see PARTY_SCALE)."""
    alpha_hp, wolf_hp, damage = party_scale(party_size)
    count = max(WOLVES_MIN, min(WOLVES_MAX, party_size))
    alpha = Alpha_Wolf(random.choice(ALPHA_NAMES))
    wolves = [Pack_Wolf(name) for name in random.sample(WOLF_NAMES, count)]
    pack = Pack(alpha, wolves)
    for mob, scale in [(alpha, alpha_hp)] + [(wolf, wolf_hp) for wolf in wolves]:
        mob.starting_health = mob.health = max(1, round(mob.starting_health * scale))
        mob.damage_mult = damage
        mob.pack = pack
    return [alpha] + wolves


async def round_end(party_dict : dict, mobs : list, round_num : int):
    """Slayer_Game_Play calls this after every round of the wolf fight that didn't end it: last round's Hunt is
    over, and (every other round, or every round once he's enraged) the Alpha picks the next one."""
    pack = mobs[0].pack
    pack.mark, pack.hunters, pack.called = None, 0, False
    for heroine in party_dict['party']:
        (getattr(heroine, 'status', None) or {}).pop('hunted', None) # the word under her box (Slayer_UI.STATUS_WORDS)
    alpha = pack.alpha
    if alpha.is_dead or not pack.standing():
        return
    if not alpha.enraged and round_num % 2 == 0:
        return
    heroines = [h for h in party_dict['party'] if not h.is_dead]
    if not heroines:
        return
    pack.mark = random.choice(heroines)
    pack.mark.status = getattr(pack.mark, 'status', None) or {}
    pack.mark.status['hunted'] = True
    await say(f"{alpha.name} lifts his muzzle, sniffs, and locks his yellow eyes on {pack.mark.name}.  The whole pack turns to look.  [narr]Uh oh.  They're coming for {pack.mark.name} next round.  Do something about that.[/]")
    await pause()
