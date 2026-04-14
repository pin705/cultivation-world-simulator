import { httpClient } from '../http';
import type { AuthSessionBootstrapDTO, AuthSessionStateDTO } from '../../types/api';

export interface BootstrapGuestSessionParams {
  preferred_viewer_id?: string;
  display_name?: string;
}

export const authApi = {
  bootstrapGuestSession(params: BootstrapGuestSessionParams = {}) {
    return httpClient.post<AuthSessionBootstrapDTO>('/api/v1/auth/guest/bootstrap', params);
  },

  fetchSession() {
    return httpClient.get<AuthSessionStateDTO>('/api/v1/auth/session/me');
  },

  logout() {
    return httpClient.post<AuthSessionStateDTO>('/api/v1/auth/session/logout', {});
  },
};
