---
name: Lumina Glass
colors:
  surface: '#fcf8ff'
  surface-dim: '#dad8ef'
  surface-bright: '#fcf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f2ff'
  surface-container: '#efecff'
  surface-container-high: '#e8e6fe'
  surface-container-highest: '#e2e0f8'
  on-surface: '#1a1a2b'
  on-surface-variant: '#464555'
  inverse-surface: '#2f2f41'
  inverse-on-surface: '#f2efff'
  outline: '#777587'
  outline-variant: '#c7c4d8'
  surface-tint: '#4f44e2'
  primary: '#4d41df'
  on-primary: '#ffffff'
  primary-container: '#675df9'
  on-primary-container: '#fffbff'
  inverse-primary: '#c4c0ff'
  secondary: '#ac2a5d'
  on-secondary: '#ffffff'
  secondary-container: '#ff6b9d'
  on-secondary-container: '#6e0034'
  tertiary: '#006762'
  on-tertiary: '#ffffff'
  tertiary-container: '#00837c'
  on-tertiary-container: '#f3fffd'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e3dfff'
  primary-fixed-dim: '#c4c0ff'
  on-primary-fixed: '#100069'
  on-primary-fixed-variant: '#3622ca'
  secondary-fixed: '#ffd9e1'
  secondary-fixed-dim: '#ffb1c5'
  on-secondary-fixed: '#3f001b'
  on-secondary-fixed-variant: '#8c0a46'
  tertiary-fixed: '#7cf6ec'
  tertiary-fixed-dim: '#5dd9d0'
  on-tertiary-fixed: '#00201e'
  on-tertiary-fixed-variant: '#00504c'
  background: '#fcf8ff'
  on-background: '#1a1a2b'
  surface-variant: '#e2e0f8'
typography:
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 8px
  sm: 16px
  md: 24px
  lg: 48px
  xl: 80px
  container-max: 1280px
  gutter: 24px
---

## Brand & Style
The brand personality is futuristic yet approachable, designed to transform the mundane task of attendance into a high-end digital experience. It targets modern educational institutions and forward-thinking corporate offices. The emotional response is one of clarity, lightness, and technical sophistication.

The design style is a refined **Glassmorphism**. It utilizes multi-layered translucency to create a sense of depth and hierarchy without the weight of heavy shadows. By combining frosted glass effects with a soft, pastel color palette, the UI feels airy and breathable, reducing cognitive load for users managing large sets of data.

## Colors
The palette is built on a foundation of soft pastels that maintain high legibility. 
- **Primary & Secondary:** A vibrant gradient pairing used for calls-to-action and active status indicators.
- **Background:** A soft lavender base that supports the glass overlays.
- **Glass Elements:** Uses a specific alpha-transparent white with backdrop-blur to ensure content remains readable over dynamic backgrounds.
- **Functional Colors:** Mint Green is used for successful attendance logs, while Light Salmon indicates warnings or late entries.

## Typography
The system uses **Plus Jakarta Sans** (as a high-quality alternative to Poppins) for headlines to provide a modern, geometric, and friendly character. **Inter** is utilized for all body text and data-heavy labels to ensure maximum legibility at small sizes and high-density attendance tables.

For mobile devices, `display-lg` should scale down to 36px, and `headline-lg` should scale to 28px to maintain visual balance on smaller viewports.

## Layout & Spacing
The layout follows a **Fluid Grid** model with a maximum container width for desktop viewing.
- **Desktop:** 12-column grid with 24px gutters and 48px side margins.
- **Tablet:** 8-column grid with 20px gutters and 32px side margins.
- **Mobile:** 4-column grid with 16px gutters and 16px side margins.

Content is organized into "Glass Modules." Spacing between modules should be consistent (24px) to allow the background gradient to peek through, reinforcing the translucent aesthetic.

## Elevation & Depth
Depth is created through optical layering rather than traditional black shadows.
- **Surface Level 0:** The base linear gradient background.
- **Surface Level 1 (Glass Cards):** 20px backdrop-blur, `rgba(255, 255, 255, 0.15)` fill, and a 1px solid white border at 30% opacity.
- **Surface Level 2 (Floating Elements/Popovers):** Higher blur (30px) and a subtle outer glow using the primary color at 10% opacity (`#6C63FF1A`) to indicate active focus.
- **Interaction:** Hovering over glass elements increases the background opacity slightly to 25% to provide tactile feedback.

## Shapes
The shape language is consistently soft and organic. All major components, including cards, modal containers, and large input fields, use a **20px (1.25rem)** corner radius. Smaller elements like buttons and chips follow a standard **rounded-lg** (1rem) or **pill** (full radius) convention to distinguish them from structural layout containers.

## Components
- **Buttons:** 
    - *Primary:* A linear gradient (135deg) from `#6C63FF` to `#FF6B9D`. White text, bold weight.
    - *Secondary:* Glass effect background with a 2px border using `#6C63FF`.
- **Inputs:** Glass containers with a 20px radius. On focus, the border transitions from 30% white to a solid `#6C63FF` with a 8px outer glow.
- **Cards:** The central container for attendance data. Must include the standard glass effect and 20px radius. Headers within cards should be separated by a subtle 1px white-transparent line.
- **Navigation:** A fixed glass sidebar or top bar with a 20px backdrop blur. Active links are indicated by a soft purple glow behind the icon and a primary color text change.
- **Attendance Chips:** Small, pill-shaped indicators for "Present" (Mint), "Absent" (Salmon), or "Excused" (Soft Blue), utilizing 20% opacity fills of their respective colors for a "tinted glass" look.