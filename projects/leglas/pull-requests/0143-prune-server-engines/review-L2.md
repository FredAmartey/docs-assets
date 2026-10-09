# Lane L2 preservation review

Step 6 of the test-pruning campaign for lane L2 (the server package's tests in `agents`, `generation` and `capture`). Reviewed head: 791ad33 on `cloud/test-prune-l2-ica8y1`, compared with `cloud/test-baseline-3ruyq4` (516ace2). This file is temporary, like the rest of `campaign/`.

## Result

- Every `D` (14) and `C` (46) in `ledger-L2.md` and every rewritten test in the eleven files was read against its keeper and its production owner.
- **One gap, restored:** a stop of one direction no longer had a test that it answers `true` on a machine without a browser. Restored in 87fa78f, with a break that is green on the lane head and red after.
- **No assertion that cannot fail** was introduced. One weak refusal row predated the lane and is now pinned to its own sentence (below).
- **No production change:** the lane touches tests and `campaign/` only.
- **Lane L1's keepers:** both tests L2's deletions lean on are byte for byte the same on `cloud/test-prune-l1-5git9i` (899a05c) as on the baseline.
- Every other deletion and fold holds. Each one that rested on reading now has a break run against its keeper in `breaks-review-L2.json`: red where the keeper must catch it, green where the break shows the deleted test guarded nothing observable or that only one keeper can see it.

## How it was read

1. The lane's diff against the baseline, every deleted or rewritten test in full, then the keeper the ledger names, then the production line both reach.
2. A script listed every `expect` statement of each baseline file that no longer appears in the lane's file (normalised for renames such as `started.job.id` to `set.id`). Each of the 117 that left was traced to a table row, a keeper or a deletion mark. One was traced to nothing: the gap below.
3. Breaks with `campaign/breaks-review-L2.py`, which works like the lane's script (patch the owner, run the keeper, restore and check the sha256) and adds the outcome the review expects. 19 runs, all owners restored byte for byte.

Coverage was not used as evidence for any finding. It measures execution: the gap below sits on a line every lifecycle test runs.

## Restored

### A stop of one direction answers that it stopped something

- **Lost:** `generation.test.ts` (baseline line 989), in "a direction stopped while its page is being rendered stays stopped": `expect(await generations.stop(started.job.id, slot.key)).toBe(true)`. The cutover folded that test and line 1337 into one table (`%s while a page is being rendered ...`) and the stop row stopped reading the answer. The ledger does not mention it.
- **Contract:** `stop` returns `targets.length > 0` (`generation/generation.ts:1325`), and `actOnGeneration` (`server.ts:1080`) turns `false` into `409 Nothing to stop there right now.` A stop that answers `false` after stopping the direction shows the person an error for a stop that worked.
- **Remaining proof before the restore:** only the end-to-end test (`generation.test.ts:632`, the `generate/stop` route's 200), which skips when `findBrowser()` finds nothing. Every other `stop` call in the file ignores the answer, and the set-wide stop at line 1129 takes the planning branch, which answers `true` unconditionally.
- **Break** (`generation stop answer`): the answer is read from the slots after the stop has already marked them stopped, so it is always `false`.
  - Lane head: the table stays green (2 passed); the end-to-end test goes red, `expected 409 to be 200`.
  - After the restore: the stop row goes red, `expected false to be true // Object.is equality`. Owner restored, sha256 `e8a76e5b…`.
- **Restoration:** the stop row asserts `expect(await ended).toBe(true)` (three lines). The lane's own `generation late render` break, rerun on the restored table, still goes red on the stop row (`expected 'ready' to be 'stopped'`).

## Checked and holding

Deleted tests are named by their baseline line and keepers by their line on the review head. "Same call" means the fold keeps the same production function, the same input and the same expected value.

### Deletions the brief asked about

| Deleted | Keeper | Verdict |
| --- | --- | --- |
| `agents.test.ts:466` Claude tool-use label | `generation.test.ts:1783` "a build and its fix run say what they are doing" | Holds. The fake Claude stream sends `Write` and `Edit` with `file_path`, `createGenerations` runs `activityFrom("claude", line, cwd)` (`generation.ts:844`) and the test asserts `editing .leglas/variants/hero/hero-ledger.tsx` for both. The deleted unit used a relative path; the relative branch of `shownPath` is still asserted by the Cursor rows. Break `agents claude edit label`: red. |
| `agents.test.ts:483` Codex file_change label | `generation.test.ts:2405` "plans, builds and fixes with restricted Codex runs" | Holds. The fake Codex sends `item.started` with `changes: [{ path }]` and the test asserts `announced` contains the `editing` label. Break `agents codex file_change label` (path no longer read from `changes`): red, `expected [] to include 'editing .leglas/...'`. |
| `runner.test.ts:1300` Cursor resume that edited is not rerun | `agents.test.ts:421` (captured Cursor stream) and `runner.test.ts:466` (edited resume, Codex) | Holds as a composition. The runner sets `observed.edited` from any vendor's `activityFrom` label starting with `editing` (`runner.ts:630-633`), with no vendor-specific branch; the vendor rule beside it, `activityVerified`, keeps `runner.test.ts:951` and `agents.test.ts:333`. Breaks: `agents cursor edit label` red (`expected 'changing hello.txt' to be 'editing hello.txt'`), `runner edited rule` red. Limit: a future Cursor-only exception written into the runner would pass both; nothing in the runner today branches on vendor there. |
| `runner.test.ts:776` cancelled request recorded as cancelled | `runner.test.ts:540` (status `cancelled`, SIGTERM) and L1 `server.test.ts` "reports a running request and cancels it through the polled API" (code and message) | Holds. `markFailed` writes status `cancelled` only for code `cancelled` (`requests/requests.ts:617`). The no-id `cancel()` answer is held by L1's live-channel test (`/requests/cancel` with no body answers `cancelled: true`). Break `requests cancelled failure`: L1 keeper red (`expected null to deeply equal { code: 'cancelled', … }`); the same break leaves the runner test green, so the L1 test is the one carrying code and message. |
| `agents.test.ts:738` custom choice stores its template | L1 `server.test.ts` "reports available agents and round-trips the saved choice" | Holds. The route saves through `saveAgentChoice` and `GET /api/agents` reads back through `readAgentChoice` from `watch.json` (`server.ts:1993-2003`), not a cache. Break `agents custom run saved`: red. |
| `capture.test.ts:342` the shutter waits for what the page asked for after load, arrived or failed | `capture.test.ts:308` shutter table | Holds without a browser. Every row requests an `Image` after load and asserts the exact shutter time, so an image holds the shutter until it lands; the "failed script" row proves `loadingFailed` releases a request, and the release is type-agnostic (`capture.ts:255-293`). Breaks: `capture failed request` red (`expected 2000 to be 301`), `capture image wait` red (3 rows). The deleted test never proved `Stylesheet` tracking (its image at 60 ms outlasted the sheet at 40 ms); only the real-browser "page drawn after load" test does, as before. |
| `browser.test.ts:730` real browser evaluates JavaScript over CDP | `capture.test.ts:526` "renders a local page, crops its element and reads console errors" | Holds. The keeper launches the same executable through `launchBrowser`, drives CDP through `withPage` and skips on the same condition the deleted test did (`findBrowser() === null`), so no machine lost a run. Break `browser flatten live` (attach without `flatten: true`): the keeper goes red (`Session with given id not found.`) while all 36 fake-socket tests stay green (`browser flatten units`). Coverage lost the one-second kill timer in `close` (`browser.ts:889-890`), which no test asserted before or after. |

### The other deletions

| Deleted | Verdict |
| --- | --- |
| `agent-command.test.ts:109` stub script | Holds. The quoting is held by "keeps a quoted value together as one token, in either quote" and the substitution by "puts the whole prompt in one argv entry, whatever it contains"; the stub's argv takes no other branch of `tokenize` or `commandFor`. |
| `agent-command.test.ts:137` empty queue | Holds. `find` on an empty list; the `null` answer is asserted by the picked-up and all-failed cases. |
| `agents.test.ts:109` and `:125` Codex flags and no model | Hold. `agents.test.ts:33`, `:64` and `:279` compare all three Codex argvs whole with `toEqual`; each contains `--skip-git-repo-check`, the network flag and no `--model` or effort. |
| `process-tree.test.ts:49` a process that never started is only asked | Holds. On Linux and macOS, without the guard `process.kill(NaN)` throws `ERR_INVALID_ARG_TYPE` and the fallback makes the same `child.kill(signal)` call. Break `process-tree unstarted guard`: the runner's cancel test stays green, as expected. The guard's only other effect is on Windows (no `taskkill /pid undefined`), which the deleted test (run as `darwin`) never exercised. |
| `hydration.test.ts:56` empty list | Holds. No branch; the seven negative rows assert `null` from the same `return null`. |
| `generation.test.ts:2150` a build that edits the switch | Holds. Line 1537 strays into the same switch from a build and asserts it is stopped and put back; line 1739 asserts the singular "put the file back" sentence, which comes from the same template; line 1594 asserts `outside-file`. |

### Folds

Every `C` was checked for the same function, input class and expected value, and for a dropped assertion with the script above.

- `agent-command.test.ts`: the refusal table (each row reaches its own branch of `parseTemplate`: glued, twice, as the program, empty), the quote cases and the queue cases are the same calls.
- `agents.test.ts`: the Cursor status answers moved from `detectAgents` to `authVerdict` with `code: 0`, which is exactly what `detectAgents` passes (`agents.ts:469`), and the hook wiring stays in line 150. The single-quoted Codex command row runs through `activityFrom("codex", …)` with a `command_execution` item, not the bare cleaner. Cursor resume, `api_retry` negatives and the Cursor tool_call rows are the same calls.
- `claude-agent-session.test.ts`: lines 234 and 431 fold into the rotation test (line 249). Rotation is one condition, `query !== null && sessionId === null` (`claude-agent-session.ts:369`), whether the earlier turn was fresh or resumed. The effort expectation is stronger now (same effort on both turns, so a carried-over `appliedEffort` fails it).
- `runner.test.ts`: the Claude fallback row (`--effort high` instead of `xhigh`, the same flag), the session cap test now asserting the resumed thread id, the allowance queue (whole tail after `--allowedTools`, stricter than the two-entry slice) and the warm table. In the "nothing asked for" row, `releaseAllBut` releases both transports in one synchronous loop (`runner.ts:349-357`), so waiting on the Codex release cannot check the Claude one too early.
- `browser.test.ts`: each `findBrowser` row keeps its old search input or a stricter one ("LEGLAS_BROWSER before CHROME_PATH" now has both paths present). The exit code and the browser's words come from one sentence (`browser.ts:420`), so one failure can carry both. The grace table is the same comparison from both sides.
- `capture.test.ts`: the `cropBox` table is the same three calls.
- `generation.test.ts`: the refusal table now matches the whole `leglas new` sentence. Stop and close during registration are now one test. Break `generation stop drain` (the planning stop no longer waits for writes) goes red with `expected [ 'stop' ] to deeply equal []`, so the stop's own wait is still proven next to the close. The build-step label, the hundred-set prune (its fixture's oldest set builds `hero-a`, so the name holds) and the Codex fix run are the same calls in their keepers.

## Assertions that cannot fail

None introduced. Every new table row reaches the branch its name says, and the two "nothing" cases (the warm table's `kept.release`, the reaper's `removed`) read state the production path writes.

Weak, and as weak at the baseline: the refusal row `["claude --message={prompt}", "{prompt}"]` in `agent-command.test.ts`. Every refusal message contains `{prompt}` through its example, so the text check could not tell which refusal fired; it failed only if the input was accepted. Pinned after the review: the row now expects `{prompt} must stand as a word of its own`, the sentence only that refusal gives (`agent-command.ts:86`).

- **Break** (`agent-command glued reason`): the glued refusal gives the "takes `{prompt}` once" sentence of the double-placeholder refusal.
  - Before the row was pinned: green, 5 passed (the four refusal rows and the unclosed-quote test).
  - After: the glued row goes red, `expected 'The agent command takes {prompt} once…' to contain '{prompt} must stand as a word of its …'`, while the other three refusal rows and the unclosed-quote test stay green (1 failed, 4 passed). Owner restored, sha256 `321e99f0…`.

## Production changes

None. `git diff origin/cloud/test-baseline-3ruyq4..HEAD -- . ':(exclude)*.test.ts' ':(exclude)campaign/**'` is empty: no export, parameter or wrapper was removed and `api-surface.txt` is unchanged.

## Type check of the test files

The repository's typecheck excludes `*.test.ts`, so the eleven lane files were checked with a throwaway tsconfig (not committed): 23 errors on the review head against 80 for the baseline versions of the same files, with no error kind the baseline lacked (stub timers typed as strings, transports missing `release`, spawn mocks, fixture configs). The restoration adds none.

## Numbers

Test lines and declarations in the lane's eleven files:

| | Baseline | Lane head 791ad33 | Review head |
| --- | --: | --: | --: |
| Test lines | 9,016 | 7,355 | 7,358 |
| Removed | | 1,661 (18.42%) | 1,658 (18.39%) |
| Short of the 1,803-line target | | 142 | 145 |
| Declarations | 243 | 187 | 187 |

`pnpm test:coverage` on the lane head and on the review head, run as `baseline.md` says (Node 24, `LEGLAS_BROWSER` set to the no-sandbox wrapper): both 4 failed, 1,839 passed, 2 skipped, 2 errors, the baseline's four VM-only failures. The review adds no case. `pnpm test` on the review head gives the same counts.

| Scope | Baseline | Lane head (this review's run) | Review head |
| --- | --- | --- | --- |
| Total lines | 82.14 | 82.14 | 82.17 |
| Total branches | 72.59 | 72.60 | 72.61 |
| Total functions | 75.09 | 75.09 | 75.15 |
| Total statements | 79.47 | 79.49 | 79.51 |
| server lines | 91.88 | 91.88 | 91.93 |
| server branches | 81.44 | 81.46 | 81.48 |
| server functions | 87.27 | 87.27 | 87.42 |
| server statements | 88.86 | 88.89 | 88.93 |

Every other package is unchanged in all three. Files below their baseline covered counts:

- Lane head: `capture/browser.ts` lines 353 to 351, branches 197 to 196, functions 93 to 92, statements 397 to 395 (the close timer the lane reported, and one branch more in this run).
- Review head: none.

The two runs differ only in `capture/browser.ts` (+5 lines, +2 branches, +3 functions, +6 statements) and `server.ts` (-2 lines, -1 branch, -1 function, -3 statements), the close and reaper counters and the health probe that `baseline.md` lists as races. The restoration asserts on a line every stop already runs, so it moves no number. The one-second kill timer in `close` counted in the review-head run and not in the lane-head run, with no change between them that reaches it, so since the live `launchBrowser` test went it is a race like the baseline's line 882 rather than a steady loss. The lane's own run read server lines 91.85; the three runs sit inside the races.

## Second opinion on the target

I agree with the lane. Its 142-line shortfall is honest: what is left in the lane is mostly real-browser proof of in-page behaviour, transport races and named regressions, each with no other test. One R test could have gone with a keeper elsewhere, and the coordinator decided to keep it as it is:

- `runner.test.ts:1060` "leaves every transport cold until something asks for it" (18 lines). L1's `server.test.ts` "the composer can ask for the saved agent to be warmed" boots the real server with a saved Claude choice and asserts no warm before the warm route. The runner test adds a poll tick and the Codex side, both of which run the same `tick` code as boot. It crosses into L1's lane, so it is safe only while L1 keeps that test.

No other R test has a keeper that asserts the same contract with the same input. Deleting the runner test would still have left the lane about 125 lines short of 20%.

## For Fred

- Lane L1's review branch (`cloud/test-review-l1-*`) is not on origin yet. The two L1 tests that carry L2's deleted contracts must survive it and the merge of the lanes: "reports a running request and cancels it through the polled API" and "reports available agents and round-trips the saved choice".
- Decided after the review: the weak refusal row is pinned, and the runner warm-at-boot test stays.
