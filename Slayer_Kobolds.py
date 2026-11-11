"""The Krazy Kobolds: the first fight in the dungeon. A pack of little magic-flinging gremlins that share one
pool of health.

How the pack works (Ted's design, Nov 7):
  - Each Kobold has its own health bar during a round.
  - At the end of every round, the pack's HP is added up and split evenly across ALL of them, the dead included:
    the dead pop back up with their share.  100 + 150 + 50 -> 100 each.  100 + dead + 50 -> 50 each.
  - The first time each Kobold dies, the rest of the pack enrages for the rest of that round (Ted, Nov 8). If the
    death was the last turn of the round, the whole pack (the revived one too) starts the next round enraged
    instead, and calms down after it. Each Kobold can set that off once. Once the link has snapped, rage never
    wears off.
  - Once the pack's total HP drops below LINK_SNAP of what it started with, the link snaps: no more sharing and no
    more coming back. The dead stay dead, the living keep the HP they have, and the party chops them down.
  - Big Badda Boom can't kill a linked Kobold (Ted, Nov 10): every one still standing that the blast would have
    killed is left on 1 hp, and the link burns out for good (Pack.shield). Any that were already dead stay dead,
    and the survivors are enraged for the rest of the fight. After the link has snapped or burnt out, a Boom
    kills them like anything else.
  - The mini-boss (Ted, Nov 10; MINI_BOSS turns him off): one Kobold in the pack is bigger. When the HP is shared
    out he gets BOSS_SHARES slices to everyone else's 1. He carries the link: kill him while it's still up and it
    snaps on the spot, with no waiting for the pack to wear down. He only stays dead if the party burns through
    his whole share inside one round, since the share-out tops him back up.
Their attacks are in mob_equipment.csv (Claws, Bite, Spark Flick, Gas Release, Junk Attack, Terrifying Hiss,
Blink Stab, and a Glowy Mushroom to heal); the special ones work through Slayer_Combat.MOB_EFFECTS.
"""
import random
import Slayer_Accessory as acc
from Slayer_UI import say, pause

PACK_EXTRA, PACK_MIN, PACK_MAX = 2, 4, 8 # the party's size + 2 Kobolds, never fewer than 4 or more than 8 (8 fill the screen)
LINK_SNAP = 0.35 # the link snaps once the pack is down to this share of its starting HP (0.35 = 35%)

MINI_BOSS = True  # one Kobold in every pack is the mini-boss (Ted, Nov 10). False = the plain pack, as it was.
BOSS_SHARES = 2   # his slice whenever the pack's HP is shared out: 2 = twice a regular Kobold's
BOSS_LABEL = 'Kobold Shaman' # what his box says. DRAFT, like his names: Ted, rename freely.
BOSS_NAMES = ['Grand Poobah', 'Big Skab', 'Chief Gristle', 'Mother Squeak']

# How tough the Kobolds are, by party size: (HP, damage), each a multiplier. HP is starting_hp from mobs.csv
# (the HP for a party of 4) times the first number; every hit they land does the second number times its usual
# damage. Bigger parties face beefier, harder-hitting Kobolds; smaller ones scrawnier, softer ones (Ted, Nov 7:
# 8 heroines winning 95% felt too easy). Tuned by simulation so every party size wins about as often.
# Nov 10: damage went up for parties of 4, 6, 7 and 8 (it was 0.8, 0.78, 0.9, 1.15) after one Gas Release stopped
# flattening the whole front line, which had made the big-party fights easier again.
PARTY_SCALE = {1: (0.8, 0.35), 2: (0.75, 0.8), 3: (1.0, 0.82), 4: (1.1, 0.86), 5: (1.1, 0.84), 6: (1.15, 0.88), 7: (1.3, 1.0), 8: (1.4, 1.25)}

# Ted: rename these freely (the game picks one per Kobold, no repeats, so keep at least 8).
KOBOLD_NAMES = ['Snik', 'Grizzik', 'Tazzle', 'Pib', 'Skritch', 'Nibbles', 'Nipples', 'Kekk', 'Zib', 'Twitch', 'Yipyip', 'Squee', 'Krinkle']

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
        self.raging = False # a death set off the rage and it hasn't worn off yet
        self.fresh = False  # ...and that death happened during the turn going on right now
        self.acted = False  # somebody has taken a turn since that death
        self.rages = 0      # how many times the pack has gone feral (the first time gets the big line)

    def total(self) -> int:
        return sum(k.health for k in self.members if not k.is_dead)

    def boss(self):
        """The mini-boss, or None for a plain pack."""
        return next((k for k in self.members if k.mini_boss), None)

    def rage_for_good(self):
        """Everyone still standing is enraged, and without the link that never wears off."""
        for kobold in self.members:
            if not kobold.is_dead:
                kobold.enraged = True
        self.raging = True

    async def shield(self, saved : list):
        """Slayer_Combat calls this when a Big Badda Boom would have killed linked Kobolds (saved: the ones it kept
        alive, on 1 hp each). The link took the blast for them and burns out: no more sharing and no more coming
        back, so any Kobold that was already dead stays dead (Ted, Nov 10). These lines are Claude's DRAFTS."""
        self.linked = False
        dead = [k for k in self.members if k.is_dead]
        one = len(saved) == 1
        await say(f"The purple flicker in the Kobolds' eyes flares blinding white.  When the smoke clears, {names_list(saved)} {'is' if one else 'are'} somehow still on {'its' if one else 'their'} feet: scorched, smoking, and hanging on by 1 hp{'' if one else ' each'}.")
        await say("[narr]WHAT?!  These little shits are LINKED, and the link just ate the whole blast for them!  But it's fried: no more sharing health, no more popping back up." + (f"  {names_list(dead)} {'stays' if len(dead) == 1 else 'stay'} dead." if dead else "") + "  Finish them![/]")
        self.explained = True
        self.rage_for_good() # Ted, Nov 10: whoever lives through the Boom is enraged for the rest of the fight
        await say(f"[red]And now {'it is' if one else 'they are'} PISSED.  That is not wearing off.[/]")


class Krazy_Kobold:

    def __init__(self, name : str, pack : Pack = None):
        self.name = name
        self.mob_class = 'Krazy Kobolds' # its row in mobs.csv and mob_equipment.csv
        acc.initialize_mob(self, mobs_table)
        self.label = 'Krazy Kobold' # what its box says
        self.is_boss = False   # that's Happy's kind of boss (one big box); the pack's mini-boss is mini_boss
        self.mini_boss = False
        self.shares = 1        # its slice when the pack's HP is shared out (the mini-boss gets BOSS_SHARES)
        self.has_raged = False # it's already set off the pack's rage once
        self.pack = pack

    async def on_death(self, mobs : list):
        """Slayer_Combat calls this when a heroine kills it: the first time, the rest of the pack goes feral."""
        pack = self.pack
        if self.mini_boss and pack.linked:
            await self.link_dies_with_me()
        if self.has_raged:
            return
        self.has_raged = True
        angry = [k for k in pack.members if not k.is_dead]
        if not angry:
            return
        calm = [k for k in angry if not k.enraged]
        for kobold in angry:
            kobold.enraged = True
        pack.raging, pack.fresh, pack.acted = True, True, False
        if not calm:
            return # they were all enraged already: nothing new to announce (Ted, Nov 10)
        pack.rages += 1
        one = len(angry) == 1
        if pack.rages == 1:
            await say(f"[red]The rest of the pack shrieks![/]  The remaining Kobold{'' if one else 's'} {'goes' if one else 'go'} absolutely feral.  [narr]Oh, you pissed them off now.[/]")
        else:
            await say(f"[red]The remaining Kobold{'' if one else 's'} {'enrages' if one else 'enrage'} once again![/]")


    async def link_dies_with_me(self):
        """The mini-boss carried the link, and he just died with it still up: it snaps right now. No more sharing,
        no more coming back, and whatever rage follows never wears off. These lines are Claude's DRAFTS."""
        pack = self.pack
        pack.linked, pack.explained = False, True
        dead = [k for k in pack.members if k.is_dead and k is not self]
        await say(f"{self.name} hits the floor, and the purple flicker goes out of every Kobold's eyes at once.  They stare at the body.  Then at each other.")
        await say("[narr]HE was holding the link together!  No more sharing health, no more popping back up." + (f"  {names_list(dead)} {'stays' if len(dead) == 1 else 'stay'} dead too." if dead else "") + "  Chop 'em down![/]")


def after_turn(mobs : list):
    """Slayer_Game_Play calls this after every turn of the Kobold fight: it's how the pack knows whether anybody
    has acted since the last death (if nobody has by the end of the round, the rage carries over)."""
    pack = mobs[0].pack
    if pack.fresh:
        pack.fresh = False # this was the turn the death happened in
    elif pack.raging:
        pack.acted = True


def party_scale(party_size : int) -> tuple:
    """(HP multiplier, damage multiplier) for this party size (see PARTY_SCALE)."""
    return PARTY_SCALE[max(min(PARTY_SCALE), min(max(PARTY_SCALE), party_size))]

def kobold_hp(party_size : int) -> int:
    """Each Kobold's HP for this party size."""
    return max(1, round(acc.get_mob_stats('Krazy Kobolds', mobs_table)['starting_hp'] * party_scale(party_size)[0]))

def make_pack(party_size : int) -> list:
    """The pack for this party size. With MINI_BOSS on, the first Kobold is the mini-boss. The pack's total HP is
    the same either way: it's cut into one slice per Kobold plus BOSS_SHARES - 1 extra for him, so he's bigger and
    the rest are a little smaller."""
    kobolds = [Krazy_Kobold(name) for name in random.sample(KOBOLD_NAMES, pack_size(party_size))]
    total = kobold_hp(party_size) * len(kobolds)
    if MINI_BOSS:
        boss = kobolds[0]
        boss.mini_boss, boss.shares, boss.label, boss.name = True, BOSS_SHARES, BOSS_LABEL, random.choice(BOSS_NAMES)
    slice_hp = max(1, round(total / sum(k.shares for k in kobolds)))
    for kobold in kobolds:
        kobold.starting_health = kobold.health = slice_hp * kobold.shares
        kobold.damage_mult = party_scale(party_size)[1]
    pack = Pack(kobolds)
    for kobold in kobolds:
        kobold.pack = pack
    return kobolds


async def round_end(party_dict : dict, mobs : list, round_num : int):
    """Slayer_Game_Play calls this after every round of the Kobold fight that didn't end it: the pack shares out
    its HP and the dead come back (or the link snaps), and the rage wears off or carries over."""
    pack = mobs[0].pack
    pack.round = round_num + 1
    said = False
    if pack.linked:
        total = pack.total()
        share, extra = divmod(total, sum(k.shares for k in pack.members)) # one slice each; the mini-boss gets BOSS_SHARES
        if total < LINK_SNAP * pack.start_total or share < 1:
            pack.linked = False # whoever's enraged right now stays that way: rage never wears off without the link
            dead = [k for k in pack.members if k.is_dead]
            await say("The purple flicker in the Kobolds' eyes sputters... and goes out.  They look at each other, panicking.")
            await say("[narr]The link is broken!  No more sharing, no more popping back up." + (f"  {names_list(dead)} {'stays' if len(dead) == 1 else 'stay'} dead." if dead else "") + "  Chop 'em down![/]")
            if any(k.enraged and not k.is_dead for k in pack.members):
                await say("[red]And they're still pissed.  That's not wearing off now.[/]")
            said = True
        else:
            carry = pack.raging and not pack.acted # the death was the last turn of the round
            if pack.raging and not carry:
                pack.raging = False
                for kobold in pack.members:
                    kobold.enraged = False
                await say("The pack calms down.  A little.")
            revived = [k for k in pack.members if k.is_dead]
            for spot, kobold in enumerate(pack.members):
                kobold.health = share * kobold.shares + (1 if spot < extra else 0) # the odd leftover point or two goes to the first ones
                kobold.is_dead = False
                if carry:
                    kobold.enraged = True # the whole pack, the revived ones too, starts the next round enraged
            if not pack.explained:
                pack.explained = True
                await say("[narr]Wait.  Are their wounds... spreading out?  These little shits SHARE their health!  Hurt one, you hurt them all.  Kill one, and it just pops back up at the end of the round.[/]")
                await say("[narr]Wear the whole pack down.  Something's gotta give eventually.[/]")
                if pack.boss(): # DRAFT hint, so players can work out what he's for
                    await say(f"[narr]And is it me, or do {pack.boss().name}'s eyes burn brighter than the rest?  I bet that one's holding this whole little circle together.  Drop him in one round and see what happens.[/]")
            boss = pack.boss()
            await say(f"The Kobolds' eyes flicker purple as their wounds even out: about {share} hp each" + (f", and {share * boss.shares} for {boss.name}." if boss else "."))
            if revived:
                await say(f"{names_list(revived)} {'twitches, sits up and giggles' if len(revived) == 1 else 'twitch, sit up and giggle'}.  [narr]Oh, come ON.[/]")
            if carry:
                pack.fresh, pack.acted = False, False # calms down at the end of the next round, once they've all had a go
                await say("[red]Still seething, the whole pack starts the next round enraged.[/]")
            said = True
    if said:
        await pause()
