import { httpClient } from '../http';
import type { AuthSessionBootstrapDTO, AuthSessionStateDTO } from '../../types/api';

export interface BootstrapGuestSessionParams {
  preferred_viewer_id?: string;
  display_name?: string;
}

export interface RegisterPasswordSessionParams {
  email: string;
  password: string;
  display_name?: string;
  preferred_viewer_id?: string;
}

export interface LoginPasswordSessionParams {
  email: string;
  password: string;
}

export const authApi = {
  bootstrapGuestSession(params: BootstrapGuestSessionParams = {}) {
    return httpClient.post<AuthSessionBootstrapDTO>('/api/v1/auth/guest/bootstrap', params);
  },

  registerPasswordSession(params: RegisterPasswordSessionParams) {
    return httpClient.post<AuthSessionBootstrapDTO>('/api/v1/auth/register', params);
  },

  loginPasswordSession(params: LoginPasswordSessionParams) {
    return httpClient.post<AuthSessionBootstrapDTO>('/api/v1/auth/login', params);
  },

  fetchSession() {
    return httpClient.get<AuthSessionStateDTO>('/api/v1/auth/session/me');
  },

  logout() {
    return httpClient.post<AuthSessionStateDTO>('/api/v1/auth/session/logout', {});
  },
};
