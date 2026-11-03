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
    },
}
DEFAULT_AOE = {'unavoidable': False, 'tough_cut': 0.5, 'party_share': {}, 'blows_up_user': False, 'once_per_run': False}

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

async def show_current_status(party: list, mobs: list, round_num: int):
    await show_battle(party, mobs, round_num) # the round/enemy/party layout lives in Slayer_UI now

def get_heroine_rolls(heroine: object) -> dict:
    heroine_stats = heroine.stats
    roll_results = {}
    if acc.roll_percent(heroine_stats['crit_chance']):
        roll_results['crit_mult'] = heroine_stats['crit_mult']
    else:
        roll_results['crit_mult'] = 1 # if not a crit, multiplier is 1
    for stat in ['hit', 'luck', 'expertise', 'toughness', 'dodge', 'parry', 'fear']:
        roll_results[stat] = acc.roll_percent(heroine_stats[stat])
    roll_results['heal'] = acc.roll_percent(heroine_stats['heal_chance'])
    roll_results['aoe_heal'] = acc.roll_percent(heroine_stats['aoe_heal_chance'])
    return roll_results

def get_mob_rolls(mob: object) -> dict:
    mob_stats = mob.stats
    prefix = 'enraged_' if mob.enraged else '' # an enraged mob rolls against the enraged_ columns from mobs.csv
    roll_results = {}
    if acc.roll_percent(mob_stats[prefix + 'crit_chance']):
        roll_results['crit_mult'] = mob_stats[prefix + 'crit_mult']
    else:
        roll_results['crit_mult'] = 1
    for stat in ['hit', 'luck', 'expertise', 'toughness', 'dodge']:
        roll_results[stat] = acc.roll_percent(mob_stats[prefix + stat])
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
        await say(f"{target.name}, being the tough muthafucka she is, shrugs off half the damage.  [narr]Hell yeah![/]")
    elif tough and target.is_mob:
        await say(f"Damn... {target.name} is one tough piece-of-shit.  They absorbed HALF the damage!")

async def check_last_cleric(fallen : list, party : list):
    """If the party just lost its last Cleric (and anyone's still standing), the narrator panics."""
    clerics_fell = any(x.hero_class == 'Cleric' for x in fallen)
    clerics_left = any(x.hero_class == 'Cleric' and not x.is_dead for x in party)
    if clerics_fell and not clerics_left and any(not x.is_dead for x in party):
        await say(LAST_CLERIC_LINES)

def item_label(item_name : str) -> str: # one line of the item menu
    data = acc.get_item(item_name)
    desc = data['item_desc']
    low = data['damage_low']
    high = data['damage_high']
    if data['attack_type'] == 'hail_mary':
        return f'{desc} (hail mary)'
    if low >= 0:
        return f'{desc} ({low} - {high} damage)'
    else:
        return f'{desc} ({-1 * high} - {-1 * low} healing)'

async def get_target_choice(mobs : list, party : list, healing : bool = False) -> object:
    living_party = [x for x in party if not x.is_dead]
    living_mobs = [x for x in mobs if not x.is_dead]
    living_targets = living_party + living_mobs
    if len(living_targets) == 1:
        return living_targets[0]
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
                f"{heroine.name} successfully heals {target.name} for {healing} hp.  [narr]What in the flying-fuck were you thinking?  Are you trying to give me gas?[/]",
                f"{heroine.name} swells with pride as she successfully heals {target.name} for {healing} hp.  [narr]Pride eh?  Well.... Good Job??[/]",
                f"{target.name} grins wickedly at {heroine.name} as their wounds begin to bind.  \"Thank you!\" {target.name} screams in your face, spraying you with spittle.  [narr]Did you expect that to go a different way or something?[/]",
                f"{heroine.name} lays her holy hands on {target.name} for {healing} hp.  [narr]Somewhere up there, a god just facepalmed so hard it echoed.[/]",
                f"[narr]Ah yes, the classic \"heal the guy who's trying to murder us\" strategy.[/]  {heroine.name} patches up {target.name} for {healing} hp.  [narr]Bold.  Stupid, but bold.[/]",
            ])
        else:
            await say(f"{heroine.name} takes it upon herself to use her {item['item_desc']} to heal {target.name} for {healing} hp")
            await say("[narr]I swear I'm on your side here, but what was she thinking?  I guess she wanted more of a challenge?[/]")
        await pause()
        if hasattr(target, 'healed_by'): # some mobs have something to say about it (Happy does)
            await target.healed_by(heroine)
        return (party_dict, mobs, False) # healing a mob never earns the luck roll

    if not heroine_rolls['heal']:
        await say(f"{heroine.name} tries to heal {'herself' if heroine == target else target.name}, but does a piss-poor job and just ends up wasting her turn.  [narr]Doh![/]")
        await pause()
        return (party_dict, mobs, False)
    if target.health == target.starting_health:
        await say(f"[narr]That was weird.  {target.name} is at full health, goof.  Oh well, better luck choosing a target next time?[/]")
        await pause()
        return (party_dict, mobs, heroine_rolls['luck'])
    target = update_health(target, -healing)
    await say(f"{heroine.name} quickly uses {item['item_desc']} to heal {'herself' if heroine == target else target.name} for {healing} hp")
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
            await say(f"{heroine.name} raises the {item['item_desc']} and mutters something she definitely made up on the spot.  It WORKS.  {chosen.name} gasps back to life with {chosen.health} hp.  [narr]Holy shit![/]")
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
    power = acc.multi_roll(item['damage_low'], item['damage_high']) * heroine_rolls['crit_mult']
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
    for mob in [m for m in mobs if not m.is_dead]:
        mob_rolls = get_mob_rolls(mob)
        if not rules['unavoidable'] and mob_rolls['dodge'] and not heroine_rolls['expertise']:
            await say(f"  {mob.name} dives out of the way!")
            continue
        damage = power * (1 - rules['tough_cut']) if mob_rolls['toughness'] else power
        damage = int(min(damage, mob.health))
        update_health(mob, damage)
        if mob.is_dead and not mob.enraged and not getattr(mob, 'is_boss', False):
            await say(f"  {mob.name} takes {damage} hp and is {'blown to bits' if rules['blows_up_user'] else 'done for'}!")
        else:
            await say(f"  {mob.name} takes {damage} hp.")
    fallen = []
    for member in [x for x in party if not x.is_dead and x is not heroine]:
        share = rules['party_share'].get(position(member), 0)
        if not share:
            continue
        damage = power * share
        if get_heroine_rolls(member)['toughness']:
            damage *= 1 - rules['tough_cut']
        damage = int(min(damage, member.health))
        update_health(member, damage)
        if member.is_dead:
            fallen.append(member)
            await say(f"  {member.name} catches {damage} hp of it.  [red]slain[/]")
        else:
            await say(f"  {member.name} catches {damage} hp of it.")
    if rules['blows_up_user']:
        heroine.health, heroine.is_dead, heroine.blown_up = 0, True, True # out for the rest of this dungeon run
        fallen.append(heroine)
        await say(f"And {heroine.name}?  Blown into a billion little pieces.  [narr]Even the Cleric can't help her without some serious smelling salts.[/]")
    await check_last_cleric(fallen, party)
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

async def get_heroine_turn_outcome(heroine : object, item : dict,  target : object, party_dict : dict,  mobs : list, heroine_rolls : dict, mob_rolls : dict) -> tuple:
    base_damage = acc.multi_roll(item['damage_low'], item['damage_high'])
    attack_type = item['attack_type']
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
        damage = int(damage)
        if target.health <= damage:
            damage = target.health
        if mob_rolls['scare'] and heroine_rolls['fear']:
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
        if mob_rolls['dodge']: # it dodged, but her expertise beat it
            await say(f"Despite their best effort to evade the attack, {heroine.name} successfully contacts {target.name} for {damage} hp.")
        else:
            await say(f"{heroine.name} slams {target.name} with her {item['item_desc']} for {damage} hp.")
        if target.mob_class == 'Disgruntled Dwarf' and target.enraged and target.is_dead:
            party_dict = acc.wipe_party(party_dict)
            return (party_dict, mobs, False)
        if target.mob_class == 'Disgruntled Dwarf' and target.health < 0.5 * target.starting_health and not target.enraged:
            await target.enrage()
            await pause()
            return (party_dict, mobs, False)
        if target.is_dead:
            await say(f"{target.name} has been slain!!  [narr]Take THAT motherfucker!![/]")
            await pause()
            return (party_dict, mobs, heroine_rolls['luck'])
        await check_tough(tough, target)
        await pause()
        return (party_dict, mobs, heroine_rolls['luck'])
    else: # can't happen today (only heals can target the party), but never a silent turn
        await say(f"{heroine.name} waves her {item['item_desc']} at {target.name}.  Nothing happens.  [narr]Weird flex.[/]")
        await pause()
        return (party_dict, mobs, False)

async def player_turn(heroine : object, party_dict : dict, mobs : list) -> tuple:
    if heroine.is_dead:
        return (party_dict, mobs, False)
    inv = heroine.inv
    inv_len = len(inv)
    if inv_len < 1:
        await say(f"[narr]{heroine.name} has no inventory, so I guess she's skipping this turn...[/]")
        await pause()
        return (party_dict, mobs, False)
    await say(f"\n{heroine.name}'s turn:")
    spent = getattr(heroine, 'spent_specials', [])
    item_labels = [item_label(item) + ('  (recharging)' if item in spent else '') for item in inv]
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
        if inv[item_choice] not in spent:
            break
        await say(f"\n[narr]Her {acc.get_item(inv[item_choice])['item_desc']} is still recharging, champ.  Specials work once per battle, remember?  Pick something else.[/]\n")
        if inv_len == 1:
            await pause()
            return (party_dict, mobs, False)

    item = acc.get_item(inv[item_choice])
    if item['special']:
        heroine.spent_specials = spent + [item['item']] # used up for the rest of this battle, hit or miss
    item_attack_type = item['attack_type']
    is_heal = item_attack_type == 'heal'

    if item_attack_type == 'aoe':
        return await heroine_aoe(heroine, item, party_dict, mobs, get_heroine_rolls(heroine))
    if item_attack_type == 'hail_mary':
        return await use_hail_mary(heroine, item, party_dict, mobs)

    if is_heal:
        target = await get_target_choice(mobs, party_dict['party'], True) # anyone can heal anyone, a mob too if they insist
    else:
        target = await get_target_choice(mobs, [])

    heroine_rolls = get_heroine_rolls(heroine)
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

def ai_level(ai : str) -> str:
    return AI_LEVELS.get(str(ai).lower(), 'easy')

def average_damage(item : dict) -> float:
    return (item['damage_low'] + item['damage_high']) / 2

def weighted_attack(attacks : list, level : str) -> dict:
    """Pick an attack, weighted by how strong it is compared to the mob's others (see WEIGHT_RANGE)."""
    ranked = sorted(attacks, key=average_damage)
    weakest, strongest = WEIGHT_RANGE[level]
    last = max(1, len(ranked) - 1)
    weights = [weakest + (strongest - weakest) * spot / last for spot in range(len(ranked))]
    return random.choices(ranked, weights)[0]

def choose_mob_item(inv : list, ai : str, party_dict : dict, mobs : list = ()) -> dict:
    level = ai_level(ai)
    gear = [dict(item) for item in acc.get_mob_equipment() if item['item'] in inv]
    attacks = [item for item in gear if item['damage_high'] >= 0]
    heals = [item for item in gear if item['damage_high'] < 0]
    hurt_mobs = [m for m in mobs if not m.is_dead and m.health < 0.6 * m.starting_health]
    if heals and hurt_mobs and level != 'easy' and random.random() < (0.6 if level == 'hard' else 0.35):
        return max(heals, key=lambda item: -average_damage(item)) if level == 'hard' else random.choice(heals)
    if level == 'hard':
        standing = len([x for x in party_dict['party'] if not x.is_dead])
        area = [item for item in attacks if item['attack_type'] == 'aoe']
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
    power = acc.multi_roll(item['damage_low'], item['damage_high']) * mob_rolls['crit_mult']
    if item['item'] == 'vomit':
        await say(f"{mob.name} doubles over, gurgles, and sprays {item['item_desc']} across the whole party!  [narr]Oh god.  The SMELL.[/]")
    else:
        await say(f"{mob.name} unleashes {item['item_desc']} on the whole party!")
    if not mob_rolls['hit']:
        await say(f"[narr]...and it splatters everywhere EXCEPT on anyone.  Lucky, lucky lassies.[/]")
        await pause()
        return (party_dict, mobs, False)
    fallen = []
    for heroine in [x for x in party if not x.is_dead]:
        rolls = get_heroine_rolls(heroine)
        if rolls['dodge'] and not mob_rolls['expertise']:
            tally(heroine, 'dodges')
            await say(f"  {heroine.name} ducks out of the way!")
            continue
        tally(heroine, 'hits_taken')
        if rolls['toughness']:
            tally(heroine, 'toughs')
        damage = int(power / 2) if rolls['toughness'] else int(power)
        damage = min(damage, heroine.health)
        update_health(heroine, damage)
        if heroine.is_dead:
            fallen.append(heroine)
            await say(f"  {heroine.name} takes {damage} hp.  [red]slain[/]")
        else:
            await say(f"  {heroine.name} takes {damage} hp{'  (tough: half)' if rolls['toughness'] else ''}.")
    await check_last_cleric(fallen, party)
    await pause()
    return (party_dict, mobs, mob_rolls['luck'])

async def get_mob_turn_outcome(mob : object, target : object, item : dict, party_dict : dict, mobs : list, mob_rolls : dict, target_rolls : dict) -> tuple:
    base_delta = acc.multi_roll(item['damage_low'], item['damage_high'])
    attack_type = item['attack_type'] # for future use to determine aoe outcomes
    crit_mult = mob_rolls['crit_mult']
    is_crit = crit_mult > 1 # intended to be used for autocommenting, for future work
    delta_w_crit = base_delta * crit_mult
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
                await say(f"Using their {item['item_desc']}, {mob.name} heals for {healing} hp.  [narr]Oh dear.[/]")
                await pause()
                return (party_dict, mobs, mob_rolls['luck'])
            else:
                target = update_health(target, -healing)
                await say(f"Using their {item['item_desc']}, {mob.name} heals {target.name} for {healing} hp.  [narr]Ugh, teamwork.  Gross.[/]")
                await pause()
                return (party_dict, mobs, mob_rolls['luck'])
        else:
            await say('Need logic for mobs healing party members, in case we decide to do this.  I say no luck roll for it, though.')
            await pause()
            return (party_dict, mobs, False) # add logic for mob healing party members
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
            if target_rolls['dodge']: # she tried to dodge, but its expertise beat her
                await say(f"Despite her best effort to dodge the attack, {mob.name} strikes {target.name} with their {item['item_desc']} for {damage} hp.")
            else:
                await say(f"{mob.name} bashes {target.name} with their {item['item_desc']} for {damage} hp.")
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
        else:
            await say('Filler for mobs attacking each other, if I decide to have a berserker spell or perhaps a witch can cast confusion or something that makes mobs attack each other, or just randomly in general (party or other mobs can be attacked?).  Might be fun.')
            await pause()
            return (party_dict, mobs, mob_rolls['luck'])

async def mob_turn(mob : object, party_dict : dict, mobs : list, extra : bool = False) -> tuple:
    """extra=True for a bonus attack: the line announcing it already said whose it is, so no "'s turn:" header."""
    if mob.is_dead:
        return (party_dict, mobs, False)
    if party_dict['wiped']:
        await say(party_wiped_taunt(mob, party_dict['party']))
        await pause()
        return (party_dict, mobs, False)

    if not extra:
        await say(f"\n\n{mob.name}'s turn:\n")
    inv = mob.inv

    ai = mob.starting_ai
    if mob.enraged:
        ai = mob.enraged_ai

    item = choose_mob_item(inv, ai, party_dict, mobs)
    if item['attack_type'] == 'aoe' and item['damage_high'] >= 0:
        return await mob_aoe(mob, item, party_dict, mobs, get_mob_rolls(mob))
    if item['damage_high'] < 0:
        living_mobs = [x for x in mobs if not x.is_dead]
        if len(living_mobs) > 0:
            target = choose_mob_target(living_mobs, ai)
            mob_rolls = get_mob_rolls(mob)
            return await get_mob_turn_outcome(mob, target, item, party_dict, mobs, mob_rolls, {})
    else:
        living_heroines = [x for x in party_dict['party'] if not x.is_dead]
        if len(living_heroines) > 0:
            target = choose_mob_target(living_heroines, ai, item)
            mob_rolls = get_mob_rolls(mob)
            target_rolls = get_heroine_rolls(target)
            return await get_mob_turn_outcome(mob, target, item, party_dict, mobs, mob_rolls, target_rolls)
    return (party_dict, mobs, False)
