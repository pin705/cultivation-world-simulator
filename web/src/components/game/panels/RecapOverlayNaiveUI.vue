<template>
  <!-- Recap Overlay - 使用 Naive UI 组件 + Shuimo 主题 -->
  <Teleport to="body">
    <NModal
      v-model:show="showModal"
      preset="card"
      :style="{ maxWidth: '800px', width: '90%' }"
      :bordered="false"
      size="huge"
      role="dialog"
      aria-modal="true"
      class="recap-modal"
      @after-leave="handleAfterLeave"
    >
      <!-- Header -->
      <template #header>
        <div class="recap-header">
          <NIcon size="24" :color="shuimoColors.primary">
            <ScrollOutlined />
          </NIcon>
          <span class="recap-title">{{ t('recap.title', '天机推演') }}</span>
        </div>
      </template>
      
      <template #header-extra>
        <NTag :type="hasActionPoints ? 'success' : 'default'" size="medium">
          {{ t('recap.fatePoints', '天命点数') }}: 
          <strong>{{ recapStore.actionPointsRemaining }}</strong> / {{ recapStore.actionPointsTotal }}
        </NTag>
      </template>

      <!-- 时间段 -->
      <NText depth="3" class="period-text">
        {{ recapStore.recap?.period_text }}
      </NText>

      <!-- 总结文本 -->
      <NAlert
        v-if="recapStore.recap?.summary_text"
        type="info"
        :bordered="false"
        class="summary-alert"
      >
        {{ recapStore.recap.summary_text }}
      </NAlert>

      <!-- 滚动内容区 -->
      <NScrollbar :style="{ maxHeight: '60vh' }">
        <NSpace vertical :size="24" class="recap-content">
          <!-- 宗门 recap -->
          <NCard
            v-if="recapStore.recap?.sect"
            :title="t('recap.sect', '宗门动态')"
            size="small"
            :bordered="false"
          >
            <template #header-extra>
              <NIcon size="18">
                <BankOutlined />
              </NIcon>
            </template>
            
            <template #header>
              <div class="card-header">
                <span>{{ t('recap.sect', '宗门动态') }}</span>
                <NTag size="small" type="info">{{ recapStore.recap.sect.sect_name }}</NTag>
              </div>
            </template>

            <NSpace vertical :size="16">
              <!-- 状态变化 -->
              <div v-if="recapStore.recap.sect.status_changes.length">
                <NText strong depth="2">{{ t('recap.statusChanges', '状态变化') }}</NText>
                <NList hoverable clickable class="event-list">
                  <NListItem v-for="(event, idx) in recapStore.recap.sect.status_changes" :key="idx">
                    <template #prefix>
                      <NSpace align="center">
                        <NBadge :color="shuimoColors.status" dot />
                        <NText>{{ event }}</NText>
                      </NSpace>
                    </template>
                  </NListItem>
                </NList>
              </div>

              <!-- 成员事件 -->
              <div v-if="recapStore.recap.sect.member_events.length">
                <NText strong depth="2">{{ t('recap.memberEvents', '成员事件') }}</NText>
                <NList hoverable clickable class="event-list">
                  <NListItem v-for="(event, idx) in recapStore.recap.sect.member_events" :key="idx">
                    <template #prefix>
                      <NSpace align="center">
                        <NBadge :color="shuimoColors.member" dot />
                        <NText>{{ event }}</NText>
                      </NSpace>
                    </template>
                  </NListItem>
                </NList>
              </div>

              <!-- 威胁 -->
              <div v-if="recapStore.recap.sect.threats.length">
                <NText strong depth="2">{{ t('recap.threats', '威胁警告') }}</NText>
                <NList hoverable clickable class="event-list threat-list">
                  <NListItem v-for="(event, idx) in recapStore.recap.sect.threats" :key="idx">
                    <template #prefix>
                      <NSpace align="center">
                        <NBadge :color="shuimoColors.threat" dot />
                        <NText type="error">{{ event }}</NText>
                      </NSpace>
                    </template>
                  </NListItem>
                </NList>
              </div>
            </NSpace>
          </NCard>

          <!-- 弟子 recap -->
          <NCard
            v-if="recapStore.recap?.main_disciple"
            :title="t('recap.disciple', '弟子进展')"
            size="small"
            :bordered="false"
          >
            <template #header-extra>
              <NIcon size="18">
                <PersonOutlined />
              </NIcon>
            </template>

            <template #header>
              <div class="card-header">
                <span>{{ t('recap.disciple', '弟子进展') }}</span>
                <NTag size="small" type="success">{{ recapStore.recap.main_disciple.name }}</NTag>
              </div>
            </template>

            <NSpace vertical :size="16">
              <!-- 修炼进展 -->
              <NDescriptions
                v-if="recapStore.recap.main_disciple.cultivation_progress || recapStore.recap.main_disciple.current_status"
                :column="1"
                size="small"
                bordered
              >
                <NDescriptionsItem
                  v-if="recapStore.recap.main_disciple.cultivation_progress"
                  :label="t('recap.cultivation', '修炼')"
                >
                  <NText type="success">{{ recapStore.recap.main_disciple.cultivation_progress }}</NText>
                </NDescriptionsItem>
                <NDescriptionsItem
                  v-if="recapStore.recap.main_disciple.current_status"
                  :label="t('recap.status', '状态')"
                >
                  {{ recapStore.recap.main_disciple.current_status }}
                </NDescriptionsItem>
              </NDescriptions>

              <!-- 重要事件 -->
              <div v-if="recapStore.recap.main_disciple.major_events.length">
                <NText strong depth="2">{{ t('recap.majorEvents', '重要事件') }}</NText>
                <NList hoverable clickable class="event-list">
                  <NListItem v-for="(event, idx) in recapStore.recap.main_disciple.major_events" :key="idx">
                    <template #prefix>
                      <NSpace align="center">
                        <NBadge :color="shuimoColors.major" dot />
                        <NText>{{ event }}</NText>
                      </NSpace>
                    </template>
                  </NListItem>
                </NList>
              </div>
            </NSpace>
          </NCard>

          <!-- 世界事件 recap -->
          <NCard
            title="天下大势"
            size="small"
            :bordered="false"
          >
            <template #header-extra>
              <NIcon size="18">
                <PublicOutlined />
              </NIcon>
            </template>

            <NSpace vertical :size="16">
              <!-- 天地灵机 -->
              <NAlert
                v-if="recapStore.recap?.world.phenomenon"
                type="warning"
                :bordered="false"
                show-icon
              >
                <template #header>
                  {{ t('recap.phenomenon', '天地灵机') }}
                </template>
                {{ recapStore.recap.world.phenomenon }}
              </NAlert>

              <!-- 重大事件 -->
              <div v-if="recapStore.recap?.world.major_events.length">
                <NText strong depth="2">{{ t('recap.majorEvents', '重大事件') }}</NText>
                <NList hoverable clickable class="event-list">
                  <NListItem v-for="(event, idx) in recapStore.recap.world.major_events" :key="idx">
                    <template #prefix>
                      <NSpace align="center">
                        <NBadge :color="shuimoColors.world" dot />
                        <NText>{{ event }}</NText>
                      </NSpace>
                    </template>
                  </NListItem>
                </NList>
              </div>

              <!-- 宗门关系 -->
              <div v-if="recapStore.recap?.world.sect_relations.length">
                <NText strong depth="2">{{ t('recap.sectRelations', '宗门关系') }}</NText>
                <NList hoverable clickable class="event-list">
                  <NListItem v-for="(event, idx) in recapStore.recap.world.sect_relations" :key="idx">
                    <template #prefix>
                      <NSpace align="center">
                        <NBadge :color="shuimoColors.relation" dot />
                        <NText>{{ event }}</NText>
                      </NSpace>
                    </template>
                  </NListItem>
                </NList>
              </div>
            </NSpace>
          </NCard>

          <!-- 机会和建议 -->
          <NCard
            v-if="recapStore.recap?.opportunities.opportunities.length || recapStore.recap?.opportunities.suggested_actions.length"
            :title="t('recap.opportunities', '机缘建议')"
            size="small"
            :bordered="false"
          >
            <template #header-extra>
              <NIcon size="18">
                <BulbOutlined />
              </NIcon>
            </template>

            <NSpace vertical :size="16">
              <!-- 可用机会 -->
              <div v-if="recapStore.recap?.opportunities.opportunities.length">
                <NText strong depth="2">{{ t('recap.availableOpportunities', '可用机会') }}</NText>
                <NList hoverable clickable class="event-list opportunity-list">
                  <NListItem v-for="(opp, idx) in recapStore.recap.opportunities.opportunities" :key="idx">
                    <template #prefix>
                      <NSpace align="center">
                        <NBadge :color="shuimoColors.opportunity" dot />
                        <NText type="success">{{ opp }}</NText>
                      </NSpace>
                    </template>
                  </NListItem>
                </NList>
              </div>

              <!-- 建议行动 -->
              <div v-if="recapStore.recap?.opportunities.suggested_actions.length">
                <NText strong depth="2">{{ t('recap.suggestedActions', '建议行动') }}</NText>
                <NSpace vertical :size="8">
                  <NButton
                    v-for="(action, idx) in recapStore.recap.opportunities.suggested_actions"
                    :key="idx"
                    size="small"
                    quaternary
                    type="primary"
                  >
                    <template #icon>
                      <NIcon>
                        <ArrowRightOutlined />
                      </NIcon>
                    </template>
                    {{ action }}
                  </NButton>
                </NSpace>
              </div>
            </NSpace>
          </NCard>
        </NSpace>
      </NScrollbar>

      <!-- Footer -->
      <template #footer>
        <NSpace justify="center">
          <NText depth="3" class="hint-text">
            {{ t('recap.hint', '阅毕此卷，天命由心') }}
          </NText>
        </NSpace>
        <NSpace justify="center" style="margin-top: 12px;">
          <NButton
            type="primary"
            size="large"
            :loading="recapStore.loading"
            @click="handleConfirm"
          >
            {{ t('recap.confirm', '了如指掌') }}
          </NButton>
        </NSpace>
      </template>
    </NModal>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { 
  NModal, 
  NCard, 
  NText, 
  NTag, 
  NIcon, 
  NSpace, 
  NList, 
  NListItem,
  NBadge,
  NButton,
  NScrollbar,
  NAlert,
  NDescriptions,
  NDescriptionsItem,
} from 'naive-ui';
import { 
  ScrollOutlined,
  BankOutlined,
  PersonOutlined,
  PublicOutlined,
  BulbOutlined,
  ArrowRightOutlined,
} from '@vicons/antd';
import { useRecapStore } from '@/stores/recap';
import { shuimoColors } from '@/themes/shuimo';

const { t } = useI18n();
const recapStore = useRecapStore();

// 控制 modal 显示
const showModal = computed(() => recapStore.showOverlay);

// 是否有 action points
const hasActionPoints = computed(() => recapStore.hasActionPoints);

// 获取 viewerId
const viewerId = computed(() => {
  return localStorage.getItem('viewer_id') || 'local';
});

// 确认已读
async function handleConfirm() {
  try {
    await recapStore.acknowledge(viewerId.value);
  } catch (error) {
    console.error('Failed to acknowledge recap:', error);
  }
}

// Modal 关闭后清理
function handleAfterLeave() {
  // 可以添加清理逻辑
}

// 监听 gameInitialized 状态（如果需要从外部触发）
watch(() => recapStore.showOverlay, (visible) => {
  if (visible) {
    document.body.style.overflow = 'hidden';
  } else {
    document.body.style.overflow = '';
  }
});
</script>

<style scoped>
/* 仅保留少量自定义样式，主要使用 Naive UI 的主题系统 */

.recap-modal :deep(.n-card__content) {
  padding: 0;
}

.recap-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.recap-title {
  font-size: 18px;
  font-weight: 600;
  color: v-bind('shuimoColors.textPrimary');
  font-family: "STKaiti", "KaiTi", sans-serif;
  letter-spacing: 1px;
}

.period-text {
  display: block;
  margin-bottom: 16px;
  font-size: 13px;
  font-style: italic;
}

.summary-alert {
  margin-bottom: 20px;
  font-style: italic;
}

.recap-content {
  padding: 4px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.event-list {
  margin-top: 8px;
}

.threat-list :deep(.n-list-item) {
  background: rgba(220, 53, 69, 0.05);
}

.opportunity-list :deep(.n-list-item) {
  background: rgba(76, 175, 80, 0.05);
}

.hint-text {
  font-style: italic;
  letter-spacing: 1px;
  font-size: 13px;
}

/* 响应式 */
@media (max-width: 768px) {
  .recap-modal {
    width: 95% !important;
  }
}
</style>
