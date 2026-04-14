<template>
  <!-- Recap Overlay - Using shuimo-ui components -->
  <Teleport to="body">
    <m-dialog v-model:show="showModal" title="天机推演" @confirm="handleConfirm">
      <!-- 时间段 -->
      <div class="recap-period">
        <span class="text-secondary text-small">{{ recapStore.recap?.period_text }}</span>
      </div>

      <!-- Action Points -->
      <div class="recap-ap">
        <m-tag :type="hasActionPoints ? 'success' : 'default'">
          天命点数: <strong>{{ recapStore.actionPointsRemaining }}</strong> / {{ recapStore.actionPointsTotal }}
        </m-tag>
      </div>

      <!-- 总结文本 -->
      <div v-if="recapStore.recap?.summary_text" class="recap-summary">
        {{ recapStore.recap.summary_text }}
      </div>

      <!-- 滚动内容 -->
      <div class="recap-content">
        <div class="vertical-space">
          <!-- 宗门 recap -->
          <div v-if="recapStore.recap?.sect" class="recap-card">
            <div class="card-header">
              <span class="card-title">{{ recapStore.recap.sect.sect_name }}</span>
              <m-tag type="primary" size="small">宗门</m-tag>
            </div>

            <m-divider>状态变化</m-divider>
            <m-list v-if="recapStore.recap.sect.status_changes.length" :data="recapStore.recap.sect.status_changes"
              size="small">
              <template #default="{ item }">
                <m-li>
                  <template #prefix>
                    <div class="bullet status"></div>
                  </template>
                  {{ item }}
                </m-li>
              </template>
            </m-list>

            <m-divider>成员事件</m-divider>
            <m-list v-if="recapStore.recap.sect.member_events.length" :data="recapStore.recap.sect.member_events"
              size="small">
              <template #default="{ item }">
                <m-li>
                  <template #prefix>
                    <div class="bullet member"></div>
                  </template>
                  {{ item }}
                </m-li>
              </template>
            </m-list>

            <m-divider>威胁警告</m-divider>
            <m-list v-if="recapStore.recap.sect.threats.length" :data="recapStore.recap.sect.threats" size="small">
              <template #default="{ item }">
                <m-li>
                  <template #prefix>
                    <div class="bullet threat"></div>
                  </template>
                  <span class="text-danger">{{ item }}</span>
                </m-li>
              </template>
            </m-list>
          </div>

          <!-- 弟子 recap -->
          <div v-if="recapStore.recap?.main_disciple" class="recap-card">
            <div class="card-header">
              <span class="card-title">{{ recapStore.recap.main_disciple.name }}</span>
              <m-tag type="success" size="small">弟子</m-tag>
            </div>

            <div v-if="recapStore.recap.main_disciple.cultivation_progress" class="info-row">
              <span class="label">修炼:</span>
              <span class="text-success">{{ recapStore.recap.main_disciple.cultivation_progress }}</span>
            </div>

            <m-divider>重要事件</m-divider>
            <m-list v-if="recapStore.recap.main_disciple.major_events.length"
              :data="recapStore.recap.main_disciple.major_events" size="small">
              <template #default="{ item }">
                <m-li>
                  <template #prefix>
                    <div class="bullet major"></div>
                  </template>
                  {{ item }}
                </m-li>
              </template>
            </m-list>

            <div v-if="recapStore.recap.main_disciple.current_status" class="info-row">
              <span class="label">状态:</span>
              <span>{{ recapStore.recap.main_disciple.current_status }}</span>
            </div>

            <!-- Breakthrough Alerts -->
            <div v-if="recapStore.recap?.main_disciple?.cultivation_progress" class="breakthrough-alert">
              <m-tag type="warning" size="medium">
                🔥 {{ recapStore.recap.main_disciple.cultivation_progress }}
              </m-tag>
            </div>
          </div>

          <!-- 世界事件 -->
          <div class="recap-card">
            <div class="card-header">
              <span class="card-title">天下大势</span>
            </div>

            <div v-if="recapStore.recap?.world.phenomenon" class="phenomenon-alert">
              <span class="phenomenon-text">{{ recapStore.recap.world.phenomenon }}</span>
            </div>

            <m-divider>重大事件</m-divider>
            <m-list v-if="recapStore.recap?.world.major_events.length" :data="recapStore.recap.world.major_events"
              size="small">
              <template #default="{ item }">
                <m-li>
                  <template #prefix>
                    <div class="bullet world"></div>
                  </template>
                  {{ item }}
                </m-li>
              </template>
            </m-list>

            <m-divider>宗门关系</m-divider>
            <m-list v-if="recapStore.recap?.world.sect_relations.length" :data="recapStore.recap.world.sect_relations"
              size="small">
              <template #default="{ item }">
                <m-li>
                  <template #prefix>
                    <div class="bullet relation"></div>
                  </template>
                  {{ item }}
                </m-li>
              </template>
            </m-list>
          </div>

          <!-- 机会和建议 -->
          <div
            v-if="recapStore.recap?.opportunities.opportunities.length || recapStore.recap?.opportunities.suggested_actions.length"
            class="recap-card">
            <div class="card-header">
              <span class="card-title">机缘建议</span>
            </div>

            <m-divider>可用机会</m-divider>
            <m-list v-if="recapStore.recap?.opportunities.opportunities.length"
              :data="recapStore.recap.opportunities.opportunities" size="small">
              <template #default="{ item }">
                <m-li>
                  <template #prefix>
                    <div class="bullet opportunity"></div>
                  </template>
                  <span class="text-success">{{ item }}</span>
                </m-li>
              </template>
            </m-list>

            <m-divider>建议行动</m-divider>
            <div v-if="recapStore.recap?.opportunities.suggested_actions.length" class="vertical-space small">
              <m-button v-for="(action, idx) in recapStore.recap.opportunities.suggested_actions" :key="idx"
                size="small" type="primary" plain>
                {{ action }}
              </m-button>
            </div>
          </div>

          <!-- Thrill Events -->
          <div v-if="hasThrillEvents" class="recap-card thrill-events">
            <div class="card-header">
              <span class="card-title">历练事件</span>
            </div>
            <!-- Show secret realm discoveries, heart demon encounters, etc. -->
            <m-divider>秘境探索</m-divider>
            <m-list v-if="recapStore.recap?.thrill_events?.secret_realms?.length"
              :data="recapStore.recap.thrill_events.secret_realms" size="small">
              <template #default="{ item }">
                <m-li>
                  <template #prefix>
                    <div class="bullet thrill"></div>
                  </template>
                  {{ item }}
                </m-li>
              </template>
            </m-list>

            <m-divider>心魔遭遇</m-divider>
            <m-list v-if="recapStore.recap?.thrill_events?.heart_demons?.length"
              :data="recapStore.recap.thrill_events.heart_demons" size="small">
              <template #default="{ item }">
                <m-li>
                  <template #prefix>
                    <div class="bullet heart-demon"></div>
                  </template>
                  {{ item }}
                </m-li>
              </template>
            </m-list>
          </div>

          <!-- Competition Results -->
          <div v-if="hasCompetitionEvents" class="recap-card competition-results">
            <div class="card-header">
              <span class="card-title">竞技事件</span>
            </div>
            <!-- Show arena challenges, rivalry changes, etc. -->
            <m-divider>竞技场挑战</m-divider>
            <m-list v-if="recapStore.recap?.competition_events?.arena_challenges?.length"
              :data="recapStore.recap.competition_events.arena_challenges" size="small">
              <template #default="{ item }">
                <m-li>
                  <template #prefix>
                    <div class="bullet arena"></div>
                  </template>
                  {{ item }}
                </m-li>
              </template>
            </m-list>

            <m-divider>宿敌变化</m-divider>
            <m-list v-if="recapStore.recap?.competition_events?.rivalry_changes?.length"
              :data="recapStore.recap.competition_events.rivalry_changes" size="small">
              <template #default="{ item }">
                <m-li>
                  <template #prefix>
                    <div class="bullet rivalry"></div>
                  </template>
                  {{ item }}
                </m-li>
              </template>
            </m-list>
          </div>
        </div>
      </div>
    </m-dialog>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import {
  MDialog,
  MTag,
  MList,
  MLi,
  MButton,
  MDivider,
} from 'shuimo-ui';
import { useRecapStore } from '@/stores/recap';
import { shuimoColors } from '@/themes/shuimo';

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

// Has thrill events?
const hasThrillEvents = computed(() => {
  const thrill = recapStore.recap?.thrill_events;
  return (
    thrill?.secret_realms?.length ||
    thrill?.heart_demons?.length
  );
});

// Has competition events?
const hasCompetitionEvents = computed(() => {
  const comp = recapStore.recap?.competition_events;
  return (
    comp?.arena_challenges?.length ||
    comp?.rivalry_changes?.length
  );
});

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

.recap-summary {
  padding: 12px;
  margin-bottom: 16px;
  background: rgba(74, 144, 217, 0.08);
  border-left: 3px solid v-bind('shuimoColors.info');
  border-radius: 4px;
  font-style: italic;
  font-size: 13px;
  line-height: 1.6;
  color: v-bind('shuimoColors.info');
}

.recap-content {
  max-height: 60vh;
  overflow-y: auto;
  margin-top: 16px;
  padding-right: 8px;
}

.vertical-space {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.vertical-space.small {
  gap: 8px;
}

.recap-card {
  padding: 16px;
  border: 1px solid rgba(139, 119, 90, 0.2);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.4);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: v-bind('shuimoColors.status');
  font-family: "STKaiti", "KaiTi", sans-serif;
}

.info-row {
  display: flex;
  gap: 8px;
  padding: 8px 12px;
  margin-bottom: 8px;
  background: rgba(139, 119, 90, 0.08);
  border-radius: 4px;
  font-size: 13px;
}

.info-row .label {
  color: v-bind('shuimoColors.threat');
  font-weight: 500;
}

.phenomenon-alert {
  padding: 10px 12px;
  margin-bottom: 12px;
  background: rgba(255, 152, 0, 0.08);
  border: 1px solid rgba(255, 152, 0, 0.2);
  border-radius: 4px;
}

.phenomenon-text {
  font-size: 13px;
  color: v-bind('shuimoColors.major');
  font-weight: 600;
}

/* Event type colored dots */
.bullet {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.bullet.status {
  background: v-bind('shuimoColors.status');
}

.bullet.member {
  background: v-bind('shuimoColors.member');
}

.bullet.threat {
  background: v-bind('shuimoColors.threat');
}

.bullet.major {
  background: v-bind('shuimoColors.major');
}

.bullet.world {
  background: v-bind('shuimoColors.world');
}

.bullet.relation {
  background: v-bind('shuimoColors.relation');
}

.bullet.opportunity {
  background: v-bind('shuimoColors.opportunity');
}

.bullet.thrill {
  background: v-bind('shuimoColors.success');
}

.bullet.heart-demon {
  background: v-bind('shuimoColors.error');
}

.bullet.arena {
  background: v-bind('shuimoColors.major');
}

.bullet.rivalry {
  background: v-bind('shuimoColors.threat');
}

/* Breakthrough alerts */
.breakthrough-alert {
  margin-top: 12px;
}

/* Text utilities */
.text-secondary {
  color: v-bind('shuimoColors.threat');
  font-style: italic;
}

.text-small {
  font-size: 13px;
}

.text-success {
  color: v-bind('shuimoColors.success');
  font-weight: 600;
}

.text-danger {
  color: v-bind('shuimoColors.error');
  font-weight: 600;
}
</style>
