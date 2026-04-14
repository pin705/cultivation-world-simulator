# Cultivation World Simulator 90-Day Online Business Roadmap

Status: draft v1  
Owner: founder / product / engineering shared plan  
Updated: 2026-04-13  
Related:

- `docs/specs/online-commercial-master-plan.vi.md`
- `docs/specs/online-business-plan.md`
- `docs/specs/online-financial-model.md`
- `docs/specs/ui-ux-shuimo-direction.md`
- `docs/specs/external-control-api.md`

## 1. Purpose

This roadmap converts the online business plan into a 90-day execution sequence.

The goal of the next 90 days is not full public launch.

The goal is to de-risk four things in order:

1. the game becomes meaningfully playable, not just watchable
2. AI cost can be reduced to a commercially survivable shape
3. the backend can support multi-world online operation safely
4. the team can prove enough business signal to justify the next 3 to 6 months

### 1.1 Commercial operating principle

This roadmap is business-first.

That means:

- each phase must move the product toward paid operation, not just technical completeness
- each workstream must connect to `revenue readiness`, `margin`, `retention`, or `operational safety`
- "MVP" is not the target framing here; the target framing is `first revenue-capable release path`
- a staged rollout is still necessary, but it is treated as commercial risk control rather than hobby validation

## 2. Day-90 Outcome

By Day 90, we should have a `commercial paid-pilot foundation`, not a polished broad launch product.

That commercial paid-pilot foundation should prove:

- a player can own a sect and one main disciple
- each session contains meaningful decisions
- the world advances asynchronously in batches
- public and private world formats are technically possible
- AI use is budgeted and intentionally limited
- the product has the first viable monetization shell

## 3. Day-90 Success Criteria

All of these do not need to be perfect, but they must be measurably real.

### 3.1 Product criteria

- the player loop is `recap -> choose -> commit -> wait -> consequence`
- there are at least `3 meaningful commands` per session
- the player has an emotional anchor through `main disciple`
- the player has ownership through `sect`
- major moments are easy to understand from the UI without reading walls of text

### 3.2 Technical criteria

- world instances exist as separate runtime units
- all state mutations flow through one serialized command path
- the game can generate snapshots and recap projections
- AI usage can be measured per world and per batch
- the system can degrade gracefully when AI budget is limited

### 3.3 Business criteria

- there is a founder paid-cohort package plan
- there is a private-world pricing hypothesis
- basic payment and entitlement flow is either implemented or mocked end to end
- the team can estimate `cost per world-day` and `cost per active player-day`

### 3.4 Go / no-go criteria for next phase

Proceed to the next 90-day phase only if:

- internal or invited testers say the game now feels participatory
- AI cost curve is no longer tied linearly to all NPC monthly decisions
- one closed world can run with stable operations and acceptable queue behavior
- at least one monetization angle feels legible and not awkward

## 4. Non-Goals for This 90-Day Window

- full public launch
- mobile launch
- real-time action combat
- deep guild system
- full creator economy
- massive content volume
- perfect art polish on every screen

## 5. Planning Assumptions

This roadmap assumes:

- current repository remains the primary incubation codebase
- team works in short weekly or two-week cycles
- product direction remains `async online cultivation world`
- launch role remains `sect owner + main disciple + limited interventions`
- first commercial surface is `founder paid cohort` or `closed paid pilot`, not broad free launch
- launch market is `Vietnam first`, then broader `SEA`
- first paid flow is `web direct`, not Steam sales

## 6. Recommended Team Shape

### 6.1 Minimum team

Recommended minimum working team for this 90-day push:

- `1` founder / product owner
- `1` gameplay engineer
- `1` backend / platform engineer
- `1` frontend engineer
- `1` UI/UX designer or technical artist
- `0.5` ops / support / QA ownership

If one person covers multiple roles, the function must still be explicitly assigned.

### 6.2 Default ownership model

- founder / product: scope control, monetization, priority calls
- gameplay engineer: player loop, systems redesign, command semantics
- backend engineer: runtime, world instances, queues, snapshots, accounts
- frontend engineer: shell, recap, sect dashboard, disciple flow
- design: Shuimo direction, flow clarity, interaction hierarchy
- ops / QA: telemetry, issue triage, test runs, paid-pilot readiness

## 7. Budget Planning Model

Because salary and contractor rates depend heavily on country, staffing mix, and contractor usage, this roadmap uses formulas instead of hard-coded market rates.

Let:

- `X = average loaded monthly cost of one full-time team member`

Then:

- lean 90-day team cost baseline = `13.5X to 15X`
- balanced 90-day team cost baseline = `18X to 21X`
- add `20% to 40%` on top for contractors, art, tools, infra, AI, and contingency

### 7.1 Planning scenarios

#### Lean scenario

- average staffing load: `4.5 to 5 FTE`
- total 90-day operating envelope: about `16X to 21X`

Use this if:

- cash is tight
- founder can personally cover product and ops
- art polish is intentionally narrow

#### Balanced scenario

- average staffing load: `6 to 7 FTE`
- total 90-day operating envelope: about `22X to 29X`

Use this if:

- you want a stronger commercial impression
- you want both design polish and backend progress in parallel

### 7.2 Budget buckets to track separately

- payroll and contractors
- AI usage
- cloud and storage
- commerce tooling and payment fees
- art and audio
- QA and ops
- contingency reserve

## 8. Workstreams

This roadmap uses five parallel workstreams.

### 8.1 Workstream A: Product and gameplay

Goal:

- turn the passive sim into a commercially testable decision loop

Core outputs:

- sect ownership loop
- main disciple loop
- intervention system
- recap and consequence loop

### 8.2 Workstream B: AI and simulation economics

Goal:

- reduce LLM dependency to high-value moments only

Core outputs:

- AI call inventory
- tiered NPC intelligence plan
- batch recap generation
- AI budget controls and telemetry

### 8.3 Workstream C: Online platform

Goal:

- make the game safely multi-world and online-ready

Core outputs:

- world instances
- serialized command queue
- snapshot read model
- account and ownership model

### 8.4 Workstream D: UX and front-end shell

Goal:

- make the game legible, intentional, and actionable

Core outputs:

- recap-first shell
- sect dashboard
- main disciple detail
- intervention UI
- first Shuimo pass

### 8.5 Workstream E: Commerce, analytics, and ops

Goal:

- prepare the product to learn and monetize, not just function

Core outputs:

- founder paid-cohort offer
- private world offer hypothesis
- payment and entitlement path
- analytics dashboard
- GM / support basics

## 9. Phase Structure

The 90 days are split into four phases.

### Phase 1: Days 1-21

Theme:

- lock the game loop and cost strategy

### Phase 2: Days 22-45

Theme:

- build the first vertical slice of the commercial loop

### Phase 3: Days 46-69

Theme:

- make it online-safe and commercially usable in closed cohorts

### Phase 4: Days 70-90

Theme:

- run paid-pilot readiness and business proof

## 10. Week-by-Week Roadmap

### Week 1

Primary goal:

- establish baseline truth

Tasks:

- audit all current LLM call paths and classify them into `keep`, `reduce`, `remove`, `on-demand`
- document the exact current player loop and passive pain points
- define the target launch role in one page: `sect`, `main disciple`, `interventions`
- define the Day-90 commercial success criteria and freeze them
- instrument current sim cost baseline and event volume baseline

Deliverables:

- `AI call inventory`
- `current-state pain map`
- `target role one-pager`
- `commercial scorecard v1`

Exit criteria:

- team agrees what the first revenue release actually is
- no one is still designing for "real-time AI spectator sim"

### Week 2

Primary goal:

- lock product loop and command vocabulary

Tasks:

- design the new session loop using `recap -> choose -> commit -> consequence`
- define the first 3 to 5 player commands
- define sect ownership semantics and what belongs to the player
- define main disciple semantics and emotional retention hooks
- define limited intervention currency and recovery cadence

Deliverables:

- `command vocabulary v1`
- `sect ownership spec`
- `main disciple spec`
- `intervention rules v1`

Exit criteria:

- every screen planned later has a clear primary action
- every player session can be described in 5 steps or fewer

### Week 3

Primary goal:

- define the commercial gameplay loop in paper and UI flow

Tasks:

- design the founder paid-pilot information architecture
- wireframe recap screen, sect dashboard, disciple detail, intervention drawer
- design what gets summarized versus what stays explorable
- define event hierarchy: factual, major, story, batch recap
- define first-time onboarding flow

Deliverables:

- `first revenue release UX flow`
- `event hierarchy spec`
- `onboarding flow v1`

Exit criteria:

- product and design agree what the player sees in their first 10 minutes

### Week 4

Primary goal:

- lock online architecture target

Tasks:

- define `world instance` data model
- define command queue semantics and idempotency
- define snapshot generation strategy
- define ownership and membership models
- define read and write service boundaries

Deliverables:

- `online architecture map`
- `runtime + snapshot contract`
- `ownership and membership data model`

Exit criteria:

- backend path away from single-world runtime is explicit and agreed

### Week 5

Primary goal:

- build the first offline vertical slice of the new loop

Tasks:

- implement basic sect ownership state
- implement main disciple selection / attachment flow
- implement one or two intervention vertical slices
- implement recap generation structure without full polish
- suppress or collapse low-value event noise

Deliverables:

- playable local vertical slice of the new loop

Exit criteria:

- internal testers can do more than watch
- at least one intervention causes visible downstream consequence

### Week 6

Primary goal:

- start AI cost separation from background simulation

Tasks:

- implement NPC tiering scaffolding
- convert background NPCs to non-LLM logic where feasible
- move story generation to major moments and recap hooks
- add AI spend logging by world, batch, and feature
- set hard AI budget guards in config

Deliverables:

- `AI tiering implementation v1`
- `budget telemetry v1`

Exit criteria:

- the team can estimate how much AI cost comes from each feature class

### Week 7

Primary goal:

- start multi-world runtime implementation

Tasks:

- implement world instance container
- implement per-world serialized mutation path
- refactor host-owned mutations behind command service boundaries
- add snapshot persistence skeleton
- create minimal account stub and world membership stub

Deliverables:

- `world instance runtime v1`
- `serialized command path v1`

Exit criteria:

- more than one world can exist conceptually without shared mutable chaos

### Week 8

Primary goal:

- connect product loop to online foundation

Tasks:

- bind sect ownership and disciple state to account or player identity
- expose query endpoints for recap, sect dashboard, disciple detail
- expose command endpoints for first player actions
- start front-end shell integration with real data
- create internal GM debug panel for world and player inspection

Deliverables:

- `end-to-end vertical slice over APIs`

Exit criteria:

- one tester can log in, view a world, make a command, and see the result later

### Week 9

Primary goal:

- make the paid pilot feel coherent

Tasks:

- implement Shuimo shell pass on core strategic screens
- improve recap readability and decision prompts
- reduce dead information density
- add one strong ritualized feedback moment for interventions
- add first basic founder paid-access landing and offer framing

Deliverables:

- `commercial shell v1`
- `founder paid-cohort offer draft`

Exit criteria:

- the product no longer looks like an internal admin tool on the main path

### Week 10

Primary goal:

- prepare business instrumentation

Tasks:

- implement analytics events for sessions, recap open, command use, disciple interactions
- implement Vietnam-first payment / entitlement flow
- define private world creation flow and operational limits
- model per-world operating cost
- define GM runbook for support and issue response

Deliverables:

- `analytics schema v1`
- `VN payment flow v1`
- `private world policy v1`
- `support runbook v1`

Exit criteria:

- the team can answer both "is it fun?" and "what does it cost?" with real data

### Week 11

Primary goal:

- run internal commercial-readiness playtests and tighten weak loops

Tasks:

- run a structured internal commercial-readiness playtest with scripted sessions
- collect friction on clarity, agency, and pacing
- patch any dominant or useless intervention choices
- tune recap density and notification timing
- confirm AI degradation behavior under budget pressure

Deliverables:

- `internal readiness findings report`
- `priority fix list`

Exit criteria:

- most testers can explain what their next move should be without coaching

### Week 12

Primary goal:

- paid-pilot readiness

Tasks:

- finalize founder paid-cohort packaging
- finalize minimum payment and entitlement path
- finalize world reset and save policy
- finalize privacy, moderation, and generated content fallback rules
- rehearse live operations for a single test world
- prepare Vietnamese launch copy and pricing presentation

Deliverables:

- `paid pilot checklist`
- `ops readiness checklist`
- `VN commercial launch sheet`

Exit criteria:

- the team can confidently invite external testers without manual chaos

### Week 13

Primary goal:

- make the investment decision for the next phase

Tasks:

- run founder paid cohort or invited paid-pilot cohort
- compare results against Day-90 scorecard
- assess cost-per-world and cost-per-active-player
- assess retention signals and command engagement
- decide whether to invest in the next 90 days, pivot harder, or stop

Deliverables:

- `Day-90 review`
- `next-phase recommendation`

Exit criteria:

- leadership can make a go / no-go decision from evidence instead of hope

## 11. Detailed Deliverables by Workstream

### 11.1 Product and gameplay

Must ship by Day 90:

- sect ownership
- main disciple
- intervention system
- recap-first session loop
- 3 to 5 meaningful commands

Should ship by Day 90:

- one rivalry loop
- one season or cycle progress marker
- one clearly legible prestige ladder

### 11.2 AI and simulation economics

Must ship by Day 90:

- AI call inventory
- NPC intelligence tiers
- budget telemetry
- budget caps
- degradation path

Should ship by Day 90:

- major event generation quality pass
- recap prompt compression
- feature-level cost dashboard

### 11.3 Online platform

Must ship by Day 90:

- world instances
- per-world command serialization
- snapshot or recap projection path
- account stub or live account system
- world membership and player ownership records

Should ship by Day 90:

- retry-safe command ids
- audit trail for money-affecting actions
- basic world lifecycle automation

### 11.4 UX and front-end shell

Must ship by Day 90:

- recap screen
- sect dashboard
- disciple detail
- intervention command surface
- first Shuimo shell pass

Should ship by Day 90:

- improved onboarding
- polished chronicle styling
- stronger premium and founder-access surfaces

### 11.5 Commerce and ops

Must ship by Day 90:

- founder paid-cohort offer
- entitlement path
- analytics schema
- support and GM basics
- pricing hypothesis for private worlds

Should ship by Day 90:

- first premium cosmetic concept pack
- founder invite/referral flow

## 12. Critical Metrics to Review Weekly

Review every week:

- internal test sessions completed
- meaningful commands per session
- recap open rate
- average time from recap to first action
- AI calls per world batch
- AI cost per feature bucket
- command queue health
- top friction issues

By external paid pilot:

- return rate after first session
- attachment to main disciple
- private world interest rate
- founder package conversion intent

## 13. Weekly Rituals

Recommended rituals:

- Monday: leadership priority lock
- Tuesday: product + design review
- Wednesday: architecture and metrics review
- Thursday: playtest or dogfood session
- Friday: demo + Day-N scorecard update

Keep every week honest by answering:

- what became more playable
- what became cheaper
- what became safer online
- what became more sellable

## 14. Major Risks During This Window

### Risk 1: team keeps polishing the old spectator loop

Mitigation:

- every sprint must include at least one player-agency deliverable

### Risk 2: AI cost work slips because it is invisible

Mitigation:

- make weekly AI budget dashboard mandatory

### Risk 3: backend refactor absorbs all energy

Mitigation:

- protect one end-to-end vertical slice at all times

### Risk 4: UX remains data-heavy and passive

Mitigation:

- force one obvious action per primary screen

### Risk 5: monetization is delayed until too late

Mitigation:

- founder paid offer and private world hypothesis must exist by Week 10

## 15. Day-90 Decision Matrix

At the end of this roadmap, choose one of three outcomes.

### Outcome A: proceed aggressively

Choose this if:

- testers show repeat intent
- player agency is clearly felt
- AI cost is under control
- private worlds or founder paid access show real demand

Next move:

- fund another 90 to 180 days toward broader revenue launch

### Outcome B: proceed narrowly

Choose this if:

- the game feels promising
- but online scope or cost is still fragile

Next move:

- focus only on private worlds or small founder cohort

### Outcome C: pause or pivot

Choose this if:

- the game is still mostly watch-only
- cost still scales badly
- testers do not show attachment or repeat intent

Next move:

- pivot to a smaller premium sandbox, creator tool, or offline-first product

## 16. Founder Checklist for the Next 7 Days

If starting immediately, the founder should do these first:

1. appoint owners for each workstream
2. freeze the Day-90 success criteria
3. schedule weekly playtest ritual
4. approve the new player role and command vocabulary direction
5. require AI cost telemetry before any new AI-heavy feature work
6. choose lean or balanced budget mode
7. announce that the commercial goal is `async online with agency`, not `real-time spectator AI sim`
