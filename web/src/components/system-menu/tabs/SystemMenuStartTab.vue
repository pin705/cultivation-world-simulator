<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { MMessage } from 'shuimo-ui'
import { useI18n } from 'vue-i18n'

import GameStartPanel from '@/components/game/panels/system/GameStartPanel.vue'
import { avatarApi, worldApi } from '@/api'
import { useSocketStore } from '@/stores/socket'
import { useSystemStore } from '@/stores/system'
import { logError } from '@/utils/appError'
import {
  playerCampaignStepLabel,
  playerOpeningChoiceDesc,
  playerOpeningChoiceEffect,
  playerOpeningChoiceTitle,
} from '@/utils/playerCampaign'

const props = defineProps<{
  gameInitialized: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const { t } = useI18n()
const message = MMessage
const systemStore = useSystemStore()
const socketStore = useSocketStore()
const {
  initStatus,
  viewerId,
  authSession,
  playerOnboarding,
  activeRoomId,
  activeRoomSummary,
  roomSummaries,
} = storeToRefs(systemStore)

const authMode = ref<'register' | 'login'>('register')
const pendingAuthEmail = ref('')
const pendingAuthPassword = ref('')
const pendingAuthDisplayName = ref('')
const authError = ref('')
const isSubmittingAuth = ref(false)

const pendingRoomId = ref('')
const pendingJoinRoomId = ref('')
const pendingInviteCode = ref('')
const roomError = ref('')
const isSwitchingRoom = ref(false)
const isJoiningRoom = ref(false)

const onboardingError = ref('')
const isSubmittingOnboarding = ref(false)

const isRegisteredAccount = computed(() => authSession.value?.auth_type === 'password')
const accountEmail = computed(() => authSession.value?.email?.trim() || '')
const currentIdentityLabel = computed(() => (
  authSession.value?.display_name?.trim()
  || playerOnboarding.value?.viewer_display_name?.trim()
  || viewerId.value
))

const normalizedPendingAuthEmail = computed(() => pendingAuthEmail.value.trim().toLowerCase())
const normalizedPendingAuthPassword = computed(() => pendingAuthPassword.value)
const normalizedPendingAuthDisplayName = computed(() => pendingAuthDisplayName.value.trim())
const hasValidPendingAuthEmail = computed(() => (
  normalizedPendingAuthEmail.value.includes('@')
  && normalizedPendingAuthEmail.value.split('@')[1]?.includes('.')
))
const canRegisterPasswordAccount = computed(() => (
  !isSubmittingAuth.value
  && hasValidPendingAuthEmail.value
  && normalizedPendingAuthPassword.value.length >= 8
))
const canLoginPasswordAccount = computed(() => (
  !isSubmittingAuth.value
  && hasValidPendingAuthEmail.value
  && normalizedPendingAuthPassword.value.length >= 8
))

const currentRoom = computed(() => (
  activeRoomSummary.value
  || roomSummaries.value?.find((room) => room.id === activeRoomId.value)
  || null
))
const currentRoomPlan = computed(() => (
  currentRoom.value?.plan_id?.trim()
  || (activeRoomId.value === 'main' ? 'main_public' : 'standard_private')
))
const currentRoomProfile = computed(() => currentRoom.value?.commercial_profile?.trim() || 'standard')
const normalizedPendingRoomId = computed(() => pendingRoomId.value.trim())
const normalizedPendingJoinRoomId = computed(() => pendingJoinRoomId.value.trim())
const normalizedPendingInviteCode = computed(() => pendingInviteCode.value.trim().toUpperCase())
const canCreateOrSwitchRoom = computed(() => (
  !isSwitchingRoom.value
  && Boolean(normalizedPendingRoomId.value)
))
const canJoinPrivateRoom = computed(() => (
  !isJoiningRoom.value
  && Boolean(normalizedPendingJoinRoomId.value)
  && Boolean(normalizedPendingInviteCode.value)
))

const worldStatus = computed(() => initStatus.value?.status || 'idle')
const worldNeedsStart = computed(() => worldStatus.value === 'idle' || worldStatus.value === 'error')
const worldIsStarting = computed(() => worldStatus.value === 'pending' || worldStatus.value === 'in_progress')
const worldReady = computed(() => worldStatus.value === 'ready')

const onboardingState = computed(() => playerOnboarding.value)
const onboardingReady = computed(() => Boolean(onboardingState.value?.ready))
const onboardingRecommendedStep = computed(() => onboardingState.value?.recommended_step || 'claim_sect')
const onboardingClaimableSects = computed(() => onboardingState.value?.claimable_sects || [])
const onboardingMainAvatarCandidates = computed(() => onboardingState.value?.main_avatar_candidates || [])
const onboardingOpeningChoices = computed(() => onboardingState.value?.opening_choices || [])
const currentSectName = computed(() => onboardingState.value?.owned_sect_name?.trim() || t('ui.player_campaign_unclaimed'))
const currentMainAvatarName = computed(() => onboardingState.value?.main_avatar_name?.trim() || t('ui.player_campaign_unselected'))
const currentOpeningChoiceLabel = computed(() => {
  const choiceId = onboardingState.value?.opening_choice_id?.trim()
  return choiceId
    ? playerOpeningChoiceTitle(t, choiceId)
    : t('ui.player_campaign_opening_empty')
})

const canEnterWorld = computed(() => (
  props.gameInitialized
  && worldReady.value
  && onboardingReady.value
))

const flowHint = computed(() => {
  if (worldNeedsStart.value) {
    return t('ui.play_flow_world_idle')
  }
  if (worldIsStarting.value) {
    return t('ui.play_flow_world_waiting')
  }
  if (!onboardingReady.value) {
    if (onboardingRecommendedStep.value === 'set_main_avatar') {
      return t('ui.player_campaign_main_avatar_title')
    }
    if (onboardingRecommendedStep.value === 'choose_opening') {
      return t('ui.player_campaign_opening_title')
    }
    return t('ui.player_campaign_claim_title')
  }
  return t('ui.play_flow_enter_hint')
})

function formatRoomPlan(planId: string) {
  if (planId === 'story_rich_private') {
    return t('ui.control_room_plan_story_rich')
  }
  if (planId === 'internal_full_private') {
    return t('ui.control_room_plan_internal')
  }
  if (planId === 'main_public') {
    return t('ui.control_room_plan_public')
  }
  return t('ui.control_room_plan_standard')
}

function onboardingStepLabel(step: string) {
  return playerCampaignStepLabel(t, step)
}

async function submitAuth() {
  if (isSubmittingAuth.value) {
    return
  }

  isSubmittingAuth.value = true
  authError.value = ''
  try {
    const session = authMode.value === 'register'
      ? await systemStore.registerPasswordSession(
        normalizedPendingAuthEmail.value,
        normalizedPendingAuthPassword.value,
        normalizedPendingAuthDisplayName.value || undefined,
      )
      : await systemStore.loginPasswordSession(
        normalizedPendingAuthEmail.value,
        normalizedPendingAuthPassword.value,
      )

    if (!session) {
      authError.value = authMode.value === 'register'
        ? t('ui.auth_register_failed')
        : t('ui.auth_login_failed')
      return
    }

    pendingAuthPassword.value = ''
    message.success(
      authMode.value === 'register'
        ? t('ui.auth_register_submit')
        : t('ui.auth_login_submit'),
    )
  } catch (error) {
    logError('SystemMenuStartTab.submitAuth', error)
    authError.value = authMode.value === 'register'
      ? t('ui.auth_register_failed')
      : t('ui.auth_login_failed')
  } finally {
    isSubmittingAuth.value = false
  }
}

async function logoutAccount() {
  authError.value = ''
  const ok = await systemStore.logoutSession()
  if (!ok) {
    authError.value = t('ui.auth_logout_failed')
  }
}

async function switchRoom(roomId: string) {
  const normalized = roomId.trim()
  if (!normalized || isSwitchingRoom.value) {
    return
  }

  isSwitchingRoom.value = true
  roomError.value = ''
  try {
    const result = await systemStore.switchWorldRoom(normalized)
    if (!result) {
      roomError.value = t('ui.control_room_switch_failed')
      return
    }
    socketStore.switchRoom(normalized)
    pendingRoomId.value = ''
  } catch (error) {
    logError('SystemMenuStartTab.switchRoom', error)
    roomError.value = t('ui.control_room_switch_failed')
  } finally {
    isSwitchingRoom.value = false
  }
}

async function joinRoomByInvite() {
  if (!canJoinPrivateRoom.value) {
    return
  }

  isJoiningRoom.value = true
  roomError.value = ''
  try {
    const result = await systemStore.joinWorldRoomByInvite(
      normalizedPendingJoinRoomId.value,
      normalizedPendingInviteCode.value,
    )
    if (!result) {
      roomError.value = t('ui.control_room_join_failed')
      return
    }
    socketStore.switchRoom(normalizedPendingJoinRoomId.value)
    pendingJoinRoomId.value = ''
    pendingInviteCode.value = ''
  } catch (error) {
    logError('SystemMenuStartTab.joinRoomByInvite', error)
    roomError.value = t('ui.control_room_join_failed')
  } finally {
    isJoiningRoom.value = false
  }
}

async function handleWorldStarted() {
  await systemStore.fetchInitStatus()
}

async function claimSectFromFlow(sectId: number) {
  if (isSubmittingOnboarding.value) {
    return
  }

  isSubmittingOnboarding.value = true
  onboardingError.value = ''
  try {
    await worldApi.claimSect({ sect_id: sectId })
    await systemStore.fetchInitStatus()
  } catch (error) {
    logError('SystemMenuStartTab.claimSectFromFlow', error)
    onboardingError.value = t('ui.player_campaign_claim_failed')
  } finally {
    isSubmittingOnboarding.value = false
  }
}

async function setMainAvatarFromFlow(avatarId: string) {
  if (isSubmittingOnboarding.value) {
    return
  }

  isSubmittingOnboarding.value = true
  onboardingError.value = ''
  try {
    await avatarApi.setMainAvatar({ avatar_id: avatarId })
    await systemStore.fetchInitStatus()
  } catch (error) {
    logError('SystemMenuStartTab.setMainAvatarFromFlow', error)
    onboardingError.value = t('ui.player_campaign_main_avatar_failed')
  } finally {
    isSubmittingOnboarding.value = false
  }
}

async function chooseOpeningFromFlow(choiceId: string) {
  if (isSubmittingOnboarding.value) {
    return
  }

  isSubmittingOnboarding.value = true
  onboardingError.value = ''
  try {
    const result = await systemStore.choosePlayerOpening(choiceId)
    if (!result) {
      onboardingError.value = t('ui.player_campaign_opening_failed')
    }
  } catch (error) {
    logError('SystemMenuStartTab.chooseOpeningFromFlow', error)
    onboardingError.value = t('ui.player_campaign_opening_failed')
  } finally {
    isSubmittingOnboarding.value = false
  }
}

function enterWorld() {
  if (!canEnterWorld.value) {
    return
  }
  emit('close')
}

onMounted(() => {
  void systemStore.fetchInitStatus()
})
</script>

<template>
  <div class="start-flow">
    <header class="start-flow__header">
      <div class="start-flow__kicker">{{ t('ui.play_flow_title') }}</div>
      <h2 class="start-flow__title">{{ t('game_start.title') }}</h2>
      <p class="start-flow__desc">{{ t('ui.play_flow_desc') }}</p>
    </header>

    <section class="start-flow__section">
      <div class="start-flow__section-head">
        <div class="start-flow__index">1</div>
        <div class="start-flow__heading-copy">
          <h3>{{ t('ui.play_flow_step_identity') }}</h3>
          <p>
            {{ isRegisteredAccount ? t('ui.play_flow_registered_hint') : t('ui.play_flow_guest_hint') }}
          </p>
        </div>
      </div>

      <div class="start-flow__meta">
        <span>{{ currentIdentityLabel }}</span>
        <span>{{ accountEmail || t('ui.auth_email_missing') }}</span>
      </div>

      <div v-if="!isRegisteredAccount" class="start-flow__auth-mode">
        <button class="mode-pill" :class="{ 'mode-pill--active': authMode === 'register' }"
          @click="authMode = 'register'">
          {{ t('ui.auth_mode_register') }}
        </button>
        <button class="mode-pill" :class="{ 'mode-pill--active': authMode === 'login' }" @click="authMode = 'login'">
          {{ t('ui.auth_mode_login') }}
        </button>
      </div>

      <div v-if="!isRegisteredAccount" class="start-flow__stack">
        <m-input v-model:value="pendingAuthEmail" :placeholder="t('ui.auth_email_placeholder')" />
        <m-input v-model:value="pendingAuthPassword" type="password" show-password-on="click"
          :placeholder="t('ui.auth_password_placeholder')" />
        <m-input v-if="authMode === 'register'" v-model:value="pendingAuthDisplayName"
          :placeholder="t('ui.auth_display_name_placeholder')" />
        <m-button type="primary" block :loading="isSubmittingAuth"
          :disabled="authMode === 'register' ? !canRegisterPasswordAccount : !canLoginPasswordAccount"
          @click="submitAuth">
          {{ authMode === 'register' ? t('ui.auth_register_submit') : t('ui.auth_login_submit') }}
        </m-button>
        <div class="start-flow__hint">{{ t('ui.auth_hint_play_now') }}</div>
      </div>

      <div v-else class="start-flow__stack">
        <div class="start-flow__hint">{{ t('ui.auth_status_registered') }}</div>
        <m-button secondary block @click="logoutAccount">
          {{ t('ui.auth_logout') }}
        </m-button>
      </div>

      <div v-if="authError" class="start-flow__error">
        {{ authError }}
      </div>
    </section>

    <section class="start-flow__section">
      <div class="start-flow__section-head">
        <div class="start-flow__index">2</div>
        <div class="start-flow__heading-copy">
          <h3>{{ t('ui.play_flow_step_room') }}</h3>
          <p>{{ t('ui.play_flow_room_switch_hint') }}</p>
        </div>
      </div>

      <div class="start-flow__meta">
        <span>{{ t('ui.control_rooms_current', { id: activeRoomId }) }}</span>
        <span>{{ formatRoomPlan(currentRoomPlan) }} · {{ currentRoomProfile }}</span>
      </div>

      <div class="start-flow__stack">
        <m-button v-if="activeRoomId !== 'main'" secondary block :disabled="isSwitchingRoom"
          @click="switchRoom('main')">
          {{ t('ui.play_flow_room_use_main') }}
        </m-button>

        <div class="start-flow__inline">
          <m-input v-model:value="pendingRoomId" :placeholder="t('ui.control_rooms_placeholder')" />
          <m-button type="primary" :loading="isSwitchingRoom" :disabled="!canCreateOrSwitchRoom"
            @click="switchRoom(normalizedPendingRoomId)">
            {{ t('ui.control_rooms_create') }}
          </m-button>
        </div>

        <div class="start-flow__hint">{{ t('ui.play_flow_room_join_hint') }}</div>

        <div class="start-flow__inline start-flow__inline--join">
          <m-input v-model:value="pendingJoinRoomId" :placeholder="t('ui.control_room_join_room_placeholder')" />
          <m-input v-model:value="pendingInviteCode" :placeholder="t('ui.control_room_join_code_placeholder')" />
          <m-button :loading="isJoiningRoom" :disabled="!canJoinPrivateRoom" @click="joinRoomByInvite">
            {{ t('ui.control_room_join_action') }}
          </m-button>
        </div>
      </div>

      <div v-if="roomError" class="start-flow__error">
        {{ roomError }}
      </div>
    </section>

    <section class="start-flow__section">
      <div class="start-flow__section-head">
        <div class="start-flow__index">3</div>
        <div class="start-flow__heading-copy">
          <h3>{{ t('ui.play_flow_step_world') }}</h3>
          <p>
            {{
              worldNeedsStart
                ? t('ui.play_flow_world_idle')
                : worldIsStarting
                  ? t('ui.play_flow_world_waiting')
                  : t('ui.play_flow_world_ready')
            }}
          </p>
        </div>
      </div>

      <div v-if="worldNeedsStart" class="start-flow__stack">
        <div v-if="worldStatus === 'error' && initStatus?.error" class="start-flow__error">
          {{ t('ui.play_flow_world_error', { error: initStatus.error }) }}
        </div>
        <GameStartPanel :readonly="false" compact @started="handleWorldStarted" />
      </div>

      <div v-else-if="worldIsStarting" class="start-flow__stack">
        <div class="start-flow__meta">
          <span>{{ initStatus?.phase_name || t('ui.play_flow_world_waiting') }}</span>
          <span>{{ Math.round((initStatus?.progress || 0) * 100) }}%</span>
        </div>
        <div class="start-flow__hint">{{ t('ui.play_flow_world_waiting') }}</div>
      </div>

      <div v-else class="start-flow__stack">
        <div class="start-flow__meta">
          <span>{{ t('ui.play_flow_world_ready') }}</span>
          <span>{{ t('ui.control_rooms_current', { id: activeRoomId }) }}</span>
        </div>
        <div class="start-flow__hint">{{ t('ui.play_flow_start_ready') }}</div>
      </div>
    </section>

    <section class="start-flow__section">
      <div class="start-flow__section-head">
        <div class="start-flow__index">4</div>
        <div class="start-flow__heading-copy">
          <h3>{{ t('ui.play_flow_step_campaign') }}</h3>
          <p>{{ onboardingStepLabel(onboardingRecommendedStep) }}</p>
        </div>
      </div>

      <div v-if="!worldReady" class="start-flow__hint">
        {{ t('ui.play_flow_campaign_waiting') }}
      </div>

      <template v-else>
        <div class="start-flow__meta">
          <span>{{ t('ui.player_campaign_current_sect') }} {{ currentSectName }}</span>
          <span>{{ t('ui.player_campaign_current_main_avatar') }} {{ currentMainAvatarName }}</span>
          <span>{{ t('ui.player_campaign_current_opening') }} {{ currentOpeningChoiceLabel }}</span>
        </div>

        <div class="start-flow__hint">
          {{
            t('ui.player_campaign_intervention_points', {
              current: onboardingState?.intervention_points || 0,
              max: onboardingState?.intervention_points_max || 0,
            })
          }}
        </div>

        <div v-if="!onboardingReady && onboardingRecommendedStep === 'claim_sect'" class="start-flow__option-list">
          <button v-for="sect in onboardingClaimableSects" :key="sect.id" class="flow-option"
            :disabled="isSubmittingOnboarding" @click="claimSectFromFlow(sect.id)">
            <span class="flow-option__title">{{ sect.name }}</span>
            <span class="flow-option__meta">
              {{ t('ui.player_campaign_members', { count: sect.member_count }) }}
            </span>
          </button>
        </div>

        <div v-else-if="!onboardingReady && onboardingRecommendedStep === 'set_main_avatar'"
          class="start-flow__option-list">
          <button v-for="avatar in onboardingMainAvatarCandidates" :key="avatar.id" class="flow-option"
            :disabled="isSubmittingOnboarding" @click="setMainAvatarFromFlow(avatar.id)">
            <span class="flow-option__title">{{ avatar.name }}</span>
            <span class="flow-option__meta">
              {{ avatar.realm }} · {{ t('ui.player_campaign_age', { age: avatar.age }) }}
            </span>
          </button>
        </div>

        <div v-else-if="!onboardingReady && onboardingRecommendedStep === 'choose_opening'"
          class="start-flow__option-list">
          <button v-for="choice in onboardingOpeningChoices" :key="choice.id" class="flow-option"
            :disabled="isSubmittingOnboarding || !choice.can_select" @click="chooseOpeningFromFlow(choice.id)">
            <span class="flow-option__title">{{ playerOpeningChoiceTitle(t, choice.id) }}</span>
            <span class="flow-option__meta">{{ playerOpeningChoiceDesc(t, choice.id) }}</span>
            <span class="flow-option__meta">{{ playerOpeningChoiceEffect(t, choice.id) }}</span>
            <span v-if="choice.is_selected" class="flow-option__meta">
              {{ t('ui.player_campaign_opening_selected') }}
            </span>
          </button>
          <div v-if="!onboardingOpeningChoices.length" class="start-flow__hint">
            {{ t('ui.player_campaign_opening_empty') }}
          </div>
        </div>

        <div v-else class="start-flow__hint">
          {{ t('ui.player_campaign_ready_desc') }}
        </div>

        <div v-if="onboardingError" class="start-flow__error">
          {{ onboardingError }}
        </div>
      </template>
    </section>

    <section class="start-flow__section start-flow__section--final">
      <div class="start-flow__section-head">
        <div class="start-flow__index">5</div>
        <div class="start-flow__heading-copy">
          <h3>{{ t('ui.play_flow_step_enter') }}</h3>
          <p>{{ flowHint }}</p>
        </div>
      </div>

      <div class="start-flow__stack">
        <m-button type="primary" size="large" block :disabled="!canEnterWorld" @click="enterWorld">
          {{ t('ui.play_flow_enter_action') }}
        </m-button>
        <div class="start-flow__hint">{{ flowHint }}</div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.start-flow {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: 880px;
  margin: 0 auto;
  color: #ece7dd;
}

.start-flow__header {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.start-flow__kicker {
  font-size: 12px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #bda98d;
}

.start-flow__title {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: #f6f1e8;
}

.start-flow__desc {
  margin: 0;
  max-width: 720px;
  color: rgba(236, 231, 221, 0.72);
  line-height: 1.6;
}

.start-flow__section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  border: 1px solid rgba(183, 152, 112, 0.26);
  border-radius: 14px;
  background:
    linear-gradient(180deg, rgba(34, 30, 24, 0.94), rgba(18, 16, 13, 0.96)),
    radial-gradient(circle at top left, rgba(183, 152, 112, 0.08), transparent 45%);
}

.start-flow__section--final {
  border-color: rgba(204, 174, 120, 0.36);
}

.start-flow__section-head {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.start-flow__index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  background: rgba(193, 158, 112, 0.14);
  color: #e2c18c;
  font-size: 13px;
  font-weight: 700;
  flex: 0 0 auto;
}

.start-flow__heading-copy h3 {
  margin: 0 0 4px;
  font-size: 17px;
  color: #f4ecdd;
}

.start-flow__heading-copy p {
  margin: 0;
  color: rgba(236, 231, 221, 0.66);
  line-height: 1.5;
}

.start-flow__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  color: rgba(236, 231, 221, 0.76);
  font-size: 13px;
}

.start-flow__stack {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.start-flow__inline {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
}

.start-flow__inline--join {
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) auto;
}

.start-flow__auth-mode {
  display: inline-flex;
  gap: 8px;
}

.mode-pill {
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid rgba(193, 158, 112, 0.22);
  background: rgba(255, 255, 255, 0.02);
  color: rgba(236, 231, 221, 0.72);
  cursor: pointer;
  transition: border-color 0.18s ease, background 0.18s ease, color 0.18s ease;
}

.mode-pill:hover,
.mode-pill--active {
  border-color: rgba(222, 187, 139, 0.48);
  background: rgba(193, 158, 112, 0.14);
  color: #f4ecdd;
}

.start-flow__hint {
  color: rgba(236, 231, 221, 0.64);
  font-size: 13px;
  line-height: 1.55;
}

.start-flow__error {
  color: #ff8d87;
  font-size: 13px;
  line-height: 1.5;
}

.start-flow__option-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.flow-option {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  width: 100%;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid rgba(193, 158, 112, 0.2);
  background: rgba(255, 255, 255, 0.02);
  color: #efe6d7;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.18s ease, background 0.18s ease, transform 0.18s ease;
}

.flow-option:hover:not(:disabled) {
  border-color: rgba(222, 187, 139, 0.42);
  background: rgba(193, 158, 112, 0.1);
  transform: translateY(-1px);
}

.flow-option:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.flow-option__title {
  font-size: 15px;
  font-weight: 600;
}

.flow-option__meta {
  color: rgba(236, 231, 221, 0.62);
  font-size: 12px;
}

@media (max-width: 720px) {

  .start-flow__inline,
  .start-flow__inline--join {
    grid-template-columns: 1fr;
  }

  .start-flow__title {
    font-size: 24px;
  }
}
</style>
