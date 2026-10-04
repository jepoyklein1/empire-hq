# The Empire Strikes Back HQ

League newspaper for The Empire Strikes Back (Sleeper dynasty league).

- **Site:** `index.html` at the root, served by GitHub Pages.
- **Data:** `data/` is refreshed from Sleeper by the "Pull Sleeper data" workflow before each edition (Sun, Tue, Thu at 12:00 AM Central). Run it any time from the Actions tab.
- **Source:** `src/template.html` (layout), `src/edition.json` (all content and numbers), `src/av/` (writer portraits). Rebuild the page with `python3 src/build.py`.

Writers are fictional characters. The numbers come from Sleeper and public sportsbook and injury reports.
