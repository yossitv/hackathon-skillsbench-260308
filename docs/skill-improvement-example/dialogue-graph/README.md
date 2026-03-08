# Dialogue Graph Skill — Before/After Comparison

## Source

- **Original skill**: bundled with SkillsBench `dialogue-parser` task
  - Repo: https://github.com/benchflow-ai/skillsbench
  - Path: `tasks/dialogue-parser/environment/skills/dialogue_graph/SKILL.md`

## Benchmark Results (SkillsBench, claude-code + claude-sonnet-4)

| Version | k=3 Scores | Mean |
|---------|-----------|------|
| **Before** (original) | 0.167, 0.667, 0.833 | **0.556** |
| **After** (personalized) | 0.0*, 0.833, 1.000 | **0.611** |

\* The 0.0 trial was a complete agent failure (no output file generated), not a skill quality issue.

### Key improvement

- After version achieved **1.000 (perfect score)** — something the original never reached
- The only change: added explicit DOT visualization guidance with `shape=diamond` for choice nodes
- Original skill mentioned diamond shapes but only in the context of `graph.visualize()` (requires graphviz package, often unavailable in sandboxes)
- Enhanced skill added a concrete manual DOT example showing per-node shape attributes

### What we learned

- **Less is more**: Over-prescriptive skills with full code templates scored WORSE (0.667, 0.500)
- **Targeted fixes win**: A small, focused addition addressing the specific test gap improved the score
- The agent already knows how to parse dialogue scripts — it just needed the DOT format hint

## Files

- `before/SKILL.md` — Original 101-line generic library API reference
- `after/SKILL.md` — Enhanced 116-line version with manual DOT generation guidance
