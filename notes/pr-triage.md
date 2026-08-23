# Upstream PR triage (ideoforms/AbletonOSC → mrkarlos/AbletonOSC develop)

Surveyed 2026-08-23. All 32 open PRs on `ideoforms/AbletonOSC`, which has had no
maintainer activity in ~9 months. Goal: find bug fixes worth pulling into this
fork's `develop` branch now, and catalogue features for later. No code has
been changed as a result of this pass — it's a menu to pick from.

## Already resolved

| # | Title | Status |
|---|---|---|
| **213** | Fix RemoteScriptError in clip_slot callback (logger.info format args) | **Already fixed independently on `develop`** (commit `b995e6c`). Close upstream PR with a thank-you, or leave it — either way no action needed here. |

## Bug fixes — good candidates for `develop`

| # | Title | Author / Age | Notes |
|---|---|---|---|
| **214** | Catch `ConnectionResetError` (WSAECONNRESET) on socket `sendto` | watatatata810, ~2mo | Tiny, additive-only fix to `osc_server.py`. Fixes a real Windows freeze when a client's port closes mid-stream. Low risk. **Applied** — see `fix/214-connection-reset-on-send`. |
| **203** | `/live/clip/get/groove` handler | esaruoho, ~3mo | Resolves a long-standing TODO — `clip.groove` returns an unserializable LOM object; adds a proper handler + test. Tiny, low risk. **Applied** — see `fix/203-clip-get-groove`. |
| **208** | Fix OSC response routing + error resilience | Ahorix, ~3mo | Real bugs (hardcoded response port breaks multi-client use; one bad packet drops the rest of the tick's queue) but **rewrites core `process()`/`_call_method` structure** in `osc_server.py`/`handler.py`. Review/test carefully against this fork's own osc_server changes before merging — not a drop-in cherry-pick. |

Recommended order: **214, 203** first (trivial, safe, both applied) → **208** (touches core `osc_server.py`, needs its own close review since it'd interact with the #214 fix above — re-implement cleanly against current `develop` rather than cherry-picking verbatim).

### Known issues — don't pull without rewriting

- **#89** Fix "Message too long" by chunking oversized OSC messages (StrongBearCeo, ~3.2yr) — was previously listed here as a bug-fix candidate; **downgraded** after checking esaruoho's "Open-PR punch list" comment (posted on upstream PR #204, 2026-05-21): the actual maintainer (`ideoforms`) tested this fix back in 2023 and found it doesn't actually resolve the underlying "message too long" bug, and the author never responded. Don't cherry-pick or reimplement this without independently re-verifying the chunking/reassembly logic from scratch — the wire-protocol change it proposes (chunk index/total/msg-id framing, `random.randint` message IDs) is real work either way, so it isn't a quick win.

### Deferred — real gap, but not being chased right now

- **#113** Improved send support (unify `send`→`sends`, add listen) (steeltrack, ~2.6yr) — the "still need to fix this" TODO this PR resolves is **still present in current `track.py`**, and it's fully isolated from `session_ring.py`/`manager.py` (confirmed: no coupling). However, esaruoho's punch list places it in the "🟪 Likely abandoned" bucket — 1+ year with no author activity, deprioritized for community bandwidth reasons, not because the idea is wrong. Decision (2026-08-23): drop it from the current fix batch. The gap is real and could be revisited later as an independent feature (would need reconciling with `develop`'s already-fixed mixer-listener stray-listener-crash logic in `track.py`'s `clear_api()`/`_start_mixer_listen`/`_stop_mixer_listen`, not a blind cherry-pick of the PR diff).

## Features — good candidates for later

Grouped by area; several upstream PRs compete to solve the same problem — pick one per group rather than merging both.

**Master/return track addressing** (pick one design, not both):
- **#205** Add Master + Return track support (esaruoho, consolidates #84/#189/#197) — well-tested, adds `_resolve_track()` to base `AbletonOSCHandler`.
- **#197** (bimsonz) and **#189** (jwhector) are two independent, earlier implementations of the same `_resolve_track()` idea; #189 has more test coverage, #197 is the dependency other bimsonz PRs (#199 chain handler, #195 arrangement) build on.
- **#84** (markmarijnissen, oldest) — has GitHub-flagged merge conflicts, superseded by the above. Skip.

**Browser API** (pick one, several attempts):
- **#204** (esaruoho) explicitly consolidates #183/#191/#192/#194/#200 into one 30-endpoint `browser.py`. No author-run tests (no local Live access) but cleanest scope.
- **#194** (bimsonz) is a competing, independently complete 25-endpoint browser handler that itself claims to close #183/#192/#191.
- Compare #204 vs #194 directly before picking — both are large isolated new files, neither touches core.
- **#191**'s sidechain-routing/chain-management code isn't covered by either consolidation — worth extracting separately if pursuing rack-chain sidechain control.
- **#183, #192, #200** — superseded, skip (from #200 salvage the small `manager.py` reload-ordering fix for submodules if useful).

**Rack chains / device variations:**
- **#199** Chain handler (25 endpoints) — bimsonz. **Requires #197** (`_resolve_track`/`_has_chains`) to function; bundle together if pursuing.
- **#170** Chain and Chain Device Implementation — suavesav (7.5mo, draft-ish). Independent, fills same gap (no `chain.py` exists today). Compare against #199 rather than doing both.
- **#167** Device Variations API (Live 12 macro variations) — elzinko. Bundles a genuinely useful feature with an unrelated always-on `/live/introspect` debug endpoint; split those before merging.

**Clip enhancements:**
- **#198** Warp markers, extended notes, time conversion — bimsonz. Single focused file, no core touch.
- **#207** `scroll_view`, clip-envelope show/hide, clip transposition — esaruoho. Well-tested, closes #153.
- **#185** Clip dict-registry rewrite (biggest diff in the batch) — **blocked**, depends on unmerged #182; overlaps #198. Pick #198's incremental approach over this rewrite unless you specifically want the registry-pattern refactor.
- **#153** — superseded by #207, skip standalone.

**Track/clip creation (trivial, low risk, pick one impl):**
- **#206** `create_audio_clip`/`create_midi_clip` (esaruoho, consolidates #168/#196) — has tests.
- **#196** (bimsonz) and **#168** (jmiceo) are the two-line versions this consolidates. Skip standalone in favor of #206, unless you want the smallest possible diff — then #196 alone (2 lines) is essentially free.

**Arrangement view:**
- **#195** New `ArrangementHandler` (bimsonz) — standalone, doesn't need `_resolve_track`. Good candidate on its own even without the master/return-track group above.

**Other standalone features:**
- **#120** `/live/song/get/live_set` (file/project/name of open set) — CoryWBoris, ~2.4yr old but tiny/simple, verify it still applies cleanly.
- **#182** clip_slot dict-registry proposal + new endpoints (PhotonicVelocity) — **conflicts with the `clip_slot.py` fix already committed to `develop`** (same file); also the dependency for #185/#186. Treat as a separate architectural decision (whether to move to dict-registry handlers project-wide) rather than a quick pull.
- **#186** Track dict-registry rewrite (PhotonicVelocity) — same registry-pattern question as #182/#185, blocked on #182, would conflict with #196/#197/#189's smaller `track.py` changes.

## Cross-cutting risk notes

- PRs that touch core files (`osc_server.py`, `manager.py`, `handler.py`) — **#208, #205, #197, #189, #186** — should each be diffed individually against `develop`'s already-substantial `SessionRingComponent` rewrite and listener-leak fixes before merging; none of them were written against this fork's current `develop`. (#89 dropped from consideration entirely — see "Known issues" above.)
- The dict-based-registry pattern (#182 → #185, #186) is a real architectural fork in the road: adopting it project-wide vs. keeping the current `methods`/`properties_r`/`properties_rw` list pattern used everywhere else. Worth a deliberate decision rather than merging piecemeal.
- None of the upstream authors had access to a local Live instance to run this project's test suite against most of these PRs — budget time to actually run `pytest` against each before merging, per this repo's own testing prerequisites.

## Suggested next step

**214 and 203 are applied** (see the `fix/214-...` and `fix/203-...` branches merged into `develop`, and `CHANGELOG.md`). Next candidate to look at closely is **#208** (touches core `osc_server.py`/`handler.py`, needs careful review against the #214 change above before pulling in). #113 is deliberately deferred and #89 is off the table — see above.
