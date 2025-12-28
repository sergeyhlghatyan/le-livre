# Le Livre: Phased Implementation Plan
## Product Roadmap for Navigation & Graph Architecture

---

## Product Owner Thinking: First Principles

### The North Star
**"Users should never get lost or lose context while researching law."**

### Success Metrics That Matter
1. **Time to Answer** - How fast users find what they need
2. **Navigation Depth** - How many provisions users explore per session
3. **Return Rate** - Do users come back?
4. **Context Retention** - Do users lose their place?

---

## Phase 0: Foundation (Weeks 1-2)
**Goal:** Fix data structure to enable everything else

### Why First?
You can't build a mansion on a shaky foundation. The UI ideas in nn.md require backend intelligence.

### What to Build

#### 1. Enhanced Graph Schema
```cypher
// Add these relationships to Neo4j
(Provision)-[:AMENDED_FROM {pub_law, date}]->(PreviousVersion)
(Provision)-[:USES_DEFINITION]->(Definition)
(Provision)-[:SEMANTICALLY_SIMILAR {score}]->(Provision)
```

**Why:** Enables impact radius, change tracking, semantic discovery

#### 2. LLM Diff Summaries (Backend)
```python
# Add to diff.py
async def summarize_change(old: str, new: str) -> DiffSummary:
    # GPT-4 summarizes: "Added prohibition for..."
    # Returns: summary, change_type, impact_level
```

**Why:** Users need "what changed?" not just red/green text

#### 3. GraphQL API Enhancement
```graphql
type ProvisionContext {
  provision: Provision!
  timeline: Timeline!
  relations: Relations!
  insights: AIInsights!  # NEW
}
```

**Why:** Frontend needs rich context in single query

### Success Criteria
- ✅ Graph queries run <100ms
- ✅ Diff summaries generate in <3s
- ✅ All provisions have relationship data

### User Story
*"As a developer, I can query rich provision context in one API call, so the frontend loads instantly."*

---

## Phase 1: Navigation Intelligence (Weeks 3-4)
**Goal:** Make current experience 10x better without breaking changes

### Why Next?
Highest ROI - big UX improvement, low risk, builds foundation for later phases.

### What to Build

#### 1. Provision Stack (Navigation State)
**Implementation:**
```typescript
// State management
provisionStack = [
  { id: '/us/usc/t18/s922/d', year: 2024 },
  { id: '/us/usc/t18/s921/a/33', year: 2024 }
]
```

**UI:**
```
┌────────────────────────────────────┐
│ Home > § 922(d) > § 921(a)(33)     │
│   ↑ Click to go back               │
└────────────────────────────────────┘
```

**Why:** Users know where they are, can backtrack easily

#### 2. Clickable Cross-References
**Implementation:**
- Parse provision text for references (regex: `§\d+`, `section \d+`)
- Make them clickable links
- Add hover preview (fetch provision summary)

**UI:**
```
"...licensed under [§923]▼..."
                    ↑
              Hover: Shows preview card
              Click: Opens provision
```

**Why:** Eliminate context switching - biggest pain point

#### 3. Enhanced Timeline Markers
**Implementation:**
- Add change markers to timeline
- Show change type (added/modified/removed)
- Click marker → show diff summary

**UI:**
```
1994 ──────●────────●───── 2024
         2006      2013
          ↑         ↑
       Modified   Added
```

**Why:** Users see when changes happened at a glance

### Success Criteria
- ✅ Users can navigate 5+ provisions without getting lost
- ✅ 80% of references are clickable
- ✅ Timeline shows change markers for all provisions

### User Stories
1. *"As an attorney, I can click any statute reference and see it immediately, so I don't lose my train of thought."*
2. *"As a user, I can see where I came from via breadcrumbs, so I can easily backtrack."*
3. *"As a researcher, I can see when a provision changed at a glance, so I know where to focus."*

### Metrics to Track
- **Before:** Users navigate 2-3 provisions per session
- **After:** Users navigate 5-7 provisions per session
- **Before:** 60% abandon after one reference
- **After:** 30% abandon after one reference

---

## Phase 2: Context Persistence (Weeks 5-6)
**Goal:** Keep context across navigation

### Why Next?
Builds on Phase 1. Once users navigate more, they need context to persist.

### What to Build

#### 1. Persistent Chat Sidebar (Optional)
**Implementation:**
- Add sidebar mode to layout
- Toggle between "full page" and "sidebar" chat
- Persist chat across page navigation

**UI:**
```
┌──────┬─────────────────────┐
│ Chat │  Provision View     │
│      │                     │
│ Q: What│  § 922(d)         │
│ changed?│                   │
│      │  [Content here]     │
│ A: In│                     │
│ 2013...│                   │
│      │                     │
│ [View →] ← Jumps to §922  │
└──────┴─────────────────────┘
```

**Why:** Users ask questions WHILE researching, not before

#### 2. Workspace State Persistence
**Implementation:**
- Store in localStorage:
  - Provision stack
  - Chat history
  - Current year
  - Open tabs
- URL-encode state for sharing

**UI:**
```
URL: /workspace?stack=922/d,921/a/33&year=2024

Anyone with link → loads exact same state
```

**Why:** Users can share research sessions, resume later

#### 3. Smart Prefetching
**Implementation:**
- Prefetch on link hover
- Prefetch common paths (§922 → §921)
- Cache aggressively

**Why:** Feels instant, not waiting

### Success Criteria
- ✅ Chat persists across navigation
- ✅ Workspace state survives page refresh
- ✅ Shared URLs load correct state

### User Stories
1. *"As a researcher, I can keep my chat visible while navigating provisions, so I don't lose the conversation."*
2. *"As a team member, I can share a URL with my colleague that shows exactly what I'm looking at."*
3. *"As a returning user, I can pick up where I left off, even after closing the browser."*

### Metrics to Track
- **Before:** 40% of users abandon mid-research
- **After:** 20% abandon mid-research
- **Before:** 0 shared research sessions
- **After:** 30% of sessions include sharing

---

## Phase 3: Provision Hub (Weeks 7-9)
**Goal:** Make provision detail page a rich research hub

### Why Next?
Foundation is solid, navigation works. Now make the destination better.

### What to Build

#### 1. Tabbed Interface
**Implementation:**
- Redesign `/provision/[id]` page
- Add tabs: Timeline, Relations, Changes, Impact
- Provision text always visible at top

**UI:**
```
┌──────────────────────────────────────┐
│ 18 USC § 922(d)(9) [2024]         ⚡│
│ ──────────────────────────────────  │
│ [Full provision text here]           │
│                                      │
│ ┌────────┬─────────┬─────────┐     │
│ │Timeline│Relations│Changes  │     │
│ └────────┴─────────┴─────────┘     │
│                                      │
│ [Active tab content]                 │
└──────────────────────────────────────┘
```

**Why:** All context in one place, no navigation needed

#### 2. Relations Tab
**Implementation:**
- Show what this provision references
- Show what references this provision
- Show semantically similar provisions
- Click any → open inline or in stack

**UI:**
```
┌─────────────────────────────────────┐
│ REFERENCES (Dependencies)            │
│ → §921(a)(33) - Definition [1996]   │
│ → §925A - Relief mechanism          │
│                                      │
│ REFERENCED BY (Dependents)           │
│ ← §922(g)(9) - Possession ban       │
│ ← §924(a)(2) - Penalties            │
│                                      │
│ SIMILAR (Semantic)                   │
│ ≈ §922(d)(1) - Felony (92%)         │
└─────────────────────────────────────┘
```

**Why:** Users see full context without searching

#### 3. Changes Tab
**Implementation:**
- Interactive timeline
- Click year → show diff
- LLM summary of changes
- Compare any two years

**UI:**
```
┌─────────────────────────────────────┐
│ 1994 ────●────●────●──── 2024      │
│        2006  2013  2018             │
│                                      │
│ Selected: 2013                       │
│ ─────────────────────────────────   │
│ 💡 Summary:                         │
│ Added prohibition for domestic      │
│ violence misdemeanors (Lautenberg)  │
│                                      │
│ [View Full Diff] [Compare Years]    │
└─────────────────────────────────────┘
```

**Why:** Users understand changes without manual comparison

#### 4. AI Insights Panel
**Implementation:**
- Show importance score (PageRank)
- Show common questions
- Show related provisions
- Show blast radius if changed

**UI:**
```
┌─────────────────────────────────────┐
│ 💡 AI INSIGHTS                      │
│                                      │
│ 📊 Importance: High (89th %ile)     │
│ 🔄 Last Changed: 1996               │
│ 📈 Blast Radius: 8 provisions       │
│                                      │
│ 💬 Common Questions:                │
│ • Are there exceptions?             │
│ • What qualifies as DV?             │
│ • When did this start?              │
│                                      │
│ 🔗 Frequently Viewed With:          │
│ • §922(g)(9)                        │
│ • §921(a)(33)                       │
└─────────────────────────────────────┘
```

**Why:** Users get context without asking

### Success Criteria
- ✅ 90% of research happens on provision hub (no navigation needed)
- ✅ Users spend 3x more time per provision (deeper understanding)
- ✅ Click-through on related provisions increases 5x

### User Stories
1. *"As an attorney, I can see everything about a provision in one place, so I don't need to navigate around."*
2. *"As a compliance officer, I can see when and why a provision changed, so I understand the impact."*
3. *"As a researcher, I get AI-powered insights about what's important, so I focus on what matters."*

### Metrics to Track
- **Before:** Average 30s per provision
- **After:** Average 90s per provision (more engaged)
- **Before:** 2 tabs/provision on average
- **After:** All tabs viewed 60% of time

---

## Phase 4: Advanced Intelligence (Weeks 10-12)
**Goal:** Power user features for deep analysis

### Why Last?
These are high-value but lower frequency. Only build after core experience is solid.

### What to Build

#### 1. Impact Radius Visualization
**Implementation:**
- D3.js or Cytoscape concentric circles
- Show direct (ring 1) and indirect (ring 2) impacts
- Color-code by change status
- Click any node → jump to provision

**UI:**
```
        §922(d)(9)
       ┌──────┐
       │Center│
       └──┬───┘
          │
    ┌─────┼─────┐
    │     │     │
  §921  §922g  §925A
   ↓     ↓
 5 more 3 more

Impact: 11 total provisions
```

**Why:** Shows blast radius for regulatory changes

#### 2. Change Constellation
**Implementation:**
- Multi-provision timeline
- Show this provision + dependencies
- Highlight cascading changes
- Interactive exploration

**UI:**
```
      §922(d) Timeline
2000 ───●────  Added
        │
        ├── §921(a)(33)
        │      │
2004 ───┼──────●── Definition clarified
        │
2013 ───●────  Modified
```

**Why:** See how changes propagate through law

#### 3. Decision Tree Navigator
**Implementation:**
- LLM-generated decision trees
- Interactive yes/no questions
- Export compliance reports
- Template library for common questions

**UI:**
```
🎯 Can I sell this firearm?

1. Is buyer prohibited?
   □ Felon  ☑ DV  □ Drug user

   → STOP: Cannot sell

Violated: §922(d)(9)
Penalty: §924(a)(2)

[Export Report]
```

**Why:** Actionable compliance guidance

### Success Criteria
- ✅ 20% of users use impact radius
- ✅ 10% of users use decision trees
- ✅ 5% of users export reports

### User Stories
1. *"As a policy analyst, I can see the full impact of a regulatory change, so I can prepare briefings."*
2. *"As a compliance officer, I can generate decision trees for common scenarios, so my team has clear guidance."*

---

## Risk Mitigation Strategy

### Technical Risks

| Risk | Mitigation |
|------|------------|
| Graph queries too slow | Pre-compute common paths, cache aggressively |
| LLM costs too high | Cache summaries, batch requests |
| UI complexity | Incremental rollout, feature flags |
| Data quality issues | Validation pipeline, manual review |

### Product Risks

| Risk | Mitigation |
|------|------------|
| Users don't adopt new UI | A/B test, keep old UI option |
| Features too complex | User testing every sprint |
| Wrong priorities | Weekly user interviews |
| Scope creep | Strict phase gates, no new features mid-phase |

---

## Resource Allocation

### Team Structure
- 1 Backend Developer (Python/FastAPI/Neo4j)
- 1 Frontend Developer (SvelteKit/TypeScript)
- 1 Full-Stack Developer (floats)
- 0.5 Product Owner (you)
- 0.25 Designer (contract)

### Weekly Sprints
- Monday: Planning & design review
- Tue-Thu: Development
- Friday: Demo, retro, user testing

### Budget Estimates
- **Phase 0:** 2 weeks × 2.5 devs = 5 dev-weeks
- **Phase 1:** 2 weeks × 2.5 devs = 5 dev-weeks
- **Phase 2:** 2 weeks × 2.5 devs = 5 dev-weeks
- **Phase 3:** 3 weeks × 2.5 devs = 7.5 dev-weeks
- **Phase 4:** 3 weeks × 2.5 devs = 7.5 dev-weeks

**Total: 12 weeks, 30 dev-weeks**

---

## Go/No-Go Decision Points

### After Phase 1
**Check:**
- Are users navigating more provisions?
- Is time-to-answer decreasing?
- Are users returning?

**If YES → Continue**
**If NO → Pivot or kill**

### After Phase 2
**Check:**
- Are users sharing workspaces?
- Is chat sidebar being used?
- Are sessions longer?

**If YES → Continue**
**If NO → Reassess Phase 3 scope**

### After Phase 3
**Check:**
- Is provision hub the primary destination?
- Are all tabs being used?
- Are users spending more time per provision?

**If YES → Continue to Phase 4**
**If NO → Focus on adoption, delay Phase 4**

---

## Success Metrics Dashboard

### North Star Metric
**Time to Answer:** Average time from question to finding answer

**Target:** <2 minutes (down from 15+ minutes)

### Supporting Metrics

| Metric | Baseline | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|--------|----------|---------|---------|---------|---------|
| Provisions/session | 2 | 5 | 7 | 10 | 15 |
| Avg session time | 5 min | 8 min | 12 min | 20 min | 30 min |
| Return rate (7-day) | 20% | 30% | 40% | 50% | 60% |
| References clicked | 10% | 50% | 70% | 80% | 90% |
| Shared workspaces | 0 | 0 | 30% | 40% | 50% |

---

## The Bottom Line

**Phase 0-1:** Foundation + Quick Wins (4 weeks)
→ Ship navigation improvements, validate concept

**Phase 2:** Context Persistence (2 weeks)
→ Ship persistent chat, validate retention

**Phase 3:** Provision Hub (3 weeks)
→ Ship rich detail page, validate engagement

**Phase 4:** Advanced Features (3 weeks)
→ Ship power tools, validate expansion

**Total:** 12 weeks to transform the product

**The key:** Ship early, measure relentlessly, iterate based on data.