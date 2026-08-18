# FIFA World Cup 1930–2026 — Dataset & Demo Site

An analysis-ready dataset of every FIFA World Cup from Uruguay 1930 through the upcoming
48-team edition in the USA, Canada and Mexico (2026), plus a zero-dependency static demo
website that explores it all in the browser.

## Dataset

| File | Contents | Size |
|---|---|---|
| `WC_1930-2014.csv` | 852 match results across 20 tournaments (Year, Stage, Stadium, City, teams, goals, attendance, half-time scores, referee, win conditions) | 852 rows × 20 cols |
| `WC_2018.csv` | Pre-tournament preview for all 32 Russia 2018 teams (FIFA rank, previous appearances/titles/finals/semifinals, first-match opponent) | 32 rows |
| `WC_2022.csv` | Full match-by-match stats for all 64 Qatar 2022 matches: possession, attempts, on/off target, passes, crosses, channels, line breaks, pressing, cards, fouls, offsides and more | 64 rows × 88 cols |
| `WC_2026/` | Complete 2026 edition: `teams.csv` (48 teams, 12 groups, placeholder flags), `host_cities.csv` (16 venues), `tournament_stages.csv` (7 stages), `matches.csv` (all 104 fixtures with venue-local kickoff times), plus an identical `worldcup2026.db` SQLite mirror | 104 matches |

## Demo website

`docs/index.html` is a self-contained single page (plus the generated `docs/data.js` data bundle).
No build step, no CDN, no frameworks — open it in any modern browser:

```bash
python3 -m http.server 8000 --directory docs
# then visit http://localhost:8000
```

Sections:

- **Overview** — headline numbers from all four datasets
- **Goals & attendance (1930–2014)** — goals-per-game and average attendance by tournament
- **Top nations & stadiums** — all-time scoring leaders and biggest venues
- **Every final** — champions highlighted, extra time / penalties noted
- **Match archive** — live search over all 852 historical matches (team, city, stadium, stage, year)
- **2018 preview** — FIFA ranks and pedigree of the 32 Russia 2018 teams
- **2022 deep dive** — per-team aggregates (W/D/L, possession, attempts, passing, discipline) and every match scoreline
- **2026 groups** — the twelve groups of four, with TBD playoff placeholders flagged
- **2026 schedule** — all 104 fixtures with venue, city and local kickoff time; filter by stage
- **Host cities** — the 16 venues across the USA, Canada and Mexico with match counts

## Regenerating the data bundle

```bash
python3 build.py   # reads the CSVs, writes docs/data.js
```

## Notable observations

- The dataset spans 20 completed tournaments (1930–2014), the 2018 preview, all 64
  Qatar 2022 matches and the full 2026 schedule — one continuous timeline in a single site.
- 2026 is the first World Cup with 48 teams (12 groups of 4) and 104 matches; the opener
  is in Mexico City on 11 June 2026 and the final at MetLife Stadium on 19 July 2026.
- Knockout fixtures in 2026 are slot-based (`1C vs 2F`) until qualifiers are decided;
  these teams are marked as placeholders in the data.