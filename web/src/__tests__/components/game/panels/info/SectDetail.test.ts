import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import SectDetail from '@/components/game/panels/info/SectDetail.vue'

function createTestI18n() {
  return createI18n({
    legacy: false,
    locale: 'en-US',
    messages: {
      'en-US': {
        common: {
          none: 'None',
          confirm: 'Confirm',
          cancel: 'Cancel',
        },
        game: {
          sect_relations: {
            status_war: 'War',
            status_peace: 'Peace',
          },
          info_panel: {
            sect: {
              claim_sect: 'Claim Sect',
              set_directive: 'Set Directive',
              clear_directive: 'Clear Directive',
              stats: {
                alignment: 'Alignment',
                orthodoxy: 'Orthodoxy',
                style: 'Style',
                preferred: 'Preferred Weapon',
                members: 'Members',
                total_battle_strength: 'Total Battle Strength',
                war_status: 'War Status',
                strongest_enemy: 'Strongest Enemy',
                income: 'Income',
                income_value: '{income}/turn',
                upkeep: 'Upkeep',
                upkeep_value: '{upkeep}/turn',
                war_weariness: 'War Weariness',
                magic_stone: 'Magic Stone',
              },
              sections: {
                control: 'Control',
                intro: 'Intro',
                rule: 'Rule',
                directive: 'Directive',
                hq: 'HQ - {name}',
                bonus: 'Bonus',
                diplomacy: 'Diplomacy',
                thinking: 'Sect Thinking',
                techniques: 'Techniques',
                members: 'Members',
              },
              diplomacy_meta_relation: 'Relation value {value}',
              diplomacy_war_years: 'At war for {count} years',
              diplomacy_peace_years: 'At peace for {count} years',
              directive_ready: 'Directive ready',
              directive_cooldown: 'Directive cooldown: {months} months',
              directive_budget: 'Directive budget: {points}/{max} · cost {cost}',
              directive_insufficient_budget: 'Insufficient intervention points: need {cost}, have {points}',
              control_owned: 'You own this sect',
              control_claimable: 'You can claim this sect',
              control_locked_other: 'You already own {name}',
              intervene_relation_ease: 'Ease Relation',
              intervene_relation_escalate: 'Escalate Relation',
              relation_intervention_ready: 'Relation intervention ready: {delta} / {cost}',
              relation_intervention_cooldown: 'Relation intervention cooldown: {months} months',
              relation_intervention_insufficient_budget: 'Need {cost}, have {points}',
              no_bonus: 'No bonus',
              no_directive: 'No directive',
              no_rule: 'No rule',
              no_runtime_effect: 'No active runtime effect',
              runtime_effect_meta: '{source} remains for {months} months',
              runtime_effect_meta_permanent: '{source} is permanent',
              modals: {
                claim_confirm: 'Claim this sect?',
                claim_failed: 'Claim failed',
                set_directive: 'Set Sect Directive',
                directive_placeholder: 'Enter directive...',
                directive_set_failed: 'Failed to set directive',
                directive_clear_confirm: 'Clear current directive?',
                relation_intervention_failed: 'Relation intervention failed',
              },
            },
          },
        },
      },
    },
  })
}

describe('SectDetail', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render successfully', () => {
    const i18n = createTestI18n()
    const wrapper = mount(SectDetail, {
      props: {
        data: {
          id: '1',
          name: 'Test Sect',
          alignment: 'Good',
          member_count: 10,
          desc: 'Test',
          style: 'Sword',
          preferred_weapon: 'Sword',
          members: [],
          orthodoxy: null,
          techniques: [],
          hq_name: 'HQ',
          hq_desc: 'HQ desc',
          effect_desc: '',
          total_battle_strength: 0,
          magic_stone: 0,
          runtime_effect_items: [],
          war_weariness: 0,
          diplomacy_items: [],
          periodic_thinking: '',
          player_directive: '',
          player_can_claim_sect: true,
          war_summary: {
            active_war_count: 0,
            peace_count: 0,
            strongest_enemy_name: '',
            strongest_enemy_relation: 0,
          },
          economy_summary: {
            current_magic_stone: 0,
            effective_income_per_tile: 0,
            controlled_tile_income: 0,
            estimated_yearly_income: 0,
            estimated_yearly_upkeep: 0,
          },
        } as any,
      },
      global: {
        plugins: [createPinia(), i18n],
        directives: {
          sound: () => {},
        },
        stubs: {
          StatItem: true,
          EntityRow: true,
          TagList: true,
        },
      },
    })

    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('.actions-bar').exists()).toBe(true)
  })

  it('displays stats and runtime sect effects', () => {
    const i18n = createTestI18n()
    const data = {
      id: '1',
      name: 'Test Sect',
      alignment: 'Good',
      desc: 'Intro',
      style: 'Sword',
      hq_name: 'HQ',
      hq_desc: 'HQ desc',
      effect_desc: 'Sect bonus',
      preferred_weapon: 'Sword',
      members: [],
      orthodoxy: null,
      techniques: [],
      magic_stone: 100,
      is_active: true,
      total_battle_strength: 2500.7,
      color: '#ff0000',
      runtime_effect_items: [
        {
          source: 'sect_random_event',
          source_label: 'Sect random event',
          desc: 'Extra income per tile +0.8',
          remaining_months: 60,
          is_permanent: false,
        },
      ],
      war_weariness: 23,
      war_summary: {
        active_war_count: 1,
        peace_count: 1,
        strongest_enemy_name: 'Enemy Sect',
        strongest_enemy_relation: -12,
      },
      economy_summary: {
        current_magic_stone: 100,
        effective_income_per_tile: 10,
        controlled_tile_income: 850.4,
        estimated_yearly_income: 850,
        estimated_yearly_upkeep: 120,
      },
      diplomacy_items: [
        {
          other_sect_id: 2,
          other_sect_name: 'Enemy Sect',
          status: 'war',
          duration_months: 18,
          war_months: 18,
          peace_months: 0,
          relation_value: -12,
          player_relation_intervention_remaining_cooldown_months: 0,
        },
        {
          other_sect_id: 3,
          other_sect_name: 'Neutral Sect',
          status: 'peace',
          duration_months: 36,
          war_months: 0,
          peace_months: 36,
          relation_value: 0,
          player_relation_intervention_remaining_cooldown_months: 0,
        },
      ],
      periodic_thinking: '我宗观天下势力分化加剧，当先稳住边界与资源脉络，再图联盟突破，以争中局主动。',
      player_directive: 'Hold the borders before expanding.',
      is_player_owned_sect: true,
      player_directive_can_update: true,
      player_relation_intervention_cost: 1,
      player_relation_intervention_delta: 18,
    }

    const wrapper = mount(SectDetail, {
      props: { data },
      global: {
        plugins: [createPinia(), i18n],
        directives: {
          sound: () => {},
        },
        stubs: {
          SecondaryPopup: true,
          StatItem: false,
          EntityRow: true,
          RelationRow: false,
          TagList: true,
        },
      },
    })

    const text = wrapper.text()
    expect(text).toContain('100')
    expect(text).toContain('2500')
    expect(text).toContain('War')
    expect(text).toContain('Enemy Sect')
    expect(text).toContain('850/turn')
    expect(text).toContain('120/turn')
    expect(text).toContain('23/100')
    expect(text).toContain('Extra income per tile +0.8')
    expect(text).toContain('Sect random event remains for 60 months')
    expect(text).toContain('At war for 1 years')
    expect(text).toContain('Neutral Sect')
    expect(text).toContain('At peace for 3 years')
    expect(text).toContain('我宗观天下势力分化加剧')
    expect(text).toContain('Hold the borders before expanding.')
    expect(text).toContain('Ease Relation')
    expect(text).toContain('Escalate Relation')
    expect(text).not.toContain('18 months')
  })

  it('opens directive modal from the action bar', async () => {
    const i18n = createTestI18n()
    const wrapper = mount(SectDetail, {
      props: {
        data: {
          id: '1',
          name: 'Test Sect',
          alignment: 'Good',
          desc: 'Test',
          style: 'Sword',
          preferred_weapon: 'Sword',
          members: [],
          orthodoxy: null,
          techniques: [],
          hq_name: 'HQ',
          hq_desc: 'HQ desc',
          effect_desc: '',
          total_battle_strength: 0,
          magic_stone: 0,
          runtime_effect_items: [],
          war_weariness: 0,
          diplomacy_items: [],
          periodic_thinking: '',
          player_directive: 'Guard the frontier.',
          is_player_owned_sect: true,
          player_directive_can_update: true,
          war_summary: {
            active_war_count: 0,
            peace_count: 0,
            strongest_enemy_name: '',
            strongest_enemy_relation: 0,
          },
          economy_summary: {
            current_magic_stone: 0,
            effective_income_per_tile: 0,
            controlled_tile_income: 0,
            estimated_yearly_income: 0,
            estimated_yearly_upkeep: 0,
          },
        } as any,
      },
      global: {
        plugins: [createPinia(), i18n],
        directives: {
          sound: () => {},
        },
        stubs: {
          SecondaryPopup: true,
          StatItem: true,
          EntityRow: true,
          RelationRow: true,
        },
      },
    })

    await wrapper.find('.actions-bar .btn.primary').trigger('click')

    expect(wrapper.find('.modal-overlay').exists()).toBe(true)
    expect((wrapper.find('textarea').element as HTMLTextAreaElement).value).toBe('Guard the frontier.')
  })

  it('shows directive cooldown state and disables updates while locked', () => {
    const i18n = createTestI18n()
    const wrapper = mount(SectDetail, {
      props: {
        data: {
          id: '1',
          name: 'Test Sect',
          alignment: 'Good',
          desc: 'Test',
          style: 'Sword',
          preferred_weapon: 'Sword',
          members: [],
          orthodoxy: null,
          techniques: [],
          hq_name: 'HQ',
          hq_desc: 'HQ desc',
          effect_desc: '',
          total_battle_strength: 0,
          magic_stone: 0,
          runtime_effect_items: [],
          war_weariness: 0,
          diplomacy_items: [],
          periodic_thinking: '',
          player_directive: '',
          player_directive_remaining_cooldown_months: 6,
          player_intervention_points: 2,
          player_intervention_points_max: 3,
          player_directive_cost: 1,
          is_player_owned_sect: true,
          player_directive_can_update: false,
          war_summary: {
            active_war_count: 0,
            peace_count: 0,
            strongest_enemy_name: '',
            strongest_enemy_relation: 0,
          },
          economy_summary: {
            current_magic_stone: 0,
            effective_income_per_tile: 0,
            controlled_tile_income: 0,
            estimated_yearly_income: 0,
            estimated_yearly_upkeep: 0,
          },
        } as any,
      },
      global: {
        plugins: [createPinia(), i18n],
        directives: {
          sound: () => {},
        },
        stubs: {
          SecondaryPopup: true,
          StatItem: true,
          EntityRow: true,
          RelationRow: true,
        },
      },
    })

    expect(wrapper.text()).toContain('Directive cooldown: 6 months')
    expect(wrapper.text()).toContain('Directive budget: 2/3 · cost 1')
    expect(wrapper.find('.actions-bar .btn.primary').attributes('disabled')).toBeDefined()
  })

  it('shows directive budget lock when intervention points are depleted', () => {
    const i18n = createTestI18n()
    const wrapper = mount(SectDetail, {
      props: {
        data: {
          id: '1',
          name: 'Test Sect',
          alignment: 'Good',
          desc: 'Test',
          style: 'Sword',
          preferred_weapon: 'Sword',
          members: [],
          orthodoxy: null,
          techniques: [],
          hq_name: 'HQ',
          hq_desc: 'HQ desc',
          effect_desc: '',
          total_battle_strength: 0,
          magic_stone: 0,
          runtime_effect_items: [],
          war_weariness: 0,
          diplomacy_items: [],
          periodic_thinking: '',
          player_directive: '',
          player_directive_remaining_cooldown_months: 0,
          player_intervention_points: 0,
          player_intervention_points_max: 3,
          player_directive_cost: 1,
          is_player_owned_sect: true,
          player_directive_can_update: false,
          war_summary: {
            active_war_count: 0,
            peace_count: 0,
            strongest_enemy_name: '',
            strongest_enemy_relation: 0,
          },
          economy_summary: {
            current_magic_stone: 0,
            effective_income_per_tile: 0,
            controlled_tile_income: 0,
            estimated_yearly_income: 0,
            estimated_yearly_upkeep: 0,
          },
        } as any,
      },
      global: {
        plugins: [createPinia(), i18n],
        directives: {
          sound: () => {},
        },
        stubs: {
          SecondaryPopup: true,
          StatItem: true,
          EntityRow: true,
          RelationRow: true,
        },
      },
    })

    expect(wrapper.text()).toContain('Directive ready')
    expect(wrapper.text()).toContain('Directive budget: 0/3 · cost 1')
    expect(wrapper.find('.actions-bar .btn.primary').attributes('disabled')).toBeDefined()
  })

  it('shows relation intervention cooldown for diplomacy items', () => {
    const i18n = createTestI18n()
    const wrapper = mount(SectDetail, {
      props: {
        data: {
          id: '1',
          name: 'Test Sect',
          alignment: 'Good',
          desc: 'Test',
          style: 'Sword',
          preferred_weapon: 'Sword',
          members: [],
          orthodoxy: null,
          techniques: [],
          hq_name: 'HQ',
          hq_desc: 'HQ desc',
          effect_desc: '',
          total_battle_strength: 0,
          magic_stone: 0,
          runtime_effect_items: [],
          war_weariness: 0,
          diplomacy_items: [
            {
              other_sect_id: 2,
              other_sect_name: 'Enemy Sect',
              status: 'war',
              duration_months: 12,
              war_months: 12,
              peace_months: 0,
              relation_value: -20,
              player_relation_intervention_remaining_cooldown_months: 5,
            },
          ],
          periodic_thinking: '',
          player_directive: '',
          player_intervention_points: 2,
          player_intervention_points_max: 3,
          player_directive_cost: 1,
          player_relation_intervention_cost: 1,
          player_relation_intervention_delta: 18,
          is_player_owned_sect: true,
          war_summary: {
            active_war_count: 1,
            peace_count: 0,
            strongest_enemy_name: 'Enemy Sect',
            strongest_enemy_relation: -20,
          },
          economy_summary: {
            current_magic_stone: 0,
            effective_income_per_tile: 0,
            controlled_tile_income: 0,
            estimated_yearly_income: 0,
            estimated_yearly_upkeep: 0,
          },
        } as any,
      },
      global: {
        plugins: [createPinia(), i18n],
        directives: {
          sound: () => {},
        },
        stubs: {
          SecondaryPopup: true,
          StatItem: true,
          EntityRow: true,
          RelationRow: false,
        },
      },
    })

    expect(wrapper.text()).toContain('Relation intervention cooldown: 5 months')
    expect(wrapper.findAll('.diplomacy-actions .mini-btn')[0].attributes('disabled')).toBeDefined()
  })
})
