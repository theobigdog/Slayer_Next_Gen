import Slayer_Accessory as acc
from Slayer_Accessory import wt, next, whine
import pandas as pd
import joblib as jb
import random
from colorama import Fore, Back, Style, Cursor
import time

# ============================================================================
# YOUR EXISTING FUNCTIONS (KEPT!)
# ============================================================================

def display_mob_summary(mob: dict):
    print()
    print(f"Name: {mob.name}")
    print(f"Class: {mob.mob_class}")
    low_health = mob.health <= (mob.starting_health * 0.1)
    half_health = mob.health <= (mob.starting_health * 0.5)
    if low_health:
        print(f"Current Health: {Fore.RED}{int(round(mob.health, 0))}{Style.RESET_ALL}/{mob.starting_health}")
    elif half_health:
        print(f"Current Health: {Fore.MAGENTA}{int(round(mob.health, 0))}{Style.RESET_ALL}/{mob.starting_health}")
    else:
        print(f"Current Health: {mob.health}/{mob.starting_health}")

def display_party_summary(party : list):
    print()
    for heroine in party:
        low_health = heroine.health <= (heroine.starting_health * 0.1)
        half_health = heroine.health <= (heroine.starting_health * 0.5)
        if low_health:
            print(f"{heroine.heroine_name}:  {heroine.hero_class}, {Fore.RED}{int(round(heroine.health, 0))}{Style.RESET_ALL}/{heroine.starting_health}")
        elif half_health:
            print(f"{heroine.heroine_name}:  {heroine.hero_class}, {Fore.MAGENTA}{int(round(heroine.health, 0))}{Style.RESET_ALL}/{heroine.starting_health}")
        else:
            print(f"{heroine.heroine_name}:  {heroine.hero_class}, {int(round(heroine.health, 0))}/{heroine.starting_health}")

def show_current_status(party: dict, mob: dict):
    wt()
    print('Enemy')
    display_mob_summary(mob)
    print()
    print()
    print('Party')
    display_party_summary(party)

def get_heroine_rolls(heroine, items=None):
    """
    Generate attack rolls for a heroine and resolve combat checks.
    
    Args:
        heroine: Hero object
        items: Items dataframe (optional)
        
    Returns:
        dict: Attack roll values and combat resolution
    """
    # Load items if not provided
    if items is None:
        try:
            items = pd.read_csv('supporting_docs/items.csv')
        except FileNotFoundError:
            print(f"{Fore.RED}WARNING: items.csv not found! Using default damage{Style.RESET_ALL}")
            items = pd.DataFrame()
    
    # Get dice cutoffs
    cutoffs = acc.get_dice_cutoffs()
    
    # Find equipped weapon
    equipped_weapon = None
    weapon_data = None
    
    if not items.empty and hasattr(heroine, 'inv') and heroine.inv:
        for item_name in heroine.inv:
            item_row = items[items['item'] == item_name]
            if not item_row.empty:
                attack_type = item_row['attack_type'].values[0]
                # Check if it's a weapon type
                if attack_type in ['melee', 'range', 'both', 'special_melee', 'special_range', 'special_both']:
                    equipped_weapon = item_name
                    weapon_data = item_row
                    break
    
    # If no weapon found, use fists (1-4 damage)
    if weapon_data is None:
        low_damage = 1
        high_damage = 4
    else:
        low_damage = int(weapon_data['damage_range_low'].values[0])
        high_damage = int(weapon_data['damage_range_high'].values[0])
    
    # Roll base damage
    damage = acc.multi_roll(low_damage, high_damage)
    
    # Apply expertise bonus
    damage += heroine.stats['expertise']
    
    # Generate all combat rolls
    crit_roll = random.randint(cutoffs['low'], cutoffs['crit_cutoff'])
    miss_roll = random.randint(heroine.stats['low_miss'], heroine.stats['high_miss'])
    luck_roll = random.randint(cutoffs['low'], heroine.stats['luck'])
    expertise_roll = random.randint(cutoffs['low'], cutoffs['expertise_cutoff'])
    toughness_roll = random.randint(cutoffs['low'], cutoffs['toughness_cutoff'])
    dodge_roll = random.randint(cutoffs['low'], cutoffs['dodge_cutoff'])
    parry_roll = random.randint(cutoffs['low'], cutoffs['parry_cutoff'])
    fear_roll = random.randint(cutoffs['low'], cutoffs['fear_cutoff'])
    heal_roll = random.randint(cutoffs['low'], cutoffs['heal_cutoff'])
    aoe_heal_roll = random.randint(cutoffs['low'], cutoffs['aoe_heal_cutoff'])
    
    # Resolve combat checks
    is_crit = crit_roll >= heroine.stats.get('crit', 18)
    is_miss = miss_roll >= cutoffs['miss_threshold']
    
    # Apply crit multiplier if crit
    if is_crit:
        damage = int(damage * cutoffs['crit_mult_cutoff'])
    
    return {
        'damage': damage,
        'crit_roll': crit_roll,
        'miss_roll': miss_roll,
        'luck_roll': luck_roll,
        'expertise_roll': expertise_roll,
        'toughness_roll': toughness_roll,
        'dodge_roll': dodge_roll,
        'parry_roll': parry_roll,
        'fear_roll': fear_roll,
        'heal_roll': heal_roll,
        'aoe_heal_roll': aoe_heal_roll,
        'crit': is_crit,
        'miss': is_miss,
        'weapon': equipped_weapon if equipped_weapon else "Fists"
    }

def get_mob_rolls(mob: object) -> dict:
    """
    Generate all combat rolls for a mob.
    Returns both numeric roll values AND success/fail booleans.
    
    Args:
        mob: Mob object performing the rolls
        
    Returns:
        dict: All roll results (numeric + boolean)
    """
    roll_results = {}
    mob_stats = mob.stats
    
    # Determine dice range based on mob type
    if mob.mob_type == 'minion':
        low = 1
        high = 10
    elif mob.mob_type == 'boss':
        low = 1
        high = 30
    else:  # regular
        low = 1
        high = 20
    
    # Roll all the dice
    crit = acc.multi_roll(low, high)
    miss = acc.multi_roll(mob_stats['low_miss'], mob_stats['high_miss'])
    luck = acc.multi_roll(low, high)
    expertise = acc.multi_roll(low, high)
    toughness = acc.multi_roll(low, high)
    dodge = acc.multi_roll(low, high)
    parry = acc.multi_roll(low, high)
    fear = acc.multi_roll(low, high)
    damage = acc.multi_roll(low, high)
    
    # Store NUMERIC roll values (for combat comparisons)
    roll_results['crit_roll'] = crit
    roll_results['miss_roll'] = miss
    roll_results['luck_roll'] = luck
    roll_results['expertise_roll'] = expertise
    roll_results['toughness_roll'] = toughness
    roll_results['dodge_roll'] = dodge
    roll_results['parry_roll'] = parry
    roll_results['fear_roll'] = fear
    roll_results['damage_roll'] = damage
    
    # Store SUCCESS/FAIL booleans (for convenience)
    roll_results['crit_success'] = crit > mob_stats['crit']
    roll_results['crit_mult'] = mob_stats['crit_mult'] if crit > mob_stats['crit'] else 1
    roll_results['miss'] = miss < 5  # Mobs have fixed miss threshold
    roll_results['luck'] = luck > mob_stats['luck']
    roll_results['expertise'] = expertise > mob_stats['expertise']
    roll_results['toughness'] = toughness > mob_stats['toughness']
    roll_results['dodge'] = dodge > mob_stats['dodge']
    roll_results['parry'] = parry > mob_stats['parry']
    roll_results['fear'] = fear > mob_stats['fear']
    
    return roll_results

def update_health(initial_health : int, delta : int) -> int:
    return initial_health - delta if initial_health - delta > 0 else 0

# ============================================================================
# NEW UTILITY FUNCTIONS
# ============================================================================

def roll_d20():
    """Standard d20 roll."""
    return random.randint(1, 20)

def roll_d100():
    """Percentage roll."""
    return random.randint(1, 100)

# ============================================================================
# FEAR SYSTEM
# ============================================================================

def check_fear(heroine, mob):
    """
    Check if heroine is frightened by mob.
    
    Args:
        heroine: Heroine object with stats
        mob: Mob object with stats
        
    Returns:
        bool: True if heroine is frightened (loses turn)
    """
    mob_scare_roll = roll_d20() + mob.stats['scare']
    heroine_fear_resist = heroine.stats['fear']
    
    if mob_scare_roll > heroine_fear_resist:
        return True
    return False

def fear_flavor_text(heroine, mob):
    """Generate flavor text for fear effects."""
    fear_messages = [
        f"{heroine.name} freezes, eyes wide with terror.",
        f"{heroine.name}'s hands tremble. She can't move.",
        f"{heroine.name} takes a step back, paralyzed by fear.",
        f"{heroine.name} tries to act, but panic overwhelms her.",
        f"{heroine.name}'s courage fails her. She's rooted to the spot.",
    ]
    return random.choice(fear_messages)

# ============================================================================
# DAMAGE TIER SYSTEM
# ============================================================================

def calculate_damage_tier(damage_dealt, max_possible_damage, is_crit, luck_stat):
    """
    Determine damage tier for flavor text.
    
    Tiers:
    1. Glancing blow (< 25% max damage)
    2. Normal hit (25-50%)
    3. Good hit (50-75%)
    4. Critical hit (75-100% OR crit succeeded)
    5. Devastating crit (crit + high damage + luck check)
    
    Args:
        damage_dealt: Actual damage number
        max_possible_damage: Maximum possible damage from this attack
        is_crit: Whether crit roll succeeded
        luck_stat: Attacker's luck stat
        
    Returns:
        str: Tier name ('glancing', 'normal', 'good', 'critical', 'devastating')
    """
    damage_percent = (damage_dealt / max_possible_damage) * 100 if max_possible_damage > 0 else 0
    
    # Devastating crit: crit + high damage + luck check
    if is_crit and damage_percent >= 75 and roll_d20() <= luck_stat:
        return 'devastating'
    
    # Critical hit: crit roll OR very high damage
    if is_crit or damage_percent >= 75:
        return 'critical'
    
    # Good hit
    if damage_percent >= 50:
        return 'good'
    
    # Normal hit
    if damage_percent >= 25:
        return 'normal'
    
    # Glancing blow
    return 'glancing'

# ============================================================================
# FLAVOR TEXT GENERATORS - HEROINE ATTACKING MOB
# ============================================================================

def get_attack_flavor_heroine_to_mob(heroine, mob, damage, tier, weapon_name):
    """
    Generate sarcastic/humorous flavor text for heroine attacking mob.
    
    Args:
        heroine: Attacking heroine object
        mob: Target mob object
        damage: Damage dealt
        tier: Damage tier ('glancing', 'normal', 'good', 'critical', 'devastating')
        weapon_name: Name of weapon used
        
    Returns:
        str: Flavor text description
    """
    
    if tier == 'glancing':
        messages = [
            f"{heroine.heroine_name} swings {weapon_name} with all the grace of a drunken ox.\nIt barely grazes {mob.name}. How embarrassing. ({damage} damage)",
            f"{heroine.heroine_name} pokes {mob.name} with {weapon_name}.\n{mob.name} looks offended. ({damage} damage)",
            f"{heroine.heroine_name}'s attack glances off {mob.name}'s... is that armor or just dirt?\nEither way, not very effective. ({damage} damage)",
            f"{heroine.heroine_name} tries. She really does.\n{weapon_name} tinks harmlessly off {mob.name}. ({damage} damage)",
        ]
    
    elif tier == 'normal':
        messages = [
            f"{heroine.heroine_name} lands a solid hit with {weapon_name}.\nNothing fancy, but it gets the job done. ({damage} damage)",
            f"{heroine.heroine_name} strikes {mob.name} with {weapon_name}.\n{mob.name} grunts. Progress! ({damage} damage)",
            f"{weapon_name} finds its mark on {mob.name}.\n{heroine.heroine_name} nods, satisfied. ({damage} damage)",
            f"{heroine.heroine_name} swings {weapon_name} competently.\nLook at her, being all professional. ({damage} damage)",
        ]
    
    elif tier == 'good':
        messages = [
            f"{heroine.heroine_name}'s {weapon_name} bites deep into {mob.name}!\nBlood spatters across the dungeon floor. ({damage} damage)",
            f"{heroine.heroine_name} strikes true! {weapon_name} tears through {mob.name}'s defenses.\nThat's going to leave a mark. ({damage} damage)",
            f"{weapon_name} slams into {mob.name} with a satisfying CRUNCH.\n{heroine.heroine_name} grins. \"Felt good.\" ({damage} damage)",
            f"{heroine.heroine_name} puts her weight behind {weapon_name}.\nIt carves a bloody path through {mob.name}. ({damage} damage)",
        ]
    
    elif tier == 'critical':
        messages = [
            f"{heroine.heroine_name}'s {weapon_name} finds a vital spot!\n*CRITICAL HIT!*\n{mob.name}'s arm hangs uselessly, blood pouring from the wound. ({damage} damage)",
            f"{weapon_name} cleaves through {mob.name}'s shoulder with a sickening CRUNCH!\n*CRITICAL HIT!*\nBone splinters. Blood fountains. {mob.name} screams. ({damage} damage)",
            f"{heroine.heroine_name} strikes with deadly precision!\n*CRITICAL HIT!*\n{weapon_name} severs something important. {mob.name}'s leg buckles. ({damage} damage)",
            f"A perfect strike! {heroine.heroine_name}'s {weapon_name} carves a gory path through {mob.name}.\n*CRITICAL HIT!*\nIntestines? Maybe. Hard to tell. ({damage} damage)",
        ]
    
    elif tier == 'devastating':
        messages = [
            f"{heroine.heroine_name} channels every ounce of strength into {weapon_name}!\n*DEVASTATING CRITICAL HIT!*\nThe blade nearly BISECTS {mob.name}! Blood and gore explode everywhere.\n{mob.name} looks down at the ruin of their body in disbelief. ({damage} damage)",
            f"Time seems to slow as {heroine.heroine_name} swings {weapon_name}.\n*DEVASTATING CRITICAL HIT!*\n{mob.name}'s arm separates from their body in a spray of crimson.\nIt lands with a wet THUD several feet away. ({damage} damage)",
            f"{heroine.heroine_name} roars and brings {weapon_name} down like the wrath of an angry god!\n*DEVASTATING CRITICAL HIT!*\n{mob.name}'s skull cracks. Their jaw hangs at an impossible angle.\nThey're still standing. Somehow. ({damage} damage)",
            f"A strike for the history books! {heroine.heroine_name}'s {weapon_name} obliterates {mob.name}!\n*DEVASTATING CRITICAL HIT!*\nRibs shatter. Organs rupture. Blood paints the walls.\n\"Overkill much?\" someone mutters. ({damage} damage)",
        ]
    
    else:
        # Fallback
        messages = [f"{heroine.heroine_name} attacks {mob.name} with {weapon_name}. ({damage} damage)"]
    
    return random.choice(messages)

# ============================================================================
# FLAVOR TEXT GENERATORS - MOB ATTACKING HEROINE
# ============================================================================

def get_attack_flavor_mob_to_heroine(mob, heroine, damage, tier, attack_name="attack"):
    """
    Generate descriptive flavor text for mob attacking heroine.
    
    Args:
        mob: Attacking mob object
        heroine: Target heroine object
        damage: Damage dealt
        tier: Damage tier ('glancing', 'normal', 'good', 'critical', 'devastating')
        attack_name: Name of attack (e.g., "claw", "fireball", "bite")
        
    Returns:
        str: Flavor text description
    """
    
    if tier == 'glancing':
        messages = [
            f"{mob.name}'s {attack_name} barely connects with {heroine.heroine_name}.\nShe sidesteps most of it. Lucky. ({damage} damage)",
            f"{heroine.heroine_name} deflects {mob.name}'s {attack_name} at the last second.\nStill hurts though. ({damage} damage)",
            f"{mob.name} swings wildly. The {attack_name} grazes {heroine.heroine_name}'s armor.\n\"Is that all you've got?\" she taunts. ({damage} damage)",
            f"{heroine.heroine_name} takes a glancing blow from {mob.name}'s {attack_name}.\nHer armor absorbs most of it. ({damage} damage)",
        ]
    
    elif tier == 'normal':
        messages = [
            f"{mob.name}'s {attack_name} strikes {heroine.heroine_name} solidly.\nShe grunts, blood welling from the wound. ({damage} damage)",
            f"{heroine.heroine_name} takes a hit from {mob.name}'s {attack_name}.\nPain flashes across her face. She grits her teeth. ({damage} damage)",
            f"{mob.name} lands a solid blow! The {attack_name} cuts into {heroine.heroine_name}.\n\"Ow,\" she says, unhelpfully. ({damage} damage)",
            f"{heroine.heroine_name} staggers as {mob.name}'s {attack_name} finds its mark.\nBlood trickles down her arm. ({damage} damage)",
        ]
    
    elif tier == 'good':
        messages = [
            f"{mob.name}'s {attack_name} SLAMS into {heroine.heroine_name} with brutal force!\nHer armor dents. Ribs crack. She gasps for air. ({damage} damage)",
            f"{heroine.heroine_name} takes a vicious hit from {mob.name}'s {attack_name}!\nBlood sprays as she's knocked backward, barely keeping her footing. ({damage} damage)",
            f"{mob.name}'s {attack_name} tears through {heroine.heroine_name}'s defenses!\nFlesh rips. Blood flows freely. She cries out in pain. ({damage} damage)",
            f"A devastating blow! {mob.name}'s {attack_name} crushes into {heroine.heroine_name}.\nShe doubles over, coughing blood. ({damage} damage)",
        ]
    
    elif tier == 'critical':
        messages = [
            f"{mob.name}'s {attack_name} finds a gap in {heroine.heroine_name}'s armor!\n*CRITICAL HIT!*\nThe strike pierces deep. Blood pours from the wound. She screams. ({damage} damage)",
            f"{heroine.heroine_name} tries to dodge, but {mob.name} is faster!\n*CRITICAL HIT!*\nThe {attack_name} rakes across her chest, shredding flesh and cloth.\nShe crumples, gasping. ({damage} damage)",
            f"{mob.name} strikes with terrifying precision!\n*CRITICAL HIT!*\nThe {attack_name} shatters {heroine.heroine_name}'s shoulder. Bone cracks audibly.\nHer weapon arm hangs limp. ({damage} damage)",
            f"A perfect strike! {mob.name}'s {attack_name} crushes into {heroine.heroine_name}!\n*CRITICAL HIT!*\nShe's thrown backward, blood streaming from multiple wounds.\n\"That... really hurt...\" she whimpers. ({damage} damage)",
        ]
    
    elif tier == 'devastating':
        messages = [
            f"{mob.name} unleashes a BRUTAL {attack_name}!\n*DEVASTATING CRITICAL HIT!*\n{heroine.heroine_name} is hurled through the air like a ragdoll!\nShe hits the wall with a sickening CRACK. Blood pools beneath her.\nShe's not getting up. ({damage} damage)",
            f"Time slows as {mob.name}'s {attack_name} connects with {heroine.heroine_name}!\n*DEVASTATING CRITICAL HIT!*\nHer armor shatters. Ribs splinter. Blood erupts from her mouth.\nShe collapses in a broken heap. ({damage} damage)",
            f"{mob.name} roars and delivers a killing blow!\n*DEVASTATING CRITICAL HIT!*\nThe {attack_name} nearly cleaves {heroine.heroine_name} in two!\nShe drops like a puppet with cut strings, unconscious before she hits the ground. ({damage} damage)",
            f"A strike of absolute carnage! {mob.name}'s {attack_name} obliterates {heroine.heroine_name}!\n*DEVASTATING CRITICAL HIT!*\nBones shatter. Organs rupture. She doesn't even have time to scream.\nShe's down. ({damage} damage)",
        ]
    
    else:
        # Fallback
        messages = [f"{mob.name} hits {heroine.heroine_name} with {attack_name}. ({damage} damage)"]
    
    return random.choice(messages)

# ============================================================================
# SPECIAL MOB BEHAVIORS
# ============================================================================

def get_silent_mob_action(mob, action_type="attack"):
    """
    Generate flavor text for silent/incomprehensible mobs.
    
    Args:
        mob: The silent mob
        action_type: Type of action ('attack', 'move', 'special')
        
    Returns:
        str: Atmospheric description
    """
    
    if action_type == "attack":
        messages = [
            f"{mob.name} advances silently. No sound. No warning.\nJust violence.",
            f"{mob.name} makes no sound as it strikes.\nThe silence is somehow worse than screaming.",
            f"{mob.name} moves with eerie quiet.\nNo battlecry. No threat. Just death.",
        ]
    elif action_type == "move":
        messages = [
            f"{mob.name} shifts position. Silent. Unreadable.",
            f"{mob.name} moves without sound. Its intentions are a mystery.",
            f"The {mob.name} repositions. No one knows what it's thinking.",
        ]
    else:
        messages = [
            f"{mob.name} does... something. Hard to say what.",
            f"The {mob.name} acts. Your guess is as good as anyone's.",
        ]
    
    return random.choice(messages)

def get_foreign_language_mob_speech(mob, context="attack"):
    """
    Generate incomprehensible foreign language speech from mobs.
    Heroines react based on body language and context.
    
    Args:
        mob: The speaking mob
        context: Situation context ('attack', 'angry', 'wounded', 'victory')
        
    Returns:
        tuple: (mob speech, heroine reaction template)
    """
    
    if context == "attack":
        speeches = [
            "K'THAK SHRII VENNA!",
            "GRAK'TAR MOSH!",
            "ZUL'THAX KREE!",
            "VOSH'NAK TERRA!",
        ]
        reactions = [
            "\"I think it just insulted my mother?\" {heroine} mutters.",
            "{heroine} narrows her eyes. \"That sounded aggressive.\"",
            "\"No idea what that means, but I don't like the tone,\" {heroine} says.",
            "{heroine} shrugs. \"Angry gibberish. Got it.\"",
        ]
    
    elif context == "angry":
        speeches = [
            "SHRAK'TAL VOSS KREEN!",
            "MAL'GORATH THUN!",
            "KRESH'VA DOOM!",
        ]
        reactions = [
            "{heroine} winces. \"Yeah, that one's definitely mad.\"",
            "\"I don't speak whatever that is, but it sounds upset,\" {heroine} observes.",
            "{heroine} takes a defensive stance. \"Angry noises are never good.\"",
        ]
    
    elif context == "wounded":
        speeches = [
            "Greth... nak... vosh...",
            "K'ree... shaal...",
            "Mosh... thara...",
        ]
        reactions = [
            "\"Is it... dying? Or cursing us? Both?\" {heroine} wonders.",
            "{heroine} frowns. \"That sounded pained. Good.\"",
            "\"Keep hitting it. Whatever it's saying, I don't care,\" {heroine} says coldly.",
        ]
    
    elif context == "victory":
        speeches = [
            "KRESH VALLA THOOM!",
            "GRAK'TAR SHEEN!",
            "MAL'GOTH REEN!",
        ]
        reactions = [
            "{heroine} scowls. \"I think it's... celebrating? Rude.\"",
            "\"Did it just laugh at us?\" {heroine} growls.",
            "{heroine} glares. \"Whatever it said, we're making it regret that.\"",
        ]
    
    else:
        speeches = ["Vosh kree tal."]
        reactions = ["{heroine} shrugs. \"No clue.\""]
    
    speech = random.choice(speeches)
    reaction_template = random.choice(reactions)
    
    return speech, reaction_template

# ============================================================================
# INITIATIVE / TURN ORDER SYSTEM
# ============================================================================

def calculate_initiative(combatants, surprise_factor=0):
    """
    Calculate turn order based on speed + random roll + surprise.
    
    Args:
        combatants: List of all combatants (heroes and mobs)
        surprise_factor: Modifier for surprise (-5 to +5, applied to one side)
        
    Returns:
        list: Sorted list of combatants by initiative (highest first)
    """
    initiative_rolls = []
    
    for combatant in combatants:
        # Base initiative = speed stat + d20 roll
        base_roll = combatant.stats['speed'] + roll_d20()
        
        # Apply surprise factor if applicable
        # (You'll set this per encounter - positive favors heroes, negative favors mobs)
        initiative_score = base_roll + surprise_factor
        
        initiative_rolls.append({
            'combatant': combatant,
            'initiative': initiative_score,
            'name': combatant.name if hasattr(combatant, 'name') else combatant.heroine_name
        })
    
    # Sort by initiative (highest goes first)
    initiative_rolls.sort(key=lambda x: x['initiative'], reverse=True)
    
    return initiative_rolls

def display_initiative_order(initiative_list):
    """
    Display the turn order to player.
    
    Args:
        initiative_list: Sorted initiative list from calculate_initiative()
    """
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}TURN ORDER:")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    for i, entry in enumerate(initiative_list, 1):
        combatant = entry['combatant']
        initiative = entry['initiative']
        
        # Color code: Green for heroes, Red for mobs
        if hasattr(combatant, 'hero_class'):  # It's a hero
            color = Fore.GREEN
            type_label = f"[{combatant.hero_class}]"
            name = combatant.heroine_name
        else:  # It's a mob
            color = Fore.RED
            type_label = f"[{combatant.mob_class}]"
            name = combatant.name
        
        print(f"{color}{i}. {name} {type_label} - Initiative: {initiative}{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

# ============================================================================
# COMBAT STATUS DISPLAY (ENHANCED VERSION)
# ============================================================================

def display_combat_status(heroes, mobs):
    """
    Show current HP and status of all combatants.
    
    Args:
        heroes: List of hero objects
        mobs: List of mob objects
    """
    print(f"\n{Fore.YELLOW}{'='*60}")
    print(f"{Fore.YELLOW}COMBAT STATUS:")
    print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
    
    # Display Heroes
    print(f"{Fore.GREEN}HEROES:{Style.RESET_ALL}")
    for hero in heroes:
        if hero.health > 0:
            hp_percent = (hero.health / hero.starting_health) * 100
            
            # Color code HP bar
            if hp_percent > 60:
                hp_color = Fore.GREEN
            elif hp_percent > 30:
                hp_color = Fore.YELLOW
            else:
                hp_color = Fore.RED
            
            print(f"  {hero.heroine_name} [{hero.hero_class}]: {hp_color}{int(hero.health)}/{hero.starting_health} HP{Style.RESET_ALL}")
        else:
            print(f"  {hero.heroine_name} [{hero.hero_class}]: {Fore.RED}UNCONSCIOUS{Style.RESET_ALL}")
    
    # Display Mobs
    print(f"\n{Fore.RED}ENEMIES:{Style.RESET_ALL}")
    for mob in mobs:
        if mob.health > 0:
            hp_percent = (mob.health / mob.starting_health) * 100
            
            # Color code HP bar
            if hp_percent > 60:
                hp_color = Fore.GREEN
            elif hp_percent > 30:
                hp_color = Fore.YELLOW
            else:
                hp_color = Fore.RED
            
            status = ""
            if hasattr(mob, 'enraged') and mob.enraged:
                status = f" {Fore.MAGENTA}[ENRAGED!]{Style.RESET_ALL}"
            
            print(f"  {mob.name} [{mob.mob_class}]: {hp_color}{int(mob.health)}/{mob.starting_health} HP{Style.RESET_ALL}{status}")
        else:
            print(f"  {mob.name} [{mob.mob_class}]: {Fore.RED}DEFEATED{Style.RESET_ALL}")
    
    print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}\n")

# ============================================================================
# HAPPY'S RESURRECTION SCENE
# ============================================================================

def happy_resurrection_scene(heroes):
    """
    Happy's emotional breakdown and resurrection of the party.
    Purple haze, lightning, tears, and rewards!
    
    Args:
        heroes: List of all hero objects (all unconscious)
    """
    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}SOMETHING UNEXPECTED HAPPENS...{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.CYAN}Happy stands over the fallen heroines, his massive warhammer dripping with blood.")
    print(f"The dungeon is silent except for his heavy breathing.{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.CYAN}He looks down at the bodies. His shoulders slump.{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f'\n{Fore.YELLOW}Happy: "...not again."{Style.RESET_ALL}\n')
    
    input("Press Enter to continue...")
    
    print(f'\n{Fore.YELLOW}Happy: "I\'m so... so tired of this."{Style.RESET_ALL}')
    print(f"{Fore.CYAN}His voice cracks. The fierce dwarf warrior begins to tremble.{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f'\n{Fore.YELLOW}Happy: "Every day. EVERY. DAMN. DAY. He makes me do this!"{Style.RESET_ALL}')
    print(f'{Fore.YELLOW}Happy: "\'Guard the dungeon, Happy.\' \'Kill the intruders, Happy.\'"')
    print(f'{Fore.YELLOW}Happy: "I didn\'t ask for this! I just wanted to mine some bloody ore!"{Style.RESET_ALL}\n')
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.CYAN}A single tear rolls down Happy's blood-splattered cheek.{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Then another.{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Then he's openly weeping.{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f'\n{Fore.YELLOW}Happy (sobbing): "I\'m sorry! I\'m so, so sorry!"{Style.RESET_ALL}')
    print(f'{Fore.YELLOW}Happy: "You seem like nice lasses! You don\'t deserve this!"{Style.RESET_ALL}')
    print(f'{Fore.YELLOW}Happy: "None of them do! But what choice do I have?!"{Style.RESET_ALL}\n')
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.CYAN}Happy wipes his eyes with a meaty fist and raises his hands.{Style.RESET_ALL}")
    print(f'{Fore.CYAN}He begins chanting in ancient Dwarvish.{Style.RESET_ALL}\n')
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.MAGENTA}A purple haze begins to swirl around each fallen heroine.{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}Crackling energy fills the air. Small lightning bolts dance across their bodies.{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}The smell of ozone and magic permeates the dungeon.{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.MAGENTA}*CRACK* *FZZZT* *BOOM*{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.GREEN}Wounds close. Bones mend. Color returns to pale faces.{Style.RESET_ALL}")
    print(f"{Fore.GREEN}One by one, the heroines gasp back to life!{Style.RESET_ALL}\n")
    
    # Resurrect all heroes to full HP
    for hero in heroes:
        hero.health = hero.starting_health
        print(f"{Fore.GREEN}{hero.heroine_name} opens her eyes, fully healed!{Style.RESET_ALL}")
    
    input("\nPress Enter to continue...")
    
    print(f'\n{Fore.YELLOW}Happy (sniffling): "There. Good as new."{Style.RESET_ALL}')
    print(f'{Fore.YELLOW}Happy: "Now get out of here before HE notices I did that."{Style.RESET_ALL}\n')
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.CYAN}Happy's demeanor suddenly shifts. The tears stop.{Style.RESET_ALL}")
    print(f"{Fore.CYAN}A genuine smile spreads across his face.{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f'\n{Fore.YELLOW}Happy: "You know what? You lasses fought well!"{Style.RESET_ALL}')
    print(f'{Fore.YELLOW}Happy: "Better than most! Here, take these. You\'ve earned them!"{Style.RESET_ALL}\n')
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.CYAN}Happy tosses each heroine a small pouch of coins and some equipment.{Style.RESET_ALL}")
    print(f'{Fore.CYAN}He winks.{Style.RESET_ALL}\n')
    
    print(f'\n{Fore.YELLOW}Happy: "Next time, hit me harder! Maybe you\'ll actually win!"{Style.RESET_ALL}')
    print(f'{Fore.YELLOW}Happy: "Now scram! And remember - you didn\'t see me cry!"{Style.RESET_ALL}\n')
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.MAGENTA}{'='*60}")
    print(f"{Fore.MAGENTA}RESURRECTION COMPLETE!{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}All heroines restored to full health!{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}\n")

# ============================================================================
# POST-COMBAT REWARDS
# ============================================================================

def apply_stat_increases(heroes):
    """
    Apply random stat increases to heroines after Happy's resurrection.
    Each heroine gets 1-3 random stat improvements, weighted toward their class specialty.
    
    Args:
        heroes: List of hero objects
    """
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}HAPPY'S GIFTS - STAT INCREASES!{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    stat_categories = {
        'Warrior': ['toughness', 'parry', 'crit', 'expertise'],
        'Shifter': ['dodge', 'speed', 'crit', 'luck'],
        'Battle_Mage': ['expertise', 'luck', 'crit_mult', 'toughness'],
        'Hunter': ['crit', 'crit_mult', 'dodge', 'speed'],
        'Wizard': ['expertise', 'luck', 'crit_mult', 'toughness'],
        'Sapper': ['expertise', 'crit', 'dodge', 'luck'],
        'Cleric': ['heal', 'aoe_heal', 'toughness', 'fear'],
    }
    
    for hero in heroes:
        num_increases = random.randint(1, 3)
        hero_class = hero.hero_class
        
        print(f"{Fore.GREEN}{hero.heroine_name} receives {num_increases} stat improvement(s):{Style.RESET_ALL}")
        
        # Get weighted stat pool for this class
        preferred_stats = stat_categories.get(hero_class, ['luck', 'toughness', 'dodge', 'fear'])
        
        for i in range(num_increases):
            # 70% chance to improve class specialty, 30% chance any stat
            if random.randint(1, 100) <= 70:
                stat_to_increase = random.choice(preferred_stats)
            else:
                # Any stat
                all_stats = ['crit', 'crit_mult', 'luck', 'expertise', 'toughness', 
                            'dodge', 'parry', 'fear', 'speed']
                stat_to_increase = random.choice(all_stats)
            
            # Determine increase amount based on stat type
            if stat_to_increase == 'crit_mult':
                increase = round(random.uniform(0.05, 0.15), 2)
            elif stat_to_increase in ['heal', 'aoe_heal']:
                increase = random.randint(1, 3)
            else:
                increase = random.randint(1, 2)
            
            # Apply the increase
            old_value = hero.stats[stat_to_increase]
            hero.stats[stat_to_increase] += increase
            new_value = hero.stats[stat_to_increase]
            
            print(f"  • {stat_to_increase}: {old_value} → {Fore.YELLOW}{new_value}{Style.RESET_ALL} (+{increase})")
        
        print()
    
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    input("Press Enter to continue...")

def apply_loot_rewards(heroes):
    """
    Give gold/items to heroines after Happy's resurrection.
    
    Args:
        heroes: List of hero objects
    """
    print(f"\n{Fore.YELLOW}{'='*60}")
    print(f"{Fore.YELLOW}HAPPY'S GIFTS - LOOT!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}\n")
    
    for hero in heroes:
        gold_reward = random.randint(50, 150)
        hero.gold += gold_reward
        
        print(f"{Fore.GREEN}{hero.heroine_name} receives {Fore.YELLOW}{gold_reward} gold!{Style.RESET_ALL}")
        print(f"  Total gold: {Fore.YELLOW}{hero.gold}{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}{'='*60}{Style.RESET_ALL}\n")
    input("Press Enter to continue...")

# ============================================================================
# COMBAT VICTORY/DEFEAT CHECKS
# ============================================================================

def check_party_wipe(heroes):
    """
    Check if all heroines are unconscious.
    
    Args:
        heroes: List of hero objects
        
    Returns:
        bool: True if all heroes are at 0 HP
    """
    return all(hero.health <= 0 for hero in heroes)

def check_mob_defeat(mobs):
    """
    Check if all mobs are defeated.
    
    Args:
        mobs: List of mob objects
        
    Returns:
        bool: True if all mobs are at 0 HP
    """
    return all(mob.health <= 0 for mob in mobs)

def check_happy_enrage(happy_mob):
    """
    Check if Happy should enter enraged state.
    
    Args:
        happy_mob: The Happy mob object
        
    Returns:
        bool: True if Happy should enrage
    """
    if hasattr(happy_mob, 'enraged') and happy_mob.enraged:
        return False  # Already enraged
    
    # Enrage at 50% HP
    hp_percent = (happy_mob.health / happy_mob.starting_health) * 100
    
    if hp_percent <= 50:
        return True
    
    return False

def trigger_happy_enrage(happy_mob):
    """
    Trigger Happy's enrage transformation.
    Updates stats to enraged values.
    
    Args:
        happy_mob: The Happy mob object
    """
    print(f"\n{Fore.RED}{'='*60}")
    print(f"{Fore.RED}{'='*60}")
    print(f"{Fore.RED}SOMETHING TERRIBLE IS HAPPENING...{Style.RESET_ALL}")
    print(f"{Fore.RED}{'='*60}")
    print(f"{Fore.RED}{'='*60}{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.CYAN}Happy staggers backward, clutching his wounds.{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Blood drips from dozens of cuts.{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f'\n{Fore.YELLOW}Happy: "Ow. OW. That... that actually hurt."{Style.RESET_ALL}\n')
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.CYAN}His breathing becomes ragged. His eyes begin to glow red.{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f'\n{Fore.RED}Happy: "You know what? I\'m TIRED of holding back!"{Style.RESET_ALL}')
    print(f'{Fore.RED}Happy: "I\'m TIRED of being nice!"{Style.RESET_ALL}')
    print(f'{Fore.RED}Happy: "I\'m TIRED OF THIS JOB!"{Style.RESET_ALL}\n')
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.RED}Happy throws his head back and ROARS!{Style.RESET_ALL}")
    print(f"{Fore.RED}The entire dungeon shakes!{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f"\n{Fore.MAGENTA}Dark energy erupts from Happy's body!{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}His muscles bulge. His wounds close. His warhammer crackles with power!{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")
    
    print(f'\n{Fore.RED}Happy (voice distorted): "LET\'S SEE HOW YOU HANDLE THIS!"{Style.RESET_ALL}\n')
    
    input("Press Enter to continue...")
    
    # Apply enraged stats
    happy_mob.enraged = True
    happy_mob.starting_health = happy_mob.stats['enraged_hp']
    happy_mob.health = happy_mob.stats['enraged_hp']  # Full heal on enrage
    
    # Update combat stats to enraged versions
    happy_mob.stats['turn'] = happy_mob.stats['enraged_turn']
    happy_mob.stats['crit'] = happy_mob.stats['enraged_crit']
    happy_mob.stats['crit_chance'] = happy_mob.stats['enraged_crit_chance']
    happy_mob.stats['miss'] = happy_mob.stats['enraged_miss']
    happy_mob.stats['luck'] = happy_mob.stats['enraged_luck']
    happy_mob.stats['expertise'] = happy_mob.stats['enraged_expertise']
    happy_mob.stats['toughness'] = happy_mob.stats['enraged_toughness']
    happy_mob.stats['dodge'] = happy_mob.stats['enraged_dodge']
    happy_mob.stats['healing_chance'] = happy_mob.stats['enraged_healing_chance']
    happy_mob.stats['healing'] = happy_mob.stats['enraged_healing']
    happy_mob.stats['scare'] = happy_mob.stats['enraged_scare']
    
    print(f"\n{Fore.RED}{'='*60}")
    print(f"{Fore.RED}HAPPY HAS ENTERED ENRAGED MODE!{Style.RESET_ALL}")
    print(f"{Fore.RED}HP: {happy_mob.health}/{happy_mob.starting_health}{Style.RESET_ALL}")
    print(f"{Fore.RED}All stats dramatically increased!{Style.RESET_ALL}")
    print(f"{Fore.RED}{'='*60}{Style.RESET_ALL}\n")
    
    input("Press Enter to continue...")

# ============================================================================
# HEROINE REACTION TO FOREIGN SPEECH (HELPER)
# ============================================================================

def display_foreign_speech_with_reaction(mob, context, random_heroine):
    """
    Display mob's foreign speech and a heroine's confused reaction.
    
    Args:
        mob: The speaking mob
        context: Speech context ('attack', 'angry', 'wounded', 'victory')
        random_heroine: A random heroine from the party to react
    """
    speech, reaction_template = get_foreign_language_mob_speech(mob, context)
    
    print(f"\n{Fore.RED}{mob.name}: \"{speech}\"{Style.RESET_ALL}")
    
    reaction = reaction_template.format(heroine=random_heroine.heroine_name)
    print(f"{Fore.CYAN}{reaction}{Style.RESET_ALL}\n")

# ============================================================================
# DODGE/PARRY FLAVOR TEXT
# ============================================================================

def get_dodge_flavor(heroine, mob):
    """Generate flavor text for successful dodge."""
    messages = [
        f"{heroine.heroine_name} twists aside at the last second! {mob.name}'s attack misses completely.",
        f"{heroine.heroine_name} ducks under {mob.name}'s swing with a grin. \"Too slow!\"",
        f"{mob.name} lunges, but {heroine.heroine_name} sidesteps gracefully. \"Missed me!\"",
        f"{heroine.heroine_name} rolls out of the way. {mob.name}'s attack hits nothing but air.",
    ]
    return random.choice(messages)

def get_parry_flavor(heroine, mob):
    """Generate flavor text for successful parry."""
    messages = [
        f"{heroine.heroine_name} deflects {mob.name}'s attack with her weapon! Sparks fly!",
        f"CLANG! {heroine.heroine_name} parries {mob.name}'s strike perfectly.",
        f"{heroine.heroine_name} blocks {mob.name}'s attack and counters with a shove. \"Not today!\"",
        f"{mob.name}'s weapon bounces off {heroine.heroine_name}'s guard. She smirks.",
    ]
    return random.choice(messages)

def get_miss_flavor(attacker, target):
    """Generate flavor text for missed attack."""
    messages = [
        f"{attacker.name if hasattr(attacker, 'name') else attacker.heroine_name} swings wildly and misses!",
        f"{attacker.name if hasattr(attacker, 'name') else attacker.heroine_name}'s attack goes wide. Embarrassing.",
        f"{attacker.name if hasattr(attacker, 'name') else attacker.heroine_name} completely whiffs the attack. Oops.",
        f"{attacker.name if hasattr(attacker, 'name') else attacker.heroine_name} stumbles mid-attack. The strike misses entirely.",
    ]
    return random.choice(messages)

# ============================================================================
# HEALING FLAVOR TEXT
# ============================================================================

def get_healing_flavor(healer, target, amount):
    """
    Generate flavor text for healing actions.
    
    Args:
        healer: The one doing the healing (heroine or mob)
        target: The one being healed
        amount: HP restored
        
    Returns:
        str: Healing flavor text
    """
    if hasattr(healer, 'hero_class'):  # Heroine healing
        messages = [
            f"{healer.heroine_name} channels healing magic into {target.heroine_name}!\nWounds close. Strength returns. (+{amount} HP)",
            f"{healer.heroine_name} mutters a prayer. Golden light surrounds {target.heroine_name}.\nFlesh mends. Pain fades. (+{amount} HP)",
            f"{healer.heroine_name} places her hands on {target.heroine_name}.\nWarm energy flows. Injuries heal. (+{amount} HP)",
        ]
    else:  # Mob healing
        messages = [
            f"{healer.name} growls and regenerates! Wounds seal with sickening speed. (+{amount} HP)",
            f"Dark energy swirls around {healer.name}. Flesh knits back together. (+{amount} HP)",
            f"{healer.name} channels unholy power! Injuries close with a wet, squelching sound. (+{amount} HP)",
        ]
    
    return random.choice(messages)

def get_aoe_healing_flavor(healer, targets, amount):
    """
    Generate flavor text for area-of-effect healing.
    
    Args:
        healer: The heroine doing the healing
        targets: List of heroines being healed
        amount: HP restored to each
        
    Returns:
        str: AOE healing flavor text
    """
    messages = [
        f"{healer.heroine_name} raises her hands and shouts a prayer!\nRadiant light explodes outward, washing over the entire party!\nWounds close. Strength returns to all! (+{amount} HP to all)",
        f"{healer.heroine_name} slams her staff into the ground!\nA wave of golden energy ripples through the party!\nEveryone feels their injuries healing! (+{amount} HP to all)",
        f"{healer.heroine_name} channels divine power!\nA warm glow envelops each heroine!\nPain fades. Hope returns! (+{amount} HP to all)",
    ]
    
    return random.choice(messages)

# ============================================================================
# PLAYER ACTION SYSTEM
# ============================================================================

def display_action_menu(hero, mobs):
    """
    Display available actions for a hero's turn.
    
    Args:
        hero: The hero taking their turn
        mobs: List of available enemy targets
        
    Returns:
        None (displays menu)
    """
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{hero.heroine_name.upper()}'S TURN [{hero.hero_class}]")
    print(f"HP: {hero.health}/{hero.starting_health}")
    
    # Show abilities if any
    abilities = hero.get_all_abilities()
    if abilities:
        print(f"Abilities: {', '.join(abilities)}")
    
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    print(f"{Fore.YELLOW}Choose Action:{Style.RESET_ALL}")
    print(f"  1. Attack (Choose target)")
    print(f"  2. Defend (Increase dodge/parry this turn)")
    print(f"  3. Special Ability")
    print(f"  4. Use Item (Not implemented yet)")
    print()

def get_player_action_choice():
    """
    Get player's action choice.
    
    Returns:
        int: Action choice (1-4) or None if invalid
    """
    while True:
        try:
            choice = input(f"{Fore.GREEN}Enter choice (1-4): {Style.RESET_ALL}").strip()
            
            if not choice:
                continue
            
            choice_num = int(choice)
            
            if choice_num < 1 or choice_num > 4:
                print(f"{Fore.RED}Please enter a number between 1 and 4.{Style.RESET_ALL}")
                continue
            
            return choice_num
            
        except ValueError:
            print(f"{Fore.RED}Please enter a valid number.{Style.RESET_ALL}")
            continue

def display_target_menu(mobs):
    """
    Display available enemy targets.
    
    Args:
        mobs: List of mob objects
        
    Returns:
        None (displays menu)
    """
    print(f"\n{Fore.YELLOW}Choose Target:{Style.RESET_ALL}")
    
    for i, mob in enumerate(mobs, 1):
        status = ""
        if hasattr(mob, 'enraged') and mob.enraged:
            status = f" {Fore.RED}[ENRAGED!]{Style.RESET_ALL}"
        
        print(f"  {i}. {mob.name} [HP: {mob.health}/{mob.starting_health}]{status}")
    
    print()

def get_target_choice(mobs):
    """
    Get player's target choice.
    
    Args:
        mobs: List of available targets
        
    Returns:
        Mob object or None if invalid
    """
    while True:
        try:
            choice = input(f"{Fore.GREEN}Enter target (1-{len(mobs)}): {Style.RESET_ALL}").strip()
            
            if not choice:
                continue
            
            choice_num = int(choice)
            
            if choice_num < 1 or choice_num > len(mobs):
                print(f"{Fore.RED}Please enter a number between 1 and {len(mobs)}.{Style.RESET_ALL}")
                continue
            
            return mobs[choice_num - 1]
            
        except ValueError:
            print(f"{Fore.RED}Please enter a valid number.{Style.RESET_ALL}")
            continue

def display_ability_menu(hero):
    """
    Display available special abilities.
    
    Args:
        hero: The hero choosing an ability
        
    Returns:
        None (displays menu)
    """
    abilities = hero.get_all_abilities()
    
    print(f"\n{Fore.YELLOW}Available Abilities:{Style.RESET_ALL}")
    
    for i, ability in enumerate(abilities, 1):
        # Check if on cooldown
        can_use, reason = hero.can_use_ability(ability)
        
        status = ""
        if not can_use:
            status = f" {Fore.RED}[{reason}]{Style.RESET_ALL}"
        
        # Get ability description
        description = get_ability_description(ability)
        
        print(f"  {i}. {ability} - {description}{status}")
    
    print(f"  0. Cancel")
    print()

def get_ability_description(ability_name):
    """
    Get description text for an ability.
    
    Args:
        ability_name: Name of the ability
        
    Returns:
        str: Description text
    """
    descriptions = {
        'Power Strike': '2x damage, -5 accuracy',
        'Heal': 'Restore HP to an ally',
        'AOE Heal': 'Restore HP to entire party',
    }
    
    return descriptions.get(ability_name, 'Unknown ability')

def get_ability_choice(hero):
    """
    Get player's ability choice.
    
    Args:
        hero: The hero choosing an ability
        
    Returns:
        str: Ability name, or None if cancelled
    """
    abilities = hero.get_all_abilities()
    
    while True:
        try:
            choice = input(f"{Fore.GREEN}Enter ability (0-{len(abilities)}): {Style.RESET_ALL}").strip()
            
            if not choice:
                continue
            
            choice_num = int(choice)
            
            if choice_num == 0:
                return None  # Cancelled
            
            if choice_num < 0 or choice_num > len(abilities):
                print(f"{Fore.RED}Please enter a number between 0 and {len(abilities)}.{Style.RESET_ALL}")
                continue
            
            ability = abilities[choice_num - 1]
            
            # Check if can use
            can_use, reason = hero.can_use_ability(ability)
            if not can_use:
                print(f"{Fore.RED}{reason}{Style.RESET_ALL}")
                continue
            
            return ability
            
        except ValueError:
            print(f"{Fore.RED}Please enter a valid number.{Style.RESET_ALL}")
            continue

# ============================================================================
# ABILITY EXECUTION FUNCTIONS
# ============================================================================

def execute_ability(hero, ability_name, target, all_heroes, all_mobs):
    """
    Execute a special ability.
    
    Args:
        hero: The hero using the ability
        ability_name: Name of ability to use
        target: Target of ability (can be hero or mob)
        all_heroes: List of all heroes (for AOE heals)
        all_mobs: List of all mobs (for AOE attacks later)
        
    Returns:
        bool: True if ability was executed successfully
    """
    # Route to appropriate ability function
    if ability_name == 'Power Strike':
        return execute_power_strike(hero, target)
    elif ability_name == 'Heal':
        return execute_heal(hero, target)
    elif ability_name == 'AOE Heal':
        return execute_aoe_heal(hero, all_heroes)
    else:
        print(f"{Fore.RED}Unknown ability: {ability_name}{Style.RESET_ALL}")
        return False

def execute_power_strike(hero, target):
    """
    Execute Power Strike ability.
    2x damage, -5 accuracy penalty
    
    Args:
        hero: Attacking hero
        target: Target mob
        
    Returns:
        bool: True if executed
    """
    print(f"\n{Fore.YELLOW}⚔️  {hero.heroine_name} winds up for a POWER STRIKE! ⚔️{Style.RESET_ALL}")
    time.sleep(0.5)
    
    # Get hero's attack rolls
    hero_rolls = get_heroine_rolls(hero)
    
    # Apply -5 accuracy penalty to expertise roll
    hit_roll = hero_rolls['expertise_roll'] - 5
    
    # Get target's defense rolls
    target_rolls = get_mob_rolls(target)
    
    # Check if attack hits (must beat both dodge and parry)
    if not check_hit(hit_roll, target_rolls['dodge_roll'], target_rolls['parry_roll']):
        miss_flavor = get_miss_flavor(hero, target)
        print(f"{Fore.CYAN}{miss_flavor}{Style.RESET_ALL}")
        time.sleep(0.5)
        return True
    
    # Calculate damage with 2x multiplier
    base_damage = calculate_damage(
        hero_rolls['damage_roll'],
        hero.stats,
        hero_rolls['crit_success'],
        hero_rolls['crit_mult']
    )
    
    # Apply Power Strike 2x multiplier
    damage = int(base_damage * 2)
    
    # Apply damage
    target.health -= damage
    
    # Flavor text
    if hero_rolls['crit_success']:
        print(f"{Fore.RED}💥 CRITICAL POWER STRIKE! 💥{Style.RESET_ALL}")
    
    hit_flavor = get_hit_flavor(hero, target, damage, hero_rolls['crit_success'])
    print(f"{Fore.GREEN}{hit_flavor}{Style.RESET_ALL}")
    time.sleep(0.5)
    
    if target.health <= 0:
        print(f"{Fore.YELLOW}☠️  {target.name} has been defeated! ☠️{Style.RESET_ALL}")
        time.sleep(0.5)
    
    return True

def execute_heal(hero, target):
    """
    Execute Heal ability.
    Restores HP to a single target.
    
    Args:
        hero: Hero casting heal
        target: Target hero to heal
        
    Returns:
        bool: True if executed
    """
    # Get hero's heal roll
    hero_rolls = get_heroine_rolls(hero)
    heal_roll = hero_rolls['heal_roll']
    
    # Add heal stat
    total_heal = heal_roll + hero.stats.get('heal', 0)
    
    if total_heal <= 0:
        print(f"{Fore.RED}{hero.heroine_name} doesn't have healing power!{Style.RESET_ALL}")
        return False
    
    # Apply healing
    old_health = target.health
    target.health = min(target.health + total_heal, target.starting_health)
    actual_heal = target.health - old_health
    
    # Flavor text
    print(f"\n{Fore.CYAN}✨ {hero.heroine_name} channels healing energy into {target.heroine_name}! ✨{Style.RESET_ALL}")
    time.sleep(0.5)
    print(f"{Fore.GREEN}{target.heroine_name} recovers {actual_heal} HP!{Style.RESET_ALL}")
    time.sleep(0.5)
    
    if target.health >= target.starting_health:
        print(f"{Fore.YELLOW}{target.heroine_name} is at full health!{Style.RESET_ALL}")
        time.sleep(0.5)
    
    return True

def execute_aoe_heal(hero, all_heroes):
    """
    Execute AOE Heal ability.
    Restores HP to entire party.
    
    Args:
        hero: Hero casting AOE heal
        all_heroes: List of all heroes in party
        
    Returns:
        bool: True if executed
    """
    # Get hero's aoe_heal roll
    hero_rolls = get_heroine_rolls(hero)
    heal_roll = hero_rolls['aoe_heal_roll']
    
    # Add aoe_heal stat
    total_heal = heal_roll + hero.stats.get('aoe_heal', 0)
    
    if total_heal <= 0:
        print(f"{Fore.RED}{hero.heroine_name} doesn't have AOE healing power!{Style.RESET_ALL}")
        return False
    
    print(f"\n{Fore.CYAN}✨✨ {hero.heroine_name} releases a wave of healing energy! ✨✨{Style.RESET_ALL}")
    time.sleep(0.5)
    
    # Heal all living heroes
    for target in all_heroes:
        if target.health > 0:
            old_health = target.health
            target.health = min(target.health + total_heal, target.starting_health)
            actual_heal = target.health - old_health
            
            if actual_heal > 0:
                print(f"{Fore.GREEN}{target.heroine_name} recovers {actual_heal} HP!{Style.RESET_ALL}")
                time.sleep(0.3)
    
    return True

def execute_defend(hero):
    """
    Execute Defend action.
    Increases dodge and parry for this turn.
    
    Args:
        hero: Hero taking defensive stance
        
    Returns:
        bool: True if executed
    """
    print(f"\n{Fore.CYAN}{hero.heroine_name} takes a defensive stance!{Style.RESET_ALL}")
    
    # Apply temporary defensive bonus
    # We'll track this with a flag
    hero.is_defending = True
    hero.defend_bonus = 5
    
    print(f"{Fore.GREEN}Dodge and Parry increased by {hero.defend_bonus} for this turn!{Style.RESET_ALL}")
    
    return True

def clear_defend_status(hero):
    """
    Clear defend status at end of turn.
    
    Args:
        hero: Hero to clear status from
    """
    if hasattr(hero, 'is_defending'):
        hero.is_defending = False
        hero.defend_bonus = 0

# ============================================================================
# COMBAT RESOLUTION FUNCTIONS
# ============================================================================

def check_hit(attacker_expertise_roll, defender_dodge_roll, defender_parry_roll):
    """
    Check if an attack hits the target.
    
    Args:
        attacker_expertise_roll: Attacker's expertise roll value
        defender_dodge_roll: Defender's dodge roll value
        defender_parry_roll: Defender's parry roll value
        
    Returns:
        bool: True if attack hits, False if dodged/parried
    """
    # Attack must beat BOTH dodge AND parry to hit
    if attacker_expertise_roll > defender_dodge_roll and attacker_expertise_roll > defender_parry_roll:
        return True
    else:
        return False

def calculate_damage(attacker_damage_roll, attacker_stats, is_crit, crit_mult):
    """
    Calculate final damage amount.
    
    Args:
        attacker_damage_roll: Attacker's damage roll value
        attacker_stats: Attacker's stat dictionary
        is_crit: Whether this is a critical hit
        crit_mult: Critical hit multiplier
        
    Returns:
        int: Final damage amount
    """
    # Base damage = roll + damage stat
    base_damage = attacker_damage_roll + attacker_stats.get('damage', 0)
    
    # Apply crit multiplier if crit
    if is_crit:
        final_damage = int(base_damage * crit_mult)
    else:
        final_damage = base_damage
    
    # Minimum 1 damage
    return max(1, final_damage)

def get_miss_flavor(attacker, defender):
    """
    Get flavor text for a missed attack.
    
    Args:
        attacker: Attacking character
        defender: Defending character
        
    Returns:
        str: Flavor text
    """
    import random
    
    attacker_name = attacker.heroine_name if hasattr(attacker, 'heroine_name') else attacker.name
    defender_name = defender.name if hasattr(defender, 'name') else defender.heroine_name
    
    flavors = [
        f"{attacker_name}'s attack misses {defender_name} completely!",
        f"{defender_name} dodges {attacker_name}'s strike!",
        f"{defender_name} parries {attacker_name}'s attack!",
        f"{attacker_name} swings wide, missing {defender_name}!",
        f"{defender_name} sidesteps {attacker_name}'s attack!",
    ]
    
    return random.choice(flavors)

def get_hit_flavor(attacker, defender, damage, is_crit):
    """
    Get flavor text for a successful hit.
    
    Args:
        attacker: Attacking character
        defender: Defending character
        damage: Damage dealt
        is_crit: Whether this was a critical hit
        
    Returns:
        str: Flavor text
    """
    import random
    
    attacker_name = attacker.heroine_name if hasattr(attacker, 'heroine_name') else attacker.name
    defender_name = defender.name if hasattr(defender, 'name') else defender.heroine_name
    
    if is_crit:
        flavors = [
            f"{attacker_name} lands a CRITICAL HIT on {defender_name} for {damage} damage!",
            f"💥 CRITICAL! {attacker_name} devastates {defender_name} for {damage} damage!",
            f"{attacker_name} finds a weak spot! CRITICAL HIT for {damage} damage!",
        ]
    else:
        flavors = [
            f"{attacker_name} hits {defender_name} for {damage} damage!",
            f"{attacker_name} strikes {defender_name}, dealing {damage} damage!",
            f"{defender_name} takes {damage} damage from {attacker_name}!",
        ]
    
    return random.choice(flavors)

def execute_normal_attack(attacker, target):
    """
    Execute a normal attack.
    
    Args:
        attacker: Attacking character (hero or mob)
        target: Target character (mob or hero)
        
    Returns:
        bool: True if executed
    """
    # Determine if attacker is hero or mob
    is_hero = hasattr(attacker, 'heroine_name')
    
    # Get attacker's rolls
    if is_hero:
        attacker_rolls = get_heroine_rolls(attacker)
    else:
        attacker_rolls = get_mob_rolls(attacker)
    
    # Get defender's rolls
    is_defender_hero = hasattr(target, 'heroine_name')
    if is_defender_hero:
        defender_rolls = get_heroine_rolls(target)
    else:
        defender_rolls = get_mob_rolls(target)
    
    # Check for automatic miss
    if attacker_rolls['miss']:
        miss_flavor = get_miss_flavor(attacker, target)
        print(f"{Fore.CYAN}{miss_flavor}{Style.RESET_ALL}")
        time.sleep(0.5)
        return True
    
    # Check if attack hits
    if not check_hit(attacker_rolls['expertise_roll'], defender_rolls['dodge_roll'], defender_rolls['parry_roll']):
        miss_flavor = get_miss_flavor(attacker, target)
        print(f"{Fore.CYAN}{miss_flavor}{Style.RESET_ALL}")
        time.sleep(0.5)
        return True
    
    # Calculate damage
    damage = calculate_damage(
        attacker_rolls['damage'],
        attacker.stats,
        attacker_rolls['crit_success'],
        attacker_rolls['crit_mult']
    )
    
    # Apply damage
    target.health -= damage
    
    # Flavor text
    hit_flavor = get_hit_flavor(attacker, target, damage, attacker_rolls['crit_success'])
    print(f"{Fore.GREEN}{hit_flavor}{Style.RESET_ALL}")
    time.sleep(0.5)
    
    # Check if target defeated
    if target.health <= 0:
        target_name = target.name if hasattr(target, 'name') else target.heroine_name
        print(f"{Fore.YELLOW}☠️  {target_name} has been defeated! ☠️{Style.RESET_ALL}")
        time.sleep(0.5)
    
    return True

def execute_player_turn(hero, all_heroes, all_mobs):
    """
    Execute a single hero's turn (player-controlled).
    
    Args:
        hero: The hero taking their turn
        all_heroes: List of all heroes in party
        all_mobs: List of all living mobs
        
    Returns:
        bool: True if turn completed successfully
    """
    # Clear defend status from last turn
    clear_defend_status(hero)
    
    # Reduce ability cooldowns
    hero.reduce_cooldowns()
    
    # Display action menu
    display_action_menu(hero, all_mobs)
    
    # Get player's action choice
    action_choice = get_player_action_choice()
    
    # Execute chosen action
    if action_choice == 1:
        # ATTACK
        display_target_menu(all_mobs)
        target = get_target_choice(all_mobs)
        
        if target:
            execute_normal_attack(hero, target)
            return True
    
    elif action_choice == 2:
        # DEFEND
        execute_defend(hero)
        return True
    
    elif action_choice == 3:
        # SPECIAL ABILITY
        display_ability_menu(hero)
        ability = get_ability_choice(hero)
        
        if ability is None:
            # Player cancelled - show menu again
            return execute_player_turn(hero, all_heroes, all_mobs)
        
        # Determine target based on ability type
        if ability in ['Heal']:
            # Single-target heal - choose ally
            print(f"\n{Fore.YELLOW}Choose ally to heal:{Style.RESET_ALL}")
            for i, ally in enumerate(all_heroes, 1):
                if ally.health > 0:
                    print(f"  {i}. {ally.heroine_name} [HP: {ally.health}/{ally.starting_health}]")
            
            while True:
                try:
                    choice = input(f"{Fore.GREEN}Enter target (1-{len(all_heroes)}): {Style.RESET_ALL}").strip()
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(all_heroes):
                        target = all_heroes[choice_num - 1]
                        break
                except ValueError:
                    continue
            
            execute_ability(hero, ability, target, all_heroes, all_mobs)
            return True
        
        elif ability in ['AOE Heal']:
            # AOE heal - no target needed
            execute_ability(hero, ability, None, all_heroes, all_mobs)
            return True
        
        elif ability in ['Power Strike']:
            # Attack ability - choose enemy
            display_target_menu(all_mobs)
            target = get_target_choice(all_mobs)
            
            if target:
                execute_ability(hero, ability, target, all_heroes, all_mobs)
                return True
    
    elif action_choice == 4:
        # USE ITEM (not implemented yet)
        print(f"{Fore.RED}Items not implemented yet!{Style.RESET_ALL}")
        time.sleep(1)
        return execute_player_turn(hero, all_heroes, all_mobs)
    
    return False

def execute_mob_turn(mob, all_heroes):
    """
    Execute a single mob's turn (AI-controlled).
    
    Args:
        mob: The mob taking their turn
        all_heroes: List of all living heroes
        
    Returns:
        bool: True if turn completed successfully
    """
    import random
    
    # Filter to living heroes only
    living_heroes = [h for h in all_heroes if h.health > 0]
    
    if not living_heroes:
        return False
    
    # Simple AI: Attack a random living hero
    target = random.choice(living_heroes)
    
    print(f"\n{Fore.RED}{mob.name}'s turn!{Style.RESET_ALL}")
    time.sleep(0.5)
    
    # Execute attack
    execute_normal_attack(mob, target)
    
    return True

# ============================================================================
# MAIN COMBAT LOOP
# ============================================================================

def run_combat(heroes, mobs, location_name="Unknown Location"):
    """
    Main combat loop - handles turn order and victory/defeat conditions.
    
    Args:
        heroes: List of Hero objects
        mobs: List of Mob objects
        location_name: Name of current location (for display)
        
    Returns:
        str: 'victory', 'defeat', or 'fled'
    """
    print(f"\n{Fore.RED}{'='*60}")
    print(f"⚔️  COMBAT BEGINS at {location_name}! ⚔️")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    time.sleep(1)
    
    # Display initial combatants
    print(f"{Fore.CYAN}YOUR PARTY:{Style.RESET_ALL}")
    for hero in heroes:
        print(f"  {hero.heroine_name} [{hero.hero_class}] - HP: {hero.health}/{hero.starting_health}")
    
    print(f"\n{Fore.RED}ENEMIES:{Style.RESET_ALL}")
    for mob in mobs:
        print(f"  {mob.name} [{mob.mob_type}] - HP: {mob.health}/{mob.starting_health}")
    
    print()
    time.sleep(2)
    
    # Initialize combat tracking
    turn_number = 1
    
    # Main combat loop
    while True:
        print(f"\n{Fore.YELLOW}{'='*60}")
        print(f"TURN {turn_number}")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        time.sleep(0.5)
        
        # ====================================================================
        # PLAYER PHASE
        # ====================================================================
        
        living_heroes = [h for h in heroes if h.health > 0]
        living_mobs = [m for m in mobs if m.health > 0]
        
        # Check victory condition before player turn
        if not living_mobs:
            return handle_victory(heroes, mobs)
        
        # Each living hero takes a turn
        for hero in living_heroes:
            # Check if all mobs defeated mid-turn
            living_mobs = [m for m in mobs if m.health > 0]
            if not living_mobs:
                return handle_victory(heroes, mobs)
            
            # Execute hero's turn
            execute_player_turn(hero, heroes, living_mobs)
            
            # Remove dead mobs from list
            mobs = [m for m in mobs if m.health > 0]
        
        # ====================================================================
        # ENEMY PHASE
        # ====================================================================
        
        living_mobs = [m for m in mobs if m.health > 0]
        living_heroes = [h for h in heroes if h.health > 0]
        
        # Check victory condition after player phase
        if not living_mobs:
            return handle_victory(heroes, mobs)
        
        # Check defeat condition before enemy phase
        if not living_heroes:
            return handle_defeat(heroes)
        
        print(f"\n{Fore.RED}{'='*60}")
        print(f"ENEMY PHASE")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        time.sleep(1)
        
        # Each living mob takes a turn
        for mob in living_mobs:
            # Check if all heroes defeated mid-turn
            living_heroes = [h for h in heroes if h.health > 0]
            if not living_heroes:
                return handle_defeat(heroes)
            
            # Execute mob's turn
            execute_mob_turn(mob, living_heroes)
        
        # ====================================================================
        # END OF TURN CLEANUP
        # ====================================================================
        
        # Check defeat condition after enemy phase
        living_heroes = [h for h in heroes if h.health > 0]
        if not living_heroes:
            return handle_defeat(heroes)
        
        # Display current status
        display_combat_status(heroes, mobs)
        
        # Increment turn counter
        turn_number += 1
        
        # Pause before next turn
        input(f"\n{Fore.CYAN}Press ENTER to continue to next turn...{Style.RESET_ALL}")

def display_combat_status(heroes, mobs):
    """
    Display current HP status of all combatants.
    
    Args:
        heroes: List of all heroes
        mobs: List of all mobs
    """
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"CURRENT STATUS")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    print(f"{Fore.CYAN}YOUR PARTY:{Style.RESET_ALL}")
    for hero in heroes:
        if hero.health > 0:
            hp_percent = (hero.health / hero.starting_health) * 100
            
            if hp_percent > 66:
                color = Fore.GREEN
            elif hp_percent > 33:
                color = Fore.YELLOW
            else:
                color = Fore.RED
            
            print(f"  {color}{hero.heroine_name}: {hero.health}/{hero.starting_health} HP{Style.RESET_ALL}")
        else:
            print(f"  {Fore.RED}{hero.heroine_name}: DEFEATED{Style.RESET_ALL}")
    
    living_mobs = [m for m in mobs if m.health > 0]
    if living_mobs:
        print(f"\n{Fore.RED}ENEMIES:{Style.RESET_ALL}")
        for mob in living_mobs:
            hp_percent = (mob.health / mob.starting_health) * 100
            
            if hp_percent > 66:
                color = Fore.GREEN
            elif hp_percent > 33:
                color = Fore.YELLOW
            else:
                color = Fore.RED
            
            print(f"  {color}{mob.name}: {mob.health}/{mob.starting_health} HP{Style.RESET_ALL}")
    
    print()

def handle_victory(heroes, mobs):
    """
    Handle victory condition.
    
    Args:
        heroes: List of heroes
        mobs: List of defeated mobs
        
    Returns:
        str: 'victory'
    """
    print(f"\n{Fore.GREEN}{'='*60}")
    print(f"✨ VICTORY! ✨")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    time.sleep(1)
    
    print(f"{Fore.YELLOW}All enemies have been defeated!{Style.RESET_ALL}\n")
    time.sleep(1)
    
    # Display surviving heroes
    living_heroes = [h for h in heroes if h.health > 0]
    print(f"{Fore.CYAN}Surviving Heroes:{Style.RESET_ALL}")
    for hero in living_heroes:
        print(f"  {hero.heroine_name}: {hero.health}/{hero.starting_health} HP")
    
    print()
    time.sleep(2)
    
    return 'victory'

def handle_defeat(heroes):
    """
    Handle defeat condition.
    
    Args:
        heroes: List of defeated heroes
        
    Returns:
        str: 'defeat'
    """
    print(f"\n{Fore.RED}{'='*60}")
    print(f"☠️  DEFEAT! ☠️")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    time.sleep(1)
    
    print(f"{Fore.YELLOW}Your entire party has been defeated...{Style.RESET_ALL}\n")
    time.sleep(2)
    
    return 'defeat'

# ============================================================================
# TEST COMBAT FUNCTION
# ============================================================================

def test_combat():
    """
    Quick test function to run a sample combat.
    Run this to test the combat system!
    """
    import Slayer_Heroes as sh
    import Slayer_Mobs as sm
    
    print(f"{Fore.CYAN}Creating test party...{Style.RESET_ALL}")
    
    # Create test heroes with names
    warrior = sh.Warrior("Aria the Brave")
    cleric = sh.Cleric("Lyra the Healer")
    wizard = sh.Wizard("Zara the Wise")
    
    heroes = [warrior, cleric, wizard]
    
    print(f"{Fore.CYAN}Creating test enemies...{Style.RESET_ALL}")
    
    # Create test mobs using the factory
    mobs = sm.create_random_encounter('medium')
    
    print(f"{Fore.GREEN}Starting combat!{Style.RESET_ALL}\n")
    time.sleep(1)
    
    # Run combat
    result = run_combat(heroes, mobs, "Test Arena")
    
    print(f"\n{Fore.YELLOW}Combat Result: {result.upper()}{Style.RESET_ALL}")
    
    return result
# ============================================================================
# RUN TEST WHEN EXECUTED DIRECTLY
# ============================================================================

if __name__ == "__main__":
    test_combat()
# ============================================================================
# END OF SLAYER_COMBAT.PY
# ============================================================================