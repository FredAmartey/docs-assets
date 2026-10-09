# Lane L4 ledger: the shell

Campaign steps 3 and 4 for lane L4 (every test in `packages/shell`, Node and happy-dom), read at `516ace2` on top of `main` d7c72d9. 35 test files, 6,927 lines, 488 declarations. Target: at least 1,385 test lines out (20%), with the shell package and each shell folder within 2 points of its baseline lines and branches.

How it was read: every test file in full, with its production owner, the owner's production callers (grep over `packages/shell/src` minus tests), the file's history (`git log` back to the squashed root `a103595`, plus PRs #105, #118 and #120 of the September audit), and per-file coverage (each L4 test file run alone with `--coverage`; "unique" below counts shell statements no other L4 file hits). Baseline coverage reproduced here before any edit: shell 66.03 lines, 58.53 branches, identical to `baseline.json`.

Marks: `R` retain, `F` repair, `C` consolidate (into the named keeper), `D` delete (with the proof that remains). Line numbers are the baseline's.

## Is the target reachable?

Yes, without lowering the retention bar, but almost all of it is consolidation, not deletion. The shell's tests are mostly small pure-function suites over view models, plus one end-to-end suite (`Shell.test.tsx`) that mounts the whole interface against a table-driven fetch. The September audit already removed what mutation testing showed was dead weight, so few tests here are wholly redundant. What is left to take out is repetition: one function's cases written as five tests with five setups, three near-identical `fetch` recorders, two hand-written fake clocks that Vitest's own fake timers replace, and a handful of tests a stronger keeper already covers. Folding those keeps every contract and removes about a fifth of the lines.

Two production functions have no production caller at all (`shortLink`, `imageFilesFrom`); their tests go with them. Several injection seams exist only for tests (`PollTimers`, most of `LiveOptions`, `AgentFetcher`, `frameRefusal`'s `fetcher`, the note writes' `fetcher`); moving their tests to the real boundary (Vitest's fake timers, a stubbed global `WebSocket` and `fetch`) lets them go, so production lines fall (shell source 125 lines down).

## Ledger

### `Shell.test.tsx` (46 declarations, 1,293 lines): the keeper layer

The shell mounted whole against a server answering from a table: the strongest boundary this package has. 2,220 shell statements, 766 of `Shell.tsx` and 154 of `useShellState.ts` hit by nothing else. Kept whole; only the generation tests' repeated setup is shared and one duplicate folded.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 237 | the rail and the stage › every direction gets a row, and the one that is picked is the one on the stage | R | Row order and the picked row on stage; only test of the rail rendering every preview |
| 256 | a page that refuses to be framed says so, and offers a tab of its own | R | Only end-to-end proof of the refusal alert, the open-in-tab link and "show anyway" not asking again |
| 286 | C puts a second direction beside the first, and its row says so | R | The `c` key reaching the split through the real listener |
| 302 | folding a family moves no card sideways | R | Regression from #118: insets measured with every family open (lives in `useShellState`, unreachable from `Gutter.test.ts`) |
| 337 | a direction taken off the rail from outside › leaves the stage on the first direction still here | R | Regression 48d65b7; only test of the followed-slot fallback in `Shell.tsx` |
| 382 | a link into the interface › opens on the direction it names, and leaves the address bar as it found it | R | Deep-link contract (`link.ts` through the shell), 3de3897 |
| 391 | a link into the interface › naming two puts them side by side, the second on the right | R | `compare=` order contract |
| 398 | a link into the interface › brings back a direction taken off the list or folded into its family | R | Saved prefs from `localStorage` plus unhide/unfold on link |
| 415 | a link into the interface › a compare with no direction opens nothing and leaves the address bar | R | Refusal path of the link reader |
| 423 | a link into the interface › naming a direction this rail doesn't have changes nothing and says so | R | Refusal path, user-visible message |
| 431 | a link into the interface › when only the second direction is here, it goes on the stage alone | R | Regression faf8995 |
| 439 | a link into the interface › is not followed on somebody else's rail | R | Viewer security boundary: a link can't move a viewer's stage |
| 453 | the keys › T opens the tools, and a typeface chosen there is the one the shell wears | R | Key to panel, pref to style |
| 466 | the keys › ? lists the keys and Escape puts the list away | R | Help overlay through real key events |
| 479 | asking for a change › what is typed is what is queued, as a variant of the direction on the stage | R | Keeper, now "… as a variant of the direction on the stage or in place": the request wire body for both modes in one composer session |
| 502 | asking for a change › the chip beside the send arms a change in place | C | Into 479: after the variant request, the chip arms the next one in place and its body carries `mode: "replace"` |
| 518 | asking for a change › a change that is waiting says so above the composer | R | Status card end to end; keeper for the queued card's words in `request-status.test.ts` |
| 526 | asking for a change › the picker lists the agents on the machine, and choosing one saves it | R | Unavailable agents hidden; `POST /api/agent {agent}` |
| 599 | building directions › switched off, the rail offers no way to build them | R | Feature flag hides the UI |
| 607 | building directions › the + takes a brief and asks for the set, then the composer goes back to changes | R | `POST /api/generate` body; "Build 4 with Claude" label. Keeper for `buildLabel` |
| 635 | building directions › the brief can ask for more like the direction on the stage, with nothing typed | R | `basedOn` on the wire, "Planning 3 variations of Table…" |
| 685 | building directions › a direction still being built has nothing to vary yet | R | `likeTitle` rule |
| 695 | building directions › each direction says how it is going, on its row and on the stage | R | Row status, failure text, `POST /generate/replace` body |
| 717 | building directions › a new idea under a new title keeps the stage on that direction | R | Followed-slot rule |
| 752 | building directions › an older set that is running again leads the card and holds the brief | R | `runningJob ?? lastEnded` order |
| 772 | building directions › a dismissed card comes back when its set runs again | R | `endingOf` dismissal key |
| 806 | building directions › a retry is sent once while the set catches up | R | Double-press guard, one `POST /generate/retry` |
| 820 | building directions › nothing reads the sets when the switch is off, or for somebody else's rail | R | No `generate` read when off or for a viewer (network contract, distinct from 599's UI check) |
| 840 | building directions › a set dismissed and then retried shows its new result, not the newest set's | R | Keeper for `lastEnded` (the set that ended last, not the newest) |
| 897 | building directions › only a new set brings its first row into view, never a retry on an older one | R | Regression 4a6f608 |
| 922 | building directions › a finished set can go on the stage whole, and each name opens its direction | R | Moved under "a set shown whole" as "goes on the stage from a finished set's card, and each name opens its direction", on its `whole()` setup |
| 950 | building directions › the card counts only the finished directions still on the rail | R | "Compare all 2" with a removed slot |
| 968 | building directions › picking a row ends the whole set, so coming back shows one direction | C | Into 1049, which picks the origin row, reopens the set, picks a member, then the origin again. A break where picking a member only hides the grid turns 1049 red at its last line |
| 1022 | a set shown whole › takes no change for a direction that is off the stage, and offers no variations of it | R | Words typed before the grid can't be sent unseen |
| 1039 | a set shown whole › gives way to comparing two when a row's compare is pressed | R | Grid to split |
| 1049 | a set shown whole › ends when the row it was opened from is picked again | R | Keeper, now "ends when any row is picked, the one it was opened from included, and stays ended"; absorbs 968 |
| 1056 | a set shown whole › stays while Escape is taken by a modal or the search field | R | Escape ownership rule |
| 1073 | a set shown whole › stays while Escape closes a popover over it | R | Escape ownership rule, popover side |
| 1087 | building directions › a fix run's step shows while the page is checked, and otherwise the page is being opened | R | Slot `activity` while checking |
| 1109 | building directions › a direction being built says what its build is doing | R | Slot `activity` while building |
| 1124 | building directions › with more than one surface, the brief can build for another | R | Surface picker order and `surface` on the wire; keeper for `surfacesOf` |
| 1160 | building directions › with Codex chosen, the brief builds with Codex and its set says so | R | "Build 3 with Codex"; keeper for `buildLabel`/`agentName` |
| 1192 | building directions › with an agent other than Claude or Codex, the brief says why it cannot build | R | Nothing sent for an unsupported agent |
| 1225 | the duplicate check › an off-stage direction reloaded by a recovery is read again | R | Regression 821bc37 (#118); keeper for scan queue order, cross-origin skip and failed reads being terminal |
| 1267 | what assistive technology is told › attaching an image is one control | R | Accessibility contract |
| 1275 | somebody else's rail › a viewer can look, flip and compare, and is given nothing that changes it | R | Viewer security boundary: no write controls, nothing sent |

### `agents/agent-api.test.ts` (11, 214 lines)

The shell's half of the agent endpoints: path, method, headers and body of each call. Nothing else in the repo checks the shell's side (server tests check the server's), so the wire shapes stay. Every test hand-builds a recorder `fetcher` passed through an injection parameter no production caller uses (all eleven `Shell.tsx` call sites pass none). The table below keeps every request shape against a stubbed global `fetch`, which lets `AgentFetcher`, `browserFetch` and the `fetcher` parameters go.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 34 | reads the complete agent picker state | R | Keeper "reads the complete agent picker state, freshly detected when the picker opens", on a stubbed global `fetch` |
| 51 | can ask for a fresh detection when the picker opens | C | Row of 34: `?refresh=1` |
| 59 | posts the picked adapter as JSON, with the template when custom | R | Keeper: the writes table "posts %s" (eight rows: path, method, headers and body each), absorbing 87, 143, 160, 173 and 190 |
| 87 | saves an effort override or returns to the agent default | C | Two rows of the writes table (59) |
| 99 | stops waiting when a local agent action never answers | R | Keeper: the deadline table "stops waiting when %s never answers" (action at 10 s), absorbing 122 |
| 122 | stops waiting when agent detection never answers | C | Other row of the deadline table (99): detection at 5 s |
| 143 | names the request being stopped when it knows one | C | Row of the writes table (59) |
| 160 | wires cancellation to the running-request endpoint | C | Row of the writes table (59): bare `POST` with no headers or body |
| 173 | posts the failed id when retrying | C | Row of the writes table (59) |
| 190 | posts the failed id when dismissing | C | Row of the writes table (59) |
| 207 | rejects a refused mutation so the caller can show a toast | R | Error text the toast shows |

### `agents/mcp-connect.test.ts` (5, 46 lines)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 6 | names recognizable clients instead of using a generic other option | D | Copied fixture: restates three literals of `MCP_CONNECT_OPTIONS`; no logic, nothing reads the labels but the dialog that renders them |
| 12 | uses non-interactive npx in both setup shapes | R | The snippet people paste must run unattended (`npx -y leglas-mcp`) and the JSON must parse to the MCP shape; nothing else checks the shell's snippet (`test/copy.test.ts` only checks `for example:` prose) |
| 21 | gives each path one concrete next step | D | Substring grep of a copied constant; no behavior |
| 28 | keeps the copy action verb-first and confirms its result | R | `copyActionLabel` state mapping, the only test of it |
| 36 | does not call an idle MCP process connected before it uses a tool | R | Only test of `connectionStatus`; swapping its branches would tell people an idle agent is connected |

### `agents/request-status.test.ts` (32, 465 lines)

The status card's view model. 22 statements only it reaches. Shell.test covers one card end to end (queued, attended). The cases stay; the repetition goes into tables.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 49 | separates queued changes from work an agent has picked up | R | Keeper, now "… and a fork leaves its parent alone" |
| 61 | a fork leaves its parent's document alone | C | Into 49 (the same two functions); the regression comment moves with it |
| 77 | composerAgent › offers the chooser while agents are detected and none is chosen | R | Keeper "composerAgent offers the chooser, wears the chosen agent's name, or disappears" |
| 83 | composerAgent › disappears when no agent is detected | C | Rows of the table |
| 90 | composerAgent › wears the chosen agent's name | C | Row |
| 98 | composerAgent › gives an existing custom choice a display name | C | Row |
| 106 | composerAgent › names a custom choice after its own command | C | Three rows (aider, path to goose, blank) |
| 124 | composerAgent › drops a chosen agent whose binary is no longer detected | C | Two rows |
| 133 | requestCard › shows the run ahead of every lower-priority state | R | Full running card from the agent poll |
| 164 | requestCard › treats a running request as active before the agent poll catches up | R | Defaults ("Your agent", nulls) |
| 178 | requestCard › counts queued requests ahead of picked-up and failed states | R | Keeper "requestCard › with nothing running: the queue, then a pickup, then the latest ending", absorbing 193, 201, 211, 232, 268 and 295 |
| 193 | requestCard › says when nothing will drain the queue | C | Into 178 |
| 201 | requestCard › reports an external pickup ahead of a failed request | C | Into 178 |
| 211 | requestCard › offers the most recent failure with the reason it ended | C | Into 178 |
| 232 | requestCard › a stop is its own card, so nothing offers to redo what was stopped | C | Into 178, comment kept |
| 250 | requestCard › a stop in progress drops the backoff line and says so | R | Keeper "a run carries the vendor's backoff and its quiet, and a stop in progress drops both", absorbing 277 and 412 |
| 268 | requestCard › a failure with no recorded reason still names the direction | C | Into 178 |
| 277 | requestCard › a run inside the vendor's backoff says what it is waiting on | C | Into 250 |
| 295 | requestCard › stays empty while the queue is empty | C | Into 178 |
| 301 | waitingLabel › names the provider's own reason, with the attempt it is on | R | Status-to-words mapping |
| 319 | formatElapsed (table) | R | Already a table |
| 340 | notesAwaitingChange › collects the notes every unsettled change answers | R | Keeper "notesAwaitingChange collects the notes every unsettled change answers, and no others" |
| 352 | notesAwaitingChange › leaves out the notes of a change nobody is working on | C | Failed and cancelled rows of 340's input |
| 361 | notesAwaitingChange › a change typed with no pins contributes nothing | C | A request without `notes` in 340's input |
| 365 | notesAwaitingChange › one note answered by two changes is counted once | D | Asserts a property of `Set`: the function returns one, so a duplicate can't appear; no failure it can detect |
| 388 | what the status card says › a run names its agent, then the one useful thing about it | R | Keeper "a headline for what happened, then the one useful thing about it" |
| 399 | what the status card says › a run that has gone quiet says for how long | R | Clock-dependent detail |
| 412 | what the status card says › the card carries the quiet only while the run is not already stopping | C | Into 250 (the quiet half) |
| 434 | what the status card says › a stop in progress says so until the agent actually goes | C | Row of the headline-and-detail table |
| 439 | what the status card says › the queue counts itself and says who takes it next | C | Three rows |
| 450 | what the status card says › a failure shows the server's verdict, and the direction when there is none | C | Two rows |
| 457 | what the status card says › a stop is named as the person's own, and a pickup needs no detail | C | Two rows |

### `annotate/anchor.test.ts` (12, 183 lines)

`annotate` sits at 26% (the 884-line `AnnotateLayer.tsx` has no test); these 35 statements are only reached here, so every contract stays.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 53 | selectorFor › walks up to the body, numbering by type | R | Selector shape the agent resolves |
| 67 | selectorFor › survives a sibling of another type being inserted above | R | The reason for `nth-of-type` |
| 78 | selectorFor › stops at a stable id | R | Keeper, now "… and ignores one that cannot survive a reload" on one shared tree |
| 93 | selectorFor › ignores an id that cannot survive a reload | C | Into 78: the same tree under an unstable id |
| 102 | selectorFor › gives up at a depth that still describes an element | R | Depth cap |
| 113 | elementText › collapses the whitespace a source file leaves behind | R | Keeper "elementText collapses a source file's whitespace, caps a paragraph, and is empty for no words" |
| 117 | elementText › caps a paragraph so one note cannot flood the brief | C | Into 113 |
| 122 | elementText › has nothing to say about an element with no words | C | Into 113 |
| 133 | anchorFor › records the four facts, rounded to whole pixels | R | The stored anchor shape |
| 153 | anchorFor › keeps the pointed-at spot as a fraction of the element | R | Keeper "keeps the pointed-at spot as a fraction of the element, inside its own box" |
| 164 | anchorFor › keeps a point outside the element inside its own box | C | Row |
| 175 | anchorFor › falls back to the middle when an element has no width to divide by | C | Row |

### `annotate/annotate.test.ts` (24, 204 lines)

45 statements only here. Same rule: contracts stay, single-line cases fold.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 17 | isDrag › a press that wobbles is still a click | R | Keeper "a press that wobbles is still a click, and a deliberate sweep is a region" |
| 21 | isDrag › a deliberate sweep is a region | C | Into 17 |
| 28 | boxBetween › reads the same box dragged in any direction | R | Only test (now top-level "boxBetween reads the same box dragged in any direction") |
| 40 | overlaps and contains › an element crossing the edge overlaps but is not contained | R | Keeper "an element crossing a region's edge overlaps it, one inside is contained, and touching is neither" |
| 46 | overlaps and contains › an element wholly inside is both | C | Row |
| 52 | overlaps and contains › touching edges is not overlapping | C | Row |
| 60 | fractionsIn and boxFromFractions › records a region as a share of what holds it | R | Stored region shape |
| 71 | fractionsIn and boxFromFractions › puts a region back proportionally when the container has resized | R | Round trip |
| 83 | fractionsIn and boxFromFractions › survives a container with no size to divide by | R | Divide-by-zero guard |
| 95 | placeCard › sits under the element, aligned to its left edge | R | Default placement |
| 105 | placeCard › flips clear of the element rather than onto it | R | Flip rule |
| 114 | placeCard › aligns to the right edge rather than hanging off it | R | Keeper, now "… and stays on screen in a corner" |
| 118 | placeCard › stays on screen in the corner where both would fail | C | Into 114 |
| 127 | placeCard › gives up gracefully when the viewport cannot hold the card | R | Tiny viewport |
| 139 | cardWidth › is comfortable on a desktop pane | R | Keeper "cardWidth is comfortable on a pane, gives up width before the margin, and never too narrow to type in" |
| 143 | cardWidth › still fits with room to spare on a phone preview | C | Row |
| 147 | cardWidth › gives up width rather than the margin when the pane is tiny | C | Row |
| 151 | cardWidth › never narrows past a slot you can type a sentence into | C | Rows |
| 158 | unionOf › holds everything it was given | R | Keeper "unionOf holds everything it was given, and nothing when the sweep caught nothing" |
| 167 | unionOf › is one box when there is one box | C | Into 158 |
| 172 | unionOf › has nothing to hold when the sweep caught nothing | C | Into 158 |
| 178 | coversFrom › keeps what was given, in order | R | Keeper "coversFrom keeps what was given in order, says a thing once, and caps a big region" |
| 190 | coversFrom › says a thing once | C | Into 178 |
| 199 | coversFrom › caps a region dragged over half the page | C | Into 178 |

### `annotate/annotations-api.test.ts` (2, 47 lines)

`NoteFetcher` stays: `Shell.tsx` passes its own signalled fetcher to `readNotes`.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 22 | rewording a note › sends the id and the new words, and nothing else | R | Only test of the update wire body; now on a stubbed global `fetch`, which lets `addNote`, `updateNote` and `deleteNotes` drop their `fetcher` parameter (`readNotes` keeps it: `Shell.tsx` passes one) |
| 42 | rewording a note › refuses when the note is no longer there | R | Only test that a 404 rejects; on the stubbed `fetch` |

### `generation/generation.test.ts` (16, 228 lines)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 51 | the surface a direction belongs to › is the v- parameter its address carries | R | Keeper "a direction's surface is the v- parameter its address carries, listed once in order" |
| 56 | the surface a direction belongs to › lists every surface once, in the order the directions name them | C | Into 51 (Shell.test 1124 covers the two-surface order end to end) |
| 62 | the surface a direction belongs to › is none for an address that is not on a switch | C | Into 51 |
| 69 | a newer set's slot speaks for a title both sets have | R | Keeper, now "… and a row is a slot's only by its key" |
| 77 | the card above the composer › says what is being planned, then how the build is going | R | Keeper "the card above the composer says what is planned, how the build goes and how it ended" |
| 97 | the card above the composer › calls a set of variations what it is, from planning to its end | C | Rows (Shell.test covers only the planning line) |
| 112 | the card above the composer › gives the time a finished set took | C | Row |
| 124 | the card above the composer › names the directions that failed or were stopped | C | Rows |
| 143 | the card above the composer › passes on the server's sentence when planning failed | C | Row |
| 152 | the card above the composer › says a set was stopped, whether it had directions yet or not | C | Rows |
| 176 | a set built again in part › runs from its latest retry, not from when the set began | R | `runStartedAt`, used by the card's clock |
| 189 | a set built again in part › does not claim the whole set took the time since it began | R | Kept as its own test beside 176, which shares its fixture (Shell.test 840 uses `toContain`, so it would not catch an added " in N s") |
| 194 | a set with nothing built says so instead of counting zero | C | Rows |
| 209 | once nothing runs, the card speaks for the set that ended last, not the newest | D | Keeper Shell.test 840: the older set ends later and its "2 hero directions ready" is what shows; checked by breaking `lastEnded` (see breaks) |
| 217 | a row is a slot's only when its address carries the slot's key | C | Into 69 (who owns a title's slot) |
| 225 | the build button says how many and whose plan pays | D | Keeper Shell.test 607 ("Build 4 with Claude") and 1160 ("Build 3 with Codex"); checked by breaking `buildLabel` |

### `keymap.test.ts` (17, 126 lines)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 15 | resolveKey › resolves each binding | R | Keeper: every binding, either case, `a` included |
| 27 | resolveKey › search › takes command or control, on either platform | R | Keeper, now "… even from inside a text field" |
| 32 | resolveKey › search › still reaches the search from inside a text field | C | Into 27 |
| 36 | resolveKey › search › leaves other combinations on the same key alone | R | Shift/alt guard |
| 42 | resolveKey › search › no longer answers to a bare slash | R | Regression: `/` shares a key with `?` |
| 47 | resolveKey › jumps to a direction by digit, counting from one | R | Digits, 0 free |
| 54 | resolveKey › takes a letter binding whether or not shift is down | C | Upper-case rows of 15 |
| 61 | resolveKey › ignores everything while typing | R | Now lists `a` too |
| 67 | resolveKey › leaves meta, control and alt combinations to the browser | R | Now includes `a` with meta |
| 75 | resolveKey › binds nothing to a character that needs AltGr outside a US layout | R | Layout regression |
| 81 | resolveKey › the shortcuts it advertises are the shortcuts it resolves | R | Overlay can't drift from keys |
| 93 | resolveKey › a viewer's list leaves out the keys that change the app | R | Viewer contract (#118 rewrite) |
| 101 | resolveKey › names the search chord for the platform it is shown on | R | Platform caps |
| 106 | resolveKey › advertises no cap that needs AltGr | R | Layout regression |
| 114 | annotating › A leaves notes on the design | C | Rows of 15 |
| 119 | annotating › stays out of the way while words are being typed | C | `a` added to 61 |
| 123 | annotating › leaves the browser's own chords alone | C | `a` with meta added to 67 |

### `lineage/Gutter.test.ts` (6, 70 lines)

No unique statements (Shell.test reaches all of `railInsets`), but only these pin the inset numbers, so the rows stay.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 10 | railInsets › a rail with no families draws nothing, so every card fills its row | R | Keeper "a rail with no families draws nothing, and one puts roots past the trunk" |
| 14 | railInsets › one family puts roots past the trunk and variants past the first lanes | C | Row |
| 21 | railInsets › two siblings fork to the next lane, which a root's card already clears | C | Row |
| 36 | railInsets › a root with four variants forks out to lane 3, and both columns move to clear it | R | Now "a root with four variants › forks out to lane 3, and both columns move to clear it", sharing its fixture with 52 |
| 52 | railInsets › a folded family takes its lanes off the rail, and its root still clears its mark | R | Now "a root with four variants › folded, takes its lanes off the rail, and its root still clears its mark"; the reason Shell.test 302 exists |
| 66 | railInsets › a lone root on a rail with a family elsewhere shares the roots' column | D | `railInsets` returns one `root` value for the whole rail; the one-family row already has a lone root (Dusk) and asserts `root: 16` |

### `lineage/lineage.test.ts` (41, 519 lines)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 58 | lineageRail › each variant follows the direction it came from | R | Lineage order |
| 74 | lineageRail › depth is the real depth | R | Keeper, now "… and a root's family count is everything beneath it" (same rail) |
| 83 | lineageRail › a chain is one lane and a fork opens a second | R | Lane assignment |
| 98 | lineageRail › a direction with no family is a mark with no lines | R | Keeper; absorbs 111 |
| 111 | lineageRail › a rail drawn in family order has no gutter | C | `widestLane(new Map())` is -1, one line in 98 |
| 115 | lineageRail › a hidden direction hands its variants to the nearest one still showing | R | Hidden parent rule |
| 129 | lineageRail › a folded root keeps its row, drops the family, and still counts it | R | Fold |
| 137 | lineageRail › the family count on a root is everything beneath it | C | Into 74 |
| 146 | lineageRail › a row at any depth can fold what is beneath it | R | Drag folds |
| 158 | lineageRail › the rail names each row's parent and children | R | `parents`/`children` maps |
| 166 | lineageRail › siblings keep their saved order, and the first one carries the line | R | Sibling order |
| 176 | lineageRail › two directions based on each other still both appear | R | Cycle promotion |
| 189 | lineageRail › previews with no basedOn behave exactly as before | D | 58's rows open with Current and Ledger, which have no `basedOn`, in saved order; 98 shows such a row is a bare mark. Same code path (`visit(root, 0, …)`) |
| 198 | ancestry › root first, the direction itself left out | R | Keeper; absorbs 202 |
| 202 | ancestry › a root has none | C | One line in 198 |
| 206 | ancestry › a cycle ends where it started | R | Cycle guard |
| 220 | collapseChain › a short chain shows whole | R | Keeper "a short chain shows whole, and a long one keeps its root and its parent" |
| 228 | collapseChain › a long chain keeps its root and its parent | C | Into 220 |
| 250 | tracedSegments › a fork child's line leaves its parent along the fork | R | Hover light |
| 262 | tracedSegments › a root lights its whole family | R | Hover light |
| 275 | tracedSegments › a direction in the middle lights the line down to it and nothing past it | R | Hover light |
| 285 | tracedSegments › a direction on no line at all lights only itself | R | Keeper; absorbs 289 |
| 289 | tracedSegments › a direction that is not on the rail lights nothing | C | One line in 285 |
| 296 | segmentsOf › names every part a row draws | R | #118 rewrite |
| 314 | reorderAmongSiblings › puts a sibling before the one it should precede | R | Keeper "puts a sibling before the one it should precede, or with none after the last" |
| 321 | reorderAmongSiblings › with nothing to go before, lands after the last sibling | C | Into 314 |
| 327 | reorderAmongSiblings › moving a root moves it among the roots | R | Root move |
| 340 | reorderAmongSiblings › an empty saved order starts from the config order | R | Empty order |
| 346 | reorderAmongSiblings › a hidden sibling keeps its place in the list | R | #120 regression |
| 371 | tracedChain › runs from the family root down to the direction, root first | D | `tracedChain` is `tracedTree`'s first half and has no other caller; tracedTree 482 asserts the same chain as `nodes` |
| 382 | tracedChain › a root is a line of one | D | tracedTree 513 asserts `nodes: ["Current"]` for the same input |
| 388 | trailPath › a straight run is one line down the lane | R | Path shape |
| 400 | trailPath › a step into another lane rides the gutter's fork and arrives vertical | R | #118 rewrite, fork curve |
| 425 | trailPath › a fork with no room before the next mark goes straight there | R | Knee cut |
| 434 | trailPath › room left around a forking mark is cut off the curve, not moved down it | R | Arc-length cut |
| 455 | trailPath › the light stops short of a mark that asks for room | R | `clear` |
| 465 | trailPath › two marks with no room between them draw nothing | R | Keeper; absorbs 474 |
| 474 | trailPath › nothing to draw is an empty path | C | One line in 465 |
| 482 | tracedTree › a leaf's lineage is the line back to its family root | R | Keeper for `tracedChain` too |
| 495 | tracedTree › a root's lineage is its whole family | R | Root exception |
| 513 | tracedTree › a direction with no family is one node and no edges | R | Keeper for `tracedChain`'s single case |

### `lineage/provenance.test.ts` (10, 58 lines)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 6 | provenanceOf › reports both facts when a variant carries them | R | Keeper "provenanceOf reports whichever origin a direction records, or nothing" |
| 13 | provenanceOf › says nothing about a direction that records neither | C | Rows |
| 19 | provenanceOf › a parent alone is worth showing | C | Row |
| 23 | provenanceOf › an ask alone is worth showing | C | Row |
| 29 | provenanceOf › blank values count as absent | C | Row |
| 33 | provenanceOf › keeps the words as they were typed, less the edges | C | Row |
| 41 | provenanceLine › names the parent and the ask in one line | R | Keeper "provenanceLine names the parent and the ask in one line, or stands on either alone" |
| 47 | provenanceLine › stands on the parent alone | C | Row |
| 51 | provenanceLine › stands on the ask alone | C | Row |
| 55 | provenanceLine › has nothing to say about a direction with no origin | C | Row |

### `naming.test.ts` (10, 57 lines)

`checkName` decides what a rename means; nothing in Shell.test renames. All ten cases stay as rows of one table.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 12 | checkName › takes a fresh name | R | Keeper "checkName takes a fresh name, trimmed and with its whitespace collapsed" (with 16 and 54) |
| 16 | checkName › trims and collapses whitespace | C | Into 12 |
| 23 | checkName › an emptied field puts the config's own title back | R | Keeper "checkName puts the config's title back, or changes nothing" (with 27, 31 and 35) |
| 27 | checkName › typing the title back is a reset too | C | Into 23 |
| 31 | checkName › clearing a direction that was never renamed changes nothing | C | Into 23 |
| 35 | checkName › retyping the current name changes nothing | C | Into 23 |
| 40 | checkName › refuses a name another direction already shows | R | Keeper "checkName refuses a name another direction already shows, as it reads on screen" (with 44 and 48) |
| 44 | checkName › refuses it whatever the casing or spacing | C | Into 40 |
| 48 | checkName › names the other direction as it reads on screen | C | Into 40 |
| 54 | checkName › allows a title that has been renamed away | C | Into 12 |

### `net/live.test.ts` (9, 296 lines)

The socket loop. Moves to the real boundary: Vitest's fake timers and a stubbed global `WebSocket` instead of the injected `connect`, `setTimeout` and `clearTimeout`, which no production caller passes (`liveConnection()` calls `startLive()` bare). `browserSocket`, which only adapted the browser's socket to the injectable shape, goes with them; its text-only rule moves into the message handler. `url` stays: `server.test.ts` (lane L1) dials a real server with it, and removing it turned that test red (caught by the full run, fixed in `a37e632`). The hand-written timer fake goes.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 88 | what a frame can say › reads %s | R | Tied to the server's `LiveChange` with `satisfies` (#105, #118) |
| 92 | what a frame can say › refuses everything else | R | Annotations ride `requests` |
| 105 | retryDelay › starts quick, doubles, and stops at the ceiling | R | Ceiling only checked here |
| 117 | startLive › hands each frame to whoever asked for that kind, and nobody else | R | Dispatch, bad frames ignored; now also checks the socket dials `ws://<host>/leglas/api/live`, which the injected `url` used to hide |
| 143 | startLive › unsubscribing stops one listener without touching the others | R | Unsubscribe |
| 159 | startLive › redials on a backoff when the socket goes, and resets once one opens | R | Keeper; absorbs 230 as its last step |
| 205 | startLive › a dial that throws is treated as a failure, not an exception | R | Constructor throw |
| 230 | startLive › an error is a close: it redials once, not twice | C | Into 159: an error then a close on one socket redials once (5 sockets, not 6) |
| 255 | startLive › stopping closes the socket and cancels a pending redial | R | #118 rewrite |

### `net/poll.test.ts` (14, 413 lines)

The one-read-at-a-time loop every poll uses. Moves to Vitest's fake timers, which replace the 70-line hand-written clock and let the `PollTimers` seam go (no production caller passes `timers`).

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 113 | startPoll › reads once straight away instead of waiting out the first interval | R | First read |
| 129 | startPoll › never starts a second read while the first is still in flight | R | The loop's reason to exist |
| 149 | startPoll › starts the next read once the last one settles | R | Keeper "starts the next read once the last one settles, and a failed one frees the slot too" |
| 171 | startPoll › a failed read frees the slot instead of wedging the loop | C | Into 149: the second read rejects and a third starts |
| 190 | startPoll › aborts a read that outlives its deadline, so the socket comes back | C | Into 209: not aborted before the deadline, aborted after |
| 209 | startPoll › resumes reading after abandoning one that hung | R | Keeper "abandons a read that outlives its deadline, then resumes reading"; absorbs 190 |
| 229 | startPoll › a read that comes back in time is left alone | F | Contract kept; the old `armed() === 0` check ran at 30 s, after a leaked deadline would have fired and gone anyway, so it could not fail on its own. The timer count is now checked right after the read settles |
| 248 | startPoll › stopping aborts the read still in flight | R | Stop aborts |
| 265 | startPoll › stopping ends the loop for good | R | Keeper "stopping ends the loop for good, whatever settles after, and twice is harmless" |
| 282 | startPoll › stopping twice is harmless | C | A second `stop()` in 265 |
| 298 | startPoll › a read settling after the loop stopped changes nothing | C | 265's read now settles after the stop |
| 319 | wasAborted › knows an abandoned read from anything the server said | R | Browser and Node abort shapes |
| 348 | a loop driven by something other than the clock › a nudge reads now, and the interval still covers a silent socket | R | Live nudge plus fallback |
| 383 | a loop driven by something other than the clock › a nudge arriving mid-read is dropped, not queued behind it | R | Connection budget |

### `prefs.test.ts` (20, 170 lines)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 23 | loadPrefs › starts in config order when nothing is saved | R | Keeper "starts in config order with nothing folded when nothing is saved"; absorbs 166 |
| 27 | loadPrefs › keeps a saved order | D | 33 keeps a saved order too (`["Aurora", "Original"]` first) and also appends; same branch |
| 33 | loadPrefs › appends previews the config has added since | R | Now "keeps a saved order, appending previews the config has added since" |
| 39 | loadPrefs › forgets a preview the config no longer has | R | Keeper "forgets a preview the config no longer has, and keeps what is still there" (a kept fold and a gone one) |
| 50 | loadPrefs › keeps permanently deleted directions out of the rail | R | Tombstones |
| 67 | loadPrefs › clamps a rail width that is out of range | R | Keeper; absorbs 72. Its NaN is stored as `null` by `JSON.stringify`, so the line checks the non-number path; `Number.isFinite` has no test (follow-up) |
| 72 | loadPrefs › falls back to a sane width when the saved one is not a number | C | One line in 67 |
| 76 | loadPrefs › ignores a viewport preset that no longer exists | R | Presets |
| 81 | loadPrefs › shows the app's own dev overlays until asked otherwise | R | Keeper "shows the app's dev overlays and the tools widget, and builds nothing, until asked" |
| 88 | loadPrefs › keeps the tools widget on screen until asked otherwise | C | Rows (`showWidget`, `buildDirections`, wrong type) |
| 98 | loadPrefs › survives a corrupt store rather than refusing to start | R | Corrupt JSON |
| 102 | loadPrefs › survives a store whose fields are the wrong shape | R | Wrong shapes |
| 110 | deleteDirections › removes directions and all of their saved rail state | R | Delete |
| 127 | deleteDirections › deleting the same direction twice does not duplicate its tombstone | R | Idempotence |
| 135 | railOrder › no saved order means config order | R | Keeper "railOrder keeps the saved order, drops titles gone since and appends new ones" |
| 139 | railOrder › appends previews that arrived after the order was saved | C | Into 135 |
| 145 | railOrder › drops titles that no longer exist | C | Into 135 |
| 156 | collapsedFamilies › survives a save and load round trip | C | Into 39's stored prefs (a kept fold survives) |
| 161 | collapsedFamilies › drops roots that no longer exist | C | Into 39 (a gone root is dropped) |
| 166 | collapsedFamilies › defaults to nothing collapsed, including for pre-family saves | C | One line in 23 |

### `preview/compare.test.ts` (27, 244 lines)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 6 | nextCompare › opens against whatever you were just looking at | R | Keeper "nextCompare picks the second pane with no second choice needed" |
| 12 | nextCompare › falls back to the first other direction when there is no history | C | Row |
| 18 | nextCompare › honours a pinned direction over history | C | Row |
| 24 | nextCompare › never compares a direction against itself | C | Row |
| 30 | nextCompare › drops a pin that no longer exists | C | Row |
| 41 | nextCompare › returns nothing when there is only one direction to show | C | Row |
| 49 | paneTitles › shows one pane when the split is off | R | Keeper "paneTitles shows both panes only for a split with another direction, active on the left" |
| 53 | paneTitles › shows both panes when the split is on, active on the left | C | Row |
| 60 | paneTitles › falls back to one pane when there is nothing to compare against | C | Row |
| 64 | paneTitles › never renders the same direction twice | C | Row |
| 70 | a variant's default comparison › prefers the direction it is based on over history | C | Row of the `nextCompare` table |
| 83 | a variant's default comparison › an explicit pin still beats the parent | C | Row |
| 95 | a variant's default comparison › a parent that is not on the rail falls back to history | C | Row |
| 117 | how one side of a split is drawn › a single pane is left alone | R | Keeper "a single pane, or a split with scaling turned off, is left to the app" |
| 124 | how one side of a split is drawn › a split keeps the width it had alone and scales to fit | R | Keeper; absorbs 135 (same call) |
| 135 | how one side of a split is drawn › the frame keeps the stage's proportions, so nothing stretches | C | Two lines in 124 |
| 143 | how one side of a split is drawn › turning it off gives the pane back to the app | C | Into 117 |
| 149 | how one side of a split is drawn › a viewport preset is what gets scaled | R | Preset scaling |
| 156 | how one side of a split is drawn › a set shown whole keeps the design's width and fits each cell | R | Grid geometry |
| 170 | how one side of a split is drawn › an inset keeps room around each frame | R | Inset |
| 178 | how one side of a split is drawn › a set is laid out one row for up to three, then two rows | R | `setLayout` |
| 188 | how one side of a split is drawn › a preset narrower than the pane is never scaled up | R | Keeper "a preset narrower than the pane is never scaled up, and its box is its own size"; absorbs 220 |
| 194 | how one side of a split is drawn › a stage not measured yet does not divide by zero | R | Keeper "a stage not measured yet, or a pane dragged to nothing, still yields a usable scale" |
| 201 | how one side of a split is drawn › a pane dragged to nothing still yields a usable scale | C | Into 194 |
| 211 | a framed preset inside a split › is scaled from the height it has unsplit | R | Gutter height |
| 220 | a framed preset inside a split › box size stays the on-screen size even when nothing is scaled | C | Into 188, whose call (`panes: 2`, `viewport: 390`) is the same; its `boxWidth`/`boxHeight` lines move there |
| 229 | sub-pixel stage widths › the design width is not rounded | R | Breakpoint regression |

### `preview/framing.test.ts` (4, 90 lines)

`frameRefusal`'s `fetcher` parameter has no production caller (`Shell.tsx` calls `frameRefusal(title)`); the tests move to a stubbed global `fetch` and the parameter goes.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 12 | frameRefusal › names the header that refused the frame | R | Keeper "names the header that refused the frame, and anything short of that is no refusal", on a stubbed `fetch` (the `fetcher` parameter goes) |
| 21 | frameRefusal › anything short of a clear refusal leaves the pane alone | C | Into 12 |
| 43 | refusalWords › says which site refused, and why, in the header's own words | R | Keeper "says which site refused, why in the header's own words, and the header that would fix it" |
| 78 | refusalWords › tells the site's owner the one header that would change it | C | Into 43 (the hint does not depend on the site) |

### `preview/health.test.ts` (10, 66 lines)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 11 | nextHealthState › stays up while the dev server keeps answering | D | 27 asserts `nextHealthState(up, true)` is `up` itself, which implies this `toEqual` |
| 15 | nextHealthState › goes down the moment it stops answering | R | Keeper "goes down the moment it stops answering, and remembers it after it comes back" |
| 19 | nextHealthState › remembers it was down after it comes back | C | Into 15 |
| 23 | nextHealthState › does not re-arm recovery while it stays down | D | 27 asserts `nextHealthState(down, false)` is `down` itself |
| 27 | nextHealthState › hands back the same state when nothing changed | R | Identity, so a poll is not a render |
| 34 | nextHealthState › treats the first successful check as ordinary | R | #118: optimistic boot |
| 49 | needsDevServer › a route on the running app depends on it | R | Keeper "only a route on the running app depends on it" |
| 53 | needsDevServer › a file preview is served by Leglas, not the app | C | Row |
| 59 | needsDevServer › a branch preview runs its own checkout | F | Into 49, and repaired: the branch row used an absolute URL, so it passed on the URL rule with the branch rule removed (checked: green under that break before the repair, red after). It now uses a root-relative URL |
| 63 | needsDevServer › an absolute url answers for itself | C | Row |

### `preview/overlays.test.ts` (6, 50 lines)

The CSS `Shell.tsx` injects into same-origin previews. The safety half (never hide an error overlay) is the contract worth most; the badge list is the user-visible half.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 18 | BADGE_CSS › hides the badges it is meant to | R | Keeper, now "… in one declaration that cannot leak into app styling" |
| 24 | BADGE_CSS › never touches an element that could be an error overlay | R | Safety: a hidden error overlay passes a broken preview as healthy |
| 30 | BADGE_CSS › is a single declaration, so it cannot leak into app styling | C | One line in 18 |
| 36 | NEXT_BADGE_CSS › targets only the dev tools indicator inside the portal | R | Keeper "targets only the dev tools indicator inside the portal, never the portal or its modal" |
| 42 | NEXT_BADGE_CSS › does not hide the portal itself | C | Into 36 |
| 46 | NEXT_BADGE_CSS › does not use a wildcard that would catch the error modal | C | Into 36 |

### `preview/preview-frame.test.ts` (8, 156 lines)

Every readiness test builds the same watcher by hand; one `watch` helper carries it. Marks are unchanged by that.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 41 | preview iframe readiness › recognizes a cached same-origin document immediately | R | Cached-load race |
| 54 | preview iframe readiness › waits through about:blank and accepts the real load event | R | about:blank |
| 69 | preview iframe readiness › treats a cross-origin load event as the only available success signal | R | Cross-origin |
| 85 | preview iframe readiness › checks the rendered document once more before timing out | R | Late check |
| 98 | preview iframe readiness › reports a real navigation failure exactly once | R | Error once |
| 115 | preview iframe readiness › removes listeners and timers when its owner unmounts | R | Cleanup |
| 138 | preview loading identity › separates URL changes and explicit reloads of one title | R | Keeper, now "… and forgets a prior mount" |
| 149 | preview loading identity › forgets a prior mount before the same identity is shown again | C | Into 138 |

### `preview/preview-message.test.ts` (2, 32 lines)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 15 | preview message protocol › recognizes only the two preview lifecycle messages | R | Inbound protocol |
| 22 | preview message protocol › resolves the sender from mounted frame windows instead of message text | R | Security: sender by `WindowProxy`, never by message data |

### `preview/rendered.test.ts` (25, 355 lines)

The duplicate verdict. 91 statements only here (no frame loads in happy-dom, so Shell.test can't reach a signature).

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 12 | renderedSignature › different words disagree | R | Keeper: "different words or structure disagree" |
| 19 | renderedSignature › the same words in a different structure disagree | C | Into 12 |
| 28 | renderedSignature › ignores whitespace, which reflows without changing the design | R | Keeper "ignores whitespace and case, which reflow and style without changing the design" |
| 35 | renderedSignature › ignores case, since a text-transform is styling not content | F | Into 28, and repaired: "SHIP DESIGN" and "Ship design" are under the 12-character floor, so both signatures were `null` and the test passed with case kept (checked: the baseline file stays green under that break). Now signed text, asserted non-null |
| 39 | renderedSignature › says nothing about a page that drew nothing yet | R | Keeper; absorbs 44 |
| 44 | renderedSignature › treats a bare app shell as nothing drawn | C | One line in 39 |
| 52 | twinsOf › pairs previews that drew the same page | R | Keeper "pairs previews that drew the same page, and says nothing of a unique one" (whole-result `toEqual`) |
| 59 | twinsOf › says nothing about a preview that is unique | C | Covered by 52's whole-result `toEqual` |
| 65 | twinsOf › groups three that all match | R | Groups |
| 71 | twinsOf › ignores previews that have not drawn yet | R | Null signatures |
| 77 | twinsOf › returns nothing when every preview differs | D | Same branch as 59 (a group of one is skipped); 52's whole-result `toEqual` covers it |
| 86 | paint in the signature › colour variants of one direction are different pages | R | Regression: variants read as duplicates |
| 102 | paint in the signature › no paint sample behaves as before | R | #118 kept it: the only test catching a default-parameter mutant |
| 106 | paint in the signature › the same copy and paint in a different layout is not a duplicate | R | Layout in the signature |
| 120 | paint in the signature › pseudo-elements, vector geometry and media sources affect the verdict | R | Visual sample in the signature |
| 231 | visualSample › captures geometry that text-and-tag comparison misses | R | Geometry |
| 235 | visualSample › captures vector path changes | R | Paths |
| 241 | visualSample › half-pixel quantisation ignores sub-raster noise | R | The "differs at half a pixel" side is only here |
| 249 | visualSample › one design read twice still agrees, mid-animation and through sub-pixel noise | R | #118 rewrite |
| 291 | paintSample › a script beside the root is not a branch | C | Into 305: the script sits beside the wrapper chain in one tree |
| 305 | paintSample › descends single-child wrappers to find the page surface | R | Keeper "descends single-child wrappers to find the page surface, past a script beside them" |
| 315 | paintSample › stops where the tree branches | R | Stop rule |
| 321 | paintSample › caps the descent so a deep chain stays cheap | R | Cap |
| 329 | paintSample › returns nothing for a missing body | R | Null body |
| 335 | signature size › the signature is a digest, not the sample it was read from | R | Memory bound |

### `preview/scan.test.ts` (13, 152 lines)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 21 | scanQueue › a branch preview that has not started has no url yet | R | Regression: thrown on an undefined url |
| 32 | scanQueue › queues same-origin previews without current results | R | Now "… not the sealed cross-origin one"; absorbs 40's claim |
| 40 | scanQueue › skips cross-origin previews, whose documents are sealed | D | 32's `toEqual(["Current", "Aurora", "Paper"])` already leaves Staging out (same input); Shell.test 1225 skips a cross-origin one end to end |
| 44 | scanQueue › treats complete and failed reads as terminal for their exact URL | R | Terminal reads |
| 54 | scanQueue › requeues a title when its URL changes | R | URL identity |
| 69 | scanQueue › previews that appear mid-session join the queue | R | Mid-session |
| 85 | scan records › keeps failures separate from valid empty signatures | R | Record shapes |
| 93 | scan records › forgets only the directions whose documents are changing | R | `forgetScans` |
| 109 | replacedPanes › a direction coming on stage keeps its verdict | R | Keeper "replacedPanes reads again only a pane whose document was replaced in place" |
| 118 | replacedPanes › a pane reloaded in place is read again | C | Row |
| 125 | replacedPanes › a pane whose url changed under the same title is read again | C | Row |
| 132 | replacedPanes › leaving the stage and coming back changes nothing | C | Two rows |
| 139 | replacedPanes › only the replaced pane of a split is read again | C | Row |

### `rail/tags.test.ts` (3, 33 lines)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 7 | a tag keeps its colour from one session to the next | R | #118 rewrite across module instances |
| 18 | the pill is the tone at full strength on a wash of itself | R | #118 kept it: only test catching its mutant |
| 24 | amber is never a tag's colour, because amber means duplicate | R | Colour contract with the duplicate mark |

### `reference.test.ts` (15, 107 lines)

The block the clipboard carries for an agent or a teammate.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 22 | referenceText › leads with the title, note and tags | R | First line |
| 27 | referenceText › says nothing where there is nothing to say | R | Bare first line |
| 33 | referenceText › prints both names when the rail shows a different one | R | Keeper, now "… and points at the config title" |
| 39 | referenceText › names the file a file-backed direction is built from | R | Keeper "names the source an agent edits: a file over the route, a branch, or the route" |
| 43 | referenceText › names the branch a branch-backed direction runs from | C | Row |
| 47 | referenceText › names the route for an ordinary direction | C | Row |
| 51 | referenceText › prefers the file over the route | C | Into 39 |
| 57 | referenceText › carries the parent of a variant | R | Keeper "carries the parent of a variant, and no parent line for a root" |
| 61 | referenceText › omits the parent line for a root direction | C | One line in 57 |
| 65 | referenceText › always ends with the way to get the rest, addressed by config title | R | The `npx leglas show` pointer |
| 72 | referenceText › points at the config title even when the row was renamed | C | One line in 33 |
| 76 | referenceText › survives a title it has no preview for | R | Missing preview |
| 90 | absoluteUrl › resolves a root-relative preview against the shell's origin | R | Keeper "absoluteUrl resolves a root-relative preview against the shell's origin, and leaves the rest" |
| 98 | absoluteUrl › leaves an already absolute preview alone | C | Into 90 |
| 104 | absoluteUrl › falls back to the raw value rather than throwing | C | Into 90 |

### `references/references.test.ts` (17, 181 lines)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 32 | imageFilesFrom › keeps the images and drops the rest of what was pasted | D | `imageFilesFrom` has no production caller in this repository's history (only its tests); function deleted |
| 44 | imageFilesFrom › reads an array-like FileList shape too | D | Same |
| 58 | admit › refuses at exactly the server's limit | R | Shared cap with the server's upload test (#118) |
| 68 | admit › takes images up to the cap, counting what is already attached | R | Keeper; absorbs 76 with a stronger case |
| 76 | admit › refuses a file over the size cap without spending a slot on it | C | Into 68, made stronger: an oversized file offered first against a two-slot room. The old test had four free slots, so a spent slot could not show (checked: the baseline file stays green when an oversized file spends a slot; 68 goes red) |
| 83 | admit › refuses what is not an image, whatever it is called | R | Type over name |
| 88 | admit › a full strip takes nothing more | D | Same `room === 0` branch 68 reaches after two admissions |
| 95 | refusalMessage › says nothing when nothing was refused | C | Into 99 |
| 99 | refusalMessage › explains the cap in the strip's own terms | R | Keeper "explains the cap in the strip's own terms, and says nothing when nothing was refused" |
| 111 | refusalMessage › names the file that was not an image | R | Words |
| 119 | refusalMessage › the first reason speaks for a batch | R | Precedence |
| 130 | names and sizes › a nameless paste is still called something | R | Keeper "a nameless paste is still called something, and its header form is bounded ascii" |
| 135 | names and sizes › the header form is printable ascii and bounded | C | Into 130 |
| 141 | names and sizes › bytes read the way people say them | R | `describeBytes` |
| 150 | what a request names › only uploads that landed become ids | R | Keeper "only uploads that landed become ids, and a failed one blocks the send" |
| 161 | what a request names › a failed upload blocks the send | C | Into 150; the precedence row now has the upload in flight before the failure, so a first-unfinished-draft rule fails it |
| 176 | carriesFiles › reads the drag's declared types | R | Drag detection |

### `share/share.test.ts` (20, 284 lines)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 40 | railShare › carries what is showing, in rail order, and names what cannot go | R | Manifest |
| 54 | railShare › keeps a rename only for a direction that goes | R | Keeper "keeps a rename only for a direction that goes, and with no saved order uses config order" |
| 60 | railShare › a rail with no saved order shares config order | C | Into 54 |
| 67 | stageShare › one direction on stage is a direction share | R | Scope |
| 76 | stageShare › a split stage is a compare share with the pair set | R | Scope |
| 83 | stageShare › refuses a pair with a branch on one side | R | Keeper "refuses a pair with a branch or a gone direction on one side, naming it as the rail does" |
| 89 | stageShare › an empty stage has nothing to share | C | Into 83 |
| 95 | unshareableReason › a branch preview cannot go; a route can | C | Into 83 through `stageShare` ("Gone is not on the rail"); the branch and route halves were already in 40 and 83. `unshareableReason` loses its test-only `export` |
| 106 | sameShare › is blind to rename order, fold order and its route list, and to nothing else | R | #118 rewrite |
| 153 | viewerPrefsRaw › seeds a viewer's rail through the same validation as a saved one | D | `adoptLayout` is `loadPrefs(viewerPrefsRaw(layout))` plus the viewer's own fields, and 163 asserts the same four seeded fields; the extra `hidden: []` can't change, since `ShareLayout` has no hidden list |
| 163 | viewerPrefsRaw › adopting a pushed layout takes its fields and keeps the viewer's own | R | Keeper for the seeding |
| 197 | observedRoutes › takes the paths a shared direction loaded, from this origin only | R | Route seed |
| 219 | observedRoutes › a frame it cannot read costs nothing | R | Cross-origin frame |
| 233 | words › scopeLine says the rail with its count, or names the pair | R | Words |
| 241 | words › viewersLine counts sessions, never people | R | Keeper "viewersLine counts sessions, never people, and totalViewers counts across every link" |
| 247 | words › expiryLine reads in hours until the last hour, then minutes | R | Words |
| 258 | words › totalViewers counts across every link | C | Into 241 |
| 264 | words › directoryOf offers the folder beside a refused path, never the root | R | Root never offered |
| 272 | words › grantLabel names an unnamed link by its place | R | Words |
| 278 | words › shortLink keeps the host and hides the token | D | `shortLink` has no production caller in this repository's history; function deleted |

### `ui/clipboard.test.ts` (6, 58 lines)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 8 | copyText › uses the async clipboard when it works | R | Fallback chain |
| 18 | copyText › falls back when permission is refused | R | Fallback chain |
| 32 | copyText › falls back when there is no async clipboard at all | R | LAN context |
| 36 | copyText › reports blocked when neither path lands | R | Keeper, now "… or the environment offers neither" |
| 45 | copyText › reports blocked rather than throwing when the legacy command is gone | R | Throwing legacy |
| 55 | copyText › reports blocked when the environment offers nothing | C | One line in 36 |

### `ui/kit.test.tsx` (3, 113 lines)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 43 | a tip's label mounts on the shell, outside whatever clips its control | R | #118 rewrite; mount and hover now shared by the three tests |
| 65 | inside a modal dialog the label stays in the dialog | R | Top layer |
| 85 | with no shell around it the label goes to the body, and leaves when the pointer does | R | #118 rewrite |

### `ui/orb.test.ts` (5, 27 lines)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 6 | orbMood › spreads rolls across every mood | R | Every mood reachable |
| 12 | orbMood › the smallest roll lands on the first mood | R | Keeper "keeps every roll on the list, clamping one out of range to the nearer end" |
| 16 | orbMood › a roll just under one lands on the last mood | C | Row |
| 20 | orbMood › clamps a roll of exactly one | C | Row |
| 24 | orbMood › clamps a negative roll | C | Row |

### `ui/tip.test.ts` (12, 100 lines)

`fitShift` and `shouldFlipBelow` are `placeTip`'s halves with no other caller; `placeTip` is what `kit.tsx` calls. Where a helper case restates a `placeTip` case it goes.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 15 | fitShift › leaves a tooltip that already fits alone | R | Keeper "fitShift leaves a tooltip that fits, pulls one in from the right, and pins a wide one left" |
| 19 | fitShift › pulls in a tooltip that runs past the right edge | C | Into 15 |
| 27 | fitShift › pushes out a tooltip that runs past the left edge | D | placeTip 70 lands the same left edge on `TIP_MARGIN` |
| 32 | fitShift › applying the shift once is enough | D | placeTip 76 ("settles after one correction") is the same idempotence at the caller |
| 39 | fitShift › pins a tooltip wider than the viewport to the left edge | C | Into 15 |
| 46 | shouldFlipBelow › flips when the tooltip is cut off at the top | D | placeTip 95 flips the same way |
| 53 | shouldFlipBelow › stays put when there is room above | R | Keeper "shouldFlipBelow stays put when there is room above, or when below is no better" |
| 59 | shouldFlipBelow › stays put when below is no better | C | Into 53 |
| 70 | placeTip › shifts a tooltip off the left edge back on screen | R | Keeper "shifts a tooltip off the left edge back on screen, and settles after one correction" |
| 76 | placeTip › settles after one correction | C | Into 70 |
| 85 | placeTip › re-fits when the label grows while it is open | R | Regression: grown label clipped |
| 95 | placeTip › flips below when there is no room above, then fits | R | Flip |

### `ui/toasts.test.ts` (7, 59 lines)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 15 | pushToast › supersedes an earlier toast of the same kind | D | 26 supersedes too (`[2, 3]` after a second "copy") and also checks the order |
| 20 | pushToast › keeps one toast per removed direction, so each undo survives | R | Kind grouping |
| 26 | pushToast › moves a superseded kind to the end | R | Keeper for superseding |
| 31 | pushToast › drops the oldest past the limit | R | Limit |
| 42 | pushToast › carries the undo through untouched | D | Identity copier: `pushToast` only filters and slices the array, so the entry is the same object; no failure it can detect |
| 50 | dismissToast › removes only the toast asked for | R | Keeper "dismissToast removes only the toast asked for, and nothing once it is gone" |
| 55 | dismissToast › leaves the stack alone when the id is already gone | C | Into 50 |

### `ui/widget.test.ts` (12, 107 lines)

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 15 | clampWidget › keeps the widget inside the stage | R | Keeper "keeps the widget inside the stage, off every edge, and leaves it be inside" |
| 22 | clampWidget › keeps it off the top and left edges too | C | Row |
| 29 | clampWidget › leaves a position that is already inside alone | C | Row |
| 33 | clampWidget › survives a stage smaller than the margins without inverting | C | Into 15 |
| 42 | nearestCorner › snaps to the bottom right | R | Keeper "nearestCorner snaps to the corner it is in, and the exact centre to bottom right" |
| 46 | nearestCorner › snaps to the top left | C | Row |
| 50 | nearestCorner › snaps to the bottom left | C | Row |
| 54 | nearestCorner › snaps to the top right | C | Row |
| 58 | nearestCorner › treats the exact centre as bottom right | C | Row |
| 69 | isDrag › treats pointer travel during a tap as a click, not a drag | R | Threshold regression |
| 86 | isDrag › treats deliberate travel as a drag | R | Threshold |
| 101 | dragAnchor › centres the button on the pointer | R | Pointer regression |

### `update/update.test.ts` (18, 324 lines)

The update panel's view model; 49 statements only here. The twelve `updateView` tests each build a status, call once and check a few fields: one table with `toMatchObject` keeps every field they check.

| Line | Test | Mark | Evidence |
| --: | --- | :-: | --- |
| 38 | ago › rounds down to the unit a person would say | R | Keeper; absorbs 47 |
| 47 | ago › an unreadable time is not a number on screen | C | One line in 38 |
| 53 | hasNews and the chip › a newer version that was not skipped is news | R | Keeper "a newer version that was not skipped is news; a skipped one, or being up to date, is not" |
| 58 | hasNews and the chip › a skipped version is not, and neither is being up to date | C | Into 53 |
| 67 | updateView › before the first read there is only a spinner | R | Keeper "with nothing newer: a spinner, then a check to run, its answer or why it failed" (73, 81, 95, 102) |
| 73 | updateView › never checked offers a check | C | Into 67 |
| 81 | updateView › up to date says so and when it was checked | C | Into 67 |
| 95 | updateView › a check in flight disables the button and says who it is asking | C | Into 67 |
| 102 | updateView › a failed check quotes the server's sentence and offers a retry | C | Into 67 |
| 116 | updateView › a newer version leads with it and says what Update will run | R | Keeper "a newer version leads with it and says what Update will run" (135, 161, 173) |
| 135 | updateView › each install kind gets its own note | C | Into 116 |
| 161 | updateView › a running change holds the button and says why | C | Into 116 |
| 173 | updateView › a skipped version stays offered, without the skip | C | Into 116 |
| 186 | updateView › installing and restarting show progress and nothing to press | R | Keeper "an update under way shows its progress and nothing to press, and a failed one what to do" (224) |
| 224 | updateView › a failed install gives the reason, a retry and the command to run by hand | C | Into 186 |
| 243 | updateView › the wait states win over whatever the last status said | R | Kept as its own test (the three waits) |
| 277 | the commands a person is told › pinnedCommand names the version that will be installed | R | Command pinning |
| 281 | the commands a person is told › startAgain matches how Leglas was started | R | Restart command per install kind |

## Totals

Final marks, after the cutover. Marks changed from the first draft where the cutover found more (second-pass folds of tests that turned out to share a call, three assertions that could not fail) or kept a test whole that the draft had folded; each changed row says what happened.

| Mark | Declarations |
| --- | --: |
| R | 293 |
| F | 3 |
| C | 168 |
| D | 24 |
| **All** | **488** |

R plus the one standalone F (poll 229) is 294, the lane's declarations after the cutover; the other two Fs were repaired as they were folded into keepers.

## Result

| | Baseline | Now | Change |
| --- | --: | --: | --: |
| L4 test lines | 6,927 | 5,539 | −1,388 (20.0%) |
| L4 declarations | 488 | 294 | −194 |
| L4 test files | 35 | 35 | 0 |
| Shell source lines (`packages/shell/src`, no tests) | 17,112 | 16,987 | −125 |
| Lane cases run (`vitest run packages/shell`) | 500 | 313 | −187 (3 of 3 runs green) |

Coverage, `pnpm test:coverage` on the final head with the baseline's environment (Node 24, the `--no-sandbox` Chromium in `LEGLAS_BROWSER`). The run is comparable: the baseline's 4 failures, 2 skipped and 2 errors, and 1,672 passed (1,859 less this lane's 187 cases). A first full run on the earlier head had a fifth failure, `server.test.ts` › "an announced update reaches the interface's update listener": it dials the shell's `startLive` with `url`, which the cutover had removed. `a37e632` puts `url` back (red without it, green with it).

| Scope | Lines | Branches | Functions | Statements |
| --- | --- | --- | --- | --- |
| Total | 82.14 → 82.11 | 72.59 → 72.57 | 75.09 → 75.04 | 79.47 → 79.46 |
| shell (budget ±2 on lines and branches) | 66.03 → 65.85 | 58.53 → 58.38 | 59.09 → 58.78 | 63.74 → 63.61 |
| cli, mcp, server, site, scripts | unchanged | unchanged | unchanged | unchanged |

| Shell folder | Lines | Branches |
| --- | --- | --- |
| (src root) | 61.65 → 61.65 | 54.85 → 54.92 |
| agents | 79.14 → 79.01 | 76.20 → 75.57 |
| annotate | 26.08 → 26.08 | 21.08 → 20.97 |
| net | 95.00 → 94.39 | 77.77 → 76.92 |
| preview | 86.22 → 86.22 | 80.28 → 80.18 |
| references | 77.04 → 76.27 | **63.49 → 61.01 (−2.48, outside the budget)** |
| share | 54.26 → 53.54 | 44.82 → 44.82 |
| composer, generation, lineage, rail, stage, ui, update | unchanged | unchanged |

No production file's line coverage fell more than 5 points (0 of 169). Seven shell files show fewer covered counts (`agent-api.ts`, `annotations-api.ts`, `live.ts`, `poll.ts`, `framing.ts`, `references.ts`, `share.ts`), and each is a file this lane deleted code from: the seams' default parameters, `browserSocket`, `realTimers`, `shortLink` and `imageFilesFrom`. Matching statements and branch arms by source text rather than line number (baseline coverage on `516ace2`'s sources against final coverage on the current ones), no statement or branch arm that still exists lost coverage, in any shell file. The same check against a run of `Shell.test.tsx` alone reports losses in `keymap.ts`, `naming.ts`, `prefs.ts` and more, so it does detect them.

**The one breach.** `shell/references` branches fall 2.48 points, 0.48 past the per-folder budget. All of it is `imageFilesFrom`, which no production code has ever called: its four covered branches left both sides of the ratio. Over the code that still exists the folder's branch coverage is the same before and after (36 of 59). Keeping it inside the budget means either keeping the dead function and its two tests, or covering two refusal messages no test checks today (`refusalMessage` for one oversized image and for several non-images, `references.ts:101` and `:104`). Neither was done; it is Fred's call.

## Layer plan

The lane has two layers: `Shell.test.tsx`, the mounted interface against a table-driven server, and per-module unit suites over pure view models and small loops. No unit suite replays another; the redundancy is inside suites (one function's cases as many tests) and between a few unit tests and the end-to-end suite.

**Keepers per contract.**

- The interface as a whole (keys reaching panels, wire bodies, viewer restrictions, generation flows, deep links, the duplicate scan's queue and recovery): `Shell.test.tsx`. It absorbs `buildLabel` (Shell.test 607 and 1160), `lastEnded` (840), the scan queue's cross-origin skip (1225, with `scan.test.ts` 32) and the queued card's words (518).
- The agent endpoints as the shell calls them: `agent-api.test.ts`, one read test, one write table, one deadline table, against a stubbed global `fetch`.
- The socket loop and the poll loop: `live.test.ts` and `poll.test.ts` on Vitest's fake timers, the socket through a stubbed global `WebSocket`; `server.test.ts` (L1) still runs both halves of the live protocol together.
- Each view model (status card, generation card, update panel, compare, prefs, share, lineage, references, reference block, rename check, provenance, tips, widget, toasts, annotation geometry): its own suite, one test per rule where its cases differed only in input.

**Files retired.** None whole. Every file keeps at least one contract nothing else checks. The two smallest candidates were checked: `mcp-connect.test.ts` keeps the snippet test (nothing else checks what people paste), `health.test.ts` keeps the recovery flag the end-to-end recovery test depends on.

**Shape of the cut.** Tables with descriptive row names grew under Prettier's 100-column width (a first pass at `request-status.test.ts` saved 23 of 465 lines), so most folds became one test per rule with sequential expectations and a short comment naming each case, the idiom this repository already uses in `waitingLabel`, `scopeLine` and similar tests.

**Deletions by category** (24 `D`):

- Dead production code whose only callers were tests: `shortLink`, `imageFilesFrom` (3 tests).
- Duplicate of a stronger keeper in the same file: health 11 and 23, toasts 15, tip 27, 32 and 46, scan 40, prefs 27, references 88, rendered 77, lineage 189, Gutter 66, share 153 (13).
- Duplicate of an end-to-end keeper in `Shell.test.tsx`: generation 209 (`lastEnded`), 225 (`buildLabel`) (2).
- Duplicate of the caller's test, for a helper with no other caller: lineage 371 and 382 (`tracedChain`, through `tracedTree`) (2).
- Copied fixtures and strings with no behaviour: mcp-connect 6 and 21 (2).
- A property of `Set` asserted (request-status 365) and an identity copier (toasts 42) (2).

**Repairs** (3 `F`): poll 229 (a timer check that ran too late to fail), health 59 (a branch row that passed on its URL), rendered 35 (a case test under the signing floor). Each was shown green under its break before the repair and red after. Not an F but stronger than before: references 76, folded into 68 with a room it can actually run out of.

**Test-only production seams removed.**

- `net/poll.ts`: `PollTimers`, `realTimers` and the `timers` option.
- `net/live.ts`: the `connect`, `setTimeout` and `clearTimeout` options, the `LiveSocket` and `LiveEvent` shapes and the `browserSocket` wrapper. `url` stays (see above).
- `agents/agent-api.ts`: `AgentFetcher`, `browserFetch` and the `fetcher` parameter on seven functions.
- `annotate/annotations-api.ts`: the `fetcher` parameter on `addNote`, `updateNote` and `deleteNotes` (`readNotes` keeps it; `Shell.tsx` passes one).
- `preview/framing.ts`: `frameRefusal`'s `fetcher` parameter.
- Dead code: `share/share.ts` `shortLink`, `references/references.ts` `imageFilesFrom`.
- Test-only `export`s dropped: `lineage.ts` `tracedChain`, `share.ts` `unshareableReason`.

None of these is in `api-surface.txt` (the shell is private; the file lists only `leglas` and `leglas-mcp`).

**Seams noticed and left** (follow-ups, no test deletion unlocks them): `references/references-api.ts` `uploadReference` takes a `fetcher` nothing passes and no test uses; `ui/clipboard.ts` `CopyDeps` and `browserCopy` exist for its tests; `toasts.ts` `pushToast`'s `limit` is passed by nobody. Other test-only exports that stay because their tests are the cheapest guard of the rule: `changeFrom`, `isLiveChange`, `retryDelay`, `waitingLabel`, `selectorFor`, `quantiseCssPixel`, `orbMood`, `fitShift`, `shouldFlipBelow`, `pinnedCommand`, `startAgain`.

**A rule this campaign found.** Shell modules are imported by other packages' tests: `server.test.ts` imports `net/live.ts` and `references/references.ts`, and three cli tests and `mcp/src/tools.test.ts` import `link.ts`. A seam that no shell caller uses can still have a caller in another lane. Grep the whole repository, tests included, before removing an option or export. The repository has no `AGENTS.md` to record this in; worth one in `packages/shell` if Fred wants it.

## Breaks (step 5)

Every consolidation that moved an assertion into a keeper, and every `D` that leans on a keeper elsewhere, got one deliberate edit of the production owner, a run of the keeper's file, and a restore checked by SHA-256 of the file before and after (all restored byte for byte). Logs are not committed; each break is a single string replacement listed here, so it can be replayed.

Line numbers in the last column are the test file's at the time of the break; later folds in the same file moved some of them.

| Consolidation | Break in the production owner | Keeper that went red, and where |
| --- | --- | --- |
| poll 190 → "abandons a read that outlives its deadline, then resumes reading" | `net/poll.ts`: the deadline fires at `timeoutMs / 2` | That test, `poll.test.ts:97` (`signals[0].aborted` true at 9 s); 10 others green |
| poll 282 → "stopping ends the loop for good, whatever settles after, and twice is harmless" | `net/poll.ts`: `stop()` throws when called a second time | That test, `poll.test.ts:141` (`not.toThrow`) |
| poll 298 → the same test | `net/poll.ts`: `stop()` neither sets `stopped` nor clears the interval | That test, `poll.test.ts:140` (31 reads, expected 1), and "stopping aborts the read still in flight" (`:129`, a timer left) |
| agent-api 51 → "reads the complete agent picker state, freshly detected when the picker opens" | `agents/agent-api.ts`: `readAgents` drops `?refresh=1` | That test, `agent-api.test.ts:53` |
| agent-api 160 → writes table row "a stop of whatever is running" | `agents/agent-api.ts`: `cancelAgentRun(null)` posts `{}` instead of no body | That row, `agent-api.test.ts:108`; the other 11 green |
| agent-api 87 → writes table rows "an effort override", "a return to the agent's default effort" | `agents/agent-api.ts`: `chooseAgentEffort` leaves `effort` out of the body | Both rows, `agent-api.test.ts:108` |
| agent-api 122 → deadline table row "agent detection" | `agents/agent-api.ts`: read deadline 5 s → 6 s | That row, `agent-api.test.ts:126` (still pending at 5 s) |
| request-status 83-124 → "composerAgent offers the chooser, wears the chosen agent's name, or disappears" | `agents/request-status.ts`: a custom command keeps its path (no `split("/").pop()`) | That test, `request-status.test.ts:92` (the goose row) |
| request-status 178-295 → "with nothing running: the queue, then a pickup, then the latest ending" | `agents/request-status.ts`: `requests.findLast` → `find` (oldest ending) | That test, `:180` (`older` shown, `newer` expected) |
| request-status 250, 277, 412 → "a run carries the vendor's backoff and its quiet, and a stop in progress drops both" | `agents/request-status.ts`: a stopping run keeps `waiting` | That test, `:220` |
| request-status 352, 361 → "notesAwaitingChange collects … and no others" | `agents/request-status.ts`: every status but `cancelled` counts | That test, `:281` (`e` from the failed change) |
| request-status 434-457 → "a headline for what happened, then the one useful thing about it" | `agents/request-status.ts`: a failure's detail drops the title fallback | That test, `:330` (null, expected "Aurora") |
| the same | `agents/request-status.ts`: an unattended queue says "your agent picks it up next" | That test, `:320` |
| update 47 → "ago › rounds down to the unit a person would say" | `update/update.ts`: `ago` loses its `Number.isFinite` guard | That test, `update.test.ts:47` ("NaN days ago") |
| update 73-102 → "with nothing newer: a spinner, then a check to run, its answer or why it failed" | `update/update.ts`: a failed check's meta says "Checked …" | That test, `:99` |
| update 135 → "a newer version leads with it and says what Update will run" | `update/update.ts`: `runnerName("pnpm")` is "pnpm exec" | That test, `:124` |
| update 173 → the same test | `update/update.ts`: a skipped version's button says "Update" | That test, `:146` |
| update 224 → "an update under way shows its progress and nothing to press, and a failed one what to do" | `update/update.ts`: a failed install's note keeps `@latest` | That test, `:174` |
| compare 12-41, 70-95 → "nextCompare picks the second pane with no second choice needed" | `preview/compare.ts`: history checked before the parent | That test, `compare.test.ts:30` (a variant's row) |
| the same | `preview/compare.ts`: a pin is taken without checking it still exists | That test, `:14` |
| compare 53-64 → "paneTitles shows both panes only for a split with another direction" | `preview/compare.ts`: the same direction may fill both panes | That test, `:49` |
| compare 135 → "a split keeps the width it had alone and scales to fit" | `preview/compare.ts`: `boxHeight` left unscaled | That test, `:80` (the proportions line), plus the grid test |
| compare 220 → "a preset narrower than the pane is never scaled up, and its box is its own size" | `preview/compare.ts`: a preset's height not inset by the gutter | That test, `:134` (950, expected 902), plus the framed-preset test |
| generation 56, 62 → "a direction's surface is the v- parameter its address carries, listed once in order" | `generation/generation.ts`: a bare `v-` names an empty surface | That test, `generation.test.ts:53` |
| generation 97-194 → "the card above the composer says what is planned, how the build goes and how it ended" | `generation/generation.ts`: failed names joined by commas only | That test, `:103` ("Pantry, Market failed") |
| the same | `generation/generation.ts`: "variations" whatever the count | That test, `:128` |
| generation 209 (D) → Shell.test "a set dismissed and then retried shows its new result, not the newest set's" | `generation/generation.ts`: `lastEnded` takes the last set in the list | That Shell test, `Shell.test.tsx:863` |
| generation 225 (D) → Shell.test "the + takes a brief…" and "with Codex chosen…" | `generation/generation.ts`: `buildLabel` says "using" | Both Shell tests, `Shell.test.tsx:617` and the Codex label |
| lineage 111 → "a direction with no family is a mark with no lines" | `lineage/lineage.ts`: `widestLane` of an empty rail is 0 | That test (0, expected -1) |
| lineage 202 → "root first, the direction itself left out, and none for a root" | `lineage/lineage.ts`: `ancestry` of a root includes the root | That test |
| lineage 289 → "a direction on no line at all lights only itself, and one not on the rail nothing" | `lineage/lineage.ts`: `tracedSegments` marks a node with no row | That test (`{ Nowhere: ["mark"] }`) |
| lineage 474 → "two marks with no room between them draw nothing, and nor does no mark" | `lineage/lineage.ts`: `trailPath([])` draws "M 0 0" | That test |
| lineage 371, 382 (D) → tracedTree "a leaf's lineage is the line back to its family root" | `lineage/lineage.ts`: `tracedChain` stops below the family root | That tracedTree test, and two tracedSegments tests |
| lineage 189 (D) → "each variant follows the direction it came from" | `lineage/lineage.ts`: roots walked in reverse saved order | That test and four more |
| keymap 54, 114 → "resolveKey › resolves each binding" | `keymap.ts`: only a lower-case `a` notes | That test |
| keymap 119 → "ignores everything while typing" | `keymap.ts`: `a` still notes while typing | That test |
| keymap 123 → "leaves meta, control and alt combinations to the browser" | `keymap.ts`: `a` with a modifier still notes | That test |
| provenance 13-33 → "provenanceOf reports whichever origin a direction records, or nothing" | `lineage/provenance.ts`: the ask kept untrimmed | That test |
| provenance 47-55 → "provenanceLine names the parent and the ask in one line, or stands on either alone" | `lineage/provenance.ts`: an ask alone loses its "You" | That test |
| naming 16, 54 → "checkName takes a fresh name, trimmed and with its whitespace collapsed" | `naming.ts`: inner whitespace not collapsed | That test |
| naming 27-35 → "checkName puts the config's title back, or changes nothing" | `naming.ts`: clearing a never-renamed direction is a reset | That test |
| naming 44, 48 → "checkName refuses a name another direction already shows" | `naming.ts`: the clash check is case-sensitive | That test |
| orb 16-24 → "keeps every roll on the list, clamping one out of range to the nearer end" | `ui/orb.ts`: no upper clamp | That test |
| widget 22, 29 → "keeps the widget inside the stage, off every edge, and leaves it be inside" | `ui/widget.ts`: no lower clamp | That test |
| widget 46-58 → "nearestCorner snaps to the corner it is in, and the exact centre to bottom right" | `ui/widget.ts`: top half includes the centre line | That test (centre row) |
| the same | `ui/widget.ts`: top right reported as top left | That test (corner row) |
| health 11, 23 (D) → "hands back the same state when nothing changed" | `preview/health.ts`: a fresh object for every up read | That test |
| health 53-63 → "only a route on the running app depends on it" | `preview/health.ts`: the branch rule removed | That test, after its branch row was repaired (see F below) |
| the same | `preview/health.ts`: the file rule removed | That test |
| overlays 30 → "hides the badges it is meant to, in one declaration …" | `preview/overlays.ts`: a second rule appended | That test |
| overlays 42, 46 → "targets only the dev tools indicator inside the portal …" | `preview/overlays.ts`: the selector scoped with `:host` | That test |
| toasts 15 (D) → "moves a superseded kind to the end" | `ui/toasts.ts`: superseded toasts kept | That test (`[1, 2, 3]`) |
| Gutter 14, 21 → "a rail with no families draws nothing, and one puts roots past the trunk" | `lineage/Gutter.tsx`: forks keep 10 px of dark instead of 2 | That test (root 24) and the four-variant test |
| Gutter 66 (D) → the same test's one-family row | `lineage/Gutter.tsx`: roots lose the 16 px column | The folded-family test (root 6); with the "family anywhere" line left in, the one-family row stays at 16, and so did the deleted test |
| tip 27 (D) → placeTip "shifts a tooltip off the left edge back on screen" | `ui/tip.ts`: the left shift ignores the margin | That test, "re-fits when the label grows", and the wide-tooltip fitShift test |
| tip 32 (D) → placeTip "settles after one correction" | `ui/tip.ts`: `placeTip` reports a change even when the shift is the same | That test |
| tip 46 (D) → placeTip "flips below when there is no room above, then fits" | `ui/tip.ts`: `shouldFlipBelow` never flips | That test |
| Shell.test 968 → "a set shown whole › ends when any row is picked, the one it was opened from included, and stays ended" | `Shell.tsx`: picking a row other than the active one only hides the grid (no render-time clear, `onPick` clears only for the active row) | That test, at its last line (`Shell.test.tsx:972`, 2 shown, expected 0); the other 44 skipped by the filter |
| rendered 19 → "different words, or the same words in a different structure, disagree" | `preview/rendered.ts`: tags left out of the signature | That test, `rendered.test.ts:19` |
| rendered 35 → "ignores whitespace and case …" (F) | `preview/rendered.ts`: case kept | Repaired test red (`:30`); the baseline test file stays green (25 passed) under the same break, since "Ship design" is under the 12-character floor and both sides were `null` |
| rendered 44 → "says nothing about a page that drew nothing yet" | `preview/rendered.ts`: no meaningful-text floor | That test |
| rendered 59, 77 → "pairs previews that drew the same page, and says nothing of a unique one" | `preview/rendered.ts`: a group of one gets an empty twin list | That test and "ignores previews that have not drawn yet" |
| rendered 291 → "descends single-child wrappers to find the page surface, past a script beside them" | `preview/rendered.ts`: `SCRIPT` counted as a rendered child | That test (1 sample, expected 3) |
| prefs 156, 161 → "forgets a preview the config no longer has, and keeps what is still there" | `prefs.ts`: saved folds dropped | That test (`[]`, expected `["Wave"]`) |
| the same | `prefs.ts`: saved folds not filtered against the live titles | That test (`Deleted` kept) |
| prefs 72 → "clamps a rail width …, and falls back when it is not a number" | `prefs.ts`: any saved width taken as a number | That test (274, expected 368). The NaN in the fixture is stored as `null` by `JSON.stringify`, so this line tests the non-number path; the `Number.isFinite` guard has no test before or after (follow-up) |
| prefs 139, 145 → "railOrder keeps the saved order, drops titles gone since and appends new ones" | `prefs.ts`: `railOrder` stops appending | That test |
| prefs 27 (D) → "keeps a saved order, appending previews the config has added since" | `prefs.ts`: the saved order ignored | That test |
| references 76 → "admit › takes images up to the cap, counting what is already attached" | `references/references.ts`: an oversized file spends a slot | That test (`["a.png"]`, expected two). The baseline file stays green under the same break (17 passed): the old test had four free slots, so its name promised more than it checked |
| references 88 (D) → the same test | `references/references.ts`: attached drafts not counted | That test (three accepted) |
| references 95 → "refusalMessage › explains the cap …, and says nothing when nothing was refused" | `references/references.ts`: an empty refusal says "" | That test |
| references 135 → "a nameless paste is still called something, and its header form is bounded ascii" | `references/references.ts`: the header name unbounded | That test |
| share 153 (D) → "a viewer's rail › adopting a pushed layout takes its fields and keeps the viewer's own" | `share/share.ts`: `viewerPrefsRaw` leaves the renames out | That test |
| annotate 21 → "a press that wobbles is still a click, and a deliberate sweep is a region" | `annotate/annotate.ts`: drag threshold 50 | That test |
| annotate 46, 52 → "an element crossing a region's edge overlaps it, one inside is contained, and touching is neither" | `annotate/annotate.ts`: touching edges overlap | That test |
| the same | `annotate/annotate.ts`: `contains` ignores the right edge | That test (`[true, true]`) |
| annotate 143-151 → "cardWidth is comfortable on a pane, …" | `annotate/annotate.ts`: 24 px margin instead of 48 | That test (256, expected 232) |
| annotate 167, 172 → "unionOf holds everything it was given, and nothing when the sweep caught nothing" | `annotate/annotate.ts`: an empty sweep is a zero box | That test |
| annotate 190, 199 → "coversFrom keeps what was given in order, says a thing once, and caps a big region" | `annotate/annotate.ts`: duplicates kept | That test |
| anchor 117, 122 → "elementText collapses …, caps a paragraph, and is empty for no words" | `annotate/anchor.ts`: no words read as "null" | That test |
| anchor 164 → "keeps the pointed-at spot as a fraction of the element, inside its own box" | `annotate/anchor.ts`: the fraction unclamped | That test |
| anchor 175 → the same | `annotate/anchor.ts`: a zero-width box divided by | That test |
| reference 72 → "prints both names when the rail shows a different one, and points at the config title" | `reference.ts`: the show command names the rail's name | That test |
| reference 43, 47 → "names the source an agent edits: a file over the route, a branch, or the route" | `reference.ts`: a branch labelled "Source:" | That test |
| reference 61 → "carries the parent of a variant, and no parent line for a root" | `reference.ts`: the parent line always printed | That test |
| reference 98, 104 → "absoluteUrl resolves a root-relative preview …, and leaves the rest" | `reference.ts`: an unreadable URL falls back to the origin | That test |
| scan 40 (D) → "queues same-origin previews without current results, not the sealed cross-origin one" | `preview/scan.ts`: any preview with a URL queued | That test and three more |
| scan 118-139 → "replacedPanes reads again only a pane whose document was replaced in place" | `preview/scan.ts`: a pane new to the stage counts as replaced | That test |
| the same | `preview/scan.ts`: one replaced pane rereads the whole split | That test |
| tip 19, 39 → "fitShift leaves a tooltip that fits, pulls one in from the right, and pins a wide one left" | `ui/tip.ts`: a tooltip past the right edge left where it is | That test |
| tip 59 → "shouldFlipBelow stays put when there is room above, or when below is no better" | `ui/tip.ts`: a cut-off tooltip always flips | That test |
| tip 76 → placeTip "shifts a tooltip off the left edge back on screen, and settles after one correction" | `ui/tip.ts`: a pass reports a change even when the shift is the same | That test |
| keymap 32 → "search › takes command or control, on either platform, even from inside a text field" | `keymap.ts`: search ignored while typing | That test |
| update 58 → "a newer version that was not skipped is news; a skipped one, or being up to date, is not" | `update/update.ts`: `hasNews` ignores the skip | That test |
| kit (setup only) → all three label tests | `ui/kit.tsx`: label always in `document.body`; label in any shell on the page; label beside its control | Each break red as in #118 (two, one and three tests) |
| clipboard 55 → "reports blocked when neither path lands, or the environment offers neither" | `ui/clipboard.ts`: a missing legacy command counts as copied | That test |
| poll 171 → "starts the next read once the last one settles, and a failed one frees the slot too" | `net/poll.ts`: a rejected read never frees the slot | That test (2 reads, expected 3) |
| the same | `net/poll.ts`: a resolved read never frees the slot | That test and two more |
| lineage 137 → "depth is the real depth, and a root's family count is everything beneath it" | `lineage/lineage.ts`: every row counts its family as variants | That test |
| lineage 228 → "collapseChain › a short chain shows whole, and a long one keeps its root and its parent" | `lineage/lineage.ts`: `collapseChain` max 5 | That test |
| lineage 321 → "puts a sibling before the one it should precede, or with none after the last" | `lineage/lineage.ts`: a drop with nothing to go before lands first | That test and the root-move test |
| share 60 → "keeps a rename only for a direction that goes, and with no saved order uses config order" | `share/share.ts`: `railShare` reads only the saved order | That test and the first railShare test |
| share 95 → stageShare "refuses a pair with a branch or a gone direction on one side …" | `share/share.ts`: a direction not on the rail can go | That test ("Gone" accepted) |
| share 258 → "viewersLine counts sessions, never people, and totalViewers counts across every link" | `share/share.ts`: `totalViewers` counts links | That test |
| compare 143 → "a single pane, or a split with scaling turned off, is left to the app" | `preview/compare.ts`: `scaleSplit` ignored | That test |
| compare 201 → "a stage not measured yet, or a pane dragged to nothing, still yields a usable scale" | `preview/compare.ts`: no scale floor | That test |
| request-status 61 → "separates queued changes …, and a fork leaves its parent alone" | `agents/request-status.ts`: a fork's parent counts as changing | That test |
| health 19 → "goes down the moment it stops answering, and remembers it after it comes back" | `preview/health.ts`: recovery forgets the outage | That test |
| references 161 → "only uploads that landed become ids, and a failed one blocks the send" | `references/references.ts`: the first unfinished draft decides | That test (`uploading`, expected `failed`) |
| Shell.test 502 → "asking for a change › what is typed is what is queued, as a variant of the direction on the stage or in place" | `Shell.tsx`: every request sent as a variant | That test, at the in-place request |
| annotate 118 → placeCard "aligns to the right edge rather than hanging off it, and stays on screen in a corner" | `annotate/annotate.ts`: flip only with 800 px above | That test and "flips clear of the element" |
| anchor 93 → "stops at a stable id …, and ignores one that cannot survive a reload" | `annotate/anchor.ts`: any non-empty id is stable | That test (`#:r7: …`) |
| toasts 55 → "dismissToast removes only the toast asked for, and nothing once it is gone" | `ui/toasts.ts`: dismiss keeps only the asked-for toast | That test |
| preview-frame 149 → "separates URL changes and explicit reloads of one title, and forgets a prior mount" | `preview/preview-frame.ts`: reset keeps the old mount | That test |
| generation 217 → "a newer set's slot speaks for a title both sets have, and a row is a slot's only by its key" | `generation/generation.ts`: the key matched on any `v-` parameter | That test (the `v-pricing` row) |
| widget 33 → "keeps the widget inside the stage, off every edge, and leaves it be inside" | `ui/widget.ts`: bounds allowed to invert on a tiny stage | That test (-4) |
| framing 78 → refusalWords "says which site refused, why …, and the header that would fix it" | `preview/framing.ts`: the hint names `*` | That test |
| framing 12 → frameRefusal "names the header that refused the frame, and anything short of that is no refusal" | `preview/framing.ts`: the header always read as content-security-policy | That test |
| live 230 → "redials on a backoff when the socket goes, and resets once one opens" | `net/live.ts`: error and close each schedule a redial | That test (6 sockets, expected 5) |
| Gutter 36, 52 (setup shared) → "a root with four variants › …" | covered by the Gutter breaks above | – |

**Breaks that stayed green, and why.** `prefs.ts` with the `Number.isFinite` width guard removed (the fixture's NaN is stored as `null`; the guard has no test, before or after, follow-up); `framing.ts` with `isRefusal` loosened to any record (the string refusal is already rejected by `isJsonRecord`; the break was not a regression for that input); `generation.ts` reading `v-hero` instead of the set's surface (the fixture's surface is `hero`; a broader break went red); `Gutter.tsx` without the "family anywhere" root column (no rail can reach that line with a family and no qualifying root, so neither the old nor the new tests reach it). The three baseline tests that stayed green under their own breaks are the three `F`s above.

## For the preservation review (step 6)

Where to look first, most likely gaps first.

1. **Seams with callers outside the lane.** The full run caught `startLive({ url })` in `server.test.ts`. The other removed options and exports (`timers`, `connect`, `setTimeout`, `clearTimeout`, `AgentFetcher`, the note writes' and `frameRefusal`'s `fetcher`, `shortLink`, `imageFilesFrom`, `tracedChain` and `unshareableReason` exports) have no import outside `packages/shell/src` (grep over `packages`, `site`, `scripts` and `test`), and typecheck passes.
2. **The two deletions that lean on Shell.test**: generation 209 (`lastEnded`) and 225 (`buildLabel`). Each break went red in `Shell.test.tsx`, but only through `toContain` on page text.
3. **The Shell.test fold 968 → 1049.** 1049 now reopens the set from the card between picks; check it still proves "picking a member, then the origin, shows one direction".
4. **Fixtures that changed while folding**: anchor 93's tree gained a `div` so it shares 78's tree (expected path extended by the same rule); coversFrom's duplicate is no longer adjacent; references 161's precedence row now has the upload in flight first; the live dispatch test now asserts the dial URL; poll 229 checks its timer count earlier.
5. **Tests folded in the second pass that the first draft had kept whole**: tip 19, 39, 59, 76; keymap 32; update 58; lineage 137, 228, 321; share 60, 89, 95, 258; compare 143, 201; request-status 61; health 19; references 95, 135, 161; generation 217; anchor 93; annotate 118; widget 33; toasts 55; preview-frame 149; framing 21, 78; live 230; poll 171; Shell.test 502. Each has a break above.
6. **The references folder's branch number** (see Result): below budget by 0.48 points from deleted dead code alone.
