 Deep dive - The core problem:

  Your system has rich data but weak navigation. Users get answers but can't explore. The graph shows structure but doesn't drive insights. Each view is a dead-end.

  The Real Questions

  1. Graph DB Structure - Is it right?

  Current:
  Provision -[PARENT_OF]-> Child
  Provision -[REFERENCES]-> Other

  Missing relationships:
  // Temporal connections
  (v2024) -[AMENDED_FROM]-> (v2018)  // Track evolution
  (v2024) -[UNCHANGED_SINCE]-> (v2006)  // Stability marker

  // Semantic connections
  (Def) -[DEFINES_TERM]-> (Term)  // "dealer" definition
  (Rule) -[USES_DEFINITION]-> (Def)  // Who uses it

  // Compliance structure
  (Rule) -[HAS_EXCEPTION]-> (Exception)
  (Rule) -[REQUIRES]-> (Condition)
  (Violation) -[PENALTY]-> (Punishment)

  Why this matters: Right now, to find "what uses the definition of 'dealer'", you'd need semantic search. But it SHOULD be a graph traversal. The relationships encode legal meaning.

  Better schema = better queries:
  - "Show everything affected if this definition changes" → follow USES_DEFINITION edges
  - "What are the exceptions to this rule?" → follow HAS_EXCEPTION
  - "What's the penalty?" → follow PENALTY edge

  ---
  2. Functional Ideas - Show Value

  Idea 1: The "Provision Hub" (Not Just a Detail Page)

  Instead of separate pages, make EVERY provision a hub with contextual panels:

  ┌─────────────────────────────────────────────┐
  │  /us/usc/t18/s922/a/1                       │
  │  ════════════════════════════════════       │
  │                                             │
  │  [Current Text - 2024]                      │
  │  "It shall be unlawful for any person..."  │
  │                                             │
  │  ┌──────────┬──────────┬──────────┐        │
  │  │Timeline  │Relations │Changes   │        │
  │  └──────────┴──────────┴──────────┘        │
  │                                             │
  │  Active: TIMELINE                           │
  │  ┌─────────────────────────────────┐       │
  │  │ 1994 ──●────●────●────●────● 2024│       │
  │  │    2000  2006  2013  2018  2022  │       │
  │  │                                  │       │
  │  │ ● 2013: Added exception for...  │       │
  │  │ ● 2006: Changed "dealer" def... │       │
  │  └─────────────────────────────────┘       │
  │                                             │
  │  [Click 2013 → text updates above]          │
  └─────────────────────────────────────────────┘

  Key: Text + Context always together. No context switching.

  ---
  Idea 2: "Impact Radius" View

  When viewing a provision, show its sphere of influence:

  Center: §922(d)(3) - "unlawful user of controlled substance"

  Ring 1 (Direct):
    → References §802 (definition of "controlled substance")
    ← Referenced by §922(g)(3) (penalties)
    ← Referenced by §924 (sentencing)

  Ring 2 (Indirect):
    → §802 references DEA schedules
    ← §924 referenced by sentencing guidelines

  Changed in: 2006, 2013
  If this changes → affects 8 provisions

  Why powerful: Shows blast radius. Attorneys need this for impact analysis.

  ---
  Idea 3: "Change Constellation"

  Timeline showing not just THIS provision, but everything connected:

                  §922(a)
                    │
      2000 ─────────●─────────── Added subsection (9)
                    │
                    ├──────── §923 (referenced)
                    │           │
      2006 ─────────┼───────────●── Changed licensing requirements
                    │
      2013 ─────────●─────────── Modified exception language
                    │
                    └──────── §921(a)(3) (definition)
                                │
      2018 ──────────────────────●── Expanded definition of "dealer"

  Why powerful: See cascade effects. "2018 changed a definition that §922 relies on."

  ---
  Idea 4: "Decision Tree Navigator"

  For compliance questions, generate an interactive tree:

  "Can I sell this firearm to this person?"
  │
  ├─ Is buyer prohibited under §922(d)?
  │  ├─ Convicted felon? → §922(d)(1) ❌ STOP
  │  ├─ Unlawful drug user? → §922(d)(3) ❌ STOP
  │  └─ None apply? ✅ Continue
  │
  ├─ Am I licensed? → §922(a)(1)
  │  ├─ No license? ❌ STOP - violation of §922(a)(1)(A)
  │  └─ Licensed? ✅ Continue
  │
  └─ Background check? → §922(t)
     ├─ Not performed? ❌ STOP
     └─ Cleared? ✅ SALE PERMITTED

  Why powerful: Actionable. Not "read the statute" but "answer these questions."

  ---
  Idea 5: "Inline Cross-Reference Expansion"

  Make provision text NAVIGABLE:

  §922(a)(2): "for any importer, manufacturer, dealer,
  or collector licensed under [§923]▼ to ship or
  transport in interstate commerce..."

  [Click §923▼]:
    ┌────────────────────────────────┐
    │ §923 - Licensing              │
    │                               │
    │ (a) No person shall engage... │
    │                               │
    │ [View Full] [Timeline] [Graph]│
    └────────────────────────────────┘

  Why powerful: Don't force users to navigate away. Expand in context.

  ---
  Idea 6: "Semantic Clusters"

  Use embeddings in the graph:

  // Add similarity edges during data load
  MATCH (p1:Provision), (p2:Provision)
  WHERE p1.year = p2.year
    AND vectorSimilarity(p1.embedding, p2.embedding) > 0.85
  CREATE (p1)-[:SEMANTICALLY_SIMILAR {score: similarity}]->(p2)

  Then query: "Show me provisions conceptually similar to this one, even if not directly referenced"

  Why powerful: Find related rules that don't explicitly cite each other.

  ---
  Idea 7: "Living Chat"

  Chat shouldn't be separate. Make it a persistent sidebar:

  ┌──────────────┬─────────────────────────┐
  │              │                         │
  │  Chat (↔)   │   Provision View        │
  │              │                         │
  │  "What are  │   §922(a)               │
  │  background │   ┌──────────────┐      │
  │  check      │   │ Text shows   │      │
  │  rules?"    │   │ here         │      │
  │              │   └──────────────┘      │
  │  Answer:    │                         │
  │  §922(t)... │   Timeline below        │
  │  [View →]   │   ────●────●────        │
  │              │                         │
  │  "When did  │   [Click View → jumps   │
  │  this       │    to §922(t) without   │
  │  change?"   │    losing chat context] │
  └──────────────┴─────────────────────────┘

  Why powerful: Chat becomes navigation. Persistent context.

  ---
  3. Graph Query Power

  Enable these queries:

  // 1. "What would be illegal in 2010 but legal now?"
  MATCH (old:Provision {year: 2010})
  WHERE old.text CONTAINS "unlawful"
    AND NOT EXISTS {
      MATCH (new:Provision {provision_id: old.provision_id, year: 2024})
    }
  RETURN old

  // 2. "Show full dependency chain for §922(t)"
  MATCH path = (start:Provision {provision_id: '/us/usc/t18/s922/t'})
    -[:REFERENCES*1..3]->()
  RETURN path

  // 3. "What uses the definition in §921(a)(3)?"
  MATCH (def:Provision {provision_id: '/us/usc/t18/s921/a/3'})
    <-[:USES_DEFINITION]-(user)
  RETURN user

  // 4. "Blast radius of §922(d) change"
  MATCH (center:Provision {provision_id: '/us/usc/t18/s922/d'})
  MATCH path = (center)<-[:REFERENCES*1..2]-(affected)
  RETURN center, affected, length(path) as distance

  ---
  Bottom Line - The Paradigm Shift

  Current: Separate tools (chat, graph, timeline, diff)
  Better: Provision-centric workspace where:
  - Every provision is a hub
  - Context (timeline/graph/relations) is always visible
  - Chat is persistent navigation
  - Links are bidirectional (answer → provision → chat)
  - Graph drives action, not decoration

  The question isn't "how do we improve the graph view?"
  It's "how do we make the graph INVISIBLE but powerful?"