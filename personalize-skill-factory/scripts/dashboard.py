# /// script
# dependencies = ["streamlit", "pandas", "altair"]
# ///
"""
Skill Factory Dashboard — Visualize the pipeline flow, benchmarks, and skill diffs.

Usage:
    uv run streamlit run personalize-skill-factory/scripts/dashboard.py
"""

import json
from difflib import unified_diff
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

FACTORY_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = FACTORY_ROOT / "skills"
STAGING_DIR = SKILLS_DIR / "staging"
DEVELOPING_DIR = SKILLS_DIR / "developing"
GENERATED_DIR = SKILLS_DIR / "generated"
LOG_FILE = FACTORY_ROOT / "logs" / "pipeline.jsonl"

STAGE_ORDER = ["staging", "developing", "generated"]


def _escape(text: str) -> str:
    """Escape HTML special characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
EVENT_LABELS = {
    "fetch": "Fetch",
    "safety_check": "Safety Check",
    "approve": "Approve",
    "customize": "Customize",
    "benchmark": "Benchmark",
    "finalize": "Finalize",
    "publish": "Publish",
}

# ── Helpers ────────────────────────────────────────────────────────────


def load_events() -> pd.DataFrame:
    """Load pipeline events from JSONL log."""
    if not LOG_FILE.exists():
        return pd.DataFrame()
    rows = []
    for line in LOG_FILE.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def scan_skills() -> list[dict]:
    """Scan all skill directories and return metadata."""
    skills = []
    for stage, stage_dir in [("staging", STAGING_DIR), ("developing", DEVELOPING_DIR), ("generated", GENERATED_DIR)]:
        if not stage_dir.exists():
            continue
        for d in sorted(stage_dir.iterdir()):
            if not d.is_dir() or d.name.startswith("_") or d.name.startswith("."):
                continue
            skill_md = d / "SKILL.md"
            info = {
                "name": d.name,
                "stage": stage,
                "path": str(d),
                "has_skill_md": skill_md.exists(),
                "has_baseline": (d / "_baseline" / "SKILL.md").exists(),
                "benchmark_count": len(list((d / "_benchmarks").glob("run-*.json"))) if (d / "_benchmarks").exists() else 0,
            }
            skills.append(info)
    return skills


def load_benchmarks(skill_path: Path) -> pd.DataFrame:
    """Load benchmark run-*.json files for a skill."""
    benchmarks_dir = skill_path / "_benchmarks"
    if not benchmarks_dir.exists():
        return pd.DataFrame()
    rows = []
    for f in sorted(benchmarks_dir.glob("run-*.json")):
        try:
            rows.append(json.loads(f.read_text()))
        except json.JSONDecodeError:
            continue
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def read_skill_md(path: Path) -> str:
    """Read SKILL.md content, return empty string if missing."""
    if path.exists():
        return path.read_text()
    return ""


# ── Page Config ────────────────────────────────────────────────────────

st.set_page_config(page_title="Skill Factory", page_icon=":", layout="wide")
st.title("Skill Factory Dashboard")

# ── Sidebar: Skill Selector ───────────────────────────────────────────

skills = scan_skills()
skill_names = sorted(set(s["name"] for s in skills))

with st.sidebar:
    st.header("Personalize Skills Factory")
    if not skill_names:
        st.info("No skills found. Run the factory pipeline first.")
        st.stop()

    selected_skill = st.selectbox("Select Skill", skill_names)

    # Show which stages this skill exists in
    skill_stages = [s for s in skills if s["name"] == selected_skill]
    for s in skill_stages:
        stage_emoji = {"staging": "1", "developing": "2", "generated": "3"}.get(s["stage"], "?")
        st.write(f"**[{stage_emoji}] {s['stage']}** — {s['benchmark_count']} benchmarks")

    st.divider()
    st.caption("Auto-refresh: re-run to see latest data")

# ── Tab Layout ─────────────────────────────────────────────────────────

tab_pipeline, tab_benchmark, tab_diff = st.tabs(["Pipeline Status", "Benchmark Trends", "Skill Diff"])

# ── Tab 1: Pipeline Status ─────────────────────────────────────────────

with tab_pipeline:
    st.subheader("Pipeline Flow")

    events_df = load_events()
    skill_events = events_df[events_df["skill"] == selected_skill] if not events_df.empty else pd.DataFrame()

    # Determine current stage and completed steps
    current_stages = [s["stage"] for s in skills if s["name"] == selected_skill]
    latest_stage = "staging"
    for s in STAGE_ORDER:
        if s in current_stages:
            latest_stage = s

    completed_events = set(skill_events["event"].tolist()) if not skill_events.empty else set()

    # Pipeline visualization
    pipeline_steps = [
        ("fetch", "Sundial Hub", "staging"),
        ("safety_check", "Claude API + Daytona", "staging"),
        ("approve", "User / Auto", "developing"),
        ("customize", "LLM Optimizer", "developing"),
        ("benchmark", "Harbor (SkillsBench)", "developing"),
        ("finalize", "Symlink", "generated"),
        ("publish", "Sundial Hub", "generated"),
    ]

    cols = st.columns(len(pipeline_steps))
    for i, (event, service, stage) in enumerate(pipeline_steps):
        with cols[i]:
            done = event in completed_events
            is_current = (stage == latest_stage and not done
                          and (i == 0 or pipeline_steps[i - 1][0] in completed_events))

            if done:
                icon = "&#9989;"  # checkmark
                border_color = "#22c55e"
            elif is_current:
                icon = "&#9203;"  # hourglass
                border_color = "#eab308"
            else:
                icon = "&#9744;"  # empty box
                border_color = "#6b7280"

            st.markdown(
                f"""<div style="border:2px solid {border_color}; border-radius:8px;
                padding:12px; text-align:center; min-height:120px;">
                <div style="font-size:24px;">{icon}</div>
                <div style="font-weight:bold; margin:4px 0;">{EVENT_LABELS.get(event, event)}</div>
                <div style="font-size:12px; color:#888;">{service}</div>
                <div style="font-size:11px; color:{border_color}; margin-top:4px;">{stage}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    # Event timeline
    if not skill_events.empty:
        st.subheader("Event Timeline")
        timeline = skill_events.sort_values("timestamp", ascending=False)
        display_cols = ["timestamp", "event", "stage"]
        extra = [c for c in ["recommendation", "score", "optimizer", "label", "iteration"] if c in timeline.columns]
        st.dataframe(
            timeline[display_cols + extra].reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No pipeline events logged yet. Events are recorded when factory.py runs.")

        # Show data from existing benchmark files as fallback
        for s in skill_stages:
            p = Path(s["path"])
            bench_df = load_benchmarks(p)
            if not bench_df.empty:
                st.write(f"Found {len(bench_df)} benchmark records in `{s['stage']}/{selected_skill}`")


# ── Tab 2: Benchmark Trends ───────────────────────────────────────────

with tab_benchmark:
    st.subheader("Benchmark Score History")

    # Collect benchmarks from all stages
    all_benchmarks = pd.DataFrame()
    for s in skill_stages:
        bench = load_benchmarks(Path(s["path"]))
        if not bench.empty:
            bench["stage"] = s["stage"]
            all_benchmarks = pd.concat([all_benchmarks, bench], ignore_index=True)

    if all_benchmarks.empty:
        st.info("No benchmark data yet. Run `factory.py` to generate benchmarks.")
    else:
        # Score over runs
        if "run" in all_benchmarks.columns and "score" in all_benchmarks.columns:
            chart_data = all_benchmarks[["run", "score", "label"]].copy()
            chart_data["score"] = chart_data["score"].fillna(0)

            # Line chart
            line = alt.Chart(chart_data).mark_line(point=True, strokeWidth=2).encode(
                x=alt.X("run:O", title="Run #"),
                y=alt.Y("score:Q", title="Score", scale=alt.Scale(domain=[0, 1])),
                tooltip=["run", "score", "label"],
            ).properties(height=300)

            # Label annotations
            text = alt.Chart(chart_data).mark_text(
                align="center", baseline="bottom", dy=-10, fontSize=11,
            ).encode(
                x="run:O",
                y="score:Q",
                text="label:N",
            )

            st.altair_chart(line + text, use_container_width=True)

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        scores = all_benchmarks["score"].dropna()
        with col1:
            st.metric("Latest Score", f"{scores.iloc[-1]:.2f}" if len(scores) > 0 else "N/A")
        with col2:
            st.metric("Best Score", f"{scores.max():.2f}" if len(scores) > 0 else "N/A")
        with col3:
            if len(scores) >= 2:
                delta = scores.iloc[-1] - scores.iloc[0]
                st.metric("Improvement", f"{delta:+.2f}")
            else:
                st.metric("Improvement", "N/A")

        # Raw data table
        with st.expander("Raw Benchmark Data"):
            st.dataframe(all_benchmarks, use_container_width=True, hide_index=True)

        # Comparison files
        for s in skill_stages:
            comp_dir = Path(s["path"]) / "_benchmarks"
            if comp_dir.exists():
                for cf in sorted(comp_dir.glob("comparison-*.json")):
                    comp = json.loads(cf.read_text())
                    with st.expander(f"Comparison: {comp.get('task_id', '?')}"):
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Baseline (Sundial)", comp.get("baseline_score", "?"))
                        c2.metric("Personalized", comp.get("personalized_score", "?"))
                        delta = comp.get("delta", 0)
                        c3.metric("Delta", f"{delta:+.2f}")


# ── Tab 3: Skill Diff ─────────────────────────────────────────────────

with tab_diff:
    st.subheader("SKILL.md Changes")

    # Find baseline and current versions
    baseline_md = ""
    current_md = ""
    current_source = ""

    for s in skill_stages:
        p = Path(s["path"])
        # Check for baseline
        bl = p / "_baseline" / "SKILL.md"
        if bl.exists() and not baseline_md:
            baseline_md = read_skill_md(bl)

        # Current = latest stage version
        cur = p / "SKILL.md"
        if cur.exists():
            current_md = read_skill_md(cur)
            current_source = s["stage"]

    if not baseline_md and not current_md:
        st.info("No SKILL.md files found.")
    elif not baseline_md:
        st.info("No baseline snapshot. Showing current SKILL.md only.")
        st.code(current_md, language="markdown")
    else:
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("**Baseline (Sundial Original)**")
        with col_right:
            st.markdown(f"**Current ({current_source})**")

        # Unified diff
        diff_lines = list(unified_diff(
            baseline_md.splitlines(keepends=True),
            current_md.splitlines(keepends=True),
            fromfile="baseline/SKILL.md",
            tofile=f"{current_source}/SKILL.md",
            lineterm="",
        ))

        if diff_lines:
            # Color the diff
            diff_html = []
            for line in diff_lines:
                if line.startswith("+") and not line.startswith("+++"):
                    diff_html.append(f'<div style="background:#163b1e;color:#4ade80;font-family:monospace;padding:1px 8px;margin:0;">{_escape(line)}</div>')
                elif line.startswith("-") and not line.startswith("---"):
                    diff_html.append(f'<div style="background:#3b1616;color:#f87171;font-family:monospace;padding:1px 8px;margin:0;">{_escape(line)}</div>')
                elif line.startswith("@@"):
                    diff_html.append(f'<div style="color:#60a5fa;font-family:monospace;padding:1px 8px;margin:0;">{_escape(line)}</div>')
                else:
                    diff_html.append(f'<div style="color:#d1d5db;font-family:monospace;padding:1px 8px;margin:0;">{_escape(line)}</div>')

            st.markdown(
                f'<div style="background:#1e1e1e;border-radius:8px;padding:8px;max-height:600px;overflow-y:auto;">{"".join(diff_html)}</div>',
                unsafe_allow_html=True,
            )

            # Stats
            added = sum(1 for l in diff_lines if l.startswith("+") and not l.startswith("+++"))
            removed = sum(1 for l in diff_lines if l.startswith("-") and not l.startswith("---"))
            st.caption(f"+{added} lines added, -{removed} lines removed")
        else:
            st.success("No changes — baseline and current are identical.")

        # Side-by-side raw view
        with st.expander("Side-by-side raw view"):
            col_l, col_r = st.columns(2)
            with col_l:
                st.code(baseline_md, language="markdown")
            with col_r:
                st.code(current_md, language="markdown")
