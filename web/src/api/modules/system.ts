import { httpClient } from '../http';
import type { 
  SaveFileDTO,
  InitStatusDTO,
  RunConfigDTO,
  AppSettingsDTO,
  AppSettingsPatchDTO,
  SwitchControlSeatParams,
  ReleaseControlSeatParams,
  UpdatePlayerProfileParams,
  TransferPlayerIdentityParams,
  SwitchWorldRoomParams,
  UpdateWorldRoomAccessParams,
  UpdateWorldRoomPlanParams,
  UpdateWorldRoomEntitlementParams,
  CreateWorldRoomPaymentOrderParams,
  SettleWorldRoomPaymentParams,
  ReconcileWorldRoomPaymentParams,
  UpdateWorldRoomMemberParams,
  RotateWorldRoomInviteParams,
  JoinWorldRoomByInviteParams,
} from '../../types/api';
import { getViewerIdentityPayload, loadOrCreateViewerId } from '../../utils/viewerIdentity';

export const systemApi = {
  pauseGame() {
    return httpClient.post('/api/v1/command/game/pause', {});
  },

  resumeGame() {
    return httpClient.post('/api/v1/command/game/resume', {});
  },

  fetchSaves() {
    return httpClient.get<{ saves: SaveFileDTO[] }>('/api/v1/query/saves')
      .then((data) => data.saves ?? []);
  },

  saveGame(customName?: string) {
    return httpClient.post<{ status: string; filename: string }>(
      '/api/v1/command/game/save',
      { custom_name: customName }
    );
  },

  deleteSave(filename: string) {
    return httpClient.post<{ status: string; message: string }>('/api/v1/command/game/delete-save', { filename });
  },

  loadGame(filename: string) {
    return httpClient.post<{ status: string; message: string }>('/api/v1/command/game/load', { filename });
  },

  fetchInitStatus(viewerId: string = loadOrCreateViewerId()) {
    const query = viewerId.trim()
      ? `?viewer_id=${encodeURIComponent(viewerId.trim())}`
      : '';
    return httpClient.get<InitStatusDTO>(`/api/v1/query/runtime/status${query}`);
  },

  switchControlSeat(params: SwitchControlSeatParams) {
    return httpClient.post<{ status: string; message: string; active_controller_id: string; seat_ids: string[]; holder_id?: string | null }>(
      '/api/v1/command/player/switch-seat',
      params,
    );
  },

  releaseControlSeat(params: ReleaseControlSeatParams) {
    return httpClient.post<{ status: string; message: string; controller_id: string }>(
      '/api/v1/command/player/release-seat',
      params,
    );
  },

  updatePlayerProfile(params: UpdatePlayerProfileParams) {
    return httpClient.post<{ status: string; message: string; profile: InitStatusDTO['viewer_profile'] }>(
      '/api/v1/command/player/update-profile',
      getViewerIdentityPayload(params),
    );
  },

  transferPlayerIdentity(params: TransferPlayerIdentityParams) {
    return httpClient.post<{ status: string; message: string; transferred_room_ids: string[]; conflicted_room_ids: string[]; skipped_room_ids: string[] }>(
      '/api/v1/command/player/transfer-identity',
      getViewerIdentityPayload(params),
    );
  },

  switchWorldRoom(params: SwitchWorldRoomParams) {
    return httpClient.post<{ status: string; message: string; active_room_id: string; room_ids: string[]; room_status: string }>(
      '/api/v1/command/world-room/switch',
      getViewerIdentityPayload(params),
    );
  },

  updateWorldRoomAccess(params: UpdateWorldRoomAccessParams) {
    return httpClient.post<{ status: string; message: string }>(
      '/api/v1/command/world-room/update-access',
      getViewerIdentityPayload(params),
    );
  },

  updateWorldRoomPlan(params: UpdateWorldRoomPlanParams) {
    return httpClient.post<{ status: string; message: string }>(
      '/api/v1/command/world-room/update-plan',
      getViewerIdentityPayload(params),
    );
  },

  updateWorldRoomEntitlement(params: UpdateWorldRoomEntitlementParams) {
    return httpClient.post<{ status: string; message: string }>(
      '/api/v1/command/world-room/update-entitlement',
      getViewerIdentityPayload(params),
    );
  },

  createWorldRoomPaymentOrder(params: CreateWorldRoomPaymentOrderParams) {
    return httpClient.post<{ status: string; message: string }>(
      '/api/v1/command/world-room/create-payment-order',
      getViewerIdentityPayload(params),
    );
  },

  settleWorldRoomPayment(params: SettleWorldRoomPaymentParams) {
    return httpClient.post<{ status: string; message: string }>(
      '/api/v1/command/world-room/settle-payment',
      getViewerIdentityPayload(params),
    );
  },

  reconcileWorldRoomPayment(params: ReconcileWorldRoomPaymentParams) {
    return httpClient.post<{ status: string; message: string }>(
      '/api/v1/command/world-room/reconcile-payment',
      getViewerIdentityPayload(params),
    );
  },

  addWorldRoomMember(params: UpdateWorldRoomMemberParams) {
    return httpClient.post<{ status: string; message: string }>(
      '/api/v1/command/world-room/add-member',
      getViewerIdentityPayload(params),
    );
  },

  removeWorldRoomMember(params: UpdateWorldRoomMemberParams) {
    return httpClient.post<{ status: string; message: string }>(
      '/api/v1/command/world-room/remove-member',
      getViewerIdentityPayload(params),
    );
  },

  rotateWorldRoomInvite(params: RotateWorldRoomInviteParams) {
    return httpClient.post<{ status: string; message: string }>(
      '/api/v1/command/world-room/rotate-invite',
      getViewerIdentityPayload(params),
    );
  },

  joinWorldRoomByInvite(params: JoinWorldRoomByInviteParams) {
    return httpClient.post<{ status: string; message: string; active_room_id: string; room_ids: string[]; room_status: string }>(
      '/api/v1/command/world-room/join-by-invite',
      getViewerIdentityPayload(params),
    );
  },

  startNewGame() {
    return this.reinitGame();
  },

  reinitGame() {
    return httpClient.post<{ status: string; message: string }>('/api/v1/command/game/reinit', {});
  },

  fetchSettings() {
    return httpClient.get<AppSettingsDTO>('/api/settings');
  },

  patchSettings(patch: AppSettingsPatchDTO) {
    return httpClient.patch<AppSettingsDTO>('/api/settings', patch);
  },

  resetSettings() {
    return httpClient.post<AppSettingsDTO>('/api/settings/reset', {});
  },

  startGame(config: RunConfigDTO) {
    return httpClient.post<{ status: string; message: string }>('/api/v1/command/game/start', config);
  },

  fetchCurrentRun() {
    return httpClient.get<RunConfigDTO>('/api/v1/query/system/current-run');
  },

  shutdown() {
    return httpClient.post<{ status: string; message: string }>('/api/v1/command/system/shutdown', {});
  },

  resetGame() {
    return httpClient.post<{ status: string; message: string }>('/api/v1/command/game/reset', {});
  }
};
