"""Copy the game, change a few CSV numbers, run marginal.py on the copy.
usage: python variant.py NAME RUNS 'JSON edits'   edits: {"hero_stats.csv": {"Battle_Mage": {"low_st_health": 45}}, ...}"""
import csv, json, os, shutil, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))  # tools/balance
name, runs, edits = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
dst = os.path.join(HERE, 'variants', name)
shutil.rmtree(dst, ignore_errors=True)
shutil.copytree(os.path.dirname(os.path.dirname(HERE)), dst, ignore=shutil.ignore_patterns('.git', 'build', 'dist', '__pycache__', 'tools', 'saves', '*.sav'))
for fname, rows in edits.items():
    path = f'{dst}/supporting_docs/{fname}'
    with open(path, newline='', encoding='utf-8') as f:
        data = list(csv.DictReader(f)); cols = list(data[0].keys())
    for row in data:
        key = row[cols[0]]
        if key in rows:
            for col, val in rows[key].items():
                assert col in row, (fname, col); row[col] = str(val)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(data)
print(name, json.dumps(edits))
subprocess.run([sys.executable, os.path.join(HERE, 'marginal.py'), os.path.abspath(dst), runs, f'{dst}.jsonl'], check=True)
