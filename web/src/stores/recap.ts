/**
 * Recap Store
 * 
 * 管理 recap 状态和 action points
 * Shuimo-inspired: 简洁、优雅、信息密度适中
 */
import { defineStore } from 'pinia';
import { getRecap, acknowledgeRecap } from '@/api/modules/recap';
import type { RecapResponse } from '@/types/recap';

interface RecapState {
  /** 当前 recap 数据 */
  recap: RecapResponse | null;
  /** 是否正在加载 */
  loading: boolean;
  /** 是否显示 recap overlay */
  showOverlay: boolean;
  /** 上次错误 */
  error: string | null;
}

export const useRecapStore = defineStore('recap', {
  state: (): RecapState => ({
    recap: null,
    loading: false,
    showOverlay: false,
    error: null,
  }),

  getters: {
    /** 是否有未读 recap */
    hasUnreadRecap: (state) => state.recap?.has_unread_recap ?? false,
    
    /** Action points 剩余 */
    actionPointsRemaining: (state) => state.recap?.action_points.remaining ?? 0,
    
    /** Action points 总计 */
    actionPointsTotal: (state) => state.recap?.action_points.total ?? 0,
    
    /** 是否有可用的 action points */
    hasActionPoints: (state) => (state.recap?.action_points.remaining ?? 0) > 0,
  },

  actions: {
    /**
     * 加载 recap
     */
    async loadRecap(viewerId: string) {
      this.loading = true;
      this.error = null;
      
      try {
        this.recap = await getRecap(viewerId);
        
        // 如果有未读 recap，显示 overlay
        if (this.recap.has_unread_recap) {
          this.showOverlay = true;
        }
      } catch (err) {
        this.error = err instanceof Error ? err.message : 'Failed to load recap';
        console.error('[RecapStore] Failed to load recap:', err);
      } finally {
        this.loading = false;
      }
    },

    /**
     * 确认已读 recap
     */
    async acknowledge(viewerId: string) {
      this.loading = true;
      this.error = null;
      
      try {
        const result = await acknowledgeRecap(viewerId);
        
        // 更新本地状态
        if (this.recap) {
          this.recap.last_recap_month_stamp = result.last_recap_month_stamp;
          this.recap.last_acknowledge_month_stamp = result.last_acknowledge_month_stamp;
          this.recap.action_points = result.action_points;
          this.recap.has_unread_recap = false;
        }
        
        // 关闭 overlay
        this.showOverlay = false;
      } catch (err) {
        this.error = err instanceof Error ? err.message : 'Failed to acknowledge recap';
        console.error('[RecapStore] Failed to acknowledge recap:', err);
        throw err;
      } finally {
        this.loading = false;
      }
    },

    /**
     * 手动关闭 overlay
     */
    closeOverlay() {
      this.showOverlay = false;
    },

    /**
     * 手动打开 overlay
     */
    openOverlay() {
      this.showOverlay = true;
    },
  },
});
