/**
* Recap Overlay Component
*
* 使用 shuimo-ui 水墨风组件
* Replaces custom CSS with shuimo-ui components
*/
<template>
  <Teleport to="body">
    <!-- shuimo-ui dialog -->
    <m-dialog v-model:show="showModal" title="天机推演" @confirm="handleConfirm">
      <!-- 时间段 -->
      <div class="recap-period">
        <m-text type="secondary" size="small">
          {{ recapStore.recap?.period_text }}
        </m-text>
      </div>

      <!-- Action Points -->
      <div class="recap-ap">
        <m-tag :type="hasActionPoints ? 'success' : 'default'">
          天命点数: <strong>{{ recapStore.actionPointsRemaining }}</strong> / {{ recapStore.actionPointsTotal }}
        </m-tag>
      </div>

      <!-- 总结文本 -->
      <m-alert v-if="recapStore.recap?.summary_text" type="info" :show-icon="true">
        {{ recapStore.recap.summary_text }}
      </m-alert>

      <!-- 滚动内容 -->
      <m-scroll style="max-height: 60vh; margin-top: 16px;">
        <m-space direction="vertical" :size="20">
          <!-- 宗门 recap -->
          <m-card v-if="recapStore.recap?.sect" :title="recapStore.recap.sect.sect_name" size="small">
            <template #extra>
              <m-tag type="primary" size="small">宗门</m-tag>
            </template>

            <m-space direction="vertical" :size="12">
              <!-- 状态变化 -->
              <div v-if="recapStore.recap.sect.status_changes.length">
                <m-text type="secondary" size="small">状态变化</m-text>
                <m-list :data="recapStore.recap.sect.status_changes" size="small">
                  <template #default="{ item }">
                    <m-list-item>
                      <template #prefix>
                        <div class="bullet status"></div>
                      </template>
                      {{ item }}
                    </m-list-item>
                  </template>
                </m-list>
              </div>

              <!-- 成员事件 -->
              <div v-if="recapStore.recap.sect.member_events.length">
                <m-text type="secondary" size="small">成员事件</m-text>
                <m-list :data="recapStore.recap.sect.member_events" size="small">
                  <template #default="{ item }">
                    <m-list-item>
                      <template #prefix>
                        <div class="bullet member"></div>
                      </template>
                      {{ item }}
                    </m-list-item>
                  </template>
                </m-list>
              </div>

              <!-- 威胁 -->
              <div v-if="recapStore.recap.sect.threats.length">
                <m-text type="secondary" size="small">威胁警告</m-text>
                <m-list :data="recapStore.recap.sect.threats" size="small" type="danger">
                  <template #default="{ item }">
                    <m-list-item>
                      <template #prefix>
                        <div class="bullet threat"></div>
                      </template>
                      {{ item }}
                    </m-list-item>
                  </template>
                </m-list>
              </div>
            </m-space>
          </m-card>

          <!-- 弟子 recap -->
          <m-card v-if="recapStore.recap?.main_disciple" :title="recapStore.recap.main_disciple.name" size="small">
            <template #extra>
              <m-tag type="success" size="small">弟子</m-tag>
            </template>

            <m-space direction="vertical" :size="12">
              <!-- 修炼进展 -->
              <div v-if="recapStore.recap.main_disciple.cultivation_progress">
                <m-text type="secondary" size="small">修炼</m-text>
                <m-text type="success">{{ recapStore.recap.main_disciple.cultivation_progress }}</m-text>
              </div>

              <!-- 重要事件 -->
              <div v-if="recapStore.recap.main_disciple.major_events.length">
                <m-text type="secondary" size="small">重要事件</m-text>
                <m-list :data="recapStore.recap.main_disciple.major_events" size="small">
                  <template #default="{ item }">
                    <m-list-item>
                      <template #prefix>
                        <div class="bullet major"></div>
                      </template>
                      {{ item }}
                    </m-list-item>
                  </template>
                </m-list>
              </div>

              <!-- 当前状态 -->
              <div v-if="recapStore.recap.main_disciple.current_status">
                <m-text type="secondary" size="small">状态</m-text>
                <m-text>{{ recapStore.recap.main_disciple.current_status }}</m-text>
              </div>
            </m-space>
          </m-card>

          <!-- 世界事件 -->
          <m-card title="天下大势" size="small">
            <m-space direction="vertical" :size="12">
              <!-- 天地灵机 -->
              <m-alert v-if="recapStore.recap?.world.phenomenon" type="warning" :show-icon="true">
                {{ recapStore.recap.world.phenomenon }}
              </m-alert>

              <!-- 重大事件 -->
              <div v-if="recapStore.recap?.world.major_events.length">
                <m-text type="secondary" size="small">重大事件</m-text>
                <m-list :data="recapStore.recap.world.major_events" size="small">
                  <template #default="{ item }">
                    <m-list-item>
                      <template #prefix>
                        <div class="bullet world"></div>
                      </template>
                      {{ item }}
                    </m-list-item>
                  </template>
                </m-list>
              </div>

              <!-- 宗门关系 -->
              <div v-if="recapStore.recap?.world.sect_relations.length">
                <m-text type="secondary" size="small">宗门关系</m-text>
                <m-list :data="recapStore.recap.world.sect_relations" size="small">
                  <template #default="{ item }">
                    <m-list-item>
                      <template #prefix>
                        <div class="bullet relation"></div>
                      </template>
                      {{ item }}
                    </m-list-item>
                  </template>
                </m-list>
              </div>
            </m-space>
          </m-card>

          <!-- 机会和建议 -->
          <m-card
            v-if="recapStore.recap?.opportunities.opportunities.length || recapStore.recap?.opportunities.suggested_actions.length"
            title="机缘建议" size="small">
            <m-space direction="vertical" :size="12">
              <!-- 可用机会 -->
              <div v-if="recapStore.recap?.opportunities.opportunities.length">
                <m-text type="secondary" size="small">可用机会</m-text>
                <m-list :data="recapStore.recap.opportunities.opportunities" size="small" type="success">
                  <template #default="{ item }">
                    <m-list-item>
                      <template #prefix>
                        <div class="bullet opportunity"></div>
                      </template>
                      {{ item }}
                    </m-list-item>
                  </template>
                </m-list>
              </div>

              <!-- 建议行动 -->
              <div v-if="recapStore.recap?.opportunities.suggested_actions.length">
                <m-text type="secondary" size="small">建议行动</m-text>
                <m-space direction="vertical" :size="8">
                  <m-button v-for="(action, idx) in recapStore.recap.opportunities.suggested_actions" :key="idx"
                    size="small" type="primary" plain>
                    {{ action }}
                  </m-button>
                </m-space>
              </div>
            </m-space>
          </m-card>
        </m-space>
      </m-scroll>
    </m-dialog>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import {
  MDialog,
  MCard,
  MText,
  MTag,
  MList,
  MListItem,
  MButton,
  MScroll,
  MSpace,
  MAlert,
} from 'shuimo-ui';
import { useRecapStore } from '@/stores/recap';

const { t } = useI18n();
const recapStore = useRecapStore();

// Control dialog visibility
const showModal = computed({
  get: () => recapStore.showOverlay,
  set: (val: boolean) => {
    if (!val) recapStore.closeOverlay();
  }
});

// Has action points?
const hasActionPoints = computed(() => recapStore.hasActionPoints);

// Get viewerId
const viewerId = computed(() => {
  return localStorage.getItem('viewer_id') || 'local';
});

// Confirm and acknowledge
async function handleConfirm() {
  try {
    await recapStore.acknowledge(viewerId.value);
  } catch (error) {
    console.error('Failed to acknowledge recap:', error);
  }
}

// Lock body scroll when dialog is open
watch(() => recapStore.showOverlay, (visible) => {
  document.body.style.overflow = visible ? 'hidden' : '';
});
</script>

<style scoped>
/* Minimal custom styles - shuimo-ui handles most styling */

.recap-period {
  margin-bottom: 12px;
}

.recap-ap {
  margin-bottom: 12px;
}

/* Event type colored dots */
.bullet {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.bullet.status {
  background: #4a90d9;
}

.bullet.member {
  background: #50c878;
}

.bullet.threat {
  background: #dc3545;
}

.bullet.major {
  background: #ff9800;
}

.bullet.world {
  background: #9c27b0;
}

.bullet.relation {
  background: #00bcd4;
}

.bullet.opportunity {
  background: #4caf50;
}
</style>
