<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useI18n } from 'vue-i18n'
import { avatarApi, worldApi } from '@/api'
import { useSystemStore } from '@/stores/system'
import { useSocketStore } from '@/stores/socket'
import { logError } from '@/utils/appError'
import {
  playerCampaignStepLabel,
  playerOpeningChoiceDesc,
  playerOpeningChoiceEffect,
  playerOpeningChoiceTitle,
} from '@/utils/playerCampaign'
import houseIcon from '@/assets/icons/ui/lucide/house.svg'
import logOutIcon from '@/assets/icons/ui/lucide/log-out.svg'
import chevronRightIcon from '@/assets/icons/ui/lucide/chevron-right.svg'
import usersIcon from '@/assets/icons/ui/lucide/users.svg'
import mapIcon from '@/assets/icons/ui/lucide/map.svg'
import plusIcon from '@/assets/icons/ui/lucide/plus.svg'
import userPlusIcon from '@/assets/icons/ui/lucide/user-plus.svg'

const { t } = useI18n()
const systemStore = useSystemStore()
const socketStore = useSocketStore()
const {
  initStatus,
  viewerId,
  authSession,
  viewerProfile,
  playerProfiles,
  playerOnboarding,
  activeRoomId,
  roomIds,
  activeRoomSummary,
  roomSummaries,
  activeControllerId,
  playerControlSeatIds,
  playerControlSeats,
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
const pendingRoomMemberId = ref('')
const roomMembershipError = ref('')
const isUpdatingRoomAccess = ref(false)
const isUpdatingRoomPlan = ref(false)
const isUpdatingRoomEntitlement = ref(false)
const isCreatingPaymentOrder = ref(false)
const isSettlingPayment = ref(false)
const isReconcilingPayment = ref(false)
const isUpdatingRoomMembers = ref(false)
const isRotatingRoomInvite = ref(false)
const isJoiningRoomByInvite = ref(false)
const pendingSeatId = ref('')
const seatError = ref('')
const isSwitchingSeat = ref(false)
const pendingDisplayName = ref('')
const profileError = ref('')
const isSavingProfile = ref(false)
const onboardingError = ref('')
const isSubmittingOnboarding = ref(false)
const pendingReconcileTransferNote = ref('')
const pendingReconcilePaymentRef = ref('')
const pendingReconcileAmountVnd = ref('')

const emit = defineEmits<{
  (e: 'return-to-main'): void
  (e: 'exit-game'): void
}>()

const canManageRooms = computed(() => (
  Boolean(initStatus.value)
  && initStatus.value?.status !== 'pending'
  && initStatus.value?.status !== 'in_progress'
))
const canManageProfile = computed(() => initStatus.value?.status === 'ready')
const normalizedPendingDisplayName = computed(() => pendingDisplayName.value.trim())
const currentViewerDisplayName = computed(() => (
  viewerProfile.value?.display_name?.trim()
  || viewerId.value
))
const isRegisteredAccount = computed(() => authSession.value?.auth_type === 'password')
const accountEmail = computed(() => authSession.value?.email?.trim() || '')
const normalizedPendingAuthEmail = computed(() => pendingAuthEmail.value.trim().toLowerCase())
const normalizedPendingAuthPassword = computed(() => pendingAuthPassword.value)
const normalizedPendingAuthDisplayName = computed(() => pendingAuthDisplayName.value.trim())
const hasValidPendingAuthEmail = computed(() => (
  normalizedPendingAuthEmail.value.includes('@')
  && normalizedPendingAuthEmail.value.split('@')[1]?.includes('.')
))
const canRegisterPasswordAccount = computed(() => (
  !isSubmittingAuth.value
  && !isRegisteredAccount.value
  && hasValidPendingAuthEmail.value
  && normalizedPendingAuthPassword.value.length >= 8
))
const canLoginPasswordAccount = computed(() => (
  !isSubmittingAuth.value
  && hasValidPendingAuthEmail.value
  && normalizedPendingAuthPassword.value.length >= 8
))
const canSaveProfile = computed(() => (
  canManageProfile.value
  && !isSavingProfile.value
  && Boolean(normalizedPendingDisplayName.value)
  && normalizedPendingDisplayName.value !== (viewerProfile.value?.display_name?.trim() || '')
))
const normalizedPendingRoomId = computed(() => pendingRoomId.value.trim())
const normalizedPendingJoinRoomId = computed(() => pendingJoinRoomId.value.trim())
const normalizedPendingInviteCode = computed(() => pendingInviteCode.value.trim().toUpperCase())
const normalizedPendingRoomMemberId = computed(() => pendingRoomMemberId.value.trim())
const normalizedPendingReconcileTransferNote = computed(() => pendingReconcileTransferNote.value.trim())
const normalizedPendingReconcilePaymentRef = computed(() => pendingReconcilePaymentRef.value.trim())
const normalizedPendingReconcileAmountVnd = computed(() => pendingReconcileAmountVnd.value.trim())
const parsedPendingReconcileAmountVnd = computed(() => {
  const normalized = normalizedPendingReconcileAmountVnd.value.replace(/[^\d]/g, '')
  if (!normalized) {
    return undefined
  }
  const amount = Number.parseInt(normalized, 10)
  return Number.isFinite(amount) && amount > 0 ? amount : undefined
})
const hasValidPendingReconcileAmount = computed(() => (
  !normalizedPendingReconcileAmountVnd.value
  || parsedPendingReconcileAmountVnd.value !== undefined
))
const availableRoomIds = computed(() => roomIds.value || ['main'])
const roomEntries = computed(() => {
  const summaries = roomSummaries.value || []
  return availableRoomIds.value.map((roomId) => {
    const summary = summaries.find((item) => item.id === roomId)
      || (activeRoomSummary.value?.id === roomId ? activeRoomSummary.value : null)
    return {
      id: roomId,
      accessMode: summary?.access_mode || 'open',
      planId: summary?.plan_id?.trim() || (roomId === 'main' ? 'main_public' : 'standard_private'),
      requestedPlanId: summary?.requested_plan_id?.trim() || summary?.plan_id?.trim() || (roomId === 'main' ? 'main_public' : 'standard_private'),
      commercialProfile: summary?.commercial_profile?.trim() || 'standard',
      priceVnd: typeof summary?.price_vnd === 'number' ? summary.price_vnd : 0,
      billingCycleDays: typeof summary?.billing_cycle_days === 'number' ? summary.billing_cycle_days : 30,
      memberLimit: typeof summary?.member_limit === 'number' ? summary.member_limit : 0,
      memberSlotsRemaining: typeof summary?.member_slots_remaining === 'number'
        ? summary.member_slots_remaining
        : null,
      entitledPlanId: summary?.entitled_plan_id?.trim() || null,
      maxSelectablePlanId: summary?.max_selectable_plan_id?.trim() || null,
      billingStatus: summary?.billing_status?.trim() || (roomId === 'main' ? 'active' : 'trial'),
      billingDeadlineAt: summary?.billing_deadline_at?.trim() || '',
      billingDaysRemaining: typeof summary?.billing_days_remaining === 'number'
        ? summary.billing_days_remaining
        : null,
      billingRenewalRecommended: Boolean(summary?.billing_renewal_recommended),
      billingRenewalStage: summary?.billing_renewal_stage?.trim() || '',
      planLockedByBilling: Boolean(summary?.plan_locked_by_billing),
      saleOffers: summary?.sellable_plan_offers || [],
      pendingPaymentOrder: summary?.pending_payment_order || null,
      lastPaidOrder: summary?.last_paid_order || null,
      paymentEvents: summary?.payment_events || [],
      lastPaymentConfirmedAt: summary?.last_payment_confirmed_at?.trim() || '',
      ownerViewerId: summary?.owner_viewer_id?.trim() || null,
      memberViewerIds: summary?.member_viewer_ids || [],
      inviteCode: summary?.invite_code?.trim() || '',
      viewerHasAccess: summary?.viewer_has_access !== false,
      viewerIsOwner: Boolean(summary?.viewer_is_owner),
      isLocked: summary?.viewer_has_access === false,
      status: summary?.status || 'idle',
    }
  })
})
const currentRoomEntry = computed(() => (
  roomEntries.value.find((item) => item.id === activeRoomId.value)
  || null
))
const currentRoomAccessMode = computed(() => currentRoomEntry.value?.accessMode || 'open')
const currentRoomPlanId = computed(() => currentRoomEntry.value?.planId || 'standard_private')
const currentRoomRequestedPlanId = computed(() => currentRoomEntry.value?.requestedPlanId || currentRoomPlanId.value)
const currentRoomCommercialProfile = computed(() => currentRoomEntry.value?.commercialProfile || 'standard')
const currentRoomPriceVnd = computed(() => currentRoomEntry.value?.priceVnd || 0)
const currentRoomBillingCycleDays = computed(() => currentRoomEntry.value?.billingCycleDays || 30)
const currentRoomMemberLimit = computed(() => currentRoomEntry.value?.memberLimit || 0)
const currentRoomMemberSlotsRemaining = computed(() => currentRoomEntry.value?.memberSlotsRemaining)
const currentRoomEntitledPlanId = computed(() => currentRoomEntry.value?.entitledPlanId || currentRoomPlanId.value)
const currentRoomMaxSelectablePlanId = computed(() => currentRoomEntry.value?.maxSelectablePlanId || currentRoomEntitledPlanId.value)
const currentRoomBillingStatus = computed(() => currentRoomEntry.value?.billingStatus || 'trial')
const currentRoomBillingDeadlineAt = computed(() => currentRoomEntry.value?.billingDeadlineAt || '')
const currentRoomBillingDaysRemaining = computed(() => currentRoomEntry.value?.billingDaysRemaining)
const currentRoomBillingRenewalRecommended = computed(() => Boolean(currentRoomEntry.value?.billingRenewalRecommended))
const currentRoomPlanLockedByBilling = computed(() => Boolean(currentRoomEntry.value?.planLockedByBilling))
const currentRoomSaleOffers = computed(() => currentRoomEntry.value?.saleOffers || [])
const currentRoomPendingPaymentOrder = computed(() => currentRoomEntry.value?.pendingPaymentOrder || null)
const currentRoomLastPaidOrder = computed(() => currentRoomEntry.value?.lastPaidOrder || null)
const currentRoomPaymentEvents = computed(() => currentRoomEntry.value?.paymentEvents || [])
const currentRoomRenewalOffer = computed(() => (
  currentRoomSaleOffers.value.find((offer) => offer.plan_id === currentRoomRequestedPlanId.value)
  || currentRoomSaleOffers.value.find((offer) => offer.plan_id === currentRoomPlanId.value)
  || currentRoomSaleOffers.value.find((offer) => offer.plan_id === currentRoomEntitledPlanId.value)
  || null
))
const canManageCurrentRoomAccess = computed(() => (
  Boolean(currentRoomEntry.value?.viewerIsOwner)
  && activeRoomId.value !== 'main'
  && !isUpdatingRoomAccess.value
))
const canManageCurrentRoomPlan = computed(() => (
  Boolean(currentRoomEntry.value?.viewerIsOwner)
  && activeRoomId.value !== 'main'
  && !isUpdatingRoomPlan.value
))
const canManageCurrentRoomEntitlement = computed(() => (
  Boolean(currentRoomEntry.value?.viewerIsOwner)
  && activeRoomId.value !== 'main'
  && !isUpdatingRoomEntitlement.value
))
const canReconcileCurrentRoomPayment = computed(() => (
  canManageCurrentRoomEntitlement.value
  && !isReconcilingPayment.value
  && Boolean(normalizedPendingReconcileTransferNote.value)
  && hasValidPendingReconcileAmount.value
))
const currentRoomMembers = computed(() => currentRoomEntry.value?.memberViewerIds || [])
const currentRoomInviteCode = computed(() => currentRoomEntry.value?.inviteCode || '')
const roomPlanOptions = computed(() => ([
  {
    id: 'main_public',
    label: t('ui.control_room_plan_public'),
  },
  {
    id: 'standard_private',
    label: t('ui.control_room_plan_standard'),
  },
  {
    id: 'story_rich_private',
    label: t('ui.control_room_plan_story_rich'),
  },
  {
    id: 'internal_full_private',
    label: t('ui.control_room_plan_internal'),
  },
]))
const roomEntitlementPlanOptions = computed(() => (
  roomPlanOptions.value.filter((plan) => plan.id !== 'main_public')
))
const billingStatusOptions = computed(() => ([
  { id: 'trial', label: t('ui.control_room_billing_trial') },
  { id: 'active', label: t('ui.control_room_billing_active') },
  { id: 'grace', label: t('ui.control_room_billing_grace') },
  { id: 'expired', label: t('ui.control_room_billing_expired') },
]))
const currentRoomPlanLabel = computed(() => (
  roomPlanOptions.value.find((plan) => plan.id === currentRoomPlanId.value)?.label
  || currentRoomPlanId.value
))
const currentRoomRequestedPlanLabel = computed(() => (
  roomPlanOptions.value.find((plan) => plan.id === currentRoomRequestedPlanId.value)?.label
  || currentRoomRequestedPlanId.value
))
const currentRoomEntitledPlanLabel = computed(() => (
  roomPlanOptions.value.find((plan) => plan.id === currentRoomEntitledPlanId.value)?.label
  || currentRoomEntitledPlanId.value
))
const canAddRoomMember = computed(() => (
  canManageCurrentRoomAccess.value
  && !isUpdatingRoomMembers.value
  && Boolean(normalizedPendingRoomMemberId.value)
  && !currentRoomMembers.value.includes(normalizedPendingRoomMemberId.value)
  && (currentRoomMemberLimit.value <= 0 || (currentRoomMemberSlotsRemaining.value ?? 0) > 0)
))
const canRotateCurrentRoomInvite = computed(() => (
  canManageCurrentRoomAccess.value
  && currentRoomAccessMode.value === 'private'
  && !isRotatingRoomInvite.value
))
const canCreateRoom = computed(() => (
  canManageRooms.value
  && !isSwitchingRoom.value
  && Boolean(normalizedPendingRoomId.value)
  && normalizedPendingRoomId.value !== activeRoomId.value
))
const canJoinPrivateRoom = computed(() => (
  canManageRooms.value
  && !isJoiningRoomByInvite.value
  && Boolean(normalizedPendingJoinRoomId.value)
  && Boolean(normalizedPendingInviteCode.value)
))
const canManageSeats = computed(() => initStatus.value?.status === 'ready')
const normalizedPendingSeatId = computed(() => pendingSeatId.value.trim())
const availableSeatIds = computed(() => playerControlSeatIds.value || ['local'])
const seatEntries = computed(() => {
  const summaries = playerControlSeats.value || []
  return availableSeatIds.value.map((seatId) => {
    const summary = summaries.find((item) => item.id === seatId)
    const holderId = summary?.holder_id?.trim() || null
    const holderDisplayName = summary?.holder_display_name?.trim() || ''
    const isMine = holderId === viewerId.value
    return {
      id: seatId,
      holderId,
      holderDisplayName,
      isMine,
      isClaimed: Boolean(holderId),
      isLockedByOther: Boolean(holderId && !isMine),
    }
  })
})
const roomPlayerEntries = computed(() => playerProfiles.value || [])
const onboardingState = computed(() => playerOnboarding.value)
const onboardingClaimableSects = computed(() => onboardingState.value?.claimable_sects || [])
const onboardingMainAvatarCandidates = computed(() => onboardingState.value?.main_avatar_candidates || [])
const onboardingOpeningChoices = computed(() => onboardingState.value?.opening_choices || [])
const onboardingRecommendedStep = computed(() => onboardingState.value?.recommended_step || 'claim_sect')
const onboardingReady = computed(() => Boolean(onboardingState.value?.ready))
const canRunOnboardingAction = computed(() => (
  initStatus.value?.status === 'ready'
  && !isSubmittingOnboarding.value
))
const canReleaseActiveSeat = computed(() => {
  const activeSeat = seatEntries.value.find((item) => item.id === activeControllerId.value)
  return Boolean(activeSeat?.isMine) && !isSwitchingSeat.value
})
const canCreateSeat = computed(() => (
  canManageSeats.value
  && !isSwitchingSeat.value
  && Boolean(normalizedPendingSeatId.value)
  && normalizedPendingSeatId.value !== activeControllerId.value
))

function getRoomPlanRank(planId: string) {
  const index = roomPlanOptions.value.findIndex((plan) => plan.id === planId)
  return index >= 0 ? index : Number.MAX_SAFE_INTEGER
}

function isPlanSelectableByCurrentEntitlement(planId: string) {
  return getRoomPlanRank(planId) <= getRoomPlanRank(currentRoomMaxSelectablePlanId.value)
}

function billingStatusLabel(status: string) {
  return billingStatusOptions.value.find((item) => item.id === status)?.label || status
}

function formatPriceVnd(amount: number) {
  return `${new Intl.NumberFormat('vi-VN').format(Math.max(0, Math.trunc(amount || 0)))}đ`
}

function formatDateTime(value: string) {
  if (!value) {
    return ''
  }
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return value
  }
  return parsed.toLocaleString('vi-VN')
}

function formatPaymentEventTitle(event: {
  event_type?: string
  order_id?: string | null
  target_plan_id?: string | null
}) {
  const parts = [event.event_type || 'event']
  if (event.order_id) {
    parts.push(event.order_id)
  }
  if (event.target_plan_id) {
    parts.push(event.target_plan_id)
  }
  return parts.join(' · ')
}

function formatPaymentEventMeta(event: {
  status?: string
  source?: string
  amount_vnd?: number | null
  payment_ref?: string | null
  note?: string | null
  timestamp?: string
}) {
  const parts = []
  if (event.status) {
    parts.push(event.status)
  }
  if (event.source) {
    parts.push(event.source)
  }
  if (typeof event.amount_vnd === 'number') {
    parts.push(formatPriceVnd(event.amount_vnd))
  }
  if (event.payment_ref) {
    parts.push(event.payment_ref)
  }
  if (event.note) {
    parts.push(event.note)
  }
  if (event.timestamp) {
    parts.push(new Date(event.timestamp).toLocaleString('vi-VN'))
  }
  return parts.join(' · ')
}

onMounted(() => {
  void systemStore.fetchInitStatus()
})

watch(
  viewerProfile,
  (value) => {
    pendingDisplayName.value = value?.display_name || ''
  },
  { immediate: true },
)

watch(
  onboardingState,
  () => {
    onboardingError.value = ''
  },
  { immediate: true },
)

watch(
  [activeRoomId, currentRoomPendingPaymentOrder],
  ([, pendingOrder]) => {
    pendingReconcileTransferNote.value = pendingOrder?.transfer_note || ''
    pendingReconcilePaymentRef.value = ''
    pendingReconcileAmountVnd.value = typeof pendingOrder?.amount_vnd === 'number'
      ? String(pendingOrder.amount_vnd)
      : ''
  },
  { immediate: true },
)

async function switchRoom(roomId: string) {
  if (!canManageRooms.value || isSwitchingRoom.value) {
    return
  }

  const targetRoom = roomEntries.value.find((item) => item.id === roomId)
  if (targetRoom?.isLocked) {
    roomError.value = t('ui.control_room_access_denied')
    return
  }

  const normalized = roomId.trim()
  if (!normalized || normalized === activeRoomId.value) {
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
    logError('SystemMenuOtherTab.switchRoom', error)
    roomError.value = t('ui.control_room_switch_failed')
  } finally {
    isSwitchingRoom.value = false
  }
}

async function createOrSwitchRoom() {
  await switchRoom(normalizedPendingRoomId.value)
}

function roomLabel(entry: {
  id: string
  accessMode: string
  isLocked: boolean
}) {
  if (entry.isLocked) {
    return `${entry.id} · ${t('ui.control_room_status_locked')}`
  }
  if (entry.accessMode === 'private') {
    return `${entry.id} · ${t('ui.control_room_status_private')}`
  }
  return `${entry.id} · ${t('ui.control_room_status_open')}`
}

async function switchSeat(controllerId: string) {
  if (!canManageSeats.value || isSwitchingSeat.value) {
    return
  }

  const normalized = controllerId.trim()
  if (!normalized || normalized === activeControllerId.value) {
    return
  }

  isSwitchingSeat.value = true
  seatError.value = ''
  try {
    const result = await systemStore.switchControlSeat(normalized)
    if (!result) {
      seatError.value = t('ui.control_seat_switch_failed')
      return
    }
    pendingSeatId.value = ''
  } catch (error) {
    logError('SystemMenuOtherTab.switchSeat', error)
    seatError.value = t('ui.control_seat_switch_failed')
  } finally {
    isSwitchingSeat.value = false
  }
}

async function createOrSwitchSeat() {
  await switchSeat(normalizedPendingSeatId.value)
}

function seatLabel(entry: {
  id: string
  holderId: string | null
  holderDisplayName: string
  isMine: boolean
  isClaimed: boolean
}) {
  if (entry.isMine) {
    return `${entry.id} · ${t('ui.control_seat_status_yours')}`
  }
  if (!entry.isClaimed) {
    return `${entry.id} · ${t('ui.control_seat_status_open')}`
  }
  if (entry.holderDisplayName) {
    return `${entry.id} · ${entry.holderDisplayName} · ${t('ui.control_seat_status_claimed')}`
  }
  return `${entry.id} · ${t('ui.control_seat_status_claimed')}`
}

async function releaseActiveSeat() {
  if (!canReleaseActiveSeat.value || isSwitchingSeat.value) {
    return
  }

  isSwitchingSeat.value = true
  seatError.value = ''
  try {
    const result = await systemStore.releaseControlSeat(activeControllerId.value)
    if (!result) {
      seatError.value = t('ui.control_seat_release_failed')
    }
  } catch (error) {
    logError('SystemMenuOtherTab.releaseActiveSeat', error)
    seatError.value = t('ui.control_seat_release_failed')
  } finally {
    isSwitchingSeat.value = false
  }
}

function playerMetaLabel(profile: {
  viewer_id: string
  controller_id?: string | null
  is_active_controller?: boolean
}) {
  const parts = []
  if (profile.viewer_id === viewerId.value) {
    parts.push(t('ui.player_identity_status_you'))
  }
  if (profile.is_active_controller) {
    parts.push(t('ui.player_identity_status_active'))
  }
  if (profile.controller_id) {
    parts.push(t('ui.player_identity_seat', { id: profile.controller_id }))
  }
  return parts.join(' · ')
}

function onboardingStepLabel(step: string) {
  return playerCampaignStepLabel(t, step)
}

function formatOnboardingSectMeta(sect: {
  member_count: number
  is_owned: boolean
}) {
  const parts = [t('ui.player_campaign_members', { count: sect.member_count })]
  if (sect.is_owned) {
    parts.push(t('ui.player_campaign_owned'))
  }
  return parts.join(' · ')
}

function formatOnboardingAvatarMeta(avatar: {
  realm: string
  age: number
  base_battle_strength: number
  is_current: boolean
}) {
  const parts = [
    avatar.realm,
    t('ui.player_campaign_age', { age: avatar.age }),
    t('ui.player_campaign_power', { value: avatar.base_battle_strength }),
  ]
  if (avatar.is_current) {
    parts.push(t('ui.player_campaign_main_avatar_current'))
  }
  return parts.join(' · ')
}

function formatOnboardingOpeningMeta(choice: {
  id: string
  is_selected: boolean
}) {
  const parts = [
    playerOpeningChoiceDesc(t, choice.id),
    playerOpeningChoiceEffect(t, choice.id),
  ]
  if (choice.is_selected) {
    parts.push(t('ui.player_campaign_opening_selected'))
  }
  return parts.join(' · ')
}

async function claimSectFromOnboarding(sectId: number) {
  if (!canRunOnboardingAction.value) {
    return
  }
  isSubmittingOnboarding.value = true
  onboardingError.value = ''
  try {
    await worldApi.claimSect({ sect_id: sectId })
    await systemStore.fetchInitStatus()
  } catch (error) {
    logError('SystemMenuOtherTab.claimSectFromOnboarding', error)
    onboardingError.value = t('ui.player_campaign_claim_failed')
  } finally {
    isSubmittingOnboarding.value = false
  }
}

async function setMainAvatarFromOnboarding(avatarId: string) {
  if (!canRunOnboardingAction.value) {
    return
  }
  isSubmittingOnboarding.value = true
  onboardingError.value = ''
  try {
    await avatarApi.setMainAvatar({ avatar_id: avatarId })
    await systemStore.fetchInitStatus()
  } catch (error) {
    logError('SystemMenuOtherTab.setMainAvatarFromOnboarding', error)
    onboardingError.value = t('ui.player_campaign_main_avatar_failed')
  } finally {
    isSubmittingOnboarding.value = false
  }
}

async function chooseOpeningFromOnboarding(choiceId: string) {
  if (!canRunOnboardingAction.value) {
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
    logError('SystemMenuOtherTab.chooseOpeningFromOnboarding', error)
    onboardingError.value = t('ui.player_campaign_opening_failed')
  } finally {
    isSubmittingOnboarding.value = false
  }
}

async function savePlayerProfile() {
  if (!canSaveProfile.value || isSavingProfile.value) {
    return
  }

  isSavingProfile.value = true
  profileError.value = ''
  try {
    const result = await systemStore.updatePlayerProfile(normalizedPendingDisplayName.value)
    if (!result) {
      profileError.value = t('ui.player_identity_save_failed')
    }
  } catch (error) {
    logError('SystemMenuOtherTab.savePlayerProfile', error)
    profileError.value = t('ui.player_identity_save_failed')
  } finally {
    isSavingProfile.value = false
  }
}

async function updateCurrentRoomAccess(accessMode: 'open' | 'private') {
  if (!canManageCurrentRoomAccess.value || isUpdatingRoomAccess.value || currentRoomAccessMode.value === accessMode) {
    return
  }
  isUpdatingRoomAccess.value = true
  roomMembershipError.value = ''
  try {
    const result = await systemStore.updateWorldRoomAccess(activeRoomId.value, accessMode)
    if (!result) {
      roomMembershipError.value = t('ui.control_room_access_update_failed')
    }
  } catch (error) {
    logError('SystemMenuOtherTab.updateCurrentRoomAccess', error)
    roomMembershipError.value = t('ui.control_room_access_update_failed')
  } finally {
    isUpdatingRoomAccess.value = false
  }
}

async function updateCurrentRoomPlan(planId: string) {
  if (
    !canManageCurrentRoomPlan.value
    || isUpdatingRoomPlan.value
    || currentRoomRequestedPlanId.value === planId
    || !isPlanSelectableByCurrentEntitlement(planId)
  ) {
    return
  }
  isUpdatingRoomPlan.value = true
  roomMembershipError.value = ''
  try {
    const result = await systemStore.updateWorldRoomPlan(activeRoomId.value, planId)
    if (!result) {
      roomMembershipError.value = t('ui.control_room_plan_update_failed')
    }
  } catch (error) {
    logError('SystemMenuOtherTab.updateCurrentRoomPlan', error)
    roomMembershipError.value = t('ui.control_room_plan_update_failed')
  } finally {
    isUpdatingRoomPlan.value = false
  }
}

async function updateCurrentRoomEntitlement(
  billingStatus: 'trial' | 'active' | 'grace' | 'expired',
  entitledPlanId: string,
) {
  if (
    !canManageCurrentRoomEntitlement.value
    || isUpdatingRoomEntitlement.value
    || !entitledPlanId.trim()
  ) {
    return
  }
  if (
    currentRoomBillingStatus.value === billingStatus
    && currentRoomEntitledPlanId.value === entitledPlanId
  ) {
    return
  }
  isUpdatingRoomEntitlement.value = true
  roomMembershipError.value = ''
  try {
    const result = await systemStore.updateWorldRoomEntitlement(
      activeRoomId.value,
      billingStatus,
      entitledPlanId,
    )
    if (!result) {
      roomMembershipError.value = t('ui.control_room_entitlement_update_failed')
    }
  } catch (error) {
    logError('SystemMenuOtherTab.updateCurrentRoomEntitlement', error)
    roomMembershipError.value = t('ui.control_room_entitlement_update_failed')
  } finally {
    isUpdatingRoomEntitlement.value = false
  }
}

async function setCurrentRoomBillingStatus(status: string) {
  if (status !== 'trial' && status !== 'active' && status !== 'grace' && status !== 'expired') {
    return
  }
  await updateCurrentRoomEntitlement(status, currentRoomEntitledPlanId.value)
}

async function setCurrentRoomEntitledPlan(planId: string) {
  await updateCurrentRoomEntitlement(currentRoomBillingStatus.value as 'trial' | 'active' | 'grace' | 'expired', planId)
}

async function createPaymentOrderForPlan(planId: string) {
  if (!canManageCurrentRoomEntitlement.value || isCreatingPaymentOrder.value) {
    return
  }
  isCreatingPaymentOrder.value = true
  roomMembershipError.value = ''
  try {
    const result = await systemStore.createWorldRoomPaymentOrder(activeRoomId.value, planId)
    if (!result) {
      roomMembershipError.value = t('ui.control_room_payment_order_create_failed')
    }
  } catch (error) {
    logError('SystemMenuOtherTab.createPaymentOrderForPlan', error)
    roomMembershipError.value = t('ui.control_room_payment_order_create_failed')
  } finally {
    isCreatingPaymentOrder.value = false
  }
}

async function createRenewalPaymentOrder() {
  const offer = currentRoomRenewalOffer.value
  if (!offer) {
    return
  }
  await createPaymentOrderForPlan(offer.plan_id)
}

async function settlePendingPaymentOrder() {
  const pendingOrder = currentRoomPendingPaymentOrder.value
  if (!pendingOrder?.order_id || !canManageCurrentRoomEntitlement.value || isSettlingPayment.value) {
    return
  }
  isSettlingPayment.value = true
  roomMembershipError.value = ''
  try {
    const result = await systemStore.settleWorldRoomPayment(
      activeRoomId.value,
      pendingOrder.order_id,
      undefined,
      pendingOrder.amount_vnd,
    )
    if (!result) {
      roomMembershipError.value = t('ui.control_room_payment_settle_failed')
    }
  } catch (error) {
    logError('SystemMenuOtherTab.settlePendingPaymentOrder', error)
    roomMembershipError.value = t('ui.control_room_payment_settle_failed')
  } finally {
    isSettlingPayment.value = false
  }
}

async function reconcileCurrentRoomPayment() {
  if (!canReconcileCurrentRoomPayment.value || isReconcilingPayment.value) {
    return
  }
  isReconcilingPayment.value = true
  roomMembershipError.value = ''
  try {
    const result = await systemStore.reconcileWorldRoomPayment(
      normalizedPendingReconcileTransferNote.value,
      normalizedPendingReconcilePaymentRef.value || undefined,
      parsedPendingReconcileAmountVnd.value,
    )
    if (!result) {
      roomMembershipError.value = t('ui.control_room_payment_reconcile_failed')
      return
    }
    pendingReconcilePaymentRef.value = ''
  } catch (error) {
    logError('SystemMenuOtherTab.reconcileCurrentRoomPayment', error)
    roomMembershipError.value = t('ui.control_room_payment_reconcile_failed')
  } finally {
    isReconcilingPayment.value = false
  }
}

async function addCurrentRoomMember() {
  if (!canAddRoomMember.value || isUpdatingRoomMembers.value) {
    return
  }
  isUpdatingRoomMembers.value = true
  roomMembershipError.value = ''
  try {
    const result = await systemStore.addWorldRoomMember(
      activeRoomId.value,
      normalizedPendingRoomMemberId.value,
    )
    if (!result) {
      roomMembershipError.value = t('ui.control_room_member_add_failed')
      return
    }
    pendingRoomMemberId.value = ''
  } catch (error) {
    logError('SystemMenuOtherTab.addCurrentRoomMember', error)
    roomMembershipError.value = t('ui.control_room_member_add_failed')
  } finally {
    isUpdatingRoomMembers.value = false
  }
}

async function removeCurrentRoomMember(memberViewerId: string) {
  if (!canManageCurrentRoomAccess.value || isUpdatingRoomMembers.value) {
    return
  }
  isUpdatingRoomMembers.value = true
  roomMembershipError.value = ''
  try {
    const result = await systemStore.removeWorldRoomMember(activeRoomId.value, memberViewerId)
    if (!result) {
      roomMembershipError.value = t('ui.control_room_member_remove_failed')
    }
  } catch (error) {
    logError('SystemMenuOtherTab.removeCurrentRoomMember', error)
    roomMembershipError.value = t('ui.control_room_member_remove_failed')
  } finally {
    isUpdatingRoomMembers.value = false
  }
}

async function rotateCurrentRoomInvite() {
  if (!canRotateCurrentRoomInvite.value || isRotatingRoomInvite.value) {
    return
  }
  isRotatingRoomInvite.value = true
  roomMembershipError.value = ''
  try {
    const result = await systemStore.rotateWorldRoomInvite(activeRoomId.value)
    if (!result) {
      roomMembershipError.value = t('ui.control_room_invite_rotate_failed')
    }
  } catch (error) {
    logError('SystemMenuOtherTab.rotateCurrentRoomInvite', error)
    roomMembershipError.value = t('ui.control_room_invite_rotate_failed')
  } finally {
    isRotatingRoomInvite.value = false
  }
}

async function joinPrivateRoomByInvite() {
  if (!canJoinPrivateRoom.value || isJoiningRoomByInvite.value) {
    return
  }
  isJoiningRoomByInvite.value = true
  roomMembershipError.value = ''
  try {
    const result = await systemStore.joinWorldRoomByInvite(
      normalizedPendingJoinRoomId.value,
      normalizedPendingInviteCode.value,
    )
    if (!result) {
      roomMembershipError.value = t('ui.control_room_join_failed')
      return
    }
    socketStore.switchRoom(normalizedPendingJoinRoomId.value)
    pendingJoinRoomId.value = ''
    pendingInviteCode.value = ''
  } catch (error) {
    logError('SystemMenuOtherTab.joinPrivateRoomByInvite', error)
    roomMembershipError.value = t('ui.control_room_join_failed')
  } finally {
    isJoiningRoomByInvite.value = false
  }
}

async function submitRegisterPasswordAccount() {
  if (!canRegisterPasswordAccount.value) {
    return
  }
  isSubmittingAuth.value = true
  authError.value = ''
  try {
    const result = await systemStore.registerPasswordSession(
      normalizedPendingAuthEmail.value,
      normalizedPendingAuthPassword.value,
      normalizedPendingAuthDisplayName.value || undefined,
    )
    if (!result) {
      authError.value = t('ui.auth_register_failed')
      return
    }
    pendingAuthPassword.value = ''
    if (normalizedPendingAuthDisplayName.value) {
      pendingDisplayName.value = normalizedPendingAuthDisplayName.value
    }
    socketStore.switchRoom(activeRoomId.value)
  } catch (error) {
    logError('SystemMenuOtherTab.submitRegisterPasswordAccount', error)
    authError.value = t('ui.auth_register_failed')
  } finally {
    isSubmittingAuth.value = false
  }
}

async function submitLoginPasswordAccount() {
  if (!canLoginPasswordAccount.value) {
    return
  }
  isSubmittingAuth.value = true
  authError.value = ''
  try {
    const result = await systemStore.loginPasswordSession(
      normalizedPendingAuthEmail.value,
      normalizedPendingAuthPassword.value,
    )
    if (!result) {
      authError.value = t('ui.auth_login_failed')
      return
    }
    pendingAuthPassword.value = ''
    pendingAuthDisplayName.value = ''
    socketStore.switchRoom(activeRoomId.value)
  } catch (error) {
    logError('SystemMenuOtherTab.submitLoginPasswordAccount', error)
    authError.value = t('ui.auth_login_failed')
  } finally {
    isSubmittingAuth.value = false
  }
}

async function logoutPasswordAccount() {
  if (isSubmittingAuth.value) {
    return
  }
  isSubmittingAuth.value = true
  authError.value = ''
  try {
    const ok = await systemStore.logoutSession()
    if (!ok) {
      authError.value = t('ui.auth_logout_failed')
      return
    }
    pendingAuthPassword.value = ''
    socketStore.switchRoom(activeRoomId.value)
  } catch (error) {
    logError('SystemMenuOtherTab.logoutPasswordAccount', error)
    authError.value = t('ui.auth_logout_failed')
  } finally {
    isSubmittingAuth.value = false
  }
}
</script>

<template>
  <div class="other-panel-container">
    <div class="panel-header">
      <h3>{{ t('ui.other_options') }}</h3>
      <p class="description">{{ t('ui.other_options_desc') }}</p>
    </div>

    <div class="seat-panel">
      <div class="seat-panel-header">
        <div class="seat-panel-title-wrap">
          <div class="btn-icon seat-icon" :style="{ '--icon-url': `url(${logOutIcon})` }" aria-hidden="true"></div>
          <div>
            <div class="seat-panel-title">{{ t('ui.auth_title') }}</div>
            <div class="seat-panel-desc">{{ t('ui.auth_desc') }}</div>
          </div>
        </div>
        <div class="seat-current">
          {{ isRegisteredAccount ? t('ui.auth_status_registered') : t('ui.auth_status_guest') }}
        </div>
      </div>

      <div class="seat-panel-body">
        <div v-if="isRegisteredAccount" class="seat-unavailable">
          <div>{{ t('ui.auth_email_label') }}: {{ accountEmail || t('ui.auth_email_missing') }}</div>
          <button
            type="button"
            class="seat-create-btn seat-create-btn--secondary"
            :disabled="isSubmittingAuth"
            @click="logoutPasswordAccount"
            v-sound
          >
            {{ t('ui.auth_logout') }}
          </button>
        </div>

        <template v-else>
          <div class="seat-chip-row">
            <button
              type="button"
              class="seat-chip"
              :class="{ active: authMode === 'register' }"
              :disabled="isSubmittingAuth"
              @click="authMode = 'register'"
              v-sound
            >
              {{ t('ui.auth_mode_register') }}
            </button>
            <button
              type="button"
              class="seat-chip"
              :class="{ active: authMode === 'login' }"
              :disabled="isSubmittingAuth"
              @click="authMode = 'login'"
              v-sound
            >
              {{ t('ui.auth_mode_login') }}
            </button>
          </div>

          <div class="seat-create-row seat-create-row--stack">
            <input
              v-model="pendingAuthEmail"
              class="seat-input"
              type="email"
              autocomplete="email"
              :placeholder="t('ui.auth_email_placeholder')"
            />
            <input
              v-model="pendingAuthPassword"
              class="seat-input"
              type="password"
              autocomplete="current-password"
              :placeholder="t('ui.auth_password_placeholder')"
              @keydown.enter.prevent="authMode === 'register' ? submitRegisterPasswordAccount() : submitLoginPasswordAccount()"
            />
            <input
              v-if="authMode === 'register'"
              v-model="pendingAuthDisplayName"
              class="seat-input"
              type="text"
              :placeholder="t('ui.auth_display_name_placeholder')"
              @keydown.enter.prevent="submitRegisterPasswordAccount"
            />
            <button
              v-if="authMode === 'register'"
              type="button"
              class="seat-create-btn"
              :disabled="!canRegisterPasswordAccount"
              @click="submitRegisterPasswordAccount"
              v-sound
            >
              {{ t('ui.auth_register_submit') }}
            </button>
            <button
              v-else
              type="button"
              class="seat-create-btn"
              :disabled="!canLoginPasswordAccount"
              @click="submitLoginPasswordAccount"
              v-sound
            >
              {{ t('ui.auth_login_submit') }}
            </button>
          </div>
          <div class="seat-panel-desc">{{ t('ui.auth_hint_play_now') }}</div>
          <div v-if="authError" class="seat-error">{{ authError }}</div>
        </template>
      </div>
    </div>

    <div class="seat-panel">
      <div class="seat-panel-header">
        <div class="seat-panel-title-wrap">
          <div class="btn-icon seat-icon" :style="{ '--icon-url': `url(${userPlusIcon})` }" aria-hidden="true"></div>
          <div>
            <div class="seat-panel-title">{{ t('ui.player_identity_title') }}</div>
            <div class="seat-panel-desc">{{ t('ui.player_identity_desc') }}</div>
          </div>
        </div>
        <div class="seat-current">{{ t('ui.player_identity_current', { id: currentViewerDisplayName }) }}</div>
      </div>

      <div v-if="canManageProfile" class="seat-panel-body">
        <div class="seat-create-row">
          <input
            v-model="pendingDisplayName"
            class="seat-input"
            type="text"
            :placeholder="t('ui.player_identity_placeholder')"
            @keydown.enter.prevent="savePlayerProfile"
          />
          <button
            type="button"
            class="seat-create-btn"
            :disabled="!canSaveProfile"
            @click="savePlayerProfile"
            v-sound
          >
            {{ t('ui.player_identity_save') }}
          </button>
        </div>

        <div class="player-roster">
          <div class="player-roster-title">{{ t('ui.player_identity_roster_title') }}</div>
          <div v-if="roomPlayerEntries.length" class="player-roster-list">
            <div
              v-for="profile in roomPlayerEntries"
              :key="profile.viewer_id"
              class="player-roster-item"
              :class="{ active: profile.viewer_id === viewerId }"
            >
              <div class="player-roster-name">
                {{ profile.display_name || profile.viewer_id }}
              </div>
              <div class="player-roster-meta">
                {{ playerMetaLabel(profile) || profile.viewer_id }}
              </div>
            </div>
          </div>
          <div v-else class="seat-unavailable">{{ t('ui.player_identity_roster_empty') }}</div>
        </div>

        <div v-if="profileError" class="seat-error">{{ profileError }}</div>
      </div>

      <div v-else class="seat-unavailable">{{ t('ui.control_seats_unavailable') }}</div>
    </div>

    <div class="seat-panel">
      <div class="seat-panel-header">
        <div class="seat-panel-title-wrap">
          <div class="btn-icon seat-icon" :style="{ '--icon-url': `url(${usersIcon})` }" aria-hidden="true"></div>
          <div>
            <div class="seat-panel-title">{{ t('ui.player_campaign_title') }}</div>
            <div class="seat-panel-desc">{{ t('ui.player_campaign_desc') }}</div>
          </div>
        </div>
        <div class="seat-current">{{ onboardingStepLabel(onboardingRecommendedStep) }}</div>
      </div>

      <div v-if="canManageProfile && onboardingState" class="seat-panel-body">
        <div class="room-access-summary">
          <span>
            {{ t('ui.player_campaign_current_sect') }}
            {{ onboardingState.owned_sect_name || t('ui.player_campaign_unclaimed') }}
          </span>
          <span>
            {{ t('ui.player_campaign_current_main_avatar') }}
            {{ onboardingState.main_avatar_name || t('ui.player_campaign_unselected') }}
          </span>
          <span>
            {{ t('ui.player_campaign_current_opening') }}
            {{
              onboardingState.opening_choice_id
                ? playerOpeningChoiceTitle(t, onboardingState.opening_choice_id)
                : t('ui.player_campaign_opening_empty')
            }}
          </span>
          <span>
            {{ t('ui.player_campaign_intervention_points', {
              current: onboardingState.intervention_points,
              max: onboardingState.intervention_points_max,
            }) }}
          </span>
        </div>

        <div v-if="onboardingRecommendedStep === 'claim_sect'" class="player-roster">
          <div class="player-roster-title">{{ t('ui.player_campaign_claim_title') }}</div>
          <div v-if="onboardingClaimableSects.length" class="player-roster-list">
            <div
              v-for="sect in onboardingClaimableSects"
              :key="sect.id"
              class="player-roster-item"
              :class="{ active: sect.is_owned }"
            >
              <div class="player-roster-name">{{ sect.name }}</div>
              <div class="player-roster-meta">{{ formatOnboardingSectMeta(sect) }}</div>
              <button
                type="button"
                class="seat-create-btn"
                :disabled="!canRunOnboardingAction || !sect.can_claim"
                @click="claimSectFromOnboarding(sect.id)"
                v-sound
              >
                {{ sect.is_owned ? t('ui.player_campaign_claimed') : t('ui.player_campaign_claim_action') }}
              </button>
            </div>
          </div>
          <div v-else class="seat-unavailable">{{ t('ui.player_campaign_claim_empty') }}</div>
        </div>

        <div v-else-if="onboardingRecommendedStep === 'set_main_avatar'" class="player-roster">
          <div class="player-roster-title">{{ t('ui.player_campaign_main_avatar_title') }}</div>
          <div v-if="onboardingMainAvatarCandidates.length" class="player-roster-list">
            <div
              v-for="avatar in onboardingMainAvatarCandidates"
              :key="avatar.id"
              class="player-roster-item"
              :class="{ active: avatar.is_current }"
            >
              <div class="player-roster-name">{{ avatar.name }}</div>
              <div class="player-roster-meta">{{ formatOnboardingAvatarMeta(avatar) }}</div>
              <button
                type="button"
                class="seat-create-btn"
                :disabled="!canRunOnboardingAction || avatar.is_current"
                @click="setMainAvatarFromOnboarding(avatar.id)"
                v-sound
              >
                {{ avatar.is_current ? t('ui.player_campaign_main_avatar_selected') : t('ui.player_campaign_main_avatar_action') }}
              </button>
            </div>
          </div>
          <div v-else class="seat-unavailable">{{ t('ui.player_campaign_main_avatar_empty') }}</div>
        </div>

        <div v-else-if="onboardingRecommendedStep === 'choose_opening'" class="player-roster">
          <div class="player-roster-title">{{ t('ui.player_campaign_opening_title') }}</div>
          <div v-if="onboardingOpeningChoices.length" class="player-roster-list">
            <div
              v-for="choice in onboardingOpeningChoices"
              :key="choice.id"
              class="player-roster-item"
              :class="{ active: choice.is_selected }"
            >
              <div class="player-roster-name">{{ playerOpeningChoiceTitle(t, choice.id) }}</div>
              <div class="player-roster-meta">{{ formatOnboardingOpeningMeta(choice) }}</div>
              <button
                type="button"
                class="seat-create-btn"
                :disabled="!canRunOnboardingAction || !choice.can_select"
                @click="chooseOpeningFromOnboarding(choice.id)"
                v-sound
              >
                {{ choice.is_selected ? t('ui.player_campaign_opening_selected') : t('ui.player_campaign_opening_action') }}
              </button>
            </div>
          </div>
          <div v-else class="seat-unavailable">{{ t('ui.player_campaign_opening_empty') }}</div>
        </div>

        <div v-else class="seat-unavailable">
          {{ t('ui.player_campaign_ready_desc') }}
        </div>

        <div v-if="onboardingError" class="seat-error">{{ onboardingError }}</div>
      </div>

      <div v-else class="seat-unavailable">{{ t('ui.control_seats_unavailable') }}</div>
    </div>

    <div class="seat-panel">
      <div class="seat-panel-header">
        <div class="seat-panel-title-wrap">
          <div class="btn-icon seat-icon" :style="{ '--icon-url': `url(${mapIcon})` }" aria-hidden="true"></div>
          <div>
            <div class="seat-panel-title">{{ t('ui.control_rooms_title') }}</div>
            <div class="seat-panel-desc">{{ t('ui.control_rooms_desc') }}</div>
          </div>
        </div>
        <div class="seat-current">{{ t('ui.control_rooms_current', { id: activeRoomId }) }}</div>
      </div>

      <div v-if="canManageRooms" class="seat-panel-body">
        <div class="seat-chip-row">
          <button
            v-for="room in roomEntries"
            :key="room.id"
            type="button"
            class="seat-chip"
            :class="{ active: room.id === activeRoomId, locked: room.isLocked }"
            :disabled="isSwitchingRoom || room.id === activeRoomId || room.isLocked"
            @click="switchRoom(room.id)"
            v-sound
          >
            {{ roomLabel(room) }}
          </button>
        </div>

        <div class="seat-create-row">
          <input
            v-model="pendingRoomId"
            class="seat-input"
            type="text"
            :placeholder="t('ui.control_rooms_placeholder')"
            @keydown.enter.prevent="createOrSwitchRoom"
          />
          <button
            type="button"
            class="seat-create-btn"
            :disabled="!canCreateRoom"
            @click="createOrSwitchRoom"
            v-sound
          >
            <span class="btn-icon seat-create-icon" :style="{ '--icon-url': `url(${plusIcon})` }" aria-hidden="true"></span>
            {{ t('ui.control_rooms_create') }}
          </button>
        </div>

        <div class="room-access-panel">
          <div class="player-roster-title">{{ t('ui.control_room_join_title') }}</div>
          <div class="seat-create-row">
            <input
              v-model="pendingJoinRoomId"
              class="seat-input"
              type="text"
              :placeholder="t('ui.control_room_join_room_placeholder')"
            />
            <input
              v-model="pendingInviteCode"
              class="seat-input"
              type="text"
              :placeholder="t('ui.control_room_join_code_placeholder')"
              @keydown.enter.prevent="joinPrivateRoomByInvite"
            />
            <button
              type="button"
              class="seat-create-btn"
              :disabled="!canJoinPrivateRoom"
              @click="joinPrivateRoomByInvite"
              v-sound
            >
              {{ t('ui.control_room_join_action') }}
            </button>
          </div>
        </div>

        <div v-if="currentRoomEntry" class="room-access-panel">
          <div class="player-roster-title">{{ t('ui.control_room_access_title') }}</div>
          <div class="room-access-summary">
            <span>
              {{ t('ui.control_room_access_mode') }}
              {{ currentRoomAccessMode === 'private' ? t('ui.control_room_status_private') : t('ui.control_room_status_open') }}
            </span>
            <span>{{ t('ui.control_room_plan_current', { plan: currentRoomPlanLabel, profile: currentRoomCommercialProfile }) }}</span>
            <span v-if="currentRoomRequestedPlanId !== currentRoomPlanId">
              {{ t('ui.control_room_plan_requested', { plan: currentRoomRequestedPlanLabel }) }}
            </span>
            <span>
              {{ t('ui.control_room_billing_summary', {
                status: billingStatusLabel(currentRoomBillingStatus),
                plan: currentRoomEntitledPlanLabel,
              }) }}
            </span>
            <span
              v-if="currentRoomBillingDeadlineAt"
              :class="{ 'room-billing-warning': currentRoomBillingRenewalRecommended }"
            >
              {{ t('ui.control_room_billing_deadline', {
                date: formatDateTime(currentRoomBillingDeadlineAt),
                days: currentRoomBillingDaysRemaining ?? 0,
              }) }}
            </span>
            <span v-if="currentRoomMemberLimit > 0">{{ t('ui.control_room_capacity', { count: currentRoomMembers.length, limit: currentRoomMemberLimit }) }}</span>
            <span v-if="currentRoomEntry.ownerViewerId">{{ t('ui.control_room_owner', { id: currentRoomEntry.ownerViewerId }) }}</span>
            <span v-if="currentRoomInviteCode">{{ t('ui.control_room_invite_code', { code: currentRoomInviteCode }) }}</span>
            <span v-if="currentRoomPlanLockedByBilling">{{ t('ui.control_room_plan_locked_by_billing') }}</span>
            <button
              v-if="canRotateCurrentRoomInvite"
              type="button"
              class="member-remove-btn"
              :disabled="isRotatingRoomInvite"
              @click="rotateCurrentRoomInvite"
              v-sound
            >
              {{ t('ui.control_room_invite_rotate') }}
            </button>
          </div>

          <div v-if="canManageCurrentRoomPlan" class="seat-chip-row">
            <button
              v-for="plan in roomPlanOptions"
              :key="plan.id"
              type="button"
              class="seat-chip"
              :class="{ active: currentRoomRequestedPlanId === plan.id, locked: !isPlanSelectableByCurrentEntitlement(plan.id) }"
              :disabled="isUpdatingRoomPlan || currentRoomRequestedPlanId === plan.id || !isPlanSelectableByCurrentEntitlement(plan.id)"
              @click="updateCurrentRoomPlan(plan.id)"
              v-sound
            >
              {{ plan.label }}
            </button>
          </div>

          <div v-if="canManageCurrentRoomEntitlement" class="room-access-panel">
            <div class="player-roster-title">{{ t('ui.control_room_billing_title') }}</div>
            <div class="room-access-summary">
              <span>{{ t('ui.control_room_billing_status', { status: billingStatusLabel(currentRoomBillingStatus) }) }}</span>
              <span>{{ t('ui.control_room_entitled_plan', { plan: currentRoomEntitledPlanLabel }) }}</span>
              <span v-if="currentRoomPlanLockedByBilling">{{ t('ui.control_room_plan_locked_hint') }}</span>
            </div>

            <div class="seat-chip-row">
              <button
                v-for="status in billingStatusOptions"
                :key="status.id"
                type="button"
                class="seat-chip"
                :class="{ active: currentRoomBillingStatus === status.id }"
                :disabled="isUpdatingRoomEntitlement || currentRoomBillingStatus === status.id"
                @click="setCurrentRoomBillingStatus(status.id)"
                v-sound
              >
                {{ status.label }}
              </button>
            </div>

            <div class="seat-chip-row">
              <button
                v-for="plan in roomEntitlementPlanOptions"
                :key="plan.id"
                type="button"
                class="seat-chip"
                :class="{ active: currentRoomEntitledPlanId === plan.id }"
                :disabled="isUpdatingRoomEntitlement || currentRoomEntitledPlanId === plan.id"
                @click="setCurrentRoomEntitledPlan(plan.id)"
                v-sound
              >
                {{ plan.label }}
              </button>
            </div>
          </div>

          <div v-if="canManageCurrentRoomEntitlement" class="room-access-panel">
            <div class="player-roster-title">{{ t('ui.control_room_payment_title') }}</div>
            <div class="room-access-summary">
              <span>{{ t('ui.control_room_plan_current', { plan: currentRoomPlanLabel, profile: currentRoomCommercialProfile }) }}</span>
              <span>{{ t('ui.control_room_price', { amount: formatPriceVnd(currentRoomPriceVnd), days: currentRoomBillingCycleDays }) }}</span>
              <span
                v-if="currentRoomBillingRenewalRecommended"
                class="room-billing-warning"
              >
                {{ t('ui.control_room_billing_renewal_recommended') }}
              </span>
            </div>

            <div
              v-if="currentRoomBillingRenewalRecommended && currentRoomRenewalOffer"
              class="room-access-summary"
            >
              <button
                type="button"
                class="seat-create-btn"
                :disabled="isCreatingPaymentOrder"
                @click="createRenewalPaymentOrder"
                v-sound
              >
                {{ t('ui.control_room_payment_renew_now', {
                  plan: roomPlanOptions.find((plan) => plan.id === currentRoomRenewalOffer.plan_id)?.label || currentRoomRenewalOffer.plan_id,
                  amount: formatPriceVnd(currentRoomRenewalOffer.price_vnd),
                }) }}
              </button>
            </div>

            <div class="seat-chip-row">
              <button
                v-for="offer in currentRoomSaleOffers.filter((item) => item.sellable)"
                :key="offer.plan_id"
                type="button"
                class="seat-chip"
                :disabled="isCreatingPaymentOrder"
                @click="createPaymentOrderForPlan(offer.plan_id)"
                v-sound
              >
                {{ t('ui.control_room_payment_order_create', {
                  plan: roomPlanOptions.find((plan) => plan.id === offer.plan_id)?.label || offer.plan_id,
                  amount: formatPriceVnd(offer.price_vnd),
                }) }}
              </button>
            </div>

            <div v-if="currentRoomPendingPaymentOrder" class="room-access-summary">
              <span>{{ t('ui.control_room_payment_pending', {
                orderId: currentRoomPendingPaymentOrder.order_id,
                amount: formatPriceVnd(currentRoomPendingPaymentOrder.amount_vnd),
              }) }}</span>
              <span v-if="currentRoomPendingPaymentOrder.transfer_note">{{ t('ui.control_room_payment_transfer_note', { note: currentRoomPendingPaymentOrder.transfer_note }) }}</span>
              <button
                type="button"
                class="member-remove-btn"
                :disabled="isSettlingPayment"
                @click="settlePendingPaymentOrder"
                v-sound
              >
                {{ t('ui.control_room_payment_settle') }}
              </button>
            </div>

            <div v-else-if="currentRoomLastPaidOrder" class="room-access-summary">
              <span>{{ t('ui.control_room_payment_last_paid', {
                orderId: currentRoomLastPaidOrder.order_id,
                amount: formatPriceVnd(currentRoomLastPaidOrder.settled_amount_vnd || currentRoomLastPaidOrder.amount_vnd),
              }) }}</span>
            </div>

            <div class="seat-create-row">
              <input
                v-model="pendingReconcileTransferNote"
                class="seat-input"
                type="text"
                :placeholder="t('ui.control_room_payment_reconcile_note_placeholder')"
              />
              <input
                v-model="pendingReconcilePaymentRef"
                class="seat-input"
                type="text"
                :placeholder="t('ui.control_room_payment_reconcile_ref_placeholder')"
              />
              <input
                v-model="pendingReconcileAmountVnd"
                class="seat-input"
                type="text"
                :placeholder="t('ui.control_room_payment_reconcile_amount_placeholder')"
                @keydown.enter.prevent="reconcileCurrentRoomPayment"
              />
              <button
                type="button"
                class="seat-create-btn"
                :disabled="!canReconcileCurrentRoomPayment"
                @click="reconcileCurrentRoomPayment"
                v-sound
              >
                {{ t('ui.control_room_payment_reconcile') }}
              </button>
            </div>

            <div class="player-roster">
              <div class="player-roster-title">{{ t('ui.control_room_payment_audit_title') }}</div>
              <div v-if="currentRoomPaymentEvents.length" class="player-roster-list">
                <div
                  v-for="event in currentRoomPaymentEvents"
                  :key="`${event.timestamp}-${event.order_id || ''}-${event.event_type || ''}`"
                  class="player-roster-item"
                >
                  <div class="player-roster-name">
                    {{ formatPaymentEventTitle(event) }}
                  </div>
                  <div class="player-roster-meta">
                    {{ formatPaymentEventMeta(event) }}
                  </div>
                </div>
              </div>
              <div v-else class="seat-unavailable">{{ t('ui.control_room_payment_audit_empty') }}</div>
            </div>
          </div>

          <div v-if="canManageCurrentRoomAccess" class="seat-chip-row">
            <button
              type="button"
              class="seat-chip"
              :class="{ active: currentRoomAccessMode === 'open' }"
              :disabled="isUpdatingRoomAccess || currentRoomAccessMode === 'open'"
              @click="updateCurrentRoomAccess('open')"
              v-sound
            >
              {{ t('ui.control_room_status_open') }}
            </button>
            <button
              type="button"
              class="seat-chip"
              :class="{ active: currentRoomAccessMode === 'private' }"
              :disabled="isUpdatingRoomAccess || currentRoomAccessMode === 'private'"
              @click="updateCurrentRoomAccess('private')"
              v-sound
            >
              {{ t('ui.control_room_status_private') }}
            </button>
          </div>

          <div v-if="canManageCurrentRoomAccess" class="seat-create-row">
            <input
              v-model="pendingRoomMemberId"
              class="seat-input"
              type="text"
              :placeholder="t('ui.control_room_member_placeholder')"
              @keydown.enter.prevent="addCurrentRoomMember"
            />
            <button
              type="button"
              class="seat-create-btn"
              :disabled="!canAddRoomMember"
              @click="addCurrentRoomMember"
              v-sound
            >
              {{ t('ui.control_room_member_add') }}
            </button>
          </div>

          <div class="player-roster-list">
            <div
              v-for="memberViewerId in currentRoomMembers"
              :key="memberViewerId"
              class="player-roster-item"
            >
              <div class="player-roster-name">{{ memberViewerId }}</div>
              <div class="player-roster-meta">
                <template v-if="currentRoomEntry.ownerViewerId === memberViewerId">
                  {{ t('ui.control_room_member_owner') }}
                </template>
                <button
                  v-else-if="canManageCurrentRoomAccess"
                  type="button"
                  class="member-remove-btn"
                  :disabled="isUpdatingRoomMembers"
                  @click="removeCurrentRoomMember(memberViewerId)"
                  v-sound
                >
                  {{ t('ui.control_room_member_remove') }}
                </button>
                <template v-else>
                  {{ t('ui.control_room_member_allowed') }}
                </template>
              </div>
            </div>
          </div>
        </div>

        <div v-if="roomError || roomMembershipError" class="seat-error">{{ roomError || roomMembershipError }}</div>
      </div>

      <div v-else class="seat-unavailable">{{ t('ui.control_rooms_unavailable') }}</div>
    </div>

    <div class="seat-panel">
      <div class="seat-panel-header">
        <div class="seat-panel-title-wrap">
          <div class="btn-icon seat-icon" :style="{ '--icon-url': `url(${usersIcon})` }" aria-hidden="true"></div>
          <div>
            <div class="seat-panel-title">{{ t('ui.control_seats_title') }}</div>
            <div class="seat-panel-desc">
              {{ t('ui.control_seats_desc') }}
              {{ t('ui.control_seats_viewer', { id: viewerId }) }}
            </div>
          </div>
        </div>
        <div class="seat-current">{{ t('ui.control_seats_current', { id: activeControllerId }) }}</div>
      </div>

      <div v-if="canManageSeats" class="seat-panel-body">
        <div class="seat-chip-row">
          <button
            v-for="seat in seatEntries"
            :key="seat.id"
            type="button"
            class="seat-chip"
            :class="{ active: seat.id === activeControllerId, locked: seat.isLockedByOther }"
            :disabled="isSwitchingSeat || seat.id === activeControllerId || seat.isLockedByOther"
            @click="switchSeat(seat.id)"
            v-sound
          >
            {{ seatLabel(seat) }}
          </button>
        </div>

        <div class="seat-create-row">
          <input
            v-model="pendingSeatId"
            class="seat-input"
            type="text"
            :placeholder="t('ui.control_seats_placeholder')"
            @keydown.enter.prevent="createOrSwitchSeat"
          />
          <button
            type="button"
            class="seat-create-btn"
            :disabled="!canCreateSeat"
            @click="createOrSwitchSeat"
            v-sound
          >
            <span class="btn-icon seat-create-icon" :style="{ '--icon-url': `url(${plusIcon})` }" aria-hidden="true"></span>
            {{ t('ui.control_seats_create') }}
          </button>
        </div>

        <div class="seat-actions-row">
          <button
            type="button"
            class="seat-release-btn"
            :disabled="!canReleaseActiveSeat"
            @click="releaseActiveSeat"
            v-sound
          >
            {{ t('ui.control_seats_release') }}
          </button>
        </div>

        <div v-if="seatError" class="seat-error">{{ seatError }}</div>
      </div>

      <div v-else class="seat-unavailable">{{ t('ui.control_seats_unavailable') }}</div>
    </div>

    <div class="other-actions">
      <button class="custom-action-btn" @click="emit('return-to-main')" v-sound>
        <div class="btn-content">
          <div class="btn-icon" :style="{ '--icon-url': `url(${houseIcon})` }" aria-hidden="true"></div>
          <div class="btn-text-group">
            <span class="btn-title">{{ t('ui.return_to_main') }}</span>
            <span class="btn-desc">{{ t('ui.return_to_main_desc') }}</span>
          </div>
        </div>
        <div class="btn-arrow" :style="{ '--icon-url': `url(${chevronRightIcon})` }" aria-hidden="true"></div>
      </button>

      <button class="custom-action-btn danger-hover" @click="emit('exit-game')" v-sound>
        <div class="btn-content">
          <div class="btn-icon" :style="{ '--icon-url': `url(${logOutIcon})` }" aria-hidden="true"></div>
          <div class="btn-text-group">
            <span class="btn-title">{{ t('ui.quit_game') }}</span>
            <span class="btn-desc">{{ t('ui.quit_game_desc') }}</span>
          </div>
        </div>
        <div class="btn-arrow" :style="{ '--icon-url': `url(${chevronRightIcon})` }" aria-hidden="true"></div>
      </button>
    </div>
  </div>
</template>

<style scoped>
.other-panel-container {
  max-width: 600px;
  margin: 0 auto;
  padding-top: 2em;
}

.panel-header {
  margin-bottom: 3em;
  text-align: center;
}

.panel-header h3 {
  margin: 0 0 0.5em 0;
  font-size: 1.5em;
  color: #eee;
}

.description {
  color: #888;
  font-size: 0.9em;
  margin: 0;
}

.seat-panel {
  margin: 0 auto 2em;
  width: min(680px, calc(100% - 40px));
  padding: 18px 20px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.03)),
    rgba(255, 255, 255, 0.03);
}

.seat-panel-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.seat-panel-title-wrap {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.seat-panel-title {
  font-size: 15px;
  font-weight: 600;
  color: #f0f0f0;
}

.seat-panel-desc {
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.5;
  color: #9aa5b1;
}

.seat-current {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(23, 125, 220, 0.14);
  border: 1px solid rgba(23, 125, 220, 0.22);
  color: #d8ecff;
  font-size: 12px;
  white-space: nowrap;
}

.seat-panel-body {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.seat-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.seat-chip {
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.05);
  color: #ddd;
  border-radius: 999px;
  padding: 7px 12px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.seat-chip:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}

.seat-chip.active {
  color: #d8ecff;
  background: rgba(23, 125, 220, 0.16);
  border-color: rgba(23, 125, 220, 0.34);
}

.seat-chip.locked {
  color: #c9b6b6;
  border-color: rgba(214, 124, 124, 0.22);
  background: rgba(214, 124, 124, 0.08);
}

.seat-chip:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.seat-create-row {
  display: flex;
  gap: 10px;
}

.seat-create-row--stack {
  flex-direction: column;
}

.player-roster {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.room-access-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.room-access-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 12px;
  color: #9aa5b1;
}

.room-billing-warning {
  color: #ffd18b;
}

.player-roster-title {
  font-size: 12px;
  color: #9aa5b1;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.player-roster-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.player-roster-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.player-roster-item.active {
  border-color: rgba(23, 125, 220, 0.26);
  background: rgba(23, 125, 220, 0.1);
}

.player-roster-name {
  font-size: 13px;
  color: #f0f0f0;
}

.player-roster-meta {
  font-size: 12px;
  color: #9aa5b1;
  text-align: right;
}

.member-remove-btn {
  border: 1px solid rgba(214, 124, 124, 0.22);
  background: rgba(214, 124, 124, 0.08);
  color: #f2d6d6;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 11px;
  cursor: pointer;
}

.member-remove-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.seat-input {
  flex: 1;
  min-width: 0;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  color: #e6e6e6;
  padding: 10px 12px;
  font-size: 13px;
}

.seat-input:focus {
  outline: none;
  border-color: rgba(23, 125, 220, 0.34);
  box-shadow: 0 0 0 1px rgba(23, 125, 220, 0.16);
}

.seat-create-btn {
  border: 1px solid rgba(23, 125, 220, 0.28);
  background: rgba(23, 125, 220, 0.14);
  color: #d8ecff;
  border-radius: 8px;
  padding: 0 14px;
  min-height: 40px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
}

.seat-create-btn:hover {
  background: rgba(23, 125, 220, 0.2);
}

.seat-create-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.seat-create-btn--secondary {
  align-self: flex-start;
  border-color: rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.04);
  color: #ddd;
}

.seat-create-btn--secondary:hover {
  background: rgba(255, 255, 255, 0.08);
}

.seat-actions-row {
  display: flex;
  justify-content: flex-end;
}

.seat-release-btn {
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.04);
  color: #ddd;
  border-radius: 8px;
  padding: 8px 12px;
  min-height: 36px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.seat-release-btn:hover {
  background: rgba(255, 255, 255, 0.08);
}

.seat-release-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.seat-error,
.seat-unavailable {
  font-size: 12px;
  color: #d2b48c;
}

.seat-icon {
  color: #d8ecff;
}

.seat-create-icon {
  width: 14px;
  height: 14px;
}

.other-actions {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
  padding: 0 40px;
}

.custom-action-btn {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 20px 24px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  color: #eee;
  text-align: left;
}

.custom-action-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.3);
}

.danger-hover:hover {
  border-color: rgba(255, 80, 80, 0.4);
  background: linear-gradient(90deg, rgba(255, 80, 80, 0.05), rgba(255, 255, 255, 0.05));
}

.btn-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.btn-icon {
  width: 24px;
  height: 24px;
  opacity: 0.8;
  flex-shrink: 0;
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

.btn-text-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.btn-title {
  font-size: 18px;
  font-weight: 500;
  letter-spacing: 1px;
}

.btn-desc {
  font-size: 12px;
  color: #888;
}

.btn-arrow {
  width: 18px;
  height: 18px;
  opacity: 0.3;
  flex-shrink: 0;
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
