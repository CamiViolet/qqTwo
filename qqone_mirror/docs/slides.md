---
marp: true
theme: default
paginate: true
style: |
  * { font-size: 90%; }
---
# qqOne: AI-Augmented Knowledge Base
#### Carlo Camicia - TrustMotion (part of NXP)
#### 07/05/2026
---

## What is qqOne?

**qqOne** is a human-curated, AI-augmented knowledge management system designed for teams and individuals.

### Key Characteristics:
- **Markdown-based**: All documents stored as plain text markdown files
- **Human-maintained**: You control what goes in—no automatic crawling
- **AI-enhanced**: Integrates with LLMs (like GitHub Copilot) for intelligent queries
- **Context injection**: Provides dynamic context to AI without retraining

### What It's NOT:
- ❌ Not a RAG system with complex indexing pipelines
- ❌ Not an LLM-wiki for narrow topics
- ❌ Not an enterprise knowledge management system

---

## Why qqOne? The Problem It Solves

### Traditional Documentation Challenge:
Authors structure docs one way → Readers need different paths → Frustration

### Current AI Approach (RAG):
- ✓ Flexible and scalable to enterprise
- ✗ Complex toolchain
- ✗ Risk of stale or contradictory information
- ✗ Answers disappear into chat history

### qqOne's Approach:
**Build once, maintain continuously, query dynamically**

- Small but **information-dense** knowledge base
- Real-time updates—no delay
- Knowledge compiles incrementally as you work
- Context tailored to your actual needs

---

### How qqOne Works

```
knowledge-base/
├── log.md              # Chronological notes (continuously updated)
├── imports/            # Raw materials from multiple sources
└── activities/         # Focused projects or tasks
    ├── description.md
    ├── activity-output.md
    ├── 1bf_configs/    # Configurations for content generation
    └── scripts/        # Activity-specific automation
```

Workflow:
1. **Curate**: Add high-quality content to `imports/`
2. **Configure**: Create `1bf_configs/` to define what content to use
3. **Generate**: qqOne creates context files (`1bf` = "One Big File")
4. **Query**: Send context to AI, ask questions naturally
5. **Iterate**: Update knowledge base as you learn

---

### Benefits for Developers:
- ✓ Instant context without hunting through Confluence
- ✓ Consistent understanding across sprint handovers
- ✓ Knowledge survives beyond chat history

### Benefits for Architects:
- ✓ Design decisions and rationales organized and searchable
- ✓ Technical alternatives documented with pros/cons
- ✓ Architecture evolves with the project

### Benefits for Team Leaders:
- ✓ Knowledge transfer made explicit and maintainable
- ✓ Reduced onboarding time for new team members
- ✓ Minimal overhead—no complex infrastructure
