import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { systemApi } from '../api';
import type { InitStatusDTO } from '../types/api';
import { logError } from '../utils/appError';
import { loadOrCreateViewerId } from '../utils/viewerIdentity';
import { useWorldStore } from './world';

export const useSystemStore = defineStore('system', () => {
  // --- State ---
  const initStatus = ref<InitStatusDTO | null>(null);
  const isInitialized = ref(false); // 前端是否完成初始化 (world store loaded, socket connected)
  const isManualPaused = ref(true); // 用户手动暂停
  const isGameRunning = ref(false); // 游戏是否处于 Running 阶段 (Init Status ready)
  const viewerId = ref(loadOrCreateViewerId());

  // 请求计数器，用于处理竞态条件。
  let fetchStatusRequestId = 0;
  
  // --- Getters ---
  const isLoading = computed(() => {
    if (!initStatus.value) return true;
    if (initStatus.value.status === 'idle') return false;
    if (initStatus.value.status === 'ready' && isInitialized.value) return false;
    return true;
  });

  const isReady = computed(() => {
    return initStatus.value?.status === 'ready' && isInitialized.value;
  });

  const activeControllerId = computed(() => initStatus.value?.active_controller_id || 'local');
  const playerControlSeatIds = computed(() => initStatus.value?.player_control_seat_ids || ['local']);
  const playerControlSeats = computed(() => initStatus.value?.player_control_seats || []);
  const playerProfiles = computed(() => initStatus.value?.player_profiles || []);
  const viewerProfile = computed(() => initStatus.value?.viewer_profile || null);
  const activeRoomId = computed(() => initStatus.value?.active_room_id || 'main');
  const roomIds = computed(() => initStatus.value?.room_ids || ['main']);
  const activeRoomSummary = computed(() => initStatus.value?.active_room_summary || null);
  const roomSummaries = computed(() => initStatus.value?.room_summaries || []);

  // --- Actions ---
  
  async function fetchInitStatus() {
    const currentRequestId = ++fetchStatusRequestId;
    try {
      const res = await systemApi.fetchInitStatus(viewerId.value);
      
      // 只接受最新请求的响应。
      if (currentRequestId !== fetchStatusRequestId) {
        return null;
      }
      
      initStatus.value = res;
      
      if (res.status === 'ready') {
        isGameRunning.value = true;
      } else {
        isGameRunning.value = false;
      }
      return res;
    } catch (e) {
      if (currentRequestId === fetchStatusRequestId) {
        logError('SystemStore fetch init status', e);
      }
      return null;
    }
  }

  async function switchControlSeat(controllerId: string) {
    try {
      await systemApi.switchControlSeat({ controller_id: controllerId, viewer_id: viewerId.value });
      return await fetchInitStatus();
    } catch (e) {
      logError('SystemStore switch control seat', e);
      return null;
    }
  }

  async function releaseControlSeat(controllerId: string) {
    try {
      await systemApi.releaseControlSeat({ controller_id: controllerId, viewer_id: viewerId.value });
      return await fetchInitStatus();
    } catch (e) {
      logError('SystemStore release control seat', e);
      return null;
    }
  }

  async function switchWorldRoom(roomId: string) {
    const worldStore = useWorldStore();
    try {
      await systemApi.switchWorldRoom({ room_id: roomId, viewer_id: viewerId.value });
      const status = await fetchInitStatus();

      worldStore.reset();
      if (status?.status === 'ready') {
        await worldStore.initialize();
        isInitialized.value = true;
      } else {
        isInitialized.value = false;
      }

      return status;
    } catch (e) {
      logError('SystemStore switch world room', e);
      return null;
    }
  }

  async function joinWorldRoomByInvite(roomId: string, inviteCode: string) {
    const worldStore = useWorldStore();
    try {
      await systemApi.joinWorldRoomByInvite({
        room_id: roomId,
        invite_code: inviteCode,
        viewer_id: viewerId.value,
      });
      const status = await fetchInitStatus();

      worldStore.reset();
      if (status?.status === 'ready') {
        await worldStore.initialize();
        isInitialized.value = true;
      } else {
        isInitialized.value = false;
      }

      return status;
    } catch (e) {
      logError('SystemStore join world room by invite', e);
      return null;
    }
  }

  async function updatePlayerProfile(displayName: string) {
    try {
      await systemApi.updatePlayerProfile({ display_name: displayName, viewer_id: viewerId.value });
      return await fetchInitStatus();
    } catch (e) {
      logError('SystemStore update player profile', e);
      return null;
    }
  }

  async function updateWorldRoomAccess(roomId: string, accessMode: 'open' | 'private') {
    try {
      await systemApi.updateWorldRoomAccess({
        room_id: roomId,
        access_mode: accessMode,
        viewer_id: viewerId.value,
      });
      return await fetchInitStatus();
    } catch (e) {
      logError('SystemStore update world room access', e);
      return null;
    }
  }

  async function updateWorldRoomPlan(roomId: string, planId: string) {
    try {
      await systemApi.updateWorldRoomPlan({
        room_id: roomId,
        plan_id: planId,
        viewer_id: viewerId.value,
      });
      return await fetchInitStatus();
    } catch (e) {
      logError('SystemStore update world room plan', e);
      return null;
    }
  }

  async function updateWorldRoomEntitlement(
    roomId: string,
    billingStatus: 'trial' | 'active' | 'grace' | 'expired',
    entitledPlanId: string,
  ) {
    try {
      await systemApi.updateWorldRoomEntitlement({
        room_id: roomId,
        billing_status: billingStatus,
        entitled_plan_id: entitledPlanId,
        viewer_id: viewerId.value,
      });
      return await fetchInitStatus();
    } catch (e) {
      logError('SystemStore update world room entitlement', e);
      return null;
    }
  }

  async function createWorldRoomPaymentOrder(roomId: string, targetPlanId: string) {
    try {
      await systemApi.createWorldRoomPaymentOrder({
        room_id: roomId,
        target_plan_id: targetPlanId,
        viewer_id: viewerId.value,
      });
      return await fetchInitStatus();
    } catch (e) {
      logError('SystemStore create world room payment order', e);
      return null;
    }
  }

  async function settleWorldRoomPayment(
    roomId: string,
    orderId: string,
    paymentRef?: string,
    amountVnd?: number,
  ) {
    try {
      await systemApi.settleWorldRoomPayment({
        room_id: roomId,
        order_id: orderId,
        payment_ref: paymentRef,
        amount_vnd: amountVnd,
        viewer_id: viewerId.value,
      });
      return await fetchInitStatus();
    } catch (e) {
      logError('SystemStore settle world room payment', e);
      return null;
    }
  }

  async function reconcileWorldRoomPayment(
    transferNote: string,
    paymentRef?: string,
    amountVnd?: number,
  ) {
    try {
      await systemApi.reconcileWorldRoomPayment({
        transfer_note: transferNote,
        payment_ref: paymentRef,
        amount_vnd: amountVnd,
        viewer_id: viewerId.value,
      });
      return await fetchInitStatus();
    } catch (e) {
      logError('SystemStore reconcile world room payment', e);
      return null;
    }
  }

  async function addWorldRoomMember(roomId: string, memberViewerId: string) {
    try {
      await systemApi.addWorldRoomMember({
        room_id: roomId,
        member_viewer_id: memberViewerId,
        viewer_id: viewerId.value,
      });
      return await fetchInitStatus();
    } catch (e) {
      logError('SystemStore add world room member', e);
      return null;
    }
  }

  async function removeWorldRoomMember(roomId: string, memberViewerId: string) {
    try {
      await systemApi.removeWorldRoomMember({
        room_id: roomId,
        member_viewer_id: memberViewerId,
        viewer_id: viewerId.value,
      });
      return await fetchInitStatus();
    } catch (e) {
      logError('SystemStore remove world room member', e);
      return null;
    }
  }

  async function rotateWorldRoomInvite(roomId: string) {
    try {
      await systemApi.rotateWorldRoomInvite({
        room_id: roomId,
        viewer_id: viewerId.value,
      });
      return await fetchInitStatus();
    } catch (e) {
      logError('SystemStore rotate world room invite', e);
      return null;
    }
  }

  function setInitialized(val: boolean) {
    isInitialized.value = val;
  }

  // 切换手动暂停状态（用户点击暂停按钮时调用）
  async function togglePause() {
    const newState = !isManualPaused.value;
    isManualPaused.value = newState;
    try {
      if (newState) {
        await systemApi.pauseGame();
      } else {
        await systemApi.resumeGame();
      }
    } catch (e) {
      // API 失败时回滚状态
      isManualPaused.value = !newState;
      logError('SystemStore toggle pause', e);
    }
  }

  // 仅调用后端 API，不修改 isManualPaused（用于菜单打开/关闭等系统行为）
  async function pause() {
    try {
      await systemApi.pauseGame();
    } catch (e) {
      logError('SystemStore pause', e);
    }
  }

  async function resume() {
    try {
      await systemApi.resumeGame();
    } catch (e) {
      logError('SystemStore resume', e);
    }
  }

  return {
    initStatus,
    isInitialized,
    isManualPaused,
    isGameRunning,
    viewerId,
    isLoading,
    isReady,
    activeRoomId,
    roomIds,
    activeControllerId,
    playerControlSeatIds,
    playerControlSeats,
    playerProfiles,
    viewerProfile,
    activeRoomSummary,
    roomSummaries,
    
    fetchInitStatus,
    switchControlSeat,
    releaseControlSeat,
    updatePlayerProfile,
    switchWorldRoom,
    joinWorldRoomByInvite,
    updateWorldRoomAccess,
    updateWorldRoomPlan,
    updateWorldRoomEntitlement,
    createWorldRoomPaymentOrder,
    settleWorldRoomPayment,
    reconcileWorldRoomPayment,
    addWorldRoomMember,
    removeWorldRoomMember,
    rotateWorldRoomInvite,
    setInitialized,
    togglePause,
    pause,
    resume
  };
});
