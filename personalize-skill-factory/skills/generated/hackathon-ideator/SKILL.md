---
name: hackathon-ideator
description: >
  Turn a hackathon event page into a winning idea. Use when: (1) User provides
  a hackathon event URL and wants to build a competitive submission, (2) User
  says "help me win this hackathon", "ideate for this event", or "analyze this
  hackathon", (3) User wants to identify sponsors, build reference docs, and
  co-create an idea that maximizes sponsor tool usage and judge appeal.
---

# Hackathon Ideator

Given a hackathon event URL, identify sponsors, build a reference library of their services, and co-create a winning idea with the user.

## Workflow

### Phase 1: Event Intelligence

1. Fetch the event page (Luma, Eventbrite, custom site, etc.)
2. Extract: event name, date, location, tracks, prizes, schedule, judging criteria, organizers, speakers
3. Identify sponsors — look for "Sponsored by", logos, partner sections, and resource providers mentioned in builder docs
4. For each sponsor, determine if they provide a **service/tool** vs. just venue/funding
5. Save event summary to `docs/references/<event-domain>.md`

### Phase 2: Sponsor Service References

For each sponsor that provides a service/tool:

1. Fetch their site (try homepage, then `/llms.txt`, then GitHub repo)
2. If SPA blocks content, try: export URL, GitHub README, or ask user for raw text
3. Extract: what it does, key features, API/SDK, pricing, getting started
4. Save to `docs/references/<sponsor-domain>.md`
5. Report which sponsors were fetched successfully vs. failed

### Phase 3: Sponsor Usage Map

Create a checklist in `docs/idea.md`:

```markdown
## Sponsor Service Usage Check

### Track: <track-name>
- [ ] **<Sponsor A>** — <how it's used>
- [ ] **<Sponsor B>** — <how it's used>
```

Maximize sponsor coverage — ideas that use more sponsor tools score better with judges. For each sponsor service, find a natural role in the project flow:

| Role | Example |
|------|---------|
| Input/Data source | Registry, API, dataset |
| Development environment | Cloud IDE, sandbox, container |
| Core logic | AI model, framework, SDK |
| Evaluation | Benchmark, testing, monitoring |
| Output/Distribution | Publishing, deployment, hosting |

### Phase 4: Idea Co-Creation

Work with the user to shape the idea:

1. **Ask what they're excited about** — personal projects, domain expertise, hardware they own
2. **Map their interest to tracks** — show which tracks fit
3. **Propose a sponsor-maximizing architecture** — every sponsor tool has a role
4. **Structure the idea**:
   - Concept (1-2 sentences)
   - Flow diagram (numbered steps with sponsor tool at each step)
   - Demo plan (fit within presentation time limit)
   - TODO checklist
5. **Check sponsor coverage** — mark checkboxes for services that will actually be used
6. **Iterate** — refine based on user feedback until the idea is sharp

### Phase 5: Competitive Analysis

Before finalizing, verify the idea is strong:

- [ ] Uses the majority of sponsor services (not just 1-2)
- [ ] Fits clearly into at least one track
- [ ] Has a measurable outcome (benchmark scores, before/after, demo)
- [ ] Can be demoed within time limit
- [ ] Solves a real problem (not contrived)
- [ ] Differentiator: what makes this unique vs. obvious submissions?

## Output Structure

```
docs/
├── references/
│   ├── <event-domain>.md        # Event summary
│   ├── <sponsor-1-domain>.md    # Sponsor service reference
│   ├── <sponsor-2-domain>.md
│   └── ...
└── idea.md                      # Idea with sponsor usage checklist
```

## Tips for Winning

- **Sponsor judges care about their tools being used well** — don't just mention them, integrate them deeply
- **Show before/after** — quantitative improvement is more convincing than qualitative claims
- **Multi-track submissions** — if the idea naturally spans tracks, submit to multiple
- **Live demo > slides** — working software wins
- **Tell a story** — problem → approach → result in the time limit
