import { beforeEach, describe, expect, it, vi } from 'vitest'

const getMock = vi.fn()
const postMock = vi.fn()

vi.mock('@/api/http', () => ({
  httpClient: {
    get: getMock,
    post: postMock,
  },
}))

describe('avatarApi', () => {
  beforeEach(() => {
    window.localStorage.clear()
    window.localStorage.setItem('cws_viewer_id', 'viewer_test')
    getMock.mockReset()
    postMock.mockReset()
  })

  it('fetches avatar adjust options from the dedicated endpoint', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    getMock.mockResolvedValue({ techniques: [], weapons: [], auxiliaries: [], personas: [], goldfingers: [] })

    await avatarApi.fetchAvatarAdjustOptions()

    expect(getMock).toHaveBeenCalledWith('/api/v1/query/meta/avatar-adjust-options')
  })

  it('posts avatar adjustment payloads through the unified endpoint', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    postMock.mockResolvedValue({ status: 'ok' })

    await avatarApi.updateAvatarAdjustment({
      avatar_id: 'avatar_1',
      category: 'personas',
      persona_ids: [1, 2, 3],
    })

    expect(postMock).toHaveBeenCalledWith('/api/v1/command/avatar/update-adjustment', {
      avatar_id: 'avatar_1',
      category: 'personas',
      persona_ids: [1, 2, 3],
    })
  })

  it('posts goldfinger adjustment payloads through the unified endpoint', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    postMock.mockResolvedValue({ status: 'ok' })

    await avatarApi.updateAvatarAdjustment({
      avatar_id: 'avatar_1',
      category: 'goldfinger',
      target_id: 930001,
    })

    expect(postMock).toHaveBeenCalledWith('/api/v1/command/avatar/update-adjustment', {
      avatar_id: 'avatar_1',
      category: 'goldfinger',
      target_id: 930001,
    })
  })

  it('posts avatar portrait update payloads through the dedicated endpoint', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    postMock.mockResolvedValue({ status: 'ok' })

    await avatarApi.updateAvatarPortrait({
      avatar_id: 'avatar_1',
      pic_id: 12,
    })

    expect(postMock).toHaveBeenCalledWith('/api/v1/command/avatar/update-portrait', {
      avatar_id: 'avatar_1',
      pic_id: 12,
    })
  })

  it('posts custom content generation requests', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    postMock.mockResolvedValue({ status: 'ok', draft: {} })

    await avatarApi.generateCustomContent({
      category: 'weapon',
      realm: 'CORE_FORMATION',
      user_prompt: '想要一把金丹剑',
    })

    expect(postMock).toHaveBeenCalledWith('/api/v1/command/avatar/generate-custom-content', {
      category: 'weapon',
      realm: 'CORE_FORMATION',
      user_prompt: '想要一把金丹剑',
    })
  })

  it('posts custom goldfinger generation requests without realm', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    postMock.mockResolvedValue({ status: 'ok', draft: {} })

    await avatarApi.generateCustomContent({
      category: 'goldfinger',
      user_prompt: '想要一个偏签到流的外挂',
    })

    expect(postMock).toHaveBeenCalledWith('/api/v1/command/avatar/generate-custom-content', {
      category: 'goldfinger',
      user_prompt: '想要一个偏签到流的外挂',
    })
  })

  it('posts custom content creation requests', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    postMock.mockResolvedValue({ status: 'ok', item: {} })

    await avatarApi.createCustomContent({
      category: 'auxiliary',
      draft: {
        id: '0',
        category: 'auxiliary',
        realm: 'CORE_FORMATION',
        name: '草稿',
        effects: { extra_max_hp: 30 },
      } as any,
    })

    expect(postMock).toHaveBeenCalledWith('/api/v1/command/avatar/create-custom-content', {
      category: 'auxiliary',
      draft: {
        id: '0',
        category: 'auxiliary',
        realm: 'CORE_FORMATION',
        name: '草稿',
        effects: { extra_max_hp: 30 },
      },
    })
  })

  it('allows technique custom generation without realm', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    postMock.mockResolvedValue({ status: 'ok', draft: {} })

    await avatarApi.generateCustomContent({
      category: 'technique',
      user_prompt: '我想要一本偏火属性的功法',
    })

    expect(postMock).toHaveBeenCalledWith('/api/v1/command/avatar/generate-custom-content', {
      category: 'technique',
      user_prompt: '我想要一本偏火属性的功法',
    })
  })

  it('fetches avatar meta from /api/v1', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    getMock.mockResolvedValue({ males: [1, 2], females: [3, 4] })

    await avatarApi.fetchAvatarMeta()

    expect(getMock).toHaveBeenCalledWith('/api/v1/query/meta/avatars')
  })

  it('fetches detail info with viewer identity in query string', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    getMock.mockResolvedValue({ id: 'avatar_1' })

    await avatarApi.fetchDetailInfo({ type: 'avatar', id: 'avatar_1' })

    expect(getMock).toHaveBeenCalledWith('/api/v1/query/detail?type=avatar&id=avatar_1&viewer_id=viewer_test')
  })

  it('posts avatar objective commands with viewer identity', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    postMock.mockResolvedValue({ status: 'ok' })

    await avatarApi.setLongTermObjective('avatar_1', '先稳固根基，再寻机突破')
    await avatarApi.clearLongTermObjective('avatar_1')

    expect(postMock).toHaveBeenNthCalledWith(1, '/api/v1/command/avatar/set-long-term-objective', {
      avatar_id: 'avatar_1',
      content: '先稳固根基，再寻机突破',
      viewer_id: 'viewer_test',
    })
    expect(postMock).toHaveBeenNthCalledWith(2, '/api/v1/command/avatar/clear-long-term-objective', {
      avatar_id: 'avatar_1',
      viewer_id: 'viewer_test',
    })
  })

  it('posts avatar support requests through the dedicated endpoint', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    postMock.mockResolvedValue({ status: 'ok' })

    await avatarApi.grantSupport({ avatar_id: 'avatar_1' })

    expect(postMock).toHaveBeenCalledWith('/api/v1/command/avatar/grant-support', {
      avatar_id: 'avatar_1',
      viewer_id: 'viewer_test',
    })
  })

  it('posts avatar seed appointment requests through the dedicated endpoint', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    postMock.mockResolvedValue({ status: 'ok' })

    await avatarApi.appointSeed({ avatar_id: 'avatar_1' })

    expect(postMock).toHaveBeenCalledWith('/api/v1/command/avatar/appoint-seed', {
      avatar_id: 'avatar_1',
      viewer_id: 'viewer_test',
    })
  })

  it('posts main avatar selection requests through the dedicated endpoint', async () => {
    const { avatarApi } = await import('@/api/modules/avatar')
    postMock.mockResolvedValue({ status: 'ok' })

    await avatarApi.setMainAvatar({ avatar_id: 'avatar_1' })

    expect(postMock).toHaveBeenCalledWith('/api/v1/command/player/set-main-avatar', {
      avatar_id: 'avatar_1',
      viewer_id: 'viewer_test',
    })
  })
})
