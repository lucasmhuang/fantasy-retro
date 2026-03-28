import json
from pathlib import Path

output = Path("output")

print(f"{'Team':<30} {'Record':>7} {'PtsFor':>8} {'AllPlay':>10} {'Optimal%':>9} {'Trades':>6} {'BenchMiss':>9}")
print("-" * 90)

for f in sorted(output.glob("team_*.json")):
    d = json.load(open(f))
    t = d["team"]
    reg = [w for w in d["weeklyResults"] if w["week"] <= 18]
    rec = f"{sum(1 for w in reg if w['result']=='W')}-{sum(1 for w in reg if w['result']=='L')}"
    ol = d["optimalLineup"]
    bench_total = sum(b["diff"] for b in d["pointsLeftOnBench"])

    print(
        f"{t['name']:<30} {rec:>7} {t['pointsFor']:>8.0f} "
        f"{d['allPlayRecord']['winPct']:>9.1%} "
        f"{ol['efficiency']:>8.1%} "
        f"{len(d['trades']):>6} "
        f"{bench_total:>9.1f}"
    )

print()

# Check: total wins should equal total losses across league
total_w = 0
total_l = 0
for f in sorted(output.glob("team_*.json")):
    d = json.load(open(f))
    reg = [w for w in d["weeklyResults"] if w["week"] <= 18]
    total_w += sum(1 for w in reg if w["result"] == "W")
    total_l += sum(1 for w in reg if w["result"] == "L")

print(f"League W/L check: {total_w}W - {total_l}L (should be equal)")
