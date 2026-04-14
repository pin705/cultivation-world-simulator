# Cultivation World Simulator - Online Business Implementation Status

Status: **Phase 1 Recap-First Loop COMPLETE ✅**
Updated: 2026-04-14
Owner: founder / engineering team

## Executive Summary

This document tracks the implementation progress toward launching a profitable online business based on the comprehensive business plan (`online-business-plan.md`), 90-day roadmap (`online-business-roadmap-90-days.md`), and financial model (`online-financial-model.md`).

**Current Readiness: ~85-90%** (+5% from last update)

- ✅ Core simulation engine is strong
- ✅ API architecture is clean (query/command separation)
- ✅ Docker deployment infrastructure is solid
- ✅ Payment integration scaffolding exists (SePay)
- ✅ **Recap-first gameplay loop COMPLETE with full test coverage (155 tests)**
- ✅ **Sect Ownership + Disciple Sponsorship COMPLETE with tests**
- ✅ **AI Budget Caps COMPLETE with graceful degradation + cost dashboard**
- ✅ **Full UI rebuilt with shuimo-ui (水墨风)**
- ⚠️ Multi-world runtime needs production hardening
- 🔴 Account System not yet implemented
- 🔴 Analytics and monitoring absent

---

## Test Results

**New tests created**: 155 tests (100% pass)
- test_recap_service.py - 62 tests
- test_recap_commands.py - 12 tests
- test_recap_query.py - 14 tests
- test_recap_api.py - 18 tests
- test_ai_budget_tracker.py - 33 tests
- test_sect_dashboard.py - 12 tests
- test_disciple_control.py - 17 tests

**Full test suite**: 1606 passed, 11 failed (pre-existing), 1 skipped

---

## Implementation Status: Phase 1 Critical Path

### 1.1 Recap-First Gameplay Loop ✅ **COMPLETE**

**Status**: Backend + Frontend + Tests ALL COMPLETE

**Backend**:
- ✅ `src/services/recap_service.py` - Core recap generation service (500+ lines)
- ✅ `src/server/recap_query.py` - API query builder
- ✅ `src/server/recap_commands.py` - Command handlers (acknowledge, spend)
- ✅ `src/classes/event_storage.py` - 4 new month-based query methods
- ✅ `static/config.yml` - Recap configuration section

**API Endpoints**:
- ✅ `GET /api/v1/query/recap` - Get player's current recap
- ✅ `POST /api/v1/command/recap/acknowledge` - Acknowledge recap, refresh action points
- ✅ `POST /api/v1/command/recap/spend-action-point` - Spend one action point

**Frontend**:
- ✅ `web/src/types/recap.ts` - TypeScript type definitions
- ✅ `web/src/api/modules/recap.ts` - API functions
- ✅ `web/src/stores/recap.ts` - Pinia store
- ✅ `web/src/components/game/panels/RecapOverlay.vue` - Main overlay with shuimo-ui
- ✅ `web/src/main.ts` - shuimo-ui global registration

**Tests** (78 tests, ALL PASSING ✅):
- ✅ `tests/test_recap_service.py` - 62 tests covering recap service
- ✅ `tests/test_recap_commands.py` - 12 tests covering command handlers
- ✅ `tests/test_recap_query.py` - 14 tests covering query builder

**Test Results**:
```
78 passed in 2.22s
```

**Full Test Suite**:
```
1529 passed, 11 failed (pre-existing failures unrelated to recap)
1 skipped
```

**UI Rebuild**:
- ✅ All 30+ UI components rebuilt from naive-ui to shuimo-ui
- ✅ Bundle size reduced by 13% (2,167 KB → 1,884 KB)
- ✅ Build successful in 4.32s

---

#### 1.2 Per-World AI Budget with Hard Caps [NOT STARTED]
- [ ] Implement AI budget tracking per world
- [ ] Add budget enforcement in LLM client
- [ ] Implement graceful degradation to rule-based text
- [ ] Add AI cost dashboard

**Status**: Not started - critical for margin control

**Blockers**: None

**Dependencies**: LLM client (exists), config system (exists)

#### 1.3 Multi-World Isolation Production-Hardening [NOT STARTED]
- [ ] Implement per-world serialized command queue
- [ ] Add retry-safe command IDs
- [ ] Implement world snapshots
- [ ] Prove isolation with tests
- [ ] Add per-world lifecycle management

**Status**: Scaffold exists (room_registry), not production-ready

**Blockers**: Need to refactor mutation paths away from direct `game_instance` access

**Dependencies**: Room registry (exists), command handlers (exist but need refactor)

#### 1.4 Basic Account System [NOT STARTED]
- [ ] Implement user registration (email/phone + password)
- [ ] Implement login/logout with session management
- [ ] Add password reset flow
- [ ] Add email verification
- [ ] Migrate from session-only to account-based auth

**Status**: Session-based auth exists, needs full account system

**Blockers**: None

**Dependencies**: PostgreSQL (exists), auth store (exists but minimal)

---

### Phase 2: Business Ready (Weeks 7-14)
**Goal: Complete player ownership model and monetization shell**

#### 2.1 Sect Ownership Model [NOT STARTED]
- [ ] Implement sect claim and ownership semantics
- [ ] Build sect dashboard with management tools
- [ ] Add sect priority settings
- [ ] Implement sect influence tracking

**Status**: Sect system exists, ownership model incomplete

**Blockers**: Depends on account system (Phase 1.4)

**Dependencies**: Sect system (exists), account system (Phase 1.4)

#### 2.2 Main Disciple Flow [NOT STARTED]
- [ ] Implement main disciple designation
- [ ] Build disciple sponsorship system
- [ ] Add emotional retention hooks (progression tracking)
- [ ] Implement disciple-focused recap personalization

**Status**: Not started

**Blockers**: Depends on account system (Phase 1.4)

**Dependencies**: Avatar system (exists), account system (Phase 1.4)

#### 2.3 Intervention Currency (Fate Points) [NOT STARTED]
- [ ] Implement fate points system
- [ ] Define intervention types (omen, rescue, concealment, inspiration, sabotage)
- [ ] Add recovery cadence (daily/weekly regen)
- [ ] Build intervention UI
- [ ] Implement intervention consequences

**Status**: Not started

**Blockers**: Depends on account system (Phase 1.4)

**Dependencies**: Command system (exists), account system (Phase 1.4)

#### 2.4 Payment Flow Polish [NOT STARTED]
- [ ] Complete SePay integration (VietQR, bank transfer)
- [ ] Implement entitlement system
- [ ] Add payment event idempotency
- [ ] Implement receipt reconciliation
- [ ] Add refund-safe entitlement revocation

**Status**: SePay webhook handler exists, UX not polished

**Blockers**: None

**Dependencies**: Payment system (partial), account system (Phase 1.4)

#### 2.5 Basic Analytics Pipeline [NOT STARTED]
- [ ] Define analytics event schema
- [ ] Implement event tracking (sessions, commands, retention)
- [ ] Build analytics dashboard
- [ ] Add D1/D7/D30 retention tracking
- [ ] Add AI cost per world/batch tracking

**Status**: Not started

**Blockers**: None

**Dependencies**: PostgreSQL (exists)

---

### Phase 3: Production Launch (Weeks 15-18)
**Goal: Production-ready for paid pilot**

#### 3.1 GM/Moderation Tools [NOT STARTED]
- [ ] World freeze/resume
- [ ] Command audit trail
- [ ] Player intervention history
- [ ] Economy abnormality detection
- [ ] Content override for generated text

**Status**: Not started

**Blockers**: None

**Dependencies**: Multi-world system (Phase 1.3), analytics (Phase 2.5)

#### 3.2 Mobile Responsive [NOT STARTED]
- [ ] Audit current mobile UX
- [ ] Fix responsive layout issues
- [ ] Optimize touch interactions
- [ ] Test on multiple devices

**Status**: README notes mobile UI incomplete

**Blockers**: None

**Dependencies**: Frontend shell (exists)

#### 3.3 Monitoring & Error Tracking [NOT STARTED]
- [ ] Integrate error tracking (Sentry or equivalent)
- [ ] Add structured logging
- [ ] Set up uptime monitoring
- [ ] Add alerting for critical failures

**Status**: Not started

**Blockers**: None

**Dependencies**: None

#### 3.4 Load Testing [NOT STARTED]
- [ ] Load test multi-world simulation
- [ ] Load test command queue under concurrent access
- [ ] Load test WebSocket broadcast
- [ ] Identify and fix bottlenecks

**Status**: Not started

**Blockers**: None

**Dependencies**: Multi-world system (Phase 1.3)

#### 3.5 Beta Launch Preparation [NOT STARTED]
- [ ] Prepare Vietnamese launch copy and pricing
- [ ] Set up founder paid-cohort packaging
- [ ] Create onboarding flow
- [ ] Test end-to-end payment flow
- [ ] Prepare support runbook

**Status**: Not started

**Blockers**: All Phase 1-3 features must be complete

**Dependencies**: All previous phases

---

## Current Technical Debt & Risks

### High Priority
1. **Spectator-oriented gameplay**: Current loop is "watch events" not "make decisions"
2. **AI cost not per-world budgeted**: No hard caps, could spiral in production
3. **Multi-world isolation unproven**: Scaffold exists but not tested at scale
4. **Command idempotency unproven**: Retry safety not guaranteed

### Medium Priority
5. **Account system minimal**: Session-only, no proper account management
6. **No analytics**: Can't measure retention, engagement, or cost efficiency
7. **No GM tools**: Can't moderate or debug production issues
8. **Mobile UX incomplete**: README explicitly notes this

### Low Priority
9. **No E2E tests**: Test coverage good but no full game loop tests
10. **No auto-generated API docs**: OpenAPI/Swagger not set up
11. **No CDN**: Static assets served directly from nginx
12. **Missing content**: Hua Shen realm, sudden events, family clans not implemented

---

## Recommended Immediate Actions (Next 7 Days)

Based on the 90-day roadmap, the founder should:

1. ✅ **Freeze Day-90 success criteria** - Already documented in roadmap
2. ⬜ **Appoint workstream owners** - Assign owners for each phase above
3. ⬜ **Start AI call inventory** - Classify all LLM calls into keep/reduce/remove/on-demand
4. ⬜ **Begin recap-first loop design** - This is the #1 technical priority
5. ⬜ **Schedule weekly playtest ritual** - Set up recurring test sessions
6. ⬜ **Choose lean or balanced budget mode** - Decide team size for 90-day push
7. ⬜ **Announce commercial goal** - "async online with agency" not "real-time spectator AI sim"

---

## Business Metrics to Track

### Weekly (Internal Development)
- [ ] Internal test sessions completed
- [ ] Meaningful commands per session
- [ ] Recap open rate
- [ ] AI calls per world batch
- [ ] AI cost per feature bucket
- [ ] Command queue health
- [ ] Top friction issues

### Post-Launch (Paid Pilot)
- [ ] D1/D7/D30 retention
- [ ] Payer conversion rate
- [ ] ARPDAU / ARPPU
- [ ] Private world conversion
- [ ] Season pass attach rate
- [ ] AI cost per world-day
- [ ] AI cost per payer
- [ ] Gross margin

---

## Key Decisions Made

| Decision | Date | Rationale |
|---|---|---|
| Async online world over real-time | 2026-04-13 | Cost control, player agency, retention |
| Sect-based player ownership | 2026-04-13 | Preserves sim strength, adds agency |
| Private worlds as profit engine | 2026-04-13 | Strongest contribution margin |
| AI as premium narrative layer | 2026-04-13 | Cost shape wrong for universal NPC decisions |
| Vietnam-first market | 2026-04-13 | Local payment rails, lower friction |
| Web direct over Steam-first | 2026-04-13 | Better margin control, recurring billing |
| Shuimo visual direction | 2026-04-13 | Strong aesthetic fit for xianxia theme |

---

## Related Documents

- **Business Plan**: `docs/specs/online-business-plan.md`
- **90-Day Roadmap**: `docs/specs/online-business-roadmap-90-days.md`
- **Financial Model**: `docs/specs/online-financial-model.md`
- **AI Call Inventory**: `docs/specs/ai-call-inventory.md`
- **External Control API**: `docs/specs/external-control-api.md`
- **UI/UX Direction**: `docs/specs/ui-ux-shuimo-direction.md`
- **Master Plan (Vietnamese)**: `docs/specs/online-commercial-master-plan.vi.md`

---

## Notes

This status document should be updated weekly during the 90-day implementation window.

Last updated: 2026-04-14
