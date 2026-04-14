<script setup lang="ts">
import { computed, ref } from 'vue';
import type { SectDetail, EffectEntity } from '@/types/core';
import { worldApi } from '@/api';
import { useUiStore } from '@/stores/ui';
import StatItem from './components/StatItem.vue';
import SecondaryPopup from './components/SecondaryPopup.vue';
import EntityRow from './components/EntityRow.vue';
import RelationRow from './components/RelationRow.vue';
import { useI18n } from 'vue-i18n';
import { logError } from '@/utils/appError';
import { formatCultivationText } from '@/utils/cultivationText';
import brainIcon from '@/assets/icons/ui/lucide/brain.svg';
import checkIcon from '@/assets/icons/ui/lucide/check.svg';
import flagIcon from '@/assets/icons/ui/lucide/flag.svg';
import heartHandshakeIcon from '@/assets/icons/ui/lucide/heart-handshake.svg';
import mapPinIcon from '@/assets/icons/ui/lucide/map-pin.svg';
import pencilLineIcon from '@/assets/icons/ui/lucide/pencil-line.svg';
import scaleIcon from '@/assets/icons/ui/lucide/scale.svg';
import scrollIcon from '@/assets/icons/ui/lucide/scroll.svg';
import sparklesIcon from '@/assets/icons/ui/lucide/sparkles.svg';
import usersIcon from '@/assets/icons/ui/lucide/users.svg';

type DiplomacyItem = NonNullable<SectDetail['diplomacy_items']>[number];

const { t } = useI18n();
const props = defineProps<{
  data: SectDetail;
}>();

const uiStore = useUiStore();
const secondaryItem = ref<EffectEntity | null>(null);
const showDirectiveModal = ref(false);
const directiveContent = ref('');
const MAX_DIPLOMACY_ITEMS = 4;

function jumpToAvatar(id: string) {
  uiStore.select('avatar', id);
}

function jumpToSect(id: string) {
  uiStore.select('sect', id);
}

function showDetail(item: EffectEntity | undefined) {
  if (item) {
    secondaryItem.value = item;
  }
}

function openDirectiveModal() {
  if (!canUpdateDirective.value) {
    return;
  }
  directiveContent.value = props.data.player_directive || '';
  showDirectiveModal.value = true;
}

const alignmentText = props.data.alignment;
const sectId = computed(() => Number.parseInt(props.data.id, 10));
const isPlayerOwnedSect = computed(() => Boolean(props.data.is_player_owned_sect));
const canClaimSect = computed(() => Boolean(props.data.player_can_claim_sect) && !isPlayerOwnedSect.value);
const ownedSectName = computed(() => props.data.player_owned_sect_name || '');
const directiveText = computed(() => props.data.player_directive?.trim() || t('game.info_panel.sect.no_directive'));
const directiveRemainingCooldown = computed(() => Math.max(
  0,
  props.data.player_directive_remaining_cooldown_months || 0,
));
const directiveCost = computed(() => Math.max(0, props.data.player_directive_cost || 0));
const interventionPoints = computed(() => Math.max(0, props.data.player_intervention_points || 0));
const interventionPointsMax = computed(() => Math.max(
  interventionPoints.value,
  props.data.player_intervention_points_max || 0,
));
const hasDirectiveBudget = computed(() => interventionPoints.value >= directiveCost.value);
const canUpdateDirective = computed(() => Boolean(props.data.player_directive_can_update));
const controlStatusText = computed(() => {
  if (isPlayerOwnedSect.value) {
    return t('game.info_panel.sect.control_owned');
  }
  if (canClaimSect.value) {
    return t('game.info_panel.sect.control_claimable');
  }
  return t('game.info_panel.sect.control_locked_other', {
    name: ownedSectName.value || t('common.none'),
  });
});
const directiveCooldownText = computed(() => (
  !isPlayerOwnedSect.value
    ? controlStatusText.value
    : directiveRemainingCooldown.value <= 0
      ? t('game.info_panel.sect.directive_ready')
      : t('game.info_panel.sect.directive_cooldown', { months: directiveRemainingCooldown.value })
));
const directiveBudgetText = computed(() => (
  t('game.info_panel.sect.directive_budget', {
    points: interventionPoints.value,
    max: interventionPointsMax.value,
    cost: directiveCost.value,
  })
));
const directiveBlockedReason = computed(() => {
  if (!isPlayerOwnedSect.value) {
    return controlStatusText.value;
  }
  if (directiveRemainingCooldown.value > 0) {
    return directiveCooldownText.value;
  }
  if (!hasDirectiveBudget.value) {
    return t('game.info_panel.sect.directive_insufficient_budget', {
      points: interventionPoints.value,
      cost: directiveCost.value,
    });
  }
  return directiveCooldownText.value;
});
const relationInterventionCost = computed(() => Math.max(0, props.data.player_relation_intervention_cost || 0));
const relationInterventionDelta = computed(() => Math.max(1, props.data.player_relation_intervention_delta || 0));

const ruleText = computed(() => {
  if (!props.data.rule_desc) {
    return t('game.info_panel.sect.no_rule');
  }
  return props.data.rule_desc;
});

const warStatusText = computed(() => (
  (props.data.war_summary?.active_war_count ?? 0) > 0
    ? t('game.sect_relations.status_war')
    : t('game.sect_relations.status_peace')
));

const strongestEnemyText = computed(() => (
  props.data.war_summary?.strongest_enemy_name || t('common.none')
));

const yearlyIncomeText = computed(() => (
  t('game.info_panel.sect.stats.income_value', {
    income: Math.floor(props.data.economy_summary?.estimated_yearly_income || 0),
  })
));

const yearlyUpkeepText = computed(() => (
  t('game.info_panel.sect.stats.upkeep_value', {
    upkeep: Math.floor(props.data.economy_summary?.estimated_yearly_upkeep || 0),
  })
));

const warWearinessText = computed(() => `${Math.max(0, Math.floor(props.data.war_weariness || 0))}/100`);

const simplifiedDiplomacyItems = computed(() => {
  const items = [...(props.data.diplomacy_items ?? [])];
  return items
    .sort((a, b) => {
      if (a.status === 'war' && b.status !== 'war') {
        return -1;
      }
      if (a.status !== 'war' && b.status === 'war') {
        return 1;
      }
      return (a.relation_value ?? 0) - (b.relation_value ?? 0);
    })
    .slice(0, MAX_DIPLOMACY_ITEMS);
});

function getDurationYears(months: number) {
  return Math.max(0, Math.floor((months || 0) / 12));
}

function getDiplomacyMeta(item: DiplomacyItem) {
  const statusKey = item.status === 'war'
    ? 'game.sect_relations.status_war'
    : 'game.sect_relations.status_peace';
  const relationPart = item.relation_value === undefined
    ? ''
    : t('game.info_panel.sect.diplomacy_meta_relation', { value: item.relation_value });
  return relationPart
    ? `${t(statusKey)} · ${relationPart}`
    : t(statusKey);
}

function getDiplomacySub(item: DiplomacyItem) {
  const years = getDurationYears(item.duration_months);
  const durationKey = item.status === 'war'
    ? 'game.info_panel.sect.diplomacy_war_years'
    : 'game.info_panel.sect.diplomacy_peace_years';
  return t(durationKey, { count: years });
}

function getRelationInterventionRemaining(item: DiplomacyItem) {
  return Math.max(0, item.player_relation_intervention_remaining_cooldown_months || 0);
}

function canInterveneRelation(item: DiplomacyItem) {
  return Boolean(item.player_relation_intervention_can_intervene);
}

function getRelationInterventionStatusText(item: DiplomacyItem) {
  if (!isPlayerOwnedSect.value) {
    return controlStatusText.value;
  }
  const remaining = getRelationInterventionRemaining(item);
  if (remaining > 0) {
    return t('game.info_panel.sect.relation_intervention_cooldown', { months: remaining });
  }
  if (interventionPoints.value < relationInterventionCost.value) {
    return t('game.info_panel.sect.relation_intervention_insufficient_budget', {
      points: interventionPoints.value,
      cost: relationInterventionCost.value,
    });
  }
  return t('game.info_panel.sect.relation_intervention_ready', {
    delta: relationInterventionDelta.value,
    cost: relationInterventionCost.value,
  });
}

async function handleClaimSect() {
  if (!canClaimSect.value) {
    alert(controlStatusText.value);
    return;
  }
  if (!confirm(t('game.info_panel.sect.modals.claim_confirm'))) {
    return;
  }
  try {
    await worldApi.claimSect({ sect_id: sectId.value });
    uiStore.refreshDetail();
  } catch (error) {
    logError('SectDetail.handleClaimSect', error);
    alert(t('game.info_panel.sect.modals.claim_failed'));
  }
}

async function handleSetDirective() {
  if (!canUpdateDirective.value) {
    alert(directiveBlockedReason.value);
    return;
  }
  if (!directiveContent.value.trim()) return;
  try {
    await worldApi.setSectDirective({
      sect_id: sectId.value,
      content: directiveContent.value,
    });
    showDirectiveModal.value = false;
    uiStore.refreshDetail();
  } catch (error) {
    logError('SectDetail.handleSetDirective', error);
    alert(t('game.info_panel.sect.modals.directive_set_failed'));
  }
}

async function handleClearDirective() {
  if (!confirm(t('game.info_panel.sect.modals.directive_clear_confirm'))) return;
  try {
    await worldApi.clearSectDirective({ sect_id: sectId.value });
    uiStore.refreshDetail();
  } catch (error) {
    logError('SectDetail.handleClearDirective', error);
  }
}

async function handleInterveneRelation(item: DiplomacyItem, mode: 'ease' | 'escalate') {
  if (!canInterveneRelation(item)) {
    alert(getRelationInterventionStatusText(item));
    return;
  }
  try {
    await worldApi.interveneSectRelation({
      sect_id: sectId.value,
      other_sect_id: item.other_sect_id,
      mode,
    });
    uiStore.refreshDetail();
  } catch (error) {
    logError('SectDetail.handleInterveneRelation', error);
    alert(t('game.info_panel.sect.modals.relation_intervention_failed'));
  }
}
</script>

<template>
  <div class="sect-detail">
    <SecondaryPopup 
      :item="secondaryItem" 
      @close="secondaryItem = null" 
    />

    <div class="actions-bar" v-if="data.is_active !== false">
      <button v-if="!isPlayerOwnedSect" class="btn primary" :disabled="!canClaimSect" @click="handleClaimSect">{{ t('game.info_panel.sect.claim_sect') }}</button>
      <template v-else>
        <button class="btn primary" :disabled="!canUpdateDirective" @click="openDirectiveModal">{{ t('game.info_panel.sect.set_directive') }}</button>
        <button class="btn" @click="handleClearDirective">{{ t('game.info_panel.sect.clear_directive') }}</button>
      </template>
    </div>

    <div class="content-scroll">
       <!-- Stats Grid -->
       <div class="stats-grid">
          <StatItem :label="t('game.info_panel.sect.stats.alignment')" :value="alignmentText" :class="data.alignment" />
          <StatItem 
            :label="t('game.info_panel.sect.stats.orthodoxy')" 
            :value="data.orthodoxy?.name || t('common.none')" 
            :onClick="() => showDetail(data.orthodoxy)"
          />
          <StatItem :label="t('game.info_panel.sect.stats.style')" :value="data.style" />
          <StatItem :label="t('game.info_panel.sect.stats.preferred')" :value="data.preferred_weapon || t('common.none')" />
          <StatItem :label="t('game.info_panel.sect.stats.members')" :value="data.members?.length || 0" />
          <StatItem :label="t('game.info_panel.sect.stats.total_battle_strength')" :value="Math.floor(data.total_battle_strength || 0)" />
          <StatItem :label="t('game.info_panel.sect.stats.war_status')" :value="warStatusText" />
          <StatItem :label="t('game.info_panel.sect.stats.strongest_enemy')" :value="strongestEnemyText" />
          <StatItem :label="t('game.info_panel.sect.stats.income')" :value="yearlyIncomeText" />
          <StatItem :label="t('game.info_panel.sect.stats.upkeep')" :value="yearlyUpkeepText" />
          <StatItem :label="t('game.info_panel.sect.stats.war_weariness')" :value="warWearinessText" />
          <StatItem :label="t('game.info_panel.sect.stats.magic_stone')" :value="data.magic_stone || 0" />
       </div>

       <!-- Intro -->
       <div class="section">
          <div class="section-title">
            <span class="section-title-icon" :style="{ '--icon-url': `url(${flagIcon})` }" aria-hidden="true"></span>
            {{ t('game.info_panel.sect.sections.control') }}
          </div>
          <div class="text-content directive-content" :class="{ empty: !isPlayerOwnedSect }">{{ controlStatusText }}</div>
       </div>

       <div class="section">
          <div class="section-title">
            <span class="section-title-icon" :style="{ '--icon-url': `url(${flagIcon})` }" aria-hidden="true"></span>
            {{ t('game.info_panel.sect.sections.intro') }}
          </div>
          <div class="text-content">{{ data.desc }}</div>
       </div>

       <div class="section">
          <div class="section-title">
            <span class="section-title-icon" :style="{ '--icon-url': `url(${scaleIcon})` }" aria-hidden="true"></span>
            {{ t('game.info_panel.sect.sections.rule') }}
          </div>
          <div class="text-content rule-content">{{ ruleText }}</div>
       </div>

       <div class="section">
          <div class="section-title">
            <span class="section-title-icon" :style="{ '--icon-url': `url(${pencilLineIcon})` }" aria-hidden="true"></span>
            {{ t('game.info_panel.sect.sections.directive') }}
          </div>
          <div class="text-content directive-content" :class="{ empty: !data.player_directive }">{{ directiveText }}</div>
          <div class="directive-meta">{{ directiveCooldownText }}</div>
          <div class="directive-meta">{{ directiveBudgetText }}</div>
       </div>

       <div class="section" v-if="data.periodic_thinking">
          <div class="section-title">
            <span class="section-title-icon" :style="{ '--icon-url': `url(${brainIcon})` }" aria-hidden="true"></span>
            {{ t('game.info_panel.sect.sections.thinking') }}
          </div>
          <div class="text-content thinking-text-content">{{ data.periodic_thinking }}</div>
       </div>

       <div class="section" v-if="simplifiedDiplomacyItems.length">
          <div class="section-title">
            <span class="section-title-icon" :style="{ '--icon-url': `url(${heartHandshakeIcon})` }" aria-hidden="true"></span>
            {{ t('game.info_panel.sect.sections.diplomacy') }}
          </div>
          <div class="list-container">
             <div
               v-for="item in simplifiedDiplomacyItems"
               :key="item.other_sect_id"
               class="diplomacy-entry"
             >
               <RelationRow
                 :name="item.other_sect_name"
                 :meta="getDiplomacyMeta(item)"
                 :sub="getDiplomacySub(item)"
                 @click="jumpToSect(item.other_sect_id)"
               />
               <div class="diplomacy-actions">
                 <button
                   class="mini-btn"
                   :disabled="!canInterveneRelation(item)"
                   @click.stop="handleInterveneRelation(item, 'ease')"
                 >
                   {{ t('game.info_panel.sect.intervene_relation_ease') }}
                 </button>
                 <button
                   class="mini-btn danger"
                   :disabled="!canInterveneRelation(item)"
                   @click.stop="handleInterveneRelation(item, 'escalate')"
                 >
                   {{ t('game.info_panel.sect.intervene_relation_escalate') }}
                 </button>
               </div>
               <div class="diplomacy-meta">{{ getRelationInterventionStatusText(item) }}</div>
             </div>
          </div>
       </div>
       
       <!-- HQ -->
       <div class="section">
          <div class="section-title">
            <span class="section-title-icon" :style="{ '--icon-url': `url(${mapPinIcon})` }" aria-hidden="true"></span>
            {{ t('game.info_panel.sect.sections.hq', { name: data.hq_name }) }}
          </div>
          <div class="text-content">{{ data.hq_desc }}</div>
       </div>

       <!-- Effects -->
       <div class="section">
         <div class="section-title">
           <span class="section-title-icon" :style="{ '--icon-url': `url(${sparklesIcon})` }" aria-hidden="true"></span>
           {{ t('game.info_panel.sect.sections.bonus') }}
         </div>
         <div class="text-content highlight">{{ data.effect_desc || t('game.info_panel.sect.no_bonus') }}</div>
         <div v-if="data.runtime_effect_items?.length" class="runtime-effects-list">
            <div
              v-for="(item, idx) in data.runtime_effect_items"
              :key="`${item.source}-${idx}`"
              class="runtime-effect-item"
            >
              <div class="runtime-effect-desc">{{ item.desc }}</div>
              <div class="runtime-effect-meta">
                {{
                  item.is_permanent
                    ? t('game.info_panel.sect.runtime_effect_meta_permanent', { source: item.source_label })
                    : t('game.info_panel.sect.runtime_effect_meta', { source: item.source_label, months: item.remaining_months })
                }}
              </div>
            </div>
         </div>
         <div v-else class="runtime-effects-empty">
            {{ t('game.info_panel.sect.no_runtime_effect') }}
         </div>
       </div>

       <!-- Techniques -->
       <div class="section">
         <div class="section-title">
           <span class="section-title-icon" :style="{ '--icon-url': `url(${scrollIcon})` }" aria-hidden="true"></span>
           {{ t('game.info_panel.sect.sections.techniques') }}
         </div>
         <div class="list-container" v-if="data.techniques?.length">
            <EntityRow 
              v-for="t in data.techniques" 
              :key="t.id" 
              :item="t"
              @click="showDetail(t)"
            />
         </div>
         <div v-else class="text-content">{{ t('common.none') }}</div>
       </div>

       <!-- Members -->
       <div class="section" v-if="data.members?.length">
          <div class="section-title">
            <span class="section-title-icon" :style="{ '--icon-url': `url(${usersIcon})` }" aria-hidden="true"></span>
            {{ t('game.info_panel.sect.sections.members') }}
          </div>
          <div class="list-container">
             <RelationRow 
               v-for="m in data.members" 
               :key="m.id"
               :name="m.name"
               :meta="m.rank"
               :sub="`${formatCultivationText(m.realm, t)} · ${t('game.info_panel.avatar.stats.sect_contribution')} ${m.contribution ?? 0}`"
               @click="jumpToAvatar(m.id)"
             />
          </div>
       </div>
    </div>

    <div v-if="showDirectiveModal" class="modal-overlay">
      <div class="modal">
        <h3>{{ t('game.info_panel.sect.modals.set_directive') }}</h3>
        <textarea
          v-model="directiveContent"
          :placeholder="t('game.info_panel.sect.modals.directive_placeholder')"
        ></textarea>
        <div class="modal-footer">
          <button class="btn primary" @click="handleSetDirective">
            <span class="button-icon" :style="{ '--icon-url': `url(${checkIcon})` }" aria-hidden="true"></span>
            {{ t('common.confirm') }}
          </button>
          <button class="btn" @click="showDirectiveModal = false">{{ t('common.cancel') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sect-detail {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  position: relative;
}

.actions-bar {
  display: flex;
  gap: 8px;
  padding-bottom: 12px;
  border-bottom: 1px solid #333;
  margin-bottom: 12px;
}

.btn {
  flex: 1;
  padding: 6px 12px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.05);
  color: #ccc;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.btn.primary {
  background: #177ddc;
  color: white;
  border: none;
}

.btn.primary:hover {
  background: #1890ff;
}

.content-scroll {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-right: 4px;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  background: rgba(255, 255, 255, 0.03);
  padding: 8px;
  border-radius: 6px;
}

.section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: bold;
  color: #9f9380;
  border-bottom: 1px solid rgba(175, 148, 105, 0.32);
  padding-bottom: 4px;
  margin-bottom: 4px;
  letter-spacing: 0.02em;
}

.section-title-icon {
  display: inline-block;
  width: 1em;
  height: 1em;
  background-color: currentColor;
  -webkit-mask-image: var(--icon-url);
  mask-image: var(--icon-url);
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  -webkit-mask-position: center;
  mask-position: center;
  -webkit-mask-size: contain;
  mask-size: contain;
  flex-shrink: 0;
}

.text-content {
  font-size: 13px;
  line-height: 1.6;
  color: #ccc;
  white-space: pre-wrap;
}

.thinking-text-content {
  line-height: 1.5;
  white-space: normal;
}

.text-content.highlight {
  color: #e6f7ff;
  background: rgba(24, 144, 255, 0.1);
  padding: 8px;
  border-radius: 4px;
}

.runtime-effects-list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.runtime-effect-item {
  padding: 8px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.04);
}

.runtime-effect-desc {
  font-size: 13px;
  color: #d8ecff;
  line-height: 1.5;
}

.runtime-effect-meta {
  margin-top: 4px;
  font-size: 12px;
  color: #9fb9d6;
}

.runtime-effects-empty {
  margin-top: 8px;
  font-size: 12px;
  color: #9aa5b1;
}

.rule-content {
  color: #f3e7bf;
  background: rgba(179, 134, 0, 0.12);
  border: 1px solid rgba(179, 134, 0, 0.18);
  padding: 8px 10px;
  border-radius: 6px;
}

.directive-content {
  color: #d9ebff;
  background: rgba(23, 125, 220, 0.12);
  border: 1px solid rgba(23, 125, 220, 0.2);
  padding: 8px 10px;
  border-radius: 6px;
}

.directive-content.empty {
  color: #93a4b4;
}

.directive-meta {
  font-size: 12px;
  color: #9fb9d6;
}

.diplomacy-entry {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.diplomacy-actions {
  display: flex;
  gap: 8px;
}

.diplomacy-meta {
  font-size: 12px;
  color: #9fb9d6;
}

.mini-btn {
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid rgba(23, 125, 220, 0.24);
  background: rgba(23, 125, 220, 0.12);
  color: #d9ebff;
  font-size: 11px;
  cursor: pointer;
}

.mini-btn.danger {
  border-color: rgba(179, 64, 64, 0.28);
  background: rgba(179, 64, 64, 0.14);
  color: #ffd7d7;
}

.mini-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

/* Tech List */
.tech-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tech-item {
  font-size: 13px;
  color: #eee;
  padding: 4px 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: background 0.2s;
}

.tech-item.clickable {
  cursor: pointer;
}

.tech-item.clickable:hover {
  background: rgba(255, 255, 255, 0.1);
}

.tech-icon {
  font-size: 14px;
}

.modal-overlay {
  position: absolute;
  top: 0;
  left: -16px;
  right: -16px;
  bottom: -16px;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal {
  width: 280px;
  background: #222;
  border: 1px solid #444;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.modal h3 {
  margin: 0;
  font-size: 14px;
  color: #f0f0f0;
}

.modal textarea {
  width: 100%;
  min-height: 100px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 6px;
  color: #ddd;
  padding: 10px;
  font-size: 13px;
  resize: vertical;
  box-sizing: border-box;
}

.modal-footer {
  display: flex;
  gap: 8px;
}

.button-icon {
  width: 14px;
  height: 14px;
  background-color: currentColor;
  -webkit-mask-image: var(--icon-url);
  mask-image: var(--icon-url);
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  -webkit-mask-position: center;
  mask-position: center;
  -webkit-mask-size: contain;
  mask-size: contain;
}
</style>
