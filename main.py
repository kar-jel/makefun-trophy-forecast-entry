"""gta6-trophy-rarity-forecast-01's starter in Python 3.13 (standard library only): persistence.

The same program as starter/main.ts (the house baseline), number for number: it forecasts that every trophy's earn rate
on Exophase at the case's target is the rate in the case's last read, with a spread that widens like a random walk's on
the logit scale:

    q_tau = 100 / (1 + exp(-(logit(r) + z_tau * 0.5 * sqrt(d)))), rounded to 4 decimals (half up)

for each trophy, where r is its rate in the last read of the case's history (percent, clamped to 0.01..99.99 before the
logit), d the case's horizon in days (horizon_minutes / 1440) and z_tau the standard normal's quantile at each level
(0.05, 0.25, 0.5, 0.75, 0.95): -1.645, -0.674, 0, 0.674, 1.645.

How the grader runs it: `python3 -P -s /bot/main.py` (PYTHONHASHSEED=0) in python:3.13-slim, standard library only: no
network, no pip packages. -P keeps this file's directory OFF sys.path, so a module you ship beside main.py (say
/bot/model.py) imports only after the sys.path line below, which puts the directory first; -s drops user
site-packages.

What an entry must do:
  - read every <id>.in in the input directory (the grader runs one case at a time, with only that case's file there):
    JSON {"schema": "makefun/gta6-trophies-case/v1", "id", "at", "horizon_minutes", "target", "levels", "game",
    "trophies", "history", "notes"}, where `trophies` lists the case's trophies {id, name, description, tier, points,
    secret} and `history` every read before `at`, oldest first, each {slot, at, players_tracked, trophies_earned,
    rates}, `rates` in the order of `trophies` (null where that read lacked the trophy);
  - write <id>.out to the output directory: {"trophies": [{"id": 1, "q": [q05, q25, q50, q75, q95]}, ...]}, one row
    for each of the case's trophies, each id once, no other key, each q five finite numbers from 0 to 100 (percent),
    non-decreasing; at most 65,536 bytes. Anything else is an invalid case, scored as if every quantile equalled the
    trophy's rate in the last read, and an entry with an invalid case takes no prize.

Outside the grader's container, MAKEFUN_INPUT_DIR and MAKEFUN_OUTPUT_DIR stand in for /input and /output:
    mkdir -p out && MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import json
import math
import os
import sys
from pathlib import Path

# The grader's -P leaves /bot off sys.path: put it back first, so `import model` finds a model.py shipped beside this file.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import model

INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

# The quantile levels the contest scores, in the order each row lists them.
LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
# The standard normal's quantile at each level.
Z = [-1.645, -0.674, 0, 0.674, 1.645]
# The spread of a rate's move, in logit units per square-root day.
SIGMA = 0.5


def clamp(x: float) -> float:
    return min(99.99, max(0.01, x))


def logit(pct: float) -> float:
    return math.log(clamp(pct) / (100 - clamp(pct)))


def round4(x: float) -> float | int:
    """x rounded to 4 decimals, half up, as JavaScript's Math.round(x * 10000) / 10000 rounds it.

    A whole number comes back as an int, so json.dumps writes 100 where JavaScript writes 100 (not 100.0).
    """
    scaled = x * 10000
    whole = math.floor(scaled)
    if scaled - whole >= 0.5:
        whole += 1
    value = whole / 10000
    return int(value) if value.is_integer() else value


def forecast_case(case: dict, name: str) -> dict:
    if case["levels"] != LEVELS:
        raise ValueError(f"{name} asks for levels {case['levels']}, not {LEVELS}")
    return model.forecast(case)


def main() -> None:
    if "--self-test" in sys.argv:
        self_test()
        return
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # Every case file, in name order, so two runs write the same bytes.
    for path in sorted(INPUT_DIR.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        forecast = forecast_case(case, path.name)
        (OUTPUT_DIR / f"{path.stem}.out").write_text(json.dumps(forecast, separators=(",", ":")) + "\n", encoding="utf-8")


def self_test() -> None:
    import importlib.util, tempfile
    from datetime import datetime, timezone
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    spec=importlib.util.spec_from_file_location("local_score", "/home/agentuser/makefun/forecast/local_score.py")
    score=importlib.util.module_from_spec(spec); spec.loader.exec_module(score)
    INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", str(Path(__file__).resolve().parent / "input")))
    OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", str(Path(__file__).resolve().parent / "out")))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cases=[]
    for path in sorted(INPUT_DIR.glob("*.in")):
        case=json.loads(path.read_text()); out=forecast_case(case,path.name)
        dest=OUTPUT_DIR/(path.stem+".out"); dest.write_text(json.dumps(out,separators=(",",":"))+"\\n" if False else json.dumps(out,separators=(",",":"))+chr(10))
        qs=[r["q"] for r in out["trophies"]]; assert all(len(q)==5 and q==sorted(q) for q in qs)
        assert dest.stat().st_size<=65536
        print(case["id"],len(qs),min(q[2] for q in qs),max(q[2] for q in qs),max(q[4]-q[0] for q in qs))
        pred={r['id']:r['q'] for r in out['trophies']}
        print('story trophies: name | last rate | total gain | target median')
        for i,t in enumerate(case['trophies']):
            if t.get('description','').lower().startswith('complete chapter') or 'complete gone fishing' in t.get('description','').lower():
                last=case['history'][-1]['rates'][i]; q=pred[t['id']]
                print(f"{t['name']} | {last:.2f}% | {q[2]-last:+.2f} pp | {q[2]:.2f}%")
        cases.append(case)
    for speed,gain in ((1.2,1.0),(2.0,1.6),(3.5,2.2)):
        c=score.synth_case("synthetic",60,108,tau_days=speed,gain=gain)
        pred=model.forecast(c); forecast={r["id"]:r["q"] for r in pred["trophies"]}
        previous={}
        for i,t in enumerate(c["trophies"]):
            last=c["history"][-1]["rates"][i]; lg=score.logit(last); spread=.5*math.sqrt(c["horizon_minutes"]/1440)
            previous[t["id"]]=[score.inv_logit(lg+z*spread) for z in score.Z]
        our=score.case_loss(c,forecast); prev=score.case_loss(c,previous); base=score.case_loss(c,score.house_baseline(c))
        print("synthetic",speed,gain,"new",round(our,6),"previous",round(prev,6),"baseline",round(base,6))


if __name__ == "__main__":
    main()
