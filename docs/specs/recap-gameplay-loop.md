# Recap-First Gameplay Loop — Implementation Plan

> Phase 1 critical path: transform the game from "watchable" to "participatory"
> by introducing a recap-then-act cycle.

## 0. Design Rationale (MDA Lens)

| Layer | Current State | Target State |
|-------|--------------|--------------|
| **Mechanics** | Player watches auto-simulated world tick by | Player returns, reads recap, spends limited actions, leaves |
| **Dynamics** | Events pile up unread; player has no structured entry point | Each session has a clear start (recap), middle (actions), end (consequences) |
| **Aesthetics** | Passive observer feeling | Sense of stewardship, agency, and consequence |

### Core Engagement Loop (Target)

```
1. RECAP     → "Here's what happened while you were away"  (emotional hook)
2. INSPECT   → "Check your sect, disciple, rivals"         (orientation)
3. ACT       → "Spend N fate points on commands"           (agency)
4. OBSERVE   → "See immediate feedback"                    (feedback)
5. LEAVE     → "World simulates; you return later"         (anticipation)
```

### Player Psychology Drivers

- **Autonomy**: Limited but meaningful choices (fate points force prioritization)
- **Competence**: Recap shows cause-effect of previous decisions
- **Relatedness**: Personal narrative about MY sect and MY disciple

---

## 1. Data Structures

### 1.1 Recap (Python)

```python
@dataclass
class RecapSection:
    kind: str              # "sect", "disciple", "world", "opportunity"
    title: str             # e.g. "Your Sect"
    items: list[str]       # Bullet points / narrative lines
    is_major: bool         # Whether to highlight visually

@dataclass
class PlayerRecap:
    viewer_id: str
    period_from: int       # MonthStamp
    period_to: int         # MonthStamp
    sect_status: dict      # Current sect state snapshot
    disciple_status: dict  # Main disciple state snapshot
    sections: list[RecapSection]
    action_points: int     # Fate points available this cycle
    pending_opportunities: list[dict]  # e.g. gatherings, wars, decisions
    recap_text: str        # LLM-enhanced narrative (Tier A / premium only)
    generated_at: float    # Unix timestamp
```

### 1.2 Frontend DTO (TypeScript)

```typescript
interface RecapSection {
  kind: 'sect' | 'disciple' | 'world' | 'opportunity';
  title: string;
  items: string[];
  isMajor: boolean;
}

interface PlayerRecap {
  viewerId: string;
  periodFrom: number;
  periodTo: number;
  sectStatus: Record<string, any>;
  discipleStatus: Record<string, any>;
  sections: RecapSection[];
  actionPoints: number;
  pendingOpportunities: Record<string, any>[];
  recapText?: string;  // LLM narrative, may be null
  generatedAt: number;
}
```

---

## 2. Implementation Order

### Phase 1: EventStorage Extensions (Foundation)

**Files to modify:**
- `src/classes/event_storage.py`

**New methods:**

```python
def get_events_by_month(self, month_stamp: int) -> list[Event]:
    """Get all events for a specific month."""

def get_events_in_range(self, from_month: int, to_month: int) -> list[Event]:
    """Get events in [from_month, to_month] inclusive, time-ascending."""

def get_events_for_sect(
    self, sect_id: int, from_month: int, to_month: int
) -> list[Event]:
    """Get events related to a sect in a month range."""

def get_events_for_avatars_in_range(
    self, avatar_ids: list[str], from_month: int, to_month: int
) -> list[Event]:
    """Get events related to any of the given avatars in a month range."""
```

**Database index to add:**
```sql
-- Already exists: idx_events_month_stamp ON events(month_stamp DESC)
-- Add composite for sect+month range queries:
CREATE INDEX IF NOT EXISTS idx_event_sects_sect_month
    ON event_sects(sect_id, event_id);
```

---

### Phase 2: RecapService (Core Logic)

**File to create:**
- `src/services/recap_service.py`

**Responsibilities:**
1. Query events for viewer's sect and main disciple in a month range
2. Classify events into sections (sect, disciple, world, opportunity)
3. Summarize routine events (group similar events, count occurrences)
4. Highlight major events (keep full text)
5. Optionally generate LLM-enhanced narrative (tier-gated)

**Key method:**

```python
class RecapService:
    async def generate_recap(
        self,
        *,
        viewer_id: str,
        world,
        from_month: int,
        to_month: int,
        is_premium: bool = False,
    ) -> PlayerRecap:
        ...
```

**Internal flow:**

```
1. Resolve viewer's sect_id and main_avatar_id from world
2. Query events for sect in [from_month, to_month]
3. Query events for main_avatar in [from_month, to_month]
4. Query major world events in range (is_major=True)
5. Classify into sections:
   - Sect: member changes, battles, decisions, stone income
   - Disciple: cultivation progress, relationships, actions taken
   - World: wars, phenomena, dynasty changes, gatherings
   - Opportunities: upcoming gatherings, pending decisions
6. Summarize routine events (e.g. "3 disciples broke through this period")
7. If is_premium: call LLM to generate narrative summary
8. Compute action points from CONFIG
9. Return PlayerRecap
```

**Summarization strategy (non-LLM, Phase 1):**
- Group events by `event_type`
- For types with > N occurrences, produce a count summary
- Keep all `is_major=True` events verbatim
- Keep most recent N events verbatim

**LLM narrative (Tier A, Phase 1 optional):**
- Reuse existing `StoryTeller` or `LLMClient` infrastructure
- Prompt: "Summarize these events as a short narrative from the player's perspective"
- Gate behind `is_premium` flag (from room_registry billing status)

---

### Phase 3: Player Session State

**Files to modify:**
- `src/server/runtime/session.py` — add recap tracking fields
- `src/server/runtime/room_registry.py` — track last_recap_month per viewer

**New state on `GameSessionRuntime`:**

```python
# In _state dict:
"viewer_recap_state": {
    "viewer_id": {
        "last_recap_month": int,   # MonthStamp when recap was last generated
        "last_acknowledge_month": int,  # MonthStamp when player acknowledged
        "action_points_remaining": int,
    }
}
```

**Or better:** persist to `world.player_profiles[viewer_id]`:

```python
# Extend player_profiles entries:
{
    "viewer_id": "...",
    "display_name": "...",
    "joined_month": 0,
    "last_seen_month": 0,
    "last_recap_month": -1,     # NEW
    "last_acknowledge_month": -1,  # NEW
    "action_points_remaining": 3,  # NEW
}
```

---

### Phase 4: API Endpoints

**Files to modify:**
- `src/server/api/public_v1/query.py` — add recap query route
- `src/server/api/public_v1/command.py` — add acknowledge + act routes
- `src/server/public_query_builders.py` — add `build_recap` builder
- `src/server/command_handlers.py` — add `run_acknowledge_recap`, `run_spend_fate_point`

#### 4.1 GET `/api/v1/query/recap`

```python
@router.get("/api/v1/query/recap")
def get_recap_v1(
    request: Request,
    viewer_id: str = Query(default=None),
):
    # Resolve viewer_id
    # Get world, current month, last_recap_month
    # Call RecapService.generate_recap
    # Return ok_response(recap_dict)
```

**Query params:**
- `viewer_id`: player identifier
- Optional `from_month` / `to_month` override (default: last_acknowledge_month → current_month)

#### 4.2 POST `/api/v1/command/acknowledge-recap`

```python
@router.post("/api/v1/command/acknowledge-recap")
def acknowledge_recap_v1(request: Request, req: AcknowledgeRecapRequest):
    # Mark recap as read
    # Update last_acknowledge_month = current_month
    # Refresh action_points_remaining to max
    # Return ok_response({ action_points: N })
```

#### 4.3 POST `/api/v1/command/spend-fate-point`

```python
@router.post("/api/v1/command/spend-fate-point")
def spend_fate_point_v1(request: Request, req: SpendFatePointRequest):
    # Check action_points_remaining > 0
    # Execute the command (set_directive, intervene, etc.)
    # Decrement action_points_remaining
    # Return ok_response({ remaining: N, result: ... })
```

**Request body:**
```python
class SpendFatePointRequest(BaseModel):
    command: str  # e.g. "set_sect_directive", "set_long_term_objective"
    payload: dict  # Command-specific args
    viewer_id: str | None = None
```

**Alternative (simpler for Phase 1):** Don't create a new endpoint; instead
track fate point consumption in existing command handlers by adding a
`viewer_id`-aware middleware or decorator that checks/deducts points.

**Recommendation for Phase 1:** Keep it simple — acknowledge_recap resets
points, and existing commands implicitly cost 1 point. Add a query endpoint
for remaining points.

#### 4.4 GET `/api/v1/query/player/state`

```python
@router.get("/api/v1/query/player/state")
def get_player_state_v1(request: Request, viewer_id: str = Query(default=None)):
    # Return viewer's profile + action_points + recap readiness
    return ok_response({
        "viewer_id": "...",
        "display_name": "...",
        "action_points_remaining": 3,
        "action_points_max": 3,
        "last_recap_month": 120,
        "current_world_month": 132,
        "has_unread_recap": True,
        "owned_sect_id": 1,
        "main_avatar_id": "abc123",
    })
```

---

### Phase 5: Frontend Changes

**Files to create:**
- `web/src/components/game/panels/RecapOverlay.vue` — Full-screen recap modal
- `web/src/components/game/panels/RecapSection.vue` — Individual section component
- `web/src/components/game/panels/ActionPointsBar.vue` — Fate points display

**Files to modify:**
- `web/src/api/modules/system.ts` — Add recap API calls
- `web/src/types/api.ts` — Add Recap DTOs
- `web/src/stores/system.ts` — Add recap state
- `web/src/App.vue` — Show recap overlay on session start
- `web/src/composables/useAppShell.ts` — Integrate recap into startup flow

#### 5.1 RecapOverlay Component

Layout:

```
┌──────────────────────────────────────────────┐
│              RECAP OVERLAY                     │
├──────────────────────────────────────────────┤
│  📅 Month 120 → Month 132                     │
│                                              │
│  ┌─ Your Sect ────────────────────────────┐  │
│  │  ⚔️  Sect won battle against X          │  │
│  │  👤 2 new disciples joined              │  │
│  │  💰 +340 magic stones this period       │  │
│  └─────────────────────────────────────────┘  │
│                                              │
│  ┌─ Your Disciple ────────────────────────┐  │
│  │  📈 Advanced to Foundation Est.         │  │
│  │  💕 Formed bond with Li Wei             │  │
│  └─────────────────────────────────────────┘  │
│                                              │
│  ┌─ World Events ─────────────────────────┐  │
│  │  🌍 New celestial phenomenon appeared   │  │
│  │  ⚔️  War declared between Sect A & B    │  │
│  └─────────────────────────────────────────┘  │
│                                              │
│  ┌─ Opportunities ────────────────────────┐  │
│  │  🎪 Gathering: Heavenly Dao Conference  │  │
│  │  📋 Sect decision pending               │  │
│  └─────────────────────────────────────────┘  │
│                                              │
│  ┌──────────────────────────────────────────┐ │
│  │     [ I understand, let's act ]          │  │
│  └──────────────────────────────────────────┘ │
│                                              │
│  ⭐ Fate Points: ● ● ● ○ ○                   │
└──────────────────────────────────────────────┘
```

#### 5.2 Integration with App Shell

```typescript
// In useAppShell.ts or a new composable:
// On scene === 'game' and world ready:
//   1. GET /api/v1/query/player/state
//   2. If has_unread_recap: show RecapOverlay
//   3. On acknowledge: hide overlay, show action points bar
//   4. Show main game UI with action-aware controls
```

#### 5.3 Action Points Display

Add to the status bar or a small floating bar:

```
⭐ 3/5
```

Clicking opens a mini-panel showing what actions cost points and which are free.

---

### Phase 6: Configuration

**File to modify:**
- `static/config.yml`

**New config section:**

```yaml
game:
  recap:
    enabled: true
    action_points_max: 3
    # Months between auto-recap triggers (0 = always show on return)
    min_months_between_recaps: 1
    # LLM narrative (requires premium / Tier A)
    llm_narrative_enabled: false
    # Summarization thresholds
    routine_group_threshold: 3  # Group if > N similar events
    keep_recent_verbatim: 5     # Always show last N events verbatim
```

---

## 3. File Creation / Modification Summary

### New Files

| # | File | Purpose |
|---|------|---------|
| 1 | `src/services/recap_service.py` | Core recap generation service |
| 2 | `web/src/components/game/panels/RecapOverlay.vue` | Recap modal UI |
| 3 | `web/src/components/game/panels/RecapSection.vue` | Individual section card |
| 4 | `web/src/components/game/panels/ActionPointsBar.vue` | Fate points HUD |

### Modified Files

| # | File | Change |
|---|------|--------|
| 1 | `src/classes/event_storage.py` | Add month-range query methods + index |
| 2 | `src/server/runtime/session.py` | Add recap state helpers (optional) |
| 3 | `src/server/api/public_v1/query.py` | Add `/recap` and `/player/state` routes |
| 4 | `src/server/api/public_v1/command.py` | Add `/acknowledge-recap` route + DTOs |
| 5 | `src/server/public_query_builders.py` | Add recap + player state builders |
| 6 | `src/server/command_handlers.py` | Add acknowledge_recap handler |
| 7 | `src/server/main.py` | Wire recap service into composition root |
| 8 | `web/src/api/modules/system.ts` | Add recap API functions |
| 9 | `web/src/types/api.ts` | Add Recap DTOs |
| 10 | `web/src/stores/system.ts` | Add recap state management |
| 11 | `web/src/App.vue` | Integrate recap overlay into startup flow |
| 12 | `static/config.yml` | Add recap config section |

---

## 4. Execution Order (Dependency Graph)

```
Step 1: EventStorage extensions      ← No dependencies
Step 2: RecapService                  ← Depends on Step 1
Step 3: Config                        ← Independent, but do early
Step 4: Player profile state          ← Depends on config
Step 5: API endpoints (query + cmd)   ← Depends on Steps 2, 3, 4
Step 6: Wire into main.py             ← Depends on Step 5
Step 7: Frontend types + API module   ← Depends on Step 5
Step 8: Frontend components           ← Depends on Step 7
Step 9: App shell integration         ← Depends on Step 8
Step 10: Tests                        ← Depends on Steps 1-6
```

---

## 5. Testing Strategy

### Backend

- `tests/test_recap_service.py`
  - Test event classification into sections
  - Test summarization of routine events
  - Test major event highlighting
  - Test LLM narrative gating
  - Test empty recap when no events

- `tests/test_event_storage_month.py`
  - Test `get_events_by_month`
  - Test `get_events_in_range`
  - Test `get_events_for_sect`

- `tests/test_api_recap.py`
  - Test GET `/api/v1/query/recap` returns correct structure
  - Test POST `/api/v1/command/acknowledge-recap` updates state
  - Test GET `/api/v1/query/player/state` returns action points

### Frontend

- `web/src/components/game/panels/__tests__/RecapOverlay.spec.ts`
  - Renders sections correctly
  - Shows/hides based on recap state
  - Acknowledge button triggers API call

---

## 6. Future Phases (Out of Scope for Phase 1)

| Phase | Feature |
|-------|---------|
| Phase 2 | LLM-enhanced narrative summaries |
| Phase 2 | Action point costs per command type |
| Phase 3 | Consequence preview ("If you do X, Y might happen") |
| Phase 3 | Recap sharing (export as image/text) |
| Phase 4 | Multi-player shared recap (world room) |
| Phase 4 | Recap timeline view (scrollable history) |

---

## 7. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Recap generation is slow (many events) | Paginate event queries; cap at N events per section |
| LLM narrative adds latency | Gate behind `is_premium`; fallback to rule-based summary |
| Frontend overlay blocks gameplay | Make it dismissible; show "skip recap" option |
| Action points feel too restrictive | Start generous (5-6), tune down based on telemetry |
| Existing commands don't deduct points | Phase 1: points are informational; Phase 2: enforce |
