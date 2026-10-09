# Lane L3 preservation review

Step 6 of the test-pruning campaign for lane L3 (cli, mcp, site, scripts and the repository tests). Reviewed head: `cloud/test-prune-l3-8c91or` at 9b4180f, against `cloud/test-baseline-3ruyq4` at 516ace2. The question was which contracts lost their only proof, not what else could go.

## Method

- Read `campaign/baseline.md`, `campaign/ledger-L3.md` and the test-audit campaign guide. The repository has no `AGENTS.md`; `CONTRIBUTING.md` holds its rules.
- Read every deleted and rewritten test in the lane diff in full, old and new side by side, then each keeper the ledger names and the production owner behind it. Counted `expect(` calls per file before and after to find every place an assertion went missing.
- Printed what the parser and `planKeep` actually answer for each refusal row in the rewritten tables, to catch rows that pass on a different guard than the one they name.
- Replayed the breaks the lane asked about (B29, B36 to B45) and four more of the riskier ones (B26, B27, B31, B35) with a runner that edits by exact unique string, runs the keeper and restores with `git checkout`, checked with `git diff --exit-code`. All went red and every restore was byte for byte.
- Proved each gap the same way before restoring it: the break stays green on the lane head and goes red on the restored keeper.

## Findings

### Gaps restored

| Id | Lost contract | Where it was | Keeper now | Break | Before restore | After restore |
| --- | --- | --- | --- | --- | --- | --- |
| G1 | Under `--json` no update check runs an hour later either, so an agent's run never asks npm | `run-update.test.ts` › JSON output remains one envelope with no startup check (D) | `run-update.test.ts` › `--json` suppresses the startup check, a row of the env opt-out table (commit 6ebe21d) | In `run.ts`, the hourly `setInterval` moved out of the `!options.json` guard into its own `if (deps.updates !== undefined && !skipStartupCheck(process.env))`, leaving the startup check guarded | Green: `run-update.test.ts` and `run.test.ts`, 35 passed. The baseline's own `run-update.test.ts` run against the same break fails on the deleted test, so it was the only proof | Red: `--json suppresses the startup check`, at the after-an-hour `not.toHaveBeenCalled()` (line 167) |
| G2 | The lower end of the port range: `--port 0` is refused, not booted | `args.test.ts` › rejects a port outside the valid range (C into K-args-refuse) | K-args-refuse row `["--port","0"]` with the exact message (commit e768ec3) | In `rules.ts`, `portRefusal` compares `port < 0` instead of `port < MIN_PORT` | Green: `args.test.ts`, `tools.test.ts` and `parity.test.ts`, 123 passed | Red: `refuses ["--port","0"], saying why` (parsed as a run on port 0) |

G1 is coverage-blind: the hourly timer's callback is never run with `--json`, and the startup check sits on the same lines, so nothing moved. The ledger's evidence for the deletion was that the timer "sits inside the same `if` as the check" and that the env rows keep it off. That is a statement about today's code shape: a refactor that splits the two (the break above) breaks the contract and nothing else. The `run.test.ts` notice table, which the ledger names as keeper, checks the envelope and the startup check and was left as it is; the restored row carries only the half it cannot see.

G2 is an unfailable row, not a deletion. `--port -1` is refused by `parsePort`'s `^\d+$` test ("needs a number") before `portRefusal` runs, so the lower bound had no proof at baseline either. The lane moved the row into K-args-refuse with `expect.any(String)`, which is where the review looks for rows that cannot fail. The `-1` row stays (it is still a refusal); the new row reaches the range.

### Deletions (D) that hold

| Deleted | Keeper | Verdict and evidence |
| --- | --- | --- |
| `tools.test.ts` › lists the same tools the CLI offers | `parity.test.ts` › every command has a tool or a reason | Holds. Parity lists the tools from a real `registerLeglasTools` over an in-memory transport and compares them with the names in its `FACES` table, so a renamed or dropped tool fails it (B36 replayed: red, plus the route test). A deliberate rename has to edit `FACES` exactly as it had to edit the deleted inventory. |
| `api-surface.test.ts` › a name nothing on the chain declares is missing | `api-surface.test.ts` › the surface refuses to build around a name nothing declares | Holds. `publicSurface` throws only when `resolve` returns `missing`; any other answer for a missing name (found, external) skips the throw and fails the keeper (B43 replayed). |
| `changelog.test.ts` › every indexed version in a shared heading has one landing anchor | `changelog.test.ts` › renders as one page that every release link lands on | Holds. `releasesIndex` is built on `parseChangelog`'s own `versions` (`site/release-notes.ts`), so the versions the update panel links to are the ones the keeper checks, and the real CHANGELOG's `0.1.0 and 0.1.1` heading is permanent (B44 replayed). |
| `release-notes.test.ts` › the real 1.0.0 entry has a title and a body | the `release-notes.ts command` tests, and line 41 | Holds, with a weaker real-data check. The command tests compare the script's output with `releaseNotes` itself, so on the real entry they only catch a null (B45 replayed). What they cannot see (an empty title or a body that runs on) is a parser rule, and the synthetic test at line 41 owns it with an exact `toEqual` over the same heading shape, `### Added`, a bold lead, indentation and an image, stopping at the next heading. The deleted title assertion was copied from CHANGELOG.md. `test/publish.test.ts` stubs `node`, so it never read the real entry either. |
| `run-update.test.ts` › JSON output remains one envelope with no startup check | `run.test.ts` notice table | Gap, restored as G1. B29 (the whole `!options.json` dropped) does turn the keeper red; the timer-only split does not. |

### Consolidations (C) checked

Every C in the ledger was read against its keeper. All hold except the `-1` row above. Notes worth keeping:

- `args.test.ts`: all 65 old declarations map to rows with the same argv class and the same or a stricter assertion (exact messages where the old test was exact, `stringContaining` where it checked a substring, `any(String)` where it checked only the kind). Sharing one title and url across the `add` rows loses nothing: `parseAdd` and `addRefusal` never read a value's content, only whether it is present or empty. Every `takes` row without a `kind` still names a field only a successful parse has, so an error result cannot satisfy it.
- `toMatchObject` with `undefined` values (the `add()` row, the `watch` rows) requires the key to be present, where the old `toBeUndefined()` did not. Stricter on structure, not a gap.
- K-keep-refuse compares case-insensitively; two rows (`Nope`, `.leglas`) used to compare exactly. Each row still reaches its own refusal (printed: not found, cannot tell, inside `.leglas`, inside the project twice). Accepted.
- K-new-param now also asserts the browser switch does not contain `searchParams`. Correct today; a `new URL(location.href).searchParams` rewrite would trip it. Accepted.
- K-show-malformed's null rows answer health with `{ cwd: 42 }` where the old test answered with this project's `cwd`. A non-string cwd is accepted as no evidence, so the capture is still requested and the null reaches `hasCaptureError` and `hasCaptureSize` (B26 and B27 replayed).
- The `run.test.ts` `--no-open` assertion moved into the dev-server owner test. `run.ts` calls `deps.open` on `options.open` alone, so the warning in that test cannot be what keeps the browser shut (B31 replayed).
- `changelog.test.ts` line 62 moved into `build.test.ts`; it dropped `expect(written).toContain(path)`, which the build test's exact file list (with `releases.json`) already carries.
- K-watch-no-template's JSON half: the first break tried here (setting `options.json` inside the refusal) stayed green because `runWatch` reads `json` once into a constant. That was a bad break, not a gap: the real one (the refusal's JSON branch disabled) turned it red, as B35 says.

### Compacted (R, compact) and repaired (F) tests

- No assertion changed in `run-share`, `run-show` (but the folded null rows), `run-keep`, `run-link`, `run-remove`, `run-previews`, `run-watch`, `bin-update` and `channel`. `addLocal` is stricter than the hand-built literals it replaced: it throws on a nonzero exit, which the old fixtures ignored. `capturing()` builds replies with `Response.json`, which adds a JSON content type; `runShow` never reads headers.
- `engagement.test.ts` (F) drives the real `post` and clock through a stubbed `fetch` and fake timers. Each old assertion has a counterpart: the posts in order, the beat two seconds later, no stacked timer (timer count 1 in place of the harness's tick), exactly one `false` on lapse with nothing pending after it.
- The coverage-blind tests (the `watch --json` process, the stdio instructions, the release-notes command and the mcp `start` and `link` tests on the built bundle) are untouched.

### Breaks replayed

Each edit below was applied to the lane head by exact unique string, the keeper run, then the file restored with `git checkout` and checked with `git diff --exit-code`.

| Lane id | Break as replayed | Red |
| --- | --- | --- |
| B26 | `hasCaptureError` loses `value !== null` | `rejects malformed capture fields: null (503)` |
| B27 | `hasCaptureSize` loses `value !== null` | `rejects malformed capture fields: null (200)` |
| B29 | the update guard loses `!options.json` | `prints the appropriate notice for true JSON …` |
| B31 | `run` opens the browser regardless of `open` | `warns without blocking when a local dev server belongs to another project` |
| B35 | `runWatch`'s refusal never prints the JSON envelope | `refuses to start with no template anywhere` |
| B36 | the `list` tool registered as `lists` | parity: every command has a tool, and each tool a route names |
| B37 | `requests` clears by default | `working the queue marks the session engaged` |
| B38 | `explore` drops `basedOn` | `explore briefs the set …, or variants of a direction` |
| B39 | `add` drops `file` | `add registers a url, a branch or a file …` |
| B40 | `add` drops `branch` | the same |
| B41 | a captured envelope is never `isError` | the same, and `show answers for one direction …` |
| B42 | `list` runs without `--json` | `add registers a url, a branch or a file …` |
| B43 | `publicSurface` writes an empty entry for a missing name | `the surface refuses to build around a name nothing declares` |
| B44 | the shared heading's alias anchors start at the third version | `renders as one page that every release link lands on` |
| B45 | `releaseNotes`' heading regex loses its colon | both `prints … from any working directory` rows |

### Production changes

- `packages/cli/src/run.ts`: `runWithServices` lost its `loadConfig` and `readLocalPreviews` services. Its callers are `run` (passes none), `run.test.ts` (passes `inspectLocalDevServer` and `startServer`) and `run-update.test.ts`. It is not exported from `packages/cli/src/index.ts` and not in `api-surface.txt`.
- `packages/mcp/src/engagement.ts`: `EngagementDeps` and the four fallbacks went. `createEngagement` and `EngagementDeps` are not exported from `packages/mcp/src/index.ts`; `tools.ts` calls `createEngagement()` bare, and embedders pass their own `Engagement` through `registerLeglasTools`, which is unchanged. The ledger does not mention one more line: `touch` returned `post(true).catch(() => {})` and now returns `post(true)`. That is safe because `post` ends in `.then(() => {}, () => {})` and `fetch` reports failure by rejecting, so `post` never rejects. Checked by break: removing that second handler turns `a rejecting post never fails the touch that carried it` red, so the contract now rests on `post` and is still proved.
- `pnpm api:update` on the final head leaves `api-surface.txt` unchanged.

### The `run.test.ts` server-refusal replay

`run.test.ts` › keeps the preview idle and reports the missing devCommand only when it is opened ends by posting `/api/previews/start` and expecting the devCommand 400. Lane L1 (`cloud/test-prune-l1-5git9i`, ledger row 2366) kept `server.test.ts` › validates branch start titles and the command needed to boot them as R, so after both lanes merge the server's refusal has its owner. The CLI test should still keep its 400: it is the only check that a project whose config has no devCommand reaches the server without one. If `run` ever filled in a default command, the preview would start instead and only this assertion would notice. No change.

### Typecheck of the test files

The package tsconfigs exclude `src/**/*.test.ts`, so `pnpm typecheck` never reads the cli and mcp tests. A throwaway tsconfig (in the session scratchpad, not committed) extending `tsconfig.base.json` over `packages/cli/src/**/*.test.ts`, `packages/cli/src/test-helpers.ts` and `packages/mcp/src/**/*.test.ts` gives no error in any file the lane or this review edited. It reports 31 errors in `packages/mcp/src/parity.test.ts` (TS2322, `Flag` is not assignable to `RouteFace`), a file neither touched; they predate the campaign. The site, scripts and test files are in the root tsconfig, which `pnpm typecheck` runs.

## Numbers

Both heads measured here with `pnpm test:coverage` as the baseline describes (Node 24, the `--no-sandbox` Chromium wrapper in `LEGLAS_BROWSER`). Both runs are comparable: 4 failed (the baseline's IPv6 and root failures), 2 skipped, 2 errors.

| | Base 516ace2 | Lane head 9b4180f | Review head |
| --- | --: | --: | --: |
| Lane test lines (files) | 8,329 (37) | 7,172 (36) | 7,179 (36) |
| Removed from base | | 1,157 (13.9%) | 1,150 (13.8%) |
| Declarations | 414 | 279 | 279 |
| Lane cases run | 471 | 442 | 444 |
| Full suite passed | 1,859 | 1,830 | 1,832 |
| Production lines | | -18 | -18 |

The review adds 7 test lines (two table rows and their comments) and no production change.

| Coverage | Base | Lane head | Review head |
| --- | --- | --- | --- |
| Total lines | 82.14 | 82.21 | 82.20 |
| Total branches | 72.59 | 72.65 | 72.65 |
| Total functions | 75.09 | 75.29 | 75.26 |
| Total statements | 79.47 | 79.55 | 79.53 |
| cli (lines, branches, functions, statements) | 77.82, 73.50, 77.63, 76.02 | 78.13, 73.70, 78.05, 76.30 | 78.13, 73.70, 78.05, 76.30 |
| mcp | 86.63, 84.96, 77.92, 85.29 | 87.37, 87.90, 83.56, 86.58 | 87.37, 87.90, 83.56, 86.58 |
| site | 98.02, 85.79, 97.29, 96.79 | unchanged | unchanged |
| scripts | 93.80, 82.71, 100, 93.79 | unchanged | unchanged |

The lane's packages read the same on both heads; the small moves in the totals are server files (lane L1's), the timing races `baseline.md` lists. The comparison snippet reports the same two files on both heads, each for code the lane deleted: `cli/src/run.ts` branches 97 -> 94 and `mcp/src/engagement.ts` lines 27 -> 25, branches 15 -> 11, statements 31 -> 28. Neither restoration moves a covered count in any cli, mcp, site or scripts file (compared file by file between the two heads), which is the point of reading assertions rather than coverage: both contracts ran on lines other tests already reached.

## Validation on the review head

- `pnpm format:check`: clean.
- `pnpm lint`: exit 0. Three `no-useless-spread` warnings in `packages/shell/src/net/poll.test.ts` and `live.test.ts`, lane L4 files nobody here touched.
- `pnpm typecheck`: exit 0. The throwaway test tsconfig above: no error outside `parity.test.ts`.
- `pnpm api:update`: `api-surface.txt` unchanged.
- `pnpm test`: 1,832 passed, 4 failed (the baseline's four), 2 skipped, 2 errors, 104 files. `pnpm test:coverage`: the same counts.

## Second opinion on the target

I agree with the lane: what is left is, test by test, the only proof of its contract. The one R that could still go is `args.test.ts` › `leglas %s --help prints the help` (12 rows, 19 lines). `parseArgs` answers `--help` and `-h` with one check before any command reads its arguments, so the 12 rows prove one contract twelve times; K-args-take's `shwo --help`, `show Aurora --screenshot --help` and `keep Aurora -h --to …` rows would carry it. Against that, the table is what fails if someone moves help into the per-command parsers and one forgets it, which is exactly what the comment on that check exists to prevent, and `docs/cli.md` tells people each command's options are under `leglas <command> --help`. I would keep it; 19 lines do not change the outcome against a 516-line shortfall.

Nothing else qualifies. Two that look like duplicates and are not: `tools.test.ts` › init writes into the project is the only test that `runInit` writes into the directory it is given (there is no cli `run-init` test), and `run-update.test.ts` › returns without waiting for npm is the only proof startup does not block on the check.

## For Fred

- The lane ends at 13.8% against a 20% target. Reaching 20% would mean deleting tests that are each the only proof of a contract.
- `parity.test.ts` has 31 type errors that no CI step sees, since package tests are outside every tsconfig. Worth a separate fix, or a test tsconfig in `pnpm typecheck`.
