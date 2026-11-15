import Slayer_Accessory as acc
from Slayer_UI import say, pause, choose, choose_target, yes_no, show_battle, effect
import random

# Area attacks (attack_type aoe) hit every mob. Most can be dodged and toughness halves them, like any
# attack. Big Badda Boom has its own rules (decided Nov 2): nothing dodges it, toughness only shaves off
# a little, it splashes the party too (melee heroines take more than ranged ones), and it blows the
# Sapper to bits for the rest of the dungeon run.
AOE_RULES = {
    'big_badda_boom': {
        'unavoidable': True,
        'tough_cut': 0.10,                          # a tough roll takes 10% off instead of half
        'party_share': {'melee': 0.30, 'range': 0.15},  # what the party catches, by position
        'blows_up_user': True,                      # she's out for the rest of the run
        'once_per_run': True,                       # gone from her kit until the next dungeon run
        'full_targets': None,                       # full damage to every mob, however many
        'link_shields': True,                       # a linked pack (the Krazy Kobolds) lives through it: see Pack.shield
        'full_strength': True,                      # a Junk Attack doesn't halve it (Ted, Nov 10)
    },
}
# Every other area attack (Fire Bomb, Fire Rain, Stink Pouch) does full damage to up to full_targets mobs; with
# more of them, the blast spreads thinner: each takes full_targets / (how many) of it (Ted, Nov 8: a Fire Bomb
# flattened the whole Kobold pack). 3 = a pack of 6 takes half each, 8 take 3/8.
DEFAULT_AOE = {'unavoidable': False, 'tough_cut': 0.5, 'party_share': {}, 'blows_up_user': False, 'once_per_run': False, 'full_targets': 3, 'link_shields': False, 'full_strength': False}

# ---------- item effects: the effect column in items.csv (Ted, Nov 14) ----------------
# What a heroine's item does besides, or instead of, damage:
#   poison     - Snake Bite: a hit poisons the mob POISON_CHANCE of the time, like the Kobold Bite does to her:
#                POISON_DAMAGE at the start of each of its next POISON_TURNS turns
#   bleed      - Tooth-Sharpened Dagger: a hit opens a wound that costs the mob BLEED_DAMAGE at the start of every
#                one of its turns, for the rest of the fight
#   intoxicate - Intoxication: no damage; a mob it lands on has its dodge halved for the rest of the fight. Rank 1
#                picks one mob, rank 2 gets them all (bosses shrug both off), rank 3 gets the bosses too
#   stun       - Fungal Infection: no damage; every mob it lands on loses its next turn (bosses and the pack's
#                mini-boss shrug it off)
#   confuse    - Confusion: no damage; for its next CONFUSE_TURNS turns the mob attacks or heals someone at random,
#                friend or foe (bosses and mini-bosses shrug it off)
#   hide       - Hide: no attack; her dodge is HIDE_DODGE until her next turn
#   blessing   - Blessing: whoever it's cast on gets BLESSING added to their rolls for their next attack
#   strength   - Strength: whoever it's cast on hits STRENGTH_DAMAGE harder on each of their next STRENGTH_ATTACKS attacks
# Blessing and Strength are the Cleric's, so they work on her heal roll, and (like her heals) they can be put on a mob.
HEXES = ('intoxicate', 'stun', 'confuse') # the no-damage ones aimed at mobs
BUFFS = ('blessing', 'strength')
BLEED_DAMAGE = (4, 6)      # Ted floated 5-8; it never stops, so over a 10-round fight 4-6 is already about 50 hp from one stab
HIDE_DODGE = 95
BLESSING = {'crit_chance': 40, 'hit': 25, 'expertise': 30} # "significant" (Ted): added to her stats for one attack
STRENGTH_DAMAGE, STRENGTH_ATTACKS = (5, 10), 2
CONFUSE_TURNS = 2

def hex_immune(mob : object, which : str, rank : int = 1) -> bool:
    """Who shrugs a hex off (see the list above)."""
    if which == 'intoxicate':
        return (getattr(mob, 'is_boss', False) or getattr(mob, 'hex_proof', False)) and rank < 3
    return getattr(mob, 'is_boss', False) or getattr(mob, 'mini_boss', False)

def strength_bonus(entity : object) -> int:
    """The extra damage for this attack if the Cleric's Strength is on them; uses one of its attacks up."""
    strong = status(entity).get('strong')
    if not strong:
        return 0
    strong['attacks'] -= 1
    if strong['attacks'] <= 0:
        del entity.status['strong']
    return acc.multi_roll(*STRENGTH_DAMAGE)

def can_act(mob : object) -> bool:
    """False while a mob is stunned (Fungal Infection): no bonus attacks either."""
    return not status(mob).get('stunned')

def ready_in(heroine : object, item_name : str) -> int:
    """How many more of her turns until this item has recharged (0 = ready). See the recharge column."""
    return getattr(heroine, 'cooldowns', {}).get(item_name, 0)

LAST_CLERIC_LINES = [
    "[narr]Well.... there went your only remaining healer.  This is getting tense!  I just peed a little![/]",
]

def position(heroine : object) -> str:
    """'melee' or 'range', for anything that cares where she stands (Big Badda Boom's splash).
    Warrior, Shifter, Battle Mage and Sapper are melee; Hunter, Witch and Cleric are ranged."""
    return 'range' if heroine.attack_style == 'range' else 'melee' # older saves have the Warrior as 'both': still melee

def tally(heroine : object, what : str):
    """Count something she did (or had done to her) this fight; the stat bonuses afterward lean toward it.
    what: attacks, crits, heals, hits_taken, dodges, parries, toughs, scared, lucky."""
    if not getattr(heroine, 'is_mob', True):
        heroine.fight_tally = getattr(heroine, 'fight_tally', {})
        heroine.fight_tally[what] = heroine.fight_tally.get(what, 0) + 1

def start_battle(party : list):
    """Reset what only lasts one battle: each heroine's special weapons are ready again, and her tally is empty."""
    for heroine in party:
        heroine.fight_tally = {} # what she did this fight (see tally)
        heroine.spent_specials = [] # special weapons she's already used this battle (a list, so saves can store it)
        heroine.status = {} # what the mobs did to her this fight: gassed, junked, hissed (see MOB_EFFECTS)
        heroine.wielding = None # no kit perk until she picks a forged weapon
        heroine.cooldowns = {} # items with a recharge: how many more of her turns each needs (see ready_in)
        heroine.ghost_spent = heroine.is_dead # down before the fight even started: no parting shot (see parting_shot)
        acc.sync_max_hp(heroine) # a max HP trinket counts (a safety net: picking one up already syncs)

def status(heroine : object) -> dict:
    """Her status effects this fight (older saves and test parties may not have any yet)."""
    if not hasattr(heroine, 'status'):
        heroine.status = {}
    return heroine.status

async def show_current_status(party: list, mobs: list, round_num: int, active : object = None):
    await show_battle(party, mobs, round_num, active) # the round/enemy/party layout lives in Slayer_UI; active = whose turn it is

def get_heroine_rolls(heroine: object, attacking : bool = False) -> dict:
    """attacking=True for the rolls of her own attack: a Blessing on her counts for it and is used up
    (roll_results['blessed'] says so)."""
    heroine_stats = heroine.stats
    roll_results = {}
    bless = status(heroine).pop('blessed', None) if attacking else None
    bonus = lambda stat: acc.stat_bonus(heroine, stat) + (bless.get(stat, 0) if bless else 0) # trinkets, a forged weapon's perk, a Blessing
    if acc.roll_percent(heroine_stats['crit_chance'] + bonus('crit_chance')):
        roll_results['crit_mult'] = round(heroine_stats['crit_mult'] + acc.stat_bonus(heroine, 'crit_mult'), 2)
    else:
        roll_results['crit_mult'] = 1 # if not a crit, multiplier is 1
    for stat in ['hit', 'luck', 'expertise', 'toughness', 'dodge', 'parry', 'fear']:
        roll_results[stat] = acc.roll_percent(heroine_stats[stat] + bonus(stat))
    roll_results['heal'] = acc.roll_percent(heroine_stats['heal_chance'] + acc.stat_bonus(heroine, 'heal_chance'))
    roll_results['aoe_heal'] = acc.roll_percent(heroine_stats['aoe_heal_chance'] + acc.stat_bonus(heroine, 'aoe_heal_chance'))
    roll_results['blessed'] = bool(bless)
    if status(heroine).get('hissed'):
        roll_results['dodge'] = False # the Terrifying Hiss: too rattled to dodge for the rest of the fight
    if status(heroine).get('hidden'):
        roll_results['dodge'] = acc.roll_percent(HIDE_DODGE) # Hide: you can't rattle what you can't find, so it beats the Hiss
    return roll_results

def get_mob_rolls(mob: object, attacking : bool = False) -> dict:
    """attacking=True for the rolls of its own attack: a Blessing some Cleric put on it counts, and is used up."""
    mob_stats = mob.stats
    prefix = 'enraged_' if mob.enraged else '' # an enraged mob rolls against the enraged_ columns from mobs.csv
    roll_results = {}
    bless = status(mob).pop('blessed', None) if attacking else None
    bonus = lambda stat: bless.get(stat, 0) if bless else 0
    if acc.roll_percent(mob_stats[prefix + 'crit_chance'] + bonus('crit_chance')):
        roll_results['crit_mult'] = mob_stats[prefix + 'crit_mult']
    else:
        roll_results['crit_mult'] = 1
    for stat in ['hit', 'luck', 'expertise', 'toughness', 'dodge']:
        roll_results[stat] = acc.roll_percent(mob_stats[prefix + stat] + bonus(stat))
    if status(mob).get('intoxicated'):
        roll_results['dodge'] = acc.roll_percent(mob_stats[prefix + 'dodge'] / 2) # Intoxication: half its dodge
    roll_results['heal'] = acc.roll_percent(mob_stats[prefix + 'heal_chance'])
    roll_results['scare'] = acc.roll_percent(mob_stats[prefix + 'scare'])
    return roll_results

def update_health(to_update : object, delta : int) -> object:
    new_health = to_update.health - delta
    if new_health > to_update.starting_health:
        to_update.health = to_update.starting_health
    elif new_health > 0:
        to_update.health = new_health
    else:
        to_update.health = 0
        to_update.is_dead = True
    return to_update

async def check_tough(tough : bool, target : object) -> None:
    if tough and not target.is_mob:
        await say(f"{target.name}, being the bad mother fucker she is, shrugs off half the damage.  [narr]Hell yeah![/]")
    elif tough and target.is_mob:
        await say(f"Damn... {target.name} is one tough piece-of-shit.  They absorbed HALF the damage!")

async def check_last_cleric(fallen : list, party : list):
    """If the party just lost its last Cleric (and anyone's still standing), the narrator panics."""
    clerics_fell = any(x.hero_class == 'Cleric' for x in fallen)
    clerics_left = any(x.hero_class == 'Cleric' and not x.is_dead for x in party)
    if clerics_fell and not clerics_left and any(not x.is_dead for x in party):
        await say('') # a blank line first, so it stands out (Ted, Nov 8)
        await say(LAST_CLERIC_LINES)

def item_label(item_name : str, heroine : object = None) -> str: # one line of the item menu (forged gear by its forged name)
    return acc.describe_item(acc.held_item(heroine, item_name), acc.uses_left(heroine, item_name) if heroine else None)

async def get_target_choice(mobs : list, party : list, healing : bool = False, prompt : str = None) -> object:
    """prompt: its own question instead of the usual ones (Blessing and Strength ask 'Who gets the ...?')."""
    living_party = [x for x in party if not x.is_dead]
    living_mobs = [x for x in mobs if not x.is_dead]
    living_targets = living_party + living_mobs
    if len(living_targets) == 1:
        return living_targets[0]
    if prompt:
        return await choose_target(prompt, living_party, living_mobs, "\nOne of THOSE numbers, please:  ")
    if healing:
        prompts = [
            "Choose whoever needs a little TLC.  ",
            "Who gets the healing love this time?  ",
        ]
        oopses = [
            "\nNo, no, one of THOSE numbers.  Somebody's bleeding over here, hurry up:  "
        ]
    else:
        prompts = [
            "Choose your target.  [narr]Make 'em regret it.[/]  ",
        ]
        oopses = [
            "\nWhoa, no, one of THOSE numbers.  Choose the one belonging to whoever you'd like to fuck up:  ",
        ]
    return await choose_target(prompts, living_party, living_mobs, oopses) # lists the targets, keeps asking until the pick is valid

async def get_heal_outcome(heroine : object, item : dict, target : object, party_dict : dict, mobs : list, heroine_rolls : dict, heal_w_crit_mult : float) -> tuple:
    """Every heal, whoever it's aimed at. The amount uses the healer's own class crit
    multiplier (no flat doubling) and never goes past the target's max HP."""
    tally(heroine, 'heals')
    healing = -int(heal_w_crit_mult) # heal items have negative damage numbers, so flip the sign
    missing_hp = target.starting_health - target.health
    if healing > missing_hp:
        healing = missing_hp

    if target.is_mob:
        # Later: undead go here (the Cleric's heals hurt them; anyone else's heal is a lost turn).
        if target.health == target.starting_health:
            await say(f"[narr]That was weird.  {target.name} is your enemy and is at full health anyway, goof.  Oh well, better luck choosing a target next time?[/]")
            await pause()
            return (party_dict, mobs, False)
        target = update_health(target, -healing) # a heal on a mob never fails: picking the target was the mistake
        if heroine.hero_class == 'Cleric': # she's a professional, she should know better
            await say([
                f"{heroine.name} successfully heals {target.name} for +{healing} hp.  [narr]What in the flying-fuck were you thinking?  Are you trying to give me gas?[/]",
                f"{heroine.name} swells with pride as she successfully heals {target.name} for +{healing} hp.  [narr]Pride eh?  Well.... Good Job??[/]",
                f"{target.name} grins wickedly at {heroine.name} as their wounds begin to bind.  \"Thank you!\" {target.name} screams in your face, spraying you with spittle.  [narr]Did you expect that to go a different way or something?[/]",
                f"{heroine.name} lays her holy hands on {target.name} for +{healing} hp.  [narr]Somewhere up there, a god just facepalmed so hard it echoed.[/]",
                f"[narr]Ah yes, the classic \"heal the guy who's trying to murder us\" strategy.[/]  {heroine.name} patches up {target.name} for +{healing} hp.  [narr]Bold.  Stupid, but bold.[/]",
            ])
        else:
            await say(f"{heroine.name} takes it upon herself to use her {item['item_desc']} to heal {target.name} for +{healing} hp")
            await say("[narr]I swear I'm on your side here, but what was she thinking?  I guess she wanted more of a challenge?[/]")
        await pause()
        if hasattr(target, 'healed_by'): # some mobs have something to say about it (Happy does)
            await target.healed_by(heroine)
        return (party_dict, mobs, False) # healing a mob never earns the luck roll

    if not heroine_rolls['heal'] and not item['uses']: # potions and the like always work: you just drink them
        await say(f"{heroine.name} tries to heal {'herself' if heroine == target else target.name}, but does a piss-poor job and just ends up wasting her turn.  [narr]Doh![/]")
        await pause()
        return (party_dict, mobs, False)
    if target.health == target.starting_health:
        if acc.slot_kind(item) == 'potion': # she drank it herself, so there was no target to get wrong (DRAFT line)
            await say(f"[narr]That was weird.  {target.name} is at full health, goof.  That's a perfectly good dose down the hatch for nothing.[/]")
        else:
            await say(f"[narr]That was weird.  {target.name} is at full health, goof.  Oh well, better luck choosing a target next time?[/]")
        await pause()
        return (party_dict, mobs, heroine_rolls['luck'])
    if status(heroine).pop('junked', False): # a Junk Attack halves her next heal too (Ted, Nov 8)
        healing = max(1, healing // 2)
        await say(f"[narr]{heroine.name}'s junk still hurts, so it's a half-strength heal.[/]")
    target = update_health(target, -healing)
    await cleanse(target, item)
    if acc.slot_kind(item) == 'potion':
        await say(f"{heroine.name} knocks back her {item['item_desc']} and heals herself for +{healing} hp")
    else:
        await say(f"{heroine.name} quickly uses {item['item_desc']} to heal {'herself' if heroine == target else target.name} for +{healing} hp")
    await say("[narr]I'm so proud of you![/]")
    await pause()
    return (party_dict, mobs, heroine_rolls['luck'])

def spend_token(item : dict, party_dict : dict):
    """One Token per dungeon run for the whole party: once anyone uses one, they all go quiet."""
    for member in party_dict['party']:
        if item['item'] in member.inv:
            member.inv.remove(item['item'])
    party_dict['token_used'] = True

MAGIC_CHANCE = 0.25 # how often a normal Token revive gets the Your Highness line (a revived Sapper always does)

async def magic_motherfucker(revived : object, party : list):
    """Ted's Easter egg: somebody can't believe it, somebody else explains."""
    others = [x for x in party if not x.is_dead and x is not revived]
    if not others:
        return
    if len(others) >= 2:
        asker, answerer = random.sample(others, 2)
    else:
        asker, answerer = others[0], revived # only one other heroine up: the revived one answers herself
    await say(f"{asker.name} stares at {revived.name} in total disbelief.  \"But... how?\"")
    await say(f"{answerer.name} just shrugs.  \"Magic.... MotherFucker!!\"")

async def token_roll(heroine : object, item : dict, chosen : object, party_dict : dict, blown_up_waiting : bool = False):
    """The gamble itself: 30% the chosen heroine comes back at half her max HP, 30% the Token takes
    the heroine using it instead, 40% it fizzles."""
    roll = acc.multi_roll(1, 100)
    if roll <= 30:
        if chosen:
            was_in_pieces = getattr(chosen, 'blown_up', False)
            chosen.is_dead = False
            chosen.blown_up = False # even a Sapper in a billion pieces.  Because magic.
            chosen.health = max(1, round(chosen.starting_health * 0.5))
            await say(f"{heroine.name} raises the {item['item_desc']} and mutters something she definitely made up on the spot.  It WORKS.  {chosen.name} gasps back to life (+{chosen.health} hp).  [narr]Holy shit![/]")
            if was_in_pieces or random.random() < MAGIC_CHANCE:
                await magic_motherfucker(chosen, party_dict['party'])
        elif blown_up_waiting:
            await say(f"The {item['item_desc']} glows a lovely, life-giving green...  and finds nothing in one piece to bring back.  [narr]A Sapper in a billion bits is a between-battles job, sweetie.[/]")
        else:
            await say(f"The {item['item_desc']} glows a lovely, life-giving green...  and finds nobody dead to bring back.  It sulks.  [narr]Wasted turn, but hey, everybody's alive.[/]")
    elif roll <= 60:
        heroine.health = 0
        heroine.is_dead = True
        await say(f"The {item['item_desc']} flares a sickly purple.  Turns out the Wise Witch wanted payment, and {heroine.name} just covered it.  With her life.  [narr]Oof.[/]")
        await check_last_cleric([heroine], party_dict['party'])
    else:
        await say(f"{heroine.name} shakes the {item['item_desc']} like a broken snow globe.  It fizzles.  Nothing happens.  [narr]Pfft.[/]")

async def use_hail_mary(heroine : object, item : dict, party_dict : dict, mobs : list) -> tuple:
    """The Token of the Wise Witch in the middle of a fight. It can reach any fallen heroine except
    a Sapper who blew herself up (that only works between battles, see token_between_battles)."""
    spend_token(item, party_dict)
    fallen = [x for x in party_dict['party'] if x.is_dead and not getattr(x, 'blown_up', False)]
    chosen = None
    if len(fallen) == 1:
        chosen = fallen[0]
    elif fallen:
        chosen = await choose_target(
            f"\nThe Token hums in {heroine.name}'s hand.  Choose the fallen heroine you're gambling on.  ",
            fallen, [], "\nOne of THOSE numbers.  The dead are waiting, and frankly so am I:  ")
    blown_up = any(getattr(x, 'blown_up', False) for x in party_dict['party'])
    await token_roll(heroine, item, chosen, party_dict, blown_up)
    await pause()
    return (party_dict, mobs, False)

async def token_between_battles(party_dict : dict) -> dict:
    """Between battles, the party can gamble its Token on anyone who's down, a blown-up Sapper included.
    Same odds and same risks as in a fight. (Hook this in between fights once the dungeon has more than one.)"""
    if party_dict.get('token_used'):
        return party_dict
    fallen = [x for x in party_dict['party'] if x.is_dead]
    holders = [x for x in party_dict['party'] if not x.is_dead and 'token_of_the_wise_witch' in x.inv]
    if not fallen or not holders:
        return party_dict
    names = ', '.join(x.name for x in fallen)
    if not await yes_no(f"{names} {'is' if len(fallen) == 1 else 'are'} still down.  Gamble the Token of the Wise Witch on bringing someone back?  "):
        return party_dict
    user = holders[0] if len(holders) == 1 else await choose_target(
        "\nWho's holding the Token for this one?  ", holders, [], "\nOne of THOSE numbers, please:  ")
    chosen = fallen[0] if len(fallen) == 1 else await choose_target(
        f"\nThe Token hums in {user.name}'s hand.  Choose the fallen heroine you're gambling on.  ",
        fallen, [], "\nOne of THOSE numbers.  The dead are waiting, and frankly so am I:  ")
    item = acc.get_item('token_of_the_wise_witch')
    spend_token(item, party_dict)
    await token_roll(user, item, chosen, party_dict)
    await pause()
    return party_dict

async def heroine_aoe(heroine : object, item : dict, party_dict : dict, mobs : list, heroine_rolls : dict) -> tuple:
    """An area attack from a heroine: it hits every mob still standing (see AOE_RULES for Big Badda Boom's extras)."""
    rules = {**DEFAULT_AOE, **AOE_RULES.get(item['item'], {})}
    party = party_dict['party']
    crit = heroine_rolls['crit_mult'] # one crit for the whole blast; the damage itself is rolled for each target
    junked = status(heroine).get('junked', False) and not rules['full_strength'] # a Junk Attack halves this whole blast (used up once it lands)
    standing = len([m for m in mobs if not m.is_dead])
    spread = min(1, rules['full_targets'] / standing) if rules['full_targets'] and standing else 1
    roll = lambda: acc.multi_roll(item['damage_low'], item['damage_high']) * crit * (0.5 if junked else 1)
    strong = strength_bonus(heroine) # the Cleric's Strength: one of its attacks, added to what each mob takes
    mob_roll = lambda: (roll() + strong) * spread
    tally(heroine, 'attacks')
    if heroine_rolls['crit_mult'] > 1:
        tally(heroine, 'crits')
    if rules['once_per_run'] and item['item'] in heroine.inv:
        heroine.inv.remove(item['item']) # back in her kit next dungeon run
    if rules['blows_up_user']:
        await say(f"{heroine.name} lights the fuse on her {item['item_desc']}, grins, and does NOT run.  [narr]Oh no.  Oh no no no.[/]")
        await effect('boom') # the keg flashes across the screen
        await say("[red]BIG.  BADDA.  BOOOOOOM!!![/]" if heroine_rolls['crit_mult'] > 1 else "[red]BIG.  BADDA.  BOOM!!![/]")
    else:
        await say(f"{heroine.name} unleashes her {item['item_desc']} on every enemy in sight!")
        if not heroine_rolls['hit']:
            await say(f"[narr]...and somehow misses every single one of them.  That's almost impressive.[/]")
            await pause()
            return (party_dict, mobs, False)
    if junked:
        del heroine.status['junked']
        await say(f"[narr]Her junk still hurts, so it's a half-strength blast.[/]")
    if strong:
        await say("[narr]The Cleric's Strength is behind this one.[/]")
    if spread < 1 and not item['special']: # Fire Rain (a special) just rains; no need to say it (Ted, Nov 8)
        await say(f"[narr]Spread across all {standing} of them, it's thinner on each one.[/]")
    killed, shielded = [], []
    for mob in [m for m in mobs if not m.is_dead]:
        mob_rolls = get_mob_rolls(mob)
        if not rules['unavoidable'] and mob_rolls['dodge'] and not heroine_rolls['expertise']:
            await say(f"  {mob.name} dives out of the way!")
            continue
        power = mob_roll()
        damage = power * (1 - rules['tough_cut']) if mob_rolls['toughness'] else power
        damage = int(min(damage, mob.health))
        pack = getattr(mob, 'pack', None)
        if rules['link_shields'] and pack and getattr(pack, 'linked', False) and damage >= mob.health: # only the Kobolds' pack has a link (the wolves' doesn't)
            damage = mob.health - 1 # the Kobolds' life-link won't let the blast kill anyone still standing (Ted, Nov 10)
            shielded.append(mob)
        update_health(mob, damage)
        if mob.is_dead:
            killed.append(mob)
        if mob in shielded:
            await say(f"  {mob.name} gets hit for -{damage} hp and is...  still standing?!")
        elif mob.is_dead and not getattr(mob, 'is_boss', False):
            await say(f"  {mob.name} gets hit for -{damage} hp and is {'blown to bits' if rules['blows_up_user'] else 'done for'}!")
        else:
            await say(f"  {mob.name} gets hit for -{damage} hp.")
    fallen = []
    for member in [x for x in party if not x.is_dead and x is not heroine]:
        share = rules['party_share'].get(position(member), 0)
        if not share:
            continue
        damage = roll() * share
        if get_heroine_rolls(member)['toughness']:
            damage *= 1 - rules['tough_cut']
        damage = int(min(damage, member.health))
        update_health(member, damage)
        if member.is_dead:
            fallen.append(member)
            await say(f"  {member.name} gets hit for -{damage} hp.  [red]slain[/]")
        else:
            await say(f"  {member.name} gets hit for -{damage} hp.")
    if rules['blows_up_user']:
        heroine.health, heroine.is_dead, heroine.blown_up = 0, True, True # out for the rest of this dungeon run
        fallen.append(heroine)
        await say(f"And {heroine.name}?  Blown into a billion little pieces.  [narr]Even the Cleric can't help her without some serious smelling salts.[/]")
    await check_last_cleric(fallen, party)
    if shielded:
        await shielded[0].pack.shield(shielded) # the link took the blast for them, and it's burnt out for good
    for mob in killed:
        if hasattr(mob, 'on_death'): # the Krazy Kobolds' pack enrages
            await mob.on_death(mobs)
    for mob in mobs:
        if mob.mob_class == 'Disgruntled Dwarf' and mob.enraged and mob.is_dead:
            party_dict = acc.wipe_party(party_dict) # killing enraged Happy wipes the party anyway
            return (party_dict, mobs, False)
        if mob.mob_class == 'Disgruntled Dwarf' and mob.health < 0.5 * mob.starting_health and not mob.enraged:
            await mob.enrage()
            await pause()
            return (party_dict, mobs, False)
    await pause()
    return (party_dict, mobs, heroine_rolls['luck'])


async def cleanse(heroine : object, item : dict):
    """A healer's heal burns out Kobold poison (Ted, Nov 8). A potion doesn't: anything with uses is one."""
    if not item['uses'] and status(heroine).pop('poisoned', None):
        await say(f"  [green]...and it burns the poison right out of {heroine.name}, too.[/]")

async def heroine_aoe_heal(heroine : object, item : dict, party_dict : dict, mobs : list, heroine_rolls : dict) -> tuple:
    """An area heal (attack_type aoe_heal): everyone still standing in the party gets patched up, each amount
    rolled on its own, one crit for the lot. A consumable always works (you just pop it); anything else needs her
    group-heal roll (aoe_heal_chance). A Junk Attack halves it, like any heal."""
    party = party_dict['party']
    tally(heroine, 'heals')
    if not heroine_rolls['aoe_heal'] and not item['uses']:
        await say(f"{heroine.name} tries to heal the whole party with her {item['item_desc']}, but it fizzles out.  [narr]Doh![/]")
        await pause()
        return (party_dict, mobs, False)
    junked = status(heroine).pop('junked', False)
    await say(f"{heroine.name} uses her {item['item_desc']} on the whole party!")
    if junked:
        await say(f"[narr]Her junk still hurts, so it's a half-strength heal.[/]")
    helped = 0
    for member in [x for x in party if not x.is_dead]:
        amount = int(-acc.multi_roll(item['damage_low'], item['damage_high']) * heroine_rolls['crit_mult'] * (0.5 if junked else 1))
        amount = min(max(1, amount), member.starting_health - member.health)
        if amount <= 0:
            continue
        update_health(member, -amount)
        helped += 1
        await say(f"  {member.name} +{amount} hp")
        await cleanse(member, item)
    if not helped:
        await say("[narr]Nobody even needed it.  Very generous of you.[/]")
    await pause()
    return (party_dict, mobs, heroine_rolls['luck'])

async def heroine_hide(heroine : object, item : dict, party_dict : dict, mobs : list) -> tuple:
    """Hide (Ted, Nov 14): no attack this turn; her dodge is HIDE_DODGE until her next turn starts. DRAFT line."""
    status(heroine)['hidden'] = True
    await say(f"{heroine.name} drops out of sight.  She'll be nearly impossible to hit until her next turn.  [narr]Where'd she go?  No, seriously, where?[/]")
    await pause()
    return (party_dict, mobs, False)

async def heroine_buff(heroine : object, item : dict, party_dict : dict, mobs : list) -> tuple:
    """Blessing and Strength: no healing and no damage, just a boost for whoever she picks (see the effect list
    at the top). They work on her heal roll; on a mob they never fail, like a heal on one. DRAFT lines."""
    which = item['effect']
    target = await get_target_choice(mobs, party_dict['party'], True, prompt=f"Who gets the {item['item_desc']}?  ")
    rolls = get_heroine_rolls(heroine)
    tally(heroine, 'heals')
    who = 'herself' if target is heroine else target.name
    if not target.is_mob and not rolls['heal']:
        await say(f"{heroine.name} starts a {item['item_desc']} for {who}, loses her place halfway through, and it fizzles.  [narr]Doh![/]")
        await pause()
        return (party_dict, mobs, False)
    if which == 'blessing':
        status(target)['blessed'] = dict(BLESSING)
        what = f"{'Their' if target.is_mob else 'Her'} next attack is going to be something special"
    else:
        status(target)['strong'] = {'attacks': STRENGTH_ATTACKS}
        what = f"{'Their' if target.is_mob else 'Her'} next {STRENGTH_ATTACKS} attacks will hit harder"
    if target.is_mob:
        await say(f"{heroine.name} lays her {item['item_desc']} on {target.name}.  [narr]On the ENEMY.  I...  okay.[/]  {what}, and they're coming for one of you.")
        await pause()
        return (party_dict, mobs, False) # helping a mob never earns the luck roll
    await say(f"{heroine.name} lays her {item['item_desc']} on {who}.  {what}.  [narr]Don't waste it.[/]")
    await pause()
    return (party_dict, mobs, rolls['luck'])

async def heroine_hex(heroine : object, item : dict, party_dict : dict, mobs : list, heroine_rolls : dict) -> tuple:
    """Intoxication, Fungal Infection and Confusion: no damage, but every mob it lands on is worse off (see the
    effect list at the top). attack_type aoe goes for every mob; anything else, the one she picks. One hit roll
    for the cast; each mob can still dodge it (if its dodge beats her expertise). DRAFT lines."""
    which, rank = item['effect'], acc.item_family(item['item'])[1]
    everyone = item['attack_type'] == 'aoe'
    targets = [m for m in mobs if not m.is_dead] if everyone else [await get_target_choice(mobs, [])]
    aim = 'every enemy in sight' if everyone else targets[0].name
    tally(heroine, 'attacks')
    opening = {'intoxicate': f"{heroine.name} flicks her {item['item_desc']} at {aim}.",
               'stun': f"{heroine.name} bursts her {item['item_desc']} over {aim}!  [narr]Spores.  Everywhere.[/]",
               'confuse': f"{heroine.name} whispers her {item['item_desc']} at {aim}."}[which]
    await say(opening)
    if not heroine_rolls['hit']:
        await say("[narr]...and it fizzles into a sad little puff.  Nothing happens.[/]")
        await pause()
        return (party_dict, mobs, False)
    landed = 0
    for mob in targets:
        if hex_immune(mob, which, rank):
            hint = "  [narr]It'd take a MUCH stronger brew to get that one tipsy.[/]" if which == 'intoxicate' else "  [narr]Too big and too mean for that.[/]"
            await say(f"  {mob.name} shrugs it off.{hint}")
            continue
        if get_mob_rolls(mob)['dodge'] and not heroine_rolls['expertise']:
            await say(f"  {mob.name} dives out of the way!")
            continue
        landed += 1
        if which == 'intoxicate':
            if status(mob).get('intoxicated'):
                await say(f"  {mob.name} is already hammered.  [narr]You can't get drunker than drunk.[/]")
                landed -= 1
                continue
            status(mob)['intoxicated'] = True
            await say(f"  {mob.name} goes cross-eyed and starts swaying.  [narr]Good luck dodging anything now.[/]")
        elif which == 'stun':
            status(mob)['stunned'] = True
            await say(f"  {mob.name} gets a faceful and will lose its next turn.")
        else:
            status(mob)['confused'] = CONFUSE_TURNS
            await say(f"  {mob.name}'s eyes spin in two different directions.  [narr]It has no idea whose side it's on.[/]")
    await pause()
    return (party_dict, mobs, heroine_rolls['luck'] if landed else False)

async def blessed_line(heroine : object, rolls : dict):
    """Says so when a Blessing is riding on this attack (it's used up now, hit or miss). DRAFT line."""
    if rolls.get('blessed'):
        await say(f"{heroine.name}'s Blessing flares as she lines it up.  [narr]Here it comes.[/]")

async def hit_effect(heroine : object, item : dict, target : object):
    """Her hit just landed on a mob that's still standing: Snake Bite may poison it, the Tooth-Sharpened Dagger
    leaves it bleeding. DRAFT lines."""
    which = item.get('effect')
    if which == 'poison' and random.random() < POISON_CHANCE:
        status(target)['poisoned'] = {'turns': POISON_TURNS, 'low': POISON_DAMAGE[0], 'high': POISON_DAMAGE[1]}
        await say(f"[green]The venom takes![/]  {target.name} will take a little damage at the start of its turns until it wears off.") # no turn count on screen (Ted, Nov 10)
    elif which == 'bleed':
        status(target)['bleeding'] = {'low': BLEED_DAMAGE[0], 'high': BLEED_DAMAGE[1]}
        await say(f"[red]That wound isn't closing.[/]  {target.name} will bleed at the start of every turn for the rest of the fight.")

async def after_mob_damage(mob : object, party_dict : dict, mobs : list) -> dict:
    """A mob just lost HP to something other than a heroine's own hit (poison, bleeding, a confused friend): the
    same things happen as when she hits it. Happy enrages at half HP, killing enraged Happy wipes the party, and a
    dead Kobold sets its pack off."""
    if mob.mob_class == 'Disgruntled Dwarf' and mob.enraged and mob.is_dead:
        return acc.wipe_party(party_dict)
    if mob.mob_class == 'Disgruntled Dwarf' and mob.health < 0.5 * mob.starting_health and not mob.enraged:
        await mob.enrage()
        await pause()
        return party_dict
    if mob.is_dead:
        await say(f"{mob.name} has been slain!!  [narr]Didn't even have to touch that one.[/]")
        if hasattr(mob, 'on_death'): # the Krazy Kobolds' pack enrages
            await mob.on_death(mobs)
    return party_dict

GHOST_DAMAGE = (3, 8) # a slain heroine's parting shot: small, and nothing can dodge it

def ghost_ready(heroine : object) -> bool:
    """She's down and her ghost hasn't had its parting shot yet (see parting_shot)."""
    return heroine.is_dead and not getattr(heroine, 'ghost_spent', True)

async def parting_shot(heroine : object, party_dict : dict, mobs : list) -> dict:
    """(Ted, Nov 15) At the end of the round she died in, a slain heroine's ghost takes one last little swipe
    (GHOST_DAMAGE) at whichever mob is closest to dead, for the times she was 1 hp away. It can't be dodged, it
    doesn't care about bodyguards, and it only happens once per death. DRAFT lines."""
    heroine.ghost_spent = True
    standing = [m for m in mobs if not m.is_dead]
    if not standing:
        return party_dict
    mob = min(standing, key=lambda m: m.health)
    damage = min(mob.health, acc.multi_roll(*GHOST_DAMAGE))
    update_health(mob, damage)
    await say(f"\n{heroine.name}'s ghost claws its way up out of her body, wails, and takes one last swipe at {mob.name}: -{damage} hp.  [narr]Spite.  Stronger than death.[/]")
    if mob.is_dead and mob.mob_class != 'Disgruntled Dwarf':
        await say(f"{mob.name} has been slain!!  [narr]From BEYOND THE GRAVE, motherfucker![/]")
        if hasattr(mob, 'on_death'):
            await mob.on_death(mobs)
    else:
        party_dict = await after_mob_damage(mob, party_dict, mobs) # Happy: enraging, or the wipe if he's enraged
    await pause()
    return party_dict

async def mob_start_of_turn(mob : object, party_dict : dict, mobs : list) -> tuple:
    """The start of a mob's own turn: poison and bleeding take their bite, and a stunned mob loses the turn.
    Returns (party_dict, whether it still gets to act). DRAFT lines."""
    for key in ('poisoned', 'bleeding'):
        tick = status(mob).get(key)
        if not tick:
            continue
        sting = min(mob.health, acc.multi_roll(tick['low'], tick['high']))
        update_health(mob, sting)
        last = False
        if key == 'poisoned':
            tick['turns'] -= 1
            last = tick['turns'] <= 0
            if last:
                del mob.status['poisoned']
            await say(f"[green]The poison burns[/] {mob.name} for -{sting} hp." + ("  [narr]That's the last of it.[/]" if last and not mob.is_dead else ""))
        else:
            await say(f"[red]{mob.name} is still bleeding:[/] -{sting} hp.")
        party_dict = await after_mob_damage(mob, party_dict, mobs)
        if mob.is_dead or party_dict['wiped']:
            return (party_dict, False)
    if status(mob).pop('stunned', False):
        await say(f"{mob.name} is still digging fungus out of its eyes and loses its turn.  [narr]Gross.  Effective, but gross.[/]")
        return (party_dict, False)
    return (party_dict, True)

async def confused_turn(mob : object, party_dict : dict, mobs : list) -> tuple:
    """Confusion (Ted, Nov 14): it attacks or heals somebody at random, friend or foe. Only its plain single-target
    moves, so nothing with its own rules (gas, the hiss, an area attack) goes off sideways. DRAFT lines."""
    gear = [dict(item) for item in acc.get_mob_equipment() if item['item'] in mob.inv]
    simple = [item for item in gear if item['attack_type'] != 'aoe' and not item.get('effect')]
    if not simple:
        await say(f"{mob.name} stares at its own hands for a while.  [narr]Take your time, buddy.[/]")
        await pause()
        return (party_dict, mobs, False)
    item = random.choice(simple)
    everyone = [x for x in party_dict['party'] + mobs if not x.is_dead]
    healing = item['damage_high'] < 0
    target = random.choice(everyone if healing else [x for x in everyone if x is not mob])
    await say(f"{mob.name} blinks, turns in a slow circle, and settles on {'itself' if target is mob else target.name}.  [narr]Eeny, meeny...[/]")
    mob_rolls = get_mob_rolls(mob, attacking=not healing)
    target_rolls = {} if target.is_mob else get_heroine_rolls(target)
    party_dict, mobs, _ = await get_mob_turn_outcome(mob, target, item, party_dict, mobs, mob_rolls, target_rolls)
    return (party_dict, mobs, False) # a confused mob never gets a lucky extra turn

async def get_heroine_turn_outcome(heroine : object, item : dict,  target : object, party_dict : dict,  mobs : list, heroine_rolls : dict, mob_rolls : dict) -> tuple:
    base_damage = acc.multi_roll(item['damage_low'], item['damage_high'])
    attack_type = item['attack_type']
    strong = strength_bonus(heroine) if attack_type != 'heal' and target.is_mob else 0 # the Cleric's Strength, if it's on her: used up hit or miss
    base_damage += strong
    crit_mult = heroine_rolls['crit_mult']
    is_crit = crit_mult > 1 # will be used for auto commenting later
    damage_w_crit_mult = base_damage * crit_mult
    if attack_type == 'heal': # every heal, on a heroine or a mob, has its own function
        return await get_heal_outcome(heroine, item, target, party_dict, mobs, heroine_rolls, damage_w_crit_mult)
    if target.is_mob:  # an attack on a mob
        tough = mob_rolls['toughness']
        if tough:
            damage = damage_w_crit_mult / 2
        else:
            damage = damage_w_crit_mult
        junked = status(heroine).get('junked')
        if junked:
            damage = damage / 2 # a Junk Attack: her next damage is cut in half
        damage = int(damage)
        if target.health <= damage:
            damage = target.health
        if mob_rolls['scare'] and heroine_rolls['fear'] and item['item'] == 'happys_norovirus_regurgitation':
            tally(heroine, 'scared') # fear doesn't stop the puke, it makes it worse (Ted, Nov 15)
            damage = min(int(damage * SCARED_PUKE), target.health)
            await say(f"{heroine.name} takes one look at {target.name} and her stomach does a backflip.  [narr]Oh no.  Fear makes it come out FASTER.[/]") # DRAFT line
        elif mob_rolls['scare'] and heroine_rolls['fear']:
            tally(heroine, 'scared')
            await say(f"As {heroine.name} approaches {target.name}, she uncontrollably recoils at the very sight of them.  [narr]Honestly?  Fair.  That's a lost turn, though.[/]")
            await pause()
            return (party_dict, mobs, False)
        tally(heroine, 'attacks') # a whiff still counts as practice
        if not heroine_rolls['hit']:
            await say(f"[narr]Wow, that was a big ol' whiff, now wasn't it, {heroine.name}.[/]")
            await pause()
            return (party_dict, mobs, False)
        if mob_rolls['dodge'] and not heroine_rolls['expertise']:
            await say(f"{target.name} slips out of the way like a greased weasel.  {heroine.name}'s attack finds only air.")
            await pause()
            return (party_dict, mobs, False)
        target = update_health(target, damage)
        if is_crit:
            tally(heroine, 'crits')
        if junked:
            del heroine.status['junked']
            await say(f"[narr]{heroine.name}'s junk still hurts, so that one only lands at half strength.[/]")
        if mob_rolls['dodge']: # it dodged, but her expertise beat it
            await say(f"Despite their best effort to evade the attack, {heroine.name} successfully contacts {target.name} for -{damage} hp.")
        else:
            await say(f"{heroine.name} slams {target.name} with her {item['item_desc']} for -{damage} hp.")
        if strong:
            await say("[narr]The Cleric's Strength put some extra muscle behind that one.[/]")
        if not target.is_dead:
            await hit_effect(heroine, item, target) # Snake Bite's poison, the Dagger's bleeding
        if target.mob_class == 'Disgruntled Dwarf' and target.enraged and target.is_dead:
            party_dict = acc.wipe_party(party_dict)
            return (party_dict, mobs, False)
        if target.mob_class == 'Disgruntled Dwarf' and target.health < 0.5 * target.starting_health and not target.enraged:
            await target.enrage()
            await pause()
            return (party_dict, mobs, False)
        if target.is_dead:
            await say(f"{target.name} has been slain!!  [narr]Take THAT motherfucker!![/]")
            if hasattr(target, 'on_death'): # the Krazy Kobolds' pack enrages
                await target.on_death(mobs)
            await pause()
            return (party_dict, mobs, heroine_rolls['luck'])
        await check_tough(tough, target)
        await pause()
        return (party_dict, mobs, heroine_rolls['luck'])
    else: # can't happen today (only heals can target the party), but never a silent turn
        await say(f"{heroine.name} waves her {item['item_desc']} at {target.name}.  Nothing happens.  [narr]Weird flex.[/]")
        await pause()
        return (party_dict, mobs, False)

async def player_turn(heroine : object, party_dict : dict, mobs : list, extra : bool = False) -> tuple:
    """extra=True for her lucky second turn in a round: it doesn't count toward anything recharging."""
    if heroine.is_dead:
        return (party_dict, mobs, False)
    status(heroine).pop('hidden', None) # Hide only lasts until her next turn
    if not extra:
        heroine.cooldowns = {name: left - 1 for name, left in getattr(heroine, 'cooldowns', {}).items() if left > 1}
    poison = status(heroine).get('poisoned')
    if poison: # ticks at the start of her turn
        sting = min(heroine.health, acc.multi_roll(poison['low'], poison['high']))
        update_health(heroine, sting)
        poison['turns'] -= 1
        if poison['turns'] <= 0 or heroine.is_dead:
            del heroine.status['poisoned']
        if heroine.is_dead:
            await say(f"\n[green]The poison finishes what the Kobold started:[/]  it burns {heroine.name} for -{sting} hp, and she drops.  [red]slain[/]")
            await say("[narr]Did you really just let her wither away like that?  What an unfitting death.  They might torture her for it in the afterlife.[/]")
            await check_last_cleric([heroine], party_dict['party'])
            await pause()
            return (party_dict, mobs, False)
        await say(f"\n[green]The poison burns[/] {heroine.name} for -{sting} hp." + ("  [narr]That's the last of it, at least.[/]" if 'poisoned' not in heroine.status else ""))
    if status(heroine).pop('cowed', False):
        await say(f"\n{heroine.name} is still frozen stiff from that howl.  She loses her turn.  [narr]Blink, honey.  Blink.[/]")
        await pause()
        return (party_dict, mobs, False)
    if status(heroine).pop('gassed', False):
        await say(f"\n{heroine.name} is still doubled over, retching from the Kobold gas.  She loses her turn.  [narr]Breathe through your mouth, sweetie.[/]")
        await pause()
        return (party_dict, mobs, False)
    inv = [x for x in heroine.inv if acc.get_item(x)['attack_type'] != 'trinket'] # trinkets just ride along in the bag
    inv.sort(key=lambda x: bool(acc.get_item(x)['special'])) # specials at the bottom of the list, in the order she carries them (Ted, Nov 15)
    inv_len = len(inv)
    if inv_len < 1:
        await say(f"[narr]{heroine.name} has no inventory, so I guess she's skipping this turn...[/]")
        await pause()
        return (party_dict, mobs, False)
    await say(f"\n{heroine.name}'s turn:")
    spent = getattr(heroine, 'spent_specials', [])
    unready = lambda name: name in spent or ready_in(heroine, name) > 0
    if all(unready(item) for item in inv): # nothing but used-up specials: no point asking (it would ask forever)
        await say(f"[narr]Everything {heroine.name} is carrying is still recharging, so she spends this turn catching her breath.[/]")
        await pause()
        return (party_dict, mobs, False)
    def recharging(name): # '' when it's ready
        turns = ready_in(heroine, name)
        if turns:
            return f"  (recharging: ready in {turns} turn{'' if turns == 1 else 's'})"
        return '  (recharging)' if name in spent else ''
    item_labels = [item_label(item, heroine) + recharging(item) for item in inv]
    while True:
        if inv_len > 1:
            item_choice = await choose( # lists the items, keeps asking until the pick is valid
                "Choose your item.  Choose wisely.  [narr]Or don't, chaos is fun too...[/]  ",
                item_labels,
                f"\nNo, numb-nuts... sorry, I mean {party_dict['name']}, please choose one of the numbers!\n",
            )
        else:
            await say(f'1:  {item_labels[0]}')
            await say(f"[narr]Looks like {heroine.name} has but one item remaining, so I'm just going to assume it's the one you want and select it for you, mkay?[/]")
            await pause()
            item_choice = 0
        if not unready(inv[item_choice]):
            break
        if ready_in(heroine, inv[item_choice]):
            await say(f"\n[narr]Her {acc.get_item(inv[item_choice])['item_desc']} is still recharging, champ.  Pick something else.[/]\n")
        else:
            await say(f"\n[narr]Her {acc.get_item(inv[item_choice])['item_desc']} is still recharging, champ.  Specials work once per battle, remember?  Pick something else.[/]\n")
        if inv_len == 1:
            await pause()
            return (party_dict, mobs, False)

    item = acc.held_item(heroine, inv[item_choice]) # forged: boosted numbers and the kit's name
    heroine.wielding = item.get('upgrade') # the kit's perk counts for this turn's rolls (acc.stat_bonus)
    acc.use_up(heroine, item['item']) # one less use, for a consumable
    if item.get('recharge'): # back after that many of her turns (the recharge column), instead of once per battle
        heroine.cooldowns = {**getattr(heroine, 'cooldowns', {}), item['item']: item['recharge'] + 1}
    elif item['special']:
        heroine.spent_specials = spent + [item['item']] # used up for the rest of this battle, hit or miss
    item_attack_type = item['attack_type']
    is_heal = item_attack_type == 'heal'
    which = item.get('effect')

    if which == 'hide':
        return await heroine_hide(heroine, item, party_dict, mobs)
    if which in BUFFS:
        return await heroine_buff(heroine, item, party_dict, mobs)
    if which in HEXES or item_attack_type == 'aoe':
        rolls = get_heroine_rolls(heroine, attacking=True)
        await blessed_line(heroine, rolls)
        if which in HEXES:
            return await heroine_hex(heroine, item, party_dict, mobs, rolls)
        return await heroine_aoe(heroine, item, party_dict, mobs, rolls)
    if item_attack_type == 'aoe_heal':
        return await heroine_aoe_heal(heroine, item, party_dict, mobs, get_heroine_rolls(heroine))
    if item_attack_type == 'hail_mary':
        return await use_hail_mary(heroine, item, party_dict, mobs)

    if is_heal and acc.slot_kind(item) == 'potion':
        target = heroine # a potion is drunk by whoever's carrying it (Ted, Nov 10): no picking a target
    elif is_heal:
        target = await get_target_choice(mobs, party_dict['party'], True) # anyone can heal anyone, a mob too if they insist
    else:
        target = await get_target_choice(mobs, [])

    if target.is_mob and not is_heal and hasattr(target, 'guard'):
        target = await target.guard(heroine) # the wolf pack: a wolf may throw itself in front of the Alpha
    heroine_rolls = get_heroine_rolls(heroine, attacking=not is_heal)
    await blessed_line(heroine, heroine_rolls)
    if target.is_mob:
        mob_rolls = get_mob_rolls(target)
        return await get_heroine_turn_outcome(heroine, item, target, party_dict, mobs, heroine_rolls, mob_rolls)
    else:
        return await get_heroine_turn_outcome(heroine, item, target, party_dict, mobs, heroine_rolls, {})

def party_wiped_taunt(mob : object, party : list) -> str:
    # first make sure at least one heroine exists (may need to adjust to starting count of party, per encounter?) and still has a melee item, if we want to include item-specific taunts
    if len(party) > 1 :
        melee_names = {item['item'] for item in acc.get_items() if item['attack_type'] == 'melee' and not item['special']} # regular melee weapons only, specials left out (same as before the special column)
        have_items = [(heroine, item_name) for heroine in party for item_name in heroine.inv if item_name in melee_names]
        # if anyone has a melee weapon, which may need to be refined by hero_class or something to avoid things like Sappers' "Deep Scratch", there is a 50:50 chance of doing item-specific or non-item-specific taunts so that both lists are actually used haha
        if len(have_items) > 0:
            do_item_taunt = random.choice([True, False])
            if do_item_taunt:
                victim, item_name = random.choice(have_items)
                victim2 = random.choice([x for x in party if x != victim])
                item_desc = acc.get_item(item_name)['item_desc']
                template = random.choice(acc.item_specific_wipe_taunts())
                return template.format(mob=mob.name, victim=victim.name, item=item_desc, victim2=victim2.name)
        # emergency backup if noone has an item - can't really see this happening but hey, it's here
        victim = random.choice(party)
        victim2 = random.choice([x for x in party if x != victim])
        template = random.choice(acc.generic_wipe_taunts())
        return template.format(mob=mob.name, victim=victim.name, victim2=victim2.name)
    elif len(party) == 1:
        return f"\n{mob.name} walks over to {party[0].name}'s mangled corpse and spits on it.  \"What kind of FUCKING idiot attempts a dungeon encounter solo?!\""
    else:
        return "[narr]No party members.  Right....[/]"

# ---------- mob AI ------------------------------------------------------------
# The ai / enraged_ai columns in mobs.csv pick how a mob fights:
#   easy   - random target; leans toward its weaker attacks (its strongest comes up about 40% as often as its weakest)
#   medium - random target; its strongest attacks come up a bit less often (about 70%); heals hurt mobs now and then
#   hard   - finishes off heroines it can kill this hit, then goes after healers; leans toward its stronger
#            attacks; uses an area attack when enough heroines are standing; heals the most hurt mob
# Mob attacks are always repeatable within a fight (no once-per-battle rule for mobs).
AI_LEVELS = {'easy': 'easy', 'medium': 'medium', 'normal': 'medium', 'hard': 'hard'} # 'normal' = medium (the Krazy Kobolds use it)
WEIGHT_RANGE = {'easy': (1.0, 0.4), 'medium': (1.0, 0.7), 'hard': (0.6, 1.0)} # weight of its weakest attack, weight of its strongest
HEAL_TRY = {'easy': 0.10, 'medium': 0.25, 'hard': 0.6} # how often a mob with a heal item uses it while a mob is below 60% HP
# The weight column in mob_equipment.csv multiplies an attack's chance on top of all that (blank = 1): the Kobolds'
# Claws come up 3 times as often as their Hiss. Specials with an effect column need the right kind of target:
#   gas   - Gas Release: hits only melee heroines (each rolls to dodge); a hit costs her next turn
#   junk  - Junk Attack: a normal hit, and her next damage or heal is cut in half
#   hiss  - Terrifying Hiss: no damage; if it lands she can't dodge for the rest of the fight (skips anyone already rattled)
#   blink - Blink Stab: teleports behind a ranged heroine; she can't dodge or parry it
#   poison - a normal hit; if it lands, POISON_CHANCE of the time she's poisoned for her next POISON_TURNS turns
#   front - an area attack that only reaches the melee heroines up front (the Alpha Wolf's Mega Pounce)
#   howl  - no damage; every heroine standing is scared half as often as her fear stat says, and a scared one loses her next turn
SCARED_PUKE = 1.5 # Happy's Norovirus Regurgitation: a scared heroine pukes this much harder instead of losing her turn

MOB_EFFECTS = ('gas', 'junk', 'hiss', 'blink', 'poison', 'front', 'howl')
POISON_CHANCE, POISON_TURNS, POISON_DAMAGE = 0.5, 3, (2, 3) # Kobold Bite (Ted, Nov 8); the damage ticks at the start of her turn
GAS_MAX = 3 # one Gas Release reaches at most this many heroines, and never more than half the front line (rounded up)

def gas_targets(item : dict, party : list) -> list:
    """Who one Gas Release reaches: a few of the melee heroines, picked at random, not the whole front line
    (Ted, Nov 10: one fart cost the whole party a round). 1 of 1 or 2, 2 of 3 or 4, 3 of 5 or more."""
    front = standing_targets(item, party)
    reach = min(GAS_MAX, -(-len(front) // 2))
    hit = random.sample(front, reach)
    return [heroine for heroine in front if heroine in hit] # in party order

def ai_level(ai : str) -> str:
    return AI_LEVELS.get(str(ai).lower(), 'easy')

def average_damage(item : dict) -> float:
    return (item['damage_low'] + item['damage_high']) / 2

def weighted_attack(attacks : list, level : str) -> dict:
    """Pick an attack, weighted by how strong it is compared to the mob's others (see WEIGHT_RANGE), times its
    weight column."""
    ranked = sorted(attacks, key=average_damage)
    weakest, strongest = WEIGHT_RANGE[level]
    last = max(1, len(ranked) - 1)
    weights = [(weakest + (strongest - weakest) * spot / last) * (item.get('weight') or 1) for spot, item in enumerate(ranked)]
    return random.choices(ranked, weights)[0]

def standing_targets(item : dict, party : list) -> list:
    """The heroines this attack can go after (see MOB_EFFECTS): Gas only reaches the front line, Blink Stab goes
    for the back line, and the Hiss skips anyone it already rattled."""
    standing = [x for x in party if not x.is_dead]
    effect = item.get('effect')
    if effect in ('gas', 'blink', 'front'):
        return [x for x in standing if position(x) == ('range' if effect == 'blink' else 'melee')]
    if effect == 'howl':
        return [x for x in standing if not status(x).get('cowed')]
    if effect == 'hiss':
        return [x for x in standing if not status(x).get('hissed')]
    return standing

def choose_mob_item(inv : list, ai : str, party_dict : dict, mobs : list = ()) -> dict:
    level = ai_level(ai)
    gear = [dict(item) for item in acc.get_mob_equipment() if item['item'] in inv]
    attacks = [item for item in gear if item['damage_high'] >= 0 and (not item.get('effect') or standing_targets(item, party_dict['party']))]
    heals = [item for item in gear if item['damage_high'] < 0]
    hurt_mobs = [m for m in mobs if not m.is_dead and m.health < 0.6 * m.starting_health]
    if heals and not attacks:
        return random.choice(heals) # nothing else in its bag
    if heals and hurt_mobs and random.random() < HEAL_TRY[level]:
        return max(heals, key=lambda item: -average_damage(item)) if level == 'hard' else random.choice(heals)
    if level == 'hard':
        standing = len([x for x in party_dict['party'] if not x.is_dead])
        area = [item for item in attacks if item['attack_type'] == 'aoe' and not item.get('effect')]
        single = [item for item in attacks if item['attack_type'] != 'aoe']
        if area and single and standing >= 3:
            best_area = max(area, key=average_damage)
            if average_damage(best_area) * standing >= 2 * max(average_damage(i) for i in single) and random.random() < 0.5:
                return best_area # it pays off: enough of them standing to make the splash worth it
    return weighted_attack(attacks, level)

def choose_mob_target(targets : list, ai : str, item : dict = None) -> object:
    if ai_level(ai) != 'hard':
        return random.choice(targets)
    if targets[0].is_mob: # a heal: whoever's hurting most
        return min(targets, key=lambda m: m.health / m.starting_health)
    if item:
        killable = [x for x in targets if x.health <= average_damage(item)]
        if killable:
            return min(killable, key=lambda x: x.health) # finish her off
    healers = [x for x in targets if x.hero_class == 'Cleric']
    return random.choice(healers or targets) # then the healers, then anyone

async def mob_aoe(mob : object, item : dict, party_dict : dict, mobs : list, mob_rolls : dict) -> tuple:
    """A mob's area attack (Happy's Regurgitation): it hits every heroine still standing. Each one can
    dodge it (if her dodge beats its expertise), and toughness halves it, like any attack. No parrying vomit."""
    party = party_dict['party']
    crit = mob_rolls['crit_mult'] # one crit for the whole spray; the damage itself is rolled for each heroine
    if item['item'] == 'vomit':
        await say(f"{mob.name} suddenly goes stark-white, a panicked look on his face.  He doubles over, gurgles and suddenly pops up and sprays projectile vomit across the whole party!  [narr]Oh god.  The SMELL.[/]  \"Och, I feel sae much better,\" he taunts.")
    elif item.get('effect') == 'front':
        await say(f"{mob.name} launches a {item['item_desc']} and comes down on the whole front line!")
    else:
        await say(f"{mob.name} unleashes {item['item_desc']} on the whole party!")
    if not mob_rolls['hit']:
        await say("[narr]...and lands in an empty patch of dirt.  Graceful.[/]" if item.get('effect') == 'front' else "[narr]...and it splatters everywhere EXCEPT on anyone.  Lucky, lucky lassies.[/]")
        await pause()
        return (party_dict, mobs, False)
    fallen = []
    for heroine in standing_targets(item, party):
        rolls = get_heroine_rolls(heroine)
        if rolls['dodge'] and not mob_rolls['expertise']:
            tally(heroine, 'dodges')
            await say(f"  {heroine.name} ducks out of the way!")
            continue
        tally(heroine, 'hits_taken')
        if rolls['toughness']:
            tally(heroine, 'toughs')
        power = acc.multi_roll(item['damage_low'], item['damage_high']) * crit * getattr(mob, 'damage_mult', 1)
        damage = int(power / 2) if rolls['toughness'] else int(power)
        damage = min(damage, heroine.health)
        update_health(heroine, damage)
        if heroine.is_dead:
            fallen.append(heroine)
            await say(f"  {heroine.name} gets hit for -{damage} hp.  [red]slain[/]")
        else:
            await say(f"  {heroine.name} gets hit for -{damage} hp.{'  [narr]Tough motherfucker: damage halved![/]' if rolls['toughness'] else ''}")
    await check_last_cleric(fallen, party)
    await pause()
    return (party_dict, mobs, mob_rolls['luck'])

async def mob_gas(mob : object, item : dict, party_dict : dict, mobs : list, mob_rolls : dict) -> tuple:
    """Gas Release: a few of the melee heroines up front get a lungful (gas_targets). Each one can dodge it (if
    her dodge beats its expertise); a hit does a little damage and costs her next turn."""
    party = party_dict['party']
    await say(f"{mob.name} turns around, squats, and lets rip a {item['item_desc']} right at the front line!  [narr]Oh god.  It's GREEN.[/]")
    if not mob_rolls['hit']:
        await say("[narr]...and the cloud drifts off into a corner.  That corner will never recover.[/]")
        await pause()
        return (party_dict, mobs, False)
    fallen = []
    for heroine in gas_targets(item, party):
        rolls = get_heroine_rolls(heroine)
        if rolls['dodge'] and not mob_rolls['expertise']:
            tally(heroine, 'dodges')
            await say(f"  {heroine.name} holds her breath and ducks out of it!")
            continue
        tally(heroine, 'hits_taken')
        damage = min(int(acc.multi_roll(item['damage_low'], item['damage_high']) * mob_rolls['crit_mult'] * getattr(mob, 'damage_mult', 1)), heroine.health)
        update_health(heroine, damage)
        if heroine.is_dead:
            fallen.append(heroine)
            await say(f"  {heroine.name} gets hit for -{damage} hp.  [red]slain[/]")
        else:
            status(heroine)['gassed'] = True
            await say(f"  {heroine.name} gets a lungful (-{damage} hp) and doubles over, retching.  She'll lose her next turn.")
    await check_last_cleric(fallen, party)
    await pause()
    return (party_dict, mobs, mob_rolls['luck'])

async def mob_howl(mob : object, item : dict, party_dict : dict, mobs : list) -> tuple:
    """The Alpha Wolf's Howl: no damage. Each heroine still standing is scared half as often as her fear stat
    says; a scared one loses her next turn. DRAFT lines."""
    await say(f"{mob.name} throws back his head and lets out a {item['item_desc']} that rattles teeth.  [narr]Every hair I have just stood up.[/]")
    scared = []
    for heroine in standing_targets(item, party_dict['party']):
        if acc.roll_percent((heroine.stats['fear'] + acc.stat_bonus(heroine, 'fear')) / 2):
            status(heroine)['cowed'] = True
            scared.append(heroine.name)
    if scared:
        await say(f"  {acc.and_words(scared)} {'freezes' if len(scared) == 1 else 'freeze'} on the spot and will lose {'her' if len(scared) == 1 else 'their'} next turn.")
    else:
        await say("  Nobody flinches.  [narr]Ice in their veins, these ladies.[/]")
    await pause()
    return (party_dict, mobs, False)

async def mob_hiss(mob : object, target : object, item : dict, party_dict : dict, mobs : list, mob_rolls : dict) -> tuple:
    """Terrifying Hiss: no damage, but if it lands she's too rattled to dodge for the rest of the fight."""
    if not mob_rolls['hit']:
        await say(f"{mob.name} rears up and hisses at {target.name}, who just hisses right back.  [narr]Atta girl.[/]")
        await pause()
        return (party_dict, mobs, False)
    status(target)['hissed'] = True
    await say(f"{mob.name} rears up and lets loose a {item['item_desc']}, right in {target.name}'s face!  She's too rattled to dodge for the rest of the fight.  [narr]That noise is going to haunt my dreams.[/]")
    await pause()
    return (party_dict, mobs, mob_rolls['luck'])

async def get_mob_turn_outcome(mob : object, target : object, item : dict, party_dict : dict, mobs : list, mob_rolls : dict, target_rolls : dict) -> tuple:
    base_delta = acc.multi_roll(item['damage_low'], item['damage_high'])
    attack_type = item['attack_type'] # for future use to determine aoe outcomes
    crit_mult = mob_rolls['crit_mult']
    is_crit = crit_mult > 1 # intended to be used for autocommenting, for future work
    if item['damage_high'] >= 0:
        base_delta += strength_bonus(mob) # some Cleric put Strength on it: used up hit or miss
    delta_w_crit = base_delta * crit_mult
    if item['damage_high'] >= 0:
        delta_w_crit *= getattr(mob, 'damage_mult', 1) # a mob scaled to the party's size (the Kobolds) hits harder or softer
    if item['damage_high'] < 0:
        healing = -int(delta_w_crit)
        if target.health + healing > target.starting_health:
            healing = target.starting_health - target.health
        if target.is_mob:
            if not mob_rolls['heal']:
                await say(f"{mob.name} attempts to heal {target.name if target != mob else 'themself'} with {item['item_desc']}, but fucks up and nothing happens.  [narr]Idiot![/]")
                await pause()
                return (party_dict, mobs, False)
            if mob == target:
                mob = update_health(mob, -healing)
                await say(f"Using their {item['item_desc']}, {mob.name} heals for +{healing} hp.  [narr]Oh dear.[/]")
                await pause()
                return (party_dict, mobs, mob_rolls['luck'])
            else:
                target = update_health(target, -healing)
                await say(f"Using their {item['item_desc']}, {mob.name} heals {target.name} for +{healing} hp.  [narr]Ugh, teamwork.  Gross.[/]")
                await pause()
                return (party_dict, mobs, mob_rolls['luck'])
        else: # only a confused mob does this (Ted: no luck roll for it)
            if healing <= 0:
                await say(f"{mob.name} wanders over and dabs at {target.name} with their {item['item_desc']}.  She's fine already.  [narr]Sweet of it, though.[/]")
            else:
                target = update_health(target, -healing)
                await say(f"{mob.name} wanders over and uses their {item['item_desc']} on {target.name} for +{healing} hp.  [narr]Uh...  thanks?[/]")
            await pause()
            return (party_dict, mobs, False)
    else:
        if not target.is_mob:
            tough = target_rolls['toughness']
            parry = target_rolls['parry'] and attack_type == 'melee'
            damage = int(delta_w_crit)
            if tough:
                damage = int(damage / 2)
            if parry:
                damage = int(damage / 2)
            if target.health <= damage:
                damage = target.health
            if not mob_rolls['hit']:
                if item.get('effect') == 'blink':
                    await say(f"{mob.name} blinks out in a puff of purple smoke, pops up behind {target.name}... and stabs the air a foot to her left.  [narr]Teleporting is hard.[/]")
                else:
                    await say(f"{mob.name} attempts to attack {target.name} with their {item['item_desc']}, but misses widely.")
                await pause()
                return (party_dict, mobs, False)
            if target_rolls['dodge'] and not mob_rolls['expertise']:
                tally(target, 'dodges')
                await say(f"[narr]HELL YES![/]  {target.name} dodges {mob.name}'s attack like a goddamn ninja!")
                await pause()
                return (party_dict, mobs, False)
            target = update_health(target, damage)
            tally(target, 'hits_taken')
            if tough:
                tally(target, 'toughs')
            if parry:
                tally(target, 'parries')
            if item.get('effect') == 'blink':
                await say(f"{mob.name} blinks out in a puff of purple smoke and pops up right behind {target.name}!  {item['item_desc']} for -{damage} hp.  [narr]No dodging that one.[/]")
            elif item.get('effect') == 'junk':
                status(target)['junked'] = True
                await say(f"{mob.name} darts in low and lands a {item['item_desc']} on {target.name} for -{damage} hp.  Her next hit will only do half damage.  [narr]Below the belt.  Literally.[/]")
            elif target_rolls['dodge']: # she tried to dodge, but its expertise beat her
                await say(f"Despite her best effort to dodge the attack, {mob.name} strikes {target.name} with their {item['item_desc']} for -{damage} hp.")
            elif item['attack_type'] == 'range':
                await say(f"{mob.name} lands their {item['item_desc']} on {target.name} for -{damage} hp.")
            else:
                await say(f"{mob.name} bashes {target.name} with their {item['item_desc']} for -{damage} hp.")
            if item.get('effect') == 'poison' and not target.is_dead and random.random() < POISON_CHANCE:
                mult = getattr(mob, 'damage_mult', 1)
                status(target)['poisoned'] = {'turns': POISON_TURNS, 'low': max(1, round(POISON_DAMAGE[0] * mult)), 'high': max(1, round(POISON_DAMAGE[1] * mult))}
                await say(f"[green]The bite was poisoned![/]  {target.name} will take a little damage at the start of her turns until it wears off.") # no turn count on screen (Ted, Nov 10)
            if target.is_dead:
                await say([
                    f"[narr]NOOO![/]  {target.name} has been slain!  [narr]We'll remember you, bud.[/]",
                    f"[narr]Oh shit.[/]  {target.name} has been slain.  [narr]She'll be back next run, but damn, that one hurt.[/]",
                ])
                await check_last_cleric([target], party_dict['party'])
                await pause()
                return (party_dict, mobs, mob_rolls['luck'])
            if parry:
                await say([
                    f"But {target.name} manages to deflect half of the damage!  [narr]Way to go![/]",
                    f"But {target.name} manages to parry half of the damage!  [narr]Incredible![/]",
                ])
            await check_tough(tough, target)
            await pause()
            return (party_dict, mobs, mob_rolls['luck'])
        else: # a mob hitting a mob: only a confused one does this today (a berserker spell could too, later)
            victim_rolls = get_mob_rolls(target)
            damage = int(delta_w_crit / 2) if victim_rolls['toughness'] else int(delta_w_crit)
            damage = min(damage, target.health)
            if not mob_rolls['hit']:
                await say(f"{mob.name} takes a wild swing at {target.name} with their {item['item_desc']} and misses.  [narr]Damn.  So close to helping.[/]")
                await pause()
                return (party_dict, mobs, False)
            if victim_rolls['dodge'] and not mob_rolls['expertise']:
                await say(f"{mob.name} lunges at {target.name}, who hops out of the way and looks deeply offended.")
                await pause()
                return (party_dict, mobs, False)
            target = update_health(target, damage)
            await say(f"{mob.name} clobbers {target.name} with their {item['item_desc']} for -{damage} hp.  [narr]Friendly fire!  My favorite kind.[/]")
            party_dict = await after_mob_damage(target, party_dict, mobs)
            await pause()
            return (party_dict, mobs, False)

async def mob_turn(mob : object, party_dict : dict, mobs : list, extra : bool = False) -> tuple:
    """extra=True for a bonus attack: the line announcing it already said whose it is, so no "'s turn:" header."""
    if mob.is_dead:
        return (party_dict, mobs, False)
    if party_dict['wiped']: # one taunt per fight (Ted, Nov 8): the first mob to get a turn after the wipe
        if not party_dict.get('wipe_taunted'):
            party_dict['wipe_taunted'] = True
            await say(party_wiped_taunt(mob, party_dict['party']))
            await pause()
        return (party_dict, mobs, False)

    if not extra:
        await say(f"\n\n{mob.name}'s turn:\n")
        party_dict, acts = await mob_start_of_turn(mob, party_dict, mobs) # poison, bleeding, and a stun costs it the turn
        if not acts:
            await pause()
            return (party_dict, mobs, False)
    confused = status(mob).get('confused')
    if confused:
        if not extra: # a bonus attack is still a confused one, but doesn't use a turn of it up
            if confused <= 1:
                del mob.status['confused']
            else:
                mob.status['confused'] = confused - 1
        return await confused_turn(mob, party_dict, mobs)
    inv = mob.inv

    ai = mob.starting_ai
    if mob.enraged:
        ai = mob.enraged_ai

    item = choose_mob_item(inv, ai, party_dict, mobs)
    effect = item.get('effect')
    if effect == 'gas':
        return await mob_gas(mob, item, party_dict, mobs, get_mob_rolls(mob, attacking=True))
    if effect == 'howl':
        return await mob_howl(mob, item, party_dict, mobs)
    if item['attack_type'] == 'aoe' and item['damage_high'] >= 0:
        return await mob_aoe(mob, item, party_dict, mobs, get_mob_rolls(mob, attacking=True))
    if item['damage_high'] < 0:
        living_mobs = [x for x in mobs if not x.is_dead]
        hurt = [x for x in living_mobs if x.health < x.starting_health] # nobody wastes a heal on a mob at full health
        if len(living_mobs) > 0:
            target = choose_mob_target(hurt or living_mobs, ai)
            mob_rolls = get_mob_rolls(mob)
            return await get_mob_turn_outcome(mob, target, item, party_dict, mobs, mob_rolls, {})
    else:
        living_heroines = standing_targets(item, party_dict['party']) or [x for x in party_dict['party'] if not x.is_dead]
        if len(living_heroines) > 0:
            target = choose_mob_target(living_heroines, ai, item)
            if hasattr(mob, 'pick_target'): # the wolf pack's Hunt: several wolves on one heroine
                target = await mob.pick_target(living_heroines, item) or target
            mob_rolls = get_mob_rolls(mob, attacking=True)
            if effect == 'hiss':
                return await mob_hiss(mob, target, item, party_dict, mobs, mob_rolls)
            target_rolls = get_heroine_rolls(target)
            if effect == 'blink': # from behind: no dodging, no parrying
                target_rolls['dodge'] = target_rolls['parry'] = False
            return await get_mob_turn_outcome(mob, target, item, party_dict, mobs, mob_rolls, target_rolls)
    return (party_dict, mobs, False)
