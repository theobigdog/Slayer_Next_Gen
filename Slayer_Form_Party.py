import Slayer_Accessory as acc
import pandas as pd
import numpy as np
import random
from colorama import Fore, Back, Style, Cursor, win32, init
import time
import string


def get_name() -> str:
    print("Greetings!")
    name = str(input('What is your name?  If you have one that is.  ')).title()
    return name

def get_saved_game():
    save_name = str(input('The name of your saved party, please:  '))
    if not save_name.endswith('csv'):
        save_name += '.csv'
    if not save_name.startswith('saved_parties/'):
        save_name = 'saved_parties/' + save_name
    try:
        saved_party = pd.read_csv(save_name)
    except(ValueError, FileNotFoundError):
        saved_party = "invalid"
    return saved_party

def create_new_party(name: str) -> pd.DataFrame:
    new_party = None
    return new_party

def form_party(name : str) -> pd.DataFrame:
    repeat_customer = acc.yes_no(input(f"Have we seen you here before, uh, what was it again?  Oh, right, {name}.  That's a weird freakin' name, but whatever.\nOk, {name}, do you have an old party to further abuse? I mean, load?\n(If you don't actually have a save or you forgot the name just enter 'No'):  "))
    saved_party = None
    if repeat_customer:
        acceptable = False
        saved_party = get_saved_game()
        while (not acceptable) and (repeat_customer):
            if type(saved_party) != pd.DataFrame and repeat_customer == True:
                repeat_customer = acc.yes_no(input('Are you having trouble understanding?  Yes, or No, do you have a valid saved party?:  '))
                if repeat_customer:
                    saved_party = get_saved_game()
                else:
                    repeat_customer = False
                    saved_party = create_new_party(name)
                    input('created a new party')
            else:
                acceptable = True
                input('Your party was imported successfully')
    else:
        saved_party = create_new_party(name)
        input('created a new party')
    return saved_party