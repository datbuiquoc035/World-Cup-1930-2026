# FIFA World Cup 1930–2026 — Dataset, Dashboard & Analysis

An analysis-ready dataset spanning every FIFA World Cup from Uruguay 1930 through the
48-team 2026 edition in the USA, Canada and Mexico, plus a zero-dependency static
dashboard that explores it all in the browser and a Jupyter notebook with charts and an
ML baseline.

> **Note on 2026 data:** the 2026 edition is fully **simulated** — all 104 matches are
> marked `Completed` with scores, penalty shootouts, xG, player of the match and referees.
> The dashboard and notebook treat it as such (see the "Simulated Champion" stat).

## Dataset

### Historical & past tournaments

| File | Contents | Size |
|---|---|---|
| `WC_1930-2014.csv` | Every match result across 20 tournaments (Year, Stage, Stadium, City, teams, goals, half-time scores, attendance, referee, win conditions). Cleaned: no duplicate rows, no blank rows | 836 rows × 20 cols |
| `data_2018/World_cup_2018_matches.csv` | Russia 2018 match stats: shots, possession, fouls, cards, corners, extra time and penalty-shootout scores | 64 rows × 30 cols |
| `data_2018/World_cup_2018_goals.csv` | Every goal of Russia 2018: scorer, minute, penalty / own-goal flags | 169 rows × 9 cols |
| `data_2018/World_cup_2018_country.csv` | Pre-tournament FIFA rank and how far each of the 32 teams went | 32 rows × 11 cols |
| `WC_2022.csv` | Qatar 2022 match-by-match team stats: possession (numeric), attempts, passes, crosses, pressing, cards, fouls, offsides and more | 64 rows × 88 cols |

### 2026 simulation

| File | Contents | Size |
|---|---|---|
| `data_2026/teams.csv` | All 48 teams: group, confederation, pre-tournament FIFA rank, Elo rating, manager | 48 rows × 8 cols |
| `data_2026/venues.csv` | The 16 host venues: city, country, capacity, coordinates, elevation | 16 rows × 8 cols |
| `data_2026/matches.csv` | All 104 simulated matches: scores, penalties, xG, result type, referee, POTM (`kickoff_local_time` is venue-local) | 104 rows × 17 cols |
| `data_2026/tournament_stages.csv` | The 7 stages from Group Stage to Final | 7 rows × 3 cols |
| `data_2026/matches_detailed.csv` | Denormalized mirror of `matches.csv` with team/venue names resolved | 104 rows × 23 cols |
| `data_2026/match_team_stats.csv` | Per-team per-match stats for the simulation | 208 rows × 12 cols |
| `data_2026/match_events.csv` | Goal, card, VAR and shootout events per match | 601 rows × 6 cols |
| `data_2026/match_lineups.csv` | Starting XIs, positions and minutes played | 5408 rows × 7 cols |
| `data_2026/player_stats.csv` | Player tournament totals: goals, assists, cards, saves, ratings | 1248 rows × 21 cols |
| `data_2026/squads_and_players.csv` | Squad details: club, market value, caps, height, age | 1248 rows × 10 cols |
| `data_2026/referees.csv` | Referee countries and average cards per game | 28 rows × 4 cols |
| `data_2026/match_prediction_features.csv` / `_X.csv` / `_targets_y.csv` | Pre-match features and H/D/A targets for modeling | 104 rows each |

## Dashboard website

`docs/index.html` is a self-contained single page plus the generated `docs/data.js`
bundle. No build step, no CDN, no frameworks:

```bash
python3 -m http.server 8000 --directory docs
# then visit http://localhost:8000
```

Sections:

- **Overview** — headline numbers across all eras, tournament growth, goals-per-game,
  top nations and biggest stadiums
- **1930–2014** — every official final (1950 had none; decided by final group round) and a
  searchable match archive with year/stage filters and pagination
- **Russia 2018** — team progression, top scorers (own goals excluded), shootout-aware
  W/D/L table, FIFA rank vs tournament run
- **Qatar 2022** — full team stats table and every match scoreline with possession
- **North America 2026** — group standings computed from results, searchable schedule &
  results with xG and referees, top scorers, referee workload, host cities with capacity

## Regenerating the data bundle

```bash
pip install -r requirements.txt   # pandas is the only hard dependency for build.py
python3 build.py                  # reads the CSVs, validates counts, writes docs/data.js
```

`build.py` asserts data integrity before writing (836 historical matches, 64 in 2018,
64 in 2022, 104 in 2026, 48 teams, 16 venues, unique MatchIDs, non-zero possession).
If validation fails, the bundle is not written.

## Analysis notebook

`analyze.ipynb` covers historical trends, 2018/2022 deep dives, the simulated 2026
tournament (standings, champion's path, xG quality) and a scikit-learn logistic-regression
baseline predicting match outcomes (73% accuracy vs 46% majority-class baseline):

```bash
jupyter nbconvert --to notebook --execute --inplace analyze.ipynb
```

## Notable observations

- The dataset covers 836 completed historical matches (1930–2014); 1950 is the only
  edition without an official final.
- 2026 is the first World Cup with 48 teams (12 groups of 4) and 104 matches; the opener
  was Mexico City on 11 June 2026 and the final at MetLife Stadium on 19 July 2026.
- In the simulation Spain win the final 1–0 against Argentina.
