<script setup lang="ts">
import { useAvatarStore } from '../../stores/avatar'
import AnimatedAvatar from './AnimatedAvatar.vue'
import { computed } from 'vue'
import { calculateVisualOffsets } from './utils/avatarLayout'

const avatarStore = useAvatarStore()
const TILE_SIZE = 64

const emit = defineEmits<{
  (e: 'avatarSelected', payload: { type: 'avatar'; id: string; name?: string }): void
}>()

const visibleAvatars = computed(() => {
  return avatarStore.avatarList.filter(a => !a.is_dead)
})

const avatarOffsets = computed(() => {
  return calculateVisualOffsets(visibleAvatars.value)
})

function handleAvatarSelect(payload: { type: 'avatar'; id: string; name?: string }) {
  emit('avatarSelected', payload)
}
</script>

<template>
  <container sortable-children>
    <AnimatedAvatar
      v-for="avatar in visibleAvatars"
      :key="avatar.id"
      :avatar="avatar"
      :tile-size="TILE_SIZE"
      :offset="avatarOffsets.get(avatar.id)"
      @select="handleAvatarSelect"
    />
  </container>
</template>
