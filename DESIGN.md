---
name: Thasonyah Clinic
description: Calm Thai clinic workspace in indigo and cream
colors:
  primary: "#2C398D"
  primary-hover: "#202C70"
  ink: "#28324A"
  muted: "#626A7B"
  paper: "#F5F2EC"
  surface: "#FFFFFF"
  soft: "#E9EDF5"
  line: "#DFE2E9"
  sand: "#A48D69"
  warning-ink: "#805A20"
  warning-bg: "#FBF0D8"
  active-ink: "#295C40"
  active-bg: "#E7F0E9"
  danger-ink: "#A14238"
  danger-bg: "#FBEDE9"
  neutral-ink: "#55645C"
  neutral-bg: "#F0F2EF"
  field-border: "#BAC2D3"
typography:
  headline:
    fontFamily: 'Thonburi, "Noto Sans Thai", Tahoma, sans-serif'
    fontSize: "28px"
    fontWeight: 600
    lineHeight: 1.5
  title:
    fontSize: "19px"
    fontWeight: 600
    lineHeight: 1.65
  body:
    fontFamily: 'Thonburi, "Noto Sans Thai", Tahoma, sans-serif'
    fontSize: "15px"
    lineHeight: 1.65
  field:
    fontSize: "13px"
    lineHeight: 1.65
  badge:
    fontSize: "12px"
    lineHeight: 1.65
rounded:
  chip: "6px"
  control: "8px"
  panel: "14px"
  circle: "50%"
spacing:
  compact: "8px"
  small: "12px"
  medium: "16px"
  panel: "24px"
  large: "32px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    padding: "10px 18px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "10px 18px"
  panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.panel}"
---

# Design System: Thasonyah Clinic

## Overview

**Creative North Star: "ห้องทำงานคลินิกที่สงบและชัดเจน"**

The existing direction uses the clinic's indigo logo against cream and muted blue surfaces. The visual language is calm, compact, and operational, with restrained sand details and Thai sans-serif text. This records the implemented prototype, with visual identity still awaiting user review.

The user explicitly named https://www.facebook.com/thasonyahclinic as the brand reference. The recorded browser observation on 2026-09-11 found an indigo logo and cream, slate-blue, and sand cover imagery. The matching local asset is `frontend/public/brand/thasonyah-logo.jpg`. UI HEX values are interpretations of that evidence, not official brand specifications. Facebook's own blue interface is not the source.

**Key Characteristics:**
- Indigo actions and selected navigation on cream and white surfaces.
- Flat, bordered panels with compact Thai text.
- Visible status labels, identity, and keyboard focus.

## Colors

### Primary
Indigo identifies the primary action, selected navigation, headings in contextual areas, and an emphasized care panel. The darker variant is the primary button hover state.

### Secondary
Sand is a restrained decorative accent and a palette sample; it is not the ordinary body-text color. Muted blue provides a quiet selected or supporting surface.

### Neutral
Paper forms the workspace background; white forms the sidebar, header, panels, and fields. Ink and muted text establish hierarchy; line separates panels and rows. Clinical fields use the stronger field-border token.

### Status
Warning pairs amber text and pale amber backgrounds; active pairs green text and pale green backgrounds; danger pairs red text and pale red backgrounds. Neutral status has a muted green-gray pairing. Green is a semantic status color, not the primary brand.

## Typography

**Display Font / Body Font:** Thonburi, then Noto Sans Thai, Tahoma, sans-serif. No separate display face is implemented.

The base font is 15px with line-height 1.65, but this is not a universal body size. Actual component text commonly uses 10–15px; the sidebar's English decorative signature is 9px. Small text remains a non-blocking observation in the existing finish review and needs real-device evaluation.

### Hierarchy
- Page heading: 28px/1.5, weight 600; 25px at widths ≤1250px, 23px at ≤760px.
- Section heading: 19px, weight 600; contextual and record subheadings use 16px. The indigo care-panel heading is 23px/1.65, weight 500.
- Summary numerals: 32px, weight 500; 28px at ≤760px. The palette specimen is also 32px.
- Body base: 15px/1.65; explanatory paragraphs commonly 12px or 14px. Fields and navigation are 13px on desktop; mobile navigation is 12px.
- Current cascade: table content and person names are 13px; person IDs, table secondary text, and status badges are 12px. The record's more-specific name rule remains 15px.
- Table headings and booking metadata are 11px; mobile header metadata and footer are 10px. The demo strip is 12px desktop and 11px mobile after the final override.
- Final brand overrides apply at every breakpoint: clinic name 22px/1.2, subtitle 10px; older media-rule sizes are superseded.

## Layout

The desktop shell is a flex layout with a sticky 240px sidebar of viewport height. The topbar is 76px tall. Main content is centered with max-width 1600px and padding 34px 36px 48px. Repeated spacing values are captured above; this is not an exclusive spacing scale: existing rules also use values such as 10, 18, 20, 22, 25, 26, 28, 30, and 36px.

At ≤1250px the sidebar becomes 210px, content padding becomes 28px 24px, and the heading reduces. At ≤760px the sidebar becomes a static full-width header; navigation scrolls horizontally, sidebar secondary material is hidden, the topbar becomes 52px, and content padding becomes 24px 18px. The logo remains 52px square because its final scoped rule overrides earlier mobile sizing.

Panels generally use 24px spacing and padding. Exact route grids, table transformation, and task composition are recorded in the surface brief. Horizontal overflow is local to the calendar; appointment rows become stacked cards on mobile.

## Elevation & Depth

No box shadows are defined in this prototype stylesheet. White panels, cream ground, indigo emphasis, and thin borders provide depth. Focus uses an indigo 2px outline with a 4px offset; it is not elevation.

## Shapes

Panels and swatches use the panel radius; buttons and fields use the control radius; status chips use the chip radius. Avatars and the clipped clinic logo are circular. Ordinary outlines are 1px. The final logo has no border, superseding the earlier asymmetric frame rule.

## Components

### Buttons
Primary, secondary, and light buttons have minimum height 44px and padding 10px 18px. Primary uses indigo and white with a darker hover; secondary is white with a line border. The light button is cream (#F9F6F0), indigo, full width, and 13px. Icon buttons are 40px square, with a muted-blue hover. Filter buttons are at least 40px tall. No blanket minimum height is specified for every button. Disabled buttons use opacity 0.5 and a not-allowed cursor.

### Chips
Status chips pair a text label with a 5px current-color dot, 6px gap, and 5px 8px padding. Their final size is 12px. Status is therefore conveyed by words as well as color.

### Cards / Containers
White bordered panels clip their contents and carry no shadow. Panel headings use 22px 24px padding; common form/context panels use 24px. The indigo care panel uses 25px 24px padding and light text.

### Inputs / Fields
Fields use a white background, stronger border, control radius, 11px 12px padding, and 13px text. Textareas resize vertically and use line-height 1.8. Search has a line border, 10px 14px padding, and maximum width 450px. All focusable elements receive the shared focus-visible outline. Dedicated field error/disabled variants are not implemented.

### Navigation
Desktop navigation is 13px, minimum height 46px, padded 12px, with muted text. Hover uses paper; selected navigation uses indigo and white. Mobile navigation has minimum height 42px, padding 10px, 12px text, and no count badge. Filter and clinical section selection use an indigo underline; patient selection uses a persistent muted-blue surface and indigo text.

### Motion and feedback
Only when reduced motion is not requested, buttons and navigation transition background-color and color over 0.15s ease-out. Notices use a muted-blue surface, a dismiss button, and role=status. A keyboard skip link appears on focus.

## Do's and Don'ts

### Do:
- **Do** preserve the supplied clinic logo and indigo/cream visual identity.
- **Do** retain visible text labels for status and a clear keyboard focus outline.
- **Do** check final CSS specificity and media overrides when extending the prototype.

### Don't:
- **Don't** describe the selected UI colors as an official brand manual.
- **Don't** claim that all body text is 15px or that every control is at least 40px tall.
- **Don't** infer new shadows, typefaces, or color ramps as established implementation tokens.
