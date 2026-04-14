<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { systemApi } from './api/modules/system'
import { avatarApi, worldApi } from './api'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// Components
import SplashLayer from './components/SplashLayer.vue'
import GameCanvas from './components/game/GameCanvas.vue'
import InfoPanelContainer from './components/game/panels/info/InfoPanelContainer.vue'
import StatusBar from './components/layout/StatusBar.vue'
import EventPanel from './components/game/panels/EventPanel.vue'
import SystemMenu from './components/SystemMenu.vue'
import LoadingOverlay from './components/LoadingOverlay.vue'
import RecapOverlay from './components/game/panels/RecapOverlay.vue'
import menuIcon from '@/assets/icons/ui/lucide/menu.svg'
import playIcon from '@/assets/icons/ui/lucide/play.svg'
import pauseIcon from '@/assets/icons/ui/lucide/pause.svg'

// Composables
import { useGameInit } from './composables/useGameInit'
import { useGameControl } from './composables/useGameControl'
import { useAudio } from './composables/useAudio'
import { useBgm } from './composables/useBgm'
import { useSidebarResize } from './composables/useSidebarResize'
import { useAppShell } from './composables/useAppShell'
import { useSystemMenuFlow } from './composables/useSystemMenuFlow'
import { logError } from './utils/appError'
import {
  playerCampaignStepLabel,
  playerOpeningChoiceDesc,
  playerOpeningChoiceTitle,
} from './utils/playerCampaign'

// Stores
import { useUiStore } from './stores/ui'
import { useSettingStore } from './stores/setting'
import { useSystemStore } from './stores/system'
import { useRecapStore } from './stores/recap'

const uiStore = useUiStore()
const settingStore = useSettingStore()
const systemStore = useSystemStore()
const { playerOnboarding, viewerId } = storeToRefs(systemStore)
const recapStore = useRecapStore()

// Sidebar resizer 状态
const { sidebarWidth, isResizing, onResizerMouseDown } = useSidebarResize()

function syncLayoutCssVars(width: number) {
  document.documentElement.style.setProperty('--cws-sidebar-width', `${width}px`)
}

// 1. 游戏初始化逻辑
const {
  initStatus,
  gameInitialized,
  showLoading,
} = useGameInit()

const {
  showMenu,
  menuDefaultTab,
  menuContext,
  canCloseMenu,
  performStartupCheck,
  openGameMenu,
  handleLLMReady,
  handleMenuClose,
} = useSystemMenuFlow()

const {
  isManualPaused,
  handleKeydown: controlHandleKeydown,
  toggleManualPause
} = useGameControl({
  gameInitialized,
  showMenu,
  canCloseMenu,
  openGameMenu,
  closeMenu: handleMenuClose,
})

const settingsHydrated = computed(() => settingStore.hydrated)

const {
  scene,
  canRenderGameShell,
  canRenderSplash,
  showLoadingOverlay,
  shouldBlockControls,
  handleSplashNavigate,
  handleMenuCloseWrapper,
  returnToSplash,
} = useAppShell({
  settingsHydrated,
  initStatus,
  gameInitialized,
  showLoading,
  showMenu,
  menuDefaultTab,
  menuContext,
  isManualPaused,
  performStartupCheck,
  handleMenuClose,
  onGameBgmStart: () => useBgm().play('map'),
  onResumeGame: () => systemStore.resume(),
})

// 事件处理
function onKeydown(e: KeyboardEvent) {
  if (shouldBlockControls.value) return
  controlHandleKeydown(e)
}

function handleSelection(target: { type: 'avatar' | 'region'; id: string; name?: string }) {
  uiStore.select(target.type, target.id)
}

const isSubmittingOnboarding = ref(false)
const onboardingError = ref('')
const onboardingOverlayVisible = computed(() => (
  canRenderGameShell.value
  && initStatus.value?.status === 'ready'
  && Boolean(playerOnboarding.value)
  && !playerOnboarding.value?.ready
))
const onboardingRecommendedStep = computed(() => (
  playerOnboarding.value?.recommended_step || 'claim_sect'
))
const onboardingClaimableSects = computed(() => (
  (playerOnboarding.value?.claimable_sects || []).slice(0, 3)
))
const onboardingMainAvatarCandidates = computed(() => (
  (playerOnboarding.value?.main_avatar_candidates || []).slice(0, 3)
))
const onboardingOpeningChoices = computed(() => (
  (playerOnboarding.value?.opening_choices || []).slice(0, 3)
))

function onboardingStepLabel(step: string) {
  return playerCampaignStepLabel(t, step)
}

function openPlayerCampaignSetup() {
  uiStore.openSystemMenu('start', true, 'game')
}

async function claimSectFromOverlay(sectId: number) {
  isSubmittingOnboarding.value = true
  onboardingError.value = ''
  try {
    await worldApi.claimSect({
      sect_id: sectId,
      viewer_id: viewerId.value,
    })
    await systemStore.fetchInitStatus()
  } catch (e) {
    logError('App.claimSectFromOverlay', e)
    onboardingError.value = t('ui.player_campaign_claim_failed')
  } finally {
    isSubmittingOnboarding.value = false
  }
}

async function setMainAvatarFromOverlay(avatarId: string) {
  isSubmittingOnboarding.value = true
  onboardingError.value = ''
  try {
    await avatarApi.setMainAvatar({
      avatar_id: avatarId,
      viewer_id: viewerId.value,
    })
    await systemStore.fetchInitStatus()
  } catch (e) {
    logError('App.setMainAvatarFromOverlay', e)
    onboardingError.value = t('ui.player_campaign_main_avatar_failed')
  } finally {
    isSubmittingOnboarding.value = false
  }
}

async function chooseOpeningFromOverlay(choiceId: string) {
  isSubmittingOnboarding.value = true
  onboardingError.value = ''
  try {
    const result = await systemStore.choosePlayerOpening(choiceId)
    if (!result) {
      onboardingError.value = t('ui.player_campaign_opening_failed')
    }
  } catch (e) {
    logError('App.chooseOpeningFromOverlay', e)
    onboardingError.value = t('ui.player_campaign_opening_failed')
  } finally {
    isSubmittingOnboarding.value = false
  }
}

async function handleSplashAction(key: string) {
  if (key === 'exit') {
    try {
      await systemApi.shutdown()
      window.close()
      document.body.innerHTML = `<div style="color:white; display:flex; justify-content:center; align-items:center; height:100vh; background:black; font-size:24px;">${t('game.controls.closed_msg')}</div>`
    } catch (e) {
      logError('App shutdown', e)
    }
    return
  }

  if (key === 'start' || key === 'load' || key === 'settings' || key === 'about') {
    handleSplashNavigate(key)
  }
}

async function handleReturnToMain() {
  try {
    await systemApi.resetGame()
    returnToSplash()
  } catch (e) {
    logError('App reset game', e)
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
  syncLayoutCssVars(sidebarWidth.value)
  settingStore.hydrate().finally(() => {
    useAudio().init()
    useBgm().init() // 确保 BGM 系统在 App 层级初始化，避免 Watcher 被子组件卸载
  })
})

// Load recap when game is initialized
watch(gameInitialized, (initialized) => {
  if (initialized && viewerId.value) {
    recapStore.loadRecap(viewerId.value).catch(err => {
      console.warn('[App] Failed to load recap (non-critical):', err)
    })
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  document.documentElement.style.removeProperty('--cws-sidebar-width')
})

watch(sidebarWidth, width => {
  syncLayoutCssVars(width)
})
</script>

<template>
  <div v-if="scene === 'boot'" class="app-layout app-layout--shell"></div>

  <SplashLayer v-else-if="canRenderSplash" @action="handleSplashAction" />

  <div v-else-if="scene === 'initializing'" class="app-layout app-layout--shell"></div>

  <div v-else-if="canRenderGameShell" class="app-layout">
    <StatusBar />

    <div class="main-content">
      <div class="map-container">
        <!-- 顶部控制栏 -->
        <div class="top-controls">
          <!-- 暂停/播放按钮 -->
          <button class="control-btn pause-toggle" @click="toggleManualPause"
            :title="isManualPaused ? t('game.controls.resume') : t('game.controls.pause')">
            <span class="control-btn-icon" :style="{ '--icon-url': `url(${isManualPaused ? playIcon : pauseIcon})` }"
              aria-hidden="true"></span>
          </button>

          <!-- 菜单按钮 -->
          <button class="control-btn menu-toggle" @click="openGameMenu()">
            <span class="control-btn-icon" :style="{ '--icon-url': `url(${menuIcon})` }" aria-hidden="true"></span>
          </button>
        </div>

        <!-- 暂停状态提示 -->
        <div v-if="isManualPaused" class="pause-indicator">
          <div class="pause-text">{{ t('game.controls.paused') }}</div>
        </div>

        <div v-if="onboardingOverlayVisible" class="player-onboarding-overlay">
          <div class="player-onboarding-card">
            <div class="player-onboarding-header">
              <div class="player-onboarding-kicker">{{ t('ui.player_campaign_title') }}</div>
              <div class="player-onboarding-step">{{ onboardingStepLabel(onboardingRecommendedStep) }}</div>
            </div>
            <p class="player-onboarding-desc">{{ t('ui.player_campaign_desc') }}</p>

            <div v-if="onboardingRecommendedStep === 'claim_sect'" class="player-onboarding-options">
              <button v-for="sect in onboardingClaimableSects" :key="sect.id" class="player-onboarding-option"
                :disabled="isSubmittingOnboarding" @click="claimSectFromOverlay(sect.id)">
                <span class="player-onboarding-option-title">{{ sect.name }}</span>
                <span class="player-onboarding-option-meta">
                  {{ t('ui.player_campaign_members', { count: sect.member_count }) }}
                </span>
              </button>
            </div>

            <div v-else-if="onboardingRecommendedStep === 'set_main_avatar'" class="player-onboarding-options">
              <button v-for="avatar in onboardingMainAvatarCandidates" :key="avatar.id" class="player-onboarding-option"
                :disabled="isSubmittingOnboarding" @click="setMainAvatarFromOverlay(avatar.id)">
                <span class="player-onboarding-option-title">{{ avatar.name }}</span>
                <span class="player-onboarding-option-meta">
                  {{ avatar.realm }} · {{ t('ui.player_campaign_age', { age: avatar.age }) }}
                </span>
              </button>
            </div>

            <div v-else-if="onboardingRecommendedStep === 'choose_opening'" class="player-onboarding-options">
              <button v-for="choice in onboardingOpeningChoices" :key="choice.id" class="player-onboarding-option"
                :disabled="isSubmittingOnboarding || !choice.can_select" @click="chooseOpeningFromOverlay(choice.id)">
                <span class="player-onboarding-option-title">
                  {{ playerOpeningChoiceTitle(t, choice.id) }}
                </span>
                <span class="player-onboarding-option-meta">
                  {{ playerOpeningChoiceDesc(t, choice.id) }}
                </span>
              </button>
            </div>

            <div v-if="onboardingError" class="player-onboarding-error">
              {{ onboardingError }}
            </div>

            <div class="player-onboarding-actions">
              <button class="player-onboarding-link" :disabled="isSubmittingOnboarding"
                @click="openPlayerCampaignSetup">
                {{ t('ui.player_campaign_open_setup') }}
              </button>
            </div>
          </div>
        </div>

        <GameCanvas :sidebar-width="sidebarWidth" @avatarSelected="handleSelection" @regionSelected="handleSelection" />
        <InfoPanelContainer />
      </div>
      <div class="sidebar-resizer" :class="{ 'is-resizing': isResizing }" @mousedown="onResizerMouseDown"></div>
      <aside class="sidebar" :style="{ width: sidebarWidth + 'px' }">
        <EventPanel />
      </aside>
    </div>
  </div>

  <SystemMenu :visible="showMenu" :default-tab="menuDefaultTab" :game-initialized="gameInitialized"
    :closable="canCloseMenu" @close="handleMenuCloseWrapper" @llm-ready="handleLLMReady"
    @return-to-main="handleReturnToMain" @exit-game="() => handleSplashAction('exit')" />

  <!-- Recap Overlay - 天机推演 -->
  <RecapOverlay />

  <LoadingOverlay v-if="showLoadingOverlay" :status="initStatus" />
</template>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  width: 100vw;
  height: 100vh;
  background: #000;
  color: #eee;
  overflow: hidden;
  position: relative;
}

.app-layout--shell {
  background: #000;
}

.main-content {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
}

.map-container {
  flex: 1;
  position: relative;
  background: #111;
  overflow: hidden;
}

.top-controls {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 100;
  display: flex;
  gap: 10px;
}

.player-onboarding-overlay {
  position: absolute;
  top: 18px;
  left: 18px;
  z-index: 95;
  max-width: min(420px, calc(100vw - 120px));
}

.player-onboarding-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  border: 1px solid rgba(240, 220, 180, 0.28);
  background:
    linear-gradient(180deg, rgba(24, 18, 12, 0.94), rgba(11, 10, 8, 0.92)),
    rgba(0, 0, 0, 0.82);
  box-shadow: 0 20px 48px rgba(0, 0, 0, 0.36);
  backdrop-filter: blur(12px);
}

.player-onboarding-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.player-onboarding-kicker {
  font-size: 12px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(226, 206, 171, 0.82);
}

.player-onboarding-step {
  font-size: 13px;
  color: #f5deb6;
}

.player-onboarding-desc {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: rgba(236, 232, 219, 0.84);
}

.player-onboarding-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.player-onboarding-option {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  width: 100%;
  padding: 10px 12px;
  border: 1px solid rgba(207, 181, 138, 0.2);
  background: rgba(255, 248, 235, 0.04);
  color: #f7edd6;
  cursor: pointer;
  transition: border-color 0.16s ease, background 0.16s ease, transform 0.16s ease;
}

.player-onboarding-option:hover:not(:disabled) {
  border-color: rgba(229, 197, 141, 0.46);
  background: rgba(255, 248, 235, 0.08);
  transform: translateY(-1px);
}

.player-onboarding-option:disabled {
  cursor: wait;
  opacity: 0.66;
}

.player-onboarding-option-title {
  font-size: 14px;
  font-weight: 600;
}

.player-onboarding-option-meta {
  font-size: 12px;
  color: rgba(221, 210, 190, 0.74);
}

.player-onboarding-error {
  font-size: 12px;
  color: #ff9f8a;
}

.player-onboarding-actions {
  display: flex;
  justify-content: flex-end;
}

.player-onboarding-link {
  border: 0;
  background: transparent;
  color: #e3c994;
  cursor: pointer;
  font-size: 12px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.player-onboarding-link:disabled {
  cursor: wait;
  opacity: 0.6;
}

.control-btn {
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid #444;
  color: #ddd;
  width: 40px;
  height: 40px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.control-btn-icon {
  width: 18px;
  height: 18px;
  display: inline-block;
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

.control-btn:hover {
  background: rgba(0, 0, 0, 0.8);
  border-color: #666;
  color: #fff;
}

.pause-indicator {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 90;
  pointer-events: none;
}

.pause-text {
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 14px;
  letter-spacing: 2px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(4px);
}

.sidebar-resizer {
  width: 4px;
  background: transparent;
  cursor: col-resize;
  transition: background 0.15s;
  flex-shrink: 0;
}

.sidebar-resizer:hover,
.sidebar-resizer.is-resizing {
  background: #555;
}

.sidebar {
  background: #181818;
  border-left: 1px solid #333;
  display: flex;
  flex-direction: column;
  z-index: 20;
  flex-shrink: 0;
}
</style>
