# Lane L3 ledger: cli, mcp, site, scripts, test

Steps 2 to 5 of the test-pruning campaign for lane L3. Base: `cloud/test-baseline-3ruyq4` at 516ace2 (`main` d7c72d9 plus coverage and the baseline). Line numbers are the base's.

Lane at baseline: 37 test files, 8,329 lines, 414 declarations, plus `packages/cli/src/test-helpers.ts` (12 lines).

Marks, as the test-audit skill defines them:

- **R** retain. The contract and the bug it catches. "R, compact" means the assertions are unchanged and only the call scaffolding moved into a helper in the same file.
- **F** retain the contract, repair the test.
- **C** consolidate. Names the keeper that absorbs every assertion. A row in a table keeps the flag or input under test and the assertion of the test it replaces; incidental values (a title, a url) may be shared between rows.
- **D** delete. Names the proof that remains, or why no contract exists.

`api-surface.txt` is read-only for this lane. Seams it lists stay even where only tests use them (see the end).

## Reading the lane

- The September audit (#112 cli, #113 mcp/site/scripts) already deleted every test Stryker showed redundant and rewrote the ones that tested structure. What is left is mostly boundary tests that each own one behavior, so honest deletions are few.
- The bulk of the lane's size is repetition, not redundancy: `parseArgs` tests that spend nine lines (parse, narrow, `if (kind !== x) return`, the readable-spacing blank lines) on one field; the eight-field `AddPreview` literal copied into six files; `runShare` and `runShow` calls that take six to ten lines each; unit tables written as one test per row.
- **Is the 1,666-line target reachable without breaking the retention bar?** No. Written before cutover, this section said yes through consolidation; the cutover showed otherwise. Deletions (D) yield 64 lines, consolidation into tables and stronger siblings (C) and shared setup (R, compact) about 1,075 more, and several planned folds came out longer than the tests they replaced (the `hostProject` table, a restart harness), so they were reverted. The lane lands at 1,157 lines (13.9%). The remaining 509 lines would have to come from tests that are each the only proof of their contract (see Results).

## packages/cli/src/args.test.ts (683 lines, 65)

Keepers after cutover: **K-args-take** is two tables, `parseArgs › parses %j exactly` (`toEqual`, for every row whose test used `toEqual`, and the help and version rows) and `parseArgs › takes %j` (`toMatchObject`, for the rows that checked fields). **K-args-refuse** is `parseArgs › refuses %j, saying why` (argv and the message: exact where the test was exact, `stringContaining` where it checked a substring, `any(String)` where it checked only the kind). The `--help` table stays.

`mcp/parity.test.ts` also proves every command refuses every flag it does not list, but it imports `parseArgs` from the built bundle, so it is coverage-blind for `args.ts`; the refusal rows stay here.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 14 | runs with defaults when given nothing | C | Row `[]` in K-args-take, full `toEqual` on the run options as before. |
| 26 | takes the Leglas port | C | Row `--port 4200` in K-args-take. |
| 30 | takes the target dev server port | C | Row `--user-port 5173` in K-args-take. |
| 34 | accepts --flag=value as well as --flag value | C | Row `--port=4200` in K-args-take. |
| 38 | takes an explicit config path | C | Row `--config` in K-args-take. |
| 42 | suppresses opening the browser | C | Row `--no-open` in K-args-take. |
| 46 | switches to machine-readable output for agents | C | Row `--json` in K-args-take. |
| 50 | asks for help | C | Rows `--help`, `-h` in K-args-take. |
| 57 | leglas %s --help prints the help | R | docs/cli.md promises `leglas <command> --help` for every command; 12 rows, both spellings. |
| 75 | help wins over whatever else the command was given | C | Two rows in K-args-take (`show … --help`, `keep … -h …`). |
| 80 | a mistyped command asking for help gets it | C | Row `shwo --help` in K-args-take, row `shwo` in K-args-refuse. |
| 86 | asks for the version | C | Row `--version` in K-args-take. |
| 90 | rejects an unknown flag rather than ignoring it | C | Row `--prot 4200` in K-args-refuse, message names the flag. |
| 99 | rejects a port that is not a number | C | Row `--port abc` in K-args-refuse. |
| 108 | rejects a flag that is missing its value | C | Row `--port` in K-args-refuse. |
| 117 | rejects a port outside the valid range | C | Rows `99999` and `-1` in K-args-refuse. |
| 122 | rejects an unknown command rather than silently booting | C | Row `start` in K-args-refuse. |
| 133 | takes the surface to scaffold | C | Row `new hero` in K-args-take (surface and `print: false`). |
| 142 | asks for a surface name when none is given | C | Row `new` in K-args-refuse. |
| 151 | can print the scaffold instead of writing it | C | Row `new hero --print` in K-args-take. |
| 160 | defaults to writing, since printing is the escape hatch | C | Same row as line 133: `print: false`. A near-duplicate parse of the same argv. |
| 169 | rejects a flag that belongs to booting, not scaffolding | C | Row `new hero --user-port 3000` in K-args-refuse. |
| 175 | takes a title and a url | C | Row `add --title --url` in K-args-take, which also pins branch, basedOn and askedFor as unset. |
| 185 | takes an optional note and tags | C | Row with `--note` and two `--tag` in K-args-take. |
| 207 | requires a title | C | Row `add --url` in K-args-refuse. |
| 216 | requires a url | C | Row `add --title Aurora` in K-args-refuse with the full message, which names `--url` and `--file`. |
| 225 | emits json for agents when asked (add) | C | Row `add … --json` in K-args-take. |
| 236 | needs no arguments (list) | C | Row `list` in K-args-take. |
| 240 | emits json for agents when asked (list) | C | Row `list --json` in K-args-take. |
| 251 | collects changed and rewritten paths with their intent | C | Row in K-args-take with both changes and `json`. |
| 271 | accepts --flag=value (classify) | C | Row `--rewrite=src/hero.tsx` in K-args-take. |
| 280 | needs at least one declared path | C | Row `classify` in K-args-refuse. |
| 289 | rejects flags it does not know (classify) | C | Row `classify --deps` in K-args-refuse. |
| 295 | takes the branch to back the preview with | C | Row `--branch` in K-args-take. |
| 304 | leaves branch undefined for an ordinary preview | C | Same row as line 175: `branch: undefined` (toMatchObject requires the key). |
| 315 | takes a file instead of a url | C | Row `--file` in K-args-take, `url: undefined`. |
| 325 | still requires a url or a file | C | Same argv as line 216; the full message carries `--file`. |
| 336 | defaults to three new directions | C | Row `explore hero` in K-args-take. |
| 346 | takes a direction title to build variants of | C | Row `--based-on --count` in K-args-take. |
| 356 | refuses --based-on with no title | C | Row in K-args-refuse. |
| 365 | --build with a brief asks the running Leglas to build the set | C | Row in K-args-take, same `toMatchObject`. |
| 386 | --build without a brief is refused, naming the flags that would do | C | Row in K-args-refuse; the matcher requires `--brief` and `--based-on`. |
| 396 | --build with --based-on builds variations | C | Row in K-args-take. |
| 405 | a brief without --build is refused | C | Row in K-args-refuse. |
| 416 | records the direction a variant is based on | C | Row `--based-on` in K-args-take. |
| 433 | is optional, and absent means an ordinary root | C | Same row as line 175: `basedOn: undefined`. |
| 444 | records the change that was asked for | C | Row `--asked-for` in K-args-take. |
| 461 | is optional, because most directions were never asked for in words | C | Same row as line 175: `askedFor: undefined`. |
| 472 | takes a screenshot width and explicit server port | C | Row in K-args-take, full `toEqual`. |
| 493 | keeps metadata-only show as the default | C | Row `show Aurora` in K-args-take. |
| 499 | width and port only make sense with a screenshot | C | Two rows in K-args-refuse with the exact messages. |
| 510 | refuses widths outside the capture range | C | Rows 319, 3841, wide in K-args-refuse. |
| 518 | no directions shares the rail; one alone; two compare | C | Three rows in K-args-take, the first a full `toEqual`. |
| 537 | takes a reach, a tunnel and the port of a Leglas elsewhere | C | Two rows in K-args-take. |
| 544 | stop ends the share and takes nothing that would start one | C | Row in K-args-take, exact message row in K-args-refuse. |
| 552 | rotates every link, or revokes the one it names, one at a time | C | Two rows in K-args-take, three exact-message rows in K-args-refuse. |
| 574 | refuses what it cannot share | C | Four exact-message rows in K-args-refuse. |
| 596 | takes one direction or more, and says so when there are none | C | One `toEqual` row in K-args-take, two exact rows in K-args-refuse. |
| 614 | takes none, one or two directions and the port | C | Two `toEqual` rows in K-args-take, one exact row in K-args-refuse. |
| 631 | takes the agent command as one argument | C | Row `watch --run` in K-args-take (`port: undefined` kept). |
| 641 | runs with no flags at all, on whatever was remembered | C | Row `watch` in K-args-take. |
| 650 | takes the port Leglas is on, for the attachment heartbeat | C | Row `--run= --port` in K-args-take. |
| 660 | refuses --run with nothing after it | C | Row in K-args-refuse. |
| 669 | rejects an unknown flag rather than ignoring it (watch) | C | Row `watch --verbose` in K-args-refuse. |
| 674 | takes --json, which prints one JSON line per event | C | Row in K-args-take (docs/cli.md comment kept on the row). |

## packages/cli/src/baseline.test.ts (61, 8)

Keeper **K-baseline**: `baselineFrom › re-exports a named component live, by a path bundlers resolve` plus one table of the other export shapes and one of the refusals.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 7 | re-exports the component instead of copying it | C | K-baseline: the exact import line and `<Hero />`. |
| 15 | drops the extension from the import specifier | C | K-baseline: the exact import line has no `.tsx`. Same input as line 7. |
| 26 | finds a default export and gives it a local name | C | Row in the export-shape table (exact import line). |
| 32 | handles an arrow component assigned to a const | C | Row in the export-shape table. |
| 38 | computes the path from a nested surface directory | C | Row in the export-shape table. |
| 48 | refuses a file with no component it can name | C | Row in the null table. |
| 52 | ignores a lowercase export | C | Row in the null table. |
| 56 | names the file it re-exports | C | K-baseline: contents name `src/Hero.tsx`. Same input as line 7. |

## packages/cli/src/bin-update.test.ts (162, 3)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 81 | routes service logs for JSON=%s and preserves the startup envelope | R | The documented stdout/stderr split under `--json`; nothing else drives `startViewer`'s log routing. |
| 108 | after a restart hands off, a shutdown signal goes to the child alone | R, compact | The `handedOff()` guard in `startViewer` (#112); the inline `startViewer` call now goes through the file's `start` helper, which leaves `installShutdown` to its default here so the real one is the one under test. |
| 152 | starts with the unresolved entry when realpath fails | R | A removed npx cache entry must not stop startup. |

## packages/cli/src/dev-server-owner.test.ts (61, 7)

All R: lsof output parsing and the ownership warning are only reachable here (`inspectLocalDevServer` needs lsof and a listener; `run.test.ts` injects it).

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 11 | recognizes loopback origins and their default ports | R | Only localhost origins may be tied to a process. |
| 17 | ignores remote and invalid origins | R | Same rule, the refusing side. |
| 24 | deduplicates listener process ids | R | lsof repeats a pid per descriptor. |
| 28 | pairs each process with only its cwd record | R | Only the `fcwd` record names the directory. |
| 39 | stays quiet when any listener belongs to the project tree | R | A monorepo package dev server must not warn. |
| 47 | names an unrelated listener and gives the correction | R | The exact warning a user reads. |
| 58 | stays quiet without ownership evidence | R | No lsof means no warning, never a failed start. |

## packages/cli/src/explore.test.ts (81, 9)

`planExplore` is public API and its text is a prompt-byte contract. Keepers: **K-explore-spread** (the spread brief, `planExplore("hero", n)`) and **K-explore-variants** (the variants brief).

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 6 | tells the agent where the files belong and how to register | C | K-explore-spread keeps all four `toContain`s. |
| 15 | normalises the surface name the same way the scaffold does | R | `planExplore` must slug the surface; a raw name breaks the URL. |
| 22 | asks for the number of directions requested | C | K-explore-spread: "Build 5 design directions". |
| 26 | supplies no taste of its own | R | The retired style deck must not come back (module comment). |
| 36 | exploring states the goal and the collapse trap | C | K-explore-spread keeps both phrases. |
| 43 | variants state the opposite goal and the drift trap | C | K-explore-variants keeps all four assertions. |
| 53 | variants register with the direction they are based on | C | K-explore-variants: `--based-on "Aurora"`; K-explore-spread: no `--based-on`. |
| 61 | asks for registration as each direction lands, not batched | C | K-explore-spread keeps all four phrases. |
| 70 | both modes share the same file mechanics | R | The shared mechanics paragraph must not drift between modes. |

## packages/cli/src/ignore.test.ts (40, 7): retired

`ignoreEntry` is private (`ignore.ts` is not exported); users meet it through the public `planInit` and `planNew`. Its rows move to **K-init-ignore** at the public boundary: `planInit › ignores .leglas/ in a .gitignore of %j, keeping what is there`, `… ends the .gitignore in exactly one newline` and `… leaves a .gitignore of %j alone`. The file is deleted.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 6 | adds the entry when there is no .gitignore at all | C | Row `null` in K-init-ignore. |
| 10 | appends to an existing file without disturbing what is there | C | Row `node_modules\ndist\n` in K-init-ignore, same three `toContain`s. |
| 18 | does nothing when the entry is already present | C | Row in K-init-ignore, `null`. |
| 22 | recognises the entry without a trailing slash | C | Row `.leglas\n`, `null`. |
| 26 | ignores surrounding whitespace when checking | C | Row `  .leglas/  \n`, `null`. |
| 30 | does not treat a longer path as the entry | C | Row `.leglas/variants\n`, contains `.leglas/\n`. |
| 34 | keeps the file ending in exactly one newline | C | Row `node_modules`, ends in exactly one newline. |

## packages/cli/src/init.test.ts (131, 15)

`planInit` is public API; the AGENTS.md section is a prompt-byte contract agents read. Keeper **K-init-section**: `planInit › the section it writes teaches the loop an agent follows` (one `plan()` call, every content assertion of lines 13 and 46 to 99).

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 13 | creates AGENTS.md when the project has none | C | K-init-section reads the AGENTS.md write and checks the start marker. |
| 17 | appends to an existing AGENTS.md without disturbing it | R | Project text survives and comes first. |
| 30 | does not add a second copy when the section is already there | R | Uses the committed marker text (#112). |
| 34 | replaces the section when asked to update it | R | `--force` keeps the project's text on both sides. |
| 46 | teaches additive authoring | C | K-init-section, same three assertions. |
| 54 | choreographs the live loop | C | K-init-section, same six assertions including both orderings. |
| 71 | does not repeat setup for a request created by the running interface | C | K-init-section, same three assertions. |
| 79 | teaches the hands-free path | C | K-init-section. |
| 86 | explains the images a request can carry | C | K-init-section. |
| 93 | names the commands an agent needs | C | K-init-section. |
| 101 | creates a starter config when the project has none | R | The config is created when absent. |
| 105 | never overwrites an existing config | R | The config is the user's. |
| 111 | ignores the working directory | C | Row `null` in K-init-ignore. |
| 115 | leaves .gitignore alone when it already ignores the directory | C | Row `.leglas/\n` in K-init-ignore. |
| 119 | reports when there is nothing left to do | R | All three inputs present means no writes. |

## packages/cli/src/keep.test.ts (133, 11)

`planKeep` is public API. `runKeep` resolves the title before calling it, so the not-found refusal is only reachable here. Keepers: **K-keep-plan** (one `planKeep` call over a hero set plus a nav direction, asserting every field) and **K-keep-refuse** (a refusal table; it compares the message case-insensitively, where two of the five rows used to compare exactly).

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 21 | moves the winner out of the ignored directory into real source | C | K-keep-plan: `move` `toEqual`. |
| 33 | deletes the whole exploration | C | K-keep-plan: `removeDir`. |
| 42 | drops every direction of that surface from the rail, winner included | C | K-keep-plan: sorted `dropTitles`. |
| 51 | leaves directions belonging to other surfaces alone | C | K-keep-plan: the same input carries the nav direction, and the sorted `toEqual` excludes it. |
| 64 | renames the exported component to suit its new home | C | K-keep-plan: `exportName`. |
| 73 | tells the user the one import change left to them | C | K-keep-plan: both `toContain`s on `instructions`. |
| 83 | refuses a direction it cannot find | C | Row in K-keep-refuse. |
| 92 | refuses a direction whose file it cannot locate | C | Row in K-keep-refuse. |
| 105 | refuses a destination inside the ignored directory | C | Row in K-keep-refuse. |
| 114 | refuses a destination that escapes the project | C | Row in K-keep-refuse. |
| 125 | refuses an absolute destination | C | Row in K-keep-refuse; the Windows comment moves with it. |

## packages/cli/src/new.test.ts (300, 23)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 138 | recognises a Next app | C | Row in **K-new-framework** (`detectFramework` table). |
| 142 | recognises a Vite React app | C | Row in K-new-framework. |
| 146 | falls back to the browser form when the framework is unknown | C | Row in K-new-framework. |
| 150 | falls back rather than throwing on an unreadable package.json | C | Row in K-new-framework. |
| 154 | falls back when there is no package.json at all | C | Row in K-new-framework. |
| 160 | keeps a simple name as-is | C | Row in **K-new-slug** (`surfaceSlug` table). |
| 164 | normalises spacing and case | C | Row in K-new-slug. |
| 168 | strips characters that would break a query string | C | Row in K-new-slug. |
| 177 | writes the switcher into the ignored directory | C | **K-new-files**: the exact three paths, all under `.leglas/variants/hero/`. |
| 183 | names the switcher after the surface | C | K-new-files: `.leglas/variants/hero/switch.tsx`. |
| 189 | ships a first variant so there is something to render immediately | C | K-new-files: `hero-a.tsx`; the render test below also loads it. |
| 200 | adds the ignored directory to .gitignore | C | **K-new-ignore**: one test, both inputs. |
| 204 | does not add a second .gitignore entry | C | K-new-ignore. Kept at `planNew` too: it proves the argument is passed, not that the helper works. |
| 221 | guards production in the %s switch | R | Production must render the fallback; runs the generated code. |
| 235 | imports nothing from Leglas | R | The scaffold must outlive the tool. |
| 242 | reads the param on the server for Next | C | Row in **K-new-param** (where each framework reads the param). |
| 249 | reads the param in the browser for a plain React app | C | Row in K-new-param, which also checks the browser switch takes no `searchParams` prop. |
| 255 | exports only the component so edits hot-swap in place | R | One export keeps Fast Refresh. |
| 265 | the generated %s renders | R | #111: the placeholder threw on render. |
| 274 | the Vite switch compiles without vite/client or @types/node | R | Runs the repository's tsc. |
| 280 | uses the surface name as the query param | C | **K-new-previews**: `previews` `toEqual` plus the switch reading `v-hero`. |
| 288 | suggests config entries for the current state and the first direction | C | K-new-previews: same call, titles in the same `toEqual`. |
| 294 | tells the user the one wiring change it deliberately did not make | R | The import is the user's to make. |

## packages/cli/src/restart.test.ts (172, 8)

All R. `createHandoff` owns the restart handoff; each test pins one ordering or exit rule, and #112 kept line 41 as the pin for a review fix.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 41 | handoff state belongs to one CLI instance | R | Module-level state was a review finding. |
| 53 | marks the handoff before stopping and frees the port before spawning | R | Ordering is observable: the port must be free before the child binds. |
| 71 | a %s during stop cancels the spawn and exits cleanly | R | Each signal, listeners removed. |
| 90 | forwards %s to the child | R | Each signal reaches the child once. |
| 102 | exits with child code %s and signal %s | R | Exit code mapping, including a signal death. |
| 116 | a spawn %s prints recovery instructions and exits once | R | The recovery sentence and a single exit for both failure shapes. |
| 139 | a stop failure returns control to ordinary shutdown | R | Handoff state is reset on failure. |
| 158 | passes through the Windows shell setting | R | `shell: true` for a quoted Windows command. |

## packages/cli/src/run-explore-build.test.ts (169, 5)

All R: `runExploreBuild` against a fake running Leglas; each test is one outcome (progress lines, variations request body, failure, refusal, JSON).

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 80 | reports each direction as it lands and exits 0 when all are ready | R | The exact progress lines a person reads. |
| 112 | asks for variations of a direction by its title, with no brief | R | The request body for `--based-on`. |
| 131 | exits 1 and says why when a direction fails | R | Failure line and exit code. |
| 144 | passes a refusal through word for word | R | Server refusals are not rewritten. |
| 154 | prints one JSON envelope for an agent | R | `--json` is one envelope. |

## packages/cli/src/run-keep.test.ts (108, 4)

All R, compact: the project fixture registers its direction through the shared `addLocal` helper (argv parsed by `parseArgs`, then `runAdd`, the way `leglas add` runs).

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 55 | a relative destination lands inside the project | R | The documented form. |
| 66 | notes the keep in the record of the set that built it | R | The generation record gets the keep event. |
| 87 | an absolute destination inside the project lands where the relative one would | R | #108. |
| 97 | an absolute destination outside the project is refused and nothing moves | R | #108, the refusing side. |

## packages/cli/src/run-link.test.ts (92, 5)

All R, compact (fixture through `addLocal`).

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 52 | opens the pair side by side, taking the name the rail shows | R | Link format read by the shell's own `readLink`. |
| 61 | with no direction named, opens the rail as it is | R | Bare interface URL. |
| 68 | refuses a pair that is one direction under both its names | R | Rename-aware pair check. |
| 76 | refuses a direction the running rail doesn't show yet | R | A link must open on something. |
| 84 | says Leglas isn't running when nothing answers | R | `NOT_RUNNING`. |

## packages/cli/src/run-log.test.ts (97, 5)

All R: `runLog` is only tested here.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 32 | lists newest first | R | Slug order. |
| 47 | says nothing is recorded rather than failing | R | Empty project. |
| 56 | prints one entry whole, with or without its extension | R | Both spellings. |
| 67 | refuses an entry that is not there, and says where it looked | R | Error names `design-log`. |
| 79 | answers json in one envelope | R | Envelope shape. |

## packages/cli/src/run-previews.test.ts (223, 10)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 43 | refuses a direction that is not registered, since that is a typo | R | `--based-on` must name a direction. |
| 56 | records the parent when it exists, and it survives the round trip | R | Written `basedOn`. |
| 84 | includes a restart note for file previews | C | Row in **K-add-note** (`runAdd --json` note by preview kind). |
| 99 | includes a live-update note for url previews | C | Row in K-add-note. |
| 109 | add and list give one that opens on the direction | R, compact | `interfaceUrl` read by the shell's `readLink`. Through the file's `addThenList` helper. |
| 134 | is left out, and nothing is asked, with no Leglas recorded | R, compact | No fetch without a record. Through the file's `addThenList` helper. |
| 148 | is left out when the recorded port serves another project | R, compact | Another project's Leglas is not linked. Through the file's `addThenList` helper. |
| 163 | is left out for a direction the running rail doesn't show yet | R, compact | Branch and file directions need a restart. Through the file's `addThenList` helper. |
| 190 | collects requests and includes id and status in the envelope | R | Collecting marks picked-up. |
| 209 | clear drops collected work and says what is still waiting | R | `--clear` reports what arrived meanwhile. |

## packages/cli/src/run-remove.test.ts (126, 6)

All R, compact (fixture through `addLocal`).

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 57 | takes a direction registered on this machine off the rail | R | The rail after removal. |
| 66 | notes the removal in the record of the set that built it | R | Generation record. |
| 84 | takes the name the rail shows | R | Rename-aware. |
| 91 | refuses a direction the shared config lists, and removes nothing | R | All-or-nothing. |
| 100 | refuses a title the config lists even when this machine registered it too | R | The config wins over a local duplicate. |
| 114 | says a registry it cannot read is why, and leaves it as it is | R | Unreadable registry is not rewritten. |

## packages/cli/src/run-share.test.ts (630, 19)

All R, compact. The fake Leglas stays; every `runShare` call goes through one `share()` helper that returns the exit code, the lines and the last envelope, and the shared `addLocal` replaces the file's `add`. No assertion changes.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 207 | shares the rail by default, leaving out what cannot go, and waits for the link | R | The POST body and the waited-for link. |
| 253 | one direction goes alone, two are compared with the second on the right | R | Scope, layout and rename. |
| 287 | a direction is not compared with itself, under either of its names | R | Exact refusal, nothing posted. |
| 308 | a share already running is shown rather than started twice | R | Three outcomes against a running share. |
| 357 | --stop ends the share | R | Stop endpoint. |
| 370 | --revoke ends the one link it names, by its address or its id | R | Both lookups. |
| 399 | --revoke of the last live link says how to get a new one | R | Human sentence. |
| 414 | --revoke refuses a link the share doesn't have, and ends nothing | R | Nothing posted. |
| 434 | --rotate ends every link and hands back the new one | R | Rotate endpoint. |
| 458 | --rotate and --revoke with nothing shared say so | R | Both acts. |
| 476 | a share it cannot follow is stopped, not left open behind an error | R | Security: no orphan share. |
| 492 | losing the share while its tunnel starts stops it too | R | Security: no orphan share. |
| 507 | a start whose answer was lost is treated as a share that may exist | R | Security: no orphan share. |
| 523 | the server's own refusal is what the person reads | R | Refusals pass through. |
| 545 | nothing running here is said plainly | R | `NOT_RUNNING` sentence. |
| 560 | in a terminal: the link, when it stops working, and how to stop it | R | Human output. |
| 580 | without a tunnel program, the local link and what would reach further | R | Human output. |
| 597 | choosing no tunnel is not the same as having none | R | Human output. |
| 614 | a tunnel still starting when the wait runs out says to ask again | R | Human output. |

## packages/cli/src/run-show.test.ts (466, 15)

R, compact: one `show()` helper runs `runShow` and returns exit code, lines and envelope; one `capturing()` builds the health-then-capture fake. `addLocal` replaces the file's `add`.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 57 | answers to the name the rail was renamed to | R, compact | Rename resolution. |
| 73 | gives the address that opens the interface on a direction the running rail shows | R, compact | `interfaceUrl` read by `readLink`, null for one not on the rail. |
| 100 | a config title still wins over another direction's local nickname | R, compact | Title precedence. |
| 116 | refuses a nickname two directions share rather than picking one | R, compact | Ambiguity refusal. |
| 132 | an unknown name says why the name it was given may not be a title | R, compact | The rename hint. |
| 148 | checks the running server and adds one screenshot to the JSON envelope | R, compact | Request order, body, abort signal and the envelope. |
| 197 | human output names the PNG and each console error | R, compact | Lines and their order. |
| 243 | human output omits hydration lines when the server has no evidence | R, compact | No false hydration claim. |
| 273 | reports a missing server and surfaces capture errors verbatim | R, compact | Default port probe and verbatim error. |
| 309 | a server serving another project is refused before anything is captured | R, compact | Security: no capture through another project's server. |
| 330 | a server serving this project is accepted by its directory | R, compact | The accepting side. |
| 374 | rejects malformed capture fields: $body | R | **K-show-malformed**, the table that absorbs line 429. |
| 399 | keeps string diagnostics in order and ignores incomplete hydration evidence | R, compact | Parsing of the optional fields. |
| 429 | a null capture reply is a failed capture, not a crash, for status %s | C | Two rows `{ body: null, status: 200 }` and `{ body: null, status: 503 }` in K-show-malformed: same exit code and message. |
| 451 | a null health reply fails before requesting a capture | R, compact | One fetch only. |

## packages/cli/src/run-update.test.ts (174, 10)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 73 | CI=%s permits the check | C | Rows in **K-skip-check**, one table of env and verdict. |
| 76 | CI=%s skips the check | C | Rows in K-skip-check. |
| 79 | LEGLAS_NO_UPDATE_CHECK=%s permits the check | C | Rows in K-skip-check. |
| 87 | LEGLAS_NO_UPDATE_CHECK=%s skips the check | C | Rows in K-skip-check. |
| 93 | forwards the port and update service it is given to the server | R | Nothing else proves `--port` reaches `startServer` (run.test boots on port 0, which a dropped port would also satisfy). |
| 107 | checks again hourly without printing another notice, and stops checking on stop | R | Fake-clock hourly check. |
| 123 | a startup check finishing after stop prints nothing | R | The `stopped` guard. |
| 138 | returns without waiting for npm | R | Startup never blocks on npm. |
| 155 | JSON output remains one envelope with no startup check | D | `run.test.ts` › startup update notice, the `json: true` row, asserts one envelope and that `check` was never called against a real server. The hourly timer sits inside the same `if` as the check, and line 166's rows prove that guard keeps the timer off an hour later. |
| 166 | %s suppresses the startup check | R | The env opt-outs at the boundary, an hour later too. |

Also F for the file as a whole: it injected `loadConfig` and `readLocalPreviews` into `runWithServices` only to return what the real ones return for an empty directory. It now runs the real ones on a project directory that does not exist (as the fake `/work/app` did, so `run`'s realpath fallback stays exercised), which unlocks deleting those two injection points (see seams).

## packages/cli/src/run-watch.test.ts (420, 16)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 95 | the first pickup waits for the server to learn a watcher exists | R, compact | Ordering: no double pickup with the embedded runner. Started and stopped through the file's `watchUntil` helper. |
| 130 | refuses to start with no template anywhere | C | **K-watch-no-template**: one test runs both output modes. |
| 139 | a --run flag beats both the saved template and agent choice | C | Row in **K-watch-precedence**. |
| 149 | a saved template beats the saved agent choice | C | Row in K-watch-precedence. |
| 159 | synthesizes the terminal template for %s | R | Exact agent command lines. |
| 177 | includes the saved effort in the %s terminal template | R | Effort flags. |
| 193 | does not write a synthesized command back to the shared config | R | watch.json is not rewritten. |
| 203 | remembering a --run template preserves the saved agent choice | R | watch.json keeps `agent`. |
| 215 | stopping mid-run waits for the request's bookkeeping | R, compact | No stranded request. Started and stopped through the file's `watchUntil` helper. |
| 244 | under --json every line is an event, in the order things happened | R, compact | docs/cli.md event stream. Started and stopped through the file's `watchUntil` helper. |
| 269 | under --json a failed request is a failed event carrying the queue's verdict | R, compact | `FailureCode` on the event. Started and stopped through the file's `watchUntil` helper. |
| 303 | under --json a watch that cannot start prints the usual failure envelope | C | K-watch-no-template, the `--json` half. |
| 313 | a command that cannot spawn is written down as failed and unretried | R, compact | `missing-agent`, left as failed. Started and stopped through the file's `watchUntil` helper. |
| 344 | remembers the template for the next flagless run | R | "Remembered after first use". |
| 357 | stdout is JSON lines while the agent's output goes to stderr | R | Coverage-blind (built bin, child process). Only a real process shows the stream split; no keeper can carry it. |
| 406 | a signal that fired during startup still stops the watcher | R | An already-aborted signal. |

## packages/cli/src/run.test.ts (465, 17)

Real-server boundary for `run`. Keeper **K-run-boot**: the first test, which now also checks the browser and the config label.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 119 | boots against the config's dev server and reports its url | R | Proxies the real app. |
| 135 | opens the browser at the interface, not at the app | C | K-run-boot: `opened` equals `[result.url]` (same boot, `open: true` default). |
| 147 | leaves the browser alone when told to | C | Moved into line 220's test, which already boots with `open: false`: `opened` is `[]`. |
| 159 | --user-port overrides the configured dev server | R | Flag beats config. |
| 168 | runs with no config at all, previewing the app root | R | Implicit App. |
| 177 | still starts when the config is invalid, and says what is wrong | R | Invalid config is reported, not fatal. |
| 186 | warns when the dev server is not reachable | R | The `(not reachable)` marker on the app line; the greenfield test reaches the separate warning block. |
| 194 | prints a single json envelope for agents | R, compact | JSON envelope. Its project comes from the file's `appProject` helper. |
| 208 | names the config file it used | C | K-run-boot: output names `leglas.config.ts` (same project shape). |
| 220 | warns without blocking when a local dev server belongs to another project | R, compact | Warning in output and in the config route. Its project comes from the file's `appProject` helper. |
| 251 | prints the appropriate notice for $json JSON and $notice | R, compact | Notice placement against a real server; the keeper for line 155 of run-update. Its project comes from the file's `appProject` helper. |
| 324 | keeps the preview idle and reports the missing devCommand only when it is opened | R, compact | Lazy branch start. Its project comes from the file's `appProject` helper. |
| 360 | does not check out a configured branch during CLI startup | R | No checkout at boot. |
| 385 | serves a file preview from the Leglas origin, with no dev server at all | R | Greenfield file mount. |
| 409 | reports a file preview whose file does not exist, and skips it | R | Skipped, reported. |
| 420 | starts the app itself when nothing is listening and the config says how | R | devCommand start. |
| 445 | does not start the app behind an explicit --user-port | R | The `--user-port` guard (#112). |

## packages/cli/src/show.test.ts (132, 8)

`planShow` is public API; `runShow` resolves titles first, so the not-found refusal is only reachable here. Keepers: **K-show-plan** (one call with requests, asserting direction, variants, comparedWith and requests) and **K-show-target** (the file behind a direction, by preview kind).

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 36 | answers with everything the config holds about the direction | C | K-show-plan: the same `direction` `toEqual`. |
| 55 | names the file behind it | C | Row "local scaffold" in K-show-target, `local: true` too. |
| 65 | a url outside the scaffold's shape has no file to name | C | Row in K-show-target, `null` (and `local: false`, newly checked). |
| 78 | a file preview names its own source rather than decoding a url | C | Row in K-show-target. |
| 91 | gathers the variants that are based on it | C | K-show-plan: variant titles. |
| 100 | says what the direction is up against, without repeating its own variants | C | K-show-plan: `comparedWith`, comment kept. |
| 111 | carries only the requests pending against this direction | C | K-show-plan: the same two requests, intents `["warmer"]`. |
| 124 | refuses a title that is not registered | R | Public API refusal. |

## packages/cli/src/shutdown.test.ts (55, 3)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 22 | handles every signal a terminal routinely sends, SIGHUP included | R | **K-shutdown-signals**: the literal list, and now each literal signal stops. |
| 32 | %s releases what Leglas is holding | C | K-shutdown-signals fires each of the three literal signals on a fresh target. The `test.each` iterated `SHUTDOWN_SIGNALS` itself, so it could not notice a signal leaving the list. |
| 42 | a second signal does not start a second shutdown | R | Stop runs once. |

## packages/mcp/src/channel.test.ts (217, 6)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 108 | meta keys are identifier-safe | R | The host drops hyphenated keys silently. |
| 121 | offers queued requests once and never picked-up ones | R | Public `unpushed`; picked-up skipping is unit-only. |
| 129 | pushes a queued request to the connected host once | R | The real notification. |
| 145 | overlapping polls never double-emit a request | R | The `busy` guard; needs the public `read` option. |
| 171 | stays quiet when there is no project to poll | R, compact | The inline server and client pair now uses the file's `connect`, which takes a project. |
| 206 | a request queued later arrives as its own event | R | Later pushes. |

## packages/mcp/src/engagement.test.ts (149, 7)

F for every test: the suite drove `createEngagement` through injected `post`, `setInterval`, `clearInterval` and `now`, while also turning on Vitest's fake timers. It now uses the fake timers alone and a stubbed `fetch`, so it exercises the real post (URL, body, swallowed failures) and the real clock, and the four injection points go.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 45 | touch starts the beat and says watching at once | F | Asserts the POST to `/leglas/api/watch` on the default port, then a beat two seconds later. |
| 56 | the first touch of a cycle settles only after the server heard it | F | Same ordering, the deferred response is the stubbed fetch's. |
| 95 | a rejecting post never fails the touch that carried it | F | `fetch` rejects; touch resolves. |
| 105 | a second touch extends the engagement instead of stacking timers | F | One timer pending, no `false` sent, 200 s after the first touch. |
| 119 | a quiet spell lets the engagement lapse, and says so | F | Exactly one `false`, no timer pending, nothing after. |
| 131 | stop ends an active beat and reports detachment once | F | Same assertions on posts and timers. |
| 142 | stop before any touch stays silent | F | Nothing posted. |

## packages/mcp/src/parity.test.ts (489, 6)

All R. Architecture contract: CLI flags, MCP parameters, `--help` and the server's routes are placed in one table. Source inspection on purpose (the route scan): it fails when a user-facing route or flag changes and survives renames.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 391 | every command has a tool or a reason, and every MCP tool belongs to one command | R | Also the keeper for tools.test line 100. |
| 401 | every MCP parameter is a flag or a positional argument of its command | R | Parameter parity. |
| 417 | each command takes exactly the flags placed under it | R | Flag parity through the published parser. |
| 427 | --help and the table agree on every command and flag | R | Help text parity. |
| 473 | every route the interface calls has a tool or a reason | R | Route scan, refuses an unreadable route. |
| 481 | each tool a route names takes the parameter it names | R | Route to parameter. |

## packages/mcp/src/project.test.ts (168, 11)

All R. `hostProject` is public API and each test is one rule of its decision order. A table of these rows (planned as K-project-decides) came out 18 lines longer than the tests, since each row needs its own scratch directories and comment, so it was not applied.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 27 | takes the declared root when the working directory is elsewhere | R | One rule of the decision order. |
| 37 | keeps the working directory when it sits inside a declared root | R | One rule of the decision order. |
| 48 | keeps the working directory when the host declares no roots at all | R | One rule of the decision order. |
| 58 | keeps the working directory when the host refuses to list its roots | R | One rule of the decision order. |
| 66 | an explicit LEGLAS_PROJECT_DIR outranks both | R | One rule of the decision order. |
| 77 | refuses when the working directory is the plugin's own and nothing else answers | R | Refusal in the plugin's own directory; the message names `LEGLAS_PROJECT_DIR`. |
| 90 | refuses too when the host fails to answer, and says so without guessing why | R | Refusal when the host fails; the message does not guess why. |
| 104 | an unexpanded ${PLUGIN_ROOT} placeholder matches nothing and is ignored | R | One rule of the decision order. |
| 115 | skips roots that name no directory on this machine | R | One rule of the decision order. |
| 130 | waits for the host to initialize before asking for roots | R | Ordering: roots before initialize is a protocol error. |
| 148 | resolves once and holds the answer | R | One `listRoots`. |

## packages/mcp/src/tools.test.ts (703, 25)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 100 | lists the same tools the CLI offers | D | A copied inventory of 13 names. `parity.test.ts` › every command has a tool or a reason asserts the listed tools equal the tools placed in its table, and line 678 asserts the instructions name exactly the listed tools. A renamed or dropped tool fails both. |
| 123 | share reaches the running Leglas through the CLI, and says so when there is none | R | NOT_RUNNING through MCP. |
| 144 | add registers a local preview and returns the CLI's envelope | R | **K-tools-add**: absorbs lines 236, 249, 263 and 309 as further calls on the same client. |
| 161 | show answers for one direction, file behind it included | R | **K-tools-show**: absorbs line 178. |
| 178 | show marks an unknown title as an error, with the CLI's message | C | K-tools-show: a second `show` call, same three assertions. |
| 188 | show with a screenshot returns the PNG beside its JSON envelope | R | Image content. |
| 236 | add with a branch carries the warning about the missing devCommand | C | K-tools-add: the branch call, same two assertions. |
| 249 | a failed add is marked as an error, with the CLI's message | C | K-tools-add: a second add of the same title, same two assertions. |
| 263 | list shows what add registered | C | K-tools-add: `list` after the adds, same assertion. |
| 275 | classify routes a dependency change to a checkout | R | Classify wiring. |
| 286 | explore briefs the set without prescribing designs | R | **K-tools-explore**: absorbs line 296. |
| 296 | explore based on a direction asks for variants instead | C | Second call in K-tools-explore, same assertions. |
| 309 | add accepts a file preview for the greenfield case | C | K-tools-add: the file call (titled Sketch, since Aurora is taken), same two assertions. |
| 321 | working the queue marks the session engaged | R | **K-tools-queue**: absorbs line 333. |
| 333 | requests is empty for a fresh project | C | K-tools-queue: the first `requests` call's envelope is `ok` with `[]`. |
| 371 | start boots the viewer, is idempotent, and shutdown stops it | R | Coverage-blind (built bundle). The lifecycle a host relies on. |
| 396 | add and link hand out addresses of the running interface | R | Coverage-blind (built bundle). Links that open the real interface. |
| 456 | registers into the project the host declares, never the plugin directory | R | Agent Plugins roots end to end. |
| 469 | init writes into the project | R | Same, for init. |
| 480 | says there is no project rather than acting on the plugin directory | R | Refusal end to end. |
| 564 | $name, in the command line's words | R | Refusal parity, eight rows. |
| 573 | takes an explore count the command line takes | R | Count range parity. |
| 606 | each says whether it only reads and whether it reaches past this machine | R | Annotations a host trusts. |
| 631 | one that says it only reads leaves the project as it found it | R | Read-only claims checked by snapshot. |
| 678 | the published server's instructions name every tool it lists, and fit what a host keeps | R | Coverage-blind (built bin over stdio). The 2048-character cap. |

## scripts/api-surface.test.ts (169, 9)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 15 | matches the snapshot | R | Release gate. |
| 36 | an unbalanced bracket in a comment does not swallow the declaration | R | Regression. |
| 51 | a bracket inside a string literal is not counted | R | Regression. |
| 56 | a line comment that looks like a declaration does not start one | R | Regression. |
| 68 | consecutive declarations are kept apart | R | Regression. |
| 98 | a same-named declaration in another module cannot stand in | R | Regression. |
| 120 | a chain that leaves the repository is reported, not guessed at | R | `external` result. |
| 129 | a name nothing on the chain declares is missing, not silently absent | D | Line 140 builds the same `index.d.ts` re-exporting `Gone` from a `real.d.ts` that declares only `Present`, and asserts `publicSurface` throws. `publicSurface` throws only when `resolve` returns `missing`, so the boundary test fails on the same regression. |
| 140 | the surface refuses to build around a name nothing declares | R | The guarantee (#113). |

## site/build.test.ts (229, 5)

All R.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 25 | the homepage carries the command, the captures and the way to the changelog | R | Captures exist and the page is self-contained. |
| 42 | the theme switch is in the bar, and the stored choice is stamped before the styles | R | No flash of the wrong theme; a11y label. The browser test cannot see the ordering. |
| 53 | the bar carries a star on both pages | R | #113 rewrite. |
| 77 | builds the pages, the docs and the captures beside them | R | K-site-build: the build's file list from the manual's own index, and now the release index's contents (changelog line 62). |
| 151 | with reduced motion %s, a click flips the theme from the switch | R | Real browser (#113). |

## site/changelog.test.ts (310, 17)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 23 | every release heading carries a date and a title | R | The changelog page needs both. |
| 36 | releases run newest first, and none repeats | R | Ordering. |
| 52 | renders as one page that every release link lands on | R | Real CHANGELOG, every version including the shared `0.1.0 and 0.1.1` heading. |
| 62 | buildSite writes a release index led by the published CLI version | C | Moved into site/build.test.ts line 77 (**K-site-build**), which already runs `buildSite` and lists `releases.json`: the same three assertions on its contents, one build fewer. |
| 90 | a bullet keeps its bold lead, its text and who it reaches | R | Parser. |
| 117 | a blank line inside a bullet starts a paragraph | R | Parser. |
| 150 | an image line with a caption becomes media | R | Parser. |
| 175 | an Unreleased section and a two-version heading both read | R | Parser and anchors. |
| 199 | every indexed version in a shared heading has one landing anchor | D | Line 52 renders the real CHANGELOG, whose `## 0.1.0 and 0.1.1 (2026-08-01)` heading (CHANGELOG.md:802) is permanent history, and asserts `id="v0.1.0"` and `id="v0.1.1"` each land exactly once. `releasesIndex` lists the same versions `parseChangelog` does. |
| 208 | an audience nobody ships is refused | R | Refusal. |
| 214 | a tag that does not end its bullet is refused | R | Refusal. |
| 229 | a paragraph that lost its indent inside a group is refused | R | Refusal. |
| 252 | a bullet inside a bullet is refused | R | Refusal. |
| 258 | inline code, bold and links, with everything else escaped | R | Escaping, security. |
| 267 | a width hint on an image sizes the figure and leaves the URL | R | Media. |
| 286 | a lead keeps its distance from a sentence and none from a comma | R | Spacing. |
| 306 | a date reads the way a person says it | R | `longDate`. |

## site/docs.test.ts (465, 30)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 77 | the index leads, and each page is served at its own path | R | Paths. |
| 88 | a file the manual does not name is not one of its pages | R | Local notes stay local. |
| 98 | a page the manual names and nobody wrote fails the build, naming it | R | Refusal. |
| 106 | every page renders with nothing left as markdown | R | Real docs. |
| 122 | every link to another page resolves, fragment included | R | Real docs. |
| 164 | another page becomes its directory | R | Links. |
| 173 | the repository README is the homepage and the rest of the tree is on GitHub | R | Links. |
| 184 | absolute links and fragments pass through | R | Links. |
| 198 | headings get GitHub's ids | R | **K-docs-ids**, absorbs line 390. |
| 205 | paragraphs join their wrapped lines and carry inline markdown | C | Row in **K-docs-render** (markdown and the exact HTML). |
| 211 | lists keep their continuation lines | C | Row in K-docs-render. |
| 217 | numbered lists count from one and keep their continuation lines | R | Accepted and refused forms. |
| 234 | code is escaped and keeps its language | C | Two rows in K-docs-render. |
| 241 | tables render a head and a body | C | Row in K-docs-render. |
| 251 | a capture block is rebuilt from its images and caption | R | Capture blocks. |
| 262 | a capture block refuses anything outside that shape | R | Security: attribute and scheme allowlist. |
| 289 | a details block wraps a summary and capture blocks | R | Details. |
| 302 | a details block refuses anything but a summary and capture blocks | R | Refusals. |
| 322 | a link to a section with a prompt block becomes a copy button | R | Copy button. |
| 354 | a prompt block renders as code with its own copy button | R | Copy button. |
| 363 | a link to a repeated heading finds the prompt under GitHub's suffixed id | R | Suffix ids. |
| 380 | the architecture page hands the reader a button for the agent prompt | R | #100, the real page. |
| 390 | a heading keeps its letters in any script and repeats get GitHub's suffix | C | K-docs-ids, same assertions. |
| 398 | a pipe escaped inside a cell stays in the cell | R | Tables. |
| 404 | a line that starts with < is prose unless it opens a capture block | R | Prose and refusal. |
| 412 | a stray angle bracket in a capture block refuses | R | Security. |
| 420 | an absolute path resolves from the repository root | R | Links. |
| 429 | refuses markdown the page cannot show, naming the line | R | Refusals. |
| 444 | carries the bar with Docs active, the page nav and the way back | R | Page chrome. |
| 458 | the homepage and the changelog link the docs | R | #113 rewrite. |

## site/release-notes.test.ts (120, 8)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 41 | returns the title and exact markdown until the next release heading | R | GitHub gets the authored markdown. |
| 48 | matches %s in a shared heading | R | Two versions, one heading. |
| 55 | reads the last entry and returns null for absent or partial versions | R | Edges. |
| 62 | handles Windows line endings without rewriting the body | R | CRLF. |
| 68 | the real 1.0.0 entry has a title and a body | D | Asserts a title copied from CHANGELOG.md. The command tests below read the same real 1.0.0 entry with `releaseNotes` and index it, so a null fails them; line 41 owns stopping at the next heading. |
| 103 | prints %s from any working directory | R | Coverage-blind (child node). The publish workflow runs the script from the repository root; `cwd: tmpdir()` proves it does not depend on that. |
| 114 | a missing version exits with the specified sentence | R | Coverage-blind (child node). The workflow's failure path. |
| 82 | lists each released version newest first without Unreleased | R | Feed order. |

## test/ (repository tests)

All R: each is the only check of a repository contract (the npx prefix in printed examples, the manual's page list, the publish workflow's channels and release notes, the Agent Plugins manifests).

| File:Line | Test | Mark | Evidence |
| --- | --- | :-: | --- |
| copy.test.ts:41 | every example is runnable without installing anything | R | Source inspection on purpose: fails when a printed example loses `npx`. |
| docs.test.ts:83 | every committed page of the manual is one the site knows to serve | R | Git is the only witness. |
| docs.test.ts:92 | the index mentions every page, in the order the site shows them | R | The reader's index. |
| plugin.test.ts:42 | plugin.json conforms to the Agent Plugins schema | R | Manifest. |
| plugin.test.ts:46 | mcp.json conforms to the Agent Plugins schema | R | Manifest. |
| plugin.test.ts:54 | both manifests target the version of the standard we vendor | R | Schema version. |
| plugin.test.ts:89 | every skill directory holds a SKILL.md naming itself | R | Skills found by position. |
| plugin.test.ts:116 | mcp.json launches the package this repository publishes | R | Package name. |
| plugin.test.ts:134 | the plugin version matches both published packages | R | Release gate. |
| publish.test.ts:153 | %s sends prereleases to next and stable releases to latest | R | Runs the workflow's own script. |
| publish.test.ts:173 | creates the matching GitHub release for %s | R | Same. |

## Layer plan

### Keepers per contract

| Contract | Keeper |
| --- | --- |
| What each command parses to | K-args-take (`args.test.ts`) |
| What each command refuses, in its words | K-args-refuse (`args.test.ts`); refusal parity with MCP stays in `tools.test.ts` |
| Every command answers `--help` | `args.test.ts` › leglas %s --help prints the help |
| Flag, parameter, route and help parity | `parity.test.ts` |
| The tool list a host sees | `parity.test.ts` line 391 and `tools.test.ts` line 678 |
| `.leglas/` ignored exactly once | K-init-ignore (`init.test.ts`, public `planInit`); `planNew` passes its input through, K-new-ignore |
| The AGENTS.md section's teaching | K-init-section |
| The explore brief | K-explore-spread, K-explore-variants |
| A kept direction's plan | K-keep-plan, K-keep-refuse; `run-keep.test.ts` for the filesystem |
| A shown direction's plan | K-show-plan, K-show-target, `show.test.ts` refusal; `run-show.test.ts` for resolution and captures |
| Capture replies that are not captures | K-show-malformed |
| Update check opt-outs | K-skip-check (values) and run-update line 166 (boundary) |
| Update notice and JSON quiet at boot | `run.test.ts` › startup update notice |
| A run's browser and config label | K-run-boot; `open: false` in the dev-server-owner test |
| watch with no template | K-watch-no-template |
| watch template precedence | K-watch-precedence |
| Shutdown signals | K-shutdown-signals |
| The MCP engagement beat | `engagement.test.ts` on the real post and clock |
| `hostProject` decisions | `project.test.ts`, unchanged |
| MCP add, list and show wiring | K-tools-add, K-tools-show |
| The release index's contents | K-site-build |
| Shared-heading anchors | `changelog.test.ts` line 52 |
| A missing declaration refuses the surface | `api-surface.test.ts` line 140 |

### Retired files

- `packages/cli/src/ignore.test.ts` (rows to K-init-ignore).

### Shared setup

- `packages/cli/src/test-helpers.ts` gains `addLocal(cwd, ...argv)`: it parses `add` arguments with `parseArgs` and runs `runAdd`, as `leglas add` does. It replaces the hand-built eight-field `AddPreview` literal in `run-keep`, `run-link`, `run-remove`, `run-share` and `run-show`.

### Test-only production seams unlocked (applied)

- `packages/mcp/src/engagement.ts`: `EngagementDeps` (`post`, `setInterval`, `clearInterval`, `now`) and their fallbacks, -16 lines. Only `engagement.test.ts` passed them; `tools.ts` calls `createEngagement()` bare. Not in `api-surface.txt`. The rewritten test passed on the old code before the seams went, and on the new code after.
- `packages/cli/src/run.ts`: the `loadConfig` and `readLocalPreviews` services of `runWithServices`, -2 lines. Only `run-update.test.ts` passed them. `startServer` and `inspectLocalDevServer` stay: `run.test.ts` needs a server that runs no agent CLI and an owner it can choose.

### Seams that stay because `api-surface.txt` lists them

- `startChannel`'s `read` option ("Tests gate this to force overlapping polls"), needed by channel.test line 145.
- `fixedProject`, used by every mcp test as an embedder would.
- `planKeep` and `planShow` not-found refusals, unreachable from `runKeep` and `runShow` (they resolve titles first) but reachable for any importer.

## Results

Measured on the final head with `pnpm test:coverage` as the baseline did (Node 24, the `--no-sandbox` Chromium wrapper in `LEGLAS_BROWSER`). The run is comparable: the same 4 failed, 2 skipped and 2 errors as the baseline, 1,830 passed (1,859 less the 29 lane cases folded into other cases). `pnpm test` gives the same counts.

### Lines and declarations

| | Base | Final | Change |
| --- | --: | --: | --: |
| Lane test lines (37 files, now 36) | 8,329 | 7,172 | -1,157 (13.9%) |
| Declarations | 414 | 279 | -135 |
| Cases run | 471 | 442 | -29 |
| Support: `cli/src/test-helpers.ts` | 12 | 29 | +17 (`addLocal`) |
| Production: `cli/src/run.ts`, `mcp/src/engagement.ts` | | | -18 (+9, -27) |

Where the 1,157 lines came from: deletions (D) 64 lines; consolidation into tables and stronger siblings (C) about 760; shared call setup in retained tests (R, compact) about 315; the engagement rewrite (F) 21.

Target: 1,666 lines. Not reached; see "Reading the lane". The 509 lines left would have to come from tests that are each the only proof of their contract: the restart handoff ordering, the share and capture refusals, parity, the docs reader's refusals, the real-browser theme test and the child-process tests.

### Coverage

| Scope | Lines | Branches | Functions | Statements |
| --- | --- | --- | --- | --- |
| Total | 82.14 -> 82.20 | 72.59 -> 72.65 | 75.09 -> 75.29 | 79.47 -> 79.53 |
| cli | 77.82 -> 78.13 | 73.50 -> 73.70 | 77.63 -> 78.05 | 76.02 -> 76.30 |
| mcp | 86.63 -> 87.37 | 84.96 -> 87.90 | 77.92 -> 83.56 | 85.29 -> 86.58 |
| site | 98.02 -> 98.02 | 85.79 -> 85.79 | 97.29 -> 97.29 | 96.79 -> 96.79 |
| scripts | 93.80 -> 93.80 | 82.71 -> 82.71 | 100 -> 100 | 93.79 -> 93.79 |

No production file's line coverage fell, by any amount. The baseline snippet reports two files with fewer covered counts, both because their code was deleted:

- `cli/src/run.ts` branches 97/113 -> 94/109: the four arms of the two deleted `services.loadConfig ??` and `services.readLocalPreviews ??` fallbacks. Uncovered branches went from 16 to 15.
- `mcp/src/engagement.ts` lines 27/29 -> 25/25, statements 31/35 -> 28/28, branches 15/21 -> 11/12: the deleted `EngagementDeps` fallbacks. The file is now fully covered but for the `LEGLAS_PORT` unset arm; the real `post` it never ran before is covered.

The first measurement of the cutover found three real losses, each a default path the old tests reached and a compaction stopped reaching: `startViewer`'s default `installShutdown`, `runShow`'s default `fetch`, and `run`'s realpath fallback for a missing project directory. Commit d83d4ab restored all three; the final run above includes it.

## Deliberate breaks

One break per consolidation (and a few for compacted or repaired tests) in the production owner, run against the keeper's file, then restored with `git checkout` and confirmed with `git diff --exit-code`. Every break went red on the named keeper and every restore was byte for byte. The runner is a script that edits by exact unique string, so each break below is reproducible from its description.

| Id | Keeper | Moved assertion | Break | Red |
| --- | --- | --- | --- | --- |
| B1 | K-args-take | args 304/433/461: branch, basedOn, askedFor unset | `parseAdd` sets `branch: branch ?? url` | `takes ["add",…,"/?v-hero=aurora"]` |
| B2 | K-args-take | args 160: writing is the default | `let print = true` | `takes ["new","hero"]` |
| B3 | K-args-refuse | args 574: share refusals in its words | "does not take" -> "cannot take" | `refuses ["share","--fast"]` |
| B4 | K-args-refuse | args 207: add names `--title` | message says "a title" | `refuses ["add","--url","/?a"]` |
| B5 | K-baseline | baseline 15: no extension | extension kept in the specifier | re-exports a named component |
| B6 | K-explore-spread | explore 61: register as each lands | "not the set at the end" reworded | a new set must disagree |
| B7 | K-explore-variants | explore 53: `--based-on` on register | dropped from the command | variants state the opposite goal |
| B8 | K-init-section | init 86: the images | sentence reworded | the section it writes |
| B9 | K-init-ignore | ignore 22: no trailing slash | `.leglas` no longer recognised | leaves a .gitignore of ".leglas\n" |
| B10 | K-init-ignore | ignore 26: whitespace | lines not trimmed | leaves a .gitignore of "  .leglas/  \n" |
| B11 | K-init-ignore | ignore 34: one newline | a second newline appended | ends the .gitignore in exactly one newline |
| B12 | K-keep-plan | keep 64: export renamed | words not capitalised | moves the winner into real source |
| B13 | K-keep-plan | keep 51: other surfaces kept | every direction dropped | moves the winner into real source |
| B14 | K-keep-refuse | keep 105: `.leglas` destination | check compares `.leglas-x` | refuses a destination inside the ignored directory |
| B15 | K-new-framework | new 138: Next | looks for `nextjs` | recognises a Next app |
| B16 | K-new-slug | new 168: query characters stripped | `/` and `?` allowed | turns "hero/backdrop?x" |
| B17 | K-new-files | new 189: first variant | file named `hero-first.tsx` | writes a switcher named for the surface |
| B18 | K-new-ignore | new 204: no second entry | `ignoreEntry(null)` | adds the ignored directory to .gitignore, once |
| B19 | K-new-param | new 249: browser param | reads `globalThis.location` | reads the param in the browser |
| B20 | K-new-previews | new 288: suggested titles | "Hero One" | suggests config entries |
| B21 | K-show-plan | show 100: compared without variants | variants not excluded | answers with everything held |
| B22 | K-show-plan | show 111: only its requests | every request kept | answers with everything held |
| B23 | K-show-target | show 78: a file names its source | url decoded instead | names the file behind a file preview |
| B24 | K-shutdown-signals | shutdown 32: each signal stops | SIGHUP dropped from the list | handles every signal |
| B25 | K-add-note | run-previews 84: restart note | "Reload" | includes a restart note |
| B26 | K-show-malformed | run-show 429: null at 503 | `hasCaptureError` loses its null check | rejects malformed capture fields: null (503) |
| B27 | K-show-malformed | run-show 429: null at 200 | `hasCaptureSize` loses its null check | rejects malformed capture fields: null (200) |
| B28 | K-skip-check | run-update 73: `CI=false` permits | the `"false"` exception removed | {"CI":"false"} skips the check |
| B29 | run.test notice table | run-update 155 (D): JSON stays quiet | `!options.json` dropped from the guard | prints the appropriate notice for true JSON |
| B30 | K-run-boot | run 135: opens the interface | opens the dev server | boots against the config's dev server |
| B31 | run.test owner test | run 147: `--no-open` | opens regardless | warns without blocking when a local dev server belongs to another project |
| B32 | K-run-boot | run 208: config file named | label replaced | boots against the config's dev server |
| B33 | K-watch-precedence | run-watch 149: saved template beats agent | agent wins when saved | a saved template beats |
| B34 | K-watch-precedence | run-watch 139: flag beats both | saved read first and preferred | a --run flag beats both |
| B35 | K-watch-no-template | run-watch 303: JSON failure envelope | plain text under `--json` | refuses to start with no template anywhere |
| B36 | parity.test.ts 391 | tools 100 (D): the tool list | `list` registered as `lists` | every command has a tool or a reason |
| B37 | K-tools-queue | tools 333: fresh queue empty | requests clears by default | working the queue marks the session engaged |
| B38 | K-tools-explore | tools 296: basedOn passed | basedOn dropped | explore briefs the set |
| B39 | K-tools-add | tools 309: file passed | file dropped | add registers a url, a branch or a file |
| B40 | K-tools-add | tools 236: branch passed | branch dropped | add registers a url, a branch or a file |
| B41 | K-tools-add, K-tools-show | tools 249, 178: failures are errors | `isError: false` | show answers for one direction (and the add test) |
| B42 | K-tools-add | tools 263: list | list runs without `--json` | add registers a url, a branch or a file |
| B43 | api-surface.test.ts 140 | api-surface 129 (D): missing name | `publicSurface` returns an empty entry | the surface refuses to build |
| B44 | changelog.test.ts 52 | changelog 199 (D): shared heading anchors | second version's alias dropped | renders as one page that every release link lands on |
| B45 | release-notes command tests | release-notes 68 (D): the real entry reads | heading regex matches nothing | prints … from any working directory |
| B46 | K-docs-ids | docs 390: any script | ASCII-only ids | headings get GitHub's ids |
| B47 | K-docs-ids | docs 390: repeat suffix | no suffix | headings get GitHub's ids |
| B48 | K-docs-render | docs 205: paragraphs join | joined with newlines | paragraphs join their wrapped lines |
| B49 | K-docs-render | docs 234: code language | `language-` class | code is escaped and keeps its language |
| B50 | K-site-build | changelog 62: index led by the published version | index sorted oldest first | builds the pages, the docs and the captures beside them |
| B51 | engagement.test.ts (F) | the real post's route | `/api/watching` | touch starts the beat |
| B52 | engagement.test.ts (F) | a lapse says so | `post(false)` dropped | a quiet spell lets the engagement lapse |
| B53 | channel.test.ts (R, compact) | no project, no reads | the located check bypassed | stays quiet when there is no project to poll |
| B54 | bin-update.test.ts (R, compact) | the guard after a handoff | `if (handedOff()) return` removed | after a restart hands off |

## Baseline failures

None in lane L3: all 37 files passed at baseline and all 36 pass now. The four failures in this VM are L1 and L2 environment failures (no IPv6, root ignores `chmod 0o444`) and are unchanged.

## For the preservation review

- Start with the tables in `args.test.ts`: 65 declarations became 4. Each old declaration maps to rows named above; the `add()` rows share one title and url where the old tests used several.
- The four D deletions and the one move out of `run-update.test.ts` rely on keepers in this lane: `parity.test.ts` 391 (tool list), `changelog.test.ts` 52 (shared-heading anchors), `api-surface.test.ts` 140 (missing name), the release-notes command tests, and `run.test.ts`'s notice table (JSON quiet). B29 and B36 to B45 show each keeper going red.
- `run.test.ts` still replays one server contract through the built bundle (`keeps the preview idle …` posts `/api/previews/start` and expects the devCommand 400, which `server.test.ts` "validates branch start titles and the command needed to boot them" owns). It was left in on purpose: that keeper sits in lane L1, which is being pruned at the same time, so trimming here could leave the contract with no proof. Worth a look once all lanes merge.
- Coverage-blind tests in this lane were all kept: `run-watch` as a process, the stdio instructions test, the release-notes command tests, and the mcp `start` and `link` tests that boot the published bundle.
- `startViewer`'s `realpath`, `createUpdateService`, `run` and `installShutdown` injection points and `runWithServices`' `startServer` and `inspectLocalDevServer` remain test seams; each is still needed by a retained test.
