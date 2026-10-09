# Lane L1 ledger: server core

Steps 2 to 5 of the test-pruning campaign for lane L1, plus step 7 for its baseline failures. Scope: every test file in `packages/server/src` (root), `config/`, `branches/`, `requests/` and `share/`, and `packages/server/src/test-helpers.ts`. Line numbers in the tables are the declaration's line at the baseline commit `516ace2` (`cloud/test-baseline-3ruyq4`), so they can be checked with `git show 516ace2:packages/server/src/<file>`.

Every test file and its production owner was read in full, with the owner's callers across packages (`rg` over `packages/*/src`), `api-surface.txt`, the September audit (#105 to #120, mainly #116, #117, #118 and #119) and `git log -S` for the seams involved.

## Marks

- **R** retain: the evidence names the contract and what breaks it. A retained test that absorbs others is called the keeper.
- **F** retain the contract, repair the test (a dead fixture or a table's duplicate rows).
- **C** consolidate: the assertion moves into the named keeper, a table row or a stronger boundary test.
- **D** delete: the evidence names the proof that remains.

## Is the 20% target reachable?

No, not by pruning under the retention bar. Lane L1 is 11,415 lines; 20% is 2,283. What the ledger removes without losing a contract is 1,114 lines (9.8%), though it is 105 of 498 declarations (21.1%), because most of what goes is short tests that a longer keeper already makes. Most of the lane is security, protocol, platform and ordering contracts with a single owner: the share listener's reach and dev-control rules, the mutation trust guard, the update service's install and restart paths, the request queue's file contracts and the HTTP route boundary. Closing the rest of the gap would mean deleting sole owners of those contracts, which the bar forbids.

Folding repeated setup in `server.test.ts` into helpers (booting a server, posting JSON) would remove about 300 more lines without touching an assertion. That is not pruning, so it is left as a follow-up below rather than done to reach the number.

## Layer plan

The keeper for most server behaviour is the HTTP boundary in `server.test.ts`: a real `startServer` on a real port with a real origin, and only the browser pool, agent detection and tunnels injected. The unit suites own what that boundary cannot reach or what is pure: protocol and spec logic (`frame-policy`, `live`, `share` reach rules, `update`), file formats and atomicity (`requests`, `annotations`, `local-previews`, `server-info`, `renames`), and anything needing a non-loopback peer, a driven clock or a fake child process.

Redundant layers found, and their keepers:

| Retired layer | Keeper |
| --- | --- |
| `json.test.ts` (whole file): the JSON predicates replayed one by one | the boundary that depends on them: `server.test` 3924 posts null, strings, arrays, numbers, booleans and malformed JSON to every route; every file reader refuses the same shapes |
| `requests.test` `variantSlot` cases under `targetFor` | `targetFor` table in `requests.test` 30 |
| `branches.test` 55, the registry's in-flight join | `server.test` 2278, two concurrent starts through the route |
| `share.test` 116 and 188, the manager's own entry and mutation checks | `server.test` 2956 through the real share listener, plus `share.test` 343 |
| `server.test` 3167, share title validation at the route | `share.test` 257, which asserts both sentences and that nothing bound |
| `server.test` 3445, update nudges into a fake hub | `server.test` 3458, the same nudge through the real hub to the shell's client (#105) |
| `server.test` 3719, trust rows a loopback peer can reproduce | `server.test` 435, 1784 and 3664 at the boundary |
| `server-info.test` 24, the record round trip | `server.test` 2163 plus `server-info.test` 46 and 78 |
| `attachments.test` 275 and 364, references without a browser and rehoming | `server.test` 643 (with 736 folded in) and 1945 |
| `live.test` 151, the hub's viewer count | nothing: no production code reads it since bd5bc2e; the count itself goes |

Assertions carried into keepers (each C row names its keeper):

- `server.test` 643 takes 736's compare, prompt and captureNote checks; 688 takes 720's fallback name; 1218 takes 1141's queued note ids and 1259's 409; 1429 takes 1362's mode and prompt checks; 1644 takes 1676's no-choice warm; 1945 takes 1894's preserved fields; 1989 takes 2011's 404; 2089 takes 2127's immediate detach; 2198 takes 2438, 2600 and 2626; 2230 becomes one table over requests, annotations and health; 2654 takes 2642's untouched read; 2742 becomes a table with 2756; 2892 takes 2900; 3694 takes 3732's loopback shapes; 3924 takes 3582's malformed row.
- `update.test` 837 takes 1198's exists(argv[1]) check; 920 keeps four of ten rows.
- `config.test` 13 becomes the defaults keeper and 64 the rejection table, taking every rejection case from `config.test` and `config-branch.test`; `config-branch.test` 18 takes 27 and 48; `load-config.test` 22 takes 82.
- `local-previews.test` 94 takes 84.
- `classify.test` 16 becomes a placement table; `worktree.test` 23 a slug table, 41 takes 37 and 84 takes 102, 148 and 199.
- `requests.test` 30 becomes a table; 64 takes 79, 91, 114, 290 and 696; 347 takes 324, 370, 377 and 383; 673 takes 659's quote.
- `annotations.test` 245 takes 140 and 180.
- `share.test` 343 takes 116's url and viewer count.

Test-only production seams the deletions unlock:

- `live.ts`: the `viewers` getter and type field, the `onViewers` and unused `now` options, `Listener.viewer` and the `viewer` option of `upgrade`. Their last production caller went in bd5bc2e. `server.ts` then calls `live.upgrade` the same way for both listeners.
- `server-info.ts`: `removeServerInfo`'s `expected` becomes required; its only caller always passes it.
- `server.ts`: `isLoopbackAddress` is no longer exported (it stays in use inside `server.ts`).
- `requests.ts`: `variantSlot` and `VariantSlot` are no longer exported.

Kept on purpose although they look test-only: `isTrustedMutation`'s export (the only way to prove the peer rule, since every test peer is loopback), `checkFraming`'s `fetcher` parameter (the redirect case cannot be reproduced at the route without depending on how `localhost` resolves), `attachRequest`'s `capture` and `deadlineMs` and `createCoalescer`'s timer options (their tests are kept). Nothing in `api-surface.txt` moves.

## Baseline failures (step 7)

Three L1 tests fail in this VM and pass on CI. All three are the environment, not the product: the kernel has no IPv6.

| Test | Failure here |
| --- | --- |
| `proxy.test.ts` › reaches a target that is an IPv6 literal | listening on `::1` fails with `EAFNOSUPPORT`; the test times out at 20 s |
| `server.test.ts` › reports the dev server as reachable when it is up on ::1 | same, times out at 30 s; the two unhandled errors in the run are these listens |
| `branches/worktree.test.ts` › finds a dev server listening on IPv6 only | the fixture dev server cannot listen on `::1` and exits 1 |

Reproduction: `node -e 'require("node:net").createServer().listen(0, "::1").on("error", (e) => console.log(e.code))'` prints `EAFNOSUPPORT` here. No owner repair applies, so no step 7 commit. All three stay R on their merits (IPv6 regressions on macOS, where `localhost` is `::1`).

## Summary

| File | Declarations | R | F | C | D |
| --- | --: | --: | --: | --: | --: |
| server.test.ts | 119 | 96 | 0 | 19 | 4 |
| json.test.ts | 3 | 0 | 0 | 0 | 3 |
| frame-policy.test.ts | 7 | 7 | 0 | 0 | 0 |
| live.test.ts | 10 | 9 | 0 | 0 | 1 |
| log.test.ts | 7 | 7 | 0 | 0 | 0 |
| proxy.test.ts | 14 | 12 | 0 | 0 | 2 |
| server-info.test.ts | 6 | 5 | 0 | 0 | 1 |
| update.test.ts | 64 | 62 | 0 | 1 | 1 |
| config/config-branch.test.ts | 16 | 5 | 0 | 11 | 0 |
| config/config.test.ts | 19 | 9 | 0 | 9 | 1 |
| config/find-config.test.ts | 6 | 5 | 0 | 0 | 1 |
| config/load-config.test.ts | 7 | 6 | 0 | 1 | 0 |
| config/local-previews.test.ts | 23 | 20 | 0 | 1 | 2 |
| config/renames.test.ts | 10 | 9 | 0 | 0 | 1 |
| branches/branches.test.ts | 7 | 5 | 1 | 0 | 1 |
| branches/classify.test.ts | 11 | 6 | 0 | 5 | 0 |
| branches/worktree.test.ts | 13 | 6 | 0 | 7 | 0 |
| requests/annotations.test.ts | 34 | 30 | 0 | 2 | 2 |
| requests/attachments.test.ts | 16 | 14 | 0 | 0 | 2 |
| requests/requests.test.ts | 55 | 31 | 0 | 15 | 9 |
| share/share.test.ts | 42 | 39 | 0 | 1 | 2 |
| share/tunnel.test.ts | 9 | 9 | 0 | 0 | 0 |
| **Total** | **498** | **392** | **1** | **72** | **33** |

## Cutover result

Measured at the final head of `cloud/test-prune-l1-5git9i`. Lines are whole files (`wc -l`); declarations are counted as the baseline counted them.

| File | Lines before | after | Removed | Declarations before | after |
| --- | --: | --: | --: | --: | --: |
| branches/branches.test.ts | 285 | 244 | 41 | 7 | 6 |
| branches/classify.test.ts | 115 | 109 | 6 | 11 | 6 |
| branches/worktree.test.ts | 225 | 165 | 60 | 13 | 6 |
| config/config-branch.test.ts | 142 | 70 | 72 | 16 | 5 |
| config/config.test.ts | 159 | 183 | -24 | 19 | 9 |
| config/find-config.test.ts | 69 | 62 | 7 | 6 | 5 |
| config/load-config.test.ts | 90 | 83 | 7 | 7 | 6 |
| config/local-previews.test.ts | 312 | 286 | 26 | 23 | 20 |
| config/renames.test.ts | 89 | 85 | 4 | 10 | 9 |
| frame-policy.test.ts | 118 | 118 | 0 | 7 | 7 |
| json.test.ts | 22 | 0 | 22 | 3 | 0 |
| live.test.ts | 273 | 250 | 23 | 10 | 9 |
| log.test.ts | 165 | 165 | 0 | 7 | 7 |
| proxy.test.ts | 359 | 338 | 21 | 14 | 12 |
| requests/annotations.test.ts | 397 | 357 | 40 | 34 | 30 |
| requests/attachments.test.ts | 461 | 415 | 46 | 16 | 14 |
| requests/requests.test.ts | 818 | 635 | 183 | 55 | 31 |
| server-info.test.ts | 116 | 102 | 14 | 6 | 5 |
| server.test.ts | 3,949 | 3,516 | 433 | 119 | 96 |
| share/share.test.ts | 1,267 | 1,211 | 56 | 42 | 39 |
| share/tunnel.test.ts | 313 | 313 | 0 | 9 | 9 |
| update.test.ts | 1,671 | 1,594 | 77 | 64 | 62 |
| **Total** | **11,415** | **10,301** | **1,114** | **498** | **393** |

`test-helpers.ts` is unchanged (40 lines). Cases run in lane L1 fell from 619 to 532 (the full run passes 1,772 against the baseline's 1,859, with the same four failures).

Production code, counted apart: 16 lines added and 54 deleted, net −38 (`live.ts` 320 → 295, `server.ts` 2,794 → 2,785, `server-info.ts` 79 → 75, `requests.ts` unchanged with two exports dropped). `pnpm api:update` regenerates `api-surface.txt` byte for byte.

By mark: 392 R, 1 F, 72 C, 33 D. The D and C rows by category: duplicate invocations of a contract a keeper makes (most C rows, folded into tables or the keeper), unit replays of a boundary test (`json.test.ts`, `branches.test` 55, `share.test` 116 and 188, `attachments.test` 275 and 364, `server-info.test` 24, `requests.test` 279), strict subsets of a neighbour (`proxy.test` 223 and 287, `find-config.test` 13, `renames.test` 13, `annotations.test` 121 and 196, `local-previews.test` 135 and 172, `requests.test` 399, 414 and 467), fake-layer copies of a real-wire test (`server.test` 3445), duplicate table rows (`update.test` 920) and one test of code nothing in production reads (`live.test` 151).

### Coverage

`pnpm test:coverage` on the final head, run as the baseline describes, is comparable: 4 failed (the same environmental four), 2 skipped, 2 errors, 104 test files (one retired).

| Scope | Lines | Branches | Functions | Statements |
| --- | --- | --- | --- | --- |
| Total | 82.14 → 82.15 | 72.59 → 72.61 | 75.09 → 75.10 | 79.47 → 79.49 |
| server | 91.88 → 91.92 | 81.44 → 81.50 | 87.27 → 87.33 | 88.86 → 88.91 |
| shell | 66.03 → 66.03 | 58.53 → 58.53 | 59.09 → 59.09 | 63.74 → 63.74 |
| cli, mcp, site, scripts | unchanged | unchanged | unchanged | unchanged |

| Server folder | Lines | Branches |
| --- | --- | --- |
| src (root) | 90.96 → 91.07 | 84.07 → 84.26 |
| branches | 95.13 → 95.13 | 84.11 → 85.04 |
| config | 94.14 → 94.14 | 90.09 → 90.09 |
| requests | 94.62 → 94.62 | 83.55 → 83.28 |
| share | 90.61 → 90.61 | 75.40 → 75.40 |
| agents, capture, generation (other lanes) | unchanged | unchanged |

Some of the gains are the timing races `baseline.md` lists, which can only show as gains, and part is the smaller denominator from deleted code; the covered counts below are the check that matters. The two statements in `shell/src/net/live.ts` that only L1 reaches are still covered (`server.test` 3458 stays).

No production file's line coverage fell by more than 5 points. Every file that lost a covered count at the final head:

| File | Lost | Why |
| --- | --- | --- |
| `server/src/live.ts` | lines 106→99, branches 59→52, functions 21→20, statements 120→113 | Deleted code (the viewer count). No remaining code became uncovered. |
| `server/src/server-info.ts` | lines 21→19, branches 24→22, statements 24→23 | Deleted code (the no-expectation branch). No remaining code became uncovered. |
| `server/src/server.ts` | functions 196→195 | The deleted wrapper around `handleUpgrade`. |
| `server/src/requests/requests.ts` | branches 143→142 | The uncut frame's wording (`"the whole page"`). Only the deleted path-only test (780) ran it, and no test asserted that wording before or after, so no contract went with it. Left as is rather than adding an assertion whose expected value would be read off the code. |

The first measurement, before the restorations below, also showed losses in `server.ts` (the retry-without-captures arms), `attachments.ts` (`rehomeCaptures` with nothing to move) and `annotations.ts` (a selector-only anchor's default arms). Those were contracts that lost their only test, not deleted code, so they are restored.

### Restored contracts

- Retrying a request that never got a capture: its prompt comes back unchanged and it has no attachments. The folded `server.test` 1894 was the only test that retried one. Restored in the retry keeper (1945).
- An anchor that is nothing but a selector is kept, with zeroed geometry and no classes. The folded `server.test` 2245 posted one and asserted a 200. Restored in `annotations.test` 56.

### Deliberate breaks

One mutation of the production owner per assertion carried into a keeper, plus the two restorations and the repaired row. Each was applied alone, the keeper run with `pnpm vitest run <file> -t <name>` and the file restored with `git checkout`; the file's hash after matched the commit every time. All 78 went red. "Red at" is the keeper's line on the final head.

The first run of these found one keeper that could not go red: the relative-url row in `config.test.ts` expected `pricing`, which the error's own hint (`"/pricing"`) always contains. The row now uses `about`, and both a message break and a rule break turn it red.

| Break (keeper ← carried from) | Production edit | Red at | Failing assertion |
| --- | --- | --- | --- |
| server 643 ← 736 | server.ts: `if (captured.skipped !== null) queued.captureNote = capture…` → (removed) | server.test.ts:694 | `expect(queued?.captureNote).toBe(NO_BROWSER);` |
| server 688 ← 720 | server.ts: `return safe \|\| "image";` → `return safe \|\| "upload";` | server.test.ts:723 | `expect(bareBody.reference.name).toBe("image");` |
| server 1218 ← 1141 | server.ts: `notes: notes ?? [],` → `notes: [],` | server.test.ts:1151 | `expect(queue.requests).toMatchObject([{ notes: [annotation.id] }]);` |
| server 1218 ← 1259 | server.ts: `sameNotes(entry) &&` → `!sameNotes(entry) &&` | server.test.ts:1152 | `expect((await send()).status).toBe(409);` |
| server 1429 ← 1362 | server.ts: `parsed.mode === "replace" ? "replace" : "variant"` → `parsed.mode === "variant" ? "variant" : "replace"` | server.test.ts:1266 | `expect(forked.mode).toBe("variant");` |
| server 1644 ← 1676 | server.ts: `if (choice.agent !== null) runner?.prepare(choice.agent);` → `runner?.prepare(choice.agent ?? "claude");` | server.test.ts:1507 | `expect(warm).toHaveBeenCalledOnce();` |
| server 1945 ← 1894 | server.ts: `target: request.target,⏎` → (removed) | server.test.ts:1765 | `expect(retried).toMatchObject({` |
| server 1945 restored (retry without captures) | server.ts: `? request.prompt⏎` → `? ""⏎` | server.test.ts:1784 | `expect(bare).toMatchObject({ status: "queued", prompt: "make it colder" });` |
| server 1989 ← 2011 | server.ts: `if (request === undefined) {⏎ return sendJson(res, 404, { o…` → `if (request === undefined) {⏎ return sendJson(res, 400, { o…` | server.test.ts:1814 | `expect(missing.status).toBe(404);` |
| server 2089 ← 2127 | server.ts: `lastSeen = parsed.watching ? Date.now() : null;` → `lastSeen = Date.now();` | server.test.ts:1880 | `expect(await attached()).toBe(false);` |
| server 2198 ← 2438 | server.ts: `devServer: target,⏎ scanPreviews: config?.scanPreviews ?? t…` → `devServer: target,⏎ scanPreviews: true,⏎ previews: previews…` | server.test.ts:1966 | `expect(body.scanPreviews).toBe(false);` |
| server 2198 ← 2600 | server.ts: `project,⏎ devServer: target,⏎ scanPreviews: config?.scanPre…` → `project: "",⏎ devServer: target,⏎ scanPreviews: config?.sca…` | server.test.ts:1964 | `expect(body.project).toBe("/work/app");` |
| server 2198 ← 2626 | server.ts: `previews: previewsForConfig([...currentBoot, ...fresh]),⏎ e…` → `previews: previewsForConfig([...currentBoot, ...fresh]),⏎ e…` | server.test.ts:1968 | `expect(body.warnings).toEqual(["Port 3000 may belong to another project."]);` |
| server 2230 ← 2245 | server.ts: `sendConditionalJson(req, res, { annotations }),` → `sendJson(res, 200, { annotations }),` | server.test.ts:1998 | `expect(etag).toMatch(/^(W\/)?"[^"]*"$/);` |
| server 2230 ← 2264 | server.ts: `sendConditionalJson(req, res, { devServer: target, reachabl…` → `sendJson(res, 200, { devServer: target, reachable, cwd }),` | server.test.ts:1998 | `expect(etag).toMatch(/^(W\/)?"[^"]*"$/);` |
| server 2654 ← 2642 | server.ts: `boot.mtimeMs !== current.mtimeMs)` → `boot.mtimeMs === current.mtimeMs)` | server.test.ts:2346 | `expect(await read()).toEqual(["existing config error"]);` |
| server 2742 ← 2756 | server.ts: `{ path: join(cwd, ANNOTATIONS_PATH), change: "requests" },` → `{ path: join(cwd, ANNOTATIONS_PATH), change: "config" },` | server.test.ts:2430 | `expect(new Set(live.changes)).toEqual(new Set(["requests"]));` |
| server 2892 ← 2900 | server.ts: `` if (path === LEGLAS_PREFIX \|\| path.startsWith(`${LEGLAS_PRE… `` → `if (path === LEGLAS_PREFIX \|\| path === "/" \|\| path.startsWi…` | server.test.ts:2562 | `` expect(await (await fetch(`${server.url}/`)).text()).toBe("<h1>app:/</h1>"); `` |
| server 3694 ← 3732 | server.ts: `address.startsWith("127.")` → `address.startsWith("127.0.0.1")` | server.test.ts:3277 | `expect(isTrustedMutation(request({ host: "localhost:4100" }, peer)), peer).toBe(true);` |
| server 3924 ← 3582 | server.ts: `return isJsonRecord(parsed) ? parsed : null;⏎ } catch {⏎ re…` → `return isJsonRecord(parsed) ? parsed : null;⏎ } catch {⏎ re…` | server.test.ts:3506 | `` expect(await answer.json(), `${route} answering ${nonsense}`).toEqual({ `` |
| annotations 56 restored (selector-only anchor) | requests/annotations.ts: `const rect = isJsonRecord(value["rect"]) ? value["rect"] : …` → `const rect = isJsonRecord(value["rect"]) ? value["rect"] : …` | requests/annotations.test.ts:63 | `expect(anchorFrom({ selector: "main" })).toMatchObject({` |
| update 837 ← 1198 | update.ts: `if (argv[1] !== undefined && options.exists(argv[1]))` → `if (argv[1] !== undefined)` | update.test.ts:845 | `expect(exists).toHaveBeenCalledWith("/invoked/leglas");` |
| config 13 ← 19 (scanPreviews default) | config/config.ts: `const scanPreviews = source["scanPreviews"] ?? true;` → `const scanPreviews = source["scanPreviews"] ?? false;` | config/config.test.ts:13 | `expect(result.config).toMatchObject({` |
| config 13 ← 154 (tags default) | config/config.ts: `tags: Array.isArray(tags) ? tags.filter((tag): tag is strin…` → `tags: Array.isArray(tags) ? tags.filter((tag): tag is strin…` | config/config.test.ts:19 | `expect(result.config?.previews[0]?.tags).toEqual([]);` |
| config 13 ← config-branch 91 (install default) | config/config.ts: `export const DEFAULT_INSTALL_COMMAND = "npm install";` → `export const DEFAULT_INSTALL_COMMAND = "pnpm install";` | config/config.test.ts:13 | `expect(result.config).toMatchObject({` |
| config 64 ← 35 (scanPreviews type) | config/config.ts: `errors.push("scanPreviews must be a boolean.");` → `errors.push("The scan setting must be a boolean.");` | config/config.test.ts:136 | `expect(result.errors.join(" ")).toContain(named);` |
| config 64 ← 45 (recordSets type) | config/config.ts: `errors.push("recordSets must be a boolean.");` → `errors.push("The record setting must be a boolean.");` | config/config.test.ts:136 | `expect(result.errors.join(" ")).toContain(named);` |
| config 64 (title row, original 64) | config/config.ts: `` errors.push(`${at} needs a title; the rail has nothing to s… `` → `` errors.push(`${at} has no name; the rail has nothing to sho… `` | config/config.test.ts:136 | `expect(result.errors.join(" ")).toContain(named);` |
| config 64 ← 71 (url) | config/config.ts: `` errors.push(`${at} needs a url.`); `` → `` errors.push(`${at} needs an address.`); `` | config/config.test.ts:136 | `expect(result.errors.join(" ")).toContain(named);` |
| config 64 ← 77 (duplicate) | config/config.ts: `` errors.push(`${at} repeats the title ${JSON.stringify(title… `` → `` errors.push(`${at} repeats a title; titles must be unique.`… `` | config/config.test.ts:136 | `expect(result.errors.join(" ")).toContain(named);` |
| config 64 ← 99 (relative url) | config/config.ts: `` `${at} has url ${JSON.stringify(url)}; use a root-relative … `` → `` `${at} has a bad url; use a root-relative path `` | config/config.test.ts:136 | `expect(result.errors.join(" ")).toContain(named);` |
| config 64 ← 99 (relative url accepted) | config/config.ts: `return value.startsWith("/") \|\| isValidOrigin(value);` → `return value !== "";` | config/config.test.ts:135 | `expect(result.config).toBeNull();` |
| config 64 ← 113 (devServer) | config/config.ts: `` errors.push(`devServer must be an http(s) URL, received ${J… `` → `` errors.push(`The dev server must be an http(s) URL.`); `` | config/config.test.ts:136 | `expect(result.errors.join(" ")).toContain(named);` |
| config 64 ← 122 (previews array) | config/config.ts: `` errors.push(`previews must be an array, received ${JSON.str… `` → `` errors.push(`The directions must be a list.`); `` | config/config.test.ts:136 | `expect(result.errors.join(" ")).toContain(named);` |
| config 64 ← config-branch 33 (devCommand required) | config/config.ts: `"A preview names a branch, so devCommand is required: Legla…` → `"A preview names a branch, so a dev command is required: Le…` | config/config.test.ts:136 | `expect(result.errors.join(" ")).toContain(named);` |
| config 64 ← config-branch 39 ({port}) | config/config.ts: `` `devCommand must include {port}, so Leglas `` → `` `devCommand must include the port placeholder, so Leglas `` | config/config.test.ts:136 | `expect(result.errors.join(" ")).toContain(named);` |
| config 64 ← config-branch 54 (branch type) | config/config.ts: `if (!isString(branch) \|\| !isSafeBranch(branch)) {` → `if (isString(branch) && !isSafeBranch(branch)) {` | config/config.test.ts:135 | `expect(result.config).toBeNull();` |
| config 64 ← config-branch 63 (branch escape) | config/config.ts: `if (value.split("/").some((segment) => segment === "." \|\| s…` → (removed) | config/config.test.ts:135 | `expect(result.config).toBeNull();` |
| config 64 ← config-branch 72 (branch + absolute) | config/config.ts: `names a branch and an absolute url;` → `names a branch and a full url;` | config/config.test.ts:136 | `expect(result.errors.join(" ")).toContain(named);` |
| config 64 ← config-branch 125 (file + url) | config/config.ts: `` errors.push(`${at} names a file and a url; a file preview's… `` → `` errors.push(`${at} names two sources.`); `` | config/config.test.ts:136 | `expect(result.errors.join(" ")).toContain(named);` |
| config 64 ← config-branch 129 (file + branch) | config/config.ts: `names a branch and a file;` → `names a branch with a file;` | config/config.test.ts:136 | `expect(result.errors.join(" ")).toContain(named);` |
| config 64 ← config-branch 138 (climbing file) | config/config.ts: `return !value.split(/[/\\]/).some((segment) => segment === …` → `return true;` | config/config.test.ts:135 | `expect(result.config).toBeNull();` |
| config 64 ← config-branch 138 (absolute file) | config/config.ts: `if (value === "" \|\| value.startsWith("/") \|\| value.startsWi…` → `if (value === "" \|\| value.startsWith("\\")) return false;` | config/config.test.ts:135 | `expect(result.config).toBeNull();` |
| config-branch 18 ← 27 (ordinary has no branch) | config/config.ts: `if (isString(branch)) preview.branch = branch;` → `preview.branch = isString(branch) ? branch : "main";` | config/config-branch.test.ts:28 | `expect(config.previews[1]?.branch).toBeUndefined();` |
| config-branch 18 ← 48 (devCommand kept) | config/config.ts: `devCommand: isString(devCommand) ? devCommand : undefined,` → `devCommand: undefined,` | config/config-branch.test.ts:26 | `expect(config.devCommand).toBe("pnpm dev --port {port}");` |
| load-config 22 ← 82 (path) | config/load-config.ts: `` errors: result.errors.map((error) => `${label}: ${error}`),… `` → `` errors: result.errors.map((error) => `${label}: ${error}`),… `` | config/load-config.test.ts:37 | `expect(result.path).toBe(join(dir, "leglas.config.ts"));` |
| local-previews 94 ← 84 | config/local-previews.ts: `previews: result.config.previews.map((preview) => ({ ...pre…` → `previews: result.config.previews.map((preview) => ({ ...pre…` | config/local-previews.test.ts:90 | `expect(result.previews).toHaveLength(1);` |
| classify 16 ← 27 (existing file in-app) | branches/classify.ts: `(change) => change.kind === "rewrite" && change.exists && !…` → `(change) => change.exists && !isExplorationFile(change.path…` | branches/classify.test.ts:52 | `expect(classifyDirection({ changes }).level).toBe(level);` |
| classify 16 ← 46 (nested lockfile) | branches/classify.ts: `return MANIFESTS.has(basename(path));` → `return MANIFESTS.has(path);` | branches/classify.test.ts:52 | `expect(classifyDirection({ changes }).level).toBe(level);` |
| classify 16 ← 67 (leglas config) | branches/classify.ts: `if (name.startsWith("leglas.config.")) return false;⏎` → (removed) | branches/classify.test.ts:52 | `expect(classifyDirection({ changes }).level).toBe(level);` |
| classify 16 ← 80 (rewrite of missing path) | branches/classify.ts: `(change) => change.kind === "rewrite" && change.exists && !…` → `(change) => change.kind === "rewrite" && !isExplorationFile…` | branches/classify.test.ts:52 | `expect(classifyDirection({ changes }).level).toBe(level);` |
| classify 16 ← 88 (own exploration files) | branches/classify.ts: `(change) => change.kind === "rewrite" && change.exists && !…` → `(change) => change.kind === "rewrite" && change.exists,` | branches/classify.test.ts:52 | `expect(classifyDirection({ changes }).level).toBe(level);` |
| worktree 23 ← 19 (plain name) | branches/worktree.ts: `.replace(/^-\|-$/g, "");` → `.replace(/^-\|-$/g, "")⏎ .toUpperCase();` | branches/worktree.test.ts:26 | `expect(worktreeSlug(branch)).toBe(slug);` |
| worktree 23 ← 27 (unsafe characters) | branches/worktree.ts: `.replace(/[^A-Za-z0-9._-]+/g, "-")` → `.replace(/[^A-Za-z0-9._ -]+/g, "-")` | branches/worktree.test.ts:26 | `expect(worktreeSlug(branch)).toBe(slug);` |
| worktree 23 ← 31 (runs collapsed) | branches/worktree.ts: `.replace(/[^A-Za-z0-9._-]+/g, "-")` → `.replace(/[^A-Za-z0-9._-]/g, "-")`; `.replace(/-+/g, "-")⏎` → (removed) | branches/worktree.test.ts:26 | `expect(worktreeSlug(branch)).toBe(slug);` |
| worktree 41 ← 37 (one placeholder) | branches/worktree.ts: `return command.split("{port}").join(String(port));` → `return command.split("{port}").join(String(port + 1));` | branches/worktree.test.ts:32 | `expect(substitutePort("serve --port {port} --hmr {port}", 90)).toBe("serve --port 90 --hm…` |
| worktree 84 ← 102 (under .leglas) | branches/worktree.ts: `const path = join(options.cwd, WORKTREES_DIR, worktreeSlug(…` → `const path = join(options.cwd, "worktrees", worktreeSlug(op…` | branches/worktree.test.ts:88 | `expect(realpathSync(worktree.path).startsWith(join(realpathSync(cwd), ".leglas") + sep)).…` |
| worktree 84 ← 148 (stop unregisters) | branches/worktree.ts: `await run("git", ["worktree", "remove", "--force", path], {…` → `await run("git", ["worktree", "list", "--force", path], { c…` | branches/worktree.test.ts:101 | `expect(stdout).not.toContain(WORKTREES_DIR);` |
| worktree 84 ← 199 (IPv4 url) | branches/worktree.ts: `` return { port, url: `http://${forUrl(host)}:${port}`, stop … `` → `` return { port, url: `http://localhost:${port}`, stop }; `` | branches/worktree.test.ts:93 | `expect(worktree.url).toContain("127.0.0.1");` |
| requests 30 ← 34 (param among others) | requests/requests.ts: `for (const pair of query.split("&")) {` → `for (const pair of query.split("&").slice(0, 1)) {` | requests/requests.test.ts:39 | `expect(targetFor(url)).toBe(target);` |
| requests 30 ← 38 (plain path) | requests/requests.ts: `return slot === null ? null :` → `return slot === null ? "" :` | requests/requests.test.ts:39 | `expect(targetFor(url)).toBe(target);` |
| requests 30 ← 42 (absolute url) | requests/requests.ts: `if (!url.startsWith("/")) return null;⏎` → (removed) | requests/requests.test.ts:39 | `expect(targetFor(url)).toBe(target);` |
| requests 30 ← 46 (look-alike) | requests/requests.ts: `if (!rawKey.startsWith("v-")) continue;` → `if (!rawKey.startsWith("v")) continue;` | requests/requests.test.ts:39 | `expect(targetFor(url)).toBe(target);` |
| requests 30 ← 50 (climbing value) | requests/requests.ts: `if (!SAFE_SEGMENT.test(surface) \|\| !SAFE_SEGMENT.test(optio…` → `if (!SAFE_SEGMENT.test(surface)) return null;` | requests/requests.test.ts:39 | `expect(targetFor(url)).toBe(target);` |
| requests 64 ← 79 (source line) | requests/requests.ts: `` `Its source is ${target}.` `` → `` `The source is ${target}.` `` | requests/requests.test.ts:67 | `expect(prompt).toContain("Its source is .leglas/variants/hero/poster.tsx.");` |
| requests 64 ← 91 (registration flags) | requests/requests.ts: `` ` ${add} --title "<name>" --url "/?v-${slot.surface}=<key>"… `` → `` ` ${add} --title "<name>" --url "/?v-${slot.surface}=<key>"… `` | requests/requests.test.ts:72 | `expect(prompt).toContain('--based-on "Poster"');` |
| requests 64 ← 114 (discovery done) | requests/requests.ts: `and do not start or restart the app or Leglas.` → `and do not restart Leglas.` | requests/requests.test.ts:81 | `expect(prompt).toContain("do not start or restart the app or Leglas");` |
| requests 64 ← 290 (never edit the parent) | requests/requests.ts: `` `it is: it is the thing the new one will be compared agains… `` → `` `it is: it is the thing the new one will be compared agains… `` | requests/requests.test.ts:90 | `expect(prompt).not.toContain("Make the change in that file");` |
| requests 64 ← 696 (register before look) | requests/requests.ts: `: "Register it before you look: the look is at the register…` → `: "Look at it, then register it."` | requests/requests.test.ts:85 | `expect(prompt).toContain("Register it before you look");` |
| requests 347 ← 324 (file in prompt) | requests/requests.ts: `` : `It lives at ${target}.`; `` → `` : `It is a scaffold file.`; `` | requests/requests.test.ts:290 | `expect(known).toContain(".leglas/variants/hero/aurora.tsx");` |
| requests 347 ← 370 (change only) | requests/requests.ts: `` `In this project, change only the "${preview.title}" design… `` → `` `In this project, change the "${preview.title}" design dire… `` | requests/requests.test.ts:291 | `expect(known).toContain('change only the "Aurora" design direction');` |
| requests 347 ← 377 (no re-register) | requests/requests.ts: `` `re-registering.`⏎ `` → `` `re-registering with leglas add.`⏎ `` | requests/requests.test.ts:296 | `expect(known).not.toContain("leglas add");` |
| requests 347 ← 383 (trimmed intent) | requests/requests.ts: `const cleaned = intent.trim();` → `const cleaned = intent;` | requests/requests.test.ts:293 | `expect(known).toContain("What to change: warmer");` |
| requests 673 ← 659 (quote in title) | requests/requests.ts: `` value.replace(/[\\"$`]/g, `` → `` value.replace(/[\\$`]/g, `` | requests/requests.test.ts:545 | `expect(prompt).toContain(` |
| annotations 245 ← 140 (trimmed rewording) | requests/annotations.ts: `const words = text(note, NOTE_CAP);` → `const words = note.slice(0, NOTE_CAP);` | requests/annotations.test.ts:211 | `expect(revised).toEqual({ ...middle, id: revised?.id, note: "b again" });` |
| annotations 245 ← 180 (neighbours untouched) | requests/annotations.ts: `annotations.map((entry) => (entry.id === id ? revised : ent…` → `annotations.map((entry) => (entry.id === id ? revised : { .…` | requests/annotations.test.ts:217 | `expect([read[0], read[2]]).toEqual([first, last]);` |
| share 343 ← 116 (no url without a tunnel) | share/share.ts: `` url: origin === null ? null : `${origin}${entryPath}`, `` → `` url: origin === null ? "" : `${origin}${entryPath}`, `` | share/share.test.ts:296 | `expect(share.grants[0]).toMatchObject({ name: "", url: null, viewers: 0 });` |
| share 343 ← 116 (no viewers yet) | share/share.ts: `viewers: grant.viewers,` → `viewers: grant.viewers + 1,` | share/share.test.ts:296 | `expect(share.grants[0]).toMatchObject({ name: "", url: null, viewers: 0 });` |

## Follow-ups

- `server.test.ts` repeats its setup: 48 blocks post JSON in five lines each and 29 boot a server with a fresh directory in about seven. Two helpers would remove roughly 300 lines without touching an assertion. Not done here: it deletes no test and would make the preservation review of the largest file harder.
- The uncut frame's wording in `requests.ts` has no test, before or after this lane.
- `TunnelDeps.now` in `share/tunnel.ts` is passed by nothing, and `withoutShareCookie` in `proxy.ts` is exported but used only inside its file. Neither is unlocked by this lane's deletions, so both are left.

## For the preservation review

Look first at:

1. `server.test.ts`, where most assertions moved (19 consolidations). The break table shows each carried assertion going red.
2. `config.test.ts`'s rejection table, which took rows from two files.
3. D marks whose keeper lives in another file: `branches.test` 55 (`server.test` 2278), `attachments.test` 275 and 364 (`server.test` 643 and 1945), `share.test` 188 (`server.test` 2956), `server.test` 3167 (`share.test` 257) and 3445 (`server.test` 3458), `server-info.test` 24 (`server.test` 2163) and `json.test.ts` (`server.test` 3924 and the file readers).
4. The seam removals in `live.ts`, `server-info.ts`, `server.ts` and `requests.ts`.

## Ledger

### packages/server/src/server.test.ts

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 421 | allows the machine's own browser under the LAN host %s | R | LAN-host allowlist for mutations (isAllowedMutationHost): .local, 10/8, 172.16/12, 192.168/16, [::1]. Fails if a private range or the bracketed IPv6 host stops being accepted. |
| 435 | refuses a public hostname even when Origin matches it | R | Security: a public Host is refused even when Origin matches it (DNS rebinding). Only boundary proof of the public-host branch. |
| 442 | still refuses a mismatched Origin on an allowed LAN hostname | R | Security: Origin must equal Host on an allowed LAN host. Fails if the Origin/Host comparison is dropped. |
| 454 | an intent that is not text is refused, not left hanging | R | A non-string intent is a 400 and nothing is queued (requestIntent returns null). Catches the route hanging or coercing 42 into a request. |
| 474 | says whether an absolute-URL direction will let the interface frame it | R | Boundary keeper for checkFraming: an absolute-URL direction reports the XFO refusal, a proxied one is framable, unknown title 404, cross-site Sec-Fetch-Site 403 (SSRF guard). |
| 510 | POST then GET exposes queued request state without collecting it | R | GET /api/requests does not collect (status stays queued, second read identical) and the default mode is variant. Fails if GET started collecting or the default flipped to replace. |
| 542 | uploads a PNG reference with its measured dimensions | R | PNG reference upload: measured 2x3, byte count, id shape, file written byte for byte. Keeper for upload + sniffImage at the route (one of #117's five keeps, PNG size reading). |
| 579 | refuses a non-image reference without writing it | R | Non-image upload is 415 with the user-facing sentence and nothing is written. |
| 597 | refuses a declared reference over 10MB before reading it | R | A declared Content-Length over 10MB is refused before any body is sent (null chunks would hang if the route waited). Resource limit. |
| 610 | stops a streamed reference as soon as it passes 10MB | R | A streamed body is cut off once it passes 10MB, with no declared length. Different branch from 597. |
| 628 | takes a reference of exactly the interface's cap, and refuses one byte more | R | Cross-package contract: the server cap equals the shell's REFERENCE_BYTES_CAP (#118). Fails when the two numbers drift apart. |
| 643 | moves an uploaded reference into the request capture directory | R | Keeper for references moving into a request (absorbs 736): upload through the route, then request; moved file, measured size, source gone. Extended with 736's compare, prompt and captureNote assertions. |
| 688 | sanitises the uploaded reference display name | R | Display-name sanitising: control, non-ASCII and slash characters dropped, 80 char cap. Absorbs 720's fallback to "image". |
| 706 | refuses an empty reference upload | R | Empty upload is a 400 with its sentence and nothing written. |
| 720 | falls back to image when the reference display name has no safe characters | C | Folded into 688 as a second upload in the same server: a name with no safe characters falls back to "image". Same referenceName branch, same route. |
| 736 | a request moves attached references and records why a browser capture was skipped | C | Folded into 643: its compare, NO_BROWSER captureNote, prompt line and body/queue equality assertions move there; the reference now arrives through the upload route instead of a hand-written file. |
| 783 | rejects malformed reference ids before moving or queueing anything | R | Security: reference ids that are not upload ids (../secret) are refused before anything moves or queues. |
| 802 | captures a direction through the shared browser pool | R | Capture route through the pool: slugged show file name, sizes, viewport, errors, hydration, bytes on disk. |
| 839 | captures one note crop and names it in the show file | R | A capture for one note writes the crop under a name carrying the note id, and reports the crop's size, not the frame's. |
| 897 | capture gives a bounded timeout when the page never loads | R | captureDeadlineMs bounds a capture that never loads: 504 with its sentence. |
| 923 | a page that rendered but never fired load is still captured | R | A page that rendered but never fired load is still captured (LOAD_SHARE of the deadline). Only route proof of the load share. |
| 958 | an upload lets go of references pasted an hour ago and never sent | R | An upload prunes references older than an hour. #117 deleted the direct pruneReferences test because this and boot pruning cover it; keep. |
| 978 | capture reports unknown directions and unavailable browsers | R | Capture: unknown direction 404, no browser 503 with the pool's reason. |
| 1000 | keeps a note, hands it back, and forgets it on request | R | Note route lifecycle: add, list, delete through the API. |
| 1048 | rewords a note that is already there | R | Reword route: new id, list shows new words, missing id 404, wordless body refused and words survive. Trimmed: its non-object body loop duplicates 3924, which posts the same bodies to /api/annotations/update. |
| 1141 | the queue says which notes each change answers | C | Folded into 1218: the queue's notes [id] assertion moves there. Its reword-reissues-id half duplicates 1048. |
| 1199 | refuses a note with nothing to point at | R | A note with no anchor is a 400 at the route (anchorFrom null mapped to 400). |
| 1218 | a change with notes and no words is still a request | R | Keeper for notes-only requests (absorbs 1141, 1259): empty intent with a pin is a 200 whose prompt carries the note, the queue records the note ids and a second send is a 409. |
| 1259 | refuses the same notes sent twice while the first is still waiting | C | Folded into 1218: the same notes sent twice while waiting is a 409. Same setup (one pin, empty intent). |
| 1297 | nothing typed and nothing pinned is not a request | R | Nothing typed and nothing pinned is a 400, not an empty request. |
| 1315 | refuses a second copy of a change that is still waiting | R | Duplicate guard by words: trimmed repeat is a 409 with its sentence; other words or other direction still queue. |
| 1362 | a change forks the direction unless the caller asks to replace it | C | Folded into 1429: the variant default and replace prompt choice are asserted on the two sends 1429 already makes. Its own last assertion (two requests queued) is implied by 1429's 200s. |
| 1404 | refuses a mode it does not recognise rather than guessing | R | Unknown mode is refused with 400 and nothing queued, not defaulted. |
| 1429 | the same words in the other mode are not a duplicate | R | Keeper for request modes (absorbs 1362): variant by default with the fork prompt, replace on request with the in-place prompt, same words in the other mode not a duplicate, a true repeat 409. |
| 1453 | a verdict inherited from an earlier process is still actionable | R | A failed verdict written by an earlier process reads as failed with its code and can be dismissed. Keeper for dismissing an ended request (2024). |
| 1505 | reports an idle agent before anything has run | R | Idle agent block shape the shell reads before any run. |
| 1527 | reports available agents and round-trips the saved choice | R | Agents list, custom and known choice round trip, login cache (three reads one probe), refresh=1 re-probes. |
| 1615 | warms Claude as soon as it is selected | R | Selecting Claude warms its session at once. |
| 1644 | the composer can ask for the saved agent to be warmed | R | Keeper for /api/agents/warm (absorbs 1676): nothing warms at boot; with nothing chosen the call is a harmless 200; with a saved choice it warms once. |
| 1676 | warming with nothing chosen is a harmless no-op | C | Folded into 1644: warm with no saved choice is a 200 and warms nothing, asserted before the choice is saved. |
| 1684 | serves stale agent state while routine authentication refreshes in the background | R | Stale agent state is served while a background refresh runs; the routine read never waits on detection. |
| 1763 | refuses an invalid agent choice: %j | R | Seven invalid agent choices are 400 with an error (unknown agent, custom without run, bad template, effort on custom, non-string run, unknown effort, effort on an agent without one). |
| 1784 | refuses cross-origin agent configuration before it reaches disk | R | Security: cross-origin agent configuration is refused before watch.json is written (the route that decides what runs). |
| 1801 | refuses a safelisted content type for agent configuration | R | Security: a CORS-safelisted content type (text/plain) cannot configure the agent. |
| 1815 | reports a running request and cancels it through the polled API | R | Embedded runner wiring: running status and agent block while a real child runs, mismatched id is not a stop, cancel ends it as cancelled with its sentence, idle cancel is false. |
| 1894 | replaces a failed request with a fresh queued copy | C | Folded into 1945: the retried copy's queued status, title, url, intent, target and prompt move there, and its capture-less retry (the only one) is restored there. The real failing child it waited on adds nothing the queue's failed status does not; runner failure marking is runner.test's (L2). |
| 1945 | a retry keeps the failed request's captures under its fresh id | R | Keeper for retry (absorbs 1894): fresh queued copy keeps every field, captures move under the new id and the prompt's paths follow; a request with no captures comes back as it was. |
| 1989 | refuses to retry a request that has not failed | R | Retry of a request that has not ended is a 400. Absorbs 2011's missing-id 404. |
| 2011 | returns 404 when retry names no request | C | Folded into 1989: retry naming no request is a 404, asserted on the same server. |
| 2024 | dismisses a failed request out of the queue | D | Dismissing a failed request is 1453's assertion (failed verdict in the queue, dismiss 200, queue empty). The real failing child only produces that same file state; runner failure marking is L2's runner.test. |
| 2066 | refuses to dismiss a request that has not failed | R | Security of the queue: a live request cannot be dismissed (only ended ones). |
| 2089 | an agent counts as attached while its heartbeat is fresh, and not once it stops | R | Keeper for the watch heartbeat (absorbs 2127): attached while fresh, still attached at 5s, detached at 7s and an explicit watching:false detaches at once. |
| 2127 | a watcher shutting down detaches immediately rather than aging out | C | Folded into 2089: beat(false) detaches immediately, asserted after a fresh beat on the faked clock. |
| 2151 | refuses a heartbeat that says nothing about watching | R | A heartbeat without the watching boolean is a 400. |
| 2163 | reports the port and url it actually bound | R | Bound port and url, server.json written with startedAt and removed on close, pool closed once. Keeper for server-info's round trip (server-info.test 24). |
| 2187 | takes the next free port when the requested one is busy | R | Takes the next free port when the requested one is busy. |
| 2198 | serves the resolved previews so the rail can render them | R | Keeper for the config payload (absorbs 2438, 2600, 2626): previews with note and tags, project id, scanPreviews false, warnings beside empty errors. |
| 2217 | returns conditional config responses and changes the etag with the body | R | Conditional GET mechanism on /api/config: quoted etag, 304 with empty body, etag and body change with the content, new etag 304. |
| 2230 | returns conditional request responses and changes the etag with the body | R | Keeper for the other polled reads (absorbs 2245, 2264): requests, annotations and health each answer with an etag and a 304 for it. The etag-follows-body mechanism is 2217's. |
| 2245 | returns conditional annotation responses and changes the etag with the body | C | Folded into 2230's row for /api/annotations. The change-the-body half repeats 2217's mechanism through the same sendConditionalJson. Its selector-only anchor was the only test of that shape and moved to annotations.test 56. |
| 2264 | returns conditional health responses and changes the etag with the body | C | Folded into 2230's row for /api/health. The flip-the-origin half repeats 2217's mechanism; health flips are 2729 and 2836. |
| 2278 | starts a branch once in the background and withholds its url until it is ready | R | Branch start joins concurrent starts (one checkout), withholds url until ready, nudges config only. Keeper for branches.test 55. |
| 2366 | validates branch start titles and the command needed to boot them | R | Branch start validation: unknown 404, not a branch 400, no devCommand 400 naming both. |
| 2397 | closing the server stops a branch worktree that reached ready | R | Server close stops a branch worktree that reached ready (close wiring). |
| 2438 | tells the shell when unopened preview scanning is disabled | C | Folded into 2198: scanPreviews false reaches the payload. |
| 2453 | a url preview registered after boot joins the config live | R | A url preview added after boot joins /api/config live; a file preview does not. |
| 2487 | keeps booted local previews in config when the local registry cannot be read | R | Booted local previews stay when the registry becomes unreadable, with no error. |
| 2514 | accepts requests for booted local previews when the local registry becomes invalid | R | Requests for booted local previews still work when the registry turns invalid (livePreviews fallback). |
| 2540 | permanently deletes local previews through the interface API, noted in the set that built them | R | Permanent delete drops a local preview from the live payload and notes the removal in the set's events. |
| 2585 | refuses to rewrite shared config previews through permanent delete | R | Delete refuses a shared config preview (only machine-local ones). |
| 2600 | identifies the project, so saved layout survives a port change | C | Folded into 2198: the project id reaches the payload. |
| 2611 | serves config errors instead of dying, so the shell can show them | R | Config errors are served instead of dying, with no previews. |
| 2626 | serves startup warnings without treating the config as invalid | C | Folded into 2198: warnings are served beside empty errors. |
| 2642 | does not report stale config when the boot config is untouched | C | Folded into 2654 as its first read: an untouched boot config reports only the existing error, no staleness notice. |
| 2654 | reports when the boot config changes, alongside existing config errors | R | Keeper for the changed-config notice (absorbs 2642): no notice while untouched, then the notice after the existing error once the file changes. |
| 2679 | reports when a config appears after boot | R | Notice when a config appears after boot. |
| 2693 | reports when the boot config is removed | R | Notice when the boot config is removed. |
| 2711 | reports the dev server as reachable when it is up on %s | R | Health reachable on 127.0.0.1 and on ::1 (Vite on macOS). The ::1 row is a baseline failure here only: no IPv6 in this VM's kernel (EAFNOSUPPORT); passes on CI. |
| 2729 | reports the dev server as unreachable when it is down | R | Health unreachable when nothing listens. |
| 2742 | a write to requests.json nudges the requests channel | R | Keeper as a table (absorbs 2756): a write to requests.json or annotations.json nudges only the requests channel. |
| 2756 | routes annotation changes through requests, never a fourth kind | C | Folded into 2742 as its annotations.json row. |
| 2770 | nudges config when the late-created previews registry changes | R | The previews registry nudges config even when .leglas is created after boot. |
| 2781 | nudges config when the resolved config file changes | R | The resolved config file nudges config. |
| 2792 | passes runner state changes to the requests channel | R | Runner state changes reach the requests channel. |
| 2836 | nudges health once when reachability flips, not on steady probes | R | Health nudges once on a flip, never on steady probes. |
| 2863 | does not probe health with no live listeners | R | No health probing without listeners; probing starts with one; close closes the hub. |
| 2892 | proxies any route the tool does not own | R | Proxies routes the tool does not own, root included (absorbs 2900). |
| 2900 | proxies the app root, since previews are usually relative to it | C | Folded into 2892: the app root proxies too. |
| 2906 | serves the shell when a built shell directory is given | R | Serves the built shell at /leglas. |
| 2916 | returns a 404 for an unknown shell path | R | Unknown shell path is a plain 404. |
| 2927 | returns a JSON 404 for an unknown API path (shell: %s) | R | Unknown API path is a JSON 404 with or without a built shell. |
| 2943 | explains itself at /leglas when no shell has been built yet | R | Without a built shell /leglas is Leglas's own placeholder, not the app. |
| 2956 | serves a read-only share and keeps its lifecycle on the primary listener | R | Read-only share end to end: second listener, entry cookie, viewer config scrubbed of the sharer's paths, mutations and APIs refused, health verdict only, mounts limited to shared directions, dotfiles, dev-control routes, service workers and app sockets refused, update, stop, share nudges. Keeper for share.test 116 and 188. |
| 3167 | validates share titles and refuses a second active share | D | Branch and unknown titles are share.test 257's exact assertions (both error sentences, nothing bound); a second active share 409 with its sentence is 2956's. |
| 3220 | counts only authenticated live sockets on the share listener | R | Viewer count on the share listener counts only cookie-authenticated live sockets and drops on disconnect. |
| 3284 | a viewer arriving settles a tunnel the probe has not seen answer | R | A viewer arriving through the tunnel (forwarded headers) settles a tunnel the probe has not seen; the sharer's own socket does not. |
| 3342 | closing the primary server stops its tunnel and share listener first | R | Closing the server stops the tunnel (SIGTERM) and the share listener. |
| 3369 | closes cleanly while a live-reload socket is still open | R | Regression: close resolves with a live-reload socket still open (upgraded sockets tracked). |
| 3445 | each service transition nudges the live update channel | D | Its fake hub only records nudge("update"); 3458 drives the same onChange through the real hub to the shell's listener (#105: the fake-hub halves passed while the wire was broken). |
| 3458 | an announced update reaches the interface's update listener | R | Cross-package: an update nudge reaches the shell's real live client (#105). Only test reaching 2 statements in shell/src/net/live.ts. |
| 3475 | close waits for the installer before releasing the server's resources | R | Close waits for the installer before releasing the hub; a second close returns the same promise. |
| 3495 | skip rejects content-type %s before reading its valid JSON | R | Security: skip refuses a missing or safelisted content type before reading valid JSON. |
| 3513 | GET returns an uncached status and wires the actual port and runner | R | GET /api/update is no-store and wires setPort and onBusy. |
| 3525 | check forces a refresh and ignores its body | R | check forces a refresh and ignores its body. |
| 3541 | skip accepts the version and returns the changed status | R | skip passes the version and returns the changed status. |
| 3557 | install answers as soon as installing starts | R | install answers as soon as installing starts. |
| 3570 | %s returns 404 when updates were not provided | R | All four update routes answer 404 without a service. |
| 3582 | skip rejects a non-object body: %s | C | Folded into 3924: its malformed "{" row joins the scan's bodies, which already send null, [] and 42 to /api/update/skip and every other JSON route; the scan's 400 implies skip was never called. |
| 3597 | skip needs a nonempty version: %j | R | skip needs a nonempty string version (four shapes). |
| 3615 | a refused skip maps to 400 and a refused install maps to 409 | R | Service refusals map to 400 for skip and 409 for install with the service's sentence. |
| 3637 | %s stays behind the cross-origin guard | R | Security: the three update POSTs (install runs npm) sit behind the cross-origin guard. Ordering contract: a route moved above the guard fails here. |
| 3664 | a cross-origin %s to the API is refused before any route sees it | R | Security: any non-GET/HEAD cross-origin method is refused before routing; own origin and no origin reach the routes; GET is a read from anywhere (#119). |
| 3694 | an origin-less request is trusted only from the machine itself | R | Keeper for peer-based trust (absorbs 3732): loopback peers (127.0.0.1, 127.x, ::1, mapped) are trusted, LAN peers and a missing address are not. No boundary test can produce a non-loopback peer. |
| 3703 | a forged Origin does not make a network peer a browser | R | Security: a forged matching Origin from a LAN peer is still refused (socket decides). |
| 3719 | cross-origin and public hosts stay refused regardless of peer | D | Both rows run with a loopback peer, which the boundary reproduces: cross-origin with a local Host is 1784 and 3664's refusal, a public Host with matching Origin is 435. |
| 3732 | loopback recognition covers the shapes Node reports | C | Folded into 3694 as isTrustedMutation rows for 127.0.0.53, ::1 and an undefined peer; isLoopbackAddress then loses its only outside caller and is no longer exported. |
| 3743 | a direction added from a file after boot is not captured, matching the rail | R | A file direction registered after boot is not captured (no mount), a url one is, matching the rail. |
| 3786 | the same words against a different comparison or picture are not a duplicate | R | Duplicate identity includes the compared direction and the reference ids; a pruned reference is a 410 with its sentence and nothing is queued for it. |
| 3924 | is refused by every route that takes one, and none of them fall over | R | Source inspection kept on purpose (#117): finds every POST route in server.ts and posts non-object JSON to each; fails when a new route reads a body without the guard. Cheapest independent guard; survives identifier renames. Gains the malformed "{" row from 3582. |

### packages/server/src/json.test.ts

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 6 | refuses %j as an object container | D | Private predicate replayed at the boundary: server.test 3924 posts null, a string, [], 7 and true to every JSON route and needs isJsonRecord to refuse each; readers (readRequests, readAnnotations, readRenames) refuse the same shapes. |
| 13 | does not coerce primitive values | D | isString/isNumber/isBoolean are one-line typeof checks every reader runs; a coercing predicate fails server.test 454 (intent 42), 2151 (watching missing), 3597 (version 1) and the update.test state rows. |
| 19 | leaves malformed JSON to the caller's error handling | D | parseJson throwing on bad JSON is what every reader's catch handles: local-previews 103 ("not valid JSON"), renames 323, annotations 272, update.test 702 and server.test 3924's "{" row. |

### packages/server/src/frame-policy.test.ts

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 13 | a page that says nothing about frames may be framed | R | HTML-standard framing rule: no XFO and a CSP without frame-ancestors frame fine. |
| 20 | X-Frame-Options refuses the way browsers read it | R | XFO as browsers read it: DENY, SAMEORIGIN against the shell and against itself, ignored ALLOW-FROM, conflicting values. Spec table; only the DENY row is reached at the route (server.test 474). |
| 39 | a frame-ancestors policy decides on its own, and X-Frame-Options is ignored | R | frame-ancestors decides alone and overrides XFO; 'self' and an empty list refuse. |
| 52 | host sources match the shell by scheme, host and port | R | Host-source matching by scheme, host, port and the scheme borrow, bracketed IPv6 shell. |
| 79 | every enforced policy has to admit the shell, and report-only ones are not enforced | R | Every enforced policy must admit; report-only is not enforced. |
| 92 | reads the answer at the end of any redirects | R | Reads the verdict at the end of redirects (response.url). Needs the fetcher seam: reproducing a redirect to the embedder's own origin at the route is not deterministic (localhost resolution), so this stays the owner. |
| 109 | a page that cannot be reached is not called a refusal | R | An unreachable page is unknown (null), never a refusal. |

### packages/server/src/live.test.ts

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 70 | computes the documented accept value and refuses a missing key | R | RFC 6455 accept value for the spec's sample key, and a missing key is refused with the socket destroyed. |
| 84 | sends the exact %s nudge to every listener | R | Exact text frame for a nudge to every listener (config and update rows). |
| 99 | encodes a $length byte payload with the right header | R | Frame length encodings at 125, 126 and 65536 bytes (protocol). |
| 115 | answers a ping with a pong and honours a client close | R | Ping gets a pong with its payload; a client close is answered and the listener dropped. |
| 129 | reaps an errored socket and later nudges are harmless | R | An errored socket is reaped and later nudges do not throw. |
| 139 | close sends close frames and empties the hub | R | close sends close frames and empties the hub. |
| 151 | counts only viewer-tagged listeners and reports every change | D | Tests a count nothing in production reads: the hub's viewers getter and onViewers lost their last caller in bd5bc2e (share counts viewers per link itself, server.test 3220). Deleting it unlocks removing viewers, onViewers, the unused now option, Listener.viewer and the upgrade option. |
| 203 | two changes inside the window are one nudge; outside it, two | R | Coalescing on a driven clock: two in the window are one nudge, apart are two (#117: coalescing is proven here, not against a watcher). |
| 227 | each kind waits on its own timer | R | Each kind has its own timer, so a config burst cannot delay requests. |
| 253 | closing drops what is pending and refuses anything after | R | Closed coalescer drops pending work and refuses new work. |

### packages/server/src/log.test.ts

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 29 | names the winner, where it went, and how many it beat | R | Decision-log heading, winner, destination and count. Only in-process proof: the cli reaches composeEntry through its bundle, which coverage cannot see. |
| 46 | carries the words that were typed, not a summary of them | R | Typed words are carried verbatim. |
| 63 | invents nothing for a direction with no note | R | Invents nothing: exactly three lines for a bare direction (#117 line count). |
| 82 | takes a direction's last frame, so a changed one shows its later self | R | The last frame wins and is copied beside the entry. |
| 101 | records the pins left on a direction | R | Pins are recorded under the direction. |
| 130 | keeps what failed, because a rejected change is part of the record | R | Failed changes listed once at the foot with why, never as asked for. |
| 153 | a title that is only punctuation still produces a usable filename | R | Punctuation-only titles still give a usable slug. |

### packages/server/src/proxy.test.ts

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 174 | reaches a target that is an IPv6 literal | R | Regression: an IPv6-literal target is dialled without brackets. Baseline failure here only (no IPv6 in this VM); passes on CI. |
| 202 | a branch proxy exposes activity and owns its loopback origin | R | Branch proxy reports activity and open connections and owns a loopback origin. |
| 223 | passes a response body through unchanged | D | Body passthrough is server.test 2892's exact-body assertion through the real server, and every echo test here reads an upstream body. |
| 229 | preserves the upstream status code | R | Upstream status passes through (418). |
| 235 | keeps the share cookie from the app, and leaves the app's own cookies alone | R | Security: the share cookie never reaches the app; the app's own cookies do. |
| 249 | rewrites Host to the upstream, so frameworks emit correct absolute URLs | R | Host rewritten to the upstream authority. |
| 255 | forwards the method and request body | R | Method and body forwarded. |
| 264 | rewrites an absolute redirect so the browser stays inside the proxy | R | Absolute redirects to the upstream are rewritten to the proxy. |
| 272 | leaves a relative redirect alone, since it already resolves correctly | R | Relative redirects are left alone. |
| 280 | passes Set-Cookie through with its attributes intact | R | Set-Cookie passes with its attributes. |
| 287 | forwards request cookies upstream, so real auth survives the hop | D | 235 already proves app cookies reach the upstream (the origin echoes session=abc; theme=dark). |
| 295 | forwards the websocket upgrade, which is what keeps live reload alive | R | Websocket upgrade forwarded (live reload). |
| 325 | lets go of the upstream request when the browser gives up | R | An abandoned browser request releases its upstream request. |
| 351 | reports a dead upstream as 502 rather than hanging or crashing | R | Dead upstream is a 502 with a sentence naming the dev server. |

### packages/server/src/server-info.test.ts

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 24 | round-trips the running endpoint and records when it started | D | server.test 2163 proves the written record (port, url, pid, startedAt) and its removal on close; 46 and 78 read it back with readServerInfo. Its only unique path was removeServerInfo with no expectation, which no production caller uses; that branch goes. |
| 38 | returns null for missing or malformed state | R | Missing or malformed record reads as null. |
| 46 | leaves nothing half-written for a reader that arrives mid-write | R | Atomic write: a concurrent reader never sees half a record, no temporary left behind (#117). |
| 78 | an older server closing leaves the newer record alone | R | Two servers on one project: an older close leaves the newer record. |
| 96 | a link standing in for the record is left as it is | R | Security: a symlink standing in for the record is not followed. |
| 107 | a link standing in for .leglas itself is left as it is | R | Security: a symlinked .leglas is not written through. |

### packages/server/src/update.test.ts

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 151 | classifies %s from %s | R | detectInstall platform table (20 rows): npx caches, project lockfiles, pnpm store, globals, Windows paths, checkouts. |
| 295 | compares a symlinked working directory with the real package directory | R | A symlinked cwd matches the real package directory. |
| 313 | recognizes %s before project or environment detection | R | Runner caches win before project or environment detection (4 rows). |
| 345 | uses the %s user agent only for anonymous runner caches | R | The user agent decides only for anonymous runner caches (3 rows). |
| 393 | recognizes a pnpm dlx entry resolved into the links store | R | pnpm dlx resolved into the links store is npx. |
| 406 | does not infer a runner from an incomplete user agent | R | An incomplete user agent infers nothing. |
| 418 | finds the nearest Berry project for %s | R | Berry entries find the nearest Berry project, else source (3 rows). |
| 455 | runs in the workspace member with the lockfile %s above it | R | Workspace member runs with the lockfile above it (5 rows). |
| 483 | a different project dependency does not claim the global entry | R | Another project's dependency does not claim a global entry. |
| 495 | uses the closest lockfile instead of an outer workspace's manager | R | The closest lockfile wins over an outer workspace. |
| 516 | compares %s with %s | R | compareVersions semver table (14 rows, symmetric). |
| 538 | reads a fresh cache once and makes no network request | R | A fresh cache is read once at start and the check makes no request. |
| 552 | does not reuse a cache aged %s milliseconds | R | Cache age boundaries (a day, a day plus one, the future). |
| 559 | force asks both sources even with a fresh cache and remembers the site's title | R | force asks both sources, remembers the title, writes state atomically. |
| 584 | offline | R | Seven registry failures keep the cache and say why in the user's words. |
| 615 | uses the configured abort deadline | R | The configured deadline ends both requests (#117 review asked for the releases case). |
| 648 | keeps the npm result when the site has %s | R | A broken changelog site costs only the title (4 rows). |
| 670 | joins concurrent checks while asking the registry and the site in parallel | R | Concurrent checks join; registry and site asked in parallel. |
| 689 | clears an old skip only when a newer release appears | R | A skip clears only when a newer release appears. |
| 702 | treats malformed state as empty: %s | R | Malformed state reads as empty (4 rows). |
| 718 | creates missing state directories and reads a saved skip on the next start | R | Missing state directories are created; a saved skip survives a restart. |
| 729 | a refused state write does not fail a check or a skip | R | A refused state write fails neither check nor skip. |
| 738 | does not write through a state-file symlink | R | Security: state is never written through a symlink. |
| 748 | a caller cannot change the service by editing a returned snapshot | R | status() returns a copy callers cannot use to change the service. |
| 763 | only the newest known version can be skipped | R | Only the newest known version can be skipped. |
| 771 | prints an aligned notice for %s | R | Terminal notice wording per install kind (4 rows, user-facing bytes). |
| 791 | omits the colon when no title was found | R | No colon without a title. |
| 802 | has no notice when running %s | R | No notice when current or newer (2 rows). |
| 824 | pins npx and replaces both forms of the old port | R | npx restart pins the version and replaces both port forms without mutating argv. |
| 837 | uses the invoked global bin with the same runtime | R | Keeper for the invoked global bin (absorbs 1198): a surviving argv[1] runs through execPath on any platform, checked through exists(argv[1]). |
| 844 | uses the project's shim on either platform | R | Project shim on POSIX. Trimmed: its Windows half is a subset of 1229 (same .cmd join and shell line, plus quoting). |
| 871 | rejects every unavailable update before starting a process | R | Every unavailable update is refused before any process starts. |
| 892 | npx answers installing before handing off the pinned version on the bound port | R | npx answers installing first, then hands off the pinned version on the bound port; logs once. |
| 920 | pins the install for %s with %s | R, 6 rows D | Rows kept (R): global npm, project npm with cwd, yarn classic (classic is read back off the displayed command), yarn berry. Rows deleted (D): global pnpm, global yarn, global bun, project pnpm, project bun, berry cache; each only replays a COMMANDS entry that 151 asserts through the same commandParts, and berry cache resolves to the yarn berry row's install (418 owns its detection). |
| 1025 | a concurrent check cannot hide the install or change its pinned version | R | A concurrent check cannot hide the install or change its pinned version. |
| 1041 | uses a shell for Windows managers | R | Windows managers run through a shell, not detached. |
| 1056 | a failed npm install names npm's own message, not one of its fields | D | Service wiring of the reason is 1074's (code plus first useful line in the failed phase); npm 11 EACCES extraction is 1310's row with the same fixture. |
| 1074 | a failed install includes the code and the first useful stderr line | R | A failed install's phase carries the exit code and the first useful stderr line; no restart. |
| 1093 | a spawn %s reports its message | R | A spawn error event or throw becomes the failed phase's reason (2 rows). |
| 1116 | a rejecting restart leaves a readable failure | R | A rejecting restart leaves a readable failure. |
| 1134 | the five-minute deadline kills a child even when it never exits | R | Five-minute deadline kills the process group on a fake clock. |
| 1167 | pins the %s runner | R | Restart pins each runner (4 rows). |
| 1182 | uses PATH after pnpm removes the previous global directory | R | pnpm global restart falls back to PATH when the old bin is gone. |
| 1198 | a surviving custom prefix runs through its original runtime | C | Folded into 837: the linux case with exists checked on argv[1] becomes 837's first assertion, beside its win32 one. |
| 1213 | PnP restarts through yarn when the project has no bin shim | R | PnP project restarts through yarn without a shim. |
| 1229 | quotes a Windows project root and config path without shell arguments | R | Windows project shim and config path quoted on one shell line. |
| 1245 | quotes empty values, embedded quotes and trailing backslashes | R | windowsLine quoting of empties, quotes and trailing backslashes. |
| 1251 | %s uses a single line when Windows needs a shell | R | Every kind uses one shell line on Windows (3 rows). |
| 1310 | extracts the reason from %s | R | installerReason against real npm 11, yarn, pnpm and bun output (8 rows, #106 fixtures). |
| 1364 | merges a later check before an older process saves its skip | R | A later check is merged before an older process saves its skip. |
| 1385 | an older writer preserves the newer skipped version | R | An older writer keeps the newer skip. |
| 1398 | checkedAt decides which latest wins, even when the version is lower | R | checkedAt decides which latest wins. |
| 1409 | orders saved prerelease skips numerically | R | Prerelease skips order numerically. |
| 1423 | survives a missing home directory without persisting | R | No home directory: works without persisting. |
| 1442 | uses the configured registry base with its trailing slash removed | R | npm_config_registry is honoured without its trailing slash. |
| 1460 | notifies checks, results, errors and skips only when they change | R | onChange fires only on real changes, in order. |
| 1498 | waits for a change that began during installation, then notifies the restart | R | Waits for a change that began during the install, then restarts once. |
| 1527 | close kills the whole %s installer tree and awaits its close | R | close kills the whole installer tree on linux and win32 and waits for it (2 rows). |
| 1560 | the Windows deadline uses taskkill and retains the child until it is gone | R | Windows deadline uses taskkill and holds the child until it is gone. |
| 1586 | close cancels an install queued for the next turn | R | close cancels an install queued for the next turn. |
| 1598 | close cancels the waiting timer without handing off | R | close cancels the waiting timer without handing off. |
| 1618 | a handoff can close its own service without awaiting itself | R | A handoff can close its own service without deadlock. |
| 1635 | waits for final stdout after exit and notifies the failure | R | The failure waits for stdout after exit (close, not exit). |
| 1655 | uses the server's default port before setPort is called | R | Default port before setPort. |

### packages/server/src/config/config-branch.test.ts

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 18 | accepts a preview that names a branch | R | Keeper for branch acceptance (absorbs 27, 48): a branch preview with a devCommand is kept with both, an ordinary preview has no branch. |
| 27 | leaves branch undefined for an ordinary preview | C | Folded into 18: an ordinary preview beside the branch one has branch undefined. |
| 33 | requires a dev command, since Leglas has to start that checkout itself | C | Row in config.test's rejection table: a branch preview without devCommand names devCommand. |
| 39 | requires the dev command to say where the port goes | C | Row in config.test's rejection table: devCommand without {port}. |
| 48 | keeps the dev command when it is well formed | C | Folded into 18: a well-formed devCommand is kept. |
| 54 | rejects a branch that is not a string | C | Row in config.test's rejection table: a non-string branch. |
| 63 | rejects a branch name that could escape a path | C | Row in config.test's rejection table: a branch that climbs out (security). |
| 72 | rejects combining a branch with an absolute url, which contradicts itself | C | Row in config.test's rejection table: branch with an absolute url. |
| 81 | accepts an install command | R | An install command is kept. |
| 91 | defaults the install command, since a fresh checkout has no dependencies | C | Folded into config.test 13's defaults: installCommand defaults to npm install. |
| 97 | accepts a lone branch preview when asked, for the local previews file | R | requireDevCommand false accepts a lone branch (the local registry's rule). |
| 107 | still validates everything else about the preview | R | requireDevCommand false still refuses an escaping branch. |
| 118 | accepts a file with no url, whose url Leglas assigns at boot | R | A file preview without url is accepted with an empty url. |
| 125 | rejects a file combined with a url, which claims two sources | C | Row in config.test's rejection table: file plus url. |
| 129 | rejects a file combined with a branch | C | Row in config.test's rejection table: file plus branch. |
| 138 | rejects a file that could escape the project | C | Two rows in config.test's rejection table: ../ and absolute files (security, #118's keeper for path escapes). |

### packages/server/src/config/config.test.ts

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 6 | accepts a config with one preview | D | Acceptance is asserted with more fields by 55, 143 and config-branch 18; any rejection of a plain preview fails those. |
| 13 | defaults devServer when the config omits it | R | Keeper for documented defaults (absorbs 19, 154 and config-branch 91): devServer http://localhost:3000, scanPreviews true, tags [], installCommand npm install. |
| 19 | scans unopened previews by default | C | Folded into 13: scanPreviews defaults to true. |
| 25 | lets expensive apps disable unopened preview scans | R | scanPreviews false is honoured. |
| 35 | rejects a non-boolean preview scan setting | C | Row in 64's rejection table: scanPreviews not a boolean, config null. |
| 45 | rejects a non-boolean record setting | C | Row in 64's rejection table: recordSets not a boolean, config null. |
| 55 | treats a missing config as one preview of the app root | R | No config is one App preview of the root. |
| 64 | rejects a preview with no title, since the rail has nothing to show | R | Keeper as a rejection table (absorbs 35, 45, 71, 77, 99, 113, 122 and config-branch's rejections): each bad config yields a null config and an error naming the field. |
| 71 | rejects a preview with no url | C | Row in 64's table: a preview with no url. |
| 77 | rejects duplicate titles, which would be indistinguishable in the rail | C | Row in 64's table: duplicate titles. |
| 88 | allows the same url under different titles | R | The same url under two titles is allowed. |
| 99 | rejects a url that is neither absolute nor root-relative | C | Row in 64's table: a url neither absolute nor root-relative. Repaired on the way: its expected text "pricing" also appears in the error's own hint ("/pricing"), so it passed whether or not the message named the refused url; the row uses "about" now. Found by a deliberate break. |
| 105 | accepts an absolute url so staging can be compared against local | R | An absolute preview url is accepted (staging against local). |
| 113 | rejects a devServer that is not a valid origin | C | Row in 64's table: devServer not an origin. |
| 122 | rejects previews that is not an array | C | Row in 64's table: previews not an array. |
| 128 | reports every problem at once rather than stopping at the first | R | Every problem is reported in one pass. |
| 137 | names the offending entry by index so the error is actionable | R | Errors name the offending index. |
| 143 | carries note and tags through untouched | R | Note and tags pass through. |
| 154 | defaults tags to an empty array so the rail never guards for undefined | C | Folded into 13: tags default to []. |

### packages/server/src/config/find-config.test.ts

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 13 | finds a config in the starting directory | D | 45 writes each documented name, leglas.config.ts first, into the starting directory and expects that path. |
| 20 | walks upward, so it works from any subdirectory of a project | R | Walks upward from a subdirectory. |
| 29 | prefers the nearest config, so one app in a monorepo wins over the root | R | The nearest config wins in a monorepo. |
| 39 | returns null when no config exists anywhere above | R | Null when none exists above. |
| 45 | accepts every documented extension | R | Every documented extension is found (the four literals, #117). |
| 59 | resolves extensions in a stable order when several exist | R | TypeScript wins when several exist. |

### packages/server/src/config/load-config.test.ts

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 13 | falls back to the implicit single preview when no config exists | R | No file: implicit preview, default devServer, null path. |
| 22 | loads a TypeScript config, including its type annotations | R | Keeper for TypeScript configs (absorbs 82): type annotations load natively and the resolved path is returned. |
| 38 | loads a JSON config | R | JSON config loads. |
| 51 | reports the file path alongside a validation error, so it is actionable | R | Validation errors carry the file name. |
| 62 | reports a config that throws on import rather than crashing the server | R | A throwing config is reported, not thrown. |
| 72 | reports a config with no default export | R | A config with no default export is reported. |
| 82 | returns the resolved path so the CLI can report what it used | C | Folded into 22: result.path is the resolved file. |

### packages/server/src/config/local-previews.test.ts

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 29 | survives the round trip, so the rail can say where a direction came from | R | basedOn and askedFor survive add then read. |
| 53 | an entry with no origin stays clean rather than carrying empty fields | R | An entry with no origin stores no empty fields. |
| 67 | refuses an ask that is not a change request | R | A blank askedFor is refused (the only test of the askedFor rule). |
| 77 | returns nothing when the project has never added one | R | A project that never added one reads empty with no errors (ENOENT). |
| 84 | reads previews that were added locally | C | Folded into 94: the seeded entry's title and count. |
| 94 | marks them local, so the interface can tell shared from unshared | R | Keeper for reading the registry (absorbs 84): seeded entries read back, marked local. |
| 103 | reports a corrupt file instead of losing the whole rail | R | A corrupt file is reported, not fatal. |
| 113 | reports a registry that exists but cannot be read | R | An unreadable registry is reported without leaking the path. |
| 124 | validates entries the same way the config is validated | R | Entries are validated like the config. |
| 135 | writes a preview that then reads back | D | 29 adds and reads back with more fields, 144 adds twice and reads both titles. |
| 144 | appends rather than replacing what is already there | R | Adds append. |
| 154 | refuses a title the shared config already uses, which the rail could not tell apart | R | A shared title is refused. |
| 163 | refuses a title already added locally | R | A local duplicate is refused. |
| 172 | refuses a url that is neither root relative nor absolute | D | The url rule is config.test's table row; that add validates before writing is proven by 228 (branch) and 270 (file), which fail the same normalizeConfig check. |
| 181 | keeps the note and tags it was given | R | Note and tags are kept. |
| 195 | writes readable json, since a human may well open it | R | The file is indented for people. |
| 204 | stores the branch, so a routed direction can be registered without config edits | R | A branch is stored. |
| 218 | reads back without demanding devCommand, which lives in the shared config | R | Reads a branch without devCommand. |
| 228 | still refuses a branch name that could escape a path | R | Security: an escaping branch is refused on add. |
| 241 | stores the file and no url, and reads back cleanly | R | A file preview is stored without url and reads back. |
| 256 | survives a second add: the filled-in empty url must not round-trip | R | Regression: the filled-in empty url does not round-trip on a second add. |
| 270 | refuses a file that could escape the project | R | Security: an escaping file is refused on add. |
| 284 | a reader never sees the registry half written while directions come and go | R | Atomic writes: a reader never sees a torn registry. |

### packages/server/src/config/renames.test.ts

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 13 | a config title resolves to itself | D | 25 resolves a config title to itself while a rename to the same word exists, which this case's plain lookup is a subset of. |
| 17 | a name from the rail resolves to the title the config knows | R | A rail name resolves to its config title. |
| 25 | a config title beats a local nickname of the same word | R | A config title beats a local nickname. |
| 31 | two directions renamed to one word is refused, not guessed at | R | Two directions renamed alike is ambiguous, not guessed. |
| 43 | a name nothing answers to is unknown | R | An unknown name is unknown. |
| 50 | a rename of a direction that no longer exists resolves nothing | R | A rename of a deleted direction resolves nothing. |
| 59 | survives a write and read round trip | R | Write then read round trip. |
| 66 | a project that never renamed anything reads as empty | R | Never renamed reads empty. |
| 70 | a corrupt file falls back to the config titles rather than throwing | R | A corrupt file reads empty. |
| 78 | drops entries that are not string pairs, since a browser writes this | R | Non-string pairs are dropped (a browser writes this file). |

### packages/server/src/branches/branches.test.ts

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 55 | joins a start already in flight, so one title gets one checkout | D | server.test 2278 starts the same branch twice concurrently through the route and asserts one checkout, the checking-out phase and ready; the shared promise identity here is not observable behaviour. |
| 89 | records a failure and lets the next start retry it | R | A failed checkout is recorded and the next start retries. |
| 119 | tracks checkout, install and app startup as coarse phases | R | Coarse phases in order: checking out, installing, starting, ready. |
| 153 | stops every worktree it owns | R | stop stops every worktree the registry owns. |
| 177 | stops a ready branch after ten minutes without proxy activity, then lets it start again | F | Idle sweep after ten minutes, then restart. Repair: drop the checkout directory it creates and removes, which nothing has asserted since #117 removed the fake's existsSync check. |
| 228 | does not stop a branch that still has an active proxy connection | R | An active proxy connection keeps the branch alive. |
| 261 | never stops a branch while it is starting | R | Never swept while starting. |

### packages/server/src/branches/classify.test.ts

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 16 | stays in-app for new files beside what exists | R | Keeper as a placement table (absorbs 27, 46, 67, 80, 88): each declared change set and its level. |
| 27 | wiring a branch point into an existing component is additive | C | Row in 16's table: wiring a branch point into an existing file is in-app. |
| 33 | routes a dependency change to a checkout | R | Dependency changes go to a checkout and the reason names the file. |
| 46 | a lockfile anywhere in a monorepo counts as a dependency change | C | Row in 16's table: a nested lockfile is a checkout. |
| 52 | routes build configuration to a checkout | R | Build configuration names go to a checkout (8 paths). |
| 67 | leglas's own config file is registration, not build configuration | C | Row in 16's table: leglas's own config is in-app. |
| 73 | routes a rewrite of an existing shared file to a checkout | R | A rewrite of an existing shared file is a checkout naming the file. |
| 80 | a rewrite of a path that does not exist is just a creation | C | Row in 16's table: a rewrite of a missing path is in-app. |
| 88 | a rewrite of the direction's own exploration files contends with nobody | C | Row in 16's table: a rewrite of the direction's own files is in-app. |
| 96 | the dependency reason wins when several rules match | R | The dependency reason wins when several rules match. |
| 108 | always says what to do next | R | Both placements say what to run next. |

### packages/server/src/branches/worktree.test.ts

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 19 | keeps a simple branch name | C | Row in 23's slug table: a plain name stays. |
| 23 | flattens slashes, so a namespaced branch is one directory | R | Keeper as a slug table (absorbs 19, 27, 31): slashes, unsafe characters and runs flattened. |
| 27 | strips characters that have no business in a path | C | Row in 23's table. |
| 31 | collapses runs of separators rather than leaving gaps | C | Row in 23's table. |
| 37 | replaces the placeholder | C | Folded into 41: one placeholder is the single-occurrence case of every occurrence. |
| 41 | replaces every occurrence, since some commands need it twice | R | Every {port} is replaced. |
| 84 | checks out the branch, boots it, and serves that branch's content | R | Keeper for the worktree lifecycle against real git (absorbs 102, 148, 199): checkout under .leglas, an IPv4-only dev server reached at a 127.0.0.1 url serving the branch's content and stop leaves git worktree list clean. |
| 102 | puts the checkout under the ignored directory | C | Folded into 84: the checkout lives under .leglas. Same real checkout and boot. |
| 121 | reports a branch that does not exist rather than hanging | R | A missing branch is reported, not hung. |
| 134 | reports a dev command that never answers, instead of waiting forever | R | A dev command that never answers is reported within its deadline. |
| 148 | removes the checkout when stopped, leaving the repository clean | C | Folded into 84: stop removes the worktree registration. |
| 172 | finds a dev server listening on IPv6 only, and reports a URL that reaches it | R | Regression: an IPv6-only dev server is found and its url bracketed. Baseline failure here only (the fixture cannot listen on ::1 in this VM); passes on CI. |
| 199 | still finds one listening on IPv4 only | C | Folded into 84: its fixture already listens on 127.0.0.1 only and is fetched through the url startAppProcess built; 84 gains the url-contains-127.0.0.1 assertion. |

### packages/server/src/requests/annotations.test.ts

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 41 | takes an anchor the interface sent | R | A well-formed anchor round-trips unchanged. |
| 47 | refuses an anchor with nothing to point at | R | No selector, a non-string one, null or a bare string is refused (only shapes beyond server.test 1199's missing anchor). |
| 56 | keeps a note whose geometry arrived malformed | R | Malformed geometry is zeroed, the note kept. After cutover it also reads an anchor that is nothing but a selector, restored from server.test 2245 (see Restored contracts). |
| 64 | caps what a browser can put in the file | R | Browser values are cut down, not thrown away (#117). |
| 84 | keeps a pointed-at spot inside the element it belongs to | R | The spot is clamped inside the element. |
| 90 | a note with no spot recorded lands in the middle | R | Legacy notes with no spot sit at the middle. |
| 95 | names an element that arrived without a tag | R | A tagless element is still named, never <>. |
| 104 | has nothing to say about a project that has never been annotated | R | Reading a never-annotated project leaves no .leglas. |
| 110 | keeps notes in the order they were left | R | Notes keep the order they were left. |
| 121 | gives every note an id of its own | D | Distinct ids are what 129 relies on: with a repeated id, dropping first.id would drop both notes and 129's ["b"] fails. server.test 1000 deletes by id too. |
| 129 | drops the notes it is asked to and reports how many there were | R | Drop by id reports how many were there. |
| 140 | rewords a note and leaves what it points at alone | C | Folded into 245: the trimmed words and the kept anchor are asserted on 245's middle note. |
| 157 | rewording a note to nothing empties it rather than dropping it | R | Rewording to nothing empties the note rather than dropping it. |
| 167 | a reworded note is capped like every other note | R | A reworded note is capped like a new one. |
| 180 | rewording one note leaves the others alone | C | Folded into 245: the two untouched neighbours are asserted equal to what was added. |
| 196 | a note reworded while a change holds it survives that change landing | D | 211 runs the same reword then sweep of the old id and asserts the same new id and surviving words; it also fails when the writes are not serialised, which this sequential version cannot. |
| 211 | a revision and a sweep landing together cannot overwrite each other | R | A revision and a sweep landing together keep the revision (serialised writes). |
| 225 | two notes left at the same moment both survive | R | Two notes left at once both survive. |
| 236 | saving a note without changing it changes nothing at all | R | Saving unchanged words keeps the note and its id. |
| 245 | a reworded note keeps its address and its turn under the new identity | R | Keeper for rewording (absorbs 140, 180): new id, same anchor and place, trimmed words, neighbours untouched. |
| 260 | rewording a note that has gone leaves no trace on disk | R | Rewording a missing note leaves no trace. |
| 266 | forgetting nothing leaves no trace on disk | R | Forgetting nothing leaves no trace. |
| 272 | an unreadable file reads as no notes rather than stopping the interface | R | An unreadable file reads as no notes. |
| 280 | skips an entry with nothing to point at rather than reading it back broken | R | Entries without anchor or title are skipped. |
| 297 | writes a file a person can read | R | The file is readable JSON with a trailing newline. |
| 308 | takes only the notes left on the direction asked about | R | annotationsFor keeps one direction's notes in order. |
| 329 | survives the round trip | R | A swept region round-trips. |
| 333 | keeps a region inside the element it is a fraction of | R | Region fractions are clamped. |
| 339 | caps what a drag across half the page can record | R | covers is capped, entries cut not dropped. |
| 354 | is described as an area, not as the element that holds it | R | A region is described as an area with what it covers (prompt wording). |
| 364 | leads with what survives a change and ends with what does not | R | Exact anchor line, durable facts first (prompt bytes). |
| 371 | leaves out what an element does not have | R | Absent class and text are left out (prompt bytes). |
| 379 | numbers the notes the way the pins are numbered | R | Notes are numbered like the pins. |
| 390 | a pin dropped without words still says where to look | R | A wordless pin still says where to look. |

### packages/server/src/requests/attachments.test.ts

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 100 | resolves project routes and leaves absolute previews alone | R | previewUrl resolves routes and leaves absolute urls alone (absolute case unreached elsewhere). |
| 111 | reads each supported container from its own bytes | R | sniffImage reads PNG, GIF, JPEG and WebP sizes from their bytes (only test of the non-PNG parsers). |
| 142 | a recognised container whose dimensions cannot be read still names itself | R | A recognised but truncated container still names itself. |
| 147 | anything else is not an image | R | Anything else is not an image. |
| 154 | writes the frame, numbered notes, comparison and moved references | R | attachRequest writes frame, numbered notes, comparison and moved references, every path real, two loads. |
| 248 | a note whose crop could not be taken is left out rather than misnumbered | R | A missing crop is left out, not misnumbered. |
| 275 | moves references even when no browser can be found | D | server.test 643 (with 736 folded in) posts a request with an uploaded reference and no browser: skipped is NO_BROWSER, the reference moves to reference-1.png measured 2x3 and the source is gone. |
| 302 | honours one deadline and returns without waiting for a stuck capture | R | One deadline: returns without a stuck capture, aborts it, the load gets a share under the deadline. |
| 337 | a page that will not load is reported rather than thrown | R | A page that will not load is reported, not thrown. |
| 364 | moves the directory and repoints every path at it | D | server.test 1945 retries a failed request with a capture: the file moves under the new id with its bytes, the path is repointed and the old directory is gone. |
| 382 | points every capture path at the new directory and nothing else | R | rehomeText rewrites only the exact id prefix (abc, not abcd). |
| 393 | removes one request and prunes everything not kept except show | R | Cleanup removes one request and prunes all but kept ids and show. |
| 411 | a project that never captured anything is left untouched | R | A project that never captured is untouched. |
| 420 | an id that is not one Leglas minted removes nothing | R | Security: an id Leglas did not mint removes nothing. |
| 436 | a symlinked captures directory is left alone instead of emptied | R | Security: a symlinked captures directory is not emptied. |
| 449 | a link inside the captures directory is not an image this project owns | R | Security: isOwnCapture refuses links and directories (published API). |

### packages/server/src/requests/requests.test.ts

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 30 | derives the file from a url the scaffold generated | R | Keeper as a targetFor table (absorbs 34-50 and the variantSlot cases): scaffold urls map to their file; other paths, absolute urls, look-alike params and climbing values give nothing. |
| 34 | works when the variant param is not the only one | C | Row in 30's table: the variant param among others. |
| 38 | returns nothing for a url that is not a variant of a surface | C | Row in 30's table: a plain path. |
| 42 | returns nothing for an absolute url, which is not ours to edit | C | Row in 30's table: an absolute url. |
| 46 | ignores a param that merely looks similar | C | Row in 30's table: a look-alike param. |
| 50 | refuses a value that would escape the variants directory | C | Row in 30's table: a climbing value (security). |
| 64 | builds a new direction and says the old one is not to be touched | R | Keeper for the scaffold variant prompt (absorbs 79, 91, 114, 290, 696): every assertion of those tests on the one composed prompt. |
| 79 | starts the new direction from a copy of the parent's file | C | Folded into 64: target, source line and copy instruction. |
| 91 | hands over the registration that puts it under its parent | C | Folded into 64: the registration command and its flags. |
| 101 | registers through the exact running CLI without package discovery | R | Registration names the exact running CLI, no npx. |
| 114 | marks interface discovery and server startup as already complete | C | Folded into 64: discovery-complete wording, no restarting, the look command. |
| 125 | puts fresh captures, comparison, references and load evidence after the ask | R | Captures, comparison, references and load evidence follow the ask, in order. |
| 195 | explains hydration evidence and the additive shared-script exception | R | Hydration evidence in both modes; the additive exception always. |
| 247 | quotes the request so a typed quote cannot break the command | R | Security: a typed quote cannot end the --asked-for argument. |
| 257 | a file-backed direction is copied as a file and registered as one | R | A file direction is copied and registered as a file. |
| 270 | a direction with no derivable source still gets a usable brief | R | No derivable source still gets a usable brief. |
| 279 | reports the mode it composed for, so the queue can record it | D | composeRequest echoes the mode it was given; server.test 1429 asserts the route returns variant and replace for the two sends. |
| 290 | never tells the agent to edit the parent | C | Folded into 64: the fork prompt never says to edit the parent. |
| 299 | reads the surface and option a scaffold url names | D | 30's table covers the same parse through targetFor (surface and option land in the path); variantSlot then has no caller outside requests.ts and stops being exported. |
| 303 | refuses anything that could climb out of the variants directory | D | 30's climbing row is the same refusal through targetFor. |
| 307 | has nothing to say about a url the scaffold did not write | D | 30's plain-path row. |
| 313 | names the direction so the agent knows what is being changed | D | Its two contains checks are carried by 347's keeper ("change only the \"Aurora\" design direction", "What to change: warmer"). |
| 324 | points at the exact file when the url reveals one | C | Folded into 347: the derived target and its path in the prompt. |
| 335 | still produces a usable prompt when the file cannot be derived | R | No derivable file: title and url name the direction. |
| 347 | tells the agent the change is scoped, so it skips the verification ceremony | R | Keeper for the in-place prompt (absorbs 324, 370, 377, 383): scoped wording, finish lines, look commands, change only this one, no re-register, trimmed intent. |
| 370 | tells the agent to change only this direction, not its siblings | C | Folded into 347. |
| 377 | does not ask the agent to re-register a direction that already exists | C | Folded into 347. |
| 383 | trims the intent, so padding from a textarea does not reach the agent | C | Folded into 347: the known prompt uses a padded intent. |
| 399 | append assigns an id and queued status | D | A minted id on append is what server.test 1815, 1989 and 2066 read back and act on; queued status after append is 476's assertion on its late request; 406 covers a preallocated id. |
| 406 | append accepts a preallocated id and ids stay URL-safe | R | A preallocated id is used; minted ids are URL-safe. |
| 414 | reads only attachments with a file and kind | D | The attachment filter is 743's (shape, own directory, kind); captureNote read-back is server.test 643's queued captureNote. The file-less entry is dropped by 743's own-file pattern too. |
| 440 | collect marks requests picked-up and persists | R | Collect marks picked-up and persists. |
| 448 | collecting an empty queue leaves no trace on disk | R | Collecting an empty queue writes nothing. |
| 454 | reads legacy entries with a stable fallback id | R | Legacy entries read with a fallback id and replace mode; the file is untouched. |
| 467 | clear drops the work that was collected | D | 476 clears the same collected request (cleared 1) and also keeps the late one. |
| 476 | clear keeps a request that arrived while the agent was working | R | Clear keeps a request queued after collection. |
| 490 | clearing an empty queue leaves no trace on disk | R | Clearing an empty queue writes nothing. |
| 497 | marking one picked-up leaves the others queued | R | markPickedUp marks one. |
| 511 | marking an unknown id changes nothing | R | markPickedUp of an unknown id changes nothing. |
| 518 | removing one request leaves everything queued behind it | R | Removing one keeps the rest. |
| 529 | removing and clearing requests remove their capture directories | R | Remove and clear delete capture directories. |
| 546 | removing an unknown id is a no-op, not an empty queue | R | Removing an unknown id is a no-op. |
| 553 | removing from a queue that was never written leaves no trace on disk | R | Removing from an unwritten queue writes nothing. |
| 571 | a verdict survives the process that wrote it | R | Verdicts persist; a stop is cancelled; an unknown id is false. |
| 597 | a hand-edited verdict is dropped rather than trusted | R | A hand-edited verdict is dropped; an unknown status reads queued. |
| 625 | collection never hands an ended request to another agent | R | Collection never hands over an ended request. |
| 642 | clearing counts only what is still waiting as pending | R | Clear counts only waiting requests as pending. |
| 659 | quotes the title the way --based-on does, so a quote in the name survives | C | Folded into 673: the title there gains a double quote, escaped by the same shellArgument. |
| 673 | a title with shell metacharacters is inert inside the show command | R | Security: quotes, $() and backticks in a title are inert in the show command (absorbs 659). |
| 685 | the registration arguments are quoted the same way | R | Security: registration arguments are quoted the same way. |
| 696 | registration is not the end any more; the look comes after it | C | Folded into 64: register before look, in that order. |
| 705 | a hand-edited id that is not one Leglas minted reads back as its index | R | Security: a hand-edited id reads back as its index. |
| 723 | is not asked to screenshot what cannot render until a restart | R | A file direction's variant finishes at registration, no screenshot. |
| 743 | only files inside the request's own capture directory survive the read | R | Security: only files inside the request's own capture directory survive the read. |
| 780 | every capture is named as a file, so a path-only agent can still open it | D | capturedBlock is shared by both modes; 125 asserts the same paths and the open-every-one line, and 195 proves the block lands in the replace prompt too. |

### packages/server/src/share/share.test.ts

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 116 | binds a second listener, issues an entry URL and nudges share | C | Folded into 343 (url null, no viewers on the first link) and server.test 2956 (second port, entry url shape, tunnel none, share nudges). |
| 139 | sets the cookie at entry and refuses wrong or missing credentials | R | Security: entry sets an HttpOnly, SameSite=Lax, Secure-over-https cookie; missing and wrong credentials refused, HTML refusal page. |
| 188 | refuses every viewer mutation before the shared handler sees it | D | server.test 2956 posts the same mutation through the real share listener and asserts this manager's own 403 sentence, which no other layer produces. |
| 215 | gives a viewer config to a live link and nothing to a stranger | R | Viewer config only for a live link; revocation applies at once. |
| 235 | builds viewer config from shared titles in config order | R | Viewer config in config order with scope and layout. |
| 257 | rejects branch-backed and unknown directions before binding | R | Branch and unknown directions are refused with their sentences before binding. Keeper for server.test 3167. |
| 296 | the stop wins, and no listener is left behind | R | A stop during creation wins and leaves no listener. |
| 343 | a share opens with one link, and every later one is its own | R | One link at first (unnamed, no url without a tunnel, no viewers), later links get their own tokens (absorbs 116). |
| 360 | refuses a seventeenth link rather than growing without end | R | The seventeenth link is refused. |
| 375 | revoking one link leaves the others, and says which happened | R | Revoking one keeps the others; turned off, lapsed and unknown answer differently. |
| 402 | a link past its deadline is expired, not merely unknown | R | A link past its deadline is expired and leaves the share. |
| 421 | the monotonic clock expires a link whose wall clock went backwards | R | The monotonic clock expires a link when the wall clock goes back. |
| 435 | extend moves a live link's deadline and will not raise a dead one | R | Extend sets an absolute deadline and cannot raise a dead link. |
| 464 | revoking a link drops the sockets and the requests it was holding | R | Revoking drops held streams. |
| 498 | rotate ends every link and issues one nobody has seen | R | Rotate ends every link and mints a new one. |
| 543 | open reach serves the app, as it did before there was a list | D | Open is the default: server.test 2956 and 139 both load /pricing with a default share and get the app. |
| 549 | listed reach serves the list and refuses the rest, remembering what it refused | R | Listed reach serves the list and the interface, refuses and remembers the rest. |
| 571 | a refusal is remembered as what it named, not as it was spelled | R | Security: refusals are remembered as settled paths. |
| 590 | allowing a path that ends in a slash allows that path, not everything beneath it | R | Allowing a slash-ended path does not allow its subtree unless asked; the root is never a folder. |
| 610 | a folder allowed by one click does not open what is beside it | R | Security: an allowed folder does not open what is beside it. |
| 627 | a path that only canonicalises into the interface is not the interface | R | Security: paths that only canonicalise into /leglas are not the interface. |
| 659 | the interface prefix is not a way around the list | R | Security: the interface prefix is no way around the list. |
| 676 | allowing a refused path lets it through and clears it from the list | R | Allowing a folder clears its refusals; a path without a slash is refused. |
| 693 | the list is read on the settled path, never on the readiest one | R | Security: the list is read on the settled path (routeAllowed table). |
| 722 | names the routes that act on the machine, and their subtrees | R | Security: dev-control routes and subtrees (17 routes). |
| 746 | takes a tool's whole dev namespace, not a list of its routes | R | Security: whole dev namespaces (Next, Nuxt, Parcel). |
| 768 | refuses every spelling the dev server would answer to | R | Security: every spelling the dev server answers (case, slashes, escapes, backslashes). |
| 793 | a malformed escape is refused rather than throwing | R | A malformed escape neither throws nor matches. |
| 799 | catches the one that hides in the query rather than the path | R | Security: Werkzeug's query-borne debugger. |
| 807 | leaves the app alone, including paths that merely start alike | R | Look-alike app paths and framework assets are left alone. |
| 879 | holds viewer traffic at twelve inside the dev server at once | R | At most twelve viewer requests inside the dev server. |
| 917 | lets the interface through while every slot is taken | R | The interface bypasses the ceiling. |
| 947 | a response that never ends does not keep its slot | R | Streams do not hold their slot. |
| 971 | gives a quiet link its turn rather than draining a loud one first | R | A quiet link gets its turn before a loud one drains (fairness ordering). |
| 1019 | turns away a link that queues more than it may | R | One link's queue is capped at 128 and the next is a 503. |
| 1066 | answers what a revoked link left waiting | R | Waiting requests of a revoked link are told 410. |
| 1099 | sheds a request that waited out its budget | R | Requests that waited out the budget are shed with a 503. |
| 1152 | takes back the slot when the dev server never answers | R | A hung upstream gives its slot back. |
| 1175 | a viewer who gives up while waiting frees the place they held | R | A viewer who leaves frees their place for the next. |
| 1216 | refuses what a leading dot usually names | R | Security: dot paths (credentials) are hidden in every spelling. |
| 1237 | a dotfile is hidden wherever it sits, node_modules included | R | Security: a dotfile under node_modules is still hidden. |
| 1249 | leaves the dot directories a dev server serves from alone | R | Dev-server dot directories stay served. |

### packages/server/src/share/tunnel.test.ts

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 44 | reads a cloudflared URL from stderr and becomes ready after the probe | R | cloudflared: URL from stderr, probe, ready; exact spawn arguments and augmented PATH. |
| 88 | reads ngrok's JSON line and accepts its https fallback | R | ngrok: JSON stdout line, exact spawn arguments. |
| 125 | fails when no URL arrives before the deadline | R | No URL by the deadline fails with the last output line. |
| 151 | fails when the process exits before reporting a URL | R | An early exit fails with its output. |
| 176 | says the link is slow past the probe deadline and keeps asking until it answers | R | Past the probe deadline: slow, still asking, a late answer counts. |
| 217 | settle reports the link ready on outside evidence and stops asking | R | settle needs a URL, reports ready and stops the probing. |
| 250 | never takes cloudflared's API host for the link | R | Security: cloudflared's API host is never the link. |
| 272 | stop sends SIGTERM, escalates and resolves on its own deadline | R | stop: SIGTERM, SIGKILL after 3s, resolves by 5s. |
| 296 | finds an executable on the augmented PATH and omits a missing provider | R | detectTunnels finds an executable on the augmented PATH and omits a missing one. |
