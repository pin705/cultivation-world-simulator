<template>
  <div class="arena-panel">
    <h3 class="title">竞技场</h3>
    
    <div v-if="leaderboard.length === 0" class="empty-state">
      <p>No arena rankings available</p>
    </div>
    
    <div v-else class="leaderboard">
      <div
        v-for="(entry, index) in leaderboard"
        :key="entry.id"
        class="leaderboard-entry"
        :class="{
          'top-3': index < 3,
          'is-challenger': entry.id === challengerId,
        }"
      >
        <div class="rank-badge" :class="getRankClass(index)">
          #{{ entry.rank || index + 1 }}
        </div>
        
        <div class="avatar-info">
          <span class="avatar-name">{{ entry.name }}</span>
          <span class="avatar-rating">Rating: {{ entry.arena_rating || 1000 }}</span>
        </div>
        
        <m-button
          v-if="entry.id !== challengerId"
          type="primary"
          size="small"
          plain
          @click="handleChallenge(entry.id)"
        >
          Challenge
        </m-button>
      </div>
    </div>
    
    <!-- Active Rivalries -->
    <div v-if="rivalries.length > 0" class="rivalries-section">
      <h4 class="section-title">宿敌</h4>
      <div v-for="rivalry in rivalries" :key="rivalry.rival_id" class="rivalry-item">
        <span class="rival-name">{{ rivalry.rival_name }}</span>
        <m-tag :type="getRivalryType(rivalry.level)" size="small">
          {{ getRivalryName(rivalry.level) }}
        </m-tag>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { MButton, MTag } from 'shuimo-ui';

const { t } = useI18n();

const props = defineProps<{
  leaderboard: Array<{
    id: string;
    name: string;
    arena_rating?: number;
    rank?: number;
  }>;
  rivalries: Array<{
    rival_id: string;
    rival_name: string;
    level: number;
  }>;
  challengerId?: string;
}>();

const emit = defineEmits<{
  (e: 'challenge', defenderId: string): void;
}>();

function handleChallenge(defenderId: string) {
  emit('challenge', defenderId);
}

function getRankClass(index: number): string {
  if (index === 0) return 'gold';
  if (index === 1) return 'silver';
  if (index === 2) return 'bronze';
  return 'normal';
}

function getRivalryType(level: number): string {
  if (level >= 4) return 'error';
  if (level >= 3) return 'warning';
  return 'default';
}

function getRivalryName(level: number): string {
  const names = {
    1: 'Cold War',
    2: 'Hostility',
    3: 'Skirmishes',
    4: 'Open Conflict',
    5: 'Total War',
  };
  return names[level as keyof typeof names] || 'Unknown';
}
</script>

<style scoped>
.arena-panel {
  padding: 16px;
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: #2c2417;
  margin-bottom: 16px;
  font-family: "STKaiti", "KaiTi", sans-serif;
}

.empty-state {
  text-align: center;
  padding: 24px;
  color: #6b5d4f;
}

.leaderboard {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.leaderboard-entry {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.4);
  border: 1px solid rgba(139, 119, 90, 0.15);
  border-radius: 6px;
}

.leaderboard-entry.top-3 {
  background: rgba(255, 255, 255, 0.6);
  border-color: rgba(255, 193, 7, 0.3);
}

.rank-badge {
  min-width: 40px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.rank-badge.gold {
  background: linear-gradient(135deg, #ffd700, #ffec80);
  color: #333;
}

.rank-badge.silver {
  background: linear-gradient(135deg, #c0c0c0, #e8e8e8);
  color: #333;
}

.rank-badge.bronze {
  background: linear-gradient(135deg, #cd7f32, #e8a87c);
  color: #fff;
}

.rank-badge.normal {
  background: rgba(139, 119, 90, 0.2);
  color: #6b5d4f;
}

.avatar-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.avatar-name {
  font-weight: 600;
  color: #2c2417;
}

.avatar-rating {
  font-size: 12px;
  color: #6b5d4f;
}

.rivalries-section {
  margin-top: 20px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #6b5d4f;
  margin-bottom: 8px;
}

.rivalry-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: rgba(220, 53, 69, 0.05);
  border-radius: 4px;
  margin-bottom: 4px;
}

.rival-name {
  font-size: 13px;
  color: #2c2417;
}
</style>
