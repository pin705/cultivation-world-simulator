<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useWorldStore } from '@/stores/world'
import { PHENOMENON_RARITY_COLORS, STATUS_BAR_COLORS } from '@/constants/uiColors'

defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
}>()

const { t } = useI18n()
const store = useWorldStore()

function getRarityColor(rarity: string) {
  return PHENOMENON_RARITY_COLORS[rarity] ?? STATUS_BAR_COLORS.neutral
}

function handleShowChange(value: boolean) {
  emit('update:show', value)
}

async function handleSelect(id: number, name: string) {
  try {
    await store.changePhenomenon(id)
    emit('update:show', false)
  } catch (e) {
    console.error('Failed to change phenomenon:', e)
  }
}
</script>

<template>
  <m-dialog :show="show" @update:show="handleShowChange" :title="t('game.status_bar.selector_title')"
    style="width: 700px; max-height: 80vh; overflow-y: auto;">
    <m-list :data="store.phenomenaList" hoverable clickable>
      <template #default="{ item: p }">
        <m-li @click="handleSelect(p.id, p.name)" v-sound:select>
          <div class="list-item-content">
            <div class="item-left">
              <div class="item-name" :style="{ color: getRarityColor(p.rarity) }">
                {{ p.name }}
                <m-tag size="small" :bordered="false"
                  :style="{ color: getRarityColor(p.rarity), background: 'rgba(255,255,255,0.1)' }">
                  {{ p.rarity }}
                </m-tag>
              </div>
              <div class="item-desc">{{ p.desc }}</div>
            </div>
            <div class="item-right">
              <div class="item-effect" v-if="p.effect_desc">{{ p.effect_desc }}</div>
            </div>
          </div>
        </m-li>
      </template>
    </m-list>
    <div v-if="store.phenomenaList.length === 0" class="empty-state">
      {{ t('game.status_bar.empty_data') }}
    </div>
  </m-dialog>
</template>

<style scoped>
.list-item-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 4px 0;
}

.item-name {
  font-weight: bold;
  font-size: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.item-desc {
  color: #aeb4bc;
  font-size: 13px;
}

.item-effect {
  font-size: 12px;
  color: #d8a14a;
  background: rgba(216, 161, 74, 0.12);
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
  margin-top: 4px;
}

.empty-state {
  text-align: center;
  color: #8ea9c8;
  padding: 20px 0;
}
</style>
