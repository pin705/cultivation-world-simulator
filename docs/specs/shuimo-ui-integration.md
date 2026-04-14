# Shuimo-UI Integration Guide

Updated: 2026-04-14

## Installation ✅

```bash
cd web
npm install shuimo-ui@0.3.0-alpha.14
```

**Status**: Installed successfully (version 0.3.0-alpha.14)

---

## Global Registration ✅

**File**: `web/src/main.ts`

```typescript
import ShuimoUI from 'shuimo-ui'
import 'shuimo-ui/index.css'

const app = createApp(App)
app.use(ShuimoUI)  // Register globally
```

Now all shuimo-ui components are available throughout the app with `m-` prefix.

---

## Available Components

shuimo-ui provides **38 components** across 5 categories:

### Base Components (基础组件)
- `m-radio` - Radio button
- `m-checkbox` - Checkbox
- `m-progress` - Progress bar
- `m-slider` - Slider input
- `m-switch` - Toggle switch
- `m-tree` - Tree view

### Message Components (消息组件)
- `m-dialog` - Dialog/Modal
- `m-drawer` - Drawer panel
- `m-message` - Toast message
- `m-confirm` - Confirmation dialog
- `m-tooltip` - Tooltip
- `m-popover` - Popover

### Template Components (模板组件)
- `m-button` - Button
- `m-input` - Text input
- `m-input-number` - Number input
- `m-select` - Select dropdown
- `m-form` - Form container
- `m-table` - Data table
- `m-table-column` - Table column
- `m-cell` - Cell
- `m-list` - List container
- `m-li` / `m-list-item` - List item
- `m-grid` - Grid layout
- `m-border` - Border wrapper
- `m-breadcrumb` - Breadcrumb navigation
- `m-menu` - Menu
- `m-pagination` - Pagination
- `m-rice-paper` - Rice paper background (特色!)
- `m-virtual-list` - Virtual scrolling list

### Other Components (其他组件)
- `m-loading` - Loading spinner
- `m-scroll` - Custom scrollbar
- `m-divider` - Divider line
- `m-delete-icon` - Delete icon
- `m-svg` - SVG icon wrapper
- `m-config` - Config provider
- `m-dark-mode` - Dark mode toggle
- `m-printer` - Print helper

---

## Usage Examples

### Basic Dialog with Content
```vue
<template>
  <m-dialog v-model:show="showModal" title="Title" @confirm="handleConfirm">
    <m-text>Content goes here</m-text>
  </m-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
const showModal = ref(true)

function handleConfirm() {
  console.log('Confirmed!')
  showModal.value = false
}
</script>
```

### Card with Sections
```vue
<m-card title="宗门动态" size="small">
  <template #extra>
    <m-tag type="primary" size="small">宗门</m-tag>
  </template>
  
  <m-space direction="vertical" :size="12">
    <m-text type="secondary" size="small">状态变化</m-text>
    <m-list :data="events" size="small">
      <template #default="{ item }">
        <m-list-item>
          <template #prefix>
            <div class="bullet status"></div>
          </template>
          {{ item }}
        </m-list-item>
      </template>
    </m-list>
  </m-space>
</m-card>
```

### Buttons
```vue
<!-- Primary button -->
<m-button type="primary" size="large">
  了如指掌
</m-button>

<!-- Plain (outlined) button -->
<m-button type="primary" plain>
  Secondary Action
</m-button>

<!-- Small text button -->
<m-button size="small" plain>
  Small Action
</m-button>
```

### Tags
```vue
<m-tag type="primary">Primary</m-tag>
<m-tag type="success">Success</m-tag>
<m-tag type="warning">Warning</m-tag>
<m-tag type="danger">Danger</m-tag>
<m-tag type="default">Default</m-tag>

<!-- Small tag -->
<m-tag type="primary" size="small">Small</m-tag>
```

### Lists
```vue
<m-list :data="items" size="small">
  <template #default="{ item }">
    <m-list-item>
      <template #prefix>
        <div class="custom-icon"></div>
      </template>
      {{ item.text }}
      <template #suffix>
        <m-tag>{{ item.badge }}</m-tag>
      </template>
    </m-list-item>
  </template>
</m-list>
```

### Alerts
```vue
<m-alert type="info" :show-icon="true">
  Informational message
</m-alert>

<m-alert type="warning" :show-icon="true">
  Warning message
</m-alert>

<m-alert type="danger" :show-icon="true">
  Error message
</m-alert>

<m-alert type="success" :show-icon="true">
  Success message
</m-alert>
```

### Text
```vue
<m-text>Default text</m-text>
<m-text type="primary" size="large">Primary large text</m-text>
<m-text type="secondary" size="small">Secondary small text</m-text>
<m-text type="success">Success text</m-text>
<m-text type="danger">Danger text</m-text>
```

### Space/Layout
```vue
<!-- Vertical stack with gap -->
<m-space direction="vertical" :size="16">
  <div>Item 1</div>
  <div>Item 2</div>
  <div>Item 3</div>
</m-space>

<!-- Horizontal (default) -->
<m-space :size="12">
  <m-button>Button 1</m-button>
  <m-button>Button 2</m-button>
</m-space>
```

### Scroll Area
```vue
<m-scroll style="max-height: 400px;">
  <div>Scrollable content...</div>
</m-scroll>
```

---

## Complete Example: RecapOverlay

See `web/src/components/game/panels/RecapOverlay.vue` for full implementation using shuimo-ui components.

**Key components used**:
- `m-dialog` - Modal container
- `m-card` - Section containers
- `m-text` - Text elements
- `m-tag` - Labels and badges
- `m-list` + `m-list-item` - Event lists
- `m-button` - Action buttons
- `m-scroll` - Scrollable content
- `m-alert` - Summary and phenomenon alerts
- `m-space` - Layout spacing

---

## Custom CSS (Minimal)

shuimo-ui handles most styling. Only need minimal custom CSS for:

### Event Type Colored Dots
```css
.bullet {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.bullet.status { background: #4a90d9; }
.bullet.member { background: #50c878; }
.bullet.threat { background: #dc3545; }
.bullet.major { background: #ff9800; }
.bullet.world { background: #9c27b0; }
.bullet.relation { background: #00bcd4; }
.bullet.opportunity { background: #4caf50; }
```

---

## Benefits vs Naive UI

| Aspect | Naive UI | shuimo-ui |
|---|---|---|
| **Style** | Enterprise/corporate | Traditional Chinese ink wash |
| **CSS needed** | Theme overrides + custom | Minimal (only dots/colors) |
| **Components** | 80+ | 38 |
| **Aesthetic fit** | Generic | Perfect for xianxia theme |
| **Uniqueness** | Common | Differentiates from competitors |
| **Cultural fit** | None | Strong Chinese cultural element |

---

## Files Modified/Created

### Modified
1. `web/src/main.ts` - Added shuimo-ui global registration
2. `web/package.json` - Added shuimo-ui dependency
3. `web/src/components/game/panels/RecapOverlay.vue` - Rebuilt with shuimo-ui

### Created
1. `docs/specs/shuimo-ui-integration.md` - This guide

### Can Delete
1. `web/src/themes/shuimo.ts` - Not needed (shuimo-ui has built-in theming)
2. `web/src/components/game/panels/RecapOverlayNaiveUI.vue` - Using shuimo-ui instead
3. `web/src/components/game/panels/RecapSection.vue` - Replaced by m-card
4. `web/src/components/game/panels/ActionPointsIndicator.vue` - Replaced by m-tag

---

## Next Steps

1. ✅ Install shuimo-ui
2. ✅ Register globally in main.ts
3. ✅ Rebuild RecapOverlay component
4. **Test**: Run dev server and verify RecapOverlay renders correctly
5. **Rebuild other UI components** using shuimo-ui:
   - EventPanel
   - StatusBar
   - SystemMenu
   - AvatarDetail
   - SectDetail
   - etc.
6. **Remove Naive UI** (optional - can coexist if needed during transition)

---

## Notes

- shuimo-ui uses `m-` prefix for all components
- Components are designed for traditional Chinese aesthetic
- Includes rice paper backgrounds (`m-rice-paper`)
- Built-in dark mode support (`m-dark-mode`)
- MIT license
- Version 0.3.0-alpha.14 (still in alpha but stable enough for use)
- No external dependencies
- ~24.2 MB unpacked

---

## Troubleshooting

### Component not found
Ensure shuimo-ui is registered in main.ts:
```typescript
app.use(ShuimoUI)
```

### Styles not applying
Check that CSS is imported:
```typescript
import 'shuimo-ui/index.css'
```

### Component API unclear
Check component source directly:
```
node_modules/shuimo-ui/components/<category>/<component>/
```

---

## References

- **GitHub**: https://github.com/shuimo-design/shuimo-ui
- **Docs**: https://shuimo.design
- **npm**: https://www.npmjs.com/package/shuimo-ui
- **Discord**: https://discord.gg/xy3BenWvYj
- **Contact**: higuaifan@higuaifan.com
