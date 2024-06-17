import pandas as pd
import joblib as jb
import Slayer_Heroes

x = pd.read_csv('saved_parties/a.csv')

print(x)
print(type(x) == pd.DataFrame)

me = jb.load('saved_parties/ted.pkl')

print(me[1].starting_inv)