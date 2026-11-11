from Slayer_UI import say, pause, wait, clear, yes_no
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

def two_of(party : list) -> tuple:
    """Two DIFFERENT heroines at random. A party of one gets the same heroine twice (random.sample would crash
    on her, and random.choices can hand back the same heroine twice in a big party)."""
    return tuple(random.sample(party, 2)) if len(party) > 1 else (party[0], party[0])

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
    await say("The tavern keeper, carefully cleaning mugs, clearly stifling a sigh, begins, \"Look here, lass, I dinnae ken where ye think ye are, but ye're no' in Vulvamora anymore, an' ye might want tae show a wee bit more respect.\"")
    await pause()
    item = threatening_item(h1) # a melee weapon if she has one (a Cleric makes do with her Healing Wand)
    await say(f"{h1.name} smirks.  \"Oh, you want a little more respect, do you?\" she says as she, seemingly idly, yet threateningly, fondles her {item}.  \"Perhaps we try this again.\"")
    await say("\"Barkeep, either help us with the cause, or get out of the way.  But we will not tolerate any further foolishness from you.\"")
    await pause()
    await say("\"Och, lassie....  Now take it easy, or ye might make me angry.\"")
    await say(f"{h2.name} belts out with laughter, \"Really, you think I'm scared of some old, washed-up dwarf?  I eat pieces of shit like you for breakfast!\"")
    await pause()
    await say("His brows furrow, and there is the briefest hint of almost-purple fire, reflecting across his eyes.  \"Why'd ye have tae go an' say somethin' like that?  We dwarves, say what ye will aboot us, but, shite?  For breakfast?  I dinnae think so!!\" he growls and nimbly leaps over the bar in front of the party.")
    await say("The two drunk dwarves suddenly stop their incoherent babbling, and seem to be taking notice of the situation.")
    await say(f"\"Now hold on, buddy,\" starts {h1.name}, but she is immediately interrupted.")
    await pause()
    await say("\"Naw!  Naw, ye hold on, BUDDY!  This is ma hame.  This is ma business, an' ye are no longer welcome.  Please Leave!\" he growls.")
    await say("The words are punctuated by both drunk dwarves hopping off their seats and taking up a fighting stance next to the tavern keeper.")
    await say(f"\"Are you fucking kidding me right now?\" starts {h2.name}.  \"We will mop the floor with you, old dwarf!\"")
    await say("\"ENOUGH!\" he booms.  \"I think it's aboot time ye lassies learned a wee bit o' respect....\"")
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
#     random.choice(party)                      pick one at random
#     h1, h2 = two_of(party)                    two DIFFERENT ones (a party of one gets her twice, no crash)
#     many = len(party) > 1                     then 'lassies' if many else 'lassie', and so on
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
    await say(f"\"Aye, aye, I've done some fine work today,\" he mutters to himself, chuckling.  That is, until he catches a glimpse of {h.name}\'s mangled corpse.")
    await say("Happy stops to look deeply into the blank eyes of the poor, late heroine.  That purple flame briefly lights up in Happy's eyes again, and then he appears to suddenly experience a complete metaphysical breakdown.")
    await say("Huge tears well up in his eyes as he thinks back to all of his countless victims over the years.")
    await say(f"[narr]Happy my ass...[/]")
    await pause()
    await say("\"All the murder.  All the senseless killin'.  An' what the fuck am I even gettin' oot o' this?\" he cries.")
    await say("\"I have fuckin' had it wi' playin' a glorified bouncer for this - \'organization\'!\" he booms.  \"I'm gonnae show THEM a thing or two, an' maybe they'll think twice afore givin' me such a shite-job again.\"")
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


async def carrying_rules(party_dict : dict) -> None:
    """Happy's speech on what each heroine can carry, and The Stash. Plays in happy_loot: always on the first
    run, and on later runs if the player asks to hear it again. The numbers come from the real rules
    (acc.capacity_facts), so Happy stays right if they ever change."""
    cap = acc.capacity_facts(party_dict)
    potions = f"{cap['potions']} potion" + ('' if cap['potions'] == 1 else 's')
    # Each subject gets said once, with a blank line between subjects (Ted, Nov 10): potions, trinkets, the bag.
    if acc.MAX_STACK > 1: # a bottle has room for more than it comes with
        top_up = f'it\'ll just top up the one ye have - a bottle holds {cap["stack"]} what it comes wi\'.'
    else:
        top_up = 'it\'ll just top yers back up tae full.'
    if cap['potions'] == 1:
        swap = 'If ye pick a new one, it\'ll replace the old one.'
    else:
        swap = 'If her potions are full, a new one\'ll replace one o\' the old ones.'
    await say(f'\"Yer loot might include potions an\' trinkets.  Potions first: each lass can carry {potions}.  If ye pick one ye\'ve already got, {top_up}  {swap}  While ye\'re here, the old one can go in The Stash, but once ye\'re down in that dungeon, ye\'ll have tae toss it.\"')
    await say()
    await say(f'\"Trinkets - wee things that give ye stat buffs - have their own separate limit: {cap["trinkets"]}.\"')
    await say()
    await say(f'\"Weapons an\' the rest o\' yer gear go in a bag that holds {cap["gear"]} pieces.\"')
    await say()
    await say('\"Be careful wi\' everythin\' ye pick up on yer adventures - ye can only carry so much, an\' anythin\' ye cannae carry just gets left behind.\"  [narr]Leave no trace....  you littering fucks![/]')
    await pause()
    await say('\"Now, The Stash.  Every time ye have a go at this dungeon, ye\'ll start right here at this Tavern.  Tae make yer lives easier, I\'ve installed The Stash for ye tae use an\' reuse.\"')
    await say(f'\"It holds up tae {cap["stash"]} things, so ye shouldnae have much trouble findin\' space there, but mind what ye\'re carryin\' intae the dungeon, because once ye\'re in, there\'s nae turnin\' back tae fetch any o\' it until the next time ye visit these parts.\"')
    await say()
    await say('\"Do keep in mind that, potentially, an upgrade might mean makin\' a permanent decision tae toss another item, if ye\'re at capacity.\"')
    await pause()

async def happy_loot(party_dict : dict) -> None:
    """Plays just before Happy hands over his loot (and whatever his dead buddies dropped). The loot menus
    come right after this."""
    h1 = random.choice(party_dict['party'])
    many = len(party_dict['party']) > 1
    heroines = 'heroines' if many else 'heroine'
    await say('\"Now dinnae ye go thinkin\' that Happy is just a big softy, but he isnae stingy neither!\" he starts.  \"Seems tae me ye could use a wee bit o\' extra help.  I honestly dinnae have a great deal here tae help ye oot, but I dinnae want tae quite literally toss ye tae the wolves withoot any help!\"')
    await say('[narr]Goddamnit, that had better not be foreshadowing - Hey I\'m on your side here, but I doubt you can handle a challenge of that magnitude![/]')
    await say(f'{h1.name} whispers, \"Wolves?  I fucking hate wolves....\"')
    await say(f'\"Breathe easy, wee lassie,\" Happy reassures.  \"We havenae had any wolves in these parts for at least the last week or two.  Nae stress.\"  Happy shoots a quick wink at {h1.name}, who just shudders.')
    await pause()
    to_share = ' tae share oot as ye see fit.' if many else '.'
    await say(f'\"Anyway, I want tae make sure ye fine {heroines} have a better chance in the future,\" Happy starts, \"so I\'ve assembled a wee goodie bag for ye{to_share}\"')
    if party_dict['times_run_dungeon'] == 1:
        await carrying_rules(party_dict)
        await say('\"I believe that\'s aboot it.  Let\'s see what ye got.\"')
    else: # a returning party can hear the rules again if they want
        if await yes_no('Happy raises an eyebrow.  \"Ye\'ve heard all this afore, but d\'ye want me tae go over the carryin\' rules an\' The Stash again?\"  '):
            await carrying_rules(party_dict)
            await say('\"I believe that\'s aboot it.  Let\'s see what ye got.\"')
        else:
            await say('\"Right, ye ken the drill, then.  Let\'s see what ye got.\"')

async def happy_back_room(party_dict : dict) -> None:
    """Right after Happy's loot: the dark corner where The Stash lives. The Stash menu happens in the middle
    (the acc.visit_stash line); the lines after it play once the player picks "Done"."""
    h = random.choice(party_dict['party'])
    await say(f"\nHappy walks you back to a VERY dark corner of the room, where he quite briefly makes what you assume must be some obscene gestures.  \"These Highland Dwarves are such a silly people,\" mutters {h.name}.")
    await say(f'Clearly ignoring {h.name}, Happy begins to reach into the dark corner, seemingly, magically pulling out any of your items currently stored in The Stash.')
    await say("[narr]Looks like this is the last chance to swap gear before heading down.[/]")
    await pause()
    await acc.visit_stash(party_dict)  # <-- The Stash menu happens right here
    await say(f'As Happy returns the party to the Tavern proper, {h.name} closely inspects the dark corner, feeling every inch, and finds nothing.  \"What the fuck?\"')
    await say(f"[narr]Did you really expect to find anything there, {h.name}?[/]")
    await pause()

async def happy_stats(party_dict : dict) -> None:
    """After The Stash: Happy explains that fights make them better, with the first stat raises in the middle
    of his speech (the acc.get_stat_increases line). This first time, every heroine gets one of the STAT_HINTS
    lines below; after later fights it's about half of them. The dungeon's secret_entrance comes next."""
    many = len(party_dict['party']) > 1
    lassies = 'lassies' if many else 'lassie'
    each = ', for each o\' ye,' if many else ''
    adventurers = 'adventurers' if many else 'adventurer'
    await say(f"\"Now listen close, young {lassies}.  I dinnae ken exactly how this could be, but that last battle seems tae have increased certain skills{each} at a rate I didnae think was possible for folk tae improve.  But ye appear tae be no average {adventurers}!\"")
    await acc.get_stat_increases(party_dict, hint_chance=1)  # <-- the stat raises happen right here: each heroine's hint line ("Neyssa looks a little beefier."), then a pause
    await say(f'\"Seein\' as how ye\'ve improved so vastly, so rapidly, I\'d expect this sort o\' thing tae happen again after each successful encounter ye wee {lassies} might face.\"')
    h = random.choice(party_dict['party'])
    us = 'us' if many else 'me'
    await say(f"{h.name} mutters just loudly enough to be heard, \"I swear to fucking Christ, if you call {us} 'wee {lassies}' one more time, I'm going to slit your fucking th...\"")
    await say(f'A quick look from Happy, eyes once again burning with purple fire, changes her mind, and she chooses not to complete the sentence.  [narr]Good choice, {h.name}.[/]')
    await pause()
    await say('\"As I was sayin\', wi\' how quickly ye seem tae develop, I\'d think if ye stick at it for a bit, ye\'ll be a FORCE tae be reckoned with.\"')
    await say('\"Or just see what this dungeon is all aboot, this one time.  The choice is yers, but I hope ye enjoy yer adventure!\"')
    await pause()

async def secret_entrance(party_dict : dict) -> None:
    """The start of the dungeon, right after Happy's stats speech: his drunk hopscotch opens the secret
    entrance, and down they go."""
    h1, h2 = two_of(party_dict['party'])
    party_len = len(party_dict['party'])
    heroines = 'heroines' if party_len > 1 else 'heroine'
    lassies = 'lassies' if party_len > 1 else 'lassie'
    await say(f"\"That\'s all the information I\'ve got for ye, fine {heroines},\" Happy says, as he abruptly returns to his work as a \"Tavern Keeper\".")
    await say("[narr]So, uh, now what?[/]")
    await pause()
    await say(f"{h1.name} decides to probe.  \"Excuse me, Happy?\" she begins.")
    await say(f"Happy looks up from the ledger he has already begun to update.  \"Aye?  Are we no' finished, {lassies}?\"")
    await say(f"{h1.name} just stares confusedly at Happy, as he mirrors the stare right back at her.")
    await say("\"Oh!\" he suddenly exclaims.  \"Ye must be wantin' tae stick around for some o' my famous mountain boar-skin stew?  Verra tasty.\"")
    await say(f"{h1.name} continues to stare at him.  [narr]Stifling her gag-reflex, no doubt![/]")
    await say("Happy smirks.  \"Och, right.  Ye want tae actually begin yer dungeon crawl,\" he says, as he adds a wink.")
    await pause()
    await say('Putting down his ledger, Happy brings the party over to a side room, filled nearly to capacity with barrels of god-knows-what, leaving just enough room to slink through.  The various smells emanating from the barrels are overwhelming.  [narr]Good thing you laid off that stew![/]')
    await say('As he nears the side room, Happy appears to begin playing a little game of invisible, drunk hopscotch.  [narr]What the fuck is this guy up to now?[/]')
    await say('As Happy lands his final awkward jump, there is a muffled \"click\".')
    await say('Just as the click is heard, a stack of barrels is suddenly yanked into a previously-unseen recess, leaving a large, shall we say, heroine-sized hole in the ground, behind it.')
    await pause()
    await say(f'\"Now, {lassies}, this is yer final chance tae decide - once ye drop intae that hole, there\'s nae comin\' back up this way.  Ever.\"')
    await say('\"Ye\'ll simply have tae ride oot the experience until The End.  What that end looks like, only fate can tell.\"')
    await say(f'\"I\'m not scared,\" starts {h1.name}, but before she can finish the thought, Happy shoves her into the hole.  [narr]What a rude piece of shit![/]')
    if party_len > 1:
        await say('Happy stares at the remaining party members.  \"Will ye be joinin\' her on yer own, or d\'ye need some - encouragement - as well?\"')
        await say(f'\"You know, for someone so \'helpful\', you certainly are an asshole,\" {h2.name} growls as she drops in.')
    last = 'the final heroine' if party_len > 1 else 'she'
    await say(f'\"Guid luck!\" he yells as {last} drops into the hole.')
    await say('\"Just another day at the Devil\'s Brew,\" Happy chuckles, as he returns to his work.')
    await pause()

# ---------- Stat raises (after every fight the party survives) --------------------------------------

# After each fight, about half the heroines get one of these, for the stat she improved most (in Happy's
# speech, the first time, every heroine gets one). {name} becomes her name. These are Claude's drafts:
# rewrite away. (Keep the words on the left of each colon as they are.)
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

# ---------- The dungeon ----------------------------------------------------------------------------

async def kobolds_appear(party_dict : dict, kobolds : list) -> None:
    """Plays when the Krazy Kobolds show up, before the fight. kobolds is the list of them (each has .name)."""
    party_len = len(party_dict['party'])
    h1, h2 = two_of(party_dict['party'])
    the_party = 'the party' if party_len > 1 else h1.name # who the kobolds are glaring at
    kobold_party_len = len(kobolds)
    k1, k2 = random.sample(kobolds, 2)
    if party_len > 1:
        await say('One-by-one, each party member drops into a basin of some foul-smelling liquid.  [narr]Probably the only thing that saved you from major injury on that fall![/]')
    else:
        await say(f'{h1.name} drops into a basin of some foul-smelling liquid.  [narr]Probably the only thing that saved you from major injury on that fall![/]')
    await say(f'\"I\'m going to kill the motherfucker next time I see him!  I hope I don\'t have to deal with that dick again!\" exclaims {h1.name}.')
    if party_len > 1:
        await say('The party takes in the surroundings, or at least they try to.  [narr]It is nearly pitch-black down here, motherfuckers!  Somebody light a match.[/]')
    else:
        await say(f'{h1.name} takes in her surroundings, or at least she tries to.  [narr]It is nearly pitch-black down here, motherfucker!  Somebody light a match.[/]')
    await pause()
    await say(f'{h1.name} tries to be patient and let her eyes adjust to the dark.')
    await say(f'[narr]Wait, what was that scratching sound?[/]  {h1.name} pauses to listen more closely.')
    await say(f'Something giggles in the dark.  Then something else giggles back.  [narr]{kobold_party_len} somethings, actually.[/]')
    await pause()
    await say(f'{h1.name} finally gets a torch burning, and just in time.')
    await say(f'To {the_party}\'s horror, {kobold_party_len} smallish creatures of varying, dark, mottled colors stream out from the shadows.')
    await say('The little bastards begin teleporting all over the chamber.  [narr]Well this is gonna suck![/]')
    if party_len > 1:
        await say(f'\"What the fuck are those things?\" asks {h2.name} in disbelief of what she is seeing.')
        await say(f'\"Ugh!\" grunts {h1.name}.  \"Those are kobolds.  Nasty little fuckers.  Watch out for their blink-stab!\"')
    else:
        await say('\"Kobolds.... I hate kobolds....\"')
    await pause()
    await say(f'As a group, the kobolds all glare at {the_party} and begin to hiss loudly.')
    await say('[narr]Them some crazy-looking motherfuckers, and they look hungry!  I wonder when they last ate?  Good luck![/]')
    await say(f'\"Already?\" sighs {h1.name}.  \"I\'m still barely recovered from that fat dwarf!\"  [narr]It doesn\'t appear that the kobolds care much what state you\'re in.[/]')
    await say(f'One of them stands tall and sticks out his chest.  \"Me {k1.name}, that {k2.name}.\"  [narr]These fuckers speak English???[/]  \"And you are...\"')
    await say(f'\"{h1.name},\" says {h1.name}, disgusted that she is even speaking to this miserable creature.')
    await pause()
    await say(f'\"Oh, good, good-good, good-good,\" chatters {k1.name} excitedly.')
    await say(f'\"Oh yeah?  And why is that so good?\" {h1.name} mumbles.')
    await say(f'\"Because we very hungry, but we no like eat food we don\'t know,\" says {k2.name}, as he hungrily licks his lips.')
    await say('Then, again, hissing as one, the kobolds charge in for battle.')
    await pause()

async def fight_won(party_dict : dict, mobs : list) -> None:
    """Plays when the party wins a dungeon fight, before the Token, loot and stat raises."""
    h1, h2 = two_of(party_dict['party'])
    await say("[narr]And THAT is how it's done.  Somebody check the bodies for shinies.[/]")
    await say()
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
