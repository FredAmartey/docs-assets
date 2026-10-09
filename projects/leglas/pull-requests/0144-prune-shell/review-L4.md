# Lane L4 preservation review: the shell

Campaign step 6 for lane L4, read against `cloud/test-baseline-3ruyq4` (`516ace2`) at the lane's head `91c3e2e`. The question for every `D` and `C` in `ledger-L4.md`: does the keeper it names run and assert the same contract, for the same input class, with the same observable result, so it fails on the same regression? Not a second pruning pass.

How it was read: every deleted or rewritten test in the diff, in full, beside the baseline file it came from; then the keeper the ledger names and the production owner. Where a fold changed its inputs rather than just merging them, the same deliberate break went against the baseline file (in a worktree at `516ace2`) and the lane's file. Every break is one edit to a production file, a run of the keeper's file and a restore checked by SHA-256 (`break.mjs`, not committed; each break is written out below so it can be replayed).

## Findings

| # | Kind | Where | Outcome |
| --: | --- | --- | --- |
| 1 | Lost contract | `poll.test.ts`: folding "stopping ends the loop for good" (265) with 282 and 298 | Restored in `7181a32` |
| 2 | Lost contract | `references.test.ts`: the send-blocker precedence row, rewritten while folding 161 into 150 | Restored in `9511192` |
| 3 | Assertion that cannot fail | `rendered.test.ts`: "different words … disagree", rewritten while folding 12 and 19 | Repaired in `6317a1d` |

### 1. A poll loop stopped between reads

The baseline's "stopping ends the loop for good" stopped a loop whose read had already settled, so `active` was `null` at the stop. The fold kept only a stop with a read in flight (from 298). Stopping between reads is the usual case in production: a read takes milliseconds and the interval is seconds, so a pane that unmounts almost always stops an idle loop. That path returns early from `stop()`, and no lane test checked that the loop ended after it. The nudge test stops an idle loop but checks only that it unsubscribed.

| Break in `net/poll.ts` | Baseline file | Lane file | Keeper after the restore |
| --- | --- | --- | --- |
| `stop()` returns before `stopped = true` and `clearInterval` when nothing is in flight (the `if (active === null) return;` moved up to just after `unsubscribe?.()`) | Red: "stopping ends the loop for good", `poll.test.ts:279`, 31 reads, expected 1 | Green, 10 of 10 | Red: "stopping ends the loop for good, mid-read or between reads, and twice is harmless", `poll.test.ts:144`, 31 reads, expected 1 |

Restored as a second half of the same test: an idle loop, stopped, then 60 s of fake time, still one read. `poll.ts` restored byte for byte (`e188d7d8…`).

### 2. A failed upload ahead of one in flight

The baseline's precedence row was `[failed, uploading]`. The fold replaced it with a four-draft fixture where the upload sits before the failure, `[ready, uploading, failed, ready]`. The ledger is right that the new order catches "the first unfinished draft decides", which the old row could not. But the old order was the only one that caught "the last unfinished draft decides", so the fold traded one direction for the other. `sendBlocker` is order-blind (`some(failed)`, then `some(uploading)`), and a blocked send is a refusal coverage cannot see. Both orders now stand side by side.

| Break in `references/references.ts` | Baseline file | Lane file | Keeper after the restore |
| --- | --- | --- | --- |
| `sendBlocker` returns the status of the last draft that is not ready (`drafts.findLast(…)`) | Red: "a failed upload blocks the send, …", `references.test.ts:169`, `uploading` for `failed` | Green, 10 of 10 | Red: "only uploads that landed become ids, and a failed one blocks the send", `references.test.ts:128` (the restored row) |

`references.ts` restored byte for byte (`c1b78f87…`).

### 3. "Different words" compared a hash with `null`

`renderedSignature` returns `null` below 12 characters of text, and "Choose well" has 11. So `renderedSignature("Ship design faster", ["H1"])` was compared against `null` and passed whatever the words did. Every other signature test uses one shared text, so nothing proved the words reach the digest at all. The baseline test had the same hole; the lane rewrote the line in its fold and repaired the same mistake one test down (case, `F` on 35) but not here.

| Break in `preview/rendered.ts` | Baseline file | Lane file | After the repair |
| --- | --- | --- | --- |
| The normalised text left out of the hashed string (`${tags.join(">")} ${paint…} ${visual…}`) | Green, 25 of 25 | Green, 19 of 19 | Red: "different words, or the same words in a different structure, disagree", `rendered.test.ts:20` |

Now both texts are long enough to sign ("Ship design faster", "Choose a plan today") and the test asserts neither digest is `null` before comparing. `rendered.ts` restored byte for byte (`3e849a62…`).

## What the brief asked to be checked

**`lastEnded` and `buildLabel` (generation 209 and 225, `D`).** Both hold. `buildLabel` is not guarded by page text: Shell.test 607 and 1160 check the submit button's exact `textContent` with `toBe`. Replayed here: `buildLabel` saying "using" turns both red (`Shell.test.tsx:630` and `:1048`), and `agentName("codex")` answering "Claude" turns 1160 red. For `lastEnded`, Shell.test 840 lists the older set first and has it end later, as the deleted unit test did. Replayed: "the last set in the list" and "the set that ended first" both go red at `Shell.test.tsx:834` ("1 of 2 ready. Pantry failed" missing), and the newer set's card would read "1 hero direction ready", so `toContain("2 hero directions ready")` cannot pass on the wrong set. The deleted test's second line (`null` when nothing has ended) has no observable effect: `Shell.tsx` reads `runningJob ?? lastEnded(jobs)` and draws the card only when `endedAt` is set.

**The fold of 968 into 1049.** Holds. `Shell.tsx` ends a set shown whole two ways: a render-time clear whenever the active direction changes, plus `onPick` on the origin row. Replayed the ledger's break (render-time clear removed, `onPick` clears only for the active row): 1049 goes red at its last line (`Shell.test.tsx:951`, 2 shown, expected 0), the "picked a member, then the origin" step that 968 owned. Reopening with "Compare all 2" between picks starts from the same state 968 started from, since the first pick sets `grid` to `null`.

**Fixtures changed while folding.**

- Anchor tree (anchor 93 into 78): the unstable-id case gained a `div` so both cases share one tree. The rule is the same (the `:r7:` id is skipped and the walk goes on to `body`), one level deeper and well under the depth cap.
- `coversFrom` (annotate 190 into 178): the duplicate is now non-adjacent, `[h1, p, h1]`. That is stronger: it catches a dedupe that only drops neighbours and one that keeps the last copy. Spot break, the key on the tag alone: red in both files.
- Send-blocker order: finding 2.
- The live dispatch test now asserts the dialled URL, `ws://<host>/leglas/api/live`. It can fail, and the injected `url` used to hide it.
- Poll 229 (`F`): the repair is sound. One correction to the ledger: the old test could fail on its `aborted` line, since a leaked deadline aborts the controller at 10 s. Only the `armed() === 0` line could not fail on its own.
- Live 230 into 159: the error-then-close now happens at attempt 1, not 0. Same guards on the path. Spot break, both guards against a double redial removed: red in both files.

## Every other `D` and `C`, rejected as a gap

Each with the reason the keeper carries it.

- **agent-api** (51, 87, 122, 143, 160, 173, 190): every request shape is a row of the writes table, now with path, method, headers and body each (87 used to check bodies only). Both deadlines are rows. The read rows record `init: {}`, the same "no method, headers or body" the old `{ input }` meant.
- **mcp-connect** 6, 21 (`D`): restated literals of `MCP_CONNECT_OPTIONS`; no logic reads them but the dialog that prints them.
- **request-status**: all composerAgent inputs (both "disappears" rows included), all seven `requestCard` cases and all status-card lines are in the folds with their values. The quiet and the backoff are independent fields of the card (`requestCard` sets each from the agent), so testing them together loses nothing. 365 (`D`): `notesAwaitingChange` is typed `Set<string>`.
- **annotate, anchor, provenance, naming, keymap, orb, widget, clipboard, overlays, preview-frame, reference, update**: every input and expected value of the baseline cases is in the folds; the only fixture changes are those above. `update`'s `toEqual` on single fields became `toMatchObject` over the view, which checks the same fields.
- **generation** 56, 62, 97 to 194, 217: carried with their values. `isSlotOf` now gets a set that has a slot, which it ignores (of the set it reads only `surface`).
- **Gutter** 66 (`D`): `railInsets` takes the maximum over every row and skips rows that draw nothing, so where a lone root sits on the rail cannot matter. 14, 21: carried.
- **lineage** 189 (`D`): every root, with or without a family, goes through the same `visit(root, 0, …)`. 371, 382 (`D`): `tracedChain` has one caller, `tracedTree`, whose leaf and lone-root tests assert the same chains.
- **prefs** 27 (`D`): 33 keeps a saved order that differs from config order. The fold of the `collapsedFamilies` tests keeps a fold, drops a gone root and defaults to none, including for a save from before families.
- **compare**: every row carried. 220 (`C` into 188) is the same call: the framed-preset block's `stage` and `{ …stage, panes: 2 }` are equal.
- **framing**: every refusal row carried. The refusal hint does not depend on the site, so reading it from the "DENY" case loses nothing.
- **health** 11, 23 (`D`): the identity test asserts `toBe(up)` and `toBe(down)`, which implies the values. 59 (`F`): the repair holds. A branch preview reaches the shell with the proxy's absolute address or none, so the root-relative row is not one the server sends; it is there to make the branch rule the only thing keeping the row off the dev server, and the absolute-address row still covers the address a real branch carries.
- **rendered** 77 (`D`) and 59: 52 asserts the whole twins map, so a unique preview with any entry fails it. 291 into 305: the wrapper chain with a script beside it; a chain with no script takes the same branch.
- **scan** 40 (`D`): 32's `toEqual` on the exact queue leaves the cross-origin preview out. `replacedPanes` compares identity strings for equality, so the new strings exercise the same rule.
- **references** 32, 44 (`D`): `imageFilesFrom` has no caller outside its tests, at this head or at the oldest commits this clone reaches. 76 into 68: stronger, as the ledger says. 88 (`D`): `room` starts at `Math.max(0, REFERENCE_CAP - current.length)` and the full strip meets the same `room === 0` check; the "attached drafts not counted" break turns 68 red.
- **share** 153 (`D`): `viewerPrefsRaw` has two production callers in `useShellState.ts` (the first seed and `adoptLayout`). The `adoptLayout` test runs the same `loadPrefs(viewerPrefsRaw(layout))` and checks the same four seeded fields; `hidden` cannot come from a `ShareLayout`, which has none. 95: the branch, gone and route answers all reach `stageShare` or `railShare`. 278 (`D`): `shortLink` had no caller.
- **tip** 27, 46 (`D`): `placeTip` reaches the same left-edge and flip branches with the same numbers. 32 (`D`) checked that `fitShift` gives 0 on a rect already moved by its own shift; no caller ever does that (`placeTip` measures from the unshifted position on every pass), and `placeTip`'s settle test is the contract that matters.
- **toasts** 15 (`D`): 26 supersedes a kind too. 42 (`D`): `pushToast` filters and slices, so the entry is the object that was pushed.
- **kit**: each label test still guards its label against `null` before a negative `contains` (the first by `textContent`, the second by `not.toBeNull`, the third by `document.body.contains`).
- **Shell.test**: 502 into 479 checks the second request's body, armed by the chip after a variant was sent. 922 moved under `whole()`, which does the same clicks and counts the grid first. `list()` before `submit()` instead of inside it: the stubbed server reads its answers when a request is made, and a set listed early would only take the submit button away and fail the test.

## Unfailable assertions

Searched every line the lane added or rewrote for a negative check, a `null` or empty expectation, a loop or a comparison whose two sides could both be `null`. One found (finding 3). The rest can fail on the regression their test names. Two older ones were left as they were, since neither was touched by the lane: `annotations-api.test.ts`'s refusal passes on the `{ ok: false }` body even without the `!response.ok` check, and the prefs width test stores its `NaN` as `null` (the ledger's follow-up).

## Do the folds still name the rule that broke?

Yes. The folds are sequential expectations with a comment above each case. A failure prints the test name and the line, with the comment in its code frame; every break above shows it (for example `poll.test.ts:144`, `references.test.ts:128`). The tables (agent-api's writes and deadlines, live's frame kinds) name each row. The two loops in `keymap.test.ts` print the kind they expected, which names the key.

## Production changes

Grepped the whole repository (packages, tests included, `site`, `scripts`, `test` and `evals`) for every name and option the lane removed. Nothing outside `packages/shell/src` uses any of them except `startLive({ url })`, which `a37e632` put back; `server.test.ts` › "an announced update reaches the interface's update listener" passes in the final run.

| Removed | Callers outside its own file and tests |
| --- | --- |
| `PollTimers`, `realTimers`, `startPoll`'s `timers` | None |
| `startLive`'s `connect`, `setTimeout`, `clearTimeout`; `LiveSocket`, `LiveEvent`, `browserSocket` | None (`liveConnection()` calls `startLive()` bare) |
| `AgentFetcher`, `browserFetch`, the `fetcher` parameter on seven functions | None (every `Shell.tsx` call passes none) |
| The `fetcher` parameter of `addNote`, `updateNote`, `deleteNotes` | None (`readNotes` keeps its own; `Shell.tsx` passes one) |
| `frameRefusal`'s `fetcher` | None (`Shell.tsx` calls `frameRefusal(title)`) |
| `shortLink`, `imageFilesFrom` | None |
| The `export` on `tracedChain`, `unshareableReason` | Same-file callers only |

Behaviour is the same in each. The one rule that moved, a binary frame carrying nothing, went from `browserSocket` into the message handler as `if (!isString(event.data)) return;`; before, `browserSocket` turned non-text data into `{}` and the handler dropped it. No test asserted that rule before or after: at the baseline its arm was covered only by open and close events passing through `browserSocket` in `server.test.ts`. `api-surface.txt` is unchanged, and `pnpm api:update` regenerates it byte for byte.

## Coverage

`pnpm test:coverage` with the baseline's environment, three times: the baseline here (`516ace2`), the lane head (`91c3e2e`) and this review's code (`6317a1d`). All three show the baseline's 4 failures, 2 skipped and 2 errors; 1,859, 1,672 and 1,672 passed. The baseline run here read 82.16 lines and 72.60 branches in total (the known races left a few counters hit, as in the baseline's third run), with the shell at the recorded 66.03 and 58.53.

| Scope | Baseline (`baseline.json`) | Lane head | After this review |
| --- | --- | --- | --- |
| Total lines | 82.14 | 82.13 | 82.11 |
| Total branches | 72.59 | 72.60 | 72.57 |
| shell lines | 66.03 | 65.85 | 65.85 |
| shell branches | 58.53 | 58.38 | 58.38 |
| shell/references lines | 77.04 | 76.27 | 76.27 |
| shell/references branches | 63.49 | 61.01 | 61.01 |

Matching statements and branch arms by source text, the lane-head run and this review's run are identical across the shell. The totals differ only by seven counters in the server's `proxy.ts`, `server.ts` and `capture/browser.ts`, the timing races `baseline.md` lists. The comparison snippet from `baseline.md` reports the same seven `lost in` files the ledger names, each a file the lane deleted code from.

**`shell/references`, per statement.** Confirmed. `references.ts` goes from 39 of 41 branch arms to 35 of 37 and from 54 of 54 statements to 51 of 51; every arm and statement that left is `imageFilesFrom`'s (its `Symbol.iterator` conditional and its `file != null && …` filter). Over the code both versions have, the folder covers 36 of 59 arms before and after (`references.ts` 35 of 37, `ReferenceStrip.tsx` 1 of 12, `references-api.ts` 0 of 10). Nothing else in the folder moved. Across the rest of the shell, no statement or arm that both versions have lost a hit.

## Test lines

| | Baseline | Lane head | After this review |
| --- | --: | --: | --: |
| L4 test lines | 6,927 | 5,539 | 5,558 |
| Removed | | 1,388 (20.0%) | 1,369 (19.8%) |
| Declarations | 488 | 294 | 294 |
| Cases run | 500 | 313 | 313 |

The restorations add 19 lines (poll 9, references 6, rendered 4) and no new test.

## For Fred

- The restorations take the lane 16 lines under its 20% target (1,369 of the 1,385 needed). Finding them means more pruning, which this review does not do.
- The `shell/references` branch breach is as the ledger says: dead code leaving both sides of the ratio. Whether that counts against the budget is still your call.
- `pnpm typecheck` does cover the shell's tests: `packages/shell/tsconfig.json` includes `src`, and `tsc --listFilesOnly` lists all 35 test files. The other packages exclude theirs.
- Follow-ups, none lost by this lane: the binary-frame rule in `live.ts` has no test; `tracedChain`'s cycle guard has none either (`ancestry`'s is tested); `refusalMessage` has no case for several oversized images or several non-images (`references.ts:101`, `:104`).
