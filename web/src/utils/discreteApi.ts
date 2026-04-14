import { MMessage, MConfirm } from 'shuimo-ui'

// Wrapper to provide naive-ui createDiscreteApi-compatible interface using shuimo-ui components
const message = MMessage

const notification = {
  success: (content: string) => MMessage.success(content),
  error: (content: string) => MMessage.error(content),
  warning: (content: string) => MMessage.warning(content),
  info: (content: string) => MMessage.info(content),
}

const dialog = MConfirm

// Simple loadingBar wrapper (shuimo-ui may not have loadingBar, provide a no-op fallback)
const loadingBar = {
  start: () => { },
  finish: () => { },
  error: () => { },
}

export { message, notification, dialog, loadingBar }
