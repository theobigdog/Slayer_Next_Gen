import Slayer_Accessory as acc
from Slayer_Accessory import whine
import Slayer_Heroes as heroes
from Slayer_UI import say, wait, pause, clear, choose, yes_no, ask_text, show_party
import random

auto_name_choices = {
    'first' : ["Ath","Jodum","Prinny","Bubba","The Cake","Tedless","Muffy","Bildo","T-Bear","Miss Beans","Billy","Djub-Djub"],
    'middle' : ["the Messy","the Wrong","the Strange","the Savage","the Potent","the Silly-Hearted","the Smelly","the Aromatic","the Unkempt","the Poorly-Dressed","the Cruel","the Really Mean"],
    'last' : ["Wet-Nurse","Sensation","Meal-Worm","Armpit","Butthead","Doofus","Dork","Lamp","Smegma","Jerk","Monkey","Walrus","Doormat"]
}

async def get_name(greet : bool = True) -> str:
    if greet:
        await say("[narr]Greetings![/]")
    name = (await ask_text(f'[narr]What\'s your name, hero?  Assuming they gave you one.  {whine()}.  Your name, please:[/]  ')).title()
    name = await acc.check_bad_name(name)
    await say()
    await say("[narr]Ooh, solid name.  I've been hosting this game for... some time... and that one's going in my top ten.  Maybe top twelve.[/]")
    return name

async def print_recommended_classes(num_chars : int):
    await say('\n[narr]Recommended Party Composition (based on party-size):[/]')
    await say()
    for hero_class in get_default_classes(num_chars): # the same lineup the narrator picks if you let him choose
        await say(acc.class_label(hero_class))

def get_default_classes(party_count : int) -> list:
    default_order =  ['Warrior', 'Cleric', 'Hunter', 'Shifter', 'Cleric', 'Sapper', 'Witch', 'Battle_Mage']
    return default_order[:party_count]


def get_hero(selection : str, name : str) -> object:
    hero_classes = {
        'Warrior' : heroes.Warrior,
        'Shifter' : heroes.Shifter,
        'Battle_Mage' : heroes.Battle_Mage,
        'Hunter' : heroes.Hunter,
        'Witch' : heroes.Witch,
        'Sapper' : heroes.Sapper,
        'Cleric' : heroes.Cleric,
    }
    hero_class = hero_classes.get(selection, heroes.Warrior) # if the selection is unrecognized, Warrior by default
    return hero_class(name)

def auto_pick_name() -> str:
    first = random.choice(auto_name_choices['first'])
    middle = random.choice(auto_name_choices['middle'])
    last = random.choice(auto_name_choices['last'])
    return first + ' ' + middle + ' ' + last

async def print_current_party(party : list):
    for member in party:
        await say(f"Hero:  {member.name}, Class:  {acc.class_label(member.hero_class)}")

async def name_heroine(prompt : str, choose_names : bool) -> str:
    if choose_names:
        return await acc.check_bad_heroine_name(await ask_text(prompt))
    return auto_pick_name()

async def healer_ok(new_party : list, selection : str, party_count : int) -> bool:
    """The nudge toward a healer (Ted, Nov 15): on the LAST pick, if nobody so far is a Cleric and this one isn't
    either, the narrator double-checks. Yes keeps the pick; no goes back to the class list. DRAFT lines."""
    if party_count == 1: # a party of one is doomed anyway: no healer nudge, just a jab (Ted, Nov 16). DRAFT lines
        if selection == 'Cleric':
            await say("[narr]A Cleric.  Alone.  And who, exactly, are you planning to hit with a Healing Wand?[/]")
        else:
            await say(f"[narr]One {selection.replace('_', ' ')}.  No healer, no backup, no friends.  Bold.  Short-lived, but bold.[/]")
        return True
    last_pick = len(new_party) == party_count - 1
    if not last_pick or selection == 'Cleric' or any(h.hero_class == 'Cleric' for h in new_party):
        return True
    sure = await yes_no("[narr]Whoa, whoa, whoa.  No Cleric?  Nobody to patch you up when shit goes sideways?  "
                        "You're SURE you don't want a healer?[/]  ")
    if sure:
        await say("[narr]Bold.  Stupid, but bold.  I'll start writing the eulogies.[/]")
        await pause()
    return sure

async def create_new_party(name: str) -> list:
    new_party = []
    await clear()
    await acc.print_classes()
    await say()
    # A menu instead of typing a number (Ted, Nov 16: on the tablet the on-screen keyboard covered the class list,
    # and it took an extra tap to get past it). Number keys still work on a PC.
    party_count = 1 + await choose("[narr]How many party members would you like to include?[/]  ", ['heroine'] + ['heroines'] * 7,  # the menu numbers them 1-8, so each reads '3  heroines'
                                   "[narr]1 to 8.  Pick one of the numbers, please.[/]  ")
    if party_count == 1:
        await say("[narr]One?  One.  You chose One.  One....  Ok, One it is....[/]")
        await wait(2)
    elif party_count <= 3:
        await say(f'[narr]{acc.number_word(party_count, capital=True)}?!  Ballsy, I like it![/]')
        await wait(2)
    await clear()
    await print_recommended_classes(party_count)
    await say()
    choose_composition = await yes_no("[narr]Would you like to choose the composition of your party?[/]  ")
    if choose_composition:
        await say("[narr]Please consider my recommendations as garbage, so take them with a grain of salt....[/]")
        await pause()
    else:
        await say("[narr]Wait... You want ME to choose for you?  Why, I'm so fucking excited, I think I need new underwear![/]")
        await say("[narr]Fair enough.  Leave it to fate.  Fate's a drunk, but she's got good instincts.  Sometimes.[/]") # moved up from below, so it answers the class question
        await pause()
    await say()
    choose_names = await yes_no("[narr]Would you like to choose the names of your party members?[/]  ")
    if choose_names:
        await say("[narr]Probably a wise choice.  I'm shit at naming.[/]")
        await pause()
    else:
        await say("[narr]Oh hell yes, I LOVE naming people.  Prepare to be emotionally attached, and perhaps disgusted a little bit too.[/]")
        await pause()
    if choose_composition:
        for _ in range(party_count):
            await clear()
            await print_current_party(new_party)
            await say()
            await print_recommended_classes(party_count)
            await say()
            hero_classes = acc.get_hero_classes()
            pick = await choose( # a numbered list in the terminal, buttons in the window
                "\nWhich Class would you like to add?  ",
                [hero_class.replace('_', ' ') for hero_class in hero_classes],
                "\nLet's try that again.  Of the listed Class options, which number would you like to add?  ",
            )
            selection = hero_classes[pick]
            while not await healer_ok(new_party, selection, party_count):
                pick = await choose("\nWhich Class would you like to add?  ", [hero_class.replace('_', ' ') for hero_class in hero_classes],
                                    "\nLet's try that again.  Of the listed Class options, which number would you like to add?  ")
                selection = hero_classes[pick]
            heroine_name = await name_heroine(f"\nOk, let's have a name for your {acc.class_label(selection)}:  ", choose_names) # the prompt names the class, so it stays on screen while naming
            new_party.append(get_hero(selection, heroine_name))
    else:
        members = get_default_classes(party_count)
        await clear()
        for selection in members:
            heroine_name = await name_heroine(f"Ok, let's have a name for your {acc.class_label(selection)}:  ", choose_names)
            new_party.append(get_hero(selection, heroine_name))
    return new_party

async def welcome_back(saved_party : dict) -> dict:
    await pause()
    await clear()
    saved_party = await acc.start_new_run(saved_party) # shows the party, with any news under it, and waits for a click
    return saved_party

async def show_the_list():
    """The List: every saved party's name (typing "the list" at the prompt, or clicking it in the window)."""
    names = acc.saved_party_names()
    if names:
        await say(f"[narr]Fiiine.  Here's The List:[/]  {',  '.join(names)}")
        await say("[narr](To start a name over, type delete and the name.)[/]")
    else:
        await say("[narr]The List is empty.  Nobody's on it.  Not even you.  Especially not you.[/]")

async def delete_from_the_list(name : str):
    """Typing "delete <name>": deletes that saved party for good, after a yes. DRAFT lines, for Ted to rewrite."""
    if name not in acc.saved_party_names():
        await say(f"[narr]There's no {name} on [/][thelist]The List[/][narr].  Can't delete what was never there.[/]")
        return
    if await yes_no(f"[narr]Delete {name} for good?  Every hero, every scrap of loot, gone.  No take-backs.[/]  "):
        acc.delete_party(name)
        await say(f"[narr]Done.  {name} is off [/][thelist]The List[/][narr].  The name's up for grabs again.[/]")
    else:
        await say(f"[narr]Fine.  {name} lives to disappoint another day.[/]")

async def offer_checkpoint(name : str):
    """If this name's last run never finished (Slayer_Accessory.save_checkpoint), offer to pick it up at the next
    fight. Returns the party to play (with 'resume_fight' set), or None to carry on as usual. Either way the
    checkpoint is used up. DRAFT lines."""
    found = acc.load_checkpoint(name)
    if found is None:
        return None
    party_dict, next_fight = found
    acc.clear_checkpoint(name)
    import Slayer_Game_Play as gp # imported here, because Slayer_Game_Play imports this file
    won = gp.FIGHTS[next_fight - 1][0]
    await say(f"[narr]Wait a second, {name}...  your last run never finished.  Last I saw, you'd just beaten {won}.  Did the whole world just...  stop?[/]")
    if await yes_no("[narr]Want to pick up right where you left off?[/]  "):
        await say("[narr]Right.  Dust yourselves off.  Onward.[/]")
        await pause()
        party_dict['resume_fight'] = next_fight
        return party_dict
    await say("[narr]Your call.  That run never happened, then.[/]")
    return None

async def get_party() -> dict:
    name = await get_name()
    resumed = await offer_checkpoint(name)
    if resumed:
        return resumed
    try:
        saved_party = acc.load_party(name)
        await say(f"[narr]Ah yes, here you are: {name}!  The legend returns![/]\n[narr]Ok, are you ready to rock and ro......{whine()}[/]\n[narr]Sorry.  I'm thrilled.  Genuinely.  This is my thrilled face.[/]")
        return await welcome_back(saved_party)
    except FileNotFoundError:
        await say('[narr]Hmmmm.....[/]')
        await wait(1)
        name = (await ask_text("[narr]I don't recognize you, and I don't think you're on [/][thelist]The List[/][narr].[/]\n[narr]What was that name again?[/]  ")).title()
        # The secret ways in: "the list" shows every saved party (in the window, click The List), and "delete <name>"
        # deletes one for good, so that name can start a fresh party (in the window, The List has delete buttons too).
        while name.strip().lower() in ('the list', 'list') or name.strip().lower().startswith('delete '):
            if name.strip().lower().startswith('delete '):
                await delete_from_the_list(name.strip()[len('delete '):].strip().title())
            else:
                await show_the_list()
            name = (await ask_text("[narr]So.  Which one are you?[/]  ")).title()
        name = await acc.check_bad_name(name)
        resumed = await offer_checkpoint(name)
        if resumed:
            return resumed
        try:
            saved_party = acc.load_party(name)
            await say(f"[narr]Oh, that's right, {name}!  You're the one who projectile-vomited into the fountain last night.  Legendary distance, by the way.{whine()}  Welcome back.[/]")
            return await welcome_back(saved_party)
        except FileNotFoundError:
            await say("[narr]No, I've never seen you.[/]")
            await wait(2)
            await say(f"[narr]Let's just make you a fresh party, mkay, {name}?[/]")
            await wait(3)
            new_party = await create_new_party(name)
            await clear()
            await show_party(new_party)
            await pause()
            return {
                "name" : name,
                "party" : new_party,
                "wiped" : False,
                "times_run_dungeon" : 1,
                "narration" : True,
                "token_used" : False,
            }
