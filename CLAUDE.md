# Empire Strikes Back HQ — edition playbook

The league newspaper for **The Empire Strikes Back**, a 12-team superflex PPR dynasty league on Sleeper
(league id `1324744734186422272`). Commissioner: Jeff Klein (Sleeper `HollywoodJK`, team **Sheev**).

- Live site: https://jepoyklein1.github.io/empire-hq/ (GitHub Pages, `main` branch, repo root)
- Layout: `src/template.html` · All content and numbers: `src/edition.json` · Portraits: `src/av/p_*.jpg`
- Build: `python3 src/build.py` writes `index.html` at the repo root. Always rebuild before committing.
- Data: `data/` is refreshed from Sleeper and FantasyCalc by `.github/workflows/sleeper-data.yml`
  at 06:00 UTC (1:00 AM Central) on Sun, Tue and Thu. `python3 src/prep.py` turns it into `data/derived.json`.
- Sleeper's API is blocked from Claude's workspace. Never try to fetch it; use the files in `data/`.

## Schedule

| Edition  | Publishes      | Covers                                              | Writers |
|----------|----------------|-----------------------------------------------------|---------|
| Tuesday  | Tue 2:00 AM CT | Recap of the week that just ended (final scores)    | Margaret Lee, Kenny Park |
| Thursday | Thu 2:00 AM CT | Waiver results + preview of the coming week         | Simone Hart, Kenny Park (Matchup Intelligence) |
| Sunday   | Sun 2:00 AM CT | Injury report + picks for that day's games          | Dr. Anita Wang, Jeff Longwood |
| Every edition when new trades exist | — | Trade grades (5 most recent trades) | Mona Lott |

The site opens on `edition.json → current`. Set `current` to the edition you just wrote. Keep the other two
editions in `editions` untouched so readers can toggle back to them.

## Run procedure (scheduled runs)

1. `git pull origin main`. Check `data/updated_at.txt`. If it is more than 6 hours old, the data workflow did
   not run: continue with what is there, and say so in your final summary.
2. `python3 src/prep.py` and read `data/derived.json`. Use `week_by_date` for the current NFL week.
   Tuesday recaps `week_by_date` (Monday night just finished). Thursday previews `week_by_date`. Sunday covers `week_by_date`.
3. Research on the web (WebSearch, then WebFetch on result pages):
   - Sunday: the week's final NFL injury report (Out / Doubtful / Questionable) and current spreads + totals for every game.
   - Thursday: opening or current spreads + totals for the week.
   - Cross-check lines across at least two sources. Where sources disagree on the favorite, treat it as a pick'em.
4. Update `src/edition.json` (schema below), write the edition, then run the fact-check list.
5. `python3 src/build.py`, then confirm `index.html` contains no `__DATA__`, `Player #`, `undefined` or `NaN`.
6. Commit with a message like `Tuesday Edition, Week 5` and `git push origin HEAD:main`. Pages redeploys in ~1 minute.

## What each edition contains

**Shared updates every run:** `teams` (standings from derived teams: id, team, mgr, w, l, t, pf, pa, max, streak,
`champ: true` stays on Send Nudes / roster 3 for 2026), `weekly` (final week scores), `throughWeek` (last final
week), `moves` (transactions from the current and previous week, newest first, with real player names, FAAB bids,
picks written like `2028 1st (Ben Football Team)`), `movesNote`.

**Tuesday Edition** (`editions.tuesday`)
- `scoreboard`: `mode: "final"`, all six results with `aPts`/`bPts`, `status: "Final"`.
- `lead`: a sensational newspaper-style headline about the weekend and a one-sentence deck.
- Margaret Lee (`avatar: "margaret"`, `color: "blue"`, `serif: true`): matchup-by-matchup recap. Use `sections`
  (one per game: `a`, `b`, `tag`, `p` paragraphs, no `pick`). Real takes on why each game went the way it did:
  which starters hit or busted, bench points left behind, what it means for the standings.
- Kenny Park (`avatar: "kenny"`, `color: "red"`): Tuesday hot takes. Loud, funny, numbers-literate. 4–6 paragraphs.

**Thursday Edition** (`editions.thursday`)
- `scoreboard`: `mode: "upcoming"`, `aProj`/`bProj` from summed starter projections.
- `lead`: headline about the waiver wire.
- Simone Hart (`avatar: "simone"`, `color: "red"`): waiver column. Who spent FAAB, on whom, how much, and who got value.
- Kenny Park (`avatar: "kenny"`, `color: "blue"`, `serif: true`): "Matchup Intelligence" column, no picks.
- `intel`: one card per matchup: `A`/`B` = {rec, ppg, last, proj, pag, eff}, `ga`/`gb` = projected points by QB/RB/WR/TE,
  `note` = "what matters" (no pick). `intelNote` explains projections.

**Sunday Edition** (`editions.sunday`)
- `scoreboard`: `mode: "live"`, Thursday points in `aPts`/`bPts`, projections in `aProj`/`bProj`.
- `lead`: game-day headline.
- Jeff Longwood (`avatar: "jeff"`, `color: "gold"`): `intro` + one `section` per matchup with `p`, `pick`, `note`, `tag`,
  and `book` = {line, total, envA, envB, hiA, hiB}. Line/total come from lineup projections. envA/envB = average
  Vegas implied team total of each side's starters (implied total = (game total − spread for that team) / 2).
  hiA/hiB = starters in offenses implied for 25+. Tags: "Game of the week", "Lock of the week", "Upset of the week",
  "Toilet bowl", or "Sunday".
  - Exactly one `upset: true` pick, and it MUST be the projected underdog. Explain the upset with matchup evidence
    (implied totals, stacks, game scripts, injuries), not vibes.
  - Every pick explains who the starters play and why that matters. Bookie perspective. Memorable, funny, vulgar is fine.
- Dr. Anita Wang (`avatar: "anita"`, `color: "teal"`, `serif: true`, `injuries: true`): injury column plus
  `editions.sunday.injuries` list: {status: out|q|clear, player, nfl, injury, teams: [roster ids affected], impact}.
  Only players who start or matter for a league roster. Note that inactives come ~90 minutes before kickoff.
- **Dynasty Rankings refresh (Sunday only):** replace `dynasty.teams` values from derived `dynasty` (keep each team's
  `breakdown`, add `sched` = weekly results). Update `dynasty.asOf`. Rewrite a team's `breakdown` if the team made a
  trade since its `asOf`, moved 2+ spots in dynasty rank, or its breakdown is the oldest (refresh at least 3 per Sunday).
  Breakdown writers: Margaret (teams 8, 10, 1, 5), Simone (3, 6, 4, 11), Anita (7, 9, 2, 12). Set `asOf` to the week.

**Trade grades (`tradeGrades`, any edition):** if trades completed since the last edition, grade them and keep the
5 most recent. Each side: team, gets, value (market value received), grade (A to F), reason (2–4 sentences).
Grade on value (FantasyCalc market values in derived dynasty data; picks valued as in derived `picks`), fit, and
timing (does the move match the team's window?). Be honest: a value win with the wrong timeline is not an A.

## Writer bible

All writers are fictional characters. Never write as, quote, or impersonate a real person.
- **Margaret Lee** — Tuesday matchup recaps. Sharp, analytical, warm, catches the detail everyone missed.
- **Kenny Park** — Tuesday hot takes; Thursday Matchup Intelligence (pure analysis, no picks: averages, recent form,
  projections, schedule strength, positional edges).
- **Simone Hart** — Thursday waiver insider. Confident, plugged-in, "here's what I'm hearing."
- **Jeff Longwood** — Sunday picks. A frantic, fast-talking degenerate gambler. Swears, exaggerates, bets his watch,
  but every pick is backed by real matchup evidence.
- **Dr. Anita Wang** — Sunday injury desk. Calm, clinical, dry wit. Designations tell you risk, not who sits.
- **Mona Lott** — trade grades. Honest, analytical, unafraid to give a C to a popular trade.

## Fact-check list (do every run)

- Every number in prose matches `data/derived.json` or a cited web source (scores, records, projections, FAAB bids, ages).
- Every player is on the roster/team you say, playing for the NFL team you say.
- Ranks and superlatives ("most in the league", "second-toughest") are verified against all 12 teams.
- Jeff's upset pick is the projected underdog. Picks match the `pick` field.
- Team names are spelled exactly as in `teams` (the first mention in each article is auto-underlined and linked).
- No placeholders, no "Player #id", no invented injuries or lines.
- Pick ownership comes ONLY from derived `dynasty[team].picks` (built from Sleeper's traded_picks.json). Never carry a
  pick claim forward from an older article; re-verify every sentence that says who owns a pick, every run.
- Trade contents (players and picks each side received) come ONLY from `data/transactions/*.json`. Re-read the raw
  trade before grading it.
- Rosters, IR and taxi status come ONLY from `data/rosters.json`. If an older article names a player a team no longer
  has, fix the article.

## edition.json schema (top level)

`season`, `throughWeek`, `current` (sunday|tuesday|thursday), `order` (tab order), `teams`, `weekly`, `moves`, `movesNote`,
`editions` {sunday, thursday, tuesday: {key, label, week, published ("Tue, Oct 6, 2026"), scoreboard {mode, label, sublabel,
games[{a,b,aPts,bPts,aProj,bProj,status}]}, lead {flag, headline, deck}, stories[{writer, role, kicker, headline, avatar,
color, serif, intro[], paragraphs[], sections[]}], injuries[], intel[], intelNote}}, `dynasty` {asOf, method, teams{id: {...,
breakdown {by, headline, p[], verdict, move, asOf}}}}, `tradeGrades` {writer, asOf, headline, intro, trades[{week, title,
sides[{team, gets[], value, grade, reason}]}], note}, `projNote`.
