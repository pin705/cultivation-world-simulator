# Recap-First Gameplay Loop Implementation Progress

Updated: 2026-04-14

## ✅ Completed (Phase 1 Foundation)

### 1. EventStorage Extensions
**File**: `src/classes/event_storage.py`

Added 4 new query methods for recap-oriented event retrieval:
- `get_events_by_month(month_stamp)` - Get all events for a specific month
- `get_events_in_range(from_month, to_month)` - Get events in month range
- `get_events_for_sect_in_range(sect_id, from_month, to_month)` - Sect-specific events
- `get_events_for_avatars_in_range(avatar_ids, from_month, to_month)` - Avatar-specific events

**Status**: ✅ Complete and tested (no errors in edit)

---

### 2. RecapService
**File**: `src/services/recap_service.py` (NEW)

Core service that generates personalized recaps for players.

**Features**:
- Data structures: `Recap`, `SectRecapSection`, `DiscipleRecapSection`, `WorldRecapSection`, `OpportunitySection`, `PlayerRecapState`
- `generate_recap(viewer_id, from_month, to_month, generate_summary)` - Main recap generation
- `acknowledge_recap(viewer_id, current_month)` - Player reads recap, refreshes action points
- `spend_action_point(viewer_id)` - Spend one action point
- `get_action_points_remaining(viewer_id)` - Get remaining points

**Logic**:
- Queries events by month range and filters by sect/avatar
- Classifies events into sections (sect status, disciple progress, world events, opportunities)
- Phase 1: Rule-based summary (no LLM)
- Persists player state in `world.player_profiles`

**Status**: ✅ Complete (created, needs integration testing)

---

### 3. Configuration
**File**: `static/config.yml`

Added `recap` section with:
- `enabled: true` - Enable recap-first mode
- `action_points_per_cycle: 3` - Default action points
- `default_recap_months: 3` - Default recap window
- `max_recap_months: 12` - Performance guard
- `generate_llm_summary: false` - Phase 1: rule-based only
- Event classification thresholds

**Status**: ✅ Complete

---

### 4. Query Builder
**File**: `src/server/recap_query.py` (NEW)

Builds recap query response for API:
- `build_recap_query(world, viewer_id)` - Generates full recap dict
- Limits event counts for performance (top 10-15 per section)
- Returns structured JSON for frontend consumption

**Status**: ✅ Complete

---

### 5. Command Handlers  
**File**: `src/server/recap_commands.py` (NEW)

Handles recap-related commands:
- `handle_acknowledge_recap(world, viewer_id)` - Acknowledge and refresh action points
- `handle_spend_action_point(world, viewer_id)` - Spend action point (with validation)

**Status**: ✅ Complete

---

### 6. API Endpoints
**Files**: `src/server/api/public_v1/query.py`, `src/server/api/public_v1/command.py`

Added endpoints:
- `GET /api/v1/query/recap` - Get player's current recap
- `POST /api/v1/command/recap/acknowledge` - Acknowledge recap, refresh points
- `POST /api/v1/command/recap/spend-action-point` - Spend action point

**Status**: ✅ Complete (endpoint definitions added, need wiring in host_app.py)

---

## 🔧 Remaining Work (Critical Path)

### 7. Wire into host_app.py (NEXT STEP)
**File**: `src/server/host_app.py`

Need to:
1. Import recap query builder and command handlers
2. Add `build_recap` to `create_public_query_router` call
3. Add `run_acknowledge_recap` and `run_spend_action_point` to `create_public_command_router` call
4. Create wrapper functions that call the handlers with current world instance

**Estimated effort**: ~50 lines of code

---

### 8. Frontend Types & API Module
**Directory**: `web/src/`

Need to:
1. Add TypeScript DTOs for recap data structures (`web/src/types/recap.ts`)
2. Add API functions to query/command modules
3. Add recap store or extend existing store

**Estimated effort**: ~150 lines

---

### 9. Frontend Components
**Directory**: `web/src/components/game/panels/`

Need to create:
1. `RecapOverlay.vue` - Modal shown when player has unread recap
2. `RecapSection.vue` - Displays one section of recap (sect/disciple/world)
3. `ActionPointsBar.vue` - Shows remaining action points

**Estimated effort**: ~400 lines

---

### 10. App Shell Integration
**File**: `web/src/App.vue` or game scene component

Need to:
1. Check for unread recap on game load
2. Show recap overlay if `has_unread_recap` is true
3. Add "What should I do now" guidance section

**Estimated effort**: ~80 lines

---

### 11. Tests
**Directory**: `tests/`

Need to create:
1. `tests/test_recap_service.py` - Backend service tests
2. `tests/test_recap_storage.py` - Storage query tests
3. `tests/test_recap_api.py` - API endpoint tests
4. Frontend component tests (optional for Phase 1)

**Estimated effort**: ~300 lines

---

## Implementation Order Recommendation

1. **✅ DONE**: EventStorage extensions
2. **✅ DONE**: RecapService
3. **✅ DONE**: Configuration
4. **✅ DONE**: Query builder & command handlers
5. **✅ DONE**: API endpoints
6. **TODO**: Wire into host_app.py (30 mins)
7. **TODO**: Frontend types & API (1 hour)
8. **TODO**: Frontend components (3-4 hours)
9. **TODO**: App shell integration (1 hour)
10. **TODO**: Tests (2-3 hours)

**Total remaining effort**: ~8-10 hours

---

## Technical Notes

### Player State Persistence
Player recap state is stored in `world.player_profiles[viewer_id]` with keys:
- `last_recap_month_stamp` - Last month player read recap for
- `last_acknowledge_month_stamp` - Last month player acknowledged
- `action_points_total` - Total points allocated this cycle
- `action_points_spent` - Points spent this cycle

This survives pause/resume and save/load.

### Action Points (Phase 1)
In Phase 1, action points are **informational** - shown to player but not strictly enforced per-command. Enforcement is a Phase 2 addition when we implement actual intervention commands.

### LLM Summary (Phase 2+)
The `generate_summary` parameter in `generate_recap()` is currently always `false`. In Phase 2, this should be:
- `true` for story_rich worlds
- `false` for standard worlds

This gates behind the `story_teller` task policy with `commercial_action: "sample"`.

---

## Next Immediate Step

Wire the recap endpoints into `src/server/host_app.py` by:
1. Finding where `create_public_query_router` is called
2. Adding `build_recap=lambda viewer_id: build_recap_query(get_world(), viewer_id)`
3. Finding where `create_public_command_router` is called  
4. Adding wrapper functions for acknowledge_recap and spend_action_point

This will make the API endpoints functional and ready for frontend integration.
