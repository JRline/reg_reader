#!/usr/bin/env python3
"""
Calls Haiku 4.5 on every prompt file in pipeline/prompts/, saving each reply as the
matching pipeline/raw/<name>.json. This is the one piece I couldn't run myself — this
environment has no ANTHROPIC_API_KEY — so this script exists for you to run wherever
you do have API access. Requires: pip install anthropic, and ANTHROPIC_API_KEY set.

Usage:
    python3 run_haiku_batch.py [prompts_dir] [raw_dir]

Defaults: pipeline/prompts -> pipeline/raw. Skips any prompt whose output file already
exists, so it's safe to re-run after an interruption or after adding new prompt files.
"""
import json
import re
import sys
import time
from pathlib import Path

import anthropic

MODEL = "claude-haiku-4-5-20251001"
PIPELINE_DIR = Path(__file__).parent


def strip_code_fence(text: str) -> str:
    m = re.match(r"^```(?:json)?\s*\n(.*)\n```\s*$", text.strip(), re.DOTALL)
    return m.group(1) if m else text.strip()


def main():
    prompts_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else PIPELINE_DIR / "prompts"
    raw_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else PIPELINE_DIR / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    client = anthropic.Anthropic()
    prompt_files = sorted(prompts_dir.glob("*.txt"))
    print(f"Found {len(prompt_files)} prompt files in {prompts_dir}/")

    done, failed = 0, []
    for pf in prompt_files:
        out_path = raw_dir / f"{pf.stem}.json"
        if out_path.exists():
            continue
        prompt_text = pf.read_text(encoding="utf-8")
        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt_text}],
            )
            reply = "".join(block.text for block in resp.content if block.type == "text")
            parsed = json.loads(strip_code_fence(reply))
            out_path.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
            done += 1
            print(f"  [{done}/{len(prompt_files)}] {pf.stem} OK")
        except json.JSONDecodeError as e:
            failed.append(pf.stem)
            print(f"  {pf.stem}: FAILED to parse JSON ({e}) — raw reply saved for inspection")
            (raw_dir / f"{pf.stem}.FAILED.txt").write_text(reply, encoding="utf-8")
        except Exception as e:
            failed.append(pf.stem)
            print(f"  {pf.stem}: FAILED ({e})")
        time.sleep(0.5)  # be polite to the API, not because Haiku needs it

    print(f"\nDone. {done} succeeded, {len(failed)} failed.")
    if failed:
        print("Failed:", failed)
        print("Re-run this script after checking the .FAILED.txt files — it skips completed ones.")


if __name__ == "__main__":
    main()
