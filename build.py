"""Compile the World Cup CSV dataset into a single JSON bundle for the demo site.

Reads:
  - WC_1930-2014.csv   (852 matches, 1930-2014)
  - WC_2018.csv        (32-team pre-tournament preview)
  - WC_2022.csv        (64 matches with detailed stats)
  - WC_2026/*.csv      (48 teams, 16 host cities, 104-match schedule)

Writes:
  - site/data.js       (window.WC_DATA = {...})
"""

import json
import pandas as pd
from collections import defaultdict

ROOT = "."
SITE = "docs"

# ---------------------------------------------------------------------------
# Team name hygiene
# ---------------------------------------------------------------------------
import re as _re

def clean_team(name):
    """Strip scraping artifacts and normalize known misspellings."""
    if pd.isna(name):
        return None
    s = str(name).strip()
    s = _re.sub(r'^rn"?>', "", s)          # 'rn">Bosnia...' artifact
    s = _re.sub(r'\s+', " ", s).strip()
    ALIASES = {
        "Columbia": "Colombia",
        "Costarica": "Costa Rica",
        "Porugal": "Portugal",
        "IRAN": "Iran",
    }
    return ALIASES.get(s, s)

def i0(v):
    return int(v) if pd.notna(v) else 0

def _s(v):
    s = str(v).strip() if pd.notna(v) else ""
    return s or None

# ---------------------------------------------------------------------------
# 1. Historical matches 1930-2014
# ---------------------------------------------------------------------------
hist = pd.read_csv(f"{ROOT}/WC_1930-2014.csv")
hist = hist.dropna(subset=["Year"])
hist["Year"] = hist["Year"].astype(int)
hist["Attendance"] = pd.to_numeric(hist["Attendance"], errors="coerce")
for col in ("Home Team Name", "Away Team Name"):
    hist[col] = hist[col].map(clean_team)

hist["Home Team Goals"] = pd.to_numeric(hist["Home Team Goals"], errors="coerce").fillna(0).astype(int)
hist["Away Team Goals"] = pd.to_numeric(hist["Away Team Goals"], errors="coerce").fillna(0).astype(int)
hist["total_goals"] = hist["Home Team Goals"] + hist["Away Team Goals"]

# Per-tournament summary
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

# All-time top nations by goals (home + away)
goals_by_team = defaultdict(int)
for _, r in hist.iterrows():
    goals_by_team[r["Home Team Name"]] += r["Home Team Goals"]
    goals_by_team[r["Away Team Name"]] += r["Away Team Goals"]
top_nations = [
    {"team": k, "goals": v}
    for k, v in sorted(goals_by_team.items(), key=lambda x: -x[1])[:15]
]

# Stadiums with the best average attendance (min 5 matches)
stadiums = hist.groupby("Stadium").agg(
    avg_att=("Attendance", "mean"),
    matches=("MatchID", "count"),
).query("matches >= 5").sort_values("avg_att", ascending=False)
top_stadiums = [
    {"stadium": idx, "avg_att": int(r.avg_att), "matches": int(r.matches)}
    for idx, r in stadiums.head(10).iterrows()
]

# Finals list
finals = hist[hist["Stage"] == "Final"].copy().sort_values("Year")
def champion_of(r):
    wc = r["Win conditions"] if pd.notna(r["Win conditions"]) and str(r["Win conditions"]).strip() else None
    if wc and str(wc).strip():
        return str(wc).strip().split()[0]
    if r["Home Team Goals"] > r["Away Team Goals"]:
        return r["Home Team Name"]
    if r["Away Team Goals"] > r["Home Team Goals"]:
        return r["Away Team Name"]
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
        "win_conditions": r["Win conditions"] if pd.notna(r["Win conditions"]) and str(r["Win conditions"]).strip() else None,
    }
    for _, r in finals.iterrows()
]

# Full match list (compact) for the searchable table
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
        "city": r["City"] if pd.notna(r["City"]) else None,
        "stadium": r["Stadium"] if pd.notna(r["Stadium"]) else None,
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

# ---------------------------------------------------------------------------
# 2. 2018 team preview
# ---------------------------------------------------------------------------
pre18 = pd.read_csv(f"{ROOT}/WC_2018.csv")
pre18.columns = [c.replace("\n", " ").strip() for c in pre18.columns]
pre18 = pre18.dropna(subset=["Team"])
preview_2018 = []
for _, r in pre18.iterrows():
    def num(v):
        try:
            f = float(str(v).replace("%", "").strip())
            return f
        except (ValueError, TypeError):
            return None
    preview_2018.append({
        "team": clean_team(r["Team"]),
        "group": r["Group"],
        "appearances": num(r.get("Previous  appearances")),
        "titles": num(r.get("Previous  titles")),
        "finals": num(r.get("Previous  finals")),
        "semis": num(r.get("Previous  semifinals")),
        "fifa_rank": num(r.get("Current  FIFA rank")),
        "first_match": r.get("First match  against") if pd.notna(r.get("First match  against")) else None,
    })

# ---------------------------------------------------------------------------
# 3. 2022 detailed stats
# ---------------------------------------------------------------------------
d22 = pd.read_csv(f"{ROOT}/WC_2022.csv")
numeric_cols = [c for c in d22.columns if c not in ("team1", "team2", "date", "hour", "category", "team", "Group")]
for c in numeric_cols:
    d22[c] = pd.to_numeric(d22[c], errors="coerce")

d22["team1"] = d22["team1"].map(clean_team)
d22["team2"] = d22["team2"].map(clean_team)

matches_2022 = []
for _, r in d22.iterrows():
    matches_2022.append({
        "t1": r["team1"].title(), "t2": r["team2"].title(),
        "g1": i0(r["number of goals team1"]), "g2": i0(r["number of goals team2"]),
        "pos1": i0(r["possession team1"]), "pos2": i0(r["possession team2"]),
        "att1": i0(r["total attempts team1"]), "att2": i0(r["total attempts team2"]),
        "ont1": i0(r["on target attempts team1"]), "ont2": i0(r["on target attempts team2"]),
        "pass1": i0(r["passes completed team1"]), "pass2": i0(r["passes completed team2"]),
        "cat": r["category"],
        # extended detail for the match modal
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

# Per-team aggregates
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
    def mean_safe(df, col):
        v = df[col].mean(skipna=True)
        return round(float(v), 1) if pd.notna(v) else 0
    team_rows.append({
        "team": team.title(),
        "p": int(len(as1) + len(as2)),
        "w": wins, "d": draws, "l": losses,
        "gf": gf, "ga": ga,
        "pos": round((as1["possession team1"].sum() + as2["possession team2"].sum()) / max(len(as1) + len(as2), 1), 1),
        "att": int(as1["total attempts team1"].sum() + as2["total attempts team2"].sum()),
        "ont": int(as1["on target attempts team1"].sum() + as2["on target attempts team2"].sum()),
        "passc": int(as1["passes completed team1"].sum() + as2["passes completed team2"].sum()),
        "fouls": int(as1["fouls against team1"].sum() + as2["fouls against team2"].sum()),
        "yellow": int(as1["yellow cards team1"].sum() + as2["yellow cards team2"].sum()),
    })
team_rows.sort(key=lambda t: (-t["w"] * 3 - t["d"], -(t["gf"] - t["ga"])))

# ---------------------------------------------------------------------------
# 4. 2026 edition
# ---------------------------------------------------------------------------
teams26 = pd.read_csv(f"{ROOT}/WC_2026/teams.csv")
cities26 = pd.read_csv(f"{ROOT}/WC_2026/host_cities.csv")
stages26 = pd.read_csv(f"{ROOT}/WC_2026/tournament_stages.csv")
matches26 = pd.read_csv(f"{ROOT}/WC_2026/matches.csv")

teams_by_group = defaultdict(list)
for _, r in teams26.iterrows():
    teams_by_group[r["group_letter"]].append({
        "name": r["team_name"],
        "code": r["fifa_code"],
        "placeholder": bool(r["is_placeholder"]),
    })
groups_2026 = [{"letter": k, "teams": v} for k, v in sorted(teams_by_group.items())]

city_map = {int(r.id): {"city": r.city_name, "country": r.country, "venue": r.venue_name,
                        "region": r.region_cluster} for _, r in cities26.iterrows()}
stage_map = {int(r.id): {"name": r.stage_name, "order": int(r.stage_order)} for _, r in stages26.iterrows()}
team_map = {int(r.id): {"name": r.team_name, "code": r.fifa_code, "placeholder": bool(r.is_placeholder)}
            for _, r in teams26.iterrows()}

# Note: 2026 uses Eastern Daylight Time (UTC-4) for US East cities in June/July,
# but the data already carries explicit UTC offsets, so we show venue-local time.
tz_label = {-4: "ET", -5: "CT", -6: "MT", -7: "PT"}

import re

def parse_kickoff(s):
    """2026-06-11 15:00:00-06 -> {iso, tz}"""
    m = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}):\d{2}([+-]\d{2})", s)
    off = int(m.group(2))
    return {"iso": m.group(1), "tz": tz_label.get(off, f"UTC{off:+d}")}

schedule_2026 = []
for _, r in matches26.iterrows():
    k = parse_kickoff(r["kickoff_at"])
    home = team_map.get(int(r["home_team_id"])) if pd.notna(r["home_team_id"]) else None
    away = team_map.get(int(r["away_team_id"])) if pd.notna(r["away_team_id"]) else None
    city = city_map.get(int(r["city_id"]), {})
    schedule_2026.append({
        "num": int(r["match_number"]),
        "stage_id": int(r["stage_id"]),
        "stage": stage_map[int(r["stage_id"])]["name"],
        "label": r["match_label"],
        "home": home["name"] if home else None,
        "home_code": home["code"] if home else None,
        "home_ph": home["placeholder"] if home else False,
        "away": away["name"] if away else None,
        "away_code": away["code"] if away else None,
        "away_ph": away["placeholder"] if away else False,
        "city": city.get("city"),
        "country": city.get("country"),
        "venue": city.get("venue"),
        "iso": k["iso"], "tz": k["tz"],
    })

stages_summary = [
    {"name": r.stage_name, "order": int(r.stage_order),
     "matches": int((matches26["stage_id"] == r.id).sum())}
    for _, r in stages26.iterrows()
]

cities_2026 = [
    {"city": r.city_name, "country": r.country, "venue": r.venue_name,
     "region": r.region_cluster, "code": r.airport_code,
     "matches": int((matches26["city_id"] == r.id).sum())}
    for _, r in cities26.iterrows()
]

# ---------------------------------------------------------------------------
# Bundle
# ---------------------------------------------------------------------------
overview = {
    "tournaments_1930_2014": len(yearly),
    "matches_1930_2014": len(matches_hist),
    "goals_1930_2014": sum(y["goals"] for y in yearly),
    "avg_gpg_1930_2014": round(sum(y["gpg"] for y in yearly) / len(yearly), 2),
    "matches_2022": int(len(d22)),
    "teams_2026": int(len(teams26)),
    "cities_2026": int(len(cities26)),
    "matches_2026": int(len(matches26)),
    "total_attendance_1930_2014": int(hist["Attendance"].sum(skipna=True)),
}

data = {
    "overview": overview,
    "yearly": yearly,
    "top_nations": top_nations,
    "top_stadiums": top_stadiums,
    "finals": finals_list,
    "matches_hist": matches_hist,
    "preview_2018": preview_2018,
    "matches_2022": matches_2022,
    "teams_2022": team_rows,
    "groups_2026": groups_2026,
    "schedule_2026": schedule_2026,
    "stages_2026": stages_summary,
    "cities_2026": cities_2026,
}

with open(f"{SITE}/data.js", "w") as f:
    f.write("// Auto-generated by build.py - do not edit\n")
    f.write("window.WC_DATA = " + json.dumps(data, ensure_ascii=False))

print("Wrote site/data.js", len(json.dumps(data)), "bytes")
print(f"  yearly: {len(yearly)} | matches_hist: {len(matches_hist)} | finals: {len(finals_list)}")
print(f"  teams_2022: {len(team_rows)} | groups: {len(groups_2026)} | schedule: {len(schedule_2026)}")
