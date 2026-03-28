import json
from collections import Counter

with open("output/team_1.json") as f:
    d = json.load(f)

print("=== TRADES (should have no phantoms) ===")
for t in d["trades"]:
    print(f"  wk{t['week']}: sent {t['sent']} -> received {t['received']} (net {t['net']})")

print(f"\n=== HEATMAP SLOTS ===")
slots = Counter(r["slot"] for r in d["rosterHeatmap"])
print(f"  Slot distribution: {dict(slots)}")
for r in d["rosterHeatmap"][:8]:
    print(f"  {r['slot']:<5} {r['player']:<25} total={sum(r['weeks']):.0f}")

print(f"\n=== POINTS LEFT ON BENCH ===")
if d["pointsLeftOnBench"]:
    for b in d["pointsLeftOnBench"]:
        print(f"  wk{b['week']}: {b['benchPlayer']}({b['benchPts']}) > {b['startPlayer']}({b['startPts']}), diff={b['diff']}")
else:
    print("  (empty)")

print(f"\n=== OPTIMAL LINEUP ===")
ol = d["optimalLineup"]
print(f"  Total actual: {ol['totalActual']}")
print(f"  Total optimal: {ol['totalOptimal']}")
print(f"  Efficiency: {ol['efficiency']}")
worst = sorted(ol["weeklyComparison"], key=lambda x: -x["diff"])[:3]
for w in worst:
    print(f"    wk{w['week']}: actual={w['actualPts']} optimal={w['optimalPts']} diff={w['diff']}")

print(f"\n=== GRADES ===")
print(f"  {d['grades']}")

print(f"\n=== WEEKLY SCORES SANITY ===")
reg = [w for w in d["weeklyResults"] if w["week"] <= 18]
print(f"  Record: {sum(1 for w in reg if w['result']=='W')}-{sum(1 for w in reg if w['result']=='L')}")
print(f"  pointsFor: {d['team']['pointsFor']}")
print(f"  Sum of reg scores: {sum(w['score'] for w in reg):.1f}")
