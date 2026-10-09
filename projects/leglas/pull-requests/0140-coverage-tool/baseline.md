# Test campaign baseline

Step 1 of the test-pruning campaign: the numbers every lane compares against. Measured at `main` d7c72d9 with `pnpm test:coverage`. Full data, per file, is in `baseline.json` next to this file. This folder is temporary and is stripped before any PR.

## Reproduce it

The cloud image needs three things before the suite runs as it does here:

```sh
nvm install 24                      # the image ships Node 22; source the image's nvm.sh first if nvm is not a command
pnpm install --frozen-lockfile
# Chromium refuses to start as root without --no-sandbox, and Leglas does not pass it.
wrapper="$(mktemp -d)/chromium"
printf '#!/bin/sh\nexec "%s" --no-sandbox "$@"\n' "$PLAYWRIGHT_BROWSERS_PATH/chromium" > "$wrapper"
chmod +x "$wrapper"
LEGLAS_BROWSER="$wrapper" pnpm test:coverage
```

A run is comparable only if it shows the same **4 failed, 2 skipped and 2 errors** as the baseline (1859 passed, which falls only by the cases a lane deleted). More than 2 skipped means no browser was found: the real-browser tests skip instead of failing and coverage drops by about 0.4 points.

Then compare against the baseline (totals, per package and every file that lost a covered line, branch, function or statement):

```sh
node -e '
const b = require("./campaign/baseline.json"), s = require("./coverage/coverage-summary.json");
const root = process.cwd() + "/", M = ["lines", "branches", "functions", "statements"];
const pkg = (f) => /^packages\/([^/]+)\//.exec(f)?.[1] ?? f.split("/")[0];
const sum = {};
for (const [abs, e] of Object.entries(s)) if (abs !== "total") for (const m of M) {
  const p = ((sum[pkg(abs.replace(root, ""))] ??= {})[m] ??= [0, 0]); p[0] += e[m].covered; p[1] += e[m].total;
}
const pct = (c, t) => (t > 0 ? Math.floor((1e5 * c) / t / 10) / 100 : 100);
for (const m of M) console.log("total", m, b.coverage.total[m].pct, "->", s.total[m].pct);
for (const [p, g] of Object.entries(b.coverage.byPackage))
  console.log(p, M.map((m) => `${m} ${g[m].pct} -> ${pct(...(sum[p]?.[m] ?? [0, 1]))}`).join(", "));
for (const [f, base] of Object.entries(b.files)) {
  const now = s[root + f];
  const lost = M.filter((m) => !now || now[m].covered < base[m][0]);
  if (lost.length) console.log("lost in", f, lost.map((m) => `${m} ${base[m][0]} -> ${now?.[m].covered ?? "gone"}`).join(", "));
}'
```

The baseline run has every known timing race in its unhit state, so a race can only show as a gain. Any `lost in` line is a real loss.

## Coverage

169 production files: `packages/*/src`, `site` and `scripts`, without tests, the two `test-helpers.ts` modules, `dist`, `evals` and worktree folders. Every file counts, so one whose tests are all deleted reads 0% instead of leaving the denominator (checked: excluding `naming.test.ts` keeps 169 files and `naming.ts` drops from 9 to 1 covered lines).

| Scope | Files | Lines | Branches | Functions | Statements |
| --- | --: | --: | --: | --: | --: |
| **Total** | 169 | **82.14** (9793/11921) | **72.59** (7852/10816) | **75.09** (2237/2979) | **79.47** (11067/13925) |
| cli | 34 | 77.82 | 73.50 | 77.63 | 76.02 |
| mcp | 7 | 86.63 | 84.96 | 77.92 | 85.29 |
| server | 42 | 91.88 | 81.44 | 87.27 | 88.86 |
| shell | 79 | 66.03 | 58.53 | 59.09 | 63.74 |
| site | 6 | 98.02 | 85.79 | 97.29 | 96.79 |
| scripts | 1 | 93.80 | 82.71 | 100.00 | 93.79 |

| Folder | Files | Lines | Branches | Functions | Statements |
| --- | --: | --: | --: | --: | --: |
| server/src (root) | 10 | 90.96 | 84.07 | 87.50 | 89.30 |
| server/agents | 8 | 90.00 | 78.71 | 86.45 | 85.81 |
| server/branches | 3 | 95.13 | 84.11 | 85.48 | 92.92 |
| server/capture | 4 | 93.14 | 82.99 | 82.71 | 90.97 |
| server/config | 5 | 94.14 | 90.09 | 93.10 | 93.02 |
| server/generation | 7 | 93.77 | 78.95 | 89.33 | 90.63 |
| server/requests | 3 | 94.62 | 83.55 | 89.52 | 91.32 |
| server/share | 2 | 90.61 | 75.40 | 88.05 | 85.18 |
| shell/src (root) | 13 | 61.65 | 54.85 | 54.47 | 58.95 |
| shell/agents | 6 | 79.14 | 76.20 | 77.61 | 78.06 |
| shell/annotate | 4 | 26.08 | 21.08 | 28.23 | 26.23 |
| shell/composer | 4 | 57.14 | 61.76 | 66.66 | 57.14 |
| shell/generation | 6 | 95.61 | 86.13 | 90.00 | 92.75 |
| shell/lineage | 5 | 87.96 | 72.99 | 83.33 | 86.04 |
| shell/net | 4 | 95.00 | 77.77 | 86.48 | 90.00 |
| shell/preview | 8 | 86.22 | 80.28 | 93.10 | 83.66 |
| shell/rail | 7 | 44.02 | 55.70 | 35.55 | 40.78 |
| shell/references | 3 | 77.04 | 63.49 | 71.42 | 78.08 |
| shell/share | 5 | 54.26 | 44.82 | 39.47 | 53.79 |
| shell/stage | 2 | 57.69 | 65.93 | 44.44 | 50.00 |
| shell/ui | 8 | 76.14 | 68.07 | 73.13 | 74.12 |
| shell/update | 4 | 70.23 | 63.44 | 52.27 | 67.00 |

Nine files already sit at 0% (both `bin.ts` entry points, four `cli/run-*.ts` modules, `App.tsx`, `main.tsx` and `DeleteRemovedDialog.tsx`); eight have no executable code.

## Stability

Five full coverage runs. Three gave identical totals; the largest spread was 0.034 points (functions). The counters that moved are all timing races, listed with lines in `baseline.json`: a double-close guard in `proxy.ts`, a health probe resolving after shutdown in `server.ts`, a rejected `Browser.close` and the orphan-profile reaper in `capture/browser.ts`. The reaper never flipped in a full run but did in 2 of 3 runs of L2 alone. If every known race flipped at once the totals would move by 0.075 (lines), 0.037 (branches), 0.134 (functions) and 0.065 (statements) points. Pass or fail for every test file was identical across all seven full runs (five with coverage, two without).

## Baseline failures

All four are environmental and deterministic here; none is a product bug.

| Lane | Test | Reason |
| --- | --- | --- |
| L1 | `proxy.test.ts` › reaches a target that is an IPv6 literal | The VM kernel has no IPv6, so listening on `::1` fails (`EAFNOSUPPORT`) and the test times out |
| L1 | `server.test.ts` › reports the dev server as reachable when it is up on ::1 | Same, no IPv6 |
| L1 | `branches/worktree.test.ts` › finds a dev server listening on IPv6 only | Same, the IPv6-only fixture dev server exits 1 |
| L2 | `generation/generation.test.ts` › a layout fix that strays is undone only when every file it touched can be put back | The suite runs as root and `chmod 0o444` does not stop root, so the locked row reads `ready`. It passes with `CAP_DAC_OVERRIDE` dropped (`setpriv --inh-caps=-dac_override --bounding-set=-dac_override`) and fails without |

The 2 unhandled errors are the same `listen EAFNOSUPPORT ::1` from the first two. The 2 skipped cases are the live agent CLI checks in `agents/agents.test.ts`, which need `LEGLAS_LIVE_AGENTS`; CI skips them too.

## Lanes

| Lane | Test files | Test lines | Support lines | Declarations | Cases run | Failures | Statements only this lane hits |
| --- | --: | --: | --: | --: | --: | --: | --: |
| L1 server core | 22 | 11,415 | 40 | 498 | 619 | 3 | 2,573 |
| L2 server engines | 11 | 9,016 | 0 | 243 | 275 | 1 | 2,023 |
| L3 cli, mcp, site, scripts, test | 37 | 8,329 | 12 | 414 | 471 | 0 | 2,193 |
| L4 shell | 35 | 6,927 | 0 | 488 | 500 | 0 | 2,738 |
| **Total** | **105** | **35,687** | **52** | **1,643** | **1,865** | **4** | |

Declarations are outermost `it`/`test` calls (an `it.each` or `test.skipIf(...)` counts once), counted from the AST; a line-start regex gives the same 1,643 per file. Cases run is what Vitest executes after expanding tables. Support is `server/src/test-helpers.ts` (L1, but imported by L1, L2 and L3 tests, so edits to it go through one owner) and `cli/src/test-helpers.ts` (L3).

"Only this lane hits" comes from running each lane's tests alone with coverage. It is the most coverage a lane can lose by itself. 1,223 more statements are hit by L1 and L2 and nobody else: if both lanes prune the tests that reach them, neither sees the loss alone. Only a run of the merged lanes does.

## Cross-package coverage

Confirmed: each package's `src` coverage comes from its own tests. Packages import each other through their exports, which point at built `dist` with no source maps, so code reached that way counts nowhere. The exceptions are tests that import another package's source directly: `site/build.test.ts` imports `server/src/capture/browser.ts`, `mcp/src/tools.test.ts` imports server request and server-info modules, `mcp/src/parity.test.ts` imports `cli/src/help.ts` and `server/src/live.ts`, and three cli tests and `mcp/src/tools.test.ts` import `shell/src/link.ts`. All of that is also covered by the owning package's tests, except 2 statements in `shell/src/net/live.ts` that only server (L1) tests reach.

## Coverage-blind tests

Coverage cannot protect these: deleting them changes no number.

- `cli/src/run-watch.test.ts` › leglas watch --json, as a process › stdout is JSON lines while the agent's output goes to stderr: starts the built cli bin in a child process.
- `mcp/src/tools.test.ts` › what the tools tell a host about themselves › the published server's instructions name every tool it lists, and fit what a host keeps: starts the built mcp bin over stdio.
- `site/release-notes.test.ts` › prints %s from any working directory (2 rows) and a missing version exits with the specified sentence: run `release-notes.ts` as a script in a child process.
- Any mcp test that reaches cli or server code, and any cli test that reaches server code (`run.test.ts` starts a real server): that code runs from the built bundles.

The server tests that spawn processes (the agents runner, generation, branches worktree and capture tests) start fixture scripts, git or Chrome. The production code that drives them runs in-process and is measured.

## Is v8 coverage a sound guardrail here?

As a tripwire for "the last test that runs this code is gone", yes: it is deterministic to within 0.134 points, covers every production file and the per-file comparison above catches a single deleted test file. As the only guardrail it is weak in five ways:

1. It measures execution, not assertion. A test can be the only one checking a behavior while a broad integration test (`server.test.ts`, `share.test.ts`) still runs the same lines. Deleting it changes nothing here, so the ledger's "stronger remaining proof" has to carry that.
2. Two points is coarse: about 238 lines or 216 branches of the total. Deleting `naming.test.ts` moved the totals by 0.04 to 0.12 points while `naming.ts` lost almost all of its coverage. Whole small folders could go dark inside the bar, so judge the per-package and per-file output too.
3. It is blind to the child-process and bundle paths above.
4. It depends on the environment: the browser (0.4 points), and the IPv6 and root failures leave their paths unmeasured here (CI has IPv6 and a non-root user, so its number would be slightly higher).
5. If a lane deletes test-only production code, the denominator shrinks and percentages can rise while protection falls. Compare covered counts per file as well as percentages.

## Wall time

`pnpm test:coverage`: 55.4 to 56.2 s, of which about 5 s is `pnpm build`; Vitest itself took 50.1 to 50.8 s. `pnpm test` took 47.4 s (Vitest) on this branch and 50.7 s on `main`, so coverage adds no measurable time. On this machine (4 CPUs) the IPv6 timeouts hold `server.test.ts` at 34 s and `proxy.test.ts` at 20 s.
