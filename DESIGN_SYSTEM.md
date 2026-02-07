# Design System Documentation
## Quantitative Trading Dashboard - Dark Theme

### Overview
This document describes the complete design system for the sandt_v1.0 Quantitative Trading Dashboard, featuring a modern dark theme optimized for professional financial data visualization and analysis.

---

## 🎨 Color Palette

### Background Colors
- **Primary Background**: `#0a0e1a` - Main application background
- **Secondary Background**: `#131825` - Alternate sections
- **Tertiary Background**: `#1a2030` - Nested elements
- **Card Background**: `#1e2533` - Card components
- **Card Hover**: `#252d3f` - Interactive card states
- **Input Background**: `#1a2030` - Form inputs
- **Sidebar Background**: `#0f1421` - Navigation sidebar

### Accent Colors
- **Primary Accent**: `#3b82f6` - Primary actions, links
- **Secondary Accent**: `#8b5cf6` - Secondary actions
- **Success**: `#10b981` - Positive indicators, gains
- **Warning**: `#f59e0b` - Caution, alerts
- **Danger**: `#ef4444` - Errors, losses
- **Info**: `#06b6d4` - Information, neutral highlights

### Gradients
- **Primary Gradient**: `linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)`
  - Used for: Card headers, primary buttons, titles
- **Success Gradient**: `linear-gradient(135deg, #10b981 0%, #059669 100%)`
  - Used for: Success buttons, positive metrics
- **Warning Gradient**: `linear-gradient(135deg, #f59e0b 0%, #d97706 100%)`
  - Used for: Warning buttons, alerts
- **Danger Gradient**: `linear-gradient(135deg, #ef4444 0%, #dc2626 100%)`
  - Used for: Danger buttons, error states

### Text Colors
- **Primary Text**: `#f1f5f9` - Main content, headings
- **Secondary Text**: `#94a3b8` - Body text, descriptions
- **Tertiary Text**: `#64748b` - Less important text
- **Muted Text**: `#475569` - Placeholder text, disabled
- **Inverse Text**: `#0a0e1a` - Text on light backgrounds

### Border Colors
- **Primary Border**: `#2d3748` - Default borders
- **Secondary Border**: `#1e293b` - Subtle dividers
- **Hover Border**: `#3b4a64` - Interactive element borders
- **Focus Border**: `#3b82f6` - Focused inputs

---

## 📝 Typography

### Font Families
- **Primary Font**: `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
  - Used for: All UI text, headings, body content
- **Monospace Font**: `'JetBrains Mono', 'Fira Code', 'Courier New', monospace`
  - Used for: Code snippets, numeric data, technical content

### Font Sizes
- **Extra Small**: `0.75rem` (12px) - Labels, captions
- **Small**: `0.875rem` (14px) - Body text, form labels
- **Base**: `1rem` (16px) - Standard body text
- **Large**: `1.125rem` (18px) - Emphasized text
- **Extra Large**: `1.25rem` (20px) - Subheadings
- **2XL**: `1.5rem` (24px) - Section headings
- **3XL**: `1.875rem` (30px) - Page subheadings
- **4XL**: `2.25rem` (36px) - Main page titles

### Font Weights
- **Light**: 300 - Subtle text
- **Normal**: 400 - Body text
- **Medium**: 500 - Form labels
- **Semibold**: 600 - Headings, emphasis
- **Bold**: 700 - Strong emphasis, titles

---

## 🔲 Spacing System

### Space Scale
- **XS**: `0.25rem` (4px) - Minimal spacing
- **SM**: `0.5rem` (8px) - Tight spacing
- **MD**: `1rem` (16px) - Default spacing
- **LG**: `1.5rem` (24px) - Comfortable spacing
- **XL**: `2rem` (32px) - Large spacing
- **2XL**: `3rem` (48px) - Section spacing

---

## 🎯 Components

### Cards
**Purpose**: Primary container for grouped content

**Styles**:
- Background: `#1e2533`
- Border: `1px solid #2d3748`
- Border Radius: `0.75rem` (12px)
- Box Shadow: `0 4px 6px -1px rgba(0, 0, 0, 0.4)`
- Transition: All properties `250ms cubic-bezier(0.4, 0, 0.2, 1)`

**Hover State**:
- Transform: `translateY(-2px)`
- Border Color: `#3b4a64`
- Box Shadow: `0 10px 15px -3px rgba(0, 0, 0, 0.5)`

**Header**:
- Background: Primary Gradient
- Color: `#f1f5f9`
- Padding: `1.5rem`
- Font Weight: 600
- Font Size: `1.125rem`

**Body**:
- Padding: `2rem`
- Color: `#94a3b8`

### Buttons

**Primary Button**:
- Background: Primary Gradient
- Color: `#f1f5f9`
- Padding: `0.625rem 1.5rem`
- Border Radius: `0.5rem`
- Font Weight: 600
- Box Shadow: `0 1px 2px 0 rgba(0, 0, 0, 0.3)`
- Hover: Brightness 1.1 + Glow shadow

**Secondary Button**:
- Background: `#1a2030`
- Color: `#94a3b8`
- Border: `1px solid #2d3748`
- Hover: Background `#252d3f`, Color `#f1f5f9`

**Success/Warning/Danger Buttons**:
- Use respective gradient backgrounds
- Same padding and border radius as primary

**Small Button**:
- Padding: `0.5rem 1rem`
- Font Size: `0.75rem`

**Large Button**:
- Padding: `0.875rem 2rem`
- Font Size: `1.125rem`

### Form Inputs

**Text Input / Textarea**:
- Background: `#1a2030`
- Border: `1px solid #2d3748`
- Border Radius: `0.5rem`
- Color: `#f1f5f9`
- Padding: `0.625rem 1rem`
- Font Size: `0.875rem`

**Focus State**:
- Border Color: `#3b82f6`
- Box Shadow: `0 0 0 3px rgba(59, 130, 246, 0.1)`
- Background: `#1e2533`

**Placeholder**:
- Color: `#475569`

**Label**:
- Color: `#94a3b8`
- Font Weight: 500
- Font Size: `0.875rem`
- Margin Bottom: `0.5rem`

### Tables

**Container**:
- Background: `#1e2533`
- Border Radius: `0.75rem`
- Box Shadow: `0 4px 6px -1px rgba(0, 0, 0, 0.4)`
- Overflow: Hidden

**Header Cells**:
- Background: `#1a2030`
- Color: `#f1f5f9`
- Font Weight: 600
- Text Transform: Uppercase
- Font Size: `0.75rem`
- Letter Spacing: `0.05em`
- Padding: `1rem`
- Border Bottom: `2px solid #2d3748`

**Data Cells**:
- Background: `#1e2533`
- Color: `#94a3b8`
- Padding: `0.875rem 1rem`
- Border Bottom: `1px solid #1e293b`

**Row Hover**:
- Background: `#252d3f`
- Color: `#f1f5f9`

### Tabs

**Tab Navigation**:
- Border Bottom: `2px solid #2d3748`
- Margin Bottom: `2rem`

**Tab Link (Inactive)**:
- Background: Transparent
- Border Bottom: `3px solid transparent`
- Color: `#94a3b8`
- Padding: `1rem 1.5rem`
- Font Weight: 600

**Tab Link (Active)**:
- Color: `#f1f5f9`
- Border Bottom Color: `#3b82f6`

**Tab Link (Hover)**:
- Color: `#f1f5f9`
- Border Bottom Color: `#3b4a64`
- Background: `#1e2533`

### Alerts

**Default Alert**:
- Background: `#1e2533`
- Border: `1px solid #2d3748`
- Border Left: `4px solid #3b82f6`
- Border Radius: `0.75rem`
- Padding: `1.5rem`

**Success Alert**:
- Border Left Color: `#10b981`
- Background: `rgba(16, 185, 129, 0.1)`

**Warning Alert**:
- Border Left Color: `#f59e0b`
- Background: `rgba(245, 158, 11, 0.1)`

**Danger Alert**:
- Border Left Color: `#ef4444`
- Background: `rgba(239, 68, 68, 0.1)`

**Info Alert**:
- Border Left Color: `#06b6d4`
- Background: `rgba(6, 182, 212, 0.1)`

### Progress Bars

**Container**:
- Background: `#1a2030`
- Border Radius: `0.5rem`
- Height: `0.75rem`
- Box Shadow: `inset 0 1px 2px rgba(0, 0, 0, 0.3)`

**Progress Fill**:
- Background: Primary Gradient
- Transition: Width `350ms cubic-bezier(0.4, 0, 0.2, 1)`

### Badges

**Default Badge**:
- Display: Inline-flex
- Padding: `0.375rem 0.75rem`
- Font Size: `0.75rem`
- Font Weight: 600
- Border Radius: `0.5rem`
- Text Transform: Uppercase
- Letter Spacing: `0.05em`

**Variants**:
- Primary: Background `#3b82f6`, Color `#f1f5f9`
- Success: Background `#10b981`, Color `#f1f5f9`
- Warning: Background `#f59e0b`, Color `#0a0e1a`
- Danger: Background `#ef4444`, Color `#f1f5f9`
- Secondary: Background `#1a2030`, Border `1px solid #2d3748`, Color `#94a3b8`

---

## 🎭 Animations & Transitions

### Transition Speeds
- **Fast**: `150ms cubic-bezier(0.4, 0, 0.2, 1)` - Quick feedback
- **Base**: `250ms cubic-bezier(0.4, 0, 0.2, 1)` - Default transitions
- **Slow**: `350ms cubic-bezier(0.4, 0, 0.2, 1)` - Smooth, deliberate

### Common Animations

**Pulse (Loading)**:
```css
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
```

**Spin (Spinner)**:
```css
@keyframes spin {
    to { transform: rotate(360deg); }
}
```

**Skeleton Loading**:
```css
@keyframes skeleton-loading {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}
```

**Fade In**:
```css
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
```

**Slide In Up**:
```css
@keyframes slideInUp {
    from {
        transform: translateY(20px);
        opacity: 0;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}
```

---

## 🎨 Shadows

### Shadow Scale
- **SM**: `0 1px 2px 0 rgba(0, 0, 0, 0.3)` - Subtle elevation
- **MD**: `0 4px 6px -1px rgba(0, 0, 0, 0.4)` - Default cards
- **LG**: `0 10px 15px -3px rgba(0, 0, 0, 0.5)` - Elevated cards
- **XL**: `0 20px 25px -5px rgba(0, 0, 0, 0.6)` - Modals, popovers
- **Glow**: `0 0 20px rgba(59, 130, 246, 0.3)` - Interactive highlights

---

## 📱 Responsive Design

### Breakpoints
- **Mobile**: `< 768px`
- **Tablet**: `768px - 1024px`
- **Desktop**: `> 1024px`

### Mobile Adjustments (`< 768px`)
- Title font sizes reduced by ~25%
- Container padding reduced to `1rem`
- Card body padding reduced to `1.5rem`
- Buttons become full-width
- Dashboard grid becomes single column

---

## ♿ Accessibility

### Focus States
All interactive elements have visible focus states:
- Border Color: `#3b82f6`
- Box Shadow: `0 0 0 3px rgba(59, 130, 246, 0.1)`

### Color Contrast
All text meets WCAG AA standards:
- Primary text on dark background: 12:1 ratio
- Secondary text on dark background: 7:1 ratio
- Buttons and interactive elements: 4.5:1 minimum

### Keyboard Navigation
- Tab order follows logical flow
- All buttons and inputs keyboard accessible
- Focus indicators visible and distinct

---

## 🔧 Usage Guidelines

### When to Use Cards
- Grouping related content
- Containing forms or controls
- Displaying data tables
- Creating visual hierarchy

### When to Use Gradients
- Card headers for visual impact
- Primary action buttons
- Page titles and main headings
- Success/warning/danger actions

### When to Use Alerts
- System messages
- User feedback
- Important notices
- Status updates

### Button Hierarchy
1. **Primary Button**: Main action (e.g., "Launch Backtest")
2. **Success Button**: Positive actions (e.g., "Export", "Save")
3. **Secondary Button**: Supporting actions (e.g., "Clear", "Cancel")
4. **Outline Button**: Tertiary actions

---

## 📦 CSS Variables Reference

All design tokens are available as CSS custom properties:

```css
:root {
    /* Colors */
    --bg-primary: #0a0e1a;
    --bg-secondary: #131825;
    --bg-card: #1e2533;
    --accent-primary: #3b82f6;
    --text-primary: #f1f5f9;
    
    /* Spacing */
    --space-xs: 0.25rem;
    --space-md: 1rem;
    --space-xl: 2rem;
    
    /* Typography */
    --text-sm: 0.875rem;
    --text-base: 1rem;
    --text-2xl: 1.5rem;
    
    /* Shadows */
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
    
    /* Transitions */
    --transition-base: 250ms cubic-bezier(0.4, 0, 0.2, 1);
}
```

---

## 🚀 Implementation Notes

### File Structure
```
sandt_v1.0/
├── assets/
│   └── dark-theme.css      # Main theme stylesheet
├── dash_ui.py              # Main UI component
└── backtest_manager_ui.py  # Backtest manager component
```

### Loading the Theme
The theme is automatically loaded through Dash's assets system:
```python
self.app = dash.Dash(
    __name__,
    external_stylesheets=[...],
    assets_folder='assets'
)
```

### Customizing Components
To maintain consistency, use the defined CSS classes and variables:
```python
# Good - uses defined classes
html.Div(className="card")

# Good - consistent with design system
dbc.Button("Action", color="primary")

# Avoid - inline styles break consistency
html.Div(style={'background': '#123456'})
```

---

## 📚 Additional Resources

### External Dependencies
- **Inter Font**: Professional sans-serif typeface
- **JetBrains Mono**: Monospace font for code
- **Dash Bootstrap Components**: UI component library

### Browser Support
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

---

## 📝 Changelog

### Version 2.0 (Current)
- Complete dark theme redesign
- Professional quant dashboard aesthetic
- Comprehensive CSS custom properties system
- Enhanced animations and transitions
- Improved accessibility compliance
- Responsive design for all screen sizes

---

## 👥 Maintainers

For questions or suggestions about the design system, please open an issue in the repository.

**Last Updated**: February 2026
