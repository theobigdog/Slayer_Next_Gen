import Slayer_Accessory as acc
import random
import time
import cursor
from colorama import Fore, Back, Style, Cursor

# Make coloring faster

b = Fore.BLACK + Style.NORMAL
g = Fore.GREEN + Style.BRIGHT
r = Fore.RED + Style.BRIGHT
b_r = Back.RED
reset = Style.RESET_ALL

# functions for opening

def grab_letter(letter: str, line: int, color: str, letters: dict) -> str:
    return color + letters[letter][line]

def append_letters (statement: str, line: int, colors: dict) -> str:
    text_line = ''
    for letter in statement:
        if statement == slayer:
            text_line += grab_letter(letter, line, colors[letter], slayer_letters)
        elif statement == loser:
            text_line += grab_letter(letter, line, colors[letter], loser_letters)
        else:
            print('No.')
    return text_line

def upd_gap(gap: float, divisor: float) -> tuple:
    time.sleep(gap)
    gap = gap / (0.0125 + divisor)
    divisor = divisor + 0.0005
    return gap, divisor

def cursor_pos():
    print(Cursor.POS(5,5))

def next_letter(top_end: int, colors_list: list, gap: float, divisor: float, statement: str) -> tuple:
    for _ in range(1, top_end):
        random_colors = random.randint(0, len(colors_list)-1)
        cursor_pos()
        if statement == slayer:
            normalizer = sl_S
        elif statement == loser:
            normalizer = L_L
        else:
            pass # leave room for other potential graphics
        for line in range(len(normalizer)):
            print(append_letters(statement, line, colors_list[random_colors]))
        gap, divisor = upd_gap(gap, divisor)
    return gap, divisor

def slayer_opening():
    dev_mode = acc.dev_mode()
    if dev_mode:
        gap = 0.05
        divisor = 2
    else:
        gap = 0.15
        divisor = 1.01
    cursor.set_cursor_visible(False)
    gap, divisor = next_letter(40, colors_, gap, divisor, slayer)
    gap, divisor = next_letter(25, colors_s, gap, divisor, slayer)
    gap, divisor = next_letter(27, colors_sl, gap, divisor, slayer)
    gap, divisor = next_letter(31, colors_sla, gap, divisor, slayer)
    gap, divisor = next_letter(27, colors_slay, gap, divisor, slayer)
    gap, divisor = next_letter(25, colors_slaye, gap, divisor, slayer)
    cursor_pos()
    for line in range(len(sl_S)):
        print(append_letters(slayer, line, colors_slayer[0]))
    time.sleep(0.35)
    print(Cursor.POS(155,19), "v 2.0")
    time.sleep(0.85)
    print()
    print(r + Cursor.POS(30,25) + (" WE DARE YOU TO ENTER!!  MUA HA-HA HA-HA!!!").center(80, '*'))
    cursor.set_cursor_visible(True)
    print(reset)

def loser_banner():
    dev_mode = acc.dev_mode()
    if dev_mode:
        gap = 0.05
        divisor = 2
    else:
        gap = 0.45
        divisor = 1.1
    cursor.set_cursor_visible(False)
    for _ in range(1,10):
        for version in range(6):
            acc.wt()
            x = random.randint(1,50)
            y = random.randint(1,20)
            print(Cursor.POS(x,y))
            for line in range(len(L_L)):
                print(append_letters(loser, line, letter_colors_loser[version]))
            time.sleep(gap)
            gap = gap / divisor
        time.sleep(gap)
        gap = gap / divisor
    acc.wt()
    x = random.randint(1,50)
    y = random.randint(1,20)
    print(Cursor.POS(x,y))
    for line in range(len(L_L)):
        print(append_letters(loser, line, letter_colors_loser[6]))
    time.sleep(0.75)
    print()
    print()
    cursor.set_cursor_visible(True)
    print(Fore.WHITE + Style.BRIGHT)

# Establish letters for opening sequence

sl_S1 = '        SSSSSSS        '
sl_S2 = '     SSSSSSSSSSSS      '
sl_S3 = '   SSSSSS      SSSS    '
sl_S4 = '  SSSSS    S      SS   '
sl_S5 = ' SSSSS     SS      SS  '
sl_S6 = ' SSSSSS    SSS      S  '
sl_S7 = '  SSSSSSSSSSSSSS       '
sl_S8 = '    SSSSSSSSSSSSSSS    '
sl_S9 = ' S     SSS    SSSSSS   '
sl_S10= ' SS     SS      SSSSS  '
sl_S11= ' SSS     S     SSSSS   '
sl_S12= '  SSSS      SSSSSS     '
sl_S13= '   SSSSSSSSSSSSS       '
sl_S14= '     SSSSSSSSS         '
sl_S = [sl_S1,sl_S2,sl_S3,sl_S4,sl_S5,sl_S6,sl_S7,sl_S8,sl_S9,sl_S10,sl_S11,sl_S12,sl_S13,sl_S14]

sl_L1 = '     L                '
sl_L2 = '   LL                 '
sl_L3 = ' LLL                  '
sl_L4 = 'LLL                   '
sl_L5 = 'LLL                   '
sl_L6 = 'LLLL                  '
sl_L7 = ' LLLL                 '
sl_L8 = '  LLLL                '
sl_L9 = '  LLLL                '
sl_L10= '  LLLL             L  '
sl_L11= ' LLLL           LLL   '
sl_L12= 'LLLLL       LLLLLL    '
sl_L13= 'LLLLLLLLLLLLLLLL      '
sl_L14= ' LLLLLLLLLL           '
sl_L = [sl_L1,sl_L2,sl_L3,sl_L4,sl_L5,sl_L6,sl_L7,sl_L8,sl_L9,sl_L10,sl_L11,sl_L12,sl_L13,sl_L14]

sl_A1 = '          AAA            '
sl_A2 = '         AAAAA           '
sl_A3 = '        AAA AAA          '
sl_A4 = '       AAA │ AAA         '
sl_A5 = '      AAA  ║  AAA        '
sl_A6 = '     AAA   ║   AAA       '
sl_A7 = '     AAAA  ║  AAAA       '
sl_A8 = '    AAAAAAA║AAAAAAA      '
sl_A9 = '    AAAAAAAAAAAAAAA      '
sl_A10= 'A  AAAAAA  ║  AAAAAA  A  '
sl_A11= 'A  AAAAA   ║   AAAAA  A  '
sl_A12= 'AA AAAA  ╒═ф═╕  AAAA AA  '
sl_A13= ' AAAAA     ▒     AAAAA   '  
sl_A14= '   AA      ╩      AA     '  
sl_A = [sl_A1,sl_A2,sl_A3,sl_A4,sl_A5,sl_A6,sl_A7,sl_A8,sl_A9,sl_A10,sl_A11,sl_A12,sl_A13,sl_A14]

sl_Y1 = '   YYYYYYYYYYY  YYYYYYYYYYYY '
sl_Y2 = '       YYYYYY      YYYYYYY   '
sl_Y3 = '        YYYYY       YYYYYY   '
sl_Y4 = '         YYYYY      YYYYY    '
sl_Y5 = '          YYYYYY    YYYYY    '
sl_Y6 = '            YYYYYY  YYYYY    '
sl_Y7 = 'Y             YYYYYYYYYY     ' 
sl_Y8 = 'Y               YYYYYYY      '
sl_Y9 = 'YY               YYYYY       '
sl_Y10= 'YYY             YYYYY        '
sl_Y11= ' YYYY          YYYYY         '
sl_Y12= '  YYYYY     YYYYYYY          '
sl_Y13= '   YYYYYYYYYYYYYY            '
sl_Y14= '      YYYYYYYY               ' 
sl_Y = [sl_Y1,sl_Y2,sl_Y3,sl_Y4,sl_Y5,sl_Y6,sl_Y7,sl_Y8,sl_Y9,sl_Y10,sl_Y11,sl_Y12,sl_Y13,sl_Y14]

sl_E1 = ' EEEEEEEEEEEEEEEEEE      '
sl_E2 = '    EEEEEE       EEEE    '
sl_E3 = '  EEEEEE             E   '
sl_E4 = '  EEEE                   '
sl_E5 = '  EEEE                   '
sl_E6 = '  EEEEEE                 '
sl_E7 = '   EEEEEEEEEEEEEE        '
sl_E8 = '    EEEEEEEEE            '
sl_E9 = '   EEEEEEE               '
sl_E10= '  EEEEEE                 '
sl_E11= ' EEEEEE               E  '
sl_E12= ' EEEEEEEE           EE   '
sl_E13= '  EEEEEEEEEEEEEEEEEEEE   '
sl_E14= '   EEEEEEEEEEEEEEE       '
sl_E = [sl_E1,sl_E2,sl_E3,sl_E4,sl_E5,sl_E6,sl_E7,sl_E8,sl_E9,sl_E10,sl_E11,sl_E12,sl_E13,sl_E14]

sl_R1 = 'RRRRRRRRRRRRRRRRRRRR  TM    '
sl_R2 = '  RRRRRRRRRRRRRRRRRRRR      '
sl_R3 = '   RRRRR   ¥      RRRRR     '
sl_R4 = '   RRRR    ▒       RRRR     '
sl_R5 = '   RRRR  ╘═ф═╛    RRRR      '
sl_R6 = '  RRRRRRR  ║   RRRRRR       '
sl_R7 = ' RRRRRRRRRR║RRRRRRRR        '
sl_R8 = '  RRRRRRRRRRRRRRR           '
sl_R9 = '   RRRRR   ║RRRRRR          '
sl_R10= '   RRRRR   ║  RRRRRR        '
sl_R11= '   RRRR    ║    RRRRR       '
sl_R12= '  RRRRR    ║     RRRRR      '
sl_R13= ' RRRRR     │      RRRRRR    '
sl_R14= 'RRRRRRRR   │       RRRRRRRRR'
sl_R = [sl_R1,sl_R2,sl_R3,sl_R4,sl_R5,sl_R6,sl_R7,sl_R8,sl_R9,sl_R10,sl_R11,sl_R12,sl_R13,sl_R14]

slayer_letters = {
    "S" : sl_S,
    "L" : sl_L,
    "A" : sl_A,
    "Y" : sl_Y,
    "E" : sl_E,
    "R" : sl_R
}
slayer = "SLAYER"

letter_colors_sl = {
    "a" : {"S":b, "L":b, "A":b, "Y":b, "E":b, "R":b},
    "b" : {"S":r, "L":b, "A":b, "Y":b, "E":b, "R":b},
    "c" : {"S":b, "L":r, "A":b, "Y":b, "E":b, "R":b},
    "d" : {"S":b, "L":b, "A":r, "Y":b, "E":b, "R":b},
    "e" : {"S":b, "L":b, "A":b, "Y":r, "E":b, "R":b},
    "f" : {"S":b, "L":b, "A":b, "Y":b, "E":r, "R":b},
    "g" : {"S":b, "L":b, "A":b, "Y":b, "E":b, "R":r},
    "h" : {"S":r, "L":r, "A":b, "Y":b, "E":b, "R":b},
    "i" : {"S":r, "L":b, "A":r, "Y":b, "E":b, "R":b},
    "j" : {"S":r, "L":b, "A":b, "Y":r, "E":b, "R":b},
    "k" : {"S":r, "L":b, "A":b, "Y":b, "E":r, "R":b},
    "l" : {"S":r, "L":b, "A":b, "Y":b, "E":b, "R":r},
    "m" : {"S":r, "L":r, "A":r, "Y":b, "E":b, "R":b},
    "n" : {"S":r, "L":r, "A":b, "Y":r, "E":b, "R":b},
    "o" : {"S":r, "L":r, "A":b, "Y":b, "E":r, "R":b},
    "p" : {"S":r, "L":r, "A":b, "Y":b, "E":b, "R":r},
    "q" : {"S":r, "L":r, "A":r, "Y":r, "E":b, "R":b},
    "r" : {"S":r, "L":r, "A":r, "Y":b, "E":r, "R":b},
    "s" : {"S":r, "L":r, "A":r, "Y":b, "E":b, "R":r},
    "t" : {"S":r, "L":r, "A":r, "Y":r, "E":r, "R":b},
    "u" : {"S":r, "L":r, "A":r, "Y":r, "E":b, "R":r},
    "v" : {"S":r, "L":r, "A":r, "Y":r, "E":r, "R":r},
}

colors_ = [letter_colors_sl['a'], letter_colors_sl['b'], letter_colors_sl['c'], letter_colors_sl['d'], letter_colors_sl['e'], letter_colors_sl['f'], letter_colors_sl['g']]
colors_s = [letter_colors_sl['b'], letter_colors_sl['h'], letter_colors_sl['i'], letter_colors_sl['j'], letter_colors_sl['k'], letter_colors_sl['l']]
colors_sl = [letter_colors_sl['h'], letter_colors_sl['m'], letter_colors_sl['n'],  letter_colors_sl['o'], letter_colors_sl['p']]
colors_sla = [letter_colors_sl['m'], letter_colors_sl['q'], letter_colors_sl['r'], letter_colors_sl['s']]
colors_slay = [letter_colors_sl['q'], letter_colors_sl['t'], letter_colors_sl['u']]
colors_slaye = [letter_colors_sl['t'], letter_colors_sl['v']]
colors_slayer = [letter_colors_sl['v']]


# Establish letters for losing

L1 = ' L                      '
L2 = ' LL                     '
L3 = ' LLLL                   '
L4 = ' LLLL                   '
L5 = ' LLLL                   '
L6 = ' LLLL                   '
L7 = ' LLLL                   '
L8 = ' LLLL                   '
L9 = ' LLLLL                  '
L10= ' LLLLL                  '
L11= '  LLLLL                 '
L12= '  LLLLLLLL              '
L13= '   LLLLLLLLLLLLLLLLLL   '
L14= '     LLLLLLLLLLLLLLLLLLL'
L_L = [L1,L2,L3,L4,L5,L6,L7,L8,L9,L10,L11,L12,L13,L14]

O1 = '          OOOOOOO            '
O2 = '      OOOO▒▒▒▒▒▒▒OOOO        '
O3 = '   OOO▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒OOO     '
O4 = '  OO▒▒▒▒≈▒▒▒≈▒▒▒▒▒▒▒▒▒▒OO    '
O5 = ' OO▒▒▒▒▒Ω▒▒▒Ω▒▒▒▒▒▒▒▒▒▒▒OO   '
O6 = 'O▒▒▒▒▒)▒▒▒‼▒▒▒)▒▒▒▒¥▒▒▒▒▒▒O  '
O7 = 'O▒▒▒▒▒▒▒▼▼▼▼▼▒▒▒▒▒▒▓▒▒▒▒▒▒O  '
O8 = 'O▒▒▒▒▒▒▒▲▲▲▲▲▒▒▒▒▒╘ф╛▒▒▒▒▒O  '
O9 = 'O▒▒▒▒▒▒▒▒▒∞▒▒▒▒▒▒▒▒║▒▒▒▒▒▒O  '
O10= ' OO▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒║▒▒▒▒OO   '
O11= '  OO▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│▒▒▒OO    '
O12= '   OOO▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒OOO     '
O13= '      OOOO▒▒▒▒▒▒▒OOOO        '
O14= '          OOOOOOO            '
L_O = [O1,O2,O3,O4,O5,O6,O7,O8,O9,O10,O11,O12,O13,O14]

S1 = '     SSSSSSSSSSSSSS       '
S2 = '  SSSSSSSSSSSSSSSSSSS     '
S3 = ' SSSSSS            SSs    '
S4 = 'SSSSS                s    '
S5 = 'SSSSSs                    '
S6 = ' SSSSSSSSs                '
S7 = '  SSSSSSSSSSSSS           '
S8 = '      SSSSSSSSSSSSSs      '
S9 = 's           SSSSSSSSSS    '
S10= 'S                SSSSSS   '
S11= 'SSS             SSSSSS    '
S12= ' SSSS        SSSSSSSS     '
S13= '  SSSSSSSSSSSSSSSS        '
S14= '    SSSSSSSSSSS           '
L_S = [S1,S2,S3,S4,S5,S6,S7,S8,S9,S10,S11,S12,S13,S14]

E1 = '    EEEEEEEEEEEEEEE       '
E2 = ' EEEEEEEEEEEEEEEEEEEE     '
E3 = 'EEEEEE             EEE    '
E4 = 'EEEE                 E    '
E5 = 'EEEE                      '
E6 = 'EEEEEEE                   '  
E7 = ' EEEEEEEEEEEEE            '
E8 = '  EEEEEEEE                '
E9 = ' EEEEEE                   '
E10= 'EEEEE                E    '
E11= 'EEEEEE             EEE    '
E12= ' EEEEEEEE     EEEEEEE     '
E13= '  EEEEEEEEEEEEEEEEE       '
E14= '     EEEEEEEEEEE          '
L_E = [E1,E2,E3,E4,E5,E6,E7,E8,E9,E10,E11,E12,E13,E14]

R1 = ' RR   RRRRRRRRRRRRRR      '
R2 = ' RRR RRRRRRRRRRRRRRRRR    '
R3 = ' RRRRRRR          RRRRR   '
R4 = ' RRRRR             RRRR   '
R5 = ' RRRR            RRRRR    '
R6 = ' RRRRR       RRRRRRR      '
R7 = 'RRRRRRRRRRRRRRRRR         '
R8 = 'RRRRRRRRRRRRRRR           '
R9 = ' RRRRR    RRRRRRR         '
R10= '  RRRR       RRRRRR       '
R11= '  RRRR          RRRRR     '
R12= '  RRRR           RRRRR    '
R13= '  RRRR            RRRRR   '
R14= ' RRRRRRR         RRRRRRRR '
L_R = [R1,R2,R3,R4,R5,R6,R7,R8,R9,R10,R11,R12,R13,R14]

loser_letters = {
    "L" : L_L,
    "O" : L_O,
    "S" : L_S,
    "E" : L_E,
    "R" : L_R
}
loser = "LOSER"

letter_colors_loser = [
    {"L":b, "O":b, "S":b, "E":b, "R":b},
    {"L":g, "O":b, "S":b, "E":b, "R":b},
    {"L":b, "O":g, "S":b, "E":b, "R":b},
    {"L":b, "O":b, "S":g, "E":b, "R":b},
    {"L":b, "O":b, "S":b, "E":g, "R":b},
    {"L":b, "O":b, "S":b, "E":b, "R":g},
    {"L":g, "O":g, "S":g, "E":g, "R":g},
]
