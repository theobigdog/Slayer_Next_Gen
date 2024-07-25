import Slayer_Accessory as acc
from Slayer_Accessory import wt, next, whine
import random
from colorama import Fore, Back, Style, Cursor
import time
import Slayer_Combat as combat

mobs = acc.get_mobs()
mob_equipment = acc.get_mob_equipment()

class Disgruntled_Dwarf:

    def __init__(self):
        self.name = "Happy"
        self.mob_class = 'Disgruntled Dwarf'
        self.attack_style = 'melee'
        self.is_dead = False
        self.enraged = False
        