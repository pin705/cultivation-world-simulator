import { describe, it, expect, vi, beforeEach } from 'vitest'
import { routeSocketMessage } from '@/stores/socketMessageRouter'

const { mockMessage } = vi.hoisted(() => ({
  mockMessage: {
    error: vi.fn(),
    warning: vi.fn(),
    success: vi.fn(),
    info: vi.fn(),
  },
}))

vi.mock('@/utils/discreteApi', () => ({
  message: mockMessage,
}))

describe('socketMessageRouter', () => {
  const worldStore = {
    handleTick: vi.fn(),
    initialize: vi.fn().mockResolvedValue(undefined),
  }
  const uiStore = {
    selectedTarget: null as null | { type: string; id: string },
    refreshDetail: vi.fn(),
    openSystemMenu: vi.fn(),
  }
  const systemStore = {
    activeRoomId: 'main',
  }

  beforeEach(() => {
    vi.clearAllMocks()
    uiStore.selectedTarget = null
    systemStore.activeRoomId = 'main'
  })

  it('routes tick message to world and refreshes selected detail', () => {
    uiStore.selectedTarget = { type: 'avatar', id: 'a1' }
    routeSocketMessage(
      { type: 'tick', year: 1, month: 1, events: [], avatars: [] },
      { worldStore: worldStore as any, uiStore: uiStore as any, systemStore: systemStore as any }
    )

    expect(worldStore.handleTick).toHaveBeenCalled()
    expect(uiStore.refreshDetail).toHaveBeenCalled()
  })

  it('opens llm config menu on llm_config_required', () => {
    routeSocketMessage(
      { type: 'llm_config_required', error: 'LLM required' },
      { worldStore: worldStore as any, uiStore: uiStore as any, systemStore: systemStore as any }
    )

    expect(uiStore.openSystemMenu).toHaveBeenCalledWith('llm', false)
    expect(mockMessage.error).toHaveBeenCalledWith('LLM required')
  })

  it('shows toast without switching frontend locale', () => {
    routeSocketMessage(
      { type: 'toast', level: 'info', message: 'ok', language: 'en-US' },
      { worldStore: worldStore as any, uiStore: uiStore as any, systemStore: systemStore as any }
    )

    expect(mockMessage.info).toHaveBeenCalledWith('ok')
  })

  it('renders toast from translation key when provided', () => {
    routeSocketMessage(
      {
        type: 'toast',
        level: 'warning',
        message: 'fallback message',
        render_key: 'ui.control_room_billing_toast_urgent',
        render_params: {
          roomId: 'guild_alpha',
          days: 2,
          date: '2026-04-20',
        },
      },
      { worldStore: worldStore as any, uiStore: uiStore as any, systemStore: systemStore as any }
    )

    expect(mockMessage.warning).toHaveBeenCalledOnce()
    const rendered = mockMessage.warning.mock.calls[0]?.[0]
    expect(typeof rendered).toBe('string')
    expect(rendered).not.toBe('fallback message')
  })

  it('ignores tick messages from a different room', () => {
    routeSocketMessage(
      { type: 'tick', room_id: 'guild_beta', year: 1, month: 1, events: [], avatars: [] },
      { worldStore: worldStore as any, uiStore: uiStore as any, systemStore: systemStore as any }
    )

    expect(worldStore.handleTick).not.toHaveBeenCalled()
  })
})
