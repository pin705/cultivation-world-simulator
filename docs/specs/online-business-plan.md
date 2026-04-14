# Cultivation World Simulator Online Business Plan

Status: draft v1  
Owner: product / design / engineering shared spec  
Updated: 2026-04-13  
Related:
- `docs/specs/external-control-api.md`
- `docs/specs/config-architecture.md`
- `docs/specs/online-commercial-master-plan.vi.md`
- `docs/specs/online-financial-model.md`
- `docs/specs/online-business-roadmap-90-days.md`
- `docs/specs/ui-ux-shuimo-direction.md`

## 1. Executive Summary

This project should not be commercialized as a real-time "AI sim that keeps talking forever".

The recommended product direction is:

- turn the current offline observer sim into an `async online cultivation world`
- make each player own meaningful agency through `sect`, `main disciple`, and `limited fate interventions`
- treat LLM as a `premium narrative layer` for key moments, not the engine for every NPC every tick
- monetize through `season/world access`, `private worlds`, `cosmetics`, and `premium creator tools`

If we launch the current model as-is, the likely outcome is:

- AI cost stays structurally high
- player agency stays too low
- retention stays weak because players mostly watch logs
- griefing and multi-tenant problems appear immediately

If we pivot correctly, the game can become:

- a distinctive online xianxia sandbox
- a creator-friendly shared world product
- a commercially viable hybrid of sim, strategy, social drama, and lightweight live-ops

### 1.1 Commercial operating principle

This project should be run as a business program, not a hobby or a speculative sandbox.

That means:

- every phase must improve at least one of `revenue readiness`, `margin`, `retention`, or `operational safety`
- no major feature should be built without a clear path to either paid value or measurable retention
- no team should describe the target as "just an MVP" if the real goal is a revenue-producing product
- phased delivery is still required, but each phase should be framed as a `commercial milestone`, not a toy milestone

## 2. Current State Diagnosis

### 2.1 What already works

The current codebase already has strong raw material:

- a rich world simulation loop
- emergent relationships, sects, wars, breakthroughs, hidden domains, tournaments, dynasties
- an event feed that naturally produces drama
- a front-end that can already visualize the world map, entities, and event timeline
- external control API foundations that can evolve into a real service boundary

The strongest fantasy today is:

- `watch a living xianxia world unfold`

### 2.2 What blocks commercialization

The current build has four structural blockers.

#### A. AI cost is too coupled to simulation volume

Today the sim advances continuously and many NPC decisions can hit LLM paths. That makes cost scale with:

- number of NPCs
- number of active worlds
- number of story triggers
- number of ticks

This is the wrong cost shape for an online game business.

#### B. Player agency is too weak

Right now the emotional loop is:

1. read world
2. watch events
3. sometimes tweak a value
4. keep watching

That is a useful exploration loop, but not yet a sticky commercial loop.

#### C. Runtime is effectively single-world and host-oriented

The current architecture is still close to:

- one runtime
- one in-memory world
- one broadcast channel
- host/admin style mutation powers

That is fine for a desktop incubation build and unacceptable for a public service.

#### D. Monetization is not aligned with value delivery

If revenue depends on "the sim happens to run", but joy depends on "interesting player-caused consequences", margin and retention will fight each other.

## 3. Recommended Product Positioning

### 3.1 Product thesis

Recommended pitch:

> An async online cultivation world where players guide a sect, sponsor key disciples, and shape a living xianxia world that keeps evolving between sessions.

This is better than pitching:

- "AI NPC simulator"
- "MMO cultivation sandbox"
- "idle spectator world"

because those frames either sound too expensive, too broad, or too passive.

### 3.2 Target fantasy

The product should deliver three fantasies at the same time:

- `power fantasy`: I can influence fate, politics, and cultivation outcomes
- `story fantasy`: I get memorable, shareable xianxia drama
- `ownership fantasy`: my sect, my disciple, my world history matter

### 3.4 Launch geography and channel strategy

Recommended market order:

- `Vietnam first`
- `Southeast Asia second`

Recommended commercial channel:

- `web direct first`

Channel rules:

- do not rely on Steam as an early revenue pillar
- if Steam is used at all in the first phase, treat it as awareness and discovery, not the primary sales channel
- prioritize local Vietnamese payment rails for the first paid cohorts and private worlds

### 3.3 Recommended player role

The recommended launch role is not "control one avatar directly in real time".

The recommended launch role is:

- each player owns a `sect`
- each player designates one `main disciple` or `favored lineage`
- each player has a limited pool of `fate interventions`

Why this is the best fit for the current repo:

- it preserves the strength of autonomous world simulation
- it turns existing admin-like interventions into gameified powers
- it creates attachment through one hero character
- it avoids having to build full real-time character controls for launch

## 4. Core Gameplay Pivot

### 4.1 From spectator sim to agency loop

The new core loop should be:

1. enter the world and read a short recap
2. inspect your sect, main disciple, rivals, and current opportunities
3. spend limited actions for this cycle
4. leave the world
5. return later to see consequences

### 4.2 Recommended session loop

Target average session: `5 to 12 minutes`

Recommended session activities:

- claim recap rewards
- assign sect priorities
- choose one disciple sponsorship
- spend fate points on one intervention
- react to one threat or opportunity
- check market / rankings / sect diplomacy

### 4.3 Recommended progression loop

Long loop:

1. survive early era
2. grow sect influence
3. raise a memorable disciple
4. compete for world events and prestige
5. secure inheritance, relics, hidden domains, alliances
6. enter season-end reckoning and rewards

### 4.4 Recommended live world cadence

For public shared worlds:

- background tick every `10 to 30 minutes`
- each batch simulates `1 in-game month`
- key results are bundled into recap packets

For private worlds:

- allow faster cadence or on-demand advancement
- keep a hard budget cap for AI and simulation throughput

This cadence is slow enough for cost control and fast enough for "the world is alive".

### 4.5 What the player can actually do

Launch command set should be narrow and meaningful.

Recommended player actions:

- set sect priority: cultivation, expansion, diplomacy, commerce, defense
- fund one disciple: pills, manuals, weapons, closed-door training
- trigger one fate intervention: omen, rescue, concealment, inspiration, sabotage
- choose one world response: join event, ignore event, support ally, punish enemy
- schedule one strategic objective: capture region, court alliance, contest domain, groom successor

Avoid launch scope like:

- direct movement click spam
- manual combat micro
- free-form global object editing
- unrestricted "god mode" commands

## 5. AI Strategy and Cost Control

### 5.1 Core rule

LLM should be used when it increases player-perceived value, not whenever the sim needs a decision.

### 5.2 AI tiering model

Use three NPC intelligence tiers.

#### Tier A: key characters

Who:

- player main disciples
- sect leaders
- major rivals
- champions in major events

Allowed LLM usage:

- long-term goal updates
- major decisions
- major story generation
- recap personalization

#### Tier B: important supporting NPCs

Who:

- named disciples
- elders
- court figures
- recurring rivals

Allowed LLM usage:

- occasional planner refresh
- only when a major trigger fires

#### Tier C: background population

Who:

- ordinary cultivators
- filler sect members
- minor civilians

Allowed LLM usage:

- none by default

These characters run on rules, utility scoring, and probabilistic templates.

### 5.3 Narrative generation policy

Generate story text only for:

- breakthroughs
- duels
- confessions and major relationship changes
- tournaments
- hidden domain outcomes
- sect wars
- player-caused interventions
- season recap / day recap

Do not generate long prose for:

- routine movement
- basic harvesting
- low-stakes conversations
- every monthly decision

### 5.4 Cost budgeting model

Track AI cost as a live budget, not as an afterthought.

Working formulas:

- `AI cost/day = worlds x batches/day x avg_llm_calls/batch x avg_cost/call`
- `AI cost/payer = AI cost/day / paying_users/day`
- `gross margin = (revenue - AI - infra - payment fees - support - content ops) / revenue`

Launch targets:

- AI cost <= `12%` of gross revenue
- infra + AI combined <= `20%` of gross revenue
- one active payer should subsidize at least `15 to 25` free or lightly paying users

### 5.5 Prompt and infra optimization checklist

- cache world context aggressively
- summarize state before prompting instead of dumping raw state
- batch recap generation
- use small/fast models for classification and relation deltas
- reserve higher quality models for season recap or premium narrative moments
- add hard daily AI budget per world
- degrade gracefully to rule-based text when budget is exhausted

### 5.6 External pricing reference

If DeepSeek remains part of the model mix, pricing assumptions must be refreshed before launch. As checked on `2026-04-13`, the official pricing pages are:

- [DeepSeek Pricing](https://api-docs.deepseek.com/quick_start/pricing/)
- [DeepSeek Pricing Details (USD)](https://api-docs.deepseek.com/quick_start/pricing-details-usd)

Because the published pages are not perfectly aligned, finance planning should assume the higher practical cost until a production provider is finalized.

## 6. Monetization Strategy

### 6.1 Monetization principles

- never sell raw token usage as the player-facing value proposition
- never make the game feel like a metered chatbot
- sell ownership, identity, convenience, style, and special world formats

### 6.2 Recommended revenue stack

Primary revenue:

- `season pass`
- `private world subscription`
- `founder pack / premium access`

Secondary revenue:

- cosmetics for sect, banners, portraits, frames, title seals, map accents
- premium chronicle exports and story album features
- premium creator tools for custom world lore and event packs

Optional later revenue:

- clan/world sponsorship for social groups
- event entry tickets for high-stakes seasonal modes
- guild-themed bundles

Vietnam-first interpretation:

- paid founder cohorts and paid pilot cohorts should be priced in `VND`
- private worlds should be marketed as a shared monthly realm for friend groups, guilds, or communities
- payment UX should optimize for local transfer and instant confirmation before expanding broader SEA payment complexity

### 6.3 What not to sell

- pay-to-win raw power that invalidates the world sim
- unlimited interventions
- compulsory token packs for basic play
- overly aggressive energy systems

### 6.4 Recommended product packaging by stage

#### Stage 1: paid founder pilot

- paid founder pack or invited paying cohort
- very limited world count
- manual operations accepted

#### Stage 2: first revenue release

- one public world
- premium private worlds
- cosmetic starter catalog

#### Stage 3: scaled commercial launch

- free-to-start onboarding
- season pass
- premium private worlds
- creator economy add-ons

### 6.5 Revenue model examples

Useful planning formulas:

- `MRR = private_world_subscriptions + recurring premium memberships`
- `season revenue = season pass buyers x season price`
- `ARPDAU = daily revenue / daily active users`
- `payer mix = whales + mid spenders + low spenders`

Practical launch targets:

- payer rate `3% to 8%`
- private worlds contribute `25%+` of revenue
- cosmetics contribute `10% to 20%` after content volume improves
- season pass contributes the largest share in the first scalable phase

## 7. Product Scope for the First Revenue Release

### 7.1 Must-have

- account system
- world instance system
- player ownership model
- sect dashboard
- main disciple flow
- limited intervention currency
- async recap feed
- stable payments and entitlement handling
- analytics, logs, moderation, GM tools
- strong onboarding and clear "what should I do now" UX

### 7.2 Should-have

- private worlds
- rankings and season ladder
- season-end rewards
- shareable story cards
- in-game codex / chronicle
- rejoin reminders and notifications

### 7.3 Nice-to-have later

- creator-authored event packs
- spectator mode for famous worlds
- social graph and friend referral
- advanced sect diplomacy UI
- marketplace and auction depth

### 7.4 Explicit no-scope for the First Revenue Release

- full action-combat MMO controls
- open global chat moderation nightmare
- player housing
- complicated crafting tree
- unrestricted sandbox editing

## 8. Online Service Architecture

### 8.1 Core shift

Move from:

- one process / one world / host-owned mutations

to:

- many world instances
- queue-based mutation processing
- snapshot-based read model
- per-world AI and simulation budget

### 8.2 Recommended service boundaries

Core services:

- auth and account
- world lifecycle service
- command service
- query service
- simulation worker
- billing and entitlement service
- analytics and telemetry pipeline
- notification service

### 8.3 Recommended data model

Minimum entities:

- `users`
- `player_profiles`
- `world_instances`
- `world_memberships`
- `player_sects`
- `player_disciples`
- `commands`
- `world_snapshots`
- `world_events`
- `billing_events`
- `season_progress`
- `inventory_and_cosmetics`

### 8.4 Runtime model

Recommended flow:

1. player submits command
2. command enters per-world serialized queue
3. simulation worker applies command safely
4. world snapshot updates
5. recap/event projections update
6. client receives incremental result

### 8.5 Technical priorities before public launch

- remove direct route-to-world mutation paths
- enforce serialized mutation at runtime layer
- split public query and command contract cleanly
- persist world snapshots and event history
- add retry-safe command ids
- add audit trail for economy-affecting mutations

## 9. UX and Retention Design

### 9.1 Retention thesis

Players do not return because the sim exists.

Players return because:

- someone they care about changed
- something they owned was threatened
- a promise is about to pay off
- they feel responsible for the next move

### 9.2 Retention hooks

- favorite disciple progression
- sect rivalry
- season milestones
- rare world events
- recap summaries with consequences
- pending decisions with a clear timer
- limited intervention recovery

### 9.3 Social hooks

- friend-run private worlds
- sect rivalry leaderboards
- shared chronicle moments
- invite-only season starts
- co-managed worlds later

## 10. Analytics and KPI Framework

### 10.1 Product KPIs

Track at minimum:

- D1 / D7 / D30 retention
- average sessions per week
- average session length
- command actions per session
- recap open rate
- world revisit rate
- season completion rate

### 10.2 Business KPIs

- payer conversion
- ARPDAU
- ARPPU
- private world conversion
- season pass attach rate
- refund rate
- payment failure rate

### 10.3 AI and infrastructure KPIs

- AI cost per world-day
- AI cost per payer
- AI cost per major story
- average LLM calls per batch
- world sim latency
- queue depth
- snapshot generation time

### 10.4 Fun diagnostics

- player-caused event share
- number of meaningful decisions per session
- ratio of passive reading time to active choice time
- disciple attachment rate
- recurrence of rival relationships

## 11. Operations and Live-Ops

### 11.1 Content cadence

Recommended cadence:

- weekly world modifiers or featured worlds
- biweekly event tuning
- monthly cosmetic drop
- season cycle every `6 to 10 weeks`

### 11.2 GM and moderation tools

Need before scale:

- world freeze / resume
- entitlement repair
- command audit
- player intervention history
- economy abnormality detection
- safe content override for generated text

### 11.3 Community strategy

- founder cohort with direct feedback loop
- devlogs explaining world stories and balance changes
- shareable recap cards
- curated "world legends" content for marketing

## 12. Team and Resourcing

### 12.1 Lean launch team

Minimum serious team:

- 1 product / design owner
- 1 gameplay engineer
- 1 backend / infra engineer
- 1 frontend engineer
- 1 technical artist or UI designer
- 1 part-time ops / support / community owner

One person can cover more than one role in incubation and paid pilot stages, but these functions must exist.

### 12.2 First 6 months focus split

- `35%` engineering platform and online architecture
- `25%` gameplay agency redesign
- `20%` UI/UX and onboarding
- `10%` monetization and commerce plumbing
- `10%` analytics and live-ops tools

## 13. Financial Planning Heuristics

### 13.1 Cost buckets

Plan budget around:

- model usage
- servers and storage
- payment processing fees
- support and moderation
- art and content production
- marketing and creator seeding

### 13.2 Margin guardrails

Healthy early-stage guardrails:

- AI cost should not exceed payment processing cost by a large margin
- private worlds should be individually profitable
- premium worlds should have explicit cost ceilings
- no live mode should be launched without a cost-per-world estimate

### 13.3 Example decision rules

- if a world is below monetization threshold, reduce AI richness automatically
- if a player is inactive, world simulation should summarize rather than fully narrate
- if a story budget is exhausted, fall back to templated prose and save premium generation for next recap

## 14. Compliance, Platform, and Legal Notes

### 14.1 AI disclosure

If the game is distributed on Steam, AI usage disclosure must be handled in line with the current Steamworks content survey guidance:

- [Steamworks Content Survey](https://partner.steamgames.com/doc/gettingstarted/contentsurvey)

### 14.2 User-generated and generated content safety

Need policies for:

- unsafe prompt injection through lore input
- abusive names and custom content
- generated text moderation and fallback
- account sanctions and appeal flow

### 14.3 Payments and entitlements

Need:

- payment event idempotency
- receipt reconciliation
- manual grant flow
- refund-safe entitlement revocation rules

## 15. Risks and Mitigation

### 15.1 Biggest product risks

Risk: still feels passive  
Mitigation:

- force every session to contain at least one meaningful choice
- reduce dead information density
- give every player one protected emotional anchor

Risk: AI cost still too high  
Mitigation:

- ship with strict tiering
- set world budgets
- make premium story density a tunable live-ops lever

Risk: online complexity delays launch  
Mitigation:

- launch with one world format
- keep commands narrow
- avoid premature social feature explosion

Risk: monetization feels cynical  
Mitigation:

- sell identity and access, not raw power
- keep free loop satisfying
- keep paid value legible and thematic

## 16. 12-Month Roadmap

### Phase 0: 0 to 6 weeks

- finalize product thesis
- cut AI call graph
- define player ownership model
- design sect + main disciple loop
- produce Shuimo-aligned UI direction

### Phase 1: 6 to 12 weeks

- build multi-world runtime foundation
- command queue and snapshot model
- account system
- first revenue-release wireframes
- recap-driven session loop

### Phase 2: 12 to 20 weeks

- paid founder pilot with founder pack
- one public test world
- one private world format
- basic cosmetics
- analytics and AI budget dashboards

### Phase 3: 20 to 32 weeks

- first revenue launch
- season loop
- premium private worlds
- improved art polish and social hooks

### Phase 4: 32 to 52 weeks

- creator tools
- richer live-ops calendar
- story sharing
- deeper sect diplomacy and market systems

## 17. Immediate 30-Day Action Plan

The best next month is not "launch online".

The best next month is:

1. redesign the player role into `sect owner + main disciple + limited interventions`
2. classify all current LLM calls into `keep`, `reduce`, `remove`, `on-demand`
3. define the first revenue-release screen flow
4. build the runtime plan for `world instances + command queue + snapshots`
5. implement the first Shuimo visual layer on the front-end shell

## 18. Decision Summary

Recommended decisions to lock now:

- `Yes`: async online world
- `Yes`: sect-based player ownership
- `Yes`: private worlds as an early monetization pillar
- `Yes`: AI as premium flavor layer, not universal decision engine
- `Yes`: Shuimo-inspired visual direction adapted to current stack
- `No`: real-time MMO scope for first commercial release
- `No`: pay-per-token user-facing pricing
- `No`: unrestricted god-mode admin actions in public worlds
