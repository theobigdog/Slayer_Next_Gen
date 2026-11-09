from Slayer_UI import say, pause, wait, clear
import Slayer_Accessory as acc
from Slayer_Accessory import whine
import random

LUCKY_GIFT = 5 # the narrator's thank-you for listening: + this much luck for every heroine, first run only

def threatening_item(heroine : object) -> str:
    """Something she can fondle threateningly: a melee weapon if she has one, then any weapon, then whatever she's got."""
    items = [acc.get_item(name) for name in heroine.inv if name != 'token_of_the_wise_witch']
    for kinds in (('melee', 'both'), ('range', 'aoe'), ('heal', 'trinket')):
        found = [item for item in items if item['attack_type'] in kinds]
        if found:
            return random.choice(found)['item_desc']
    return 'fists'

async def intro(party_dict : dict) -> dict:
    await say("[narr]Welcome, welcome.. welcome..... yeah, welcome to Slayer, the GOAT, game of the year.....  Um...[/]")
    await wait(1)
    await say("[narr]Look, I'm just going to be honest with you - I've been doing this for a long fucking time.[/]")
    await say("[narr]I've seen so many parties, like yours, enter this thing and just never come out.[/]")
    await say("[narr]The vast majority, really.[/]")
    await say("[narr]I think...[/]")
    await wait(2)
    await say("[narr]Fuck, now that I think about it, has anyone ever actually walked back out of here?  No?[/]")
    await say("[narr]I just can't take many more observations of failure.  I think it's starting to break me...[/]")
    await pause()
    await say("[narr]Please do better than those who have come before you!  Please?[/]")
    await pause()
    await clear()
    await say(f"[narr]Ok... <ahem>  I hope you're ready for this, {party_dict['name']}.[/]")
    await wait(0.5)
    if party_dict['times_run_dungeon'] == 1:
        await say("[narr]Firstly, as a Thank You for taking the time to enjoy my immense wit and charm...[/]")
        await say("[narr]Fine.  As a token of gratitude for allowing me my little \"stories\", your whole starting party has received a small gift.[/]")
        await say("[narr]If you ask me, I'd say all of you just look.... a little more lucky than you did.[/]")
        for heroine in party_dict['party']: # the gift: a little luck for everyone (never shown as a number)
            heroine.stats['luck'] = min(acc.STAT_CAP, heroine.stats['luck'] + LUCKY_GIFT)
        await say("[narr]Now that my small measure of sappiness is out of my system, let's get to it.[/]")
        await wait(0.5)
    await say("[narr]Well, whether you have played before or not, welcome to Slayer Next Gen.  The LONG-anticipated version of Slayer, the....[/]")
    await say(f"[narr]Wait, Slayer 1 never released?  Then why the fuck is this one called Next Gen?  {whine()}[/]")
    await say("[narr]I guess, suffice it to say that this version is at least a mild upgrade.  Anyone out there sick enough to want to try it, contact My Mom![/]")
    await pause()
    await clear()
    await say("You enter Empathia, a magical world dominated by women.  Wise women.  Honorable women.  Strong women.  Beautiful women.")
    await pause()
    await say("However, festering wounds of ugly chauvinism remain - tucked away in dark pockets of the world.")
    if len(party_dict['party']) == 1:
        await say("You recently squeezed a lead out of someone regarding a newly-discovered dark pocket, deep in the Phallic Mountains - where else?")
    else:
        h1, h2 = random.sample(party_dict['party'], 2) # two different heroines, picked at random
        await say(f"Investigating some of these dark pockets, {h1.name} recently beat the shit out of a rather suspicious character she met down a dark passageway.")
        await say(f"\"Yeah, I remember that!\" squeals {h2.name}.  \"Remember, {h1.name}?  Once you had tightly gripped him by his shriveled cojones, he became the loudest rat I've ever heard!\"")
        await say(f"{h1.name} sneers, \"Right, the fucking 'Phallic Mountains.'  He kept talking about those Dick Hills or whatever.\"")
        await pause()
        await say("[narr]Now where else would it be?[/]")
    await pause()
    await clear()
    await say("[narr]Right.  So the Dick Hills have been calling to you, apparently?  Be honest, have you ever even heard of the \"Phallic Mountains\"?  No?[/]")
    await say("[narr]Exactly, you've never heard of them, you know nothing of the secret tavern in the southwest foothills, shit, if it weren't for me rambling you wouldn't even know about....  Right.[/]")
    await pause()
    await say("[narr]Well, then I guess it's off you go now, to the infamous Devil's Brew Tavern, found in the darkest depths of the Dick Hi...[/]")
    await say("[narr]Wait, what?  You're already here?[/]")
    await say(f"[narr]Jesus Fucking Christ, I'm the fucking Narrator, can someone just keep me up-to-date on this?  You're making me sound like a fucking moron!  {whine()}[/]")
    await say("[narr]I guess I missed out on the part where you were traveling.  It's a shame, I was going to tell you all about the local flora and fauna on the way to the mountains.  All about the histories and cultures of every town we passed.[/]")
    await say("[narr]We were going to do some real girl-scout shit....[/]")
    await wait(1)
    await say("[narr]Welcome to the Devil's Brew![/]")
    await pause()
    return party_dict # party_dict returns unchanged if this isn't the first time they've gone through.  They have to do this their first time, or the opportunity is gone forever for that party

async def happy_intro(party_dict : dict) -> None:
    party = party_dict['party']
    armed = [x for x in party if any(acc.get_item(i)['attack_type'] in ('melee', 'both') for i in x.inv)]
    h1 = random.choice(armed or party) # the one who gets in the barkeep's face, with a melee weapon if anyone has one
    others = [x for x in party if x is not h1]
    h2 = random.choice(others) if others else h1 # a solo heroine does all the talking
    await clear()
    await say("As your ragtag party enters the tavern, weary from days of traveling, and ready to kick back with a fresh cold mug, they catch sight of the general clientele.")
    await say(f"Coming from back home, a tavern filled with men, seedy, dark, vicious men, is not something {h1.name} is used to.")
    await say(f"\"What the hell are they looking at?\" murmurs {h2.name}.  \"I'm getting the feeling that I'm not wanted here.\"")
    await pause()
    await say(f"Catching the eye of the proprietor, a somewhat-aged, dwarven tavern-keep, {h1.name} maneuvers past two semi-comatose dwarves, incoherently mumbling to each other, more in gurgles and pops than in any identifiable language.")
    await say(f"\"Tavern Keeper!\" yells {h1.name}, in a voice far too loud for such close quarters.  \"A word, please.\"")
    await say("\"It is my understanding that this building is a front for the center of the Nocturnal Order of Males Against Authoritative Matriarchy (NO MAAM) movement.  You ARE familiar with this movement, no?\"")
    await say("The tavern keeper, carefully cleaning mugs, clearly stifling a sigh, begins, \"Look here, lass, I don't know where you think you are, but you're not in Vulvamora anymore, and you might want to show a little more respect.\"")
    await pause()
    item = threatening_item(h1) # a melee weapon if she has one (a Cleric makes do with her Healing Wand)
    await say(f"{h1.name} smirks.  \"Oh, you want a little more respect, do you?\" she says as she, seemingly idly, yet threateningly, fondles her {item}.  \"Perhaps we try this again.\"")
    await say("\"Barkeep, either help us with the cause, or get out of the way.  But we will not tolerate any further foolishness from you.\"")
    await pause()
    await say("\"Oh lassie.... Now take it easy or you might make me angry.\"")
    await say(f"{h2.name} belts out with laughter, \"Really, you think I'm scared of some old, washed-up dwarf?  I eat pieces of shit like you for breakfast!\"")
    await pause()
    await say("His brows furrow, and there is the briefest hint of almost-purple fire, reflecting across his eyes.  \"Why did you have to go and say something like that?  We dwarves, say what you will about us, but, shit?  For breakfast?  I don't think so!!\" he growls and nimbly leaps over the bar in front of the party.")
    await say("The two drunk dwarves suddenly stop their incoherent babbling, and seem to be taking notice of the situation.")
    await say(f"\"Now hold on, buddy,\" starts {h1.name}, but she is immediately interrupted.")
    await pause()
    await say("\"No!  No, you hold on, BUDDY!  This is my home.  This is my business, and you are no longer welcome.  Please Leave!\" he growls.")
    await say("The words are punctuated by both drunk dwarves hopping off their seats and taking up a fighting stance next to the tavern keeper.")
    await say(f"\"Are you fucking kidding me right now?\" starts {h2.name}.  \"We will mop the floor with you, old dwarf!\"")
    await say("\"ENOUGH!\" he booms.  \"I think it's about time you lassies learn a little respect....\"")
    await say(f"{h1.name} stares the tavern keeper in the eyes, hissing, \"Bring it!!\"")
    await pause()


# =====================================================================================================
#   TED'S WRITING SPOTS
#
#   Each function below is one moment in the game, in the order they happen. Everything in them now is a
#   placeholder (your old notes, or Claude's drafts marked DRAFT), so rewrite, add and delete lines freely:
#   say(), pause(), wait(seconds) and clear() all work here, same as in intro() above.
#
#   The only rules: keep each function's name and the things in its parentheses (the game calls them by
#   name), and close every [narr] tag on the same line it opens.
#
#   Handy things you can use in any of them:
#     party = party_dict['party']               the heroines (each has .name, .hero_class, .is_dead)
#     random.choice(party), random.sample(party, 2)   pick one or two at random
#     party_dict['name']                        the player's name
#     party_dict['times_run_dungeon']           1 on the first run, 2 on the second...
#     party_dict.get('narration')               True if they said yes to narrative (None in dev mode)
#     say([line_a, line_b, line_c])             a list makes the game pick one line at random
# =====================================================================================================

# ---------- The tavern, after the Happy fight -------------------------------------------------------

async def happy_wipe(party_dict : dict, happy_killed : bool) -> None:
    """Plays the moment enraged Happy has wiped the party. happy_killed is True when they actually killed
    enraged Happy (he wipes them anyway); False when he just beat them to death the normal way."""
    if happy_killed:
        living_party = [x for x in party_dict['party'] if not x.is_dead]
        h = random.choice(living_party)
        await say('Happy hits the ground.  Hard.')
        await say(f"Still catching her breath, {h.name} begins to walk over to the crumpled dwarf.")
        await pause()
        await say("As she approaches, Happy's body begins to twitch.  And then bounce a bit.  Even a little jiggling. [narr] WHAT THE FUCK?[/]")
        await say(f"{h.name} pauses, \"Is he... laughing?\"")
        await say('Happy continues to chuckle, then in one extremely quick move, flips directly onto his feet.')
        await say(f"\"Now wait a second...\" begins {h.name} and she reaches for the nearest weapon her hand can find.")
        await pause()
        await say(f"Before {h.name} can say another word, Happy stops laughing, concurrently sweeping a beefy leg across her face, snapping her neck instantly.")
        if len(living_party) > 1:
            remaining_members = [x for x in living_party if x != h]
            await say("Moving with such blazing fast speed that all any remaining heroine can see are blurred motions, Happy systematically shreds every remaining party member's defense, pulverizing each victim as he somersaults from one to the next.")
            await say(f"Happy drops what\'s left of {random.choice(remaining_members).name}, and begins to take in the carnage.")
            await say("[narr]Fuck, you didn\'t have a chance, did you?[/]")
    else:
        await say('As the final heroine hits the floor, Happy takes a second to stop and smile - he savors the moment.')
    await pause()

async def happy_resurrection(party_dict : dict) -> None:
    """Plays right after happy_wipe: Happy brings everyone back. (The design doc also has him getting sappy
    about his 'Disgruntled' bouncer job here.) Leave it empty and nothing plays."""
    h = random.choice(party_dict['party'])
    solo = len(party_dict['party']) == 1 # a party of one gets her name instead of "each heroine"
    await say(f"\"Yes, yes, I have done fine work today,\" he mutters to himself, chuckling.  That is, until he catches a glimpse of {h.name}\'s mangled corpse.")
    await say("Happy stops to look deeply into the blank eyes of the poor, late heroine.  That purple flame briefly lights up in Happy's eyes again, and then he appears to suddenly experience a complete metaphysical breakdown.")
    await say("Huge tears well up in his eyes as he thinks back to all of his countless victims over the years.")
    await say(f"[narr]Happy my ass...[/]")
    await pause()
    await say("\"All the murder.  All the senseless killing.  And what the fuck am I even getting out of this?\" he cries.")
    await say("\"I have fucking had it with playing a glorified bouncer for this - \'organization\'!\" he booms.  \"I'm going to show THEM a thing or two, and maybe they'll think twice before giving me such a shit-job again.\"")
    await say("[narr]I think I can see now where the \"Disgruntled\" part of his title comes from![/]")
    await pause()
    await say("Happy stops blubbering and closes his eyes.  He holds both arms out to his sides, palms up and begins muttering some sort of rapid, runic language.")
    await say("Cold, purple fire, the same shade as what was briefly caught in Happy\'s eyes, begins to stream from his palms.")
    await say(f"Purple tendrils thicken and split, wrapping {h.name if solo else 'each heroine'}\'s body until you can\'t see a square millimeter of the unfortunate, engulfed adventurer.")
    await say('Sweat begins to bead up on Happy\'s forehead, quickly becoming a flowing stream, as he almost literally pours every ounce of his magical capacity into the process.')
    if solo:
        await say(f"As Happy begins to shake and visibly weaken, the un-fucking-thinkable happens:  {h.name} begins to slowly rouse, moaning painfully as she returns to the land of the living.")
    else:
        await say("As Happy begins to shake and visibly weaken, the un-fucking-thinkable happens:  One by one, each heroine begins to slowly rouse, moaning painfully as they return to the land of the living.")
    await pause()
    await say("[narr]Oh.  Oh my.  I just went from 6 to midnight....[/]")
    await say(f"{h.name if solo else 'The final party member'} comes back to full consciousness, and Happy\'s face softens, the staccato runes slow down and eventually cease completely.")
    await say('\"Welcome Back!\" Happy booms.')


async def happy_loot(party_dict : dict) -> None:
    """Plays just before Happy hands over his loot (and whatever his dead buddies dropped). The loot menus
    come right after this."""
    h1 = random.choice(party_dict['party'])
    await say('\"Now don\'t you go thinking that Happy is just a big softy, but he ain\'t stingy neither!\" he starts.  \"It seems like you all could use a little extra help.  I honestly don\'t have a great deal here to help you out, but I don\'t want to quite literally toss you to the wolves without any help!\"')
    await say('[narr]Goddamnit, that had better not be foreshadowing - Hey I\'m on your side here, but I doubt you can handle a challenge of that magnitude![/]')
    await say(f'{h1.name} whispers, \"Wolves?  I fucking hate wolves....\"')
    await say(f'\"Breathe easy, lassie,\" Happy reassures.  \"We haven\'t had any wolves in these parts for at least the last week or two.  No stress."  Happy shoots a quick wink at {h1.name} who just shudders.')
    await pause()
    to_share = ' to distribute as you see fit.' if len(party_dict['party']) > 1 else '.'
    await say(f'\"Anyway, I want to make sure that you fine heroines have a better chance in the future,\" Happy starts, \"so I have assembled a goodie bag for you{to_share}\"')
    if party_dict['times_run_dungeon'] == 1:
        cap = acc.capacity_facts(party_dict) # the real limits, so Happy stays right if they ever change
        potions = f"{cap['potions']} potion" + ('' if cap['potions'] == 1 else 's')
        await say(f'\"Your loot may include potions and/or trinkets.  Each heroine can carry {potions}, with up to {cap["stack"]} its usual doses per potion.  A similar but separate capacity exists for trinkets - small items that give you stat buffs: {cap["trinkets"]}.  Weapons and the rest of your gear go in a bag that holds {cap["gear"]} pieces.\"')
        if cap['potions'] == 1:
            await say('\"If you choose a potion that you already have, it will just be topped-off.  If you choose a new potion, it will replace the old one, which you will have to discard.\"')
        else:
            await say('\"If you choose a potion that you already have, it will just be topped-off.  If her potions are full, a new one will replace one of the old ones, which you will have to discard.\"')
        await say('\"Be careful with all items you obtain during your adventures - you can only carry so many, and anything you can\'t carry is simply left behind.\"  [narr]Leave no trace....  you littering fucks![/]')
        await pause()
        await say('\"Your Stash.  Every time you attempt to complete this dungeon, you will start at this Tavern.  To make your lives easier, I have installed a Stash for you to use and reuse.\"')
        await say(f'\"It holds up to {cap["stash"]} different objects, so you shouldn\'t have too much trouble finding space there, but be mindful of what you are carrying into the dungeon, because once you enter, there is no turning back to recover these items until the next time you visit these parts again.\"')
        await say('\"Do keep in mind that, potentially, item upgrades will require you to make a permanent decision to discard another item, if you are at inventory capacity.\"')
        await pause()
        await say('\"I believe that is about it.  Who\'s first?\"')

async def happy_stats(party_dict : dict) -> None:
    """Plays just before the first stat raises (Happy explaining that fights make them better). After this,
    some heroines get one of the STAT_HINTS lines below."""
    await say('Add specific Happy narration here for get stat increases, to explain how it works even, maybe?  Actual stats will never be shown, just set and updated in the background, so nothing should actually print from this function when finished.')
    await say('1 idea:  "Now listen close, young lassies, I don\'t know exactly how this could be, but this last battle seems to have increased certain skills, for each of you, at a rate I didn\'t think was possible for folks to improve, but you appear to be no average adventurers!')
    await say('Don\'t ask me who improved in what, or by how much.')
    await say('Also, I would expect this to occur again after each successful encounter you wee lassies may face.')
    await pause()

async def happy_back_room(party_dict : dict) -> None:
    """Plays just before the stash menu in Happy's back room."""
    await say("\n[narr]Happy unlocks his back room, where your stash lives.  Last chance to swap gear before heading down.[/]")

async def secret_entrance(party_dict : dict) -> None:
    """Plays after the back room: Happy's toe-tap opens the secret dungeon entrance. (Not hooked in until
    the Kobold fight is built.)"""
    await say("[narr]DRAFT: Happy taps his toes in some weird little pattern, and a chunk of the tavern floor grinds open.  Stairs.  Down.  Of course it's down.[/]")
    await pause()

# ---------- Stat raises (after every fight the party survives) --------------------------------------

# After each fight, about half the heroines get one of these, for the stat she improved most. {name} becomes
# her name. These are Claude's drafts: rewrite away. (Keep the words on the left of each colon as they are.)
STAT_HINTS = {
    'hit': "{name}'s aim looks a little steadier.",
    'crit_chance': "{name} has a nasty new glint in her eye.",
    'crit_mult': "{name} seems to hit a little harder when it counts.",
    'luck': "{name} found a penny on the floor.  Heads up, even.",
    'expertise': "{name} is reading her enemies a little better.",
    'toughness': "{name} looks a bit sturdier.  Scarier, too.",
    'dodge': "{name} seems quicker on her feet.",
    'parry': "{name}'s blocking looks a little crisper.",
    'fear': "{name} doesn't flinch quite so much anymore.",
    'heal_chance': "{name}'s bandaging is getting less embarrassing.",
    'aoe_heal_chance': "{name}'s prayers seem to carry a little farther.",
    'max_hp': "{name} looks a little beefier.",
}

# ---------- The dungeon (not hooked in until the Kobold fight is built) -----------------------------

async def kobolds_appear(party_dict : dict, kobolds : list) -> None:
    """Plays when the Krazy Kobolds show up, before the fight. kobolds is the list of them (each has .name)."""
    await say(f"[narr]DRAFT: Something giggles in the dark.  Then something else giggles back.  {len(kobolds)} somethings, actually.[/]")
    await pause()

async def fight_won(party_dict : dict, mobs : list) -> None:
    """Plays when the party wins a dungeon fight, before the Token, loot and stat raises."""
    await say("[narr]DRAFT: And THAT is how it's done.  Somebody check the bodies for shinies.[/]")
    await pause()

async def loot_found(party_dict : dict) -> None:
    """Plays before the loot menus after any fight that dropped something (at the tavern too)."""
    await say(f"\n[narr]Loot!  Let's see what's on the floor.[/]")

async def stats_after_fight(party_dict : dict) -> None:
    """Plays before the stat raises after a dungeon fight (Happy's happy_stats covers the tavern). Leave it
    empty and only the STAT_HINTS lines play."""
    pass

async def dungeon_wipe(party_dict : dict, mobs : list) -> None:
    """Plays when the whole party dies in the dungeon. That ends the run."""
    await say("[narr]DRAFT: Well.  Shit.  That's the run, folks.[/]")
    await pause()
