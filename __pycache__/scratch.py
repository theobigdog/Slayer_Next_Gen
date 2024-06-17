import pandas as pd

x = pd.read_csv('saved_parties/a.csv')

print(x)
print(type(x) == pd.DataFrame)