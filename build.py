"""Build the World Cup data bundle for the dashboard.

Reads the CSV files and generates docs/data.js.
Run from anywhere: paths are resolved relative to this file.
"""

import json
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "docs"


def clean_team(name):
    """Clean team names."""
    if pd.isna(name):
        return None
    s = str(name).strip()
    s = s.replace('rn">', "").replace('"', "")
    s = " ".join(s.split())
    aliases = {"Columbia": "Colombia", "Costarica": "Costa Rica", "Porugal": "Portugal"}
    return aliases.get(s, s)


def i0(v):
    """NaN-safe int."""
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def f1(v):
    """NaN-safe float rounded to 1 decimal."""
    try:
        return round(float(v), 1)
    except (TypeError, ValueError):
        return 0.0


def _s(v):
    s = str(v).strip() if pd.notna(v) else ""
    return s or None


# ---------------------------------------------------------------- historical
print("Loading historical data (1930-2014)...")
hist = pd.read_csv(ROOT / "WC_1930-2014.csv")
hist = hist.dropna(subset=["Year"]).drop_duplicates()
hist["Year"] = hist["Year"].astype(int)
hist["Attendance"] = pd.to_numeric(hist["Attendance"], errors="coerce")
for col in ("Home Team Name", "Away Team Name"):
    hist[col] = hist[col].map(clean_team)
hist["Home Team Goals"] = pd.to_numeric(hist["Home Team Goals"], errors="coerce").fillna(0).astype(int)
hist["Away Team Goals"] = pd.to_numeric(hist["Away Team Goals"], errors="coerce").fillna(0).astype(int)
hist["total_goals"] = hist["Home Team Goals"] + hist["Away Team Goals"]

yearly = []
for year, g in hist.groupby("Year"):
    yearly.append({
        "year": int(year),
        "matches": int(len(g)),
        "goals": int(g["total_goals"].sum()),
        "gpg": round(float(g["total_goals"].mean()), 2),
        "avg_att": int(g["Attendance"].mean(skipna=True)) if g["Attendance"].notna().any() else 0,
        "att_missing": int(g["Attendance"].isna().sum()),
    })

goals_by_team = defaultdict(int)
for _, r in hist.iterrows():
    goals_by_team[r["Home Team Name"]] += r["Home Team Goals"]
    goals_by_team[r["Away Team Name"]] += r["Away Team Goals"]
top_nations = [
    {"team": k, "goals": v}
    for k, v in sorted(goals_by_team.items(), key=lambda x: -x[1])[:15]
]

stadiums = hist.groupby("Stadium").agg(
    avg_att=("Attendance", "mean"),
    matches=("MatchID", "count"),
).query("matches >= 5").sort_values("avg_att", ascending=False)
top_stadiums = [
    {"stadium": idx, "avg_att": int(r.avg_att), "matches": int(r.matches)}
    for idx, r in stadiums.head(10).iterrows()
]

finals = hist[hist["Stage"] == "Final"].copy().sort_values("Year")


def champion_of(row):
    """Pick whichever finalist is named in 'Win conditions'; fall back to score."""
    wc = _s(row["Win conditions"]) or ""
    home, away = row["Home Team Name"], row["Away Team Name"]
    if wc:
        home_in = home and home in wc
        away_in = away and away in wc
        if home_in and not away_in:
            return home
        if away_in and not home_in:
            return away
    if row["Home Team Goals"] > row["Away Team Goals"]:
        return home
    if row["Away Team Goals"] > row["Home Team Goals"]:
        return away
    return None


finals_list = [
    {
        "year": int(r.Year),
        "home": r["Home Team Name"],
        "home_goals": int(r["Home Team Goals"]),
        "away_goals": int(r["Away Team Goals"]),
        "away": r["Away Team Name"],
        "att": int(r["Attendance"]) if pd.notna(r["Attendance"]) else None,
        "champion": champion_of(r),
        "win_conditions": _s(r.get("Win conditions")),
    }
    for _, r in finals.iterrows()
]

matches_hist = []
for _, r in hist.iterrows():
    matches_hist.append({
        "year": int(r.Year),
        "stage": r["Stage"],
        "home": r["Home Team Name"],
        "hg": int(r["Home Team Goals"]),
        "ag": int(r["Away Team Goals"]),
        "away": r["Away Team Name"],
        "att": int(r["Attendance"]) if pd.notna(r["Attendance"]) else None,
        "city": _s(r["City"]),
        "stadium": _s(r["Stadium"]),
        "datetime": _s(r["Datetime"]),
        "ht_h": i0(r["Half-time Home Goals"]) if pd.notna(r.get("Half-time Home Goals")) else None,
        "ht_a": i0(r["Half-time Away Goals"]) if pd.notna(r.get("Half-time Away Goals")) else None,
        "referee": _s(r.get("Referee")),
        "assist1": _s(r.get("Assistant 1")),
        "assist2": _s(r.get("Assistant 2")),
        "hi": _s(r.get("Home Team Initials")),
        "ai": _s(r.get("Away Team Initials")),
        "matchid": int(r["MatchID"]) if pd.notna(r["MatchID"]) else None,
        "win_conditions": _s(r.get("Win conditions")),
    })

print(f"  Historical: {len(matches_hist)} matches, {len(yearly)} tournaments")

# ---------------------------------------------------------------- 2018
print("Loading 2018 data...")
m18 = pd.read_csv(ROOT / "World_cup_2018_matches.csv")
g18 = pd.read_csv(ROOT / "World_cup_2018_goals.csv")
c18 = pd.read_csv(ROOT / "World_cup_2018_country.csv")

matches_2018 = []
for _, r in m18.iterrows():
    hg, ag = i0(r["Home_goals"]), i0(r["Away_goals"])
    pen = _s(r.get("Penalties")) == "Y"
    hpk, apk = i0(r.get("Home_PK_made")), i0(r.get("Away_PK_made"))
    # regulation/extra-time result; shootout winner recorded separately
    if pen:
        outcome = "H" if hpk > apk else "A" if apk > hpk else None
    elif hg != ag:
        outcome = "H" if hg > ag else "A"
    else:
        outcome = None
    matches_2018.append({
        "date": _s(r["Date"]),
        "stage": _s(r["Stage"]),
        "home": clean_team(r["Home"]),
        "away": clean_team(r["Away"]),
        "home_goals": hg, "away_goals": ag,
        "home_shots": i0(r["Home_shots"]), "away_shots": i0(r["Away_shots"]),
        "home_shots_on_target": i0(r["Home_shots_on_target"]), "away_shots_on_target": i0(r["Away_shots_on_target"]),
        "home_possession": i0(r["Home_possession"]), "away_possession": i0(r["Away_possession"]),
        "home_fouls": i0(r["Home_fouls"]), "away_fouls": i0(r["Away_fouls"]),
        "home_yellow": i0(r["Home_yellow"]), "away_yellow": i0(r["Away_yellow"]),
        "home_red": i0(r["Home_red"]), "away_red": i0(r["Away_red"]),
        "home_corners": i0(r["Home_corners"]), "away_corners": i0(r["Away_corners"]),
        "penalty_shootout": pen,
        "outcome": outcome,
        "total_goals": hg + ag,
    })

goals_2018 = []
for _, r in g18.iterrows():
    goals_2018.append({
        "date": _s(r["Date"]),
        "stage": _s(r["Stage"]),
        "home": clean_team(r["Home"]),
        "away": clean_team(r["Away"]),
        "team_scored": _s(r["Team_scored"]),
        "player_scored": _s(r["Player_scored"]),
        "time": _s(r["Time"]),
        "own_goal": _s(r.get("Own_goal")) == "Y",
        "penalty": _s(r.get("Penalty")) == "Y",
    })

countries_2018 = []
for _, r in c18.iterrows():
    countries_2018.append({
        "country": _s(r["Country"]),
        "world_ranking": i0(r["World_ranking"]) or None,
        "tournament_ranking": i0(r["Tournament_ranking"]) or None,
        "group": _s(r["Group"]),
        "group_score": i0(r["Group_score"]),
        "group_ranking": i0(r["Group_ranking"]) or None,
        "last16": _s(r["Last16"]) == "Y",
        "qfinals": _s(r["QFinals"]) == "Y",
        "sfinals": _s(r["SFinals"]) == "Y",
        "finals": _s(r["Finals"]) == "Y",
        "winner": _s(r["Winner"]) == "Y",
    })

team_perf_2018 = {}
for m in matches_2018:
    for team, is_home in [(m["home"], True), (m["away"], False)]:
        if team not in team_perf_2018:
            team_perf_2018[team] = {"matches": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "poss": []}
        st = team_perf_2018[team]
        st["matches"] += 1
        gf = m["home_goals"] if is_home else m["away_goals"]
        ga = m["away_goals"] if is_home else m["home_goals"]
        st["gf"] += gf
        st["ga"] += ga
        st["poss"].append(m["home_possession"] if is_home else m["away_possession"])
        won = m["outcome"] == ("H" if is_home else "A")
        lost = m["outcome"] == ("A" if is_home else "H")
        if won:
            st["w"] += 1
        elif lost:
            st["l"] += 1
        else:
            st["d"] += 1

teams_2018 = sorted(
    (
        {
            "team": team,
            "matches": s["matches"], "w": s["w"], "d": s["d"], "l": s["l"],
            "gf": s["gf"], "ga": s["ga"], "gd": s["gf"] - s["ga"],
            "avg_possession": round(sum(s["poss"]) / len(s["poss"]), 1) if s["poss"] else 0,
        }
        for team, s in team_perf_2018.items()
    ),
    key=lambda x: -(x["w"] * 3 + x["d"]),
)

print(f"  2018: {len(matches_2018)} matches, {len(goals_2018)} goals, {len(countries_2018)} teams")

# ---------------------------------------------------------------- 2022
print("Loading 2022 data...")
d22 = pd.read_csv(ROOT / "WC_2022.csv")


def strip_pct(df):
    """Defensively strip '%' from any object column so numeric coercion works."""
    for c in df.columns:
        if df[c].dtype == object:
            as_str = df[c].astype(str)
            if as_str.str.contains("%").any():
                df[c] = pd.to_numeric(as_str.str.replace("%", "", regex=False), errors="coerce")
    return df


d22 = strip_pct(d22)
numeric_cols = [c for c in d22.columns if c not in ("team1", "team2", "date", "hour", "category", "team", "Group")]
for c in numeric_cols:
    d22[c] = pd.to_numeric(d22[c], errors="coerce")
d22["team1"] = d22["team1"].map(clean_team)
d22["team2"] = d22["team2"].map(clean_team)


def t22(name):
    return str(name).title().replace("Ir Iran", "IR Iran").replace("Usa", "USA")


matches_2022 = []
for _, r in d22.iterrows():
    matches_2022.append({
        "t1": t22(r["team1"]), "t2": t22(r["team2"]),
        "g1": i0(r["number of goals team1"]), "g2": i0(r["number of goals team2"]),
        "pos1": i0(r["possession team1"]), "pos2": i0(r["possession team2"]),
        "att1": i0(r["total attempts team1"]), "att2": i0(r["total attempts team2"]),
        "ont1": i0(r["on target attempts team1"]), "ont2": i0(r["on target attempts team2"]),
        "pass1": i0(r["passes completed team1"]), "pass2": i0(r["passes completed team2"]),
        "cat": _s(r["category"]),
        "date": _s(r.get("date")), "hour": _s(r.get("hour")),
        "off1": i0(r["offsides team1"]), "off2": i0(r["offsides team2"]),
        "def1": i0(r["conceded team1"]), "def2": i0(r["conceded team2"]),
        "inb1": i0(r["attempts inside the penalty area team1"]),
        "inb2": i0(r["attempts inside the penalty area  team2"]),
        "outb1": i0(r["attempts outside the penalty area  team1"]),
        "outb2": i0(r["attempts outside the penalty area  team2"]),
        "pass_t1": i0(r["passes team1"]), "pass_t2": i0(r["passes team2"]),
        "cross1": i0(r["crosses team1"]), "cross2": i0(r["crosses team2"]),
        "crossc1": i0(r["crosses completed team1"]), "crossc2": i0(r["crosses completed team2"]),
        "corners1": i0(r["corners team1"]), "corners2": i0(r["corners team2"]),
        "fk1": i0(r["free kicks team1"]), "fk2": i0(r["free kicks team2"]),
        "yc1": i0(r["yellow cards team1"]), "yc2": i0(r["yellow cards team2"]),
        "rc1": i0(r["red cards team1"]), "rc2": i0(r["red cards team2"]),
        "fouls1": i0(r["fouls against team1"]), "fouls2": i0(r["fouls against team2"]),
        "og1": i0(r["own goals team1"]), "og2": i0(r["own goals team2"]),
        "pen1": i0(r["penalties scored team1"]), "pen2": i0(r["penalties scored team2"]),
        "gp1": i0(r["goal preventions team1"]), "gp2": i0(r["goal preventions team2"]),
        "fto1": i0(r["forced turnovers team1"]), "fto2": i0(r["forced turnovers team2"]),
        "dp1": i0(r["defensive pressures applied team1"]), "dp2": i0(r["defensive pressures applied team2"]),
    })

team_rows = []
for team in sorted(set(d22["team1"].unique()) | set(d22["team2"].unique())):
    as1 = d22[d22["team1"] == team]
    as2 = d22[d22["team2"] == team]
    gf = int(as1["number of goals team1"].sum()) + int(as2["number of goals team2"].sum())
    ga = int(as1["number of goals team2"].sum()) + int(as2["number of goals team1"].sum())
    wins = int(((as1["number of goals team1"] > as1["number of goals team2"]).sum()
                + (as2["number of goals team2"] > as2["number of goals team1"]).sum()))
    draws = int(((as1["number of goals team1"] == as1["number of goals team2"]).sum()
                 + (as2["number of goals team2"] == as2["number of goals team1"]).sum()))
    losses = int(len(as1) + len(as2) - wins - draws)
    n = len(as1) + len(as2)
    pos_sum = as1["possession team1"].sum() + as2["possession team2"].sum()
    team_rows.append({
        "team": t22(team),
        "p": n, "w": wins, "d": draws, "l": losses,
        "gf": gf, "ga": ga,
        "pos": round(float(pos_sum) / max(n, 1), 1),
        "att": int(as1["total attempts team1"].sum() + as2["total attempts team2"].sum()),
        "ont": int(as1["on target attempts team1"].sum() + as2["on target attempts team2"].sum()),
        "passc": int(as1["passes completed team1"].sum() + as2["passes completed team2"].sum()),
        "fouls": int(as1["fouls against team1"].sum() + as2["fouls against team2"].sum()),
        "yellow": int(as1["yellow cards team1"].sum() + as2["yellow cards team2"].sum()),
    })
team_rows.sort(key=lambda t: (-t["w"] * 3 - t["d"], -(t["gf"] - t["ga"])))

print(f"  2022: {len(matches_2022)} matches, {len(team_rows)} teams")

# ---------------------------------------------------------------- 2026
print("Loading 2026 data...")
teams26 = pd.read_csv(ROOT / "teams.csv")
cities26 = pd.read_csv(ROOT / "venues.csv")
stages26 = pd.read_csv(ROOT / "tournament_stages.csv")
matches26 = pd.read_csv(ROOT / "matches.csv")
players26 = pd.read_csv(ROOT / "player_stats.csv")
referees26 = pd.read_csv(ROOT / "referees.csv")

team_map = {int(r.team_id): {"name": r.team_name, "code": r.fifa_code} for _, r in teams26.iterrows()}
city_map = {
    int(r.venue_id): {"city": r.city, "country": r.country, "venue": r.stadium_name, "capacity": int(r.capacity)}
    for _, r in cities26.iterrows()
}
stage_map = {int(r.stage_id): {"name": r.stage_name, "knockout": bool(r.is_knockout)} for _, r in stages26.iterrows()}
ref_map = {int(r.referee_id): {"name": r.name, "country": r.country} for _, r in referees26.iterrows()}
player_name_map = {int(r.player_id): r.player_name for _, r in players26.iterrows()}

schedule_2026 = []
for _, r in matches26.iterrows():
    home = team_map.get(int(r["home_team_id"])) if pd.notna(r["home_team_id"]) else None
    away = team_map.get(int(r["away_team_id"])) if pd.notna(r["away_team_id"]) else None
    city = city_map.get(int(r["venue_id"]), {})
    ref = ref_map.get(int(r["referee_id"])) if pd.notna(r["referee_id"]) else None
    potm = player_name_map.get(int(r["player_of_the_match_id"])) if pd.notna(r["player_of_the_match_id"]) else None
    stage_id = int(r["stage_id"])
    hs, as_ = r["home_score"], r["away_score"]
    schedule_2026.append({
        "num": int(r["match_id"]),
        "stage_id": stage_id,
        "stage": stage_map[stage_id]["name"],
        "knockout": stage_map[stage_id]["knockout"],
        "label": f"{home['name'] if home else 'TBD'} vs {away['name'] if away else 'TBD'}",
        "home": home["name"] if home else None,
        "home_code": home["code"] if home else None,
        "away": away["name"] if away else None,
        "away_code": away["code"] if away else None,
        "hg": int(hs) if pd.notna(hs) else None,
        "ag": int(as_) if pd.notna(as_) else None,
        "hpk": int(r["home_penalty_score"]) if pd.notna(r["home_penalty_score"]) else None,
        "apk": int(r["away_penalty_score"]) if pd.notna(r["away_penalty_score"]) else None,
        "hxg": f1(r["home_xg"]) if pd.notna(r["home_xg"]) else None,
        "axg": f1(r["away_xg"]) if pd.notna(r["away_xg"]) else None,
        "status": _s(r["status"]),
        "result_type": _s(r["result_type"]),
        "city": city.get("city"),
        "country": city.get("country"),
        "venue": city.get("venue"),
        "date": _s(r["date"]),
        "kickoff_local": _s(r["kickoff_local_time"]),
        "referee": ref["name"] if ref else None,
        "potm": potm,
    })

groups_2026 = []
for letter, grp in teams26.groupby("group_letter"):
    teams_in_group = [{"name": r.team_name, "code": r.fifa_code} for _, r in grp.iterrows()]
    codes = {t["code"]: t["name"] for t in teams_in_group}
    table = {code: {"team": name, "code": code, "p": 0, "w": 0, "d": 0, "l": 0,
                    "gf": 0, "ga": 0, "gd": 0, "pts": 0} for code, name in codes.items()}
    for m in schedule_2026:
        if m["stage_id"] != 1 or m["hg"] is None or m["home_code"] not in table or m["away_code"] not in table:
            continue
        h, a = table[m["home_code"]], table[m["away_code"]]
        h["p"] += 1; a["p"] += 1
        h["gf"] += m["hg"]; h["ga"] += m["ag"]
        a["gf"] += m["ag"]; a["ga"] += m["hg"]
        if m["hg"] > m["ag"]:
            h["w"] += 1; a["l"] += 1; h["pts"] += 3
        elif m["hg"] < m["ag"]:
            a["w"] += 1; h["l"] += 1; a["pts"] += 3
        else:
            h["d"] += 1; a["d"] += 1; h["pts"] += 1; a["pts"] += 1
    standings = []
    for row in table.values():
        row["gd"] = row["gf"] - row["ga"]
        standings.append(row)
    standings.sort(key=lambda x: (-x["pts"], -x["gd"], -x["gf"]))
    groups_2026.append({"letter": letter, "teams": teams_in_group, "standings": standings})
groups_2026.sort(key=lambda g: g["letter"])

stages_summary = [
    {"name": r.stage_name, "order": int(r.stage_id),
     "matches": int((matches26["stage_id"] == r.stage_id).sum())}
    for _, r in stages26.iterrows()
]

cities_2026 = [
    {"city": r.city, "country": r.country, "venue": r.stadium_name,
     "capacity": int(r.capacity),
     "matches": int((matches26["venue_id"] == r.venue_id).sum())}
    for _, r in cities26.iterrows()
]

scorers = players26.nlargest(10, "goals").merge(
    teams26[["team_id", "team_name", "fifa_code"]], on="team_id", how="left")
top_scorers_2026 = [
    {"player": r.player_name, "team": r.team_name, "code": r.fifa_code,
     "goals": int(r.goals), "assists": int(r.assists)}
    for _, r in scorers.iterrows()
]

ref_matches = matches26["referee_id"].value_counts()
referees_2026 = sorted(
    (
        {"name": r.name, "country": r.country,
         "matches": int(ref_matches.get(r.referee_id, 0)),
         "cards_per_game": f1(r.avg_cards_per_game)}
        for _, r in referees26.iterrows()
    ),
    key=lambda x: -x["matches"],
)[:10]

print(f"  2026: {len(schedule_2026)} matches, {len(teams26)} teams, {len(cities26)} venues")

# ---------------------------------------------------------------- champions
# 2018: the countries table carries an explicit winner flag.
champion_2018 = next((c["country"] for c in countries_2018 if c["winner"]), None)

# 2022: decide from the Final scoreline. The CSV has no shootout score and
# that final ended 3-3, so fall back to the recorded result (4-2 on pens).
CHAMPION_TIEBREAK = {"2022": "Argentina"}
final22 = d22[d22["category"] == "Final"]
if len(final22):
    r = final22.iloc[0]
    g1, g2 = i0(r["number of goals team1"]), i0(r["number of goals team2"])
    if g1 != g2:
        champion_2022 = t22(r["team1"] if g1 > g2 else r["team2"])
    else:
        champion_2022 = CHAMPION_TIEBREAK.get("2022")
else:
    champion_2022 = None

# 2026: winner of the simulated Final (penalty score decides if level).
final26 = next((m for m in schedule_2026 if m["stage"] == "Final"), None)
champion_2026 = None
if final26 and final26["hg"] is not None:
    if final26["hpk"] is not None and final26["hpk"] != final26["apk"]:
        champion_2026 = final26["home"] if final26["hpk"] > final26["apk"] else final26["away"]
    elif final26["hg"] != final26["ag"]:
        champion_2026 = final26["home"] if final26["hg"] > final26["ag"] else final26["away"]

champions = {
    "2018": champion_2018,
    "2022": champion_2022,
    "2026": champion_2026,
}
print(f"  Champions: 2018 {champion_2018} | 2022 {champion_2022} | 2026 {champion_2026}")

# ---------------------------------------------------------------- overview
goals_2018_total = sum(m["total_goals"] for m in matches_2018)
goals_2022_total = sum(m["g1"] + m["g2"] for m in matches_2022)
goals_2026_total = sum(m["hg"] + m["ag"] for m in schedule_2026 if m["hg"] is not None)

overview = {
    "tournaments": len(yearly),
    "matches_hist": len(matches_hist),
    "goals_hist": sum(y["goals"] for y in yearly),
    "avg_gpg_hist": round(sum(y["gpg"] for y in yearly) / len(yearly), 2),
    "total_attendance_hist": int(hist["Attendance"].sum(skipna=True)),
    "matches_2018": len(matches_2018),
    "matches_2022": int(len(d22)),
    "teams_2026": int(len(teams26)),
    "venues_2026": int(len(cities26)),
    "matches_2026": int(len(matches26)),
    "matches_all": len(matches_hist) + len(matches_2018) + int(len(d22)) + int(len(matches26)),
    "goals_all": sum(y["goals"] for y in yearly) + goals_2018_total + goals_2022_total + goals_2026_total,
}

data = {
    "overview": overview,
    "champions": champions,
    "yearly": yearly,
    "top_nations": top_nations,
    "top_stadiums": top_stadiums,
    "finals": finals_list,
    "matches_hist": matches_hist,
    "matches_2018": matches_2018,
    "goals_2018": goals_2018,
    "countries_2018": countries_2018,
    "teams_2018": teams_2018,
    "matches_2022": matches_2022,
    "teams_2022": team_rows,
    "groups_2026": groups_2026,
    "schedule_2026": schedule_2026,
    "stages_2026": stages_summary,
    "cities_2026": cities_2026,
    "top_scorers_2026": top_scorers_2026,
    "referees_2026": referees_2026,
}


# ---------------------------------------------------------------- validation
def validate(data):
    o = data["overview"]
    assert o["matches_hist"] == 836, f"expected 836 historical matches, got {o['matches_hist']}"
    # 1950 had no official final (decided by a final group round) -> 19 finals
    assert len(data["finals"]) == 19, f"expected 19 finals, got {len(data['finals'])}"
    assert len({f["year"] for f in data["finals"]}) == 19, "duplicate final years"
    assert len({m["matchid"] for m in data["matches_hist"]}) == 836, "duplicate MatchIDs"
    assert o["matches_2018"] == 64, f"expected 64 matches in 2018, got {o['matches_2018']}"
    assert o["matches_2022"] == 64, f"expected 64 matches in 2022, got {o['matches_2022']}"
    assert all(m["pos1"] > 0 and m["pos2"] > 0 for m in data["matches_2022"]), "2022 possession has zeros"
    assert all(t["pos"] > 0 for t in data["teams_2022"]), "2022 team possession has zeros"
    assert o["matches_2026"] == 104, f"expected 104 matches in 2026, got {o['matches_2026']}"
    assert o["teams_2026"] == 48, f"expected 48 teams in 2026, got {o['teams_2026']}"
    assert o["venues_2026"] == 16, f"expected 16 venues in 2026, got {o['venues_2026']}"
    assert all(data["champions"].values()), f"missing champion(s): {data['champions']}"
    group_games = sum(t["p"] for g in data["groups_2026"] for t in g["standings"]) // 2
    assert group_games == 72, f"expected 72 group games in 2026, got {group_games}"
    assert len(data["schedule_2026"][0]) > 0 and all(m["venue"] for m in data["schedule_2026"]), "missing venue"
    print("Validation passed.")


validate(data)

# ---------------------------------------------------------------- write bundle
SITE.mkdir(exist_ok=True)
payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
with open(SITE / "data.js", "w") as f:
    f.write("// Auto-generated by build.py - do not edit\n")
    f.write("window.WC_DATA=" + payload + ";")

print(f"\nGenerated docs/data.js ({len(payload):,} bytes)")

# ---------------------------------------------------------------- cache busting
# GitHub Pages caches assets for up to 10 minutes; pin the script tag to the
# exact bundle content so browsers always fetch fresh data after a deploy.
import hashlib
import re

html_path = SITE / "index.html"
html = html_path.read_text(encoding="utf-8")
version = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:10]
updated, n = re.subn(r'(src=")data\.js(\?v=[0-9a-f]+)?(")', rf"\g<1>data.js?v={version}\g<3>", html)
if n != 1:
    raise SystemExit(f'ERROR: expected exactly one data.js script tag in docs/index.html, found {n}')
if updated != html:
    html_path.write_text(updated, encoding="utf-8")
print(f"Cache buster: data.js?v={version}")
