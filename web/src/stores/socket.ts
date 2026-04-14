import { defineStore } from 'pinia';
import { ref } from 'vue';
import { gameSocket } from '../api/socket';
import { useWorldStore } from './world';
import { useUiStore } from './ui';
import { useSystemStore } from './system';
import { routeSocketMessage } from './socketMessageRouter';

export const useSocketStore = defineStore('socket', () => {
  const isConnected = ref(false);
  const lastError = ref<string | null>(null);
  
  let cleanupMessage: (() => void) | undefined;
  let cleanupStatus: (() => void) | undefined;

  function init(roomId = 'main') {
    if (cleanupStatus) return; // Already initialized

    const worldStore = useWorldStore();
    const uiStore = useUiStore();
    const systemStore = useSystemStore();

    // Listen for status
    cleanupStatus = gameSocket.onStatusChange((connected) => {
      isConnected.value = connected;
      if (connected) {
        lastError.value = null;
      }
    });

    cleanupMessage = gameSocket.on((data) => {
      routeSocketMessage(data, { worldStore, uiStore, systemStore });
    });

    // Connect socket
    gameSocket.connect(roomId);
  }

  function switchRoom(roomId: string) {
    if (!cleanupStatus) {
      init(roomId);
      return;
    }
    gameSocket.switchRoom(roomId);
  }

  function disconnect() {
    if (cleanupMessage) cleanupMessage();
    if (cleanupStatus) cleanupStatus();
    cleanupMessage = undefined;
    cleanupStatus = undefined;
    gameSocket.disconnect();
    isConnected.value = false;
  }

  return {
    isConnected,
    lastError,
    init,
    switchRoom,
    disconnect
  };
});
