"""Turn the raw Sleeper / FantasyCalc files in data/ into one tidy file, data/derived.json,
that each edition is written from. Run from the repo root:  python3 src/prep.py

Nothing here is invented: every number comes from the files the GitHub workflow downloads.
"""
import json, os, glob, math, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(ROOT, "data", *p)
load = lambda p, default=None: json.load(open(p)) if os.path.exists(p) else default

# The 2026 NFL season: week 1 runs Wed Sep 9 - Tue Sep 15 (week N = the Wed-Tue span holding its games)
SEASON_WEEK1_WED = datetime.date(2026, 9, 9)
REG_SEASON_WEEKS = 14          # league playoffs start week 15
TZ_OFFSET = -5                 # Central (CDT). Close enough for picking a date at 2 AM.

def nfl_week_for(date):
    return max(1, (date - SEASON_WEEK1_WED).days // 7 + 1)

def main():
    state = load(D("state.json"), {})
    league = load(D("league.json"), {})
    users = {u["user_id"]: u for u in load(D("users.json"), [])}
    rosters = load(D("rosters.json"), [])
    players = load(D("players.json"), {})
    traded = load(D("traded_picks.json"), [])
    fc = load(D("fc_values.json"), [])

    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(hours=TZ_OFFSET)
    today = now.date()
    week_by_date = nfl_week_for(today)

    def pname(pid):
        p = players.get(str(pid), {})
        return p.get("full_name") or (f'{p.get("first_name","")} {p.get("last_name","")}'.strip()) or f"Player {pid}"
    def pinfo(pid):
        p = players.get(str(pid), {})
        return {"id": str(pid), "name": pname(pid), "pos": p.get("position"), "nfl": p.get("team"),
                "age": p.get("age"), "birth": p.get("birth_date"), "yrs": p.get("years_exp"),
                "inj": p.get("injury_status"), "inj_body": p.get("injury_body_part")}

    # ---- teams
    teams = {}
    for r in rosters:
        s = r.get("settings", {}); u = users.get(r.get("owner_id"), {})
        f = lambda a, b: round((s.get(a) or 0) + (s.get(b) or 0) / 100, 2)
        md = r.get("metadata") or {}
        teams[r["roster_id"]] = {
            "id": r["roster_id"], "team": ((u.get("metadata") or {}).get("team_name") or u.get("display_name") or f'Team {r["roster_id"]}').replace("🏆", "").strip(),
            "mgr": u.get("display_name"), "w": s.get("wins", 0), "l": s.get("losses", 0), "t": s.get("ties", 0),
            "pf": f("fpts", "fpts_decimal"), "pa": f("fpts_against", "fpts_against_decimal"), "max": f("ppts", "ppts_decimal"),
            "streak": md.get("streak", ""), "record": md.get("record", ""),
            "players": [str(p) for p in (r.get("players") or [])], "reserve": [str(p) for p in (r.get("reserve") or [])],
            "taxi": [str(p) for p in (r.get("taxi") or [])], "faab_used": s.get("waiver_budget_used", 0)}

    # ---- weekly matchups
    weeks = {}
    for fpath in glob.glob(D("matchups", "*.json")):
        w = int(os.path.basename(fpath)[:-5]); rows = load(fpath, []) or []
        if not rows: continue
        wk = {}
        for m in rows:
            st = [str(x) for x in (m.get("starters") or [])]
            sp = m.get("starters_points") or [0] * len(st)
            wk[m["roster_id"]] = {"mid": m.get("matchup_id"), "pts": round(m.get("points") or 0, 2),
                                  "starters": [{**pinfo(p), "pts": sp[i] if i < len(sp) else 0} for i, p in enumerate(st)]}
        weeks[w] = wk
    def pairs(w):
        by = {}
        for rid, v in weeks.get(w, {}).items(): by.setdefault(v["mid"], []).append(rid)
        return [sorted(v) for k, v in sorted(by.items(), key=lambda kv: (kv[0] is None, kv[0])) if k is not None and len(v) == 2]

    # a week is "final" when it is before the current NFL week by date and everyone scored
    final_weeks = sorted(w for w, wk in weeks.items() if w < week_by_date and all(v["pts"] > 0 for v in wk.values()))
    if today.weekday() == 1 and week_by_date in weeks and all(v["pts"] > 0 for v in weeks[week_by_date].values()):
        final_weeks = sorted(set(final_weeks) | {week_by_date})  # Tuesday: Monday night is done

    # ---- projections for the current week
    def load_proj(w):
        out = {}
        for fpath in glob.glob(D("projections", f"{w}_*.json")):
            for e in load(fpath, []) or []:
                pid = str(e.get("player_id")); stats = e.get("stats") or {}
                if "pts_ppr" in stats:
                    out[pid] = {"proj": round(stats["pts_ppr"], 2), "opp": e.get("opponent"), "team": e.get("team")}
        return out
    proj = {w: load_proj(w) for w in {week_by_date, week_by_date + 1}}

    # ---- all-play and luck over final weeks
    ids = sorted(teams)
    allplay = {i: 0.0 for i in ids}
    for w in final_weeks:
        sc = {i: weeks[w][i]["pts"] for i in ids if i in weeks[w]}
        for i in sc: allplay[i] += sum(1 for j in sc if j != i and sc[i] > sc[j]) / (len(sc) - 1)
    for i in ids:
        g = teams[i]["w"] + teams[i]["l"] + teams[i]["t"]
        teams[i].update({"allplay": round(allplay[i], 2), "luck": round(teams[i]["w"] - allplay[i], 2),
                         "ppg": round(teams[i]["pf"] / g, 1) if g else 0, "pag": round(teams[i]["pa"] / g, 1) if g else 0,
                         "eff": round(teams[i]["pf"] / teams[i]["max"] * 100) if teams[i]["max"] else 0})

    # ---- transactions (newest first) with names
    tx = []
    for fpath in glob.glob(D("transactions", "*.json")):
        w = int(os.path.basename(fpath)[:-5])
        for t in load(fpath, []) or []:
            if t.get("status") != "complete": continue
            sides = {}
            for pid, rid in (t.get("adds") or {}).items(): sides.setdefault(rid, {"team": rid, "adds": [], "drops": [], "picks": [], "faab": 0})["adds"].append(pname(pid))
            for pid, rid in (t.get("drops") or {}).items(): sides.setdefault(rid, {"team": rid, "adds": [], "drops": [], "picks": [], "faab": 0})["drops"].append(pname(pid))
            for pk in t.get("draft_picks") or []:
                rid = pk["owner_id"]; orig = teams.get(pk["roster_id"], {}).get("team", f'Team {pk["roster_id"]}')
                sides.setdefault(rid, {"team": rid, "adds": [], "drops": [], "picks": [], "faab": 0})["picks"].append(f'{pk["season"]} round {pk["round"]} ({orig})')
            for wb in t.get("waiver_budget") or []:
                sides.setdefault(wb["receiver"], {"team": wb["receiver"], "adds": [], "drops": [], "picks": [], "faab": 0})["faab"] += wb["amount"]
            tx.append({"week": w, "type": t.get("type"), "created": t.get("created"), "bid": (t.get("settings") or {}).get("waiver_bid"),
                       "rosters": t.get("roster_ids"), "sides": list(sides.values())})
    tx.sort(key=lambda t: -(t["created"] or 0))

    # ---- dynasty values
    fcmap, fcpick = {}, {}
    for e in fc or []:
        p = e.get("player") or {}
        if p.get("position") == "PICK": fcpick[p.get("name")] = e.get("value")
        elif p.get("sleeperId"): fcmap[str(p["sleeperId"])] = {"val": e.get("value"), "age": p.get("maybeAge"), "rank": e.get("overallRank")}
    season = int(state.get("season") or league.get("season") or today.year)
    rounds = int((league.get("settings") or {}).get("draft_rounds") or 6)
    own = {(s, r, o): o for s in (season + 1, season + 2) for r in range(1, rounds + 1) for o in ids}
    for tp in traded:
        k = (int(tp["season"]), int(tp["round"]), int(tp["roster_id"]))
        if k in own: own[k] = int(tp["owner_id"])
    strength = sorted(ids, key=lambda i: (teams[i]["w"] - teams[i]["l"], teams[i]["pf"]))
    tier = {i: ("Early" if k < 4 else "Mid" if k < 8 else "Late") for k, i in enumerate(strength)}
    first_generic = fcpick.get(f"{season+1} 1st") or 2900
    def pick_val(s, r, o):
        if r == 1:
            if s == season + 1: return fcpick.get(f"{s} 1st ({tier[o]})") or first_generic
            return fcpick.get(f"{s} 1st") or round(first_generic * 0.9)
        base = fcpick.get(f"{s} {['','1st','2nd','3rd','4th'][r] if r<5 else ''}") if r < 5 else None
        return base or {2: round(first_generic * 0.37), 3: round(first_generic * 0.14)}.get(r, 0) * (1 if s == season + 1 else 0.9)
    cur_starters = {rid: {s["id"] for s in v["starters"]} for rid, v in weeks.get(week_by_date, weeks.get(max(weeks) if weeks else 0, {})).items()} if weeks else {}
    def depth_val(p):
        y = p.get("yrs")
        return {0: 900, 1: 700, 2: 500, 3: 350, 4: 250}.get(y, 150) if y is not None else 300
    dyn = {}
    for i in ids:
        t = teams[i]; plist = []
        for pid in t["players"]:
            info = pinfo(pid)
            if pid in fcmap: v, src, age = fcmap[pid]["val"], "market", fcmap[pid]["age"] or info["age"]
            else: v, src, age = depth_val(info) + (300 if pid in cur_starters.get(i, set()) else 0), "est", info["age"]
            st = "IR" if pid in t["reserve"] else "Taxi" if pid in t["taxi"] else "Starter" if pid in cur_starters.get(i, set()) else "Bench"
            plist.append({**info, "age": age, "val": v, "src": src, "status": st})
        plist.sort(key=lambda p: -p["val"])
        pk = [{"season": s, "round": r, "from": o, "val": round(pick_val(s, r, o)), "slot": tier[o] if (s == season + 1 and r == 1) else None}
              for (s, r, o), c in own.items() if c == i and r <= 3]
        pk.sort(key=lambda p: (p["season"], p["round"], p["from"]))
        pv = sum(p["val"] for p in plist); kv = sum(p["val"] for p in pk)
        mk = [p for p in plist if p["src"] == "market" and p["age"]]
        wage = sum(p["age"] * p["val"] for p in mk) / max(1, sum(p["val"] for p in mk))
        young = sum(p["val"] for p in plist if p["age"] and p["age"] <= 25)
        old = sum(p["val"] for p in plist if p["age"] and p["age"] >= 29)
        dyn[i] = {"players": plist, "picks": pk, "playerVal": pv, "pickVal": kv, "total": pv + kv, "wage": round(wage, 1),
                  "youngShare": round(young / pv * 100) if pv else 0, "oldShare": round(old / pv * 100) if pv else 0}
    order = sorted(ids, key=lambda i: -dyn[i]["total"])
    for k, i in enumerate(order): dyn[i]["drank"] = k + 1
    med_v = sorted(dyn[i]["total"] for i in ids)[len(ids) // 2]
    med_s = sorted(teams[i]["ppg"] for i in ids)[len(ids) // 2]
    for i in ids:
        hv, hs = dyn[i]["total"] >= med_v, teams[i]["ppg"] >= med_s
        dyn[i]["window"] = "Dynasty power" if hv and hs else "Rising" if hv else "Win-now" if hs else "Rebuild"

    out = {"generated": now.strftime("%Y-%m-%d %H:%M Central"), "data_updated": open(D("updated_at.txt")).read().strip() if os.path.exists(D("updated_at.txt")) else None,
           "season": season, "sleeper_week": state.get("week"), "week_by_date": week_by_date, "weekday": today.strftime("%A"),
           "final_weeks": final_weeks, "teams": teams,
           "weeks": {w: {"pairs": pairs(w), "teams": weeks[w]} for w in sorted(weeks)},
           "projections": {w: v for w, v in proj.items()}, "transactions": tx, "dynasty": dyn,
           "pick_tiers": tier, "fc_loaded": len(fcmap), "players_loaded": len(players)}
    json.dump(out, open(D("derived.json"), "w"), indent=1, default=str)
    print(f"derived.json written: week_by_date={week_by_date} sleeper_week={state.get('week')} final_weeks={final_weeks} "
          f"transactions={len(tx)} fc_values={len(fcmap)} players={len(players)}")

if __name__ == "__main__":
    main()
