"""Lane L2's deliberate breaks: patch a production owner, run the keeper, restore byte for byte.

Run from the repository root with Node 24 on PATH: python3 campaign/breaks-L2.py [break name ...].

Each break names the owner file, the exact text replaced, the keeper test file and
a name filter. The script records the keeper's result with the break in place and
proves the restore with a sha256 before and after.
"""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = str(Path(__file__).resolve().parents[1])
S = "packages/server/src"

BREAKS = [
    # id, owner, old, new, test file, -t filter, what the break simulates
    ("agent-command quotes", f"{S}/agents/agent-command.ts",
     """    if (character === '"' || character === "'") {""",
     """    if (character === '"') {""",
     f"{S}/agents/agent-command.test.ts", "keeps a quoted value together",
     "single quotes are no longer quotes"),
    ("agent-command punctuation", f"{S}/agents/agent-command.ts",
     """    args: template.args.map((argument) => (argument === PROMPT_TOKEN ? prompt : argument)),""",
     """    args: template.args.map((argument) => (argument === PROMPT_TOKEN ? prompt.replaceAll('"', '\\\\"') : argument)),""",
     f"{S}/agents/agent-command.test.ts", "puts the whole prompt in one argv entry",
     "the prompt is escaped for a shell that is not there"),
    ("agent-command failed set", f"{S}/agents/agent-command.ts",
     """request.status === "queued" && !failed.has(request.id)""",
     """request.status === "queued\"""",
     f"{S}/agents/agent-command.test.ts", "takes the first queued request in order",
     "a failed request is handed out again"),
    ("agent-command refusals", f"{S}/agents/agent-command.ts",
     """  if (tokens.some((token) => token !== PROMPT_TOKEN && token.includes(PROMPT_TOKEN))) {""",
     """  if (tokens.some((token) => token !== PROMPT_TOKEN && token.startsWith(PROMPT_TOKEN))) {""",
     f"{S}/agents/agent-command.test.ts", "refuses",
     "a placeholder glued after a word is let through"),
    ("agents cursor verdict", f"{S}/agents/agents.ts",
     """      if (/not (logged|signed) in/i.test(result.stdout)) return "signed-out";

      if (/logged in|signed in/i.test(result.stdout)) return "ok";""",
     """      if (/logged in|signed in/i.test(result.stdout)) return "ok";

      if (/not (logged|signed) in/i.test(result.stdout)) return "signed-out";""",
     f"{S}/agents/agents.test.ts", "verdict reads its own CLI honestly",
     "Cursor's signed-out answer is read as signed in"),
    ("agents cursor resume", f"{S}/agents/agents.ts",
     """      "-p",
      "--resume",
      sessionId,
      prompt,
      "--output-format",
      "stream-json",
      "--trust",
    ],""",
     """      "-p",
      "--resume",
      sessionId,
      prompt,
      "--output-format",
      "stream-json",
    ],""",
     f"{S}/agents/agents.test.ts", "resume argv continues the session",
     "a resumed Cursor run stops at the trust prompt"),
    ("agents retry negatives", f"{S}/agents/agents.ts",
     """  if (event === null || event.type !== "system" || event.subtype !== "api_retry") return null;""",
     """  if (event === null || event.type !== "system") return null;""",
     f"{S}/agents/agents.test.ts", "reads the api_retry event",
     "any system line reads as a retry"),
    ("agents single-quote unwrap", f"{S}/agents/agents.ts",
     """    if ((quote === "'" || quote === '"') && command.endsWith(quote) && command.length > 1) {""",
     """    if (quote === '"' && command.endsWith(quote) && command.length > 1) {""",
     f"{S}/agents/agents.test.ts", "cleans command text",
     "a single-quoted shell command keeps its quotes"),
    ("agents cursor rows", f"{S}/agents/agents.ts",
     """  const key = Object.keys(wrapper).find((name) => name.endsWith("ToolCall"));""",
     """  const key = Object.keys(wrapper)[0];""",
     f"{S}/agents/agents.test.ts", "reads a Cursor tool_call",
     "the first key of the wrapper is read as the tool"),
    ("claude unwarmed resume", f"{S}/agents/claude-agent-session.ts",
     """        await waitForAbort(this.startQuery(signal, input.sessionId), signal);""",
     """        await waitForAbort(this.startQuery(signal, null), signal);""",
     f"{S}/agents/claude-agent-session.test.ts", "a fresh turn after a resumed conversation",
     "a run naming a session with nothing warmed starts fresh"),
    ("claude rotated effort", f"{S}/agents/claude-agent-session.ts",
     """    this.loadedSessionId = sessionId;
    this.appliedEffort = null;
    this.pump = this.read(query);""",
     """    this.loadedSessionId = sessionId;
    this.pump = this.read(query);""",
     f"{S}/agents/claude-agent-session.test.ts", "a fresh turn after a resumed conversation",
     "a new process is assumed to carry the old process's effort",
     # the reset also clears it; both go, as one forgotten rule
     ("""    this.loadedSessionId = null;
    this.appliedEffort = null;
    this.warmedFor = null;""",
      """    this.loadedSessionId = null;
    this.warmedFor = null;""")),
    ("claude replacement reverse", f"{S}/agents/claude-agent-session.ts",
     """      if (this.warmedFor === sessionId) return this.warming ?? Promise.resolve();""",
     """      if (this.warmedFor === sessionId || sessionId === null)
        return this.warming ?? Promise.resolve();""",
     f"{S}/agents/claude-agent-session.test.ts", "a handle warmed for another conversation",
     "a handle warmed for a session serves a fresh request"),
    ("runner claude fallback", f"{S}/agents/runner.ts",
     """        if (persistent !== null) {
          try {""",
     """        if (persistent !== null && resolved.agent === "codex") {
          try {""",
     f"{S}/agents/runner.test.ts", "falls back to the",
     "only Codex falls back to its CLI"),
    ("runner resumed thread", f"{S}/agents/runner.ts",
     """          sessions.set(resolved.agent, {
            id: observed.sessionId,""",
     """          sessions.set(resolved.agent, {
            id: previous?.id ?? observed.sessionId,""",
     f"{S}/agents/runner.test.ts", "the ninth request starts cold",
     "a new session's id never replaces the old one"),
    ("runner resumed fork allowance", f"{S}/agents/runner.ts",
     """      args: [...adapter.resumeArgs(sessionId, prompt, choice.effort, images), ...allow],""",
     """      args: [...adapter.resumeArgs(sessionId, prompt, choice.effort, images)],""",
     f"{S}/agents/runner.test.ts", "hands claude the registration allowance",
     "a resumed fork loses its allowance"),
    ("runner warm after run", f"{S}/agents/runner.ts",
     """      releaseAllBut(desiredAgent ?? choice.agent);""",
     """      releaseAllBut(choice.agent);""",
     f"{S}/agents/runner.test.ts", "when a run ends",
     "the vendor that ran stays warm over the one asked for"),
    ("browser explicit order", f"{S}/capture/browser.ts",
     """  for (const candidate of [env.LEGLAS_BROWSER, env.CHROME_PATH, env.PUPPETEER_EXECUTABLE_PATH]) {""",
     """  for (const candidate of [env.CHROME_PATH, env.LEGLAS_BROWSER, env.PUPPETEER_EXECUTABLE_PATH]) {""",
     f"{S}/capture/browser.test.ts", "finds LEGLAS_BROWSER before CHROME_PATH",
     "CHROME_PATH outranks LEGLAS_BROWSER"),
    ("browser shell first", f"{S}/capture/browser.ts",
     """  if (shell !== null) return shell;

  if (platform === "darwin") {""",
     """  if (platform === "darwin") {""",
     f"{S}/capture/browser.test.ts", "finds a headless shell before a desktop browser",
     "a desktop browser wins over a headless shell"),
    ("browser exit code", f"{S}/capture/browser.ts",
     """      finish(new Error(`The browser did not start (exit code ${code ?? "unknown"}).${because()}`)),""",
     """      finish(new Error(`The browser did not start.${because()}`)),""",
     f"{S}/capture/browser.test.ts", "a startup failure carries its exit code",
     "the exit code is dropped from the startup failure"),
    ("browser grace", f"{S}/capture/browser.ts",
     """    if (owner === null && clock() - details.createdAt < RECORD_GRACE_MS) continue;""",
     """    if (owner === null && clock() - details.createdAt > RECORD_GRACE_MS) continue;""",
     f"{S}/capture/browser.test.ts", "profile",
     "the grace period is read backwards"),
    ("browser unreadable cache", f"{S}/capture/browser.ts",
     """function readableDirectories(dir: string): string[] {
  try {
    return readdirSync(dir);
  } catch {
    return [];
  }
}""",
     """function readableDirectories(dir: string): string[] {
  return readdirSync(dir);
}""",
     f"{S}/capture/browser.test.ts", "finds each Windows program root",
     "a cache folder that can't be read fails the search"),
    ("capture cropBox region", f"{S}/capture/capture.ts",
     """  const selected =
    region === undefined
      ? found""",
     """  const selected =
    region === undefined || region !== undefined
      ? found""",
     f"{S}/capture/capture.test.ts", "cropBox",
     "a swept region is ignored"),
    ("generation late render", f"{S}/generation/generation.ts",
     """      const report = await deps.render(slot.title, { picture: live.record !== null });

      if (!owns(live, slot, attempt)) return null;""",
     """      const report = await deps.render(slot.title, { picture: live.record !== null });
""",
     f"{S}/generation/generation.test.ts", "while a page is being rendered",
     "a render that outlives a stop or close still speaks for the slot"),
    ("generation close drain", f"{S}/generation/generation.ts",
     """            await stop(live.job.id);
            await drain(live);""",
     """            await stop(live.job.id);""",
     f"{S}/generation/generation.test.ts", "a stop and a close while the directions go on the rail",
     "close stops waiting for writes under way"),
    ("generation build activity", f"{S}/generation/generation.ts",
     """      const activity = activityFrom(live.agent.id, line, deps.cwd);""",
     """      const activity = activityFrom(live.agent.id, line);""",
     f"{S}/generation/generation.test.ts", "a build and its fix run say what they are doing",
     "a build's step names its file from the wrong folder"),
    ("generation prune order", f"{S}/generation/generation.ts",
     """      if (recording) await records.prune();

      // The kept set that built the direction this set varies, looked up after
      // the prune so a set let go isn't brought back by its event.
      const baseSet =
        base === null || !recording ? null : await setOfKey(deps.cwd, base.key).catch(() => null);""",
     """      // The kept set that built the direction this set varies, looked up after
      // the prune so a set let go isn't brought back by its event.
      const baseSet =
        base === null || !recording ? null : await setOfKey(deps.cwd, base.key).catch(() => null);

      if (recording) await records.prune();""",
     f"{S}/generation/generation.test.ts", "keeps the newest hundred sets",
     "the base is looked up before the prune lets it go"),
    ("generation codex fix sandbox", f"{S}/generation/generation.ts",
     """      const fixing = run(
        live.agent,
        live.agent.build(prompt),""",
     """      const fixing = run(
        live.agent,
        live.agent.plan(prompt),""",
     f"{S}/generation/generation.test.ts", "plans, builds and fixes with restricted Codex runs",
     "a fix run gets the read-only planner's sandbox"),
    ("generation agent refusal", f"{S}/generation/generation.ts",
     """      if (agent !== "claude" && agent !== "codex") {""",
     """      if (agent !== "claude" && agent !== "codex" && agent !== "cursor") {""",
     f"{S}/generation/generation.test.ts", "is refused for",
     "Cursor is let through to build directions"),
]


def sha(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def main():
    only = sys.argv[1:]
    results = []
    for entry in BREAKS:
        name, owner, old, new, test, filter_, what = entry[:7]
        extra = entry[7] if len(entry) > 7 else None
        if only and name not in only:
            continue
        path = f"{ROOT}/{owner}"
        before = sha(path)
        source = open(path).read()
        assert source.count(old) == 1, (name, source.count(old))
        broken = source.replace(old, new)
        if extra is not None:
            assert broken.count(extra[0]) == 1, (name, "extra")
            broken = broken.replace(extra[0], extra[1])
        open(path, "w").write(broken)
        try:
            run = subprocess.run(
                ["npx", "vitest", "run", test, "-t", filter_],
                cwd=ROOT, capture_output=True, text=True, timeout=600,
                env=None,
            )
            output = run.stdout + run.stderr
        finally:
            open(path, "w").write(source)
        after = sha(path)
        failed = re.findall(r"(?:×|FAIL)\s+(?:packages\S+ > )?(.+?)(?:\s\d+ms)?$", output, re.M)
        tally = re.search(r"Tests\s+(.+)", output)
        assertion = re.search(r"AssertionError: (.+)|Error: (.+)", output)
        results.append({
            "break": name,
            "owner": owner,
            "simulates": what,
            "keeper": f"{test} -t \"{filter_}\"",
            "red": run.returncode != 0,
            "tests": tally.group(1).strip() if tally else None,
            "failed": sorted(set(f.strip() for f in failed))[:6],
            "first assertion": (assertion.group(1) or assertion.group(2)).strip()[:200] if assertion else None,
            "restored": before == after,
            "sha256": after,
        })
        print(json.dumps(results[-1]), flush=True)
    with open(f"{ROOT}/campaign/breaks-L2.json", "w") as handle:
        json.dump(results, handle, indent=2)


main()
