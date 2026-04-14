# Rebuild UI with Shuimo Design + Naive UI Components

Updated: 2026-04-14

## Strategy: Naive UI + Shuimo Theme (Not Custom CSS)

### Problem
- shuimo.design/en documentation is inaccessible (empty responses)
- @shuimo-design/shuimo-ui exists but unclear component API
- Custom CSS is hard to maintain and inconsistent

### Solution
The project already uses **Naive UI** (enterprise-grade Vue 3 component library).

**Approach**: Use Naive UI components + Shuimo theme overrides instead of custom styles.

---

## Implementation Plan

### Phase 1: Theme Configuration ✅
**File**: `web/src/themes/shuimo.ts`

Created complete Shuimo theme configuration for Naive UI:
- Color palette (米色宣纸, 墨色文字, event colors)
- Font configuration (楷体 for headers)
- Border radius, shadows, spacing
- Theme overrides for all major Naive UI components
- Dark theme support

**Key exports**:
```typescript
import { shuimoThemeOverrides, shuimoColors, shuimoFonts } from '@/themes/shuimo';
```

### Phase 2: RecapOverlay with Naive UI ✅
**File**: `web/src/components/game/panels/RecapOverlayNaiveUI.vue`

Rebuilt RecapOverlay using only Naive UI components:
- `NModal` - Overlay container
- `NCard` - Section containers
- `NText` - Text elements
- `NTag` - Labels and badges
- `NList` + `NListItem` - Event lists
- `NBadge` - Color dots for event types
- `NButton` - Action buttons
- `NScrollbar` - Scrollable content
- `NAlert` - Summary and phenomenon alerts
- `NDescriptions` - Key-value displays
- `NSpace` - Layout spacing
- `NIcon` - Icons (using project's Lucide SVGs)

**Benefits**:
- ✅ Zero custom layout CSS
- ✅ Consistent with rest of app
- ✅ Accessible by default
- ✅ Responsive out of the box
- ✅ Proper keyboard navigation
- ✅ Screen reader friendly

### Phase 3: Replace Custom Components
**Files to rebuild**:
1. `RecapSection.vue` - Replace with `NCard`
2. `ActionPointsIndicator.vue` - Replace with `NTag` + `NBadge`
3. Future components - Always use Naive UI first

### Phase 4: Apply Theme Globally
**File**: `web/src/App.vue`

Add theme provider:
```vue
<NConfigProvider :theme-overrides="shuimoThemeOverrides">
  <!-- App content -->
</NConfigProvider>
```

---

## Naive UI Component Mapping

| Custom Element | Naive UI Component | Notes |
|---|---|---|
| Modal/Overlay | `NModal` | Use `preset="card"` for card-style |
| Card/Section | `NCard` | Use `size="small"`, `:bordered="false"` |
| Text | `NText` | Use `depth` prop for color variants |
| Button | `NButton` | Use `type="primary"`, `quaternary` for text buttons |
| Tag/Label | `NTag` | Use `type` for color (info, success, warning, error) |
| List | `NList` + `NListItem` | Use `hoverable`, `clickable` props |
| Badge/Dot | `NBadge` | Use `dot` prop for colored dots |
| Icon | `NIcon` | Wrap SVG or use icon components |
| Scrollbar | `NScrollbar` | Set `maxHeight` for scrollable areas |
| Alert/Notice | `NAlert` | Use `type` and `show-icon` props |
| Divider | `NDivider` | Automatic theming |
| Space/Gap | `NSpace` | Use `vertical` or `horizontal` with `size` |
| Description List | `NDescriptions` | Use for key-value pairs |
| Loading | `NSpin` | Use `:loading` prop on buttons |
| Input | `NInput` | Automatic theme styling |
| Select | `NSelect` | Automatic theme styling |
| Tabs | `NTabs` + `NTabPane` | Automatic theme styling |

---

## Shuimo Theme Colors

```typescript
// Backgrounds
body: '#F7F3E8'        // 米色宣纸
card: '#FFFFFF'         // White cards
popover: '#FDFBF7'      // Light popover

// Text (墨色)
textPrimary: '#2C2417'   // Dark ink
textSecondary: '#6B5D4F' // Medium brown
textTertiary: '#4A3F35'  // Light brown

// Event colors (Shuimo palette)
status: '#4A90D9'        // Blue - status changes
member: '#50C878'        // Green - member events
threat: '#DC3545'        // Red - threats
major: '#FF9800'         // Orange - major events
world: '#9C27B0'         // Purple - world events
relation: '#00BCD4'      // Cyan - relations
opportunity: '#4CAF50'   // Green - opportunities
```

---

## Usage Examples

### Basic Card Section
```vue
<NCard title="宗门动态" size="small" :bordered="false">
  <template #header-extra>
    <NIcon size="18"><BankOutlined /></NIcon>
  </template>
  
  <NList hoverable>
    <NListItem v-for="event in events" :key="event.id">
      <template #prefix>
        <NBadge :color="shuimoColors.status" dot />
      </template>
      {{ event.content }}
    </NListItem>
  </NList>
</NCard>
```

### Modal/Overlay
```vue
<NModal
  v-model:show="showModal"
  preset="card"
  :style="{ maxWidth: '800px' }"
  :bordered="false"
  size="huge"
>
  <template #header>
    <div class="header">
      <NIcon><ScrollOutlined /></NIcon>
      <span>天机推演</span>
    </div>
  </template>
  
  <!-- Content -->
  
  <template #footer>
    <NButton type="primary" @click="handleConfirm">
      了如指掌
    </NButton>
  </template>
</NModal>
```

### Action Points Indicator
```vue
<NTag type="success" size="medium">
  天命点数: <strong>{{ remaining }}</strong> / {{ total }}
</NTag>
```

---

## Files Created

1. **`web/src/themes/shuimo.ts`** - Complete Shuimo theme configuration
2. **`web/src/components/game/panels/RecapOverlayNaiveUI.vue`** - Rebuilt with Naive UI

## Files to Modify

1. **`web/src/App.vue`** - Add `NConfigProvider` with Shuimo theme
2. **`web/src/components/game/panels/RecapOverlay.vue`** - Replace with NaiveUI version

## Files to Delete

1. **`web/src/components/game/panels/RecapSection.vue`** - Use `NCard` instead
2. **`web/src/components/game/panels/ActionPointsIndicator.vue`** - Use `NTag` + `NBadge`

---

## Next Steps

1. **Install icon library** (if needed)
   ```bash
   npm install @vicons/antd
   # OR use existing Lucide SVGs
   ```

2. **Wrap app with theme provider**
   ```vue
   <NConfigProvider :theme-overrides="shuimoThemeOverrides">
     <NDialogProvider>
       <NMessageProvider>
         <!-- App content -->
       </NMessageProvider>
     </NDialogProvider>
   </NConfigProvider>
   ```

3. **Replace all custom components**
   - Go through each custom component
   - Replace with Naive UI equivalent
   - Remove custom CSS
   - Only keep minimal overrides

4. **Test and refine**
   - Check all components render correctly
   - Verify theme colors apply properly
   - Test responsive design
   - Check accessibility

---

## Benefits

✅ **Maintainable**: Uses industry-standard component library
✅ **Consistent**: All components share same theme
✅ **Accessible**: Naive UI has built-in a11y
✅ **Performant**: Optimized components, no custom CSS overhead
✅ **Type-safe**: Full TypeScript support
✅ **Professional**: Enterprise-grade components
✅ **Themed**: Shuimo aesthetic without custom hacks

---

## Comparison: Custom vs Naive UI

| Aspect | Custom CSS | Naive UI + Shuimo Theme |
|---|---|---|
| Lines of CSS | ~400 | ~50 (overrides only) |
| Accessibility | Manual | Automatic |
| Responsive | Custom media queries | Built-in |
| Keyboard nav | Manual | Built-in |
| Screen reader | Manual ARIA | Built-in |
| Dark mode | Duplicate CSS | Simple theme switch |
| Maintenance | High | Low |
| Consistency | Manual checks | Guaranteed |

---

## Conclusion

**Recommendation**: Use Naive UI + Shuimo theme for all UI.

This approach:
- Leverages existing dependency (naive-ui already installed)
- Avoids unclear shuimo-ui library documentation
- Provides professional, maintainable UI
- Keeps Shuimo aesthetic through theme overrides
- Significantly reduces custom CSS

**Estimated effort**: 2-3 hours to rebuild all current recap UI with Naive UI components.
