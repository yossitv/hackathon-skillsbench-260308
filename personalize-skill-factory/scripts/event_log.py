# /// script
# dependencies = []
# ///
"""
Event Logger — Structured JSON Lines logging for the Skill Factory pipeline.

Each event is a single JSON line written to logs/pipeline.jsonl.
The Streamlit dashboard reads these events to visualize the pipeline.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

FACTORY_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = FACTORY_ROOT / "logs"
LOG_FILE = LOG_DIR / "pipeline.jsonl"


def emit(event_type: str, skill_name: str, stage: str, **data):
    """Write a structured event to the pipeline log.

    Args:
        event_type: e.g. "fetch", "safety_check", "approve", "customize", "benchmark", "finalize", "publish"
        skill_name: Skill identifier
        stage: Current pipeline stage ("staging", "developing", "generated")
        **data: Additional event-specific data
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event_type,
        "skill": skill_name,
        "stage": stage,
        **data,
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")


def read_events(skill_name: str | None = None) -> list[dict]:
    """Read all events, optionally filtered by skill name."""
    if not LOG_FILE.exists():
        return []
    events = []
    for line in LOG_FILE.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
            if skill_name is None or ev.get("skill") == skill_name:
                events.append(ev)
        except json.JSONDecodeError:
            continue
    return events


def get_all_skills() -> list[str]:
    """Return unique skill names from the log."""
    events = read_events()
    seen = []
    for ev in events:
        name = ev.get("skill", "")
        if name and name not in seen:
            seen.append(name)
    return seen
