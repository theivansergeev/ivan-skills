# Example 2: New Feature with Hidden Regression

## The Task

"Add dark mode to the settings page."

## Without Вайбкодинг

The AI agent:
1. Added a theme toggle component
2. Created CSS variables for dark/light themes
3. Updated the settings page layout
4. Modified the global `ThemeProvider` to support the new toggle
5. Tested dark mode — looks great!
6. Shipped it

**Two days later:**
- Users report that the dashboard charts are invisible in dark mode (white lines on white background)
- The mobile navigation menu doesn't respond to theme changes
- Performance regression: `ThemeProvider` now re-renders every child on every toggle

## With Вайбкодинг

**Stage 1 — Research:** Agent maps all theme consumers: settings page, dashboard charts (uses hardcoded colors), navigation (uses separate CSS), profile page. Identifies that charts library uses inline styles, not CSS variables.

**Stage 3 — Planning + Challenge Loop:**
- "Does the plan cover all theme consumers?" — No, charts and nav are missing. Plan updated.
- "What's the most efficient solution?" — CSS variables for most components, but charts need a config override. Agent researches the chart library docs.

**Stage 4 — Implementation (Phase 1):** Theme toggle + CSS variables + chart config.

**Stage 7 — Impact Analysis:**
- "What re-renders when theme changes?" — Found: `ThemeProvider` wraps entire app. Solution: memoize theme value, only settings page re-renders.
- "What about mobile nav?" — Found: uses separate stylesheet. Added CSS variable fallback.

**Result:**
- Dark mode works everywhere including charts ✅
- No performance regression ✅
- Mobile navigation themed correctly ✅

## The Lesson

Research found the chart library problem before any code was written. Impact Analysis caught the re-render performance issue. Both would have been production bugs without Вайбкодинг.
