<template>
  <!-- Action Points Indicator - 水墨风格 -->
  <div v-if="recapStore.recap && recapStore.recap.action_points.total > 0" class="action-points-indicator">
    <div class="ap-header">
      <span class="ap-icon">💫</span>
      <span class="ap-label">{{ t('recap.fatePoints', '天命') }}</span>
    </div>
    
    <div class="ap-display">
      <div class="ap-circle" :class="{ empty: !recapStore.hasActionPoints }">
        <span class="ap-number">{{ recapStore.actionPointsRemaining }}</span>
      </div>
      <div class="ap-divider"></div>
      <div class="ap-total">
        <span class="ap-total-label">{{ t('recap.total', '总计') }}</span>
        <span class="ap-total-number">{{ recapStore.actionPointsTotal }}</span>
      </div>
    </div>
    
    <!-- Tooltip with details -->
    <div class="ap-tooltip">
      {{ t('recap.apTooltip', '点击 recap 按钮查看期间事件') }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { useRecapStore } from '@/stores/recap';

const { t } = useI18n();
const recapStore = useRecapStore();
</script>

<style scoped>
/* Shuimo-inspired: 简洁优雅 */

.action-points-indicator {
  position: relative;
  padding: 12px;
  background: linear-gradient(135deg, rgba(139, 119, 90, 0.15), rgba(139, 119, 90, 0.08));
  border: 1px solid rgba(139, 119, 90, 0.25);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 180px;
}

.action-points-indicator:hover {
  background: linear-gradient(135deg, rgba(139, 119, 90, 0.2), rgba(139, 119, 90, 0.12));
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.ap-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
}

.ap-icon {
  font-size: 16px;
  filter: grayscale(0.2);
}

.ap-label {
  font-size: 12px;
  color: #6b5d4f;
  font-weight: 600;
  letter-spacing: 1px;
}

.ap-display {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ap-circle {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b775a, #6b5d4f);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(139, 119, 90, 0.3);
}

.ap-circle.empty {
  background: linear-gradient(135deg, rgba(139, 119, 90, 0.3), rgba(139, 119, 90, 0.2));
  box-shadow: none;
}

.ap-number {
  font-size: 20px;
  font-weight: 700;
  color: #f7f3e8;
  font-family: "STKaiti", "KaiTi", sans-serif;
}

.ap-circle.empty .ap-number {
  color: rgba(247, 243, 232, 0.5);
}

.ap-divider {
  width: 1px;
  height: 32px;
  background: rgba(139, 119, 90, 0.3);
}

.ap-total {
  flex: 1;
}

.ap-total-label {
  display: block;
  font-size: 11px;
  color: #6b5d4f;
  margin-bottom: 2px;
}

.ap-total-number {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: #2c2417;
}

/* Tooltip */
.ap-tooltip {
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%) translateY(-8px);
  padding: 8px 12px;
  background: rgba(44, 36, 23, 0.95);
  color: #f7f3e8;
  font-size: 12px;
  border-radius: 6px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.action-points-indicator:hover .ap-tooltip {
  opacity: 1;
}

.ap-tooltip::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  border: 6px solid transparent;
  border-top-color: rgba(44, 36, 23, 0.95);
}
</style>
