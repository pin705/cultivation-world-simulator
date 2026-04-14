/**
 * Recap API 模块
 * 
 * Recap-first gameplay loop - 玩家每次回归先看发生了什么
 */
import { httpClient } from '../http';
import type {
  RecapResponse,
  AcknowledgeRecapResponse,
  ActionPointResponse
} from '@/types/recap';

/**
 * 获取玩家的 recap（期间发生的重要事件）
 */
export async function getRecap(viewerId: string): Promise<RecapResponse> {
  return httpClient.get<RecapResponse>(
    `/api/v1/query/recap?viewer_id=${encodeURIComponent(viewerId)}`
  );
}

/**
 * 确认已读 recap，刷新 action points
 */
export async function acknowledgeRecap(viewerId: string): Promise<AcknowledgeRecapResponse> {
  return httpClient.post<AcknowledgeRecapResponse>(
    '/api/v1/command/recap/acknowledge',
    { viewer_id: viewerId }
  );
}

/**
 * 花费一个 action point
 */
export async function spendActionPoint(viewerId: string): Promise<ActionPointResponse> {
  return httpClient.post<ActionPointResponse>(
    '/api/v1/command/recap/spend-action-point',
    { viewer_id: viewerId }
  );
}

