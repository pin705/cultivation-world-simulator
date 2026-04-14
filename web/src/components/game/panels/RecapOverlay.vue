<template>
  <!-- Recap Overlay - 水墨风格的事件回顾 -->
  <Teleport to="body">
    <Transition name="recap-fade">
      <div v-if="recapStore.showOverlay && recapStore.recap" class="recap-overlay">
        <!-- 背景遮罩 -->
        <div class="recap-backdrop" @click="handleClose"></div>
        
        <!-- 主内容区 - 宣纸效果 -->
        <div class="recap-container">
          <!-- 标题区 - 书法风格 -->
          <header class="recap-header">
            <div class="recap-title">
              <span class="title-icon">📜</span>
              <h2>{{ t('recap.title', '天机推演') }}</h2>
            </div>
            <p class="recap-period">{{ recapStore.recap.period_text }}</p>
            
            <!-- Action Points 指示器 -->
            <div class="action-points-bar" v-if="recapStore.recap.action_points.total > 0">
              <span class="ap-label">{{ t('recap.fatePoints', '天命点数') }}</span>
              <div class="ap-dots">
                <span 
                  v-for="i in recapStore.recap.action_points.total" 
                  :key="i"
                  class="ap-dot"
                  :class="{ spent: i > recapStore.recap!.action_points.remaining }"
                ></span>
              </div>
              <span class="ap-count">
                {{ recapStore.recap.action_points.remaining }}/{{ recapStore.recap.action_points.total }}
              </span>
            </div>
          </header>

          <!-- 滚动内容区 -->
          <div class="recap-content">
            <!-- 总结文本 -->
            <div v-if="recapStore.recap.summary_text" class="recap-summary">
              {{ recapStore.recap.summary_text }}
            </div>

            <!-- 宗门 recap -->
            <RecapSection
              v-if="recapStore.recap.sect"
              :title="t('recap.sect', '宗门动态')"
              icon="🏛️"
            >
              <template #subtitle>{{ recapStore.recap.sect.sect_name }}</template>
              
              <div v-if="recapStore.recap.sect.status_changes.length" class="event-group">
                <h4 class="group-title">{{ t('recap.statusChanges', '状态变化') }}</h4>
                <ul class="event-list">
                  <li v-for="(event, idx) in recapStore.recap.sect.status_changes" :key="idx" class="event-item">
                    <span class="event-bullet status"></span>
                    <span class="event-text">{{ event }}</span>
                  </li>
                </ul>
              </div>

              <div v-if="recapStore.recap.sect.member_events.length" class="event-group">
                <h4 class="group-title">{{ t('recap.memberEvents', '成员事件') }}</h4>
                <ul class="event-list">
                  <li v-for="(event, idx) in recapStore.recap.sect.member_events" :key="idx" class="event-item">
                    <span class="event-bullet member"></span>
                    <span class="event-text">{{ event }}</span>
                  </li>
                </ul>
              </div>

              <div v-if="recapStore.recap.sect.threats.length" class="event-group threat">
                <h4 class="group-title">{{ t('recap.threats', '威胁警告') }}</h4>
                <ul class="event-list">
                  <li v-for="(event, idx) in recapStore.recap.sect.threats" :key="idx" class="event-item">
                    <span class="event-bullet threat"></span>
                    <span class="event-text">{{ event }}</span>
                  </li>
                </ul>
              </div>
            </RecapSection>

            <!-- 弟子 recap -->
            <RecapSection
              v-if="recapStore.recap.main_disciple"
              :title="t('recap.disciple', '弟子进展')"
              icon="🧑‍🎓"
            >
              <template #subtitle>{{ recapStore.recap.main_disciple.name }}</template>
              
              <div v-if="recapStore.recap.main_disciple.cultivation_progress" class="cultivation-progress">
                <span class="label">{{ t('recap.cultivation', '修炼') }}:</span>
                <span class="value">{{ recapStore.recap.main_disciple.cultivation_progress }}</span>
              </div>

              <div v-if="recapStore.recap.main_disciple.major_events.length" class="event-group">
                <h4 class="group-title">{{ t('recap.majorEvents', '重要事件') }}</h4>
                <ul class="event-list">
                  <li v-for="(event, idx) in recapStore.recap.main_disciple.major_events" :key="idx" class="event-item">
                    <span class="event-bullet major"></span>
                    <span class="event-text">{{ event }}</span>
                  </li>
                </ul>
              </div>

              <div v-if="recapStore.recap.main_disciple.current_status" class="current-status">
                <span class="label">{{ t('recap.status', '状态') }}:</span>
                <span class="value">{{ recapStore.recap.main_disciple.current_status }}</span>
              </div>
            </RecapSection>

            <!-- 世界事件 recap -->
            <RecapSection
              :title="t('recap.world', '天下大势')"
              icon="🌍"
            >
              <div v-if="recapStore.recap.world.phenomenon" class="phenomenon-banner">
                <span class="phenomenon-icon">✨</span>
                <span class="phenomenon-text">{{ recapStore.recap.world.phenomenon }}</span>
              </div>

              <div v-if="recapStore.recap.world.major_events.length" class="event-group">
                <h4 class="group-title">{{ t('recap.majorEvents', '重大事件') }}</h4>
                <ul class="event-list">
                  <li v-for="(event, idx) in recapStore.recap.world.major_events" :key="idx" class="event-item">
                    <span class="event-bullet world"></span>
                    <span class="event-text">{{ event }}</span>
                  </li>
                </ul>
              </div>

              <div v-if="recapStore.recap.world.sect_relations.length" class="event-group">
                <h4 class="group-title">{{ t('recap.sectRelations', '宗门关系') }}</h4>
                <ul class="event-list">
                  <li v-for="(event, idx) in recapStore.recap.world.sect_relations" :key="idx" class="event-item">
                    <span class="event-bullet relation"></span>
                    <span class="event-text">{{ event }}</span>
                  </li>
                </ul>
              </div>
            </RecapSection>

            <!-- 机会和建议 -->
            <RecapSection
              v-if="recapStore.recap.opportunities.opportunities.length || recapStore.recap.opportunities.suggested_actions.length"
              :title="t('recap.opportunities', '机缘建议')"
              icon="💫"
            >
              <div v-if="recapStore.recap.opportunities.opportunities.length" class="opportunity-list">
                <h4 class="group-title">{{ t('recap.availableOpportunities', '可用机会') }}</h4>
                <ul class="event-list">
                  <li v-for="(opp, idx) in recapStore.recap.opportunities.opportunities" :key="idx" class="event-item opportunity">
                    <span class="event-bullet opportunity"></span>
                    <span class="event-text">{{ opp }}</span>
                  </li>
                </ul>
              </div>

              <div v-if="recapStore.recap.opportunities.suggested_actions.length" class="suggested-actions">
                <h4 class="group-title">{{ t('recap.suggestedActions', '建议行动') }}</h4>
                <ul class="action-list">
                  <li v-for="(action, idx) in recapStore.recap.opportunities.suggested_actions" :key="idx" class="action-item">
                    <span class="action-icon">→</span>
                    <span class="action-text">{{ action }}</span>
                  </li>
                </ul>
              </div>
            </RecapSection>
          </div>

          <!-- 底部操作区 -->
          <footer class="recap-footer">
            <div class="recap-hint">
              {{ t('recap.hint', '阅毕此卷，天命由心') }}
            </div>
            <button 
              class="recap-confirm-btn"
              @click="handleConfirm"
              :disabled="recapStore.loading"
            >
              <span v-if="recapStore.loading" class="loading-spinner"></span>
              <span v-else>{{ t('recap.confirm', '了如指掌') }}</span>
            </button>
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { useRecapStore } from '@/stores/recap';
import RecapSection from './RecapSection.vue';
import { computed } from 'vue';

const { t } = useI18n();
const recapStore = useRecapStore();

// 获取 viewerId (从 auth store 或其他地方获取)
// TODO: Replace with actual viewerId from auth store
const viewerId = computed(() => {
  // This should come from your auth store
  return localStorage.getItem('viewer_id') || 'local';
});

async function handleConfirm() {
  try {
    await recapStore.acknowledge(viewerId.value);
  } catch (error) {
    console.error('Failed to acknowledge recap:', error);
    // Could show a toast notification here
  }
}

function handleClose() {
  // Optional: allow closing by clicking backdrop
  // For now, only the confirm button works
}
</script>

<style scoped>
/* Shuimo-inspired: 水墨风格 */

/* 过渡动画 */
.recap-fade-enter-active,
.recap-fade-leave-active {
  transition: opacity 0.4s ease;
}

.recap-fade-enter-from,
.recap-fade-leave-to {
  opacity: 0;
}

/* 背景遮罩 */
.recap-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}

.recap-backdrop {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(20, 20, 25, 0.7);
  backdrop-filter: blur(4px);
}

/* 主容器 - 宣纸效果 */
.recap-container {
  position: relative;
  width: 90%;
  max-width: 800px;
  max-height: 85vh;
  background: #f7f3e8; /* 米色宣纸 */
  background-image: 
    linear-gradient(90deg, rgba(200, 180, 140, 0.03) 1px, transparent 1px),
    linear-gradient(rgba(200, 180, 140, 0.03) 1px, transparent 1px);
  background-size: 20px 20px;
  border-radius: 8px;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.4),
    0 2px 8px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(139, 119, 90, 0.2);
}

/* 标题区 */
.recap-header {
  padding: 24px 32px 16px;
  border-bottom: 2px solid rgba(139, 119, 90, 0.3);
  background: linear-gradient(to bottom, rgba(245, 240, 225, 0.5), transparent);
}

.recap-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.title-icon {
  font-size: 28px;
  filter: grayscale(0.3);
}

.recap-title h2 {
  margin: 0;
  font-size: 26px;
  font-weight: 600;
  color: #2c2417; /* 墨色 */
  letter-spacing: 2px;
  font-family: "STKaiti", "KaiTi", "Microsoft YaHei", sans-serif; /* 楷体 */
}

.recap-period {
  margin: 0 0 12px;
  font-size: 13px;
  color: #6b5d4f;
  font-style: italic;
}

/* Action Points 条 */
.action-points-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: rgba(139, 119, 90, 0.1);
  border-radius: 6px;
}

.ap-label {
  font-size: 13px;
  color: #6b5d4f;
  font-weight: 500;
}

.ap-dots {
  display: flex;
  gap: 6px;
  flex: 1;
}

.ap-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #8b775a;
  transition: all 0.3s ease;
}

.ap-dot.spent {
  background: rgba(139, 119, 90, 0.2);
  border: 1px dashed rgba(139, 119, 90, 0.4);
}

.ap-count {
  font-size: 13px;
  color: #2c2417;
  font-weight: 600;
  min-width: 40px;
  text-align: right;
}

/* 内容滚动区 */
.recap-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
}

/* 总结文本 */
.recap-summary {
  padding: 16px;
  margin-bottom: 24px;
  background: rgba(139, 119, 90, 0.05);
  border-left: 3px solid rgba(139, 119, 90, 0.3);
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.7;
  color: #4a3f35;
  font-style: italic;
}

/* 事件组 */
.event-group {
  margin-bottom: 20px;
}

.event-group.threat {
  padding: 12px;
  background: rgba(220, 53, 69, 0.05);
  border-left: 3px solid rgba(220, 53, 69, 0.3);
  border-radius: 4px;
}

.group-title {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 600;
  color: #6b5d4f;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.event-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.event-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid rgba(139, 119, 90, 0.1);
}

.event-item:last-child {
  border-bottom: none;
}

.event-bullet {
  flex-shrink: 0;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 6px;
}

.event-bullet.status {
  background: #4a90d9;
}

.event-bullet.member {
  background: #50c878;
}

.event-bullet.threat {
  background: #dc3545;
}

.event-bullet.major {
  background: #ff9800;
}

.event-bullet.world {
  background: #9c27b0;
}

.event-bullet.relation {
  background: #00bcd4;
}

.event-bullet.opportunity {
  background: #4caf50;
}

.event-text {
  flex: 1;
  font-size: 14px;
  line-height: 1.6;
  color: #2c2417;
}

/* 弟子进展 */
.cultivation-progress,
.current-status {
  display: flex;
  gap: 8px;
  padding: 10px 12px;
  margin-bottom: 12px;
  background: rgba(139, 119, 90, 0.08);
  border-radius: 4px;
}

.label {
  font-size: 13px;
  color: #6b5d4f;
  font-weight: 500;
}

.value {
  flex: 1;
  font-size: 13px;
  color: #2c2417;
  font-weight: 600;
}

/* 天地灵机 */
.phenomenon-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  margin-bottom: 16px;
  background: linear-gradient(135deg, rgba(156, 39, 176, 0.1), rgba(156, 39, 176, 0.05));
  border: 1px solid rgba(156, 39, 176, 0.2);
  border-radius: 6px;
}

.phenomenon-icon {
  font-size: 20px;
}

.phenomenon-text {
  flex: 1;
  font-size: 14px;
  color: #9c27b0;
  font-weight: 600;
}

/* 机会列表 */
.event-item.opportunity {
  background: rgba(76, 175, 80, 0.05);
  padding: 10px 12px;
  margin-bottom: 8px;
  border-radius: 4px;
  border-bottom: none;
}

/* 建议行动 */
.action-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  margin-bottom: 8px;
  background: rgba(76, 175, 80, 0.08);
  border-radius: 4px;
}

.action-icon {
  font-size: 16px;
  color: #4caf50;
}

.action-text {
  flex: 1;
  font-size: 14px;
  color: #2c2417;
}

/* 底部操作区 */
.recap-footer {
  padding: 20px 32px 24px;
  border-top: 2px solid rgba(139, 119, 90, 0.3);
  background: linear-gradient(to top, rgba(245, 240, 225, 0.5), transparent);
}

.recap-hint {
  text-align: center;
  font-size: 13px;
  color: #6b5d4f;
  margin-bottom: 16px;
  font-style: italic;
  letter-spacing: 1px;
}

.recap-confirm-btn {
  width: 100%;
  padding: 14px 24px;
  font-size: 16px;
  font-weight: 600;
  color: #f7f3e8;
  background: linear-gradient(135deg, #8b775a, #6b5d4f);
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  letter-spacing: 2px;
  font-family: "STKaiti", "KaiTi", "Microsoft YaHei", sans-serif;
}

.recap-confirm-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #9c8b6d, #7d6f5f);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(139, 119, 90, 0.4);
}

.recap-confirm-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(247, 243, 232, 0.3);
  border-top-color: #f7f3e8;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 响应式 */
@media (max-width: 768px) {
  .recap-container {
    width: 95%;
    max-height: 90vh;
  }
  
  .recap-header,
  .recap-content,
  .recap-footer {
    padding-left: 20px;
    padding-right: 20px;
  }
  
  .recap-title h2 {
    font-size: 22px;
  }
}
</style>
