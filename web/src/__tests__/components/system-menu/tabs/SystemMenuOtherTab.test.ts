import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'

import SystemMenuOtherTab from '@/components/system-menu/tabs/SystemMenuOtherTab.vue'
import { useSystemStore } from '@/stores/system'
import { useSocketStore } from '@/stores/socket'

function createTestI18n() {
  return createI18n({
    legacy: false,
    locale: 'en-US',
    messages: {
      'en-US': {
        ui: {
          other_options: 'Other Options',
          other_options_desc: 'Manage game process and exit.',
          player_identity_title: 'Player Identity',
          player_identity_desc: 'Room identity management',
          player_identity_current: 'Current identity: {id}',
          player_identity_placeholder: 'Display name',
          player_identity_save: 'Save Identity',
          player_identity_save_failed: 'Save failed',
          player_identity_roster_title: 'Room Roster',
          player_identity_roster_empty: 'No players yet',
          player_identity_status_you: 'You',
          player_identity_status_active: 'Active Control',
          player_identity_seat: 'Seat {id}',
          control_rooms_title: 'World Rooms',
          control_rooms_desc: 'Room management',
          control_rooms_current: 'Current room: {id}',
          control_rooms_placeholder: 'New room',
          control_rooms_create: 'Create / Switch Room',
          control_rooms_unavailable: 'Unavailable',
          control_room_switch_failed: 'Room switch failed',
          control_room_status_open: 'open',
          control_room_status_private: 'private',
          control_room_status_locked: 'locked',
          control_room_access_title: 'Room Access',
          control_room_access_mode: 'Access mode:',
          control_room_owner: 'Owner: {id}',
          control_room_access_denied: 'Room denied',
          control_room_access_update_failed: 'Room access update failed',
          control_room_member_placeholder: 'Viewer ID',
          control_room_member_add: 'Add Member',
          control_room_member_remove: 'Remove',
          control_room_member_owner: 'Owner',
          control_room_member_allowed: 'Allowed',
          control_room_member_add_failed: 'Add failed',
          control_room_member_remove_failed: 'Remove failed',
          control_room_join_title: 'Join Private Room',
          control_room_join_room_placeholder: 'Room ID',
          control_room_join_code_placeholder: 'Invite code',
          control_room_join_action: 'Join Room',
          control_room_join_failed: 'Join failed',
          control_room_invite_code: 'Invite: {code}',
          control_room_invite_rotate: 'Rotate Invite',
          control_room_invite_rotate_failed: 'Rotate failed',
          control_room_plan_current: 'Plan: {plan} · Profile: {profile}',
          control_room_plan_requested: 'Requested plan: {plan}',
          control_room_capacity: 'Members: {count}/{limit}',
          control_room_plan_public: 'Main Public World',
          control_room_plan_standard: 'Standard Private',
          control_room_plan_story_rich: 'Story-Rich Private',
          control_room_plan_internal: 'Internal Full',
          control_room_plan_update_failed: 'Plan update failed',
          control_room_billing_title: 'Commercial Entitlement',
          control_room_billing_summary: 'Billing: {status} · Entitled plan: {plan}',
          control_room_billing_status: 'Billing status: {status}',
          control_room_billing_deadline: 'Renew by: {date} · {days} days left',
          control_room_billing_renewal_recommended: 'Renew now to avoid plan downgrade',
          control_room_entitled_plan: 'Entitled plan: {plan}',
          control_room_billing_trial: 'Trial',
          control_room_billing_active: 'Active',
          control_room_billing_grace: 'Grace',
          control_room_billing_expired: 'Expired',
          control_room_entitlement_update_failed: 'Entitlement update failed',
          control_room_plan_locked_by_billing: 'Plan downgraded by billing',
          control_room_plan_locked_hint: 'Higher plans are downgraded by billing limits.',
          control_room_payment_title: 'Payments',
          control_room_price: 'Price: {amount} / {days} days',
          control_room_payment_order_create: 'Create payment order: {plan} · {amount}',
          control_room_payment_order_create_failed: 'Create payment order failed',
          control_room_payment_pending: 'Pending order: {orderId} · {amount}',
          control_room_payment_transfer_note: 'Transfer note: {note}',
          control_room_payment_settle: 'Mark payment settled',
          control_room_payment_settle_failed: 'Settle payment failed',
          control_room_payment_last_paid: 'Last settled order: {orderId} · {amount}',
          control_room_payment_renew_now: 'Renew {plan} · {amount}',
          control_room_payment_reconcile: 'Reconcile from transfer note',
          control_room_payment_reconcile_failed: 'Reconcile payment failed',
          control_room_payment_reconcile_note_placeholder: 'Enter transfer note',
          control_room_payment_reconcile_ref_placeholder: 'Enter payment reference',
          control_room_payment_reconcile_amount_placeholder: 'Enter amount',
          control_room_payment_audit_title: 'Recent payment events',
          control_room_payment_audit_empty: 'No payment events yet',
          control_seats_title: 'Control Seats',
          control_seats_desc: 'Seat management',
          control_seats_viewer: 'Viewer: {id}',
          control_seats_current: 'Current seat: {id}',
          control_seats_placeholder: 'New seat',
          control_seats_create: 'Create / Switch Seat',
          control_seats_release: 'Release Active Seat',
          control_seats_unavailable: 'Unavailable',
          control_seat_switch_failed: 'Switch failed',
          control_seat_release_failed: 'Release failed',
          control_seat_status_yours: 'Yours',
          control_seat_status_open: 'Open',
          control_seat_status_claimed: 'Claimed',
          return_to_main: 'Return',
          return_to_main_desc: 'Return to main menu',
          quit_game: 'Quit',
          quit_game_desc: 'Exit the game',
        },
      },
    },
  })
}

describe('SystemMenuOtherTab', () => {
  let pinia: ReturnType<typeof createPinia>

  beforeEach(() => {
    window.localStorage.clear()
    window.localStorage.setItem('cws_viewer_id', 'viewer_test')
    pinia = createPinia()
    setActivePinia(pinia)
  })

  it('renders control seats and switches to an existing seat', async () => {
    const i18n = createTestI18n()
    const store = useSystemStore()
    const socketStore = useSocketStore()
    store.initStatus = {
      status: 'ready',
      phase: 0,
      phase_name: '',
      progress: 100,
      elapsed_seconds: 0,
      error: null,
      llm_check_failed: false,
      llm_error_message: '',
      active_room_id: 'main',
      room_ids: ['main', 'guild_alpha'],
      active_controller_id: 'local',
      viewer_profile: {
        viewer_id: 'viewer_test',
        display_name: 'Bon',
        joined_month: 1200,
        last_seen_month: 1201,
        controller_id: 'local',
        is_active_controller: true,
      },
      player_profiles: [
        {
          viewer_id: 'viewer_test',
          display_name: 'Bon',
          joined_month: 1200,
          last_seen_month: 1201,
          controller_id: 'local',
          is_active_controller: true,
        },
      ],
      player_control_seat_ids: ['local', 'seat_b'],
      player_control_seats: [
        { id: 'local', holder_id: 'viewer_test', is_active: true },
        { id: 'seat_b', holder_id: null, is_active: false },
      ],
    }

    vi.spyOn(store, 'fetchInitStatus').mockResolvedValue(store.initStatus)
    const socketSwitchSpy = vi.spyOn(socketStore, 'switchRoom').mockImplementation(() => {})
    const switchRoomSpy = vi.spyOn(store, 'switchWorldRoom').mockResolvedValue({
      ...store.initStatus,
      active_room_id: 'guild_alpha',
      room_ids: ['main', 'guild_alpha'],
    })
    const switchSpy = vi.spyOn(store, 'switchControlSeat').mockResolvedValue({
      ...store.initStatus,
      active_room_id: 'main',
      room_ids: ['main', 'guild_alpha'],
      active_controller_id: 'seat_b',
      player_control_seat_ids: ['local', 'seat_b'],
    })

    const wrapper = mount(SystemMenuOtherTab, {
      global: {
        plugins: [pinia, i18n],
        directives: {
          sound: () => {},
        },
      },
    })

    expect(wrapper.text()).toContain('Current room: main')
    expect(wrapper.text()).toContain('Current seat: local')
    expect(wrapper.text()).toContain('Current identity: Bon')
    expect(wrapper.text()).toContain('Viewer: viewer_test')

    const panels = wrapper.findAll('.seat-panel')
    expect(panels).toHaveLength(3)
    const roomButtons = panels[1].findAll('.seat-chip')
    const seatButtons = panels[2].findAll('.seat-chip')
    expect(roomButtons).toHaveLength(2)
    expect(seatButtons).toHaveLength(2)

    await roomButtons[1].trigger('click')
    expect(switchRoomSpy).toHaveBeenCalledWith('guild_alpha')
    expect(socketSwitchSpy).toHaveBeenCalledWith('guild_alpha')

    await seatButtons[1].trigger('click')

    expect(switchSpy).toHaveBeenCalledWith('seat_b')
    expect(seatButtons[1].text()).toContain('Open')
  })

  it('creates or switches to a typed seat id and can release the active seat', async () => {
    const i18n = createTestI18n()
    const store = useSystemStore()
    const socketStore = useSocketStore()
    store.initStatus = {
      status: 'ready',
      phase: 0,
      phase_name: '',
      progress: 100,
      elapsed_seconds: 0,
      error: null,
      llm_check_failed: false,
      llm_error_message: '',
      active_room_id: 'main',
      room_ids: ['main'],
      active_controller_id: 'local',
      viewer_profile: {
        viewer_id: 'viewer_test',
        display_name: 'Bon',
        joined_month: 1200,
        last_seen_month: 1201,
        controller_id: 'local',
        is_active_controller: true,
      },
      player_profiles: [
        {
          viewer_id: 'viewer_test',
          display_name: 'Bon',
          joined_month: 1200,
          last_seen_month: 1201,
          controller_id: 'local',
          is_active_controller: true,
        },
      ],
      player_control_seat_ids: ['local', 'seat_locked'],
      player_control_seats: [
        { id: 'local', holder_id: 'viewer_test', is_active: true },
        { id: 'seat_locked', holder_id: 'viewer_other', is_active: false },
      ],
    }

    vi.spyOn(store, 'fetchInitStatus').mockResolvedValue(store.initStatus)
    const socketSwitchSpy = vi.spyOn(socketStore, 'switchRoom').mockImplementation(() => {})
    const switchRoomSpy = vi.spyOn(store, 'switchWorldRoom').mockResolvedValue({
      ...store.initStatus,
      active_room_id: 'guild_beta',
      room_ids: ['main', 'guild_beta'],
    })
    const switchSpy = vi.spyOn(store, 'switchControlSeat').mockResolvedValue({
      ...store.initStatus,
      active_room_id: 'main',
      room_ids: ['main'],
      active_controller_id: 'seat_c',
      player_control_seat_ids: ['local', 'seat_c'],
      player_control_seats: [
        { id: 'local', holder_id: 'viewer_test', is_active: false },
        { id: 'seat_c', holder_id: 'viewer_test', is_active: true },
      ],
    })
    const releaseSpy = vi.spyOn(store, 'releaseControlSeat').mockResolvedValue({
      ...store.initStatus,
      active_controller_id: 'local',
      player_control_seat_ids: ['local', 'seat_locked'],
      player_control_seats: [
        { id: 'local', holder_id: null, is_active: true },
        { id: 'seat_locked', holder_id: 'viewer_other', is_active: false },
      ],
    })

    const wrapper = mount(SystemMenuOtherTab, {
      global: {
        plugins: [pinia, i18n],
        directives: {
          sound: () => {},
        },
      },
    })

    const panels = wrapper.findAll('.seat-panel')
    await panels[1].find('.seat-input').setValue('guild_beta')
    await panels[1].find('.seat-create-btn').trigger('click')
    expect(switchRoomSpy).toHaveBeenCalledWith('guild_beta')
    expect(socketSwitchSpy).toHaveBeenCalledWith('guild_beta')

    const seatButtons = panels[2].findAll('.seat-chip')
    expect(seatButtons[0].text()).toContain('Yours')
    expect(seatButtons[1].text()).toContain('Claimed')
    expect(seatButtons[1].attributes('disabled')).toBeDefined()

    await panels[2].find('.seat-input').setValue('seat_c')
    await panels[2].find('.seat-create-btn').trigger('click')

    expect(switchSpy).toHaveBeenCalledWith('seat_c')

    const releaseButton = panels[2].find('.seat-release-btn')
    await releaseButton.trigger('click')
    expect(releaseSpy).toHaveBeenCalledWith('local')
  })

  it('saves player profile display name and shows room roster', async () => {
    const i18n = createTestI18n()
    const store = useSystemStore()
    store.initStatus = {
      status: 'ready',
      phase: 0,
      phase_name: '',
      progress: 100,
      elapsed_seconds: 0,
      error: null,
      llm_check_failed: false,
      llm_error_message: '',
      active_room_id: 'guild_alpha',
      room_ids: ['main', 'guild_alpha'],
      active_controller_id: 'seat_b',
      viewer_profile: {
        viewer_id: 'viewer_test',
        display_name: 'Bon',
        joined_month: 1200,
        last_seen_month: 1201,
        controller_id: 'seat_b',
        is_active_controller: true,
      },
      player_profiles: [
        {
          viewer_id: 'viewer_test',
          display_name: 'Bon',
          joined_month: 1200,
          last_seen_month: 1201,
          controller_id: 'seat_b',
          is_active_controller: true,
        },
        {
          viewer_id: 'viewer_other',
          display_name: 'Rival',
          joined_month: 1200,
          last_seen_month: 1201,
          controller_id: 'seat_c',
          is_active_controller: false,
        },
      ],
      player_control_seat_ids: ['seat_b', 'seat_c'],
      player_control_seats: [
        { id: 'seat_b', holder_id: 'viewer_test', holder_display_name: 'Bon', is_active: true },
        { id: 'seat_c', holder_id: 'viewer_other', holder_display_name: 'Rival', is_active: false },
      ],
    }

    vi.spyOn(store, 'fetchInitStatus').mockResolvedValue(store.initStatus)
    const updateSpy = vi.spyOn(store, 'updatePlayerProfile').mockResolvedValue({
      ...store.initStatus,
      viewer_profile: {
        viewer_id: 'viewer_test',
        display_name: 'Azure',
        joined_month: 1200,
        last_seen_month: 1202,
        controller_id: 'seat_b',
        is_active_controller: true,
      },
    })

    const wrapper = mount(SystemMenuOtherTab, {
      global: {
        plugins: [pinia, i18n],
        directives: {
          sound: () => {},
        },
      },
    })

    const panels = wrapper.findAll('.seat-panel')
    expect(panels[0].text()).toContain('Room Roster')
    expect(panels[0].text()).toContain('Bon')
    expect(panels[0].text()).toContain('Rival')

    await panels[0].find('.seat-input').setValue('Azure')
    await panels[0].find('.seat-create-btn').trigger('click')

    expect(updateSpy).toHaveBeenCalledWith('Azure')
  })

  it('shows private room invite controls for the owner and can join by invite', async () => {
    const i18n = createTestI18n()
    const store = useSystemStore()
    const socketStore = useSocketStore()
    store.initStatus = {
      status: 'ready',
      phase: 0,
      phase_name: '',
      progress: 100,
      elapsed_seconds: 0,
      error: null,
      llm_check_failed: false,
      llm_error_message: '',
      active_room_id: 'guild_alpha',
      room_ids: ['main', 'guild_alpha', 'guild_beta'],
      active_room_summary: {
        id: 'guild_alpha',
        access_mode: 'private',
        plan_id: 'story_rich_private',
        requested_plan_id: 'story_rich_private',
        commercial_profile: 'story_rich',
        price_vnd: 1990000,
        billing_cycle_days: 30,
        member_limit: 8,
        member_slots_remaining: 7,
        entitled_plan_id: 'story_rich_private',
        max_selectable_plan_id: 'story_rich_private',
        billing_status: 'active',
        billing_deadline_at: '2026-04-20T00:00:00+00:00',
        billing_days_remaining: 6,
        billing_renewal_recommended: true,
        billing_renewal_stage: 'soon',
        plan_locked_by_billing: false,
        sellable_plan_offers: [
          {
            plan_id: 'standard_private',
            commercial_profile: 'standard',
            member_limit: 4,
            price_vnd: 990000,
            billing_cycle_days: 30,
            sellable: true,
          },
          {
            plan_id: 'story_rich_private',
            commercial_profile: 'story_rich',
            member_limit: 8,
            price_vnd: 1990000,
            billing_cycle_days: 30,
            sellable: true,
          },
        ],
        pending_payment_order: {
          order_id: 'rpo_1234',
          room_id: 'guild_alpha',
          target_plan_id: 'story_rich_private',
          amount_vnd: 1990000,
          billing_cycle_days: 30,
          status: 'pending',
          created_at: '2026-04-14T00:00:00+00:00',
          transfer_note: 'CWS GUILD_ALPHA RPO_1234',
        },
        payment_events: [
          {
            timestamp: '2026-04-14T00:00:00+00:00',
            event_type: 'order_created',
            source: 'owner_command',
            status: 'pending',
            order_id: 'rpo_1234',
            amount_vnd: 1990000,
            note: 'CWS GUILD_ALPHA RPO_1234',
          },
        ],
        owner_viewer_id: 'viewer_test',
        member_viewer_ids: ['viewer_test'],
        invite_code: 'ABCD2345',
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
          plan_id: 'story_rich_private',
          requested_plan_id: 'story_rich_private',
          commercial_profile: 'story_rich',
          price_vnd: 1990000,
          billing_cycle_days: 30,
          member_limit: 8,
          member_slots_remaining: 7,
          entitled_plan_id: 'story_rich_private',
          max_selectable_plan_id: 'story_rich_private',
          billing_status: 'active',
          billing_deadline_at: '2026-04-20T00:00:00+00:00',
          billing_days_remaining: 6,
          billing_renewal_recommended: true,
          billing_renewal_stage: 'soon',
          plan_locked_by_billing: false,
          sellable_plan_offers: [
            {
              plan_id: 'standard_private',
              commercial_profile: 'standard',
              member_limit: 4,
              price_vnd: 990000,
              billing_cycle_days: 30,
              sellable: true,
            },
            {
              plan_id: 'story_rich_private',
              commercial_profile: 'story_rich',
              member_limit: 8,
              price_vnd: 1990000,
              billing_cycle_days: 30,
              sellable: true,
            },
          ],
          pending_payment_order: {
            order_id: 'rpo_1234',
            room_id: 'guild_alpha',
            target_plan_id: 'story_rich_private',
            amount_vnd: 1990000,
            billing_cycle_days: 30,
            status: 'pending',
            created_at: '2026-04-14T00:00:00+00:00',
            transfer_note: 'CWS GUILD_ALPHA RPO_1234',
          },
          payment_events: [
            {
              timestamp: '2026-04-14T00:00:00+00:00',
              event_type: 'order_created',
              source: 'owner_command',
              status: 'pending',
              order_id: 'rpo_1234',
              amount_vnd: 1990000,
              note: 'CWS GUILD_ALPHA RPO_1234',
            },
          ],
          owner_viewer_id: 'viewer_test',
          member_viewer_ids: ['viewer_test'],
          invite_code: 'ABCD2345',
          viewer_has_access: true,
          viewer_is_owner: true,
          is_active: true,
          status: 'ready',
        },
        {
          id: 'guild_beta',
          access_mode: 'private',
          owner_viewer_id: null,
          member_viewer_ids: [],
          viewer_has_access: false,
          viewer_is_owner: false,
          is_active: false,
          status: 'ready',
        },
      ],
      active_controller_id: 'seat_b',
      viewer_profile: {
        viewer_id: 'viewer_test',
        display_name: 'Bon',
        joined_month: 1200,
        last_seen_month: 1201,
        controller_id: 'seat_b',
        is_active_controller: true,
      },
      player_profiles: [
        {
          viewer_id: 'viewer_test',
          display_name: 'Bon',
          joined_month: 1200,
          last_seen_month: 1201,
          controller_id: 'seat_b',
          is_active_controller: true,
        },
      ],
      player_control_seat_ids: ['seat_b'],
      player_control_seats: [
        { id: 'seat_b', holder_id: 'viewer_test', holder_display_name: 'Bon', is_active: true },
      ],
    }

    vi.spyOn(store, 'fetchInitStatus').mockResolvedValue(store.initStatus)
    const rotateInviteSpy = vi.spyOn(store, 'rotateWorldRoomInvite').mockResolvedValue(store.initStatus)
    const updatePlanSpy = vi.spyOn(store, 'updateWorldRoomPlan').mockResolvedValue(store.initStatus)
    const createPaymentOrderSpy = vi.spyOn(store, 'createWorldRoomPaymentOrder').mockResolvedValue(store.initStatus)
    const settlePaymentSpy = vi.spyOn(store, 'settleWorldRoomPayment').mockResolvedValue(store.initStatus)
    const reconcilePaymentSpy = vi.spyOn(store, 'reconcileWorldRoomPayment').mockResolvedValue(store.initStatus)
    const joinByInviteSpy = vi.spyOn(store, 'joinWorldRoomByInvite').mockResolvedValue({
      ...store.initStatus,
      active_room_id: 'guild_beta',
    })
    const socketSwitchSpy = vi.spyOn(socketStore, 'switchRoom').mockImplementation(() => {})

    const wrapper = mount(SystemMenuOtherTab, {
      global: {
        plugins: [pinia, i18n],
        directives: {
          sound: () => {},
        },
      },
    })

    expect(wrapper.text()).toContain('Invite: ABCD2345')
    expect(wrapper.text()).toContain('locked')
    expect(wrapper.text()).toContain('Plan: Story-Rich Private · Profile: story_rich')
    expect(wrapper.text()).toContain('Billing: Active · Entitled plan: Story-Rich Private')
    expect(wrapper.text()).toContain('Renew by:')
    expect(wrapper.text()).toContain('Renew now to avoid plan downgrade')
    expect(wrapper.text()).toContain('Pending order: rpo_1234')
    expect(wrapper.text()).toContain('Transfer note: CWS GUILD_ALPHA RPO_1234')
    expect(wrapper.text()).toContain('Members: 1/8')
    expect(wrapper.text()).toContain('Recent payment events')
    expect(wrapper.text()).toContain('order_created')

    const roomPanel = wrapper.findAll('.seat-panel')[1]
    const planButton = roomPanel.findAll('button.seat-chip').find((item) => item.text() === 'Standard Private')
    expect(planButton).toBeTruthy()
    await planButton!.trigger('click')
    expect(updatePlanSpy).toHaveBeenCalledWith('guild_alpha', 'standard_private')

    const textInputs = roomPanel.findAll('input.seat-input')
    await textInputs[1].setValue('guild_beta')
    await textInputs[2].setValue('ABCD2345')
    await roomPanel.findAll('button.seat-create-btn')[1].trigger('click')

    expect(joinByInviteSpy).toHaveBeenCalledWith('guild_beta', 'ABCD2345')
    expect(socketSwitchSpy).toHaveBeenCalledWith('guild_beta')

    const paymentButtons = roomPanel.findAll('button.seat-chip').filter((item) => item.text().includes('Create payment order:'))
    expect(paymentButtons.length).toBeGreaterThan(0)
    const renewButton = roomPanel.findAll('button.seat-create-btn').find((item) => item.text().includes('Renew Story-Rich Private'))
    expect(renewButton).toBeTruthy()
    await renewButton!.trigger('click')
    expect(createPaymentOrderSpy).toHaveBeenCalledWith('guild_alpha', 'story_rich_private')
    await paymentButtons[0].trigger('click')
    expect(createPaymentOrderSpy).toHaveBeenCalled()

    const settleButton = roomPanel.findAll('button.member-remove-btn').find((item) => item.text() === 'Mark payment settled')
    expect(settleButton).toBeTruthy()
    await settleButton!.trigger('click')
    expect(settlePaymentSpy).toHaveBeenCalledWith('guild_alpha', 'rpo_1234', undefined, 1990000)

    const paymentInputs = roomPanel.findAll('input.seat-input')
    await paymentInputs[3].setValue('CWS GUILD_ALPHA RPO_1234')
    await paymentInputs[4].setValue('manual_tx_124')
    await paymentInputs[5].setValue('1990000')
    const reconcileButton = roomPanel.findAll('button.seat-create-btn').find((item) => item.text() === 'Reconcile from transfer note')
    expect(reconcileButton).toBeTruthy()
    await reconcileButton!.trigger('click')
    expect(reconcilePaymentSpy).toHaveBeenCalledWith('CWS GUILD_ALPHA RPO_1234', 'manual_tx_124', 1990000)

    const rotateButton = roomPanel.findAll('button.member-remove-btn').find((item) => item.text() === 'Rotate Invite')
    expect(rotateButton).toBeTruthy()
    await rotateButton!.trigger('click')
    expect(rotateInviteSpy).toHaveBeenCalledWith('guild_alpha')
  })
})
