/**
 * Shuimo Theme Configuration for Naive UI
 * 
 * 水墨风格主题配置 - 使用 Naive UI 组件库而非自定义样式
 * Based on shuimo.design design principles
 */
import type { GlobalThemeOverrides } from 'naive-ui';
import { darkTheme } from 'naive-ui';

/**
 * Shuimo 主题色板
 */
export const shuimoColors = {
  // 主要背景色 - 米色宣纸
  primary: '#8B775A',
  primaryHover: '#9C8B6D',
  primaryPressed: '#6B5D4F',
  primarySuppl: '#A89B8A',
  
  // 文字颜色 - 墨色
  textPrimary: '#2C2417',
  textSecondary: '#6B5D4F',
  textTertiary: '#4A3F35',
  textPlaceholder: '#9B8D7E',
  
  // 背景色
  body: '#F7F3E8',
  card: '#FFFFFF',
  popover: '#FDFBF7',
  modal: '#F7F3E8',
  
  // 边框
  borderColor: 'rgba(139, 119, 90, 0.2)',
  borderColorHover: 'rgba(139, 119, 90, 0.35)',
  dividerColor: 'rgba(139, 119, 90, 0.3)',
  
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
 * Shuimo 字体配置
 */
export const shuimoFonts = {
  body: '"Inter", "STKaiti", "KaiTi", "Microsoft YaHei", -apple-system, sans-serif',
  header: '"STKaiti", "KaiTi", "Microsoft YaHei", sans-serif',
  mono: '"JetBrains Mono", "Fira Code", monospace',
} as const;

/**
 * Naive UI Theme Overrides for Shuimo
 */
export const shuimoThemeOverrides: GlobalThemeOverrides = {
  common: {
    // 主色
    primaryColor: shuimoColors.primary,
    primaryColorHover: shuimoColors.primaryHover,
    primaryColorPressed: shuimoColors.primaryPressed,
    primaryColorSuppl: shuimoColors.primarySuppl,
    
    // 文字颜色
    textColorBase: shuimoColors.textPrimary,
    textColor1: shuimoColors.textPrimary,
    textColor2: shuimoColors.textSecondary,
    textColor3: shuimoColors.textTertiary,
    
    // 背景色
    bodyColor: shuimoColors.body,
    cardColor: shuimoColors.card,
    popoverColor: shuimoColors.popover,
    modalColor: shuimoColors.modal,
    
    // 边框
    borderColor: shuimoColors.borderColor,
    dividerColor: shuimoColors.dividerColor,
    
    // 圆角
    borderRadius: '6px',
    borderRadiusSmall: '4px',
    
    // 阴影
    boxShadow1: '0 2px 8px rgba(44, 36, 23, 0.08)',
    boxShadow2: '0 4px 16px rgba(44, 36, 23, 0.12)',
    boxShadow3: '0 8px 32px rgba(44, 36, 23, 0.16)',
    
    // 字体
    fontFamily: shuimoFonts.body,
    fontFamilyHeader: shuimoFonts.header,
    fontSize: '14px',
    fontSizeTiny: '12px',
    fontSizeSmall: '13px',
    fontSizeMedium: '14px',
    fontSizeLarge: '16px',
    fontSizeHuge: '20px',
    
    // 行高
    lineHeight: '1.6',
    
    // 高度
    heightTiny: '22px',
    heightSmall: '28px',
    heightMedium: '34px',
    heightLarge: '40px',
    heightHuge: '46px',
  },
  
  // Button 组件
  Button: {
    textColor: shuimoColors.textPrimary,
    colorPrimary: shuimoColors.primary,
    colorHoverPrimary: shuimoColors.primaryHover,
    colorPressedPrimary: shuimoColors.primaryPressed,
    borderRadius: '6px',
    borderRadiusSmall: '4px',
    borderRadiusLarge: '8px',
    fontWeightStrong: '600',
    paddingTiny: '4px 12px',
    paddingSmall: '6px 16px',
    paddingMedium: '8px 20px',
    paddingLarge: '12px 24px',
  },
  
  // Card 组件
  Card: {
    borderRadius: '8px',
    borderColor: shuimoColors.borderColor,
    color: shuimoColors.card,
    colorModal: shuimoColors.modal,
    paddingSmall: '16px',
    paddingMedium: '20px',
    paddingLarge: '24px',
  },
  
  // Modal 组件
  Modal: {
    borderRadius: '8px',
    color: shuimoColors.modal,
    boxShadow: '0 8px 32px rgba(44, 36, 23, 0.24)',
    padding: '0',
  },
  
  // Tag 组件
  Tag: {
    borderRadius: '4px',
    heightSmall: '20px',
    heightMedium: '24px',
    padding: '0 8px',
  },
  
  // Divider 组件
  Divider: {
    color: shuimoColors.dividerColor,
  },
  
  // Spin 组件
  Spin: {
    color: shuimoColors.primary,
  },
  
  // Input 组件
  Input: {
    borderRadius: '6px',
    borderColor: shuimoColors.borderColor,
    borderColorHover: shuimoColors.borderColorHover,
    color: shuimoColors.card,
    colorFocus: shuimoColors.card,
  },
  
  // Select 组件
  Select: {
    peers: {
      InternalSelection: {
        borderRadius: '6px',
        borderColor: shuimoColors.borderColor,
        borderColorHover: shuimoColors.borderColorHover,
      },
    },
  },
  
  // Tabs 组件
  Tabs: {
    color: shuimoColors.card,
    tabColor: shuimoColors.card,
  },
};

/**
 * Shuimo Dark Theme (based on darkTheme)
 */
export const shuimoDarkTheme = {
  ...darkTheme,
  overrides: {
    ...shuimoThemeOverrides,
    common: {
      ...shuimoThemeOverrides.common,
      bodyColor: '#1A1814',
      cardColor: '#242119',
      popoverColor: '#2A2520',
      modalColor: '#1A1814',
      textColor1: '#E8E0D0',
      textColor2: '#C8BCA8',
      textColor3: '#A89C88',
    },
  },
};

/**
 * Shuimo preset configuration (recommended defaults)
 */
export const shuimoPreset = {
  theme: null, // Use default theme with overrides
  themeOverrides: shuimoThemeOverrides,
};

/**
 * Helper: Get color from shuimo palette
 */
export function shuimoColor(colorName: keyof typeof shuimoColors): string {
  return shuimoColors[colorName];
}

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
  fonts: shuimoFonts,
  themeOverrides: shuimoThemeOverrides,
  darkTheme: shuimoDarkTheme,
  preset: shuimoPreset,
};
