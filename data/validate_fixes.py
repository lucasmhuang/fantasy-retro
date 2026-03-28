import json

with open("output/team_1.json") as f:
    d = json.load(f)

print("=== TRADES (should be reversed from before) ===")
for t in d["trades"]:
    print(f"  wk{t['week']}: SENT {t['sent']} -> RECEIVED {t['received']} (net {t['net']})")

print(f"\n=== WAIVER PICKUPS (Deni Avdija should NOT be here) ===")
names = [p["player"] for p in d["waiverPickups"]]
print(f"  Players: {names}")
deni = any("Deni" in n or "Avdija" in n for n in names)
print(f"  Deni Avdija present: {deni}")

print(f"\n=== BENCH MISPLAYS (adjusted weeks skipped) ===")
if d["pointsLeftOnBench"]:
    for b in d["pointsLeftOnBench"]:
        print(f"  wk{b['week']}: {b['benchPlayer']}({b['benchPts']}) > {b['startPlayer']}({b['startPts']}), diff={b['diff']}")
else:
    print("  (empty)")

print(f"\n=== EVENTS (check trade events read correctly) ===")
for w in d["weeklyResults"]:
    if "event" in w and "Traded" in w["event"]:
        print(f"  wk{w['week']}: {w['event']}")
