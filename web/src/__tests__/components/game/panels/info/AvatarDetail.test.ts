import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { defineComponent, h } from 'vue'
import AvatarDetail from '@/components/game/panels/info/AvatarDetail.vue'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'

const entityRowSpy = vi.fn()

vi.mock('@/components/game/panels/info/components/EntityRow.vue', () => ({
  default: defineComponent({
    name: 'EntityRow',
    props: ['item', 'meta', 'compact', 'detailsBelow'],
    emits: ['click'],
    setup(props) {
      entityRowSpy(props)
      return () => h('div', { class: 'entity-row-stub' }, props.item?.name || '')
    },
  }),
}))

describe('AvatarDetail', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    entityRowSpy.mockClear()
  })

  const i18n = createI18n({
    legacy: false,
    locale: 'zh-CN',
    messages: {
      'zh-CN': {
        game: {
          info_panel: {
            avatar: {
              empty_short: '-',
              set_objective: 'Set Objective',
              set_main_avatar: 'Set Main Avatar',
              grant_support: 'Grant Support',
              appoint_seed: 'Appoint Seed',
              clear_objective: 'Clear Objective',
              control_unclaimed: 'Claim a sect first',
              control_foreign_sect: 'Avatar is outside owned sect {sect}',
              control_owned_member: 'Avatar belongs to owned sect {sect}',
              control_main_avatar: 'Avatar is already the main disciple',
              main_avatar_ready: 'Ready to become main disciple',
              main_avatar_current: 'Main disciple already assigned here',
              objective_requires_main_avatar: 'Only the main disciple can change objectives: {name}',
              long_term_objective: 'Long-term Objective',
              objective_ready: 'Objective ready',
              objective_cooldown: 'Objective cooldown: {months} months',
              objective_budget: 'Objective budget: {points}/{max} · cost {cost}',
              objective_insufficient_budget: 'Insufficient intervention points: need {cost}, have {points}',
              support_ready: 'Support ready',
              support_cooldown: 'Support cooldown: {months} months',
              support_budget: 'Grant {amount} stones · cost {cost}',
              support_insufficient_budget: 'Insufficient intervention points: need {cost}, have {points}',
              seed_ready: 'Seed ready',
              seed_active: 'Seed active: {months} months remaining',
              seed_cooldown: 'Seed cooldown: {months} months',
              seed_budget: 'Seed lasts {duration} months · cost {cost}',
              seed_no_sect: 'Only sect members can become seed disciples',
              seed_insufficient_budget: 'Insufficient intervention points: need {cost}, have {points}',
              short_term_objective: 'Short-term Objective',
              portrait: {
                entry: 'Change Portrait',
                preview_alt: 'Portrait Preview',
              },
              dead_with_reason: 'Dead ({reason})',
              modals: {
                support_confirm: 'Grant {amount} stones?',
                support_failed: 'Support failed',
                seed_confirm: 'Mark as seed disciple for {months} months?',
                seed_failed: 'Seed failed',
                set_main_confirm: 'Set as main disciple?',
                set_main_failed: 'Set main failed',
                set_long_term: 'Set Long Term Objective',
                placeholder: 'Enter objective...',
                set_failed: 'Set failed',
                clear_confirm: 'Clear objective?',
              },
              stats: {
                realm: 'Realm',
                age: 'Age',
                origin: 'Origin',
                hp: 'HP',
                gender: 'Gender',
                alignment: 'Alignment',
                sect: 'Sect',
                rogue: 'Rogue',
                official_rank: 'Official Rank',
                sect_contribution: 'Sect Contribution',
                root: 'Root',
                luck: 'Luck',
                magic_stone: 'Spirit Stone',
                appearance: 'Appearance',
                battle_strength: 'Battle Strength',
                emotion: 'Emotion',
              },
              sections: {
                traits: 'Traits',
                techniques_equipment: 'Arts & Gear',
                goldfinger: 'Goldfinger',
                relations: 'Relations',
                current_effects: 'Current Effects',
              },
              adjust: {
                entry: 'Adjust',
                empty_item: 'No {label}',
                categories: {
                  personas: 'Traits',
                  technique: 'Technique',
                  weapon: 'Weapon',
                  auxiliary: 'Auxiliary',
                  goldfinger: 'Goldfinger',
                },
              },
              father_short: 'Father',
              mother_short: 'Mother',
              mortal_realm: 'Mortal',
            }
          }
        },
        common: {
          none: 'None'
        },
        ui: {
          create_avatar: {
            gender_labels: {
              male: 'Male',
              female: 'Female',
            },
          },
          other: 'Other',
        },
      }
    }
  })

  const mockAvatarData = {
    id: 'avatar_1',
    name: 'Test Avatar',
    realm: 'Foundation',
    pic_id: 7,
    level: 1,
    age: 20,
    lifespan: 100,
    origin: 'Test Origin',
    hp: { cur: 100, max: 100 },
    gender: 'Male',
    alignment: 'Good',
    root: 'Gold',
    luck: 0,
    magic_stone: 0,
    appearance: 'Plain',
    base_battle_strength: 10,
    emotion: { emoji: '😀', name: 'Happy' },
    player_owned_sect_id: 1,
    player_owned_sect_name: 'Test Sect',
    is_player_owned_avatar: true,
    is_player_main_avatar: true,
    player_can_set_main_avatar: false,
    is_dead: false,
    current_effects: '',
    personas: [],
    materials: [],
    goldfinger: undefined,
    traits: [],
    items: [],
    skills: [],
    events: [],
    relations: [],
  }

  it('should render successfully', () => {
    const wrapper = mount(AvatarDetail, {
      props: {
        data: mockAvatarData as any
      },
      global: {
        plugins: [
          createPinia(),
          i18n
        ],
        stubs: {
          StatItem: true,
          RelationRow: true,
          TagList: true,
          SecondaryPopup: true,
          AvatarAdjustPanel: true,
          AvatarPortraitPanel: true,
        }
      }
    })

    expect(wrapper.exists()).toBe(true)
    // Check if the actions bar exists since it's not dead
    expect(wrapper.find('.actions-bar').exists()).toBe(true)
    expect(wrapper.find('.avatar-header').exists()).toBe(true)
    expect(wrapper.find('.portrait-button').exists()).toBe(true)
  })

  it('should display dead banner if avatar is dead', () => {
    const deadAvatar = { ...mockAvatarData, is_dead: true, death_info: { reason: 'Old age' } }
    const wrapper = mount(AvatarDetail, {
      props: {
        data: deadAvatar as any
      },
      global: {
        plugins: [
          createPinia(),
          i18n
        ],
        stubs: {
          StatItem: true,
          RelationRow: true,
          TagList: true,
          SecondaryPopup: true,
          AvatarAdjustPanel: true,
          AvatarPortraitPanel: true,
        }
      }
    })

    expect(wrapper.find('.dead-banner').exists()).toBe(true)
    expect(wrapper.find('.actions-bar').exists()).toBe(false)
  })

  it('renders identity and non-stranger attitude on separate lines', () => {
    const relationAvatar = {
      ...mockAvatarData,
      relations: [
        {
          target_id: 'avatar_2',
          name: '青岚',
          relation: '道侣 / 友好',
          relation_type: 'lovers',
          identity_relations: ['lovers'],
          numeric_relation: 'friend',
          friendliness: 12,
          realm: '金丹后期',
          sect: '凌霄剑宗',
        },
        {
          target_id: 'avatar_3',
          name: '丹七杀',
          relation: '陌生',
          relation_type: '',
          identity_relations: [],
          numeric_relation: 'stranger',
          friendliness: 0,
          realm: '金丹后期',
          sect: '金丹后期',
        },
      ],
    }

    const wrapper = mount(AvatarDetail, {
      props: {
        data: relationAvatar as any,
      },
      global: {
        plugins: [
          createPinia(),
          i18n,
        ],
        directives: {
          sound: () => {},
        },
        stubs: {
          StatItem: true,
          TagList: true,
          SecondaryPopup: true,
          AvatarAdjustPanel: true,
          AvatarPortraitPanel: true,
        },
      },
    })

    expect(wrapper.text()).toContain('道侣')
    expect(wrapper.text()).toContain('友好（12）')
    expect(wrapper.text()).not.toContain('态度：陌生')
    expect(wrapper.text()).not.toContain('身份：')
    expect(wrapper.text()).not.toContain('态度：')
    expect(wrapper.text()).not.toContain('丹七杀')
  })

  it('renders long effect sources as separate rows with segmented content', () => {
    const effectAvatar = {
      ...mockAvatarData,
      current_effects: '[Orthodoxy [Nature]] Special Ability Respiration Refinement Success Rate +15.0%; Battle Strength +20\n[Heaven and Earth Phenomenon] Respiration Experience +20',
    }

    const wrapper = mount(AvatarDetail, {
      props: {
        data: effectAvatar as any,
      },
      global: {
        plugins: [
          createPinia(),
          i18n,
        ],
        directives: {
          sound: () => {},
        },
        stubs: {
          StatItem: true,
          RelationRow: true,
          TagList: true,
          SecondaryPopup: true,
          AvatarAdjustPanel: true,
          AvatarPortraitPanel: true,
        },
      },
    })

    const rows = wrapper.findAll('.effect-row')
    expect(rows).toHaveLength(2)
    expect(rows[0].find('.effect-source').text()).toBe('Orthodoxy [Nature]')
    expect(rows[0].find('.effect-content').text()).toContain('Special Ability Respiration Refinement Success Rate +15.0%')
    expect(rows[0].find('.effect-content').text()).toContain('Battle Strength +20')
    expect(rows[1].find('.effect-source').text()).toBe('Heaven and Earth Phenomenon')
  })

  it('renders goldfinger entry when present', () => {
    const wrapper = mount(AvatarDetail, {
      props: {
        data: {
          ...mockAvatarData,
          goldfinger: {
            id: '1',
            name: '气运之子',
            desc: '天命偏爱，机缘主动靠近',
            effect_desc: '气运 +20',
          },
        } as any,
      },
      global: {
        plugins: [
          createPinia(),
          i18n,
        ],
        directives: {
          sound: () => {},
        },
        stubs: {
          StatItem: true,
          RelationRow: true,
          TagList: true,
          SecondaryPopup: true,
          AvatarAdjustPanel: true,
          AvatarPortraitPanel: true,
        },
      },
    })

    expect(wrapper.text()).toContain('Goldfinger')
    expect(wrapper.findAll('.equipment-slot-block')).toHaveLength(4)
    expect(entityRowSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        item: expect.objectContaining({
          name: '气运之子',
          desc: '天命偏爱，机缘主动靠近',
        }),
      }),
    )
  })

  it('passes goldfinger category and current item into adjust panel when clicking edit', async () => {
    let capturedProps: Record<string, unknown> | null = null
    const AvatarAdjustPanelStub = defineComponent({
      name: 'AvatarAdjustPanel',
      props: ['avatarId', 'category', 'currentItem', 'currentPersonas'],
      setup(props) {
        capturedProps = props as unknown as Record<string, unknown>
        return () => h('div', { class: 'adjust-panel-stub' })
      },
    })

    const wrapper = mount(AvatarDetail, {
      props: {
        data: {
          ...mockAvatarData,
          goldfinger: {
            id: '1',
            name: '气运之子',
            desc: '天命眷顾',
            effect_desc: '气运 +20',
          },
        } as any,
      },
      global: {
        plugins: [
          createPinia(),
          i18n,
        ],
        directives: {
          sound: () => {},
        },
        stubs: {
          StatItem: true,
          RelationRow: true,
          TagList: true,
          SecondaryPopup: true,
          AvatarAdjustPanel: AvatarAdjustPanelStub,
          AvatarPortraitPanel: true,
        },
      },
    })

    const adjustButtons = wrapper.findAll('button.adjust-btn.inline')
    expect(adjustButtons).toHaveLength(4)

    await adjustButtons[3].trigger('click')

    expect(capturedProps).not.toBeNull()
    expect(capturedProps?.category).toBe('goldfinger')
    expect(capturedProps?.currentItem).toMatchObject({
      id: '1',
      name: '气运之子',
    })
  })

  it('shows objective cooldown and disables updates while locked', () => {
    const wrapper = mount(AvatarDetail, {
      props: {
        data: {
          ...mockAvatarData,
          player_objective_remaining_cooldown_months: 4,
          player_intervention_points: 2,
          player_intervention_points_max: 3,
          player_objective_cost: 1,
          player_objective_can_update: false,
          player_support_remaining_cooldown_months: 0,
          player_support_cost: 1,
          player_support_amount: 200,
          player_support_can_grant: true,
          player_seed_remaining_cooldown_months: 0,
          player_seed_remaining_duration_months: 0,
          player_seed_cost: 1,
          player_seed_duration_months: 36,
          player_seed_can_appoint: false,
        } as any,
      },
      global: {
        plugins: [createPinia(), i18n],
        stubs: {
          StatItem: true,
          RelationRow: true,
          TagList: true,
          SecondaryPopup: true,
          AvatarAdjustPanel: true,
          AvatarPortraitPanel: true,
        },
      },
    })

    expect(wrapper.text()).toContain('Objective cooldown: 4 months')
    expect(wrapper.text()).toContain('Objective budget: 2/3 · cost 1')
    expect(wrapper.text()).toContain('Support ready')
    expect(wrapper.text()).toContain('Grant 200 stones · cost 1')
    expect(wrapper.text()).toContain('Only sect members can become seed disciples')
    expect(wrapper.text()).toContain('Seed lasts 36 months · cost 1')
    expect(wrapper.find('.actions-bar .btn.primary').attributes('disabled')).toBeDefined()
  })

  it('shows objective budget lock when intervention points are depleted', () => {
    const wrapper = mount(AvatarDetail, {
      props: {
        data: {
          ...mockAvatarData,
          player_objective_remaining_cooldown_months: 0,
          player_intervention_points: 0,
          player_intervention_points_max: 3,
          player_objective_cost: 1,
          player_objective_can_update: false,
          player_support_remaining_cooldown_months: 0,
          player_support_cost: 1,
          player_support_amount: 200,
          player_support_can_grant: false,
          player_seed_remaining_cooldown_months: 0,
          player_seed_remaining_duration_months: 0,
          player_seed_cost: 1,
          player_seed_duration_months: 36,
          player_seed_can_appoint: false,
        } as any,
      },
      global: {
        plugins: [createPinia(), i18n],
        stubs: {
          StatItem: true,
          RelationRow: true,
          TagList: true,
          SecondaryPopup: true,
          AvatarAdjustPanel: true,
          AvatarPortraitPanel: true,
        },
      },
    })

    expect(wrapper.text()).toContain('Objective ready')
    expect(wrapper.text()).toContain('Objective budget: 0/3 · cost 1')
    expect(wrapper.text()).toContain('Grant 200 stones · cost 1')
    expect(wrapper.text()).toContain('Seed lasts 36 months · cost 1')
    expect(wrapper.find('.actions-bar .btn.primary').attributes('disabled')).toBeDefined()
    expect(wrapper.findAll('.actions-bar .btn')[2].attributes('disabled')).toBeDefined()
  })

  it('shows support cooldown state and disables support button while locked', () => {
    const wrapper = mount(AvatarDetail, {
      props: {
        data: {
          ...mockAvatarData,
          player_objective_remaining_cooldown_months: 0,
          player_intervention_points: 2,
          player_intervention_points_max: 3,
          player_objective_cost: 1,
          player_support_remaining_cooldown_months: 5,
          player_support_cost: 1,
          player_support_amount: 200,
          player_support_can_grant: false,
          player_seed_remaining_cooldown_months: 0,
          player_seed_remaining_duration_months: 0,
          player_seed_cost: 1,
          player_seed_duration_months: 36,
          player_seed_can_appoint: false,
        } as any,
      },
      global: {
        plugins: [createPinia(), i18n],
        stubs: {
          StatItem: true,
          RelationRow: true,
          TagList: true,
          SecondaryPopup: true,
          AvatarAdjustPanel: true,
          AvatarPortraitPanel: true,
        },
      },
    })

    expect(wrapper.text()).toContain('Support cooldown: 5 months')
    expect(wrapper.text()).toContain('Grant 200 stones · cost 1')
    expect(wrapper.findAll('.actions-bar .btn')[2].attributes('disabled')).toBeDefined()
  })

  it('shows seed status for sect members and disables seed action during cooldown', () => {
    const wrapper = mount(AvatarDetail, {
      props: {
        data: {
          ...mockAvatarData,
          sect: {
            id: 'sect_1',
            name: 'Test Sect',
            alignment: 'Good',
            style: 'Sword',
            hq_name: 'HQ',
            hq_desc: 'HQ desc',
            rank: 'Disciple',
          },
          player_objective_remaining_cooldown_months: 0,
          player_intervention_points: 2,
          player_intervention_points_max: 3,
          player_objective_cost: 1,
          player_support_remaining_cooldown_months: 0,
          player_support_cost: 1,
          player_support_amount: 200,
          player_support_can_grant: true,
          player_seed_remaining_cooldown_months: 4,
          player_seed_remaining_duration_months: 20,
          player_seed_cost: 1,
          player_seed_duration_months: 36,
          player_seed_can_appoint: false,
        } as any,
      },
      global: {
        plugins: [createPinia(), i18n],
        stubs: {
          StatItem: true,
          RelationRow: true,
          TagList: true,
          SecondaryPopup: true,
          AvatarAdjustPanel: true,
          AvatarPortraitPanel: true,
        },
      },
    })

    expect(wrapper.text()).toContain('Seed active: 20 months remaining')
    expect(wrapper.text()).toContain('Seed lasts 36 months · cost 1')
    expect(wrapper.findAll('.actions-bar .btn')[3].attributes('disabled')).toBeDefined()
  })
})
