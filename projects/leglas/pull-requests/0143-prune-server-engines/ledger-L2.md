# Lane L2 ledger: server engines

Steps 2 to 5 of the test-pruning campaign for lane L2: the server package's tests in `agents`, `generation` and `capture`. Baseline at `main` d7c72d9: 11 files, 9,016 test lines, 243 declarations, 275 cases (272 passed, 1 failed, 2 skipped when run alone). This file is temporary, like the rest of `campaign/`.

## Marks

- `R` retain: the contract it names and the bug it catches.
- `F` retain and repair the assertion.
- `C` consolidate: the keeper that absorbs the assertion first.
- `D` delete: the proof that remains, or why no contract exists.

A declaration is an outermost `test`, `test.each` or `test.skipIf` call. Line numbers are the baseline file's.

## How each file was read

Every test file was read in full with its production owner, the owner's callers (`server.ts`, `runner.ts`, `generation.ts`, `cli/src/run-watch.ts`, `cli/src/watch.ts`), the overlapping L1 tests in `server.test.ts` and `site/build.test.ts`, and the history of September's audit (#117 touched every agents and capture file here; `generation.test.ts` landed in #110 after the audit and was never audited). The audit kept a test when Stryker showed it was the only one catching a mutant, and named five such keeps; the one in this lane is `activityVerified`'s test, which stays.

Two kinds of evidence decide a `D` or `C` here:

1. An exact `toEqual` on a whole argv, message or record elsewhere already fails on the change the candidate guards (for example `codex is told it may run outside a git repository`).
2. A boundary test drives the same production line with the same input and asserts the same output (for example Claude and Codex activity labels, which the generation suite asserts through `createGenerations` and its own fake CLIs).

Coverage cannot see refusal text, ordering or timing, so every `D` and `C` below names the assertion that still holds that contract.

## agents/agent-command.test.ts (144 lines, 18 declarations)

Owner `agents/agent-command.ts`. Callers: `runner.ts` (custom templates), `server.ts` (validates a saved template), `cli/src/watch.ts` and `run-watch.ts` through the built bundle, so the cli's own tests are blind to this code. `parseTemplate`, `commandFor` and `nextRequest` are in `api-surface.txt`.

| Line | Declaration | Mark | Evidence |
| --: | --- | :-: | --- |
| 34 | splits an agent command into argv, with no shell involved | R | Argv contract with `spawn(shell: false)`; fails if the template is joined or shell-split. |
| 38 | accepts a command with no placeholder; the prompt rides along at the end | R | Only proof that a template without `{prompt}` appends the prompt last (`commandFor` branch). |
| 50 | refuses a placeholder glued to another word | C | Into one refusal table (`refuses %j with one line that says why`): each row keeps its wording, and every refusal is now held to the one line the cli prints. |
| 56 | refuses a second placeholder rather than filling both | C | Same refusal table. |
| 60 | refuses a placeholder used as the program itself | C | Same refusal table. |
| 64 | refuses an empty command | C | Same refusal table. |
| 68 | keeps a double-quoted value together as one token | R | Keeper for the quoting rules; absorbs lines 75 and 83 as further expectations. |
| 75 | takes single quotes too | C | Into line 68: same `tokenize` quote branch with the other quote character. |
| 83 | joins a quoted section to the word it is attached to | C | Into line 68: same tokenizer, `started` flag across a quote. |
| 90 | refuses an unclosed quote instead of guessing where it ended | R | Refusal branch in `tokenize`. |
| 96 | puts the whole prompt in one argv entry, however many words it has | R | Security: browser text reaches the agent as one argv entry. Absorbs line 103. |
| 103 | leaves a prompt full of shell punctuation exactly as it is | C | Into line 96: the same substitution, with the punctuation prompt as a second expectation. |
| 109 | carries a stub script through unchanged | D | Composition of line 68 (quoted token) and line 96 (substitution); no branch of its own. |
| 121 | takes the first queued request, so the queue runs in order | R | Keeper for `nextRequest`; absorbs lines 127 and 141. The cli's watch loop uses it from the bundle, where no cli test can see it. |
| 127 | skips one that already failed | C | Into line 121: the `failed` set check. |
| 133 | leaves a picked-up request alone, since another agent has it | R | The `status === "queued"` filter; after a restart the failed set is empty and only the status keeps a failed or picked-up request from rerunning. |
| 137 | has nothing to do with an empty queue | D | `find` on an empty list; lines 133 and 141 already assert the `null` answer. |
| 141 | returns nothing once every queued request has failed | C | Into line 121: the null answer when the failed set covers the queue. |

## agents/agents.test.ts (756 lines, 38 declarations)

Owner `agents/agents.ts`. Callers: `runner.ts` (argv, session, retry, activity), `generation.ts` (activity, edited files), `server.ts` (detection, saved choice), `share/tunnel.ts` (`pathLookup`), `claude-agent-session.ts` and `codex-app-server.ts` (`agentEnvironment`), `cli/src/run-watch.ts` (`terminalArgs`, from the bundle).

| Line | Declaration | Mark | Evidence |
| --: | --- | :-: | --- |
| 33 | builds the verified argv for each vendor without a cwd flag | R | Exact argv per vendor (`--trust`, `--skip-git-repo-check`, network access, no model). Fails on any added or dropped flag. |
| 64 | builds readable terminal argv for each vendor | R | Exact `terminalArgs`; its only caller is the cli's watch, which no measured test reaches. |
| 87 | puts every image before the Codex prompt on cold, resumed and terminal runs | R | Image order on all three Codex builders, and none for Claude or Cursor. |
| 109 | codex is told it may run outside a git repository | D | Lines 33, 64 and 322 compare all three Codex argvs whole, each with `--skip-git-repo-check` and the sandbox; dropping the flag fails all three. |
| 125 | agent defaults do not override the user's quality settings | D | Same three whole-argv comparisons: an added `--model` or effort, or a dropped network flag, fails them. |
| 136 | adds an explicit effort only when the user chooses one | R | Effort on Codex resume and terminal argv and on Claude; only the cold forms are reached by runner tests. |
| 150 | searches conventional user install directories beyond a service PATH | R | Platform contract: a detached server finds CLIs outside its PATH, with no duplicates. |
| 169 | finds CLIs installed inside an NVM-managed Node version | R | Version-manager directories; regression for CLIs installed per Node version. |
| 177 | detectAgents probes binaries and logins through the injected hooks | R | Lookup order, no probe for a missing binary, and the detected shape the picker reads. |
| 206 | a status command whose child outlives it still answers, as unknown | R | Regression: a probe waiting on `close` hung the agents endpoint for good. |
| 217 | an unreadable or failed probe reads as unknown, never as signed out | R | Safety rule: an unknown never boxes a user out of a working agent. |
| 226 | reads both of Cursor's real status answers | C | Into line 387: the same `authVerdict` call, with the two real Cursor answers as table rows. |
| 293 | the real agent CLIs ... read as signed in | R | Opt-in live check named in CONTRIBUTING; skipped in CI and here. |
| 297 | the real agent CLIs ... read as signed out with no saved login | R | Same opt-in live check. |
| 322 | resume argv continues the session without trying to replace its sandbox | R | Exact Claude and Codex resume argv (Codex refuses `-s` on resume). Absorbs line 366. |
| 348 | sessionFrom reads each vendor's own id and nothing else | R | Codex ids only on `thread.started`, custom never resumes; runner tests only send the positive lines. |
| 366 | Cursor resumes a chat by its id | C | Into line 322: the third vendor's resume argv. |
| 378 | only a vendor whose output Leglas has read reports edits it can act on | R | Kept by September's audit as the only test catching the custom-agent rule; also the only guard of Claude's flag, since runner rerun tests use Codex and Cursor. |
| 387 | each vendor's verdict reads its own CLI honestly | R | Keeper for `authVerdict`, rewritten as one table that also carries line 226's real Cursor answers. |
| 400 | reads the api_retry event Claude prints while it backs off | R | Field mapping from a captured stream line; runner tests only reach the verdict. Absorbs line 424. |
| 424 | ignores every other line, including malformed ones | C | Into line 400: the negative lines become further expectations. |
| 434 | a project reached through a symlink still knows its own files | R | Regression: macOS answers `/tmp` from `/private`, and a build's own file read as a stray. |
| 451 | a file outside the project is named by its whole path, not by ../.. | R | The stray message names the path a person can open. |
| 466 | reads Claude tool-use events | D | `generation.test.ts` asserts Claude `Write` and `Edit` events read as `editing <project path>` through `createGenerations` (lines 2262 and 2300, which this lane keeps). |
| 483 | reads the Codex file-change item shape emitted by codex exec --json | D | `generation.test.ts` "plans and builds with restricted Codex runs" asserts the same `item.started` file change announces `editing .leglas/variants/hero/hero-ledger.tsx`; runner line 592 reads it as an edit. |
| 497 | shows the command a Codex item is running, unwrapped from its shell | C | Into the command table at line 665 as a single-quoted row; the table already covers the double-quoted and array forms. |
| 511 | reads Cursor's own tool_call events, which are not Claude's shape | R | Captured from cursor-agent 2026.09.02; the only proof of Cursor's real event shape. |
| 582 | a Cursor edit with no path is still an edit | C | Into a new `Cursor tool_call rows` table: the runner reads "editing" to refuse a rerun. |
| 602 | finds the Cursor tool wherever it sits among the wrapper's other keys | C | Into the same Cursor table: bookkeeping keys first. |
| 618 | names a Cursor tool it does not know without guessing what it did | C | Into the same Cursor table. |
| 628 | shows the command a Cursor tool call is running | C | Into the same Cursor table. |
| 654 | shows the command Claude's Bash tool is running | R | Only test of Claude's Bash branch. |
| 665 | cleans command text for the status line (6 rows) | R | Status-line truncation and unwrapping; absorbs line 497 as a row. |
| 681 | ignores unparseable or unrecognized output (3 rows) | R | No label from malformed lines for either vendor. |
| 690 | agent choice preserves the saved run template and unknown config fields | R | Storage contract: `watch.json` keeps fields Leglas does not own. |
| 717 | remembers effort separately for each built-in agent | R | Storage contract: per-agent efforts and clearing one. |
| 738 | a custom choice stores its validated template for the runner | D | `server.test.ts` (L1) "reports available agents and round-trips the saved choice" saves `{ agent: "custom", run }` through the API and reads it back. |
| 750 | an inherited object key is not accepted as a built-in agent id | R | Security: `toString` in `watch.json` is not an agent. |

## agents/claude-agent-session.test.ts (628 lines, 15 declarations)

Owner `agents/claude-agent-session.ts`, reached in production only through `runner.ts`. The runner tests inject a stub transport, so this file is the only one that drives the session class.

| Line | Declaration | Mark | Evidence |
| --: | --- | :-: | --- |
| 138 | a release outlasts a warm started while an earlier release was settling | R | Generation race between `warm` and `release`; regression from resident processes. |
| 165 | a warm asked for after a release began survives it | R | The reverse race. |
| 187 | a released conversation is loaded into the next warm process | R | Regression: after an idle release every request fell to the `claude --resume` CLI. |
| 234 | a run naming a session loads it even when nothing was warmed for it | C | Into line 271, whose first run already names a session with nothing warmed; it now also asserts `resume` on that start. |
| 244 | a handle warmed fresh is replaced when the request continues a session | R | Keeper for replacing a warm handle loaded for another conversation; absorbs line 257. |
| 257 | a handle warmed for a session is replaced when the request starts fresh | C | Into line 244: the same `warmedFor !== sessionId` branch in the other direction. |
| 271 | a fresh turn after a resumed conversation rotates the process | R | Keeper for rotation on a fresh turn; absorbs lines 234 and 431. |
| 300 | warms once and keeps multiple turns in one SDK process | R | SDK options contract (permission mode, setting sources, allowed tools, no model) and per-turn effort. |
| 388 | hands readable bounded images to Claude as base64 content blocks | R | Image size bound, type filter and missing-file skip. |
| 431 | rotates to a fresh process when the caller starts a fresh session | C | Into line 271: same rotation branch; its effort expectation moves there, strengthened to the same effort on both turns so a stale `appliedEffort` fails it. |
| 473 | maps a polite stop to the SDK interrupt without killing the session | R | SIGTERM is an interrupt, not a close. |
| 500 | reports SDK error results as failed turns | R | Exit code 1 for an error result. |
| 526 | replays a result that arrives before the close listener is attached | R | Rewritten by #117 with a proof that the replay branch is needed. |
| 560 | aborts an in-flight SDK warmup during shutdown | R | Shutdown does not wait on a hung handshake. |
| 582 | finishes cancelled rotation cleanup before starting the next query | R | Ordering of reset and next start. |

## agents/codex-app-server.test.ts (416 lines, 9 declarations)

Owner `agents/codex-app-server.ts`, reached only through `runner.ts`. Each test pins a distinct protocol step or race; #117 rewrote the timeout test with a proof.

| Line | Declaration | Mark | Evidence |
| --: | --- | :-: | --- |
| 123 | a release outlasts a warm queued behind an earlier reset | R | Generation race, Codex side. |
| 149 | a warm asked for after a release began survives it | R | Reverse race. |
| 168 | warms once, streams a turn and reuses its loaded thread | R | JSON-RPC contract: thread and turn params, item translation to the CLI's event shape, thread reuse. |
| 264 | resumes a stored thread after a new app-server process | R | `thread/resume` branch and effort on a resumed turn. |
| 294 | maps cancellation to turn/interrupt | R | Interrupt params. |
| 324 | replays an immediate completion to a late close listener | R | Replay branch. |
| 355 | fails pending requests instead of crashing on an asynchronous stdin error | R | EPIPE rejects and resets instead of crashing the server. |
| 367 | terminates an ambiguously accepted turn before reporting its timeout | R | Safety: no CLI fallback while the app-server may still edit. |
| 398 | waits for an in-progress reset to escalate before shutdown completes | R | Shutdown ordering. |

## agents/failure.test.ts (128 lines, 9 declarations)

Owner `agents/failure.ts`. `FailureCode` is in `api-surface.txt` and the messages are what the interface shows. Each test owns a branch of the verdict order; #117 already deleted the one the runner proves.

| Line | Declaration | Mark | Evidence |
| --: | --- | :-: | --- |
| 9 | what Leglas did itself outranks anything the agent said | R | Verdict order and "You stopped this run."; kept by September's audit. |
| 25 | a binary that never ran is not a provider problem | R | Spawn errors as `missing-agent`. |
| 30 | codex's refusal of an untrusted directory is named as itself | R | Verbatim codex-cli refusal and its message. |
| 45 | the vendor's own retry event decides an overload, a limit and a login | R | Status mapping and the retry count in the message. |
| 62 | output carries the verdict when no retry event does | R | Output patterns. |
| 74 | the last word wins, because that is the one it stopped for | R | Newest-first scan. |
| 85 | an agent that just exited gets an honest, quotable message | R | Message never quotes output (privacy). |
| 96 | a run that went quiet is ended by Leglas, and says so | R | Silence message with the ceiling in minutes. |
| 111 | only a session-shaped failure earns a second run | R | Every code but `agent-error` refuses the rerun; the runner tests reach two of them. |

## agents/process-tree.test.ts (72 lines, 4 declarations)

Owner `agents/process-tree.ts`, used by `runner.ts` and `generation.ts`.

| Line | Declaration | Mark | Evidence |
| --: | --- | :-: | --- |
| 27 | leads a group everywhere but Windows, where detaching opens a console | R | Windows row is reachable only here. |
| 35 | falls back to the process itself when there is no group to signal | R | ESRCH fallback; the real-process stop test only covers the group path. |
| 49 | a process that never started is only asked | D | Runner line 687 cancels a fake child with no pid and asserts it gets SIGTERM, this branch's only observable result. The one extra, that no group signal is tried, changes nothing: `kill(-undefined)` throws and falls back to the same call. |
| 59 | on Windows taskkill walks the tree, and the process is killed if it cannot | R | Windows path, reachable only here. |

## agents/runner.test.ts (1,708 lines, 36 declarations)

Owner `agents/runner.ts`, started by `server.ts`. These are boundary tests on `startRunner` with a fake spawn and a manual clock; #117 rewrote four of them with proofs. `server.test.ts` (L1) drives the runner over HTTP with a real custom agent for cancel and the live channel.

| Line | Declaration | Mark | Evidence |
| --: | --- | :-: | --- |
| 127 | reports state changes through the optional onChange hook | R | Rewritten by #117: the hook sees the state it reports. The L1 channel test counts changes and would pass a hook fired too early. |
| 156 | runs requests in queue order and never overlaps children | R | Order, one child at a time, spawn options with its own process group. |
| 197 | records a failed request as failed and never retries it | R | Durable failure and its message; no second run. |
| 231 | falls back to codex exec when the persistent app-server is unavailable | R | Keeper, as a table over Codex and Claude, for falling back to the CLI when the transport refuses; absorbs line 393. |
| 267 | cancels a persistent run before its synthetic child exists | R | Stop before a transport has a child. |
| 328 | runs Claude through the persistent Agent SDK transport | R | Turn input to the transport: images under the request's directory, effort, no session. |
| 393 | falls back to claude -p when the Agent SDK is unavailable | C | Into line 231's table: the same fallback branch in `runChild`, Claude row with its argv expectations. |
| 429 | yields while an external watcher is attached | R | Attached watcher goes first. |
| 454 | a finished run's session carries into the next request, cold after the cap | C | Into line 507, which already runs turns 1 to 10; its session-id expectation moves there (each resumed argv names the thread). Its whole-argv checks repeat `agents.test.ts` lines 33 and 322, and its name promised a cap it never reached. |
| 507 | the ninth request starts cold: eight turns is one session's whole life | R | Session cap; now also asserts the resumed thread id. |
| 542 | a failed resume that never edited retries cold, invisibly to the request | R | One invisible cold retry for a dead session. |
| 592 | a resume that edited and then failed is a real failure and ends the session | R | No rerun after an edit; keeper for the rule line 1300 replayed with Cursor. |
| 636 | a nudge starts immediately and survives a tick already in flight | R | Counted nudges; no run after stop. |
| 687 | cancels the active child with SIGTERM and treats the request as failed | R | Cancel by id, SIGTERM, saved as `cancelled`. |
| 725 | an overloaded provider is not answered with a second cold run | R | The verdict gate on the cold retry. |
| 776 | a cancelled request is recorded as cancelled, not as a failure to retry | D | Line 687 asserts the saved status `cancelled`, which `markFailed` writes only for code `cancelled`; `server.test.ts` "reports a running request and cancels it through the polled API" asserts the code and message through the API. |
| 804 | a child that will not go is stopped anyway, and the queue moves on | R | Rewritten by #117: SIGKILL escalation and nothing logged. |
| 863 | a stop reaches what the agent started, not only the agent | R | Real process tree; the only test of group signalling with real processes. |
| 913 | a run that goes quiet is described, then ended with a reason of its own | R | Notice and ceiling. |
| 968 | a stop that lands while a quiet run is being ended leaves its verdict alone | R | Verdict race. |
| 1009 | a child that errors on the way out keeps the %s's verdict (2 rows) | R | Error event after a chosen ending. |
| 1057 | an agent that keeps talking is never cut off, however long it runs | R | Silence is per gap, not total. |
| 1093 | a transport that never finishes starting is ended by the same ceiling | R | No CLI fallback after a hung transport. |
| 1138 | hands claude the registration allowance on a fork, and only on a fork | R | Keeper for the allowance; now one queue of a cold fork, a resumed fork and a change in place, each run's whole allowance asserted. |
| 1180 | a resumed fork carries the registration allowance too | C | Into line 1138: its resumed fork is the second request of the same queue. |
| 1218 | a fork that registers nothing fails instead of vanishing | R | `not-registered` and the next fork starts cold. |
| 1261 | a Cursor resume that died without editing is tried once more, cold | R | Delivery proof for Cursor's verified flag and its bare `session_id` events. |
| 1300 | a Cursor resume that edited and then died is not rerun | D | Composition: `agents.test.ts` line 511 reads the same `editToolCall` with a path under the project as `editing ...`, and line 592 proves an edited resume is not rerun. |
| 1413 | leaves every transport cold until something asks for it | R | No warm at boot. |
| 1439 | warming one vendor lets go of the other | R | One warm transport at a time. |
| 1466 | releases an idle transport and warms it again on the next ask | R | Idle release keeps the transport usable. |
| 1497 | a superseded warm-up does not fire a stale release | R | Rewritten by #117 with a timeline clock. |
| 1530 | a vendor kept warm through a switch is let go when its run ends | R | Keeper, as a two-row table (`when a run ends, %s stays warm`), for which vendor `releaseAllBut` keeps at a run's end. |
| 1575 | with nothing asked for since boot, the vendor that ran stays warm | C | Into line 1530's table: the same release at a run's end with nothing asked for. |
| 1616 | an ask warms the vendor for the conversation it will continue | R | Warm with the held session id. |
| 1657 | the idle release waits out a run in flight | R | Rewritten by #117 with a proof. |

## capture/browser.test.ts (941 lines, 32 declarations)

Owner `capture/browser.ts`. Callers: `server.ts` (pool), `cli` (reaper at start, from the bundle), `site/build.test.ts` (L3, real launch). `findBrowser`, `launchBrowser`, `createBrowserPool` and `reapOrphanedBrowsers` are in `api-surface.txt`.

| Line | Declaration | Mark | Evidence |
| --: | --- | :-: | --- |
| 29 | prefers the explicit Leglas and Chrome paths | C | Into one `findBrowser` search-order table: each expectation becomes a row with the same search input. |
| 54 | checks system then user applications on macOS | C | Same table, two rows. |
| 78 | checks PATH before fixed Linux locations | C | Same table, two rows. |
| 102 | checks each Windows program root | C | Same table, one row. It reads cache folders from the real disk as the old test did, which is the only proof that an unreadable cache folder holds no browser (the coverage run caught its loss when the table first stubbed every folder). |
| 118 | uses the newest Playwright and Puppeteer cache entries | C | Same table. Its name over-promised: only one build existed in each case, so it proved the path, not the order; the rows are named for the path, and line 197 keeps the order. |
| 146 | finds the Chrome for Testing the tools actually install today | C | Same table, one row (regression: the current Playwright layout). |
| 165 | finds the headless shell, which is often the only Chromium in a container | C | Same table, two rows. |
| 197 | prefers the newest build when several are cached | C | Same table, one row (numeric, not string, order). |
| 215 | honours the executable a test tool already points at | C | Same table, one row. |
| 228 | prefers a headless shell over a desktop browser on the same machine | C | Same table, two rows (the shell wins; an explicit choice still outranks it). |
| 258 | returns null when no supported browser exists | C | Same table, one row. |
| 347 | uses the required argv and frames page commands with their session | R | Launch argv and session framing. |
| 408 | serializes tabs and closes each target after work | R | One tab at a time; every target closed. |
| 438 | rejects pending commands when the socket closes | R | A dead socket retires the browser. |
| 466 | a command that never comes back retires the browser rather than the command | R | Regression: a silent socket made every queued capture pay its own timeout. |
| 496 | times out and kills a browser that never exposes CDP | R | Start deadline and SIGKILL. |
| 508 | a startup failure carries what the browser itself said | R | Keeper for the startup failure text; absorbs line 525. |
| 525 | includes the early exit code in a startup failure | C | Into line 508: the same `close` path; the merged test asserts the exit code and the browser's words in one message. |
| 559 | shares one launch and closes it after the last page goes idle | R | Shared launch and idle close. |
| 591 | retires a browser that lost its socket before launching a replacement | R | Dead browser closed, not leaked. |
| 625 | holds the browser open while other work is still outstanding | R | Regression measured against a real browser (one of six captures survived). |
| 674 | closing while a launch is still in flight closes what the launch returns | R | Close during launch. |
| 706 | reports no browser and retries a failed launch on the next acquire | R | `NO_BROWSER` text and retry. |
| 730 | launchBrowser with a real browser: evaluates JavaScript over CDP | D | `capture.test.ts` "renders a local page, crops its element and reads console errors" launches the same real browser through `launchBrowser` and evaluates over CDP through `withPage`; `site/build.test.ts` does too. |
| 792 | closes an orphan through the endpoint only its own browser answers | R | Security: close by the browser's own token, not by pid. |
| 822 | leaves a browser alone while its Leglas is still running | R | Two Leglas on one machine. |
| 838 | a dead endpoint costs nothing and still clears the directory | R | Cleanup without a live browser. |
| 854 | spares a profile whose record has not been written yet | R | Keeper for the grace period, as a two-row table with line 873. |
| 873 | clears a long-abandoned profile that never got a record | C | Into line 854: the other side of the same grace comparison. |
| 887 | never signals a process id, whatever the record says | R | Security; rewritten by #117 with a proof. |
| 913 | leaves another user's profile alone | R | Security: shared temp directory on Linux. |
| 932 | survives a temp directory it cannot read | R | Start never fails on an unreadable temp directory. |

## capture/capture.test.ts (1,036 lines, 19 declarations)

Owner `capture/capture.ts`, used by `server.ts` (capture route, render check). The fake-page tests own the timing logic; the real-browser tests own what Chrome does.

| Line | Declaration | Mark | Evidence |
| --: | --- | :-: | --- |
| 25 | pads a swept region and clamps it at the page edge | C | Into one `cropBox` table with lines 35 and 41; each case keeps its expected box. |
| 35 | grows a tiny element around its centre | C | Same table. |
| 41 | an element larger than the page becomes the page | C | Same table. |
| 147 | a picture for keeping that fails leaves the capture as it was | R | JPEG failure is not a capture failure. |
| 168 | takes one frame and ordered crops while collecting load errors | R | Width clamp, frame cap, crop order, recorded-rect fallback, one navigation. |
| 221 | a resource that failed to load is named by its path, and a missing favicon is not an error | R | Error text names the module (#110). |
| 248 | keeps hydration evidence after the console error cap | R | Hydration is read past the ten-error cap. |
| 275 | a note below the frame cap is cropped where it is, not where the frame ends | R | Crop bounds use the whole document. |
| 304 | a document the app could not serve is not a capture of the direction | R | 5xx refusal and its text. |
| 319 | throws a navigation error when the page does not load | R | `errorText` refusal and its text. |
| 342 | the shutter waits for what the page asked for after load, arrived or failed | D | The shutter table (line 382) proves `loadingFinished` and `loadingFailed` both release the wait (its "quickly arrived" and "failed script" rows) and that an image after load holds the shutter; the real-browser "page drawn after load" tests prove stylesheets, fonts and images. Removing `Stylesheet` from the tracked types passes this test and fails the real one. |
| 382 | the shutter $name (7 rows) | R | Post-load wait timing. |
| 514 | a script landing during the reveal wait gets its own window and its content gets a look | R | Second reveal window. |
| 603 | capturePage with a real browser: renders a local page, crops its element and reads console errors | R | Real Chrome capture; also the remaining live proof for `launchBrowser`. |
| 653 | a page measured for its layout: reports text that collides or is cut off | R | Real-browser proof for `LAYOUT_PROBE`, which runs only in the page and is invisible to coverage. |
| 768 | reports every finding on a crowded page | R | No cap on findings. |
| 818 | two captures of one design agree, even when the page fades itself in after load | R | Determinism of the settled frame. |
| 860 | a page drawn after load is shot with the script, stylesheet, web font and image it asked for | R | Real post-load wait. |
| 971 | is shot after a lazy script reveals its content | R | Real reveal window. |

## capture/hydration.test.ts (59 lines, 5 declarations)

Owner `capture/hydration.ts`, used by `capture.ts`.

| Line | Declaration | Mark | Evidence |
| --: | --- | :-: | --- |
| 6 | recognises %s evidence (13 rows) | R | Each framework's real wording. |
| 24 | does not mistake ordinary load noise for hydration evidence (7 rows) | R | False positives from stores and caches that "rehydrate". |
| 36 | returns the first match across a list without changing its message | R | First match wins, message unchanged. |
| 46 | keeps the first line of an exception and drops its stack | R | Stack trimming. |
| 56 | returns null for an empty list | D | No branch: the loop never runs and the function ends in `return null`, which the seven negative rows already assert. |

## generation/generation.test.ts (3,128 lines, 58 declarations)

Owners `generation/*.ts` and the generate routes in `server.ts`. Never audited: #110 added it after #117. Most lifecycle tests are regressions from named review rounds (a9bbfdf "stop means stopped", 7751806 attempt tokens, 9d61d0a stop and close wait for writes, 7386918 refusals while closing, 8ff6515 a draft that doesn't compile, 918630a strays). One test fails here only because root ignores `chmod 0o444`.

| Line | Declaration | Mark | Evidence |
| --: | --- | :-: | --- |
| 331 | a switch file gaining slots keeps every direction it had and adds one import and entry per slot | R | Exact import and `DIRECTIONS` lines the dev server compiles. |
| 344 | the facts a builder is given come from the project's stylesheet, public images and current direction | R | Facts contract. |
| 356 | describe each image with the alt text the app's code gives that image alone | R | Alt text only when tied to one image (regression list in the fixture). |
| 411 | read the app's code before its directions, and no direction the switch dropped | R | Source order for alt text. |
| 452 | say where a long direction was cut, so a build never takes it for the whole | R | Truncation marker text, singular and plural. |
| 475 | name the example as the direction being varied only when it was read from it | R | Prompt wording. |
| 490 | is refused, with the reason, for an agent Leglas cannot hold to time | R | HTTP 422 and its text; keeper, as a two-row table with line 505. |
| 505 | is refused for a surface with no switch, naming the command that makes one | C | Into line 490's table: the same route and status, its row naming the `leglas new` command. |
| 518 | builds variations of a direction named as the rail names it, with no brief needed | R | Route's base lookup and refusals, and the plan prompt for a variation. |
| 588 | a generation, end to end: plans, builds all at once, repairs a broken direction, stops one and replaces it | R | The end-to-end keeper with a real browser and dev server. |
| 963 | a direction stopped while its page is being rendered stays stopped | R | a9bbfdf. Keeper, as a two-row table with line 1337; the stop row keeps its clean report, which only the ownership check after a render stops. |
| 999 | a retry waits for the stopped build's process to be gone | R | Retry refused while the old run lives. |
| 1044 | a render that outlives a stop and a retry does not speak for the new attempt | R | 7751806, attempt tokens. |
| 1093 | a replace that loses its slot to a stop and a retry leaves the retry's work alone | R | Attempt tokens on replace. |
| 1152 | a stop while the directions go on the rail waits for them and lists them, stopped | R | Keeper for waiting on registration; absorbs line 1203. |
| 1203 | closing waits for directions still going on the rail, even after a stop | C | Into line 1152: the merged test stops and closes during the same held registration and asserts neither answers before it lands. |
| 1251 | a replace whose registration fails shows the error on the direction | R | Error surfaces on the slot. |
| 1299 | a render that throws fails that direction and its retry, not the whole set | R | Thrown render scoped to its slot. |
| 1337 | closing while a page is being rendered starts no fix run and puts the placeholder back | C | Into line 963's table as the closing row, with its error report; it now also asserts the direction reads stopped. |
| 1373 | a retry, a replace or a new set asked for while Leglas closes is refused and writes nothing | R | 7386918. |
| 1412 | a set that starts as Leglas closes starts no process | R | 7386918. |
| 1440 | a page broken by another direction still being written waits for it instead of blaming this one | R | 8ff6515. |
| 1491 | text still cut off after its fix run is kept on a direction that is ready | R | Layout-only fix prompt and kept findings. |
| 1523 | a layout fix that goes wrong puts back the direction it started from | R | Three ways a layout fix fails. |
| 1566 | a layout fix that strays is undone only when every file it touched can be put back | R | Baseline failure in this VM only (root ignores `chmod 0o444`); passes with `setpriv --inh-caps=-dac_override --bounding-set=-dac_override`. |
| 1647 | a failed draft goes back to the placeholder, so it cannot break the others' pages | R | 8ff6515. |
| 1677 | two drafts that fail their render check do not stop the rest | R | `broken` is an own failure, not a same-failure stop. |
| 1707 | a new idea's start is when it was asked for, not when its build began | R | de0b6d0. |
| 1742 | a generated direction carries its brief and its surface onto the rail | R | Registration provenance. |
| 1786 | a retry in an older set puts back the switch as it is now, not as that set found it | R | Retries read the switch fresh. |
| 1842 | every file a build strays into is put back, a stylesheet a direction imports among them | R | Keeper for restoring the switch and imports, plural message; covers line 2150's restore. |
| 1888 | an edit a stopped build makes on its way out is put back too | R | Strays after a stop. |
| 1932 | an edit on a stream's last line, with no newline after it, is still caught | R | Trailing line flush. |
| 1971 | a retry read while another build's stray is not yet put back keeps the good switch | R | Pending restore read as it will be. |
| 2033 | a stray into a direction another set is building is named, not put back | R | Never restore over a building direction. |
| 2092 | a direction whose page breaks because another build strayed waits for the fix instead of failing | R | Pending strays hold sibling checks. |
| 2150 | a build that edits the switch file is stopped, and the switch is put back | D | Line 1842 strays into the same switch from a hanging build and asserts it is stopped and restored; line 2197 asserts the singular "put the file back" message; line 1932 asserts the `outside-file` code. |
| 2197 | a fix run that edits a file a direction imports is stopped, and the file is put back | R | Strays from a fix run, message, still retryable. |
| 2262 | a building direction says what its build is doing | C | Into line 2300, which sends the same `Write` event and now asserts the label it produces. |
| 2300 | checking starts with no build step left over, and a fix run says what it is doing | R | Keeper for slot activity (7bb28f4). |
| 2375 | another direction finishing leaves a fix run's step on its cover | R | 9729be1. |
| 2452 | a planned direction never overwrites a file that is already there | R | a9bbfdf, `wx` and the folder check. |
| 2484 | variations are built from their direction's own file and sit under it on the rail | R | 7731dcd. |
| 2555 | a direction that failed to build cannot be varied until it is built | R | bcae0c0. |
| 2594 | two sets asked for at once start only one | R | d672a7e. |
| 2620 | a direction that is not in the switch cannot be varied, and nothing starts | R | Only test of `start`'s own switch check; the route refuses earlier for rail titles. |
| 2645 | the record of a set is kept unless the project turns records off | R | `recordSets: false` config. |
| 2678 | says how each run a stop ended: the plan's, a build's, a fix's and a new idea's | R | `endedAt` on each kind of run. |
| 2752 | keeps the newest hundred sets, and a new set makes room | R | Record pruning; keeper for line 2789, whose variation now makes the room. |
| 2789 | of variations whose direction's set was just let go brings none of it back | C | Into line 2752: the set that makes room varies the direction the oldest set built, and the test asserts the base reads as let go and the oldest folder stays gone. |
| 2836 | of variations names the set that built their direction, which notes them | R | `more-like` event. |
| 3044 | a build that edits a file of the app's own is stopped, and the file is named | R | Codex strays read from `file_change`. |
| 3056 | plans and builds with restricted Codex runs, reading its answer and its steps | R | Codex argv contract and activity; keeper for line 3091, so its run now includes a fix. |
| 3082 | switches off exactly the servers its config defines, however they are written | R | Exact server list from TOML variants. |
| 3091 | a page that fails its check gets a Codex fix run that may write | C | Into line 3056, whose first render now fails: the fix run's prompt and `-s workspace-write` are asserted there. |
| 3102 | a failed build says Codex failed, not Claude | R | Agent name in the message. |
| 3110 | its answer is the last agent message, whatever Codex reports around it | R | Result parsing past log lines. |
| 3125 | with no Codex config, no server is named | R | A missing config does not fail a Codex set. |

## Tally

Final marks, after the layer plan and the cutover. The cutover folded seven more same-contract pairs and deleted one more test; each is marked above.

| File | Decl. | R | F | C | D | Decl. after |
| --- | --: | --: | --: | --: | --: | --: |
| agent-command | 18 | 7 | 0 | 9 | 2 | 8 |
| agents | 38 | 25 | 0 | 8 | 5 | 26 |
| claude-agent-session | 15 | 12 | 0 | 3 | 0 | 12 |
| codex-app-server | 9 | 9 | 0 | 0 | 0 | 9 |
| failure | 9 | 9 | 0 | 0 | 0 | 9 |
| process-tree | 4 | 3 | 0 | 0 | 1 | 3 |
| runner | 36 | 30 | 0 | 4 | 2 | 30 |
| browser | 32 | 18 | 0 | 13 | 1 | 19 |
| capture | 19 | 15 | 0 | 3 | 1 | 16 |
| hydration | 5 | 4 | 0 | 0 | 1 | 4 |
| generation | 58 | 51 | 0 | 6 | 1 | 51 |
| **Lane** | **243** | **183** | **0** | **46** | **14** | **187** |

"Decl. after" counts each new table (`findBrowser` search order, `cropBox`, Cursor tool_call rows, template refusals) as one declaration.

## Layer plan

The ledger read declaration by declaration. This pass reads the lane by layer, looking for a suite that replays a stronger one.

### Layers and keepers

| Contract | Layers that test it | Keeper | Retired or narrowed |
| --- | --- | --- | --- |
| Claude and Codex activity labels | `activityFrom` units; `createGenerations` with fake CLIs; runner edited flag | `generation.test.ts` (Claude `Write`/`Edit`, Codex `file_change`), runner line 592 | `agents.test.ts` lines 466 and 483 |
| Cursor activity labels | `activityFrom` units only (the runner consumes the "editing" word) | `agents.test.ts` captured stream (line 511) and one table of synthetic rows | runner line 1300, which replayed the rule with Cursor's event |
| Vendor argv | exact argv units; runner checks of argv positions | `agents.test.ts` whole-argv tests (lines 33, 64, 322) | `agents.test.ts` lines 109 and 125; runner line 454's argv copies |
| Queue order and failed requests | `nextRequest` unit; runner boundary | runner for the embedded loop, one `nextRequest` test for the cli watch loop that runs from the bundle | four of the five `nextRequest` tests fold into one |
| Transport fallback | runner with refusing stub transports | runner, one table over Codex and Claude | runner line 393 |
| Cancel verdict | runner unit; `server.test.ts` over HTTP | runner line 687 for the status, `server.test.ts` for code and message | runner line 776 |
| Saved custom template | `saveAgentChoice` unit; `server.test.ts` over HTTP | `server.test.ts` round trip | `agents.test.ts` line 738 |
| Real Chrome over CDP | `browser.test.ts` live; `capture.test.ts` live; `site/build.test.ts` | `capture.test.ts` live capture | `browser.test.ts` live test |
| Post-load shutter | fake-page unit; shutter table; real-browser pages | shutter table for timing, real-browser tests for asset types | `capture.test.ts` line 342 |
| Stray restore and message | four generation tests on the switch | line 1842 (restore, plural), line 2197 (singular), line 1932 (code) | line 2150 |
| Close and stop wait for registration | two generation tests with the same held registration | line 1152 | line 1203 folds in |

No whole file retires: each file owns at least one contract no other layer reaches (the transports are reached in production only through the runner, whose tests stub them).

### Assertions carried into keepers

- `agent-command.test.ts`: single quotes and attached quotes into the double-quote test; the shell-punctuation prompt into the one-argv-entry test; failed-set skipping and the empty answer into the queue-order test.
- `agents.test.ts`: the two captured Cursor status answers into the `authVerdict` table; Cursor's resume argv into the resume test; the `api_retry` negatives into the positive test; the single-quoted unwrap into the command table; four synthetic Cursor events into one table.
- `claude-agent-session.test.ts`: the `resume` option on an unwarmed run and the effort applied to a rotated process into the rotation test; the reverse warm replacement into the forward one.
- `runner.test.ts`: the Claude fallback row into the fallback table; the resumed thread id into the session-cap test.
- `browser.test.ts`: every `findBrowser` expectation into one search-order table; the exit code into the startup-failure test; the abandoned-profile side into the grace-period test.
- `capture.test.ts`: the three `cropBox` cases into one table.
- `generation.test.ts`: close's wait into the stop-during-registration test; the build-step label into the checking-activity test.

### Shared setup

Most of the lane's lines are setup repeated per test, not assertions. With the plan above applied, each file's repeated setup goes into one helper in that file (nothing shared across lanes, and `test-helpers.ts` is untouched):

- `runner.test.ts`: a project with a saved choice and queued requests, started on the manual clock and fake spawn.
- `generation.test.ts`: the one-concept fixture, the clean render, starting a set and waiting on a slot's state.
- `claude-agent-session.test.ts`: ending a turn with a result and waiting for its close.
- `codex-app-server.test.ts`: answering `thread/start` and `turn/start` for a turn.
- `capture.test.ts`: a browser over one fake page, and a real page served for the live tests.
- `browser.test.ts`: the reaper's removal log.

### Production seams

None unlocked. Every injection point the retired tests used is still used by a kept test (`execProbe` and its deadline by line 206 and the live checks, `LaunchOptions` by the launch tests, `RunnerOptions.setTimeout` and `now` by the silence and warm tests), and every export has a production caller or sits in `api-surface.txt`. Production lines do not change.

## Cutover result

Measured on the final head against `main` d7c72d9.

| File | Lines before | Lines after | Declarations before | Declarations after |
| --- | --: | --: | --: | --: |
| agents/agent-command.test.ts | 144 | 113 | 18 | 8 |
| agents/agents.test.ts | 756 | 631 | 38 | 26 |
| agents/claude-agent-session.test.ts | 628 | 507 | 15 | 12 |
| agents/codex-app-server.test.ts | 416 | 404 | 9 | 9 |
| agents/failure.test.ts | 128 | 128 | 9 | 9 |
| agents/process-tree.test.ts | 72 | 62 | 4 | 3 |
| agents/runner.test.ts | 1,708 | 1,235 | 36 | 30 |
| capture/browser.test.ts | 941 | 827 | 32 | 19 |
| capture/capture.test.ts | 1,036 | 926 | 19 | 16 |
| capture/hydration.test.ts | 59 | 55 | 5 | 4 |
| generation/generation.test.ts | 3,128 | 2,467 | 58 | 51 |
| **Lane** | **9,016** | **7,355** | **243** | **187** |

- Test lines: 1,661 removed (18.4%), 142 short of the 1,803 target. Declarations: 56 removed (23%). Cases run: 275 to 255.
- Where the lines came from: the 14 deleted tests held 279 lines; the 46 folded tests held 885 lines, whose assertions now sit in keepers and tables; the rest is shared setup written once per file (`boot` in the runner tests, `startSet` and `firstSlot` in the generation tests, a turn-ending helper, a request-answering helper, a fake browser and a live page helper).
- Production lines: unchanged. No production file is touched; no seam was unlocked (see the layer plan).
- Support files: `server/src/test-helpers.ts` untouched; no test outside the lane touched.

### Why the target is not met

The remaining 142 lines would have to come from tests the retention bar keeps: regressions from named review rounds in `generation.test.ts` (the attempt tokens, stop and close waiting for writes, refusals while closing, strays), the real-browser proofs in `capture.test.ts` (the layout probe and post-load waits, which coverage cannot see because they run in the page), September's keeps and rewrites in the runner and transports, the opt-in live agent checks CONTRIBUTING names, and Windows paths reachable only through their injected seams. Further setup folding was tried and paid one line per edit (an options object for the generation stand-in saved one line and was dropped).

## Coverage

`pnpm test:coverage` on the final head, run as the baseline was: 4 failed, 2 skipped, 2 errors, 1,839 passed (the baseline's 1,859 less the lane's 20 deleted cases).

| Scope | Lines | Branches | Functions | Statements |
| --- | --- | --- | --- | --- |
| Total | 82.14 to 82.13 | 72.59 to 72.59 | 75.09 to 75.05 | 79.47 to 79.46 |
| server | 91.88 to 91.85 | 81.44 to 81.44 | 87.27 to 87.20 | 88.86 to 88.83 |
| server/agents | 90.00 to 90.00 | 78.71 to 78.71 | 86.45 to 86.45 | 85.81 to 85.81 |
| server/generation | 93.77 to 93.77 | 78.95 to 78.95 | 89.33 to 89.33 | 90.63 to 90.63 |
| server/capture | 93.14 to 92.79 | 82.99 to 82.99 | 82.71 to 82.09 | 90.97 to 90.67 |

Every other package is unchanged. No production file lost more than 5 points.

Files that lost a covered line, branch, function or statement:

- `capture/browser.ts`: lines 353 to 351, functions 93 to 92, statements 397 to 395. The lines are the body of the one-second timer in `close` (lines 889 and 890) that kills a browser still alive after `Browser.close`. It ran at baseline only because the deleted live test (`launchBrowser with a real browser`) closed its browser with seconds of the file still to run; the capture live tests close theirs in `afterAll`, as the file ends. No test asserted the timer before or after, and its kill branch was uncovered at baseline too. Accepted as timing, the same kind as the baseline's unstable counter at line 882.
- The first coverage run also lost `readableDirectories` (lines 158 to 162): the new `findBrowser` table stubbed every cache folder, while the old Windows test read the real disk. Restored in 999c5b8 (rows read the real disk unless they name a cache) and proven by the `browser unreadable cache` break below.

## Deliberate breaks

Every consolidation that moved an assertion into a keeper, and the one assertion restored after the coverage run, was checked by breaking its production owner, running the keeper and restoring the source. `campaign/breaks-L2.py` makes each break and checks the owner's sha256 after restoring; `campaign/breaks-L2.json` holds the run. All 28 went red and all 28 owners were restored byte for byte (`git status` clean afterwards).

| Break | Owner | What it simulates | Keeper (`-t` filter) | Result with the break | Restored |
| --- | --- | --- | --- | --- | :-: |
| agent-command quotes | `agents/agent-command.ts` | single quotes are no longer quotes | `agents/agent-command.test.ts` "keeps a quoted value together" | red: 1 failed, 10 skipped (11); expected [ '--note', '\'two', 'words\'', ...(1) ] to deeply equal [ '--note', 'two words', '{prompt}' ] | yes |
| agent-command punctuation | `agents/agent-command.ts` | the prompt is escaped for a shell that is not there | `agents/agent-command.test.ts` "puts the whole prompt in one argv entry" | red: 1 failed, 10 skipped (11); expected [ '-p', ...(1) ] to deeply equal [ '-p', ...(1) ] | yes |
| agent-command failed set | `agents/agent-command.ts` | a failed request is handed out again | `agents/agent-command.test.ts` "takes the first queued request in order" | red: 1 failed, 10 skipped (11); expected 'a' to be 'b' | yes |
| agent-command refusals | `agents/agent-command.ts` | a placeholder glued after a word is let through | `agents/agent-command.test.ts` "refuses" | red: 1 failed, 4 passed, 6 skipped (11); expected a refusal for "claude --message={prompt}" | yes |
| agents cursor verdict | `agents/agents.ts` | Cursor's signed-out answer is read as signed in | `agents/agents.test.ts` "verdict reads its own CLI honestly" | red: 1 failed, 5 passed, 37 skipped (43); expected 'ok' to be 'signed-out' | yes |
| agents cursor resume | `agents/agents.ts` | a resumed Cursor run stops at the trust prompt | `agents/agents.test.ts` "resume argv continues the session" | red: 1 failed, 42 skipped (43); expected [ '-p', '--resume', 'chat_1', ...(3) ] to deeply equal [ '-p', '--resume', 'chat_1', ...(4) ] | yes |
| agents retry negatives | `agents/agents.ts` | any system line reads as a retry | `agents/agents.test.ts` "reads the api_retry event" | red: 1 failed, 42 skipped (43); expected { attempt: 1, max: null, ...(2) } to be null | yes |
| agents single-quote unwrap | `agents/agents.ts` | a single-quoted shell command keeps its quotes | `agents/agents.test.ts` "cleans command text" | red: 1 failed, 6 passed, 36 skipped (43); expected 'running \'npm test\'' to be 'running npm test' | yes |
| agents cursor rows | `agents/agents.ts` | the first key of the wrapper is read as the tool | `agents/agents.test.ts` "reads a Cursor tool_call" | red: 1 failed, 4 passed, 38 skipped (43); expected 'using toolCallId' to be 'editing src/Hero.tsx' | yes |
| claude unwarmed resume | `agents/claude-agent-session.ts` | a run naming a session with nothing warmed starts fresh | `agents/claude-agent-session.test.ts` "a fresh turn after a resumed conversation" | red: 1 failed, 11 skipped (12); expected undefined to be 'claude_5' | yes |
| claude rotated effort | `agents/claude-agent-session.ts` | a new process is assumed to carry the old process's effort | `agents/claude-agent-session.test.ts` "a fresh turn after a resumed conversation" | red: 1 failed, 11 skipped (12); expected [] to deeply equal [ { effortLevel: 'high' } ] | yes |
| claude replacement reverse | `agents/claude-agent-session.ts` | a handle warmed for a session serves a fresh request | `agents/claude-agent-session.test.ts` "a handle warmed for another conversation" | red: 1 failed, 11 skipped (12); expected [ { options: { ...(7) }, ...(1) } ] to have a length of 2 but got 1 | yes |
| runner claude fallback | `agents/runner.ts` | only Codex falls back to its CLI | `agents/runner.test.ts` "falls back to the" | red: 1 failed, 1 passed, 31 skipped (33); condition never held | yes |
| runner resumed thread | `agents/runner.ts` | a new session's id never replaces the old one | `agents/runner.test.ts` "the ninth request starts cold" | red: 1 failed, 32 skipped (33); expected [ 10, 'resume', 'th_1' ] to deeply equal [ 10, 'resume', 'th_2' ] | yes |
| runner resumed fork allowance | `agents/runner.ts` | a resumed fork loses its allowance | `agents/runner.test.ts` "hands claude the registration allowance" | red: 1 failed, 32 skipped (33); expected [] to deeply equal [ 'Bash(npx -y leglas show *)', ...(1) ] | yes |
| runner warm after run | `agents/runner.ts` | the vendor that ran stays warm over the one asked for | `agents/runner.test.ts` "when a run ends" | red: 1 failed, 1 passed, 31 skipped (33); condition never held | yes |
| browser explicit order | `capture/browser.ts` | CHROME_PATH outranks LEGLAS_BROWSER | `capture/browser.test.ts` "finds LEGLAS_BROWSER before CHROME_PATH" | red: 1 failed, 35 skipped (36); expected '/chosen/chrome' to be '/chosen/leglas' | yes |
| browser shell first | `capture/browser.ts` | a desktop browser wins over a headless shell | `capture/browser.test.ts` "finds a headless shell before a desktop browser" | red: 1 failed, 35 skipped (36); expected '/Applications/Google Chrome.app/Conte...' to be '/Users/u/Library/Caches/ms-playwright...' | yes |
| browser exit code | `capture/browser.ts` | the exit code is dropped from the startup failure | `capture/browser.test.ts` "a startup failure carries its exit code" | red: 1 failed, 35 skipped (36); expected [Function] to throw error including 'exit code 17' but got 'The browser did not start. It said: F...' | yes |
| browser grace | `capture/browser.ts` | the grace period is read backwards | `capture/browser.test.ts` "profile" | red: 2 failed, 1 passed, 33 skipped (36); expected [ '/tmp/leglas-browser-halfborn' ] to deeply equal [] | yes |
| browser unreadable cache | `capture/browser.ts` | a cache folder that can't be read fails the search | `capture/browser.test.ts` "finds each Windows program root" | red: 1 failed, 35 skipped (36); ENOENT: no such file or directory, scandir 'C:\Users\u/.cache/ms-playwright' | yes |
| capture cropBox region | `capture/capture.ts` | a swept region is ignored | `capture/capture.test.ts` "cropBox" | red: 1 failed, 2 passed, 21 skipped (24); expected { x: +0, y: +0, width: 448, ...(1) } to deeply equal { x: +0, y: +0, width: 320, ...(1) } | yes |
| generation late render | `generation/generation.ts` | a render that outlives a stop or close still speaks for the slot | `generation/generation.test.ts` "while a page is being rendered" | red: 1 failed, 1 passed, 51 skipped (53); expected 'ready' to be 'stopped' | yes |
| generation close drain | `generation/generation.ts` | close stops waiting for writes under way | `generation/generation.test.ts` "a stop and a close while the directions go on the rail" | red: 1 failed, 52 skipped (53); expected [ 'close' ] to deeply equal [] | yes |
| generation build activity | `generation/generation.ts` | a build's step names its file from the wrong folder | `generation/generation.test.ts` "a build and its fix run say what they are doing" | red: 1 failed, 52 skipped (53); expected { key: 'hero-ledger', ...(10) } to match object { state: 'building', ...(1) } | yes |
| generation prune order | `generation/generation.ts` | the base is looked up before the prune lets it go | `generation/generation.test.ts` "keeps the newest hundred sets" | red: 1 failed, 52 skipped (53); expected [ 'gen-loyw3v28', ...(100) ] to have a length of 100 but got 101 | yes |
| generation codex fix sandbox | `generation/generation.ts` | a fix run gets the read-only planner's sandbox | `generation/generation.test.ts` "plans, builds and fixes with restricted Codex runs" | red: 1 failed, 52 skipped (53); expected 'exec --json --ephemeral --skip-git-re...' to contain '-s workspace-write' | yes |
| generation agent refusal | `generation/generation.ts` | Cursor is let through to build directions | `generation/generation.test.ts` "is refused for" | red: 1 failed, 1 passed, 51 skipped (53); expected 202 to be 422 | yes |

The first run of these breaks found one gap of this campaign's own making: `generation late render` stayed green, because the merged stop and close test sent both rows an error report, whose path has a second ownership guard. The original stop test used a clean report, which reaches the ready state with no other guard. 1e15458 gives each row its original report; the break now goes red on the stop row.

## Baseline failure in this lane

`generation.test.ts` "a layout fix that strays is undone only when every file it touched can be put back" fails here and passes on CI. It is environmental, not a product bug: the suite runs as root, and `chmod 0o444` does not stop root writing the file back, so the locked case reads `ready`. Reproduction on this head:

```sh
npx vitest run packages/server/src/generation/generation.test.ts -t "a layout fix that strays"                  # 1 failed
setpriv --inh-caps=-dac_override --bounding-set=-dac_override \
  npx vitest run packages/server/src/generation/generation.test.ts -t "a layout fix that strays"                # 1 passed
```

The whole generation file passes (53 of 53) under the same `setpriv`. Nothing to fix in the owner, and the test stays as it is.

## Retained candidates that looked deletable

- `agents.test.ts` "only a vendor whose output Leglas has read reports edits it can act on": restates declared flags, a junk pattern, but September's audit kept it as the only test catching the custom-agent rule, and it is the only guard of Claude's flag (the runner's rerun tests use Codex and Cursor).
- `runner.test.ts` "a Cursor resume that died without editing is tried once more, cold": composes units like the deleted Cursor-edited test, but it is the delivery proof for Cursor's verified flag; without it that flag has only the restating test.
- `runner.test.ts` "cancels the active child with SIGTERM": `server.test.ts` (L1) covers the refusal and the saved verdict, but only this test proves the first signal is SIGTERM, not SIGKILL.
- `capture.test.ts` "takes one frame and ordered crops": the live capture runs the same path, but only this one proves the width clamp, the frame cap and the recorded-rect fallback.
- The facts tests in `generation.test.ts`: the end-to-end test checks three facts in the prompt; these hold the alt-text rules, truncation marker and dependency list.
- `agents.test.ts` live checks (two declarations): never run in CI or here, kept because CONTRIBUTING sends people to them before changing how a login is read.
- `process-tree.test.ts` Windows tests and `failure.test.ts`: small, and each owns a branch nothing else reaches.

## For the preservation review

Start with these, where a deletion or fold rests on reading rather than a break:

1. `agents.test.ts` lines 466 and 483 (Claude and Codex activity labels), deleted on the strength of `generation.test.ts`; check that the generation assertions name the same labels.
2. `runner.test.ts` line 1300 (Cursor edited, not rerun), deleted as a composition of `agents.test.ts` line 511 and runner line 592.
3. `runner.test.ts` line 776 and `agents.test.ts` line 738, deleted for L1 tests in `server.test.ts`. Lane L1 prunes that file at the same time: if it removes "reports a running request and cancels it through the polled API" or "reports available agents and round-trips the saved choice", restore these two.
4. `capture.test.ts` line 342 (the shutter waits for an arrived and a failed request), deleted for the shutter table and the real-browser tests, which skip without a browser.
5. `browser.test.ts` live test, deleted for the capture live tests; both skip without a browser, and `site/build.test.ts` (L3) also launches one.
6. `process-tree.test.ts` line 49, deleted for the runner's cancel test.
7. The `agent-command.test.ts` refusal table now also asserts every refusal is one line; that is new for three rows, true of the source today and taken from the cli's one-line printing.
