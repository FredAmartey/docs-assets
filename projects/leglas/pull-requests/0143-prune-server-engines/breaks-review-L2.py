"""Preservation review of lane L2: deliberate breaks of production owners, each run against its keeper.

Run from the repository root with Node 24 on PATH and LEGLAS_BROWSER set as campaign/baseline.md
says: python3 campaign/breaks-review-L2.py [break name ...]. PHASE=<label> tags the run (the
restoration break runs once on the lane head and once after the restore).

Each break names the owner, the exact text replaced, the keeper test file, a name filter and the
outcome the review expects: "red" where the keeper must catch it, "green" where the break shows a
deleted test guarded nothing observable or that only one keeper can see it. Results merge into
campaign/breaks-review-L2.json by break and phase; each restore is proved with a sha256.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = str(Path(__file__).resolve().parents[1])
S = "packages/server/src"
OUT = f"{ROOT}/campaign/breaks-review-L2.json"

BREAKS = [
    # id, owner, old, new, test file, -t filter, expected, what the break simulates
    ("generation stop answer", f"{S}/generation/generation.ts",
     """    return targets.length > 0;
  };""",
     """    return job.slots.some(
      (slot) =>
        (key === undefined || slot.key === key) &&
        (slot.state === "building" || slot.state === "checking"),
    );
  };""",
     f"{S}/generation/generation.test.ts", "while a page is being rendered", "red",
     "a stop answers from the slots after it has already marked them stopped, so it says it stopped nothing"),
    ("generation stop answer e2e", f"{S}/generation/generation.ts",
     """    return targets.length > 0;
  };""",
     """    return job.slots.some(
      (slot) =>
        (key === undefined || slot.key === key) &&
        (slot.state === "building" || slot.state === "checking"),
    );
  };""",
     f"{S}/generation/generation.test.ts", "a generation, end to end", "red",
     "the same break against the real-browser end-to-end test, the only other test that reads a stop's answer"),
    # The lane's own break of the same table, rerun to show the restored row still catches it.
    ("generation late render", f"{S}/generation/generation.ts",
     """      const report = await deps.render(slot.title, { picture: live.record !== null });

      if (!owns(live, slot, attempt)) return null;""",
     """      const report = await deps.render(slot.title, { picture: live.record !== null });
""",
     f"{S}/generation/generation.test.ts", "while a page is being rendered", "red",
     "a render that outlives a stop or close still speaks for the slot"),
    ("generation stop drain", f"{S}/generation/generation.ts",
     """      // Past its run, planning may still be writing the slots: stopped means those writes are done.
      await drain(live);
""",
     "",
     f"{S}/generation/generation.test.ts", "a stop and a close while the directions go on the rail", "red",
     "a stop of a planning set answers before the writes under way are done"),
    ("agents claude edit label", f"{S}/agents/agents.ts",
     """      return path === null ? `using ${block.name}` : `editing ${path}`;""",
     """      return path === null ? `using ${block.name}` : `changing ${path}`;""",
     f"{S}/generation/generation.test.ts", "a build and its fix run say what they are doing", "red",
     "Claude's Write and Edit read as something other than editing"),
    ("agents codex file_change label", f"{S}/agents/agents.ts",
     """  const first = Array.isArray(item.changes) ? record(item.changes[0]) : null;""",
     """  const first = null;""",
     f"{S}/generation/generation.test.ts", "plans, builds and fixes with restricted Codex runs", "red",
     "Codex's file_change items, which name their path under changes, get no label"),
    ("agents cursor edit label", f"{S}/agents/agents.ts",
     """    return path === null ? "editing a file" : `editing ${path}`;""",
     """    return path === null ? "editing a file" : `changing ${path}`;""",
     f"{S}/agents/agents.test.ts", "reads Cursor's own tool_call events", "red",
     "a Cursor edit with a path stops reading as editing, so the runner would rerun it"),
    ("runner edited rule", f"{S}/agents/runner.ts",
     """          if (activity.startsWith("editing")) observed.edited = true;""",
     """          if (activity.startsWith("edited")) observed.edited = true;""",
     f"{S}/agents/runner.test.ts", "a resume that edited and then failed", "red",
     "an edit seen in a resumed run no longer blocks its cold rerun"),
    ("process-tree unstarted guard", f"{S}/agents/process-tree.ts",
     """  // It never started, so nothing below it exists.
  if (pid === undefined) {
    child.kill(signal);

    return;
  }

""",
     "",
     f"{S}/agents/runner.test.ts", "cancels the active child with SIGTERM", "green",
     "the never-started guard is gone; on Linux and macOS process.kill(NaN) throws and the same child.kill runs"),
    ("capture failed request", f"{S}/capture/capture.ts",
     """    page.on("Network.loadingFailed", (params) => {
      if (isString(params?.requestId)) received(params.requestId);
    }),""",
     """    page.on("Network.loadingFailed", () => {}),""",
     f"{S}/capture/capture.test.ts", "the shutter", "red",
     "a request that failed to load holds the shutter until the deadline"),
    ("capture image wait", f"{S}/capture/capture.ts",
     """const DRAWN_WITH = new Set(["Script", "Stylesheet", "Font", "Image"]);""",
     """const DRAWN_WITH = new Set(["Script", "Stylesheet", "Font"]);""",
     f"{S}/capture/capture.test.ts", "the shutter", "red",
     "an image the page asks for after load no longer holds the shutter"),
    ("browser flatten live", f"{S}/capture/browser.ts",
     """          flatten: true,""",
     """          flatten: false,""",
     f"{S}/capture/capture.test.ts", "renders a local page, crops its element", "red",
     "page sessions attach in a framing real Chrome does not route"),
    ("browser flatten units", f"{S}/capture/browser.ts",
     """          flatten: true,""",
     """          flatten: false,""",
     f"{S}/capture/browser.test.ts", "", "green",
     "the same break against the fake-socket tests, which cannot see it"),
    ("requests cancelled failure", f"{S}/requests/requests.ts",
     """            status: failure.code === "cancelled" ? ("cancelled" as const) : ("failed" as const),
            failure,""",
     """            status: failure.code === "cancelled" ? ("cancelled" as const) : ("failed" as const),
            failure: failure.code === "cancelled" ? null : failure,""",
     f"{S}/server.test.ts", "reports a running request and cancels it through the polled API", "red",
     "a cancelled request keeps its status but loses the code and message that say who stopped it"),
    ("requests cancelled failure runner", f"{S}/requests/requests.ts",
     """            status: failure.code === "cancelled" ? ("cancelled" as const) : ("failed" as const),
            failure,""",
     """            status: failure.code === "cancelled" ? ("cancelled" as const) : ("failed" as const),
            failure: failure.code === "cancelled" ? null : failure,""",
     f"{S}/agents/runner.test.ts", "cancels the active child with SIGTERM", "green",
     "the same break against the runner's cancel test, which reads only the status"),
    ("agent-command glued reason", f"{S}/agents/agent-command.ts",
     """      error: `${PROMPT_TOKEN} must stand as a word of its own, for example: ${EXAMPLE}`,""",
     """      error: `The agent command takes ${PROMPT_TOKEN} once, for example: ${EXAMPLE}`,""",
     f"{S}/agents/agent-command.test.ts", "refuses", "red",
     "a placeholder glued to a word is refused with another refusal's reason"),
    ("agents custom run saved", f"{S}/agents/agents.ts",
     """  if (choice.run !== undefined) config.run = choice.run;""",
     """  if (choice.run !== undefined && choice.agent !== "custom") config.run = choice.run;""",
     f"{S}/server.test.ts", "reports available agents and round-trips the saved choice", "red",
     "a custom agent's command is not written to watch.json"),
]


def sha(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def main():
    only = sys.argv[1:]
    phase = os.environ.get("PHASE", "review head")
    try:
        with open(OUT) as handle:
            results = json.load(handle)
    except FileNotFoundError:
        results = []
    for name, owner, old, new, test, filter_, expected, what in BREAKS:
        if only and name not in only:
            continue
        path = f"{ROOT}/{owner}"
        before = sha(path)
        source = open(path).read()
        assert source.count(old) == 1, (name, source.count(old))
        open(path, "w").write(source.replace(old, new))
        command = ["npx", "vitest", "run", test] + (["-t", filter_] if filter_ else [])
        try:
            run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=900)
            output = run.stdout + run.stderr
        finally:
            open(path, "w").write(source)
        after = sha(path)
        failed = re.findall(r"(?:×|FAIL)\s+(?:packages\S+ > )?(.+?)(?:\s\d+ms)?$", output, re.M)
        tally = re.search(r"Tests\s+(.+)", output)
        assertion = re.search(r"AssertionError: (.+)|Error: (.+)", output)
        result = {
            "break": name,
            "phase": phase,
            "owner": owner,
            "simulates": what,
            "keeper": f"{test}" + (f" -t \"{filter_}\"" if filter_ else ""),
            "expected": expected,
            "red": run.returncode != 0,
            "as expected": (run.returncode != 0) == (expected == "red"),
            "tests": tally.group(1).strip() if tally else None,
            "failed": sorted(set(f.strip() for f in failed))[:6],
            "first assertion": (assertion.group(1) or assertion.group(2)).strip()[:200] if assertion and run.returncode != 0 else None,
            "restored": before == after,
            "sha256": after,
        }
        results = [r for r in results if (r["break"], r["phase"]) != (name, phase)] + [result]
        print(json.dumps(result), flush=True)
        with open(OUT, "w") as handle:
            json.dump(results, handle, indent=2)


main()
