# Code Review — 2026-06-18

## Summary
Current approach: **Fast category scraping** (4 listing pages) vs profile-by-profile (300+ requests). Kept as-is for speed.

## Issues Noted (Not Fixing Now)

### 1. Category flags ≠ actual services
- Leila: listed in `anal_natur_no_condom` + `mundvollendung_cum_in_mouth` → a0=🍑, cim=💦
- But her profile lists: Klassisch, Busenerotik, Deep Throat, Foto/Video, Girlfriendsex, Strip, Zungenküsse
- **Root cause:** Site category listings are upsell/noisy; profile page is ground truth
- **Tradeoff:** 4 requests vs 342× profile requests (~20 min vs ~5 sec)

### 2. gallib.py monolith (700+ lines)
Mixes: parsing, pandas ops, file I/O, HTML generation, stats, delta comparison.
Should split: `scrape/`, `parse/`, `normalize/`, `storage/`, `render/`, `vote/`

### 3. Merge logic lossy
`dfComprehend` groups by `(Girl, Tel, sid)` and takes `.max()` — flags OR together correctly for same gal, but would merge different gals sharing name+tel (rare, fixed by adding `sid`).

### 4. No profile page scraping
Rich data (prices, availability, reviews, full service list) unused.

### 5. Bash + Python hybrid fragile
`getGals.sh` (wget, tar, rclone) + `gallib.py` (parse, merge, render). Should unify in Python with `httpx`/`aiohttp`.

### 6. Vote server (`vote.py`) issues
- Cache invalidation only on file mtime (misses DB changes)
- No CSRF/auth on `/api/vote`
- Single-threaded `HTTPServer`
- No rate limiting
- `votes.db` committed (should be in `.gitignore`)

### 7. No data validation
No schema validation, fragile `sid`/`gid` extraction, no handling of deleted listings.

### 8. Manual deployment
nginx + systemd configs not versioned, no docker-compose/ansible, no health checks.

## Decision
**Kept current fast-scrape architecture.** Category flags are "good enough" signals for filtering. Profile scraping would add 300+ HTTP requests per run — not worth it for the voting use case.

## Files Changed This Session
- `gallib.py:346` — groupby now includes `sid` (fixes Vivien merge bug)
- `vote.py` — new voting server
- `votes.db` — SQLite for votes
- `all.html` — regenerated

---

## 2026-06-18 (follow-up)

### 9. Price info in table
- Profile pages often have prices (e.g., "30min 80€ / 60min 120€" for Leila)
- Would be valuable in the HTML table
- Currently not scraped — would require profile page requests
- **If available conveniently** (e.g., in category listing JSON or meta tags), add column
- Otherwise skip for now (same speed tradeoff)
