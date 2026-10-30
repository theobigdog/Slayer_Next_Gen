import Slayer_Accessory as acc
from Slayer_Accessory import pause


mobs_df = acc.get_mobs()

class Disgruntled_Dwarf:

    def __init__(self, name : str):
        self.name = name
        self.mob_class = 'Disgruntled Dwarf'
        acc.initialize_mob(self, mobs_df)
        self.is_boss = True
        
    def enrage(self):
        print(f"\n\n{self.name} gasps loudly.  \"Now that one fucking hurt!!\"")
        pause()
        print(f"\n{self.name} suddenly bulges out in all directions.  He becomes a rippling mass of what looks like pure muscle - the veins in his neck and forearms swell to such a size, they look like they might rupture.\n")
        print("\"Oh lassies,\" he growls, \"you really fucked up now!  Now?  NOW I'M ANGRY!!!!\"")
        self.is_dead = False # setting to True is necessary just in case the blow that caused Happy to enrage also "killed" him
        self.enraged = True
        self.starting_health = self.stats['enraged_hp']
        self.health = self.stats['enraged_hp']

    def trigger_happy_wipe(self, party_dict : dict, happy_killed : bool) -> dict:
        if happy_killed:
            print('Add Immortal Happy -> wipes the party anyway narration')
        else:
            print('Add wipe narration here')
        print('Add specific Happy narration here for getting the loot, maybe explaining whats up, though this part may not be necessary to explain')
        party_dict = acc.get_loot(self, party_dict)
        print('Add specific Happy narration here for get stat increases, to explain how it works even, maybe?  Actual stats will never be shown, just set and updated in the background, so nothing should actually print from this function when finished.')
        print('1 idea:  "Now listen close, young lassies, I don\'t know exactly how this could be, but this last battle seems to have increased certain skills, for each of you, at a rate I didn\'t think was possible for folks to improve, but you appear to be no average adventurers!')
        print('Don\'t ask me who improved in what, or by how much.')
        print('Also, I would expect this to occur again after each successful encounter you wee lassies may face.')
        pause()
        party_dict = acc.get_stat_increases(party_dict)
        return party_dict


class Drunk_Dwarf:

    def __init__(self, name : str):
        self.name = name
        self.mob_class = 'Drunk Dwarf'
        acc.initialize_mob(self, mobs_df)
        self.is_boss = False