"""The Krazy Kobolds: the first fight in the dungeon. A pack of little magic-flinging gremlins that share one
pool of health.

How the pack works (Ted's design, Nov 7):
  - Each Kobold has its own health bar during a round.
  - At the end of every round, the pack's HP is added up and split evenly across ALL of them, the dead included:
    the dead pop back up with their share.  100 + 150 + 50 -> 100 each.  100 + dead + 50 -> 50 each.
  - The first time each Kobold dies, the rest of the pack enrages, from that moment through the end of the next
    round (so always at least one full round). Each Kobold can set that off once.
  - Once the pack's total HP drops below LINK_SNAP of what it started with, the link snaps: no more sharing and no
    more coming back. The dead stay dead, the living keep the HP they have, and the party chops them down.
Their attacks are in mob_equipment.csv (Claws, Bite, Spark Flick, Gas Release, Junk Attack, Terrifying Hiss,
Blink Stab, and a Glowy Mushroom to heal); the special ones work through Slayer_Combat.MOB_EFFECTS.
"""
import random
import Slayer_Accessory as acc
from Slayer_UI import say, pause

PACK_EXTRA, PACK_MIN, PACK_MAX = 2, 4, 8 # the party's size + 2 Kobolds, never fewer than 4 or more than 8 (8 fill the screen)
LINK_SNAP = 0.35 # the link snaps once the pack is down to this share of its starting HP (0.35 = 35%)

# Ted: rename these freely (the game picks one per Kobold, no repeats, so keep at least 8).
KOBOLD_NAMES = ['Snik', 'Grizzik', 'Tazzle', 'Pib', 'Skritch', 'Nibbles', 'Kekk', 'Zib', 'Twitch', 'Yipyip', 'Squee', 'Krinkle']

mobs_table = acc.get_mobs()


def pack_size(party_size : int) -> int:
    return max(PACK_MIN, min(PACK_MAX, party_size + PACK_EXTRA))

def names_list(kobolds : list) -> str:
    """'Snik', 'Snik and Pib', 'Snik, Pib and Kekk'"""
    names = [k.name for k in kobolds]
    return names[0] if len(names) == 1 else ', '.join(names[:-1]) + ' and ' + names[-1]


class Pack:
    """What the Kobolds share: the link, where the round is at, and what they started with."""

    def __init__(self, members : list):
        self.members = members
        self.linked = True
        self.round = 1 # the round being fought right now (round_end moves it on)
        self.start_total = sum(k.starting_health for k in members)
        self.explained = False # the narrator explains the link the first time it does anything

    def total(self) -> int:
        return sum(k.health for k in self.members if not k.is_dead)


class Krazy_Kobold:

    def __init__(self, name : str, pack : Pack = None):
        self.name = name
        self.mob_class = 'Krazy Kobolds' # its row in mobs.csv and mob_equipment.csv
        acc.initialize_mob(self, mobs_table)
        self.label = 'Krazy Kobold' # what its box says
        self.is_boss = False
        self.has_raged = False # it's already set off the pack's rage once
        self.rage_until = 0 # enraged through the end of this round
        self.pack = pack

    async def on_death(self, mobs : list):
        """Slayer_Combat calls this when a heroine kills it: the first time, the rest of the pack goes feral."""
        if self.has_raged:
            return
        self.has_raged = True
        angry = [k for k in self.pack.members if not k.is_dead]
        if not angry:
            return
        for kobold in angry:
            kobold.enraged = True
            kobold.rage_until = self.pack.round + 1
        one = len(angry) == 1
        await say(f"[red]The rest of the pack shrieks![/]  {names_list(angry)} {'goes' if one else 'go'} absolutely feral.  [narr]Oh, you pissed them off now.[/]")


def make_pack(party_size : int) -> list:
    kobolds = [Krazy_Kobold(name) for name in random.sample(KOBOLD_NAMES, pack_size(party_size))]
    pack = Pack(kobolds)
    for kobold in kobolds:
        kobold.pack = pack
    return kobolds


async def round_end(party_dict : dict, mobs : list, round_num : int):
    """Slayer_Game_Play calls this after every round of the Kobold fight that didn't end it: the rage wears off,
    then the pack shares out its HP and the dead come back, or the link snaps."""
    pack = mobs[0].pack
    pack.round = round_num + 1
    said = False
    calmed = [k for k in pack.members if k.enraged and not k.is_dead and k.rage_until <= round_num]
    for kobold in pack.members:
        if kobold.enraged and kobold.rage_until <= round_num:
            kobold.enraged = False
    if calmed:
        await say(f"{names_list(calmed)} {'calms' if len(calmed) == 1 else 'calm'} down.  A little.")
        said = True
    if pack.linked:
        total = pack.total()
        share, extra = divmod(total, len(pack.members))
        if total < LINK_SNAP * pack.start_total or share < 1:
            pack.linked = False
            dead = [k for k in pack.members if k.is_dead]
            await say("The purple flicker in the Kobolds' eyes sputters... and goes out.  They look at each other, panicking.")
            await say("[narr]The link is broken!  No more sharing, no more popping back up." + (f"  {names_list(dead)} {'stays' if len(dead) == 1 else 'stay'} dead." if dead else "") + "  Chop 'em down![/]")
            said = True
        else:
            revived = [k for k in pack.members if k.is_dead]
            for spot, kobold in enumerate(pack.members):
                kobold.health = share + (1 if spot < extra else 0) # the odd leftover point or two goes to the first ones
                if kobold.is_dead:
                    kobold.is_dead, kobold.enraged, kobold.rage_until = False, False, 0
            if not pack.explained:
                pack.explained = True
                await say("[narr]Wait.  Are their wounds... spreading out?  These little shits SHARE their health!  Hurt one, you hurt them all.  Kill one, and it just pops back up at the end of the round.[/]")
                await say("[narr]Wear the whole pack down.  Something's gotta give eventually.[/]")
            await say(f"The Kobolds' eyes flicker purple as their wounds even out: about {share} hp each.")
            if revived:
                await say(f"{names_list(revived)} {'twitches, sits up and giggles' if len(revived) == 1 else 'twitch, sit up and giggle'}.  [narr]Oh, come ON.[/]")
            said = True
    if said:
        await pause()
