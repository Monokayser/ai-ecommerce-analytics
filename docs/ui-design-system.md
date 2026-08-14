# Midnight Analytics UI Design System

## Direction

Version 1.14 translates the supplied dark financial-dashboard reference into a real Streamlit design system. It preserves the reference's near-black canvas, cyan analytical light, rounded pill navigation, compact data density, thin outlined surfaces, and strong visual hierarchy without copying its business content or sacrificing application semantics.

The theme is intentionally neutral rather than green-tinted. Cyan identifies primary actions, selected navigation, focus, live status, and the principal chart series. Green, amber, and red remain semantic colors for positive, caution, and negative states.

## Tokens

| Role | Value | Usage |
|---|---:|---|
| Canvas | `#03070B` | Primary page background |
| Raised canvas | `#070D13` | Sidebar and supporting regions |
| Control | `#081119` | Inputs and compact controls |
| Text | `#F4F8FB` | Headings and primary values |
| Muted text | `#9AABB7` | Supporting copy and metadata |
| Primary cyan | `#70DDFF` | Selection, focus, data, and primary actions |
| Positive | `#72E3BD` | Favorable deltas |
| Warning | `#F2C96D` | Caution and demo-data status |
| Negative | `#FF7D91` | Errors, anomalies, and unfavorable deltas |

The system uses the native system-font stack, avoiding a network font dependency and preserving familiar rendering across Windows, macOS, Android, and iOS.

## Interaction and performance rules

- Controls retain at least 44px touch targets.
- Keyboard focus uses a solid high-contrast cyan outline.
- Hover depth changes only transform, border, background, and shadow; charts never tilt or scale.
- The page has no fixed parallax background, perpetual full-screen animation, or backdrop blur.
- Decorative grid and light fields are static and use no JavaScript.
- `prefers-reduced-motion` and forced-colors modes remain fully supported.
- Mobile removes most decorative layers while preserving hierarchy and contrast.

## Accessibility basis

The implementation targets WCAG 2.2 AA text contrast, visible and unobscured focus, meaningful labels, keyboard access, responsive reflow, and appropriately sized controls. The theme keeps chart labels and values as real text rather than incorporating them into decorative imagery.

References:

- [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/)
- [Understanding contrast minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
- [Understanding focus appearance](https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html)
- [Animations and performance](https://web.dev/articles/animations-and-performance)
- [Reduced-motion media queries](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Media_queries/Using_for_accessibility)
