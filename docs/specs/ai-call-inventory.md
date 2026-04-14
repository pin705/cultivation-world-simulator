# AI Call Inventory And Commercial Cost Policy

Status: draft v1  
Updated: 2026-04-13  
Scope: current codebase inventory after first commercial cost-control patch

## 1. Purpose

This document records:

- where LLM calls exist in the codebase
- which calls are now governed by task policy
- which calls were disabled or sampled in the first commercial cost-control pass
- which support tools now exist to measure task-level spend

## 2. Current Commercial Policy Summary

The first cost-control patch implements task-level policy in:

- `src/utils/llm/config.py`
- `src/utils/llm/client.py`

Configured tasks now support:

- `enabled`
- `sample_rate`
- `category`
- `commercial_action`

The active configuration lives in:

- `static/config.yml`

Commercial rollout profiles are now also available:

- runtime selector: `LLMProfile.commercial_profile`
- config source: `llm.commercial_profiles` in `static/config.yml`

That means the codebase can now switch between:

- `standard`
- `story_rich`
- `internal_full`

without forking the LLM call sites themselves.

## 3. Current Policy Outcomes

### 3.1 Kept at full strength

These tasks remain enabled because they still affect core game state or core player-facing agency:

| Task | Current policy | Why |
|---|---|---|
| `action_decision` | keep | Core avatar behavior |
| `long_term_objective` | keep | Strategic direction |
| `single_choice` | keep | Concrete mechanical resolution |
| `relation_resolver` | keep | Social state correctness |
| `relation_delta` | keep | Social delta correctness |
| `interaction_feedback` | keep | Mutual social responses |
| `sect_random_event` | keep | Macro world texture |
| `sect_random_event_reason` | keep | Macro world reason text |
| `auction_need` | keep | Auction demand resolution still depends on AI for now |
| `sect_decider` | keep | Sect-level strategy |
| `custom_content_generation` | keep | Explicit user/admin request |

### 3.2 Sampled down

These tasks still run, but at a lower rate:

| Task | Current policy | Why |
|---|---|---|
| `story_teller` | sample at `0.35` | Keep some premium narrative, fall back to factual text for the rest |

### 3.3 Disabled in the first commercial pass

These tasks were disabled because they are mostly flavor or low-value recurring spend:

| Task | Current policy | Why |
|---|---|---|
| `nickname` | disabled | Flavor only |
| `backstory` | disabled | Flavor only |
| `random_minor_event` | disabled | Ambient AI spend with weak business value |
| `sect_thinker` | disabled | Flavor prose, safe fallback exists |

## 4. Inventory By Code Location

### 4.1 Task-policy governed calls

| Task | File |
|---|---|
| `action_decision` | `src/classes/ai.py` |
| `story_teller` | `src/classes/story_teller.py` |
| `long_term_objective` | `src/classes/long_term_objective.py` |
| `sect_decider` | `src/classes/sect_decider.py` |
| `backstory` | `src/classes/backstory.py` |
| `interaction_feedback` | `src/classes/mutual_action/mutual_action.py` |
| `nickname` | `src/classes/nickname.py` |
| `sect_thinker` | `src/classes/sect_thinker.py` |
| `relation_resolver` | `src/classes/relation/relation_resolver.py` |
| `relation_delta` | `src/classes/relation/relation_delta_service.py` |
| `random_minor_event` | `src/systems/random_minor_event_service.py` |
| `single_choice` | `src/systems/single_choice/engine.py` and call sites |
| `sect_random_event_reason` | `src/systems/sect_random_event.py` |
| `auction_need` | `src/classes/gathering/auction.py` |
| `custom_content_generation` | `src/server/services/custom_goldfinger_service.py`, `src/server/services/custom_content_service.py`, `src/classes/world_lore.py` |

### 4.2 Task usage reporting support

Commercial AI review now also has a lightweight log aggregation tool:

- `tools/llm_task_usage_report.py`

It reads `LLM_INTERACTION` rows and groups by `task_name`, so we can see:

- call counts
- skipped counts
- prompt volume
- response volume
- average duration

That gives the next commercial tuning passes a concrete baseline instead of intuition.

## 5. Commercial Interpretation

The first patch already shifts the AI profile in the right direction:

- removes low-value flavor generation
- suppresses ambient AI drift
- preserves core decisions and social mechanics
- keeps some narrative richness through sampled story generation

This is not the final commercial target.

It is the first safe cut that reduces recurring cost without breaking the core sim.

## 6. Recommended Next AI Cost Steps

### Step 1

Introduce premium-world aware policy overrides:

- standard worlds
- story-rich worlds
- internal test worlds

### Step 2

Reduce dependence on LLM for social state:

- more fixed delta rules
- more utility-based responses
- fewer free-text resolution calls

### Step 3

Add dashboard views for:

- calls by task
- calls by world
- calls by SKU tier
- skipped vs executed ratio

## 7. Practical Reading

Right now, the codebase has moved from:

- "every available AI garnish can fire"

to:

- "core AI stays, optional flavor is gated"

That is the correct first move for commercial online operation.
