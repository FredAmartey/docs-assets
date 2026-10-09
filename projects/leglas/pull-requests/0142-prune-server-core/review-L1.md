# Lane L1 preservation review: server core

Step 6 of the test-pruning campaign for lane L1, done independently of the session that pruned it. Reviewed: `cloud/test-prune-l1-5git9i` at `899a05c` against the baseline `516ace2` (`cloud/test-baseline-3ruyq4`). Keepers in `server.test.ts` are cited at this branch's head, where most of that file moved; every other test line number is the baseline commit's, as in the ledger. A `file:line` reference is always the head.

## In brief

- **Two contracts had lost their only proof.** Both are restored in their keepers, and each restoration has a break that turns the keeper red. Neither shows in coverage: the lines still run, nothing asserts them.
- **No assertion that cannot fail** beyond the relative-url row the lane already repaired. One weak assertion is noted below.
- **Production changes are sound.** Each removed export, parameter and wrapper had no production caller, and `pnpm api:update` regenerates `api-surface.txt` byte for byte.
- **Three ledger lines are inaccurate.** No assertion was lost through them.
- **On the target:** I agree with the lane. Nothing marked R can be deleted with its contract carried elsewhere. The candidates below are small consolidations.

## Method

1. Read `baseline.md`, the lane ledger and the whole diff `516ace2..899a05c`. For every D and C mark, read the deleted test in full at the baseline and the keeper the ledger names at the head. Then trace the production owner the contract lives in.
2. Coverage was used to find leads, never to clear a deletion. I measured `pnpm test:coverage` at the baseline commit in a separate worktree, and it reproduced the recorded baseline exactly (9793/7852/2237/11067). I measured it again at the lane head. Then I diffed the two runs **by source text** per file: uncovered statements, branch arms and functions. Diffing by source text instead of by count means renumbering and deleted code can't hide a real loss.
3. Each suspected gap got the same test. I broke the production owner on the lane head and ran the full `pnpm test`; a contract with a remaining proof would go red. Then I made the same break at the baseline commit, to show that the deleted test had caught it.
4. I restored each confirmed gap in its keeper, broke the owner again to see the keeper go red, then restored the source with `git checkout`, checking it byte for byte by sha256.

## Gaps found and restored

### 1. A request that names `mode: "variant"`

- **Lost from:** `server.test` 1429 sent `mode: "variant"` explicitly and expected a 200. The cutover merged it with 1362 into "a change forks unless the caller asks to replace, and the two are different requests" (head 1245). The merged test's first send names no mode, so no test sent an explicit `"variant"` any more.
- **Why it matters:** the interface always names the mode. `Shell.tsx` builds `{ title, intent: value, mode }`, where `mode` is state that is `"variant"` or `"replace"` (default `"variant"`). Every ordinary send from the interface is therefore an explicit `"variant"`. The route's guard is `parsed.mode !== undefined && parsed.mode !== "variant" && parsed.mode !== "replace"` (`server.ts` 1654). Dropping the middle clause would refuse every default send with a 400.
- **Confirmed:** that break on the lane head left the full `pnpm test` at the baseline's four failures (1772 passed). The same break at `516ace2` turned the old 1429 red with `expected 400 to be 200`.
- **Restored:** one assertion in the keeper, right after the implied send: `expect((await send("variant")).status).toBe(409)`. Naming the default is the same request again, so it is refused as a copy. A refusal of the mode would be a 400 instead, and a misread as replace would be a 200.
- **Breaks:** each turned `server.test.ts:1270` red:
  - dropping `parsed.mode !== "variant" &&` gave `expected 400 to be 409`;
  - `const mode = parsed.mode === undefined ? "variant" : "replace"` gave `expected 200 to be 409`.

  Restored byte for byte (`5cdeb855…`). Commit `f6e143b`.

### 2. A share's status says how far viewers reach

- **Lost from:** `share.test` 543, "open reach serves the app, as it did before there was a list". It asserted `share.reach === "open"` for a share that asked for nothing, plus a 200 for an arbitrary path. The D evidence ("server.test 2956 and 139 both load /pricing with a default share") covers only the behaviour half.
- **Why it matters:** the field is read by `SharePanel.tsx` (528 and 589 show "only what you shared" when it is `"listed"`; 749 and 917 send it back on update), by `shell/src/share/share.ts` 144 and by `cli/src/run-share.ts` 321 and 335, which print the listed notice. It is set at `share.ts` 817.
- **Confirmed:** on the lane head, `reach: share.reach,` → `reach: "listed",` left the full `pnpm test` at the baseline's four failures. At `516ace2` the same break turned 543 red with `expected 'listed' to be 'open'`.
- **Restored:** `expect(created.share.reach).toBe("open")` in the route keeper, "serves a read-only share and keeps its lifecycle on the primary listener" (head 2618). The check sits next to the tunnel check, where the interface and the CLI read the field. The test already proves the open behaviour (`/pricing` is served to a viewer).
- **Break:** the same edit turned `server.test.ts:2672` red with `expected 'listed' to be 'open'`. Restored byte for byte (`83806b71…`). Commit `7df680c`.
- **Not a preservation gap but worth knowing:** neither the baseline nor now has a test that a `listed` share reports `"listed"`.

## Deletions and consolidations checked and kept as the lane left them

Each line names the keeper read and the source that makes it sufficient.

### server.test.ts

- **720 → 697:** the fallback name `"image"` is asserted on a second upload in the same server.
- **736 → 640:** every assertion moved: the reference prompt line, `NO_BROWSER` in the prompt and in `captureNote`, queue attachments equal to the response and the source file gone. The ledger says 643 took 736's "compare"; 736 sent a compare but never asserted it, so nothing moved and nothing was lost.
- **1048, trimmed loop → 3493:** the scan finds `/api/annotations/update` (no exemption in `NOT_A_JSON_OBJECT`), posts the same bodies plus `"{"` and checks that the server still answers.
- **1141 → 1102:** carries the queue's note ids. The reword half is 1005's `reworded.id !== annotation.id`, and every reword reissues the id, not only a held one.
- **1259 → 1102:** carries the second send's 409.
- **1362 → 1245:** carries the variant default and both prompts. The two-requests-queued check is implied by 200, 200, then 409 for the replace. The explicit-variant input class is gap 1.
- **1676 → 1475:** the new check is stronger, because it asserts that warm is not called again. The input differs (`watch.json` of `{}` with a session, against no file and no session), but the route answers `{ ok: true }` on both arms of `readAgentChoice` (`server.ts` 1983–1990), so nothing observable is lost. The ledger says this is "asserted before the choice is saved"; it is asserted after, by blanking `watch.json`.
- **1894 → 1723:**
  - The queued copy's fields are carried, and the capture-less prompt was restored by the lane.
  - What went is the real failing child. A runner failing a request is the runner's own contract (L2, `runner.test`). The server's wiring of the embedded runner to the queue is still proven by 1644, which reads `running` and then `cancelled`, with its failure, through `/api/requests`.
  - The source-text coverage diff shows no `server.ts` statement lost.
- **2011 → 1791:** the 404 with an error string.
- **2024 D → 1284:** dismissing a failed verdict read from the file, which is the state the runner leaves. Same wiring note as 1894.
- **2127 → 1844:** `beat(false)` detaches at once (the lane's break).
- **2245 and 2264 → 1991 table:**
  - `sendConditionalJson` (`server.ts` 247–268) hashes the serialised body. Every route builds its body per request, so "the etag follows the body" is the helper's contract, which 1975 proves.
  - The selector-only anchor was restored by the lane in `annotations.test` 56. The route reaches the anchor only through `anchorFrom` (`server.ts` 2323).
- **2438, 2600 and 2626 → 1936:** carried, with breaks.
- **2642 → 2328:** carried as its first read, with a break.
- **2756 → 2426:** the table row.
- **2900 → 2558:** carries the root route.
- **3167 D:**
  - `share.test` 257 asserts both sentences and `status: 400`.
  - The share route forwards `result.status` and `result.error` unchanged (`server.ts` 1261–1291).
  - The 409 for a second share, with its sentence, is in 2618.
- **3445 D → 3060:**
  - The server wires `options.updates?.onChange(() => live.nudge("update"))` (`server.ts` 2750) with no state in between, and the real hub writes one frame per nudge (`live.test` 84).
  - The fake hub's count of two calls is the only thing that went. It would fail only if state were added between the two.
- **3582 → 3493:** that server boots with an update service, `/api/update/skip` is scanned and the error body is asserted exactly.
- **3719 D:**
  - A public Host with a matching Origin from a loopback peer is 432's 403.
  - Cross-origin from loopback is 1613, 3225 and 3252.
  - All of them go through `isTrustedMutation`.
- **3732 → 3281:** rows for `127.0.0.1`, `127.0.0.53`, `::1`, `::ffff:127.0.0.1` and an undefined peer: one row per arm of `isLoopbackAddress` (`server.ts` 339–347). Each row reaches it, since it is the first check in `isTrustedMutation`.

### Other files

- **`json.test.ts` → the route scan (3493).**
  - Non-object JSON and `"{"` reach `isJsonRecord` and `parseJson` through `jsonBody`.
  - `isString("")` is needed by 1102's empty intent.
  - A coercing `isString` fails 451.
- **`live.test` 151:** the code is deleted. Nothing in `packages/*/src` reads `hub.viewers` or `onViewers`; share counts viewers per link (`share.ts` 1280 and 1291).
- **`proxy.test` 223 → 2558:** the exact body through the real server.
- **`proxy.test` 287 → 235:** `withoutShareCookie` is one generic filter (`proxy.ts` 34–43), and 235's first request is a superset of 287's.
- **`server-info.test` 24 → 1901 and `server-info.test` 46 and 78:**
  - 1901 covers `startedAt` and removal on close.
  - 46 and 78 cover the full record read back.
  - The branch it alone ran is the deleted no-expectation path.
- **`update.test` 920, six rows → 151:**
  - Install arguments come from one table through `commandParts` (`update.ts` 120–145), and 151 asserts every entry as a command string.
  - The berry cache row's detection is 418's.
- **`update.test` 1056 → 1074 and the npm 11 EACCES row of 1310:** the service passes all of stdout and stderr to `installerReason` (`update.ts` 709–715).
- **`update.test` 1198 → 837:** the global restart path ignores `install.command` (`update.ts` 377–382).
- **`update.test` 844, Windows half → 1229.**
- **`config-branch` rejections → the `config.test` table.**
  - Each of the 17 rows reaches its own rule (the lane's breaks).
  - Every row now also asserts a null config.
  - I checked each named string against the other errors the same fixture produces: none of them contains it.
- **`config.test` 6, 19 and 154, and `config-branch` 27, 48 and 91:** absorbed by the defaults and branch keepers.
- **`find-config` 13 → 45.**
- **`load-config` 82 → 22.**
- **`renames` 13 → 25.**
- **`local-previews`:**
  - 84 → 94.
  - 135 → 29 and 144.
  - 172 → `addLocalPreview` validates through `normalizeConfig` (`local-previews.ts` 145), and the config table's url row covers the rule.
- **`branches.test` 55 → 2006:** two concurrent starts through the route, one checkout. For the 177 F, `branches.ts` never reads `worktree.path`.
- **`classify` and `worktree` tables:** same inputs and same expected values. 102, 148 and 199 go to 84, whose `serve.mjs` listens on 127.0.0.1 only.
- **`annotations`:**
  - 121 → 129.
  - 140 and 180 → 245.
  - 196 → 211, which also fails when writes are not serialised.
- **`attachments` 275 → 640 and 364 → 1723.**
- **`requests`:**
  - 299, 303 and 307 go to the `targetFor` table, through the same function.
  - 79, 91, 114, 290 and 696 go to 64.
  - 279 goes to 1245 and 507: the route spreads `...composed` into both the queue entry and the response (`server.ts` 1801–1830).
  - 313, 324, 370, 377 and 383 go to 347.
  - 399 goes to 476 and to the route tests that read minted ids.
  - 414 goes to the own-directory test and to 640's `captureNote`. Its "all filtered reads as absent" detail has no reader that tells `[]` from absent: `runner.ts` 701, `server.ts` 2251 and `log.ts` 49 all use `?? []`.
  - 467 → 476.
  - 659 → 673.
  - 780 goes to 125 and 195: both prompts call `capturedBlock(captured)` with the same argument (`requests.ts` 301 and 359).
- **`share.test`:**
  - 116 → 2618 (port, 32-character token, tunnel and the three share nudges) and 343.
  - 188 → 2618, which gets the manager's own sentence through the real listener.
  - 543 is gap 2.

## Assertions that cannot fail

- **None new.** I checked every table row the lane wrote:
  - config (17)
  - classify (6)
  - slug (4)
  - targetFor (6)
  - conditional reads (3)
  - nudge (2)
  - the `"{"` scan row
  - the loopback rows

  Each has a recorded break, in the lane's table or above. I also checked the rewritten negatives (`not.toContain` in 64 and 347, `warm` called once in 1475, `beat(false)` in 1844). Each fails under a break.
- **One weak assertion:** `server.test.ts:1788`, `expect(bare?.attachments).toBeUndefined()`.
  - `readRequests` drops an empty list (`requests.ts` 526), so the assertion cannot tell `[]` from absent. It fails only if another request's attachments leak into the copy.
  - The restored contract's real check is the prompt assertion beside it, which the lane's break turned red.
  - Left as is.

## Production changes

| Change | Callers checked |
| --- | --- |
| `isLoopbackAddress` unexported | `server.ts` 351 and 2011 only; never in `index.ts` |
| `variantSlot`, `VariantSlot` unexported | `requests.ts` 65 and 323 only; never in `index.ts` |
| `removeServerInfo`'s `expected` required | Exported from `index.ts`. The only caller is `server.ts` 2779, which always passes it; cli and mcp do not import it; `pnpm typecheck` passes |
| `live.ts`: `viewers`, `onViewers`, `now`, `Listener.viewer`, the `viewer` option of `upgrade` | `createLiveHub` callers are `server.ts` 864 and `share.test`. Nothing reads `hub.viewers` or `onViewers`. The `evals/tasks` fixtures call `createLiveHub()` with no options and run against their own base commits |
| `server.ts` `handleUpgrade` wrapper | Both listeners called `live.upgrade` the same way apart from the viewer tag, which only fed the deleted count |

`pnpm api:update` leaves `api-surface.txt` unchanged. In the source-text coverage diff, the only code that lost coverage was code the lane deleted, plus one branch:

- `server.ts` loses only the deleted wrapper; its anonymous functions renumber.
- `live.ts` and `server-info.ts` lose only deleted code.
- `requests.ts` loses the uncut frame's `"the whole page"` branch. The lane noted it, and it was unasserted before and after.

## Ledger corrections

- **`server.test` 1676:** the ledger says the no-choice warm is "asserted before the choice is saved". It is asserted after, by writing `{}` to `watch.json`.
- **`server.test` 736:** the ledger says 643 took its "compare". 736 never asserted one.
- **`share.test` 543:** the D evidence names only the open behaviour. The status field it also asserted is gap 2.

## Second opinion on the 20% target

I agree with the lane. I found no R-marked test that can be deleted with its contract carried by another. The lines that could still go without losing a contract are consolidations:

| Candidate | Keeper | Lines |
| --- | --- | --: |
| `update.test` 1167 "pins the %s runner": keep the npm row and one other, drop two | `update.test` 313's rows assert the same `COMMANDS.npx` entries (the lane's own rule for 920) | 2 |
| `server.test` 2360 and 2374 (config appeared, config removed) as rows of a table with 2328's changed case | the table | ~12 |
| `server.test` 2436 and 2447 (config nudges) as rows of the 2426 nudge table, with a channel column | the table; the late-created `.leglas` case keeps its own setup | ~10 |
| The two setup helpers the lane names (posting JSON, booting with a fresh directory) | no assertion moves | ~300 |

With all of them the lane would remove about 1,430 lines (12.5%). Reaching 20% (2,283) would mean deleting sole owners of security, protocol and ordering contracts.

## Numbers

Test lines are whole files (`wc -l`) over the lane's 22 files.

| | Baseline | Lane head | After review |
| --- | --: | --: | --: |
| Test lines | 11,415 | 10,301 | 10,308 |
| Removed | | 1,114 (9.8%) | 1,107 (9.7%) |
| Declarations | 498 | 393 | 393 |
| Cases run in the full suite (passed) | 1,859 | 1,772 | 1,772 |

The review changed no production code.

### Coverage

`pnpm test:coverage` was run on the final head as `baseline.md` describes. The run is comparable: 4 failed, 2 skipped, 2 errors, 104 test files.

| Scope | Lines | Branches | Functions | Statements |
| --- | --- | --- | --- | --- |
| Total | 82.14 → 82.13 | 72.59 → 72.57 | 75.09 → 75.10 | 79.47 → 79.46 |
| server | 91.88 → 91.87 | 81.44 → 81.42 | 87.27 → 87.33 | 88.86 → 88.85 |
| cli, mcp, shell, site, scripts | unchanged | unchanged | unchanged | unchanged |

| Server folder | Lines | Branches |
| --- | --- | --- |
| src (root) | 90.96 → 90.90 | 84.07 → 84.01 |
| branches | 95.13 → 95.13 | 84.11 → 85.04 |
| config | 94.14 → 94.14 | 90.09 → 90.09 |
| requests | 94.62 → 94.62 | 83.55 → 83.28 |
| share | 90.61 → 90.61 | 75.40 → 75.40 |
| agents, capture, generation (other lanes) | unchanged | unchanged |

Every server folder is within 2 points of the baseline. The snippet's `lost in` lines name the same four files the lane listed:

- `live.ts`: lines 106→99, branches 59→51
- `server-info.ts`: lines 21→19
- `server.ts`: lines 871→869, branches 811→809, functions 196→195
- `requests.ts`: branches 143→142

The source-text diff shows that each is deleted code, apart from the uncut-frame branch in `requests.ts`.

My measurement of the lane head before this review gave 82.13 / 72.58 / 75.10 / 79.46, and the lane recorded 82.15 / 72.61 / 75.10 / 79.49. The difference is the timing races `baseline.md` lists. Between my two runs, the only counter that moved is the output-cap arm in `capture/browser.ts` (198 → 197; the baseline has 197).

The two restored assertions add no coverage. They assert lines that already ran, which is why coverage could not have found these gaps.

## Validation on the final head

- **`pnpm format:check`:** clean.
- **`pnpm lint`:** exit 0, with three warnings that predate the lane, all in shell tests (`net/poll.test.ts`, `net/live.test.ts`).
- **`pnpm typecheck`:** exit 0.
- **The 18 test files the lane or this review edited**, typechecked with a throwaway tsconfig (not committed):
  - 197 errors at the head against 218 for the same files at the baseline, under the same config.
  - None is new in kind. They are the existing patterns: `Response.json()` typed `unknown` under `@types/node`, `Preview` literals without `note` and `tags`, possibly-undefined reads in `share.test` and spawn mock types.
  - The three messages whose text is new are that `json()` pattern on statements whose type annotation the lane or this review rewrote.
  - The repository does not typecheck test files.
- **`pnpm test`:** 4 failed (the baseline's environmental four), 1,772 passed, 2 skipped, 2 errors.
