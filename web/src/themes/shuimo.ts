/**
 * Shuimo Design System - Color Palette & Utilities
 * 
 * 水墨风格色板 - 用于 event colors 等自定义颜色
 * Note: shuimo-ui handles all component styling, this is just for custom elements
 */

/**
 * Shuimo 色板 - Event colors và functional colors
 */
export const shuimoColors = {
  // 事件类型颜色
  status: '#4A90D9',      // 状态变化 - 蓝
  member: '#50C878',      // 成员事件 - 绿
  threat: '#DC3545',      // 威胁 - 红
  major: '#FF9800',       // 重要 - 橙
  world: '#9C27B0',       // 世界 - 紫
  relation: '#00BCD4',    // 关系 - 青
  opportunity: '#4CAF50', // 机会 - 绿

  // 功能色
  success: '#50C878',
  warning: '#FF9800',
  error: '#DC3545',
  info: '#4A90D9',
} as const;

/**
 * Helper: Get CSS variable name for shuimo color
 */
export function shuimoCSSVar(colorName: keyof typeof shuimoColors): string {
  return `var(--shuimo-${colorName})`;
}

/**
 * Export all shuimo utilities
 */
export const ShuimoDesignSystem = {
  colors: shuimoColors,
};
