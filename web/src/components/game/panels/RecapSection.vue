<template>
  <div class="recap-section">
    <header class="section-header">
      <span class="section-icon">{{ icon }}</span>
      <h3 class="section-title">{{ title }}</h3>
      <slot name="subtitle"></slot>
    </header>
    
    <div class="section-content">
      <slot></slot>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  icon: string;
}>();
</script>

<style scoped>
.recap-section {
  margin-bottom: 24px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.4);
  border: 1px solid rgba(139, 119, 90, 0.15);
  border-radius: 6px;
  transition: all 0.3s ease;
}

.recap-section:hover {
  background: rgba(255, 255, 255, 0.6);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid rgba(139, 119, 90, 0.2);
}

.section-icon {
  font-size: 22px;
  filter: grayscale(0.2);
}

.section-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #2c2417;
  letter-spacing: 1px;
  font-family: "STKaiti", "KaiTi", "Microsoft YaHei", sans-serif;
}

.section-header :slotted(.section-subtitle) {
  margin-left: 8px;
  font-size: 13px;
  color: #6b5d4f;
  font-style: italic;
}

.section-content {
  padding: 4px 0;
}
</style>
