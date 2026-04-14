import { httpClient } from '../http';
import type { 
  DetailResponseDTO,
  SimpleAvatarDTO,
  CreateAvatarParams,
  GameDataDTO,
  AvatarAdjustCatalogDTO,
  AvatarAdjustOptionDTO,
  UpdateAvatarAdjustmentParams,
  UpdateAvatarPortraitParams,
  GenerateCustomContentParams,
  CustomContentDraftDTO,
  CreateCustomContentParams,
  GrantAvatarSupportParams,
  AppointAvatarSeedParams,
  SetMainAvatarParams,
} from '../../types/api';
import { getViewerIdentityPayload, loadOrCreateViewerId } from '../../utils/viewerIdentity';

export interface HoverParams {
  type: string;
  id: string;
}

export const avatarApi = {
  fetchAvatarMeta() {
    return httpClient.get<{ males: number[]; females: number[] }>('/api/v1/query/meta/avatars');
  },

  fetchDetailInfo(params: HoverParams) {
    const query = new URLSearchParams();
    query.set('type', params.type);
    query.set('id', params.id);
    query.set('viewer_id', loadOrCreateViewerId());
    return httpClient.get<DetailResponseDTO>(`/api/v1/query/detail?${query}`);
  },

  setLongTermObjective(avatarId: string, content: string) {
    return httpClient.post('/api/v1/command/avatar/set-long-term-objective', getViewerIdentityPayload({
      avatar_id: avatarId,
      content
    }));
  },

  clearLongTermObjective(avatarId: string) {
    return httpClient.post('/api/v1/command/avatar/clear-long-term-objective', getViewerIdentityPayload({
      avatar_id: avatarId
    }));
  },

  grantSupport(params: GrantAvatarSupportParams) {
    return httpClient.post('/api/v1/command/avatar/grant-support', getViewerIdentityPayload(params));
  },

  appointSeed(params: AppointAvatarSeedParams) {
    return httpClient.post('/api/v1/command/avatar/appoint-seed', getViewerIdentityPayload(params));
  },

  setMainAvatar(params: SetMainAvatarParams) {
    return httpClient.post('/api/v1/command/player/set-main-avatar', getViewerIdentityPayload(params));
  },

  fetchGameData() {
    return httpClient.get<GameDataDTO>('/api/v1/query/meta/game-data');
  },

  fetchAvatarList() {
    return httpClient.get<{ avatars: SimpleAvatarDTO[] }>('/api/v1/query/meta/avatar-list')
      .then((data) => data.avatars ?? []);
  },

  fetchAvatarAdjustOptions() {
    return httpClient.get<AvatarAdjustCatalogDTO>('/api/v1/query/meta/avatar-adjust-options');
  },

  createAvatar(params: CreateAvatarParams) {
    return httpClient.post<{ status: string; message: string; avatar_id: string }>('/api/v1/command/avatar/create', params);
  },

  updateAvatarAdjustment(params: UpdateAvatarAdjustmentParams) {
    return httpClient.post<{ status: string; message: string }>('/api/v1/command/avatar/update-adjustment', params);
  },

  updateAvatarPortrait(params: UpdateAvatarPortraitParams) {
    return httpClient.post<{ status: string; message: string }>('/api/v1/command/avatar/update-portrait', params);
  },

  generateCustomContent(params: GenerateCustomContentParams) {
    return httpClient.post<{ status: string; draft: CustomContentDraftDTO }>('/api/v1/command/avatar/generate-custom-content', params);
  },

  createCustomContent(params: CreateCustomContentParams) {
    return httpClient.post<{ status: string; item: AvatarAdjustOptionDTO }>('/api/v1/command/avatar/create-custom-content', params);
  },

  deleteAvatar(avatarId: string) {
    return httpClient.post<{ status: string; message: string }>('/api/v1/command/avatar/delete', { avatar_id: avatarId });
  }
};
