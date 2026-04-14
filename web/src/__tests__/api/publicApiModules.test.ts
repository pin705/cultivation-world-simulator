import { beforeEach, describe, expect, it, vi } from 'vitest'

const getMock = vi.fn()
const postMock = vi.fn()
const deleteMock = vi.fn()

vi.mock('@/api/http', () => ({
  httpClient: {
    get: getMock,
    post: postMock,
    delete: deleteMock,
  },
}))

describe('public api module migration', () => {
  beforeEach(() => {
    window.localStorage.clear()
    window.localStorage.setItem('cws_viewer_id', 'viewer_test')
    getMock.mockReset()
    postMock.mockReset()
    deleteMock.mockReset()
  })

  it('worldApi fetches world state and map from /api/v1', async () => {
    const { worldApi } = await import('@/api/modules/world')
    getMock.mockResolvedValueOnce({ status: 'ok', year: 100, month: 1 })
    getMock.mockResolvedValueOnce({ data: [], regions: [], render_config: {} })

    const state = await worldApi.fetchInitialState()
    const map = await worldApi.fetchMap()

    expect(getMock).toHaveBeenNthCalledWith(1, '/api/v1/query/world/state')
    expect(getMock).toHaveBeenNthCalledWith(2, '/api/v1/query/world/map')
    expect(state.avatars).toEqual([])
    expect(state.events).toEqual([])
    expect(map.renderConfig).toEqual({ water_speed: 'high', cloud_frequency: 'none' })
  })

  it('eventApi fetches events from /api/v1 query endpoint', async () => {
    const { eventApi } = await import('@/api/modules/event')
    getMock.mockResolvedValue({ events: [], next_cursor: null, has_more: false })

    const page = await eventApi.fetchEvents({ avatar_id: 'a1', limit: 20 })

    expect(getMock).toHaveBeenCalledWith('/api/v1/query/events?avatar_id=a1&limit=20')
    expect(page).toEqual({ events: [], nextCursor: null, hasMore: false })
  })

  it('eventApi cleans up events through /api/v1 command endpoint', async () => {
    const { eventApi } = await import('@/api/modules/event')
    deleteMock.mockResolvedValue({ deleted: 12 })

    await eventApi.cleanupEvents(false, 1200)

    expect(deleteMock).toHaveBeenCalledWith('/api/v1/command/events/cleanup?keep_major=false&before_month_stamp=1200')
  })

  it('worldApi fetches sect territories from /api/v1', async () => {
    const { worldApi } = await import('@/api/modules/world')
    getMock.mockResolvedValue({ sects: [] })

    await worldApi.fetchSectTerritories()

    expect(getMock).toHaveBeenCalledWith('/api/v1/query/sects/territories')
  })

  it('worldApi posts sect directive commands through /api/v1', async () => {
    const { worldApi } = await import('@/api/modules/world')
    postMock.mockResolvedValue({ status: 'ok' })

    await worldApi.claimSect({ sect_id: 7 })
    await worldApi.setSectDirective({ sect_id: 7, content: '先稳边界，再择机争夺资源。' })
    await worldApi.clearSectDirective({ sect_id: 7 })
    await worldApi.interveneSectRelation({ sect_id: 7, other_sect_id: 9, mode: 'ease' })

    expect(postMock).toHaveBeenNthCalledWith(1, '/api/v1/command/player/claim-sect', {
      sect_id: 7,
      viewer_id: 'viewer_test',
    })
    expect(postMock).toHaveBeenNthCalledWith(2, '/api/v1/command/sect/set-directive', {
      sect_id: 7,
      content: '先稳边界，再择机争夺资源。',
      viewer_id: 'viewer_test',
    })
    expect(postMock).toHaveBeenNthCalledWith(3, '/api/v1/command/sect/clear-directive', {
      sect_id: 7,
      viewer_id: 'viewer_test',
    })
    expect(postMock).toHaveBeenNthCalledWith(4, '/api/v1/command/sect/intervene-relation', {
      sect_id: 7,
      other_sect_id: 9,
      mode: 'ease',
      viewer_id: 'viewer_test',
    })
  })

  it('systemApi uses /api/v1 lifecycle and save endpoints', async () => {
    const { systemApi } = await import('@/api/modules/system')
    getMock.mockResolvedValue({ status: 'idle' })
    postMock.mockResolvedValue({ status: 'ok' })

    await systemApi.fetchInitStatus()
    await systemApi.fetchSaves()
    await systemApi.saveGame('存档A')
    await systemApi.loadGame('save.json')

    expect(getMock).toHaveBeenNthCalledWith(1, '/api/v1/query/runtime/status?viewer_id=viewer_test')
    expect(getMock).toHaveBeenNthCalledWith(2, '/api/v1/query/saves')
    expect(postMock).toHaveBeenNthCalledWith(1, '/api/v1/command/game/save', { custom_name: '存档A' })
    expect(postMock).toHaveBeenNthCalledWith(2, '/api/v1/command/game/load', { filename: 'save.json' })
  })

  it('systemApi startNewGame and shutdown use /api/v1 endpoints', async () => {
    const { systemApi } = await import('@/api/modules/system')
    postMock.mockResolvedValue({ status: 'ok' })

    await systemApi.startNewGame()
    await systemApi.shutdown()

    expect(postMock).toHaveBeenNthCalledWith(1, '/api/v1/command/game/reinit', {})
    expect(postMock).toHaveBeenNthCalledWith(2, '/api/v1/command/system/shutdown', {})
  })

  it('systemApi switches control seats through /api/v1 endpoint', async () => {
    const { systemApi } = await import('@/api/modules/system')
    postMock.mockResolvedValue({ status: 'ok' })

    await systemApi.switchControlSeat({ controller_id: 'seat_b', viewer_id: 'viewer_test' })
    await systemApi.releaseControlSeat({ controller_id: 'seat_b', viewer_id: 'viewer_test' })

    expect(postMock).toHaveBeenNthCalledWith(1, '/api/v1/command/player/switch-seat', {
      controller_id: 'seat_b',
      viewer_id: 'viewer_test',
    })
    expect(postMock).toHaveBeenNthCalledWith(2, '/api/v1/command/player/release-seat', {
      controller_id: 'seat_b',
      viewer_id: 'viewer_test',
    })
  })

  it('systemApi switches world rooms through /api/v1 endpoint', async () => {
    const { systemApi } = await import('@/api/modules/system')
    postMock.mockResolvedValue({ status: 'ok' })

    await systemApi.switchWorldRoom({ room_id: 'guild_alpha' })

    expect(postMock).toHaveBeenCalledWith('/api/v1/command/world-room/switch', {
      room_id: 'guild_alpha',
      viewer_id: 'viewer_test',
    })
  })

  it('systemApi updates player profile through /api/v1 endpoint', async () => {
    const { systemApi } = await import('@/api/modules/system')
    postMock.mockResolvedValue({ status: 'ok' })

    await systemApi.updatePlayerProfile({ display_name: 'Azure' })

    expect(postMock).toHaveBeenCalledWith('/api/v1/command/player/update-profile', {
      display_name: 'Azure',
      viewer_id: 'viewer_test',
    })
  })

  it('systemApi manages world room access through /api/v1 endpoints', async () => {
    const { systemApi } = await import('@/api/modules/system')
    postMock.mockResolvedValue({ status: 'ok' })

    await systemApi.updateWorldRoomAccess({ room_id: 'guild_alpha', access_mode: 'private' })
    await systemApi.updateWorldRoomPlan({ room_id: 'guild_alpha', plan_id: 'story_rich_private' })
    await systemApi.updateWorldRoomEntitlement({
      room_id: 'guild_alpha',
      billing_status: 'active',
      entitled_plan_id: 'story_rich_private',
    })
    await systemApi.createWorldRoomPaymentOrder({
      room_id: 'guild_alpha',
      target_plan_id: 'story_rich_private',
    })
    await systemApi.settleWorldRoomPayment({
      room_id: 'guild_alpha',
      order_id: 'rpo_1234',
      payment_ref: 'manual_tx_123',
    })
    await systemApi.reconcileWorldRoomPayment({
      transfer_note: 'CWS GUILD_ALPHA RPO_1234',
      payment_ref: 'manual_tx_124',
      amount_vnd: 1990000,
    })
    await systemApi.addWorldRoomMember({ room_id: 'guild_alpha', member_viewer_id: 'viewer_other' })
    await systemApi.removeWorldRoomMember({ room_id: 'guild_alpha', member_viewer_id: 'viewer_other' })
    await systemApi.rotateWorldRoomInvite({ room_id: 'guild_alpha' })
    await systemApi.joinWorldRoomByInvite({ room_id: 'guild_alpha', invite_code: 'ABCD2345' })

    expect(postMock).toHaveBeenNthCalledWith(1, '/api/v1/command/world-room/update-access', {
      room_id: 'guild_alpha',
      access_mode: 'private',
      viewer_id: 'viewer_test',
    })
    expect(postMock).toHaveBeenNthCalledWith(2, '/api/v1/command/world-room/update-plan', {
      room_id: 'guild_alpha',
      plan_id: 'story_rich_private',
      viewer_id: 'viewer_test',
    })
    expect(postMock).toHaveBeenNthCalledWith(3, '/api/v1/command/world-room/update-entitlement', {
      room_id: 'guild_alpha',
      billing_status: 'active',
      entitled_plan_id: 'story_rich_private',
      viewer_id: 'viewer_test',
    })
    expect(postMock).toHaveBeenNthCalledWith(4, '/api/v1/command/world-room/create-payment-order', {
      room_id: 'guild_alpha',
      target_plan_id: 'story_rich_private',
      viewer_id: 'viewer_test',
    })
    expect(postMock).toHaveBeenNthCalledWith(5, '/api/v1/command/world-room/settle-payment', {
      room_id: 'guild_alpha',
      order_id: 'rpo_1234',
      payment_ref: 'manual_tx_123',
      viewer_id: 'viewer_test',
    })
    expect(postMock).toHaveBeenNthCalledWith(6, '/api/v1/command/world-room/reconcile-payment', {
      transfer_note: 'CWS GUILD_ALPHA RPO_1234',
      payment_ref: 'manual_tx_124',
      amount_vnd: 1990000,
      viewer_id: 'viewer_test',
    })
    expect(postMock).toHaveBeenNthCalledWith(7, '/api/v1/command/world-room/add-member', {
      room_id: 'guild_alpha',
      member_viewer_id: 'viewer_other',
      viewer_id: 'viewer_test',
    })
    expect(postMock).toHaveBeenNthCalledWith(8, '/api/v1/command/world-room/remove-member', {
      room_id: 'guild_alpha',
      member_viewer_id: 'viewer_other',
      viewer_id: 'viewer_test',
    })
    expect(postMock).toHaveBeenNthCalledWith(9, '/api/v1/command/world-room/rotate-invite', {
      room_id: 'guild_alpha',
      viewer_id: 'viewer_test',
    })
    expect(postMock).toHaveBeenNthCalledWith(10, '/api/v1/command/world-room/join-by-invite', {
      room_id: 'guild_alpha',
      invite_code: 'ABCD2345',
      viewer_id: 'viewer_test',
    })
  })
})
