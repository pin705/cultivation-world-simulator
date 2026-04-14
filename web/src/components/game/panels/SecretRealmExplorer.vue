<template>
  <div class="secret-realm-explorer">
    <h3 class="title">秘境探索</h3>
    
    <div v-if="realms.length === 0" class="empty-state">
      <p>No active secret realms</p>
    </div>
    
    <div v-else class="realms-list">
      <div
        v-for="(realm, index) in realms"
        :key="index"
        class="realm-card"
        :class="{ 'high-danger': realm.danger_level >= 7 }"
      >
        <div class="realm-header">
          <span class="realm-name">{{ realm.name }}</span>
          <m-tag :type="realm.danger_level >= 7 ? 'error' : realm.danger_level >= 4 ? 'warning' : 'info'" size="small">
            Danger: {{ realm.danger_level }}/10
          </m-tag>
        </div>
        
        <div class="realm-details">
          <p>Reward Multiplier: x{{ realm.reward_multiplier.toFixed(1) }}</p>
          <p>Death Risk: {{ (realm.death_risk * 100).toFixed(0) }}%</p>
          <p>Rewards: {{ realm.possible_rewards.join(', ') }}</p>
        </div>
        
        <m-button
          type="primary"
          size="small"
          :disabled="actionPoints < 2"
          @click="handleExplore(index)"
        >
          Explore (2 AP)
        </m-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { MButton, MTag } from 'shuimo-ui';
import type { SecretRealm } from '@/types/core';

const { t } = useI18n();

const props = defineProps<{
  realms: SecretRealm[];
  actionPoints: number;
}>();

const emit = defineEmits<{
  (e: 'explore', realmIndex: number): void;
}>();

function handleExplore(realmIndex: number) {
  emit('explore', realmIndex);
}
</script>

<style scoped>
.secret-realm-explorer {
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

.realms-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.realm-card {
  padding: 12px;
  border: 1px solid rgba(139, 119, 90, 0.2);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.4);
}

.realm-card.high-danger {
  border-color: rgba(220, 53, 69, 0.4);
  background: rgba(220, 53, 69, 0.05);
}

.realm-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.realm-name {
  font-weight: 600;
  color: #2c2417;
}

.realm-details {
  margin-bottom: 12px;
  font-size: 13px;
  color: #4a3f35;
}

.realm-details p {
  margin: 4px 0;
}
</style>
