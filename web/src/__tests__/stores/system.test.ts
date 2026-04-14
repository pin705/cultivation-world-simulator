import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { InitStatusDTO } from '@/types/api'

// Mock the API module.
vi.mock('@/api', () => ({
  systemApi: {
    fetchInitStatus: vi.fn(),
    switchControlSeat: vi.fn(),
    releaseControlSeat: vi.fn(),
    updatePlayerProfile: vi.fn(),
    switchWorldRoom: vi.fn(),
    updateWorldRoomAccess: vi.fn(),
    updateWorldRoomPlan: vi.fn(),
    updateWorldRoomEntitlement: vi.fn(),
    createWorldRoomPaymentOrder: vi.fn(),
    settleWorldRoomPayment: vi.fn(),
    reconcileWorldRoomPayment: vi.fn(),
    addWorldRoomMember: vi.fn(),
    removeWorldRoomMember: vi.fn(),
    rotateWorldRoomInvite: vi.fn(),
    joinWorldRoomByInvite: vi.fn(),
    pauseGame: vi.fn(),
    resumeGame: vi.fn(),
  },
}))

const worldStoreMock = {
  reset: vi.fn(),
  initialize: vi.fn().mockResolvedValue(undefined),
}

vi.mock('@/stores/world', () => ({
  useWorldStore: () => worldStoreMock,
}))

import { systemApi } from '@/api'
import { useSystemStore } from '@/stores/system'

const createMockStatus = (overrides: Partial<InitStatusDTO> = {}): InitStatusDTO => ({
  status: 'idle',
  phase: 0,
  phase_name: '',
  progress: 0,
  elapsed_seconds: 0,
  error: null,
  llm_check_failed: false,
  llm_error_message: '',
  ...overrides,
})

describe('useSystemStore', () => {
  let store: ReturnType<typeof useSystemStore>

  beforeEach(() => {
    window.localStorage.clear()
    window.localStorage.setItem('cws_viewer_id', 'viewer_test')
    vi.clearAllMocks()
    store = useSystemStore()
    worldStoreMock.reset.mockReset()
    worldStoreMock.initialize.mockReset()
    worldStoreMock.initialize.mockResolvedValue(undefined)
  })

  describe('initial state', () => {
    it('should have correct initial values', () => {
      expect(store.initStatus).toBeNull()
      expect(store.isInitialized).toBe(false)
      expect(store.isManualPaused).toBe(true)
      expect(store.isGameRunning).toBe(false)
    })
  })

  describe('isLoading', () => {
    it('should return true when initStatus is null', () => {
      expect(store.isLoading).toBe(true)
    })

    it('should return false when status is idle', () => {
      store.initStatus = createMockStatus({ status: 'idle', progress: 0 })
      expect(store.isLoading).toBe(false)
    })

    it('should return true when status is in_progress', () => {
      store.initStatus = createMockStatus({ status: 'in_progress', progress: 50 })
      expect(store.isLoading).toBe(true)
    })

    it('should return false when status is ready and initialized', () => {
      store.initStatus = createMockStatus({ status: 'ready', progress: 100 })
      store.setInitialized(true)
      expect(store.isLoading).toBe(false)
    })

    it('should return true when status is error', () => {
      store.initStatus = createMockStatus({ status: 'error' as any, progress: 0 })
      expect(store.isLoading).toBe(true)
    })
  })

  describe('isReady', () => {
    it('should return false when not initialized', () => {
      store.initStatus = createMockStatus({ status: 'ready', progress: 100 })
      expect(store.isReady).toBe(false)
    })

    it('should return true when status is ready and initialized', () => {
      store.initStatus = createMockStatus({ status: 'ready', progress: 100 })
      store.setInitialized(true)
      expect(store.isReady).toBe(true)
    })
  })

  describe('togglePause', () => {
    it('should toggle from paused to playing and call resumeGame', async () => {
      store.isManualPaused = true
      vi.mocked(systemApi.resumeGame).mockResolvedValue(undefined)

      await store.togglePause()

      expect(store.isManualPaused).toBe(false)
      expect(systemApi.resumeGame).toHaveBeenCalled()
    })

    it('should toggle from playing to paused and call pauseGame', async () => {
      store.isManualPaused = false
      vi.mocked(systemApi.pauseGame).mockResolvedValue(undefined)

      await store.togglePause()

      expect(store.isManualPaused).toBe(true)
      expect(systemApi.pauseGame).toHaveBeenCalled()
    })

    it('should rollback state on API failure', async () => {
      store.isManualPaused = true
      vi.mocked(systemApi.resumeGame).mockRejectedValue(new Error('API error'))

      await store.togglePause()

      // Should rollback to original state.
      expect(store.isManualPaused).toBe(true)
    })
  })

  describe('setInitialized', () => {
    it('should set isInitialized value', () => {
      store.setInitialized(true)
      expect(store.isInitialized).toBe(true)

      store.setInitialized(false)
      expect(store.isInitialized).toBe(false)
    })
  })

  describe('fetchInitStatus', () => {
    it('should update initStatus on success', async () => {
      const mockStatus = createMockStatus({ status: 'ready', progress: 100, active_controller_id: 'local', player_control_seat_ids: ['local'] })
      vi.mocked(systemApi.fetchInitStatus).mockResolvedValue(mockStatus)

      const result = await store.fetchInitStatus()

      expect(result).toEqual(mockStatus)
      expect(store.initStatus).toEqual(mockStatus)
      expect(systemApi.fetchInitStatus).toHaveBeenCalledWith('viewer_test')
    })

    it('should set isGameRunning to true when status is ready', async () => {
      const mockStatus = createMockStatus({ status: 'ready', progress: 100 })
      vi.mocked(systemApi.fetchInitStatus).mockResolvedValue(mockStatus)

      await store.fetchInitStatus()

      expect(store.isGameRunning).toBe(true)
    })

    it('should set isGameRunning to false when status is not ready', async () => {
      const mockStatus = createMockStatus({ status: 'in_progress', progress: 50 })
      vi.mocked(systemApi.fetchInitStatus).mockResolvedValue(mockStatus)

      await store.fetchInitStatus()

      expect(store.isGameRunning).toBe(false)
    })

    it('should return null and log error on failure', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      vi.mocked(systemApi.fetchInitStatus).mockRejectedValue(new Error('Network error'))

      const result = await store.fetchInitStatus()

      expect(result).toBeNull()
      expect(consoleSpy).toHaveBeenCalled()
      consoleSpy.mockRestore()
    })

    it('should ignore stale response when called rapidly (race condition fix)', async () => {
      // Scenario:
      // 1. fetchInitStatus() called, request R1 starts (slow, returns 'in_progress')
      // 2. fetchInitStatus() called again, request R2 starts (fast, returns 'ready')
      // 3. R2 returns first -> initStatus = 'ready', isGameRunning = true
      // 4. R1 returns later -> should be ignored (requestId mismatch)
      
      let resolveR1: (value: any) => void
      const r1Promise = new Promise(resolve => { resolveR1 = resolve })
      
      let callCount = 0
      vi.mocked(systemApi.fetchInitStatus).mockImplementation(async () => {
        callCount++
        if (callCount === 1) {
          await r1Promise
          return createMockStatus({ status: 'in_progress', progress: 50 })
        }
        return createMockStatus({ status: 'ready', progress: 100 })
      })

      // Start R1 (slow)
      const fetch1 = store.fetchInitStatus()
      
      // Start R2 (fast) - this should be the "truth"
      const result2 = await store.fetchInitStatus()
      expect(result2?.status).toBe('ready')
      expect(store.initStatus?.status).toBe('ready')
      expect(store.isGameRunning).toBe(true)
      
      // R1 completes with stale data - should be ignored
      resolveR1!(undefined)
      const result1 = await fetch1
      
      // Stale response should return null and not update state
      expect(result1).toBeNull()
      expect(store.initStatus?.status).toBe('ready') // Still fresh data
      expect(store.isGameRunning).toBe(true) // Still correct
    })

    it('should expose control seat info from runtime status', async () => {
      const mockStatus = createMockStatus({
        status: 'ready',
        progress: 100,
        active_room_id: 'guild_alpha',
        room_ids: ['main', 'guild_alpha'],
        active_room_summary: {
          id: 'guild_alpha',
          access_mode: 'private',
          owner_viewer_id: 'viewer_test',
          member_viewer_ids: ['viewer_test'],
          viewer_has_access: true,
          viewer_is_owner: true,
          is_active: true,
          status: 'ready',
        },
        room_summaries: [
          {
            id: 'main',
            access_mode: 'open',
            owner_viewer_id: null,
            member_viewer_ids: [],
            viewer_has_access: true,
            viewer_is_owner: false,
            is_active: false,
            status: 'ready',
          },
          {
            id: 'guild_alpha',
            access_mode: 'private',
            owner_viewer_id: 'viewer_test',
            member_viewer_ids: ['viewer_test'],
            viewer_has_access: true,
            viewer_is_owner: true,
            is_active: true,
            status: 'ready',
          },
        ],
        active_controller_id: 'seat_b',
        player_control_seat_ids: ['local', 'seat_b'],
        player_control_seats: [
          { id: 'local', holder_id: 'viewer_a', is_active: false },
          { id: 'seat_b', holder_id: 'viewer_test', is_active: true },
        ],
        player_profiles: [
          { viewer_id: 'viewer_a', display_name: 'Alpha', joined_month: 1200, last_seen_month: 1201, controller_id: 'local' },
          { viewer_id: 'viewer_test', display_name: 'Bon', joined_month: 1200, last_seen_month: 1201, controller_id: 'seat_b', is_active_controller: true },
        ],
        viewer_profile: { viewer_id: 'viewer_test', display_name: 'Bon', joined_month: 1200, last_seen_month: 1201, controller_id: 'seat_b', is_active_controller: true },
      })
      vi.mocked(systemApi.fetchInitStatus).mockResolvedValue(mockStatus)

      await store.fetchInitStatus()

      expect(store.activeRoomId).toBe('guild_alpha')
      expect(store.roomIds).toEqual(['main', 'guild_alpha'])
      expect(store.activeRoomSummary).toEqual(mockStatus.active_room_summary)
      expect(store.roomSummaries).toEqual(mockStatus.room_summaries)
      expect(store.activeControllerId).toBe('seat_b')
      expect(store.playerControlSeatIds).toEqual(['local', 'seat_b'])
      expect(store.playerControlSeats).toEqual(mockStatus.player_control_seats)
      expect(store.playerProfiles).toEqual(mockStatus.player_profiles)
      expect(store.viewerProfile).toEqual(mockStatus.viewer_profile)
    })
  })

  describe('switchControlSeat', () => {
    it('should call switch endpoint and refresh init status', async () => {
      vi.mocked(systemApi.switchControlSeat).mockResolvedValue({ status: 'ok' } as any)
      vi.mocked(systemApi.fetchInitStatus).mockResolvedValue(
        createMockStatus({
          status: 'ready',
          active_controller_id: 'seat_b',
          player_control_seat_ids: ['local', 'seat_b'],
        }),
      )

      const result = await store.switchControlSeat('seat_b')

      expect(systemApi.switchControlSeat).toHaveBeenCalledWith({
        controller_id: 'seat_b',
        viewer_id: 'viewer_test',
      })
      expect(systemApi.fetchInitStatus).toHaveBeenCalled()
      expect(result?.active_controller_id).toBe('seat_b')
    })
  })

  describe('releaseControlSeat', () => {
    it('should call release endpoint and refresh init status', async () => {
      vi.mocked(systemApi.releaseControlSeat).mockResolvedValue({ status: 'ok' } as any)
      vi.mocked(systemApi.fetchInitStatus).mockResolvedValue(
        createMockStatus({
          status: 'ready',
          active_controller_id: 'local',
          player_control_seat_ids: ['local', 'seat_b'],
          player_control_seats: [
            { id: 'local', holder_id: 'viewer_test', is_active: true },
            { id: 'seat_b', holder_id: null, is_active: false },
          ],
        }),
      )

      const result = await store.releaseControlSeat('local')

      expect(systemApi.releaseControlSeat).toHaveBeenCalledWith({
        controller_id: 'local',
        viewer_id: 'viewer_test',
      })
      expect(systemApi.fetchInitStatus).toHaveBeenCalled()
      expect(result?.active_controller_id).toBe('local')
    })
  })

  describe('switchWorldRoom', () => {
    it('should switch world room, refresh status, and reload world when room is ready', async () => {
      vi.mocked(systemApi.switchWorldRoom).mockResolvedValue({ status: 'ok' } as any)
      vi.mocked(systemApi.fetchInitStatus).mockResolvedValue(
        createMockStatus({
          status: 'ready',
          active_room_id: 'guild_alpha',
          room_ids: ['main', 'guild_alpha'],
        }),
      )

      const result = await store.switchWorldRoom('guild_alpha')

      expect(systemApi.switchWorldRoom).toHaveBeenCalledWith({
        room_id: 'guild_alpha',
        viewer_id: 'viewer_test',
      })
      expect(worldStoreMock.reset).toHaveBeenCalled()
      expect(worldStoreMock.initialize).toHaveBeenCalled()
      expect(store.activeRoomId).toBe('guild_alpha')
      expect(result?.active_room_id).toBe('guild_alpha')
    })

    it('should reset world and mark app uninitialized when target room is not ready', async () => {
      store.setInitialized(true)
      vi.mocked(systemApi.switchWorldRoom).mockResolvedValue({ status: 'ok' } as any)
      vi.mocked(systemApi.fetchInitStatus).mockResolvedValue(
        createMockStatus({
          status: 'idle',
          active_room_id: 'draft_world',
          room_ids: ['main', 'draft_world'],
        }),
      )

      const result = await store.switchWorldRoom('draft_world')

      expect(worldStoreMock.reset).toHaveBeenCalled()
      expect(worldStoreMock.initialize).not.toHaveBeenCalled()
      expect(store.isInitialized).toBe(false)
      expect(result?.active_room_id).toBe('draft_world')
    })
  })

  describe('joinWorldRoomByInvite', () => {
    it('should join private world room, refresh status, and reload world when room is ready', async () => {
      vi.mocked(systemApi.joinWorldRoomByInvite).mockResolvedValue({ status: 'ok' } as any)
      vi.mocked(systemApi.fetchInitStatus).mockResolvedValue(
        createMockStatus({
          status: 'ready',
          active_room_id: 'guild_alpha',
          room_ids: ['main', 'guild_alpha'],
        }),
      )

      const result = await store.joinWorldRoomByInvite('guild_alpha', 'ABCD2345')

      expect(systemApi.joinWorldRoomByInvite).toHaveBeenCalledWith({
        room_id: 'guild_alpha',
        invite_code: 'ABCD2345',
        viewer_id: 'viewer_test',
      })
      expect(worldStoreMock.reset).toHaveBeenCalled()
      expect(worldStoreMock.initialize).toHaveBeenCalled()
      expect(result?.active_room_id).toBe('guild_alpha')
    })
  })

  describe('updatePlayerProfile', () => {
    it('should call update profile endpoint and refresh runtime status', async () => {
      vi.mocked(systemApi.updatePlayerProfile).mockResolvedValue({ status: 'ok' } as any)
      vi.mocked(systemApi.fetchInitStatus).mockResolvedValue(
        createMockStatus({
          status: 'ready',
          viewer_profile: {
            viewer_id: 'viewer_test',
            display_name: 'Azure',
            joined_month: 1200,
            last_seen_month: 1201,
            controller_id: 'local',
          },
        }),
      )

      const result = await store.updatePlayerProfile('Azure')

      expect(systemApi.updatePlayerProfile).toHaveBeenCalledWith({
        display_name: 'Azure',
        viewer_id: 'viewer_test',
      })
      expect(systemApi.fetchInitStatus).toHaveBeenCalled()
      expect(result?.viewer_profile?.display_name).toBe('Azure')
    })
  })

  describe('world room access management', () => {
    it('should update room access and refresh runtime status', async () => {
      vi.mocked(systemApi.updateWorldRoomAccess).mockResolvedValue({ status: 'ok' } as any)
      vi.mocked(systemApi.fetchInitStatus).mockResolvedValue(
        createMockStatus({
          status: 'ready',
          active_room_summary: {
            id: 'guild_alpha',
            access_mode: 'private',
            plan_id: 'standard_private',
            commercial_profile: 'standard',
            member_limit: 4,
            member_slots_remaining: 3,
            owner_viewer_id: 'viewer_test',
            member_viewer_ids: ['viewer_test'],
            viewer_has_access: true,
            viewer_is_owner: true,
            is_active: true,
            status: 'ready',
          },
        }),
      )

      const result = await store.updateWorldRoomAccess('guild_alpha', 'private')

      expect(systemApi.updateWorldRoomAccess).toHaveBeenCalledWith({
        room_id: 'guild_alpha',
        access_mode: 'private',
        viewer_id: 'viewer_test',
      })
      expect(result?.active_room_summary?.access_mode).toBe('private')
    })

    it('should update room plan and refresh runtime status', async () => {
      vi.mocked(systemApi.updateWorldRoomPlan).mockResolvedValue({ status: 'ok' } as any)
      vi.mocked(systemApi.fetchInitStatus).mockResolvedValue(
        createMockStatus({
          status: 'ready',
          active_room_summary: {
            id: 'guild_alpha',
            access_mode: 'private',
            plan_id: 'story_rich_private',
            commercial_profile: 'story_rich',
            member_limit: 8,
            member_slots_remaining: 6,
            owner_viewer_id: 'viewer_test',
            member_viewer_ids: ['viewer_test', 'viewer_other'],
            viewer_has_access: true,
            viewer_is_owner: true,
            is_active: true,
            status: 'ready',
          },
        }),
      )

      const result = await store.updateWorldRoomPlan('guild_alpha', 'story_rich_private')

      expect(systemApi.updateWorldRoomPlan).toHaveBeenCalledWith({
        room_id: 'guild_alpha',
        plan_id: 'story_rich_private',
        viewer_id: 'viewer_test',
      })
      expect(result?.active_room_summary?.commercial_profile).toBe('story_rich')
    })

    it('should update room entitlement and refresh runtime status', async () => {
      vi.mocked(systemApi.updateWorldRoomEntitlement).mockResolvedValue({ status: 'ok' } as any)
      vi.mocked(systemApi.fetchInitStatus).mockResolvedValue(
        createMockStatus({
          status: 'ready',
          active_room_summary: {
            id: 'guild_alpha',
            access_mode: 'private',
            plan_id: 'standard_private',
            requested_plan_id: 'story_rich_private',
            commercial_profile: 'standard',
            entitled_plan_id: 'story_rich_private',
            max_selectable_plan_id: 'standard_private',
            billing_status: 'expired',
            plan_locked_by_billing: true,
            member_limit: 4,
            member_slots_remaining: 3,
            owner_viewer_id: 'viewer_test',
            member_viewer_ids: ['viewer_test'],
            viewer_has_access: true,
            viewer_is_owner: true,
            is_active: true,
            status: 'ready',
          },
        }),
      )

      const result = await store.updateWorldRoomEntitlement('guild_alpha', 'expired', 'story_rich_private')

      expect(systemApi.updateWorldRoomEntitlement).toHaveBeenCalledWith({
        room_id: 'guild_alpha',
        billing_status: 'expired',
        entitled_plan_id: 'story_rich_private',
        viewer_id: 'viewer_test',
      })
      expect(result?.active_room_summary?.billing_status).toBe('expired')
      expect(result?.active_room_summary?.plan_locked_by_billing).toBe(true)
    })

    it('should create room payment order and settle it through system api', async () => {
      vi.mocked(systemApi.createWorldRoomPaymentOrder).mockResolvedValue({ status: 'ok' } as any)
      vi.mocked(systemApi.settleWorldRoomPayment).mockResolvedValue({ status: 'ok' } as any)
      vi.mocked(systemApi.fetchInitStatus).mockResolvedValue(
        createMockStatus({
          status: 'ready',
          active_room_summary: {
            id: 'guild_alpha',
            access_mode: 'private',
            plan_id: 'story_rich_private',
            commercial_profile: 'story_rich',
            price_vnd: 1990000,
            billing_cycle_days: 30,
            pending_payment_order: null,
            last_paid_order: {
              order_id: 'rpo_1234',
              target_plan_id: 'story_rich_private',
              amount_vnd: 1990000,
              billing_cycle_days: 30,
              status: 'paid',
              created_at: '2026-04-14T00:00:00+00:00',
              payment_ref: 'manual_tx_123',
            },
            owner_viewer_id: 'viewer_test',
            member_viewer_ids: ['viewer_test'],
            viewer_has_access: true,
            viewer_is_owner: true,
            is_active: true,
            status: 'ready',
          },
        }),
      )

      await store.createWorldRoomPaymentOrder('guild_alpha', 'story_rich_private')
      const result = await store.settleWorldRoomPayment('guild_alpha', 'rpo_1234', 'manual_tx_123')

      expect(systemApi.createWorldRoomPaymentOrder).toHaveBeenCalledWith({
        room_id: 'guild_alpha',
        target_plan_id: 'story_rich_private',
        viewer_id: 'viewer_test',
      })
      expect(systemApi.settleWorldRoomPayment).toHaveBeenCalledWith({
        room_id: 'guild_alpha',
        order_id: 'rpo_1234',
        payment_ref: 'manual_tx_123',
        amount_vnd: undefined,
        viewer_id: 'viewer_test',
      })
      expect(result?.active_room_summary?.last_paid_order?.payment_ref).toBe('manual_tx_123')
    })

    it('should reconcile room payment and refresh runtime status', async () => {
      vi.mocked(systemApi.reconcileWorldRoomPayment).mockResolvedValue({ status: 'ok' } as any)
      vi.mocked(systemApi.fetchInitStatus).mockResolvedValue(
        createMockStatus({
          status: 'ready',
          active_room_summary: {
            id: 'guild_alpha',
            access_mode: 'private',
            plan_id: 'story_rich_private',
            commercial_profile: 'story_rich',
            payment_events: [
              {
                timestamp: '2026-04-14T00:00:00+00:00',
                event_type: 'payment_settled',
                source: 'manual_reconcile',
                status: 'paid',
                order_id: 'rpo_1234',
                payment_ref: 'manual_tx_124',
                amount_vnd: 1990000,
              },
            ],
            owner_viewer_id: 'viewer_test',
            member_viewer_ids: ['viewer_test'],
            viewer_has_access: true,
            viewer_is_owner: true,
            is_active: true,
            status: 'ready',
          },
        }),
      )

      const result = await store.reconcileWorldRoomPayment(
        'CWS GUILD_ALPHA RPO_1234',
        'manual_tx_124',
        1990000,
      )

      expect(systemApi.reconcileWorldRoomPayment).toHaveBeenCalledWith({
        transfer_note: 'CWS GUILD_ALPHA RPO_1234',
        payment_ref: 'manual_tx_124',
        amount_vnd: 1990000,
        viewer_id: 'viewer_test',
      })
      expect(result?.active_room_summary?.payment_events?.[0]?.source).toBe('manual_reconcile')
    })

    it('should add and remove room members through system api', async () => {
      vi.mocked(systemApi.addWorldRoomMember).mockResolvedValue({ status: 'ok' } as any)
      vi.mocked(systemApi.removeWorldRoomMember).mockResolvedValue({ status: 'ok' } as any)
      vi.mocked(systemApi.fetchInitStatus).mockResolvedValue(createMockStatus({ status: 'ready' }))

      await store.addWorldRoomMember('guild_alpha', 'viewer_other')
      await store.removeWorldRoomMember('guild_alpha', 'viewer_other')

      expect(systemApi.addWorldRoomMember).toHaveBeenCalledWith({
        room_id: 'guild_alpha',
        member_viewer_id: 'viewer_other',
        viewer_id: 'viewer_test',
      })
      expect(systemApi.removeWorldRoomMember).toHaveBeenCalledWith({
        room_id: 'guild_alpha',
        member_viewer_id: 'viewer_other',
        viewer_id: 'viewer_test',
      })
    })

    it('should rotate room invite and refresh runtime status', async () => {
      vi.mocked(systemApi.rotateWorldRoomInvite).mockResolvedValue({ status: 'ok' } as any)
      vi.mocked(systemApi.fetchInitStatus).mockResolvedValue(
        createMockStatus({
          status: 'ready',
          active_room_summary: {
            id: 'guild_alpha',
            access_mode: 'private',
            owner_viewer_id: 'viewer_test',
            member_viewer_ids: ['viewer_test'],
            invite_code: 'ZXCV1234',
            viewer_has_access: true,
            viewer_is_owner: true,
            is_active: true,
            status: 'ready',
          },
        }),
      )

      const result = await store.rotateWorldRoomInvite('guild_alpha')

      expect(systemApi.rotateWorldRoomInvite).toHaveBeenCalledWith({
        room_id: 'guild_alpha',
        viewer_id: 'viewer_test',
      })
      expect(result?.active_room_summary?.invite_code).toBe('ZXCV1234')
    })
  })

  describe('pause', () => {
    it('should call pauseGame API', async () => {
      vi.mocked(systemApi.pauseGame).mockResolvedValue(undefined)

      await store.pause()

      expect(systemApi.pauseGame).toHaveBeenCalled()
    })

    it('should not modify isManualPaused state', async () => {
      store.isManualPaused = false
      vi.mocked(systemApi.pauseGame).mockResolvedValue(undefined)

      await store.pause()

      expect(store.isManualPaused).toBe(false)
    })

    it('should log error on failure', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      vi.mocked(systemApi.pauseGame).mockRejectedValue(new Error('API error'))

      await store.pause()

      expect(consoleSpy).toHaveBeenCalled()
      consoleSpy.mockRestore()
    })
  })

  describe('resume', () => {
    it('should call resumeGame API', async () => {
      vi.mocked(systemApi.resumeGame).mockResolvedValue(undefined)

      await store.resume()

      expect(systemApi.resumeGame).toHaveBeenCalled()
    })

    it('should not modify isManualPaused state', async () => {
      store.isManualPaused = true
      vi.mocked(systemApi.resumeGame).mockResolvedValue(undefined)

      await store.resume()

      expect(store.isManualPaused).toBe(true)
    })

    it('should log error on failure', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      vi.mocked(systemApi.resumeGame).mockRejectedValue(new Error('API error'))

      await store.resume()

      expect(consoleSpy).toHaveBeenCalled()
      consoleSpy.mockRestore()
    })
  })

  describe('isGameRunning', () => {
    it('should have initial value of false', () => {
      expect(store.isGameRunning).toBe(false)
    })
  })
})
