# Shared context for agents is an operating model problem

AI is starting to raise personal productivity, but whether it raises team and company productivity is still an open question. Working with an agent differs from working with people, and that difference is what stands in the way.

This article is for strategy, operations and product leaders who want to move from individual to company-level impact: how to connect strategy to the daily work of individuals and teams, and what is missing between the two.

In a meeting, people bring their own knowledge, skills and experience into the company's shared context, and they exchange it continuously. Work with agents has no equivalent of that exchange yet, and a shared context alone does not supply it.

So the question I started from was this: how can individuals and groups use personal and shared knowledge interactively, as they do in a room together?

## Agents need both shared and local memory

Agents need persistent knowledge, shared and local, combined with scalable tools, so that individuals and teams can work at full capacity alone or together, async or in real time.

[IMAGE v1: shared-and-local-memory]

Most open-source setups I found for coding agents stop at one person. In my experience Claude Cowork is single-player by design: sharing context takes a Claude Project or hand-built MCP connections, which is cumbersome and needs manual steps.

I wanted to test the next step: people across functions working from one shared context, with each person's work rolling up into company goals. My first goal was to make the multi-player experience the default, with the system running the setup.

My second goal was a problem that predates AI: alignment. Strategy and goals are written down but often not linked to execution, so people regularly answer the same "so what?" from scratch: how does what I did this week connect to the company's goals?

So I built a prototype, Company Brain, of what I expect to become widely available once the right infrastructure and enterprise systems are in place.

## What Company Brain is

Company Brain is a shared, machine-readable context layer for an organization, combined with each person's private context. Automations keep that context current and control who sees what.

Access follows three layers: company, team and personal. Setup creates shared and local workspaces in one Obsidian vault of plain markdown, each with its own privacy rules. Content for the company and team layers lives in a shared drive, the system (skills, templates) is managed through git, and the personal layer (daily notes, 1:1s, private goals, drafts) stays on your laptop. Content moves up only by promotion.

[IMAGE v4: stack]

[IMAGE v5: layers-1]

[IMAGE v6: layers-2]

It builds on obsidian-second-brain by Eugeniu Ghelbur and adds automated workspace setup, strategy frameworks, and an operating rhythm that ties personal goals to daily work. The agent operates the vault with 32 skills, and the result is a set of personal and shared knowledge graphs that connect to the company's knowledge, tools and capabilities.

[IMAGE v2: company-brain-demo-1]

[IMAGE v3: company-brain-demo-2]

### Daily work links up to the strategy

The alignment problem gets one schema rule: **every note links to what it serves.** A weekly update links to the key results, team objectives and company objectives it moves. Meetings and decisions tie to the same goals through the built-in strategy and product frameworks, and the agent questions actions that do not align.

[IMAGE v7: alignment-1]

[IMAGE v8: alignment-2]

[IMAGE v9: alignment-3]

[IMAGE v10: alignment-4]

For individual contributors, the agent surfaces insights and patterns that would otherwise be hard to spot. For a team lead, it reports key result trends against goal, risks and decisions needed. Scheduled runs only draft: they never publish or promote personal content without the individual's agreement.

[IMAGE v11: team-view]

## AI system design is organizational design

Most of the design work was organizational: where knowledge lives, who can read and write each layer, which steps need a human sign-off, what done looks like, and the rhythm the team keeps. The code enforces those operating model decisions. My creation process was close to designing a planning cycle or an onboarding program.

Guardrails enforce quality in the system: hooks with automated tests, a freshness lint that keeps content current, and frontmatter written for agents that humans find useful too.

**AI systems are organizational design and operating model problems first: decide what is shared, who owns it, how it stays current and where a human says yes, then let the system enforce it.**

## Limitations

Company Brain is a prototype for early experimentation, and no real team has run it yet. An enterprise deployment of a similar system needs policies and controls enforced by the system itself: agent identities with scoped credentials (beyond OAuth token exchange), audit trails and delegation chains. That identity work is still emerging, with no settled standard for delegation chains.

Company Brain is open source under the MIT license: https://github.com/anna-hovhan/company-brain

It ships as an empty template with its own test suite and CI.

If you use agents for strategy, operations or product work today, which of your needs does shared context cover, and what is still missing?
