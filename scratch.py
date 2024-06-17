import pandas as pd
import joblib as jb
import Slayer_Heroes

x = pd.read_csv('saved_parties/a.csv')

print(x)
print(type(x) == pd.DataFrame)

me = jb.load('saved_parties/ted.pkl')

print(me[1].starting_inv)

print(jb.load('saved_parties/ted.pkl'))

x = [1,2,3,4,'1','2','3','4']

x = input('count')
y = 1
while y == 1:
    try:
        x = int(x)
        print(type(x))
        y=0
    except(ValueError):
        x = input('try again')
