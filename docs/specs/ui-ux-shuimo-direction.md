# Shuimo UI/UX Direction for Cultivation World Simulator

Status: draft v1  
Owner: design / frontend shared spec  
Updated: 2026-04-13  
Reference:

- [Shuimo Design](https://shuimo.design/en)
- `docs/frontend.md`
- `docs/specs/online-business-plan.md`

## 1. Purpose

This document defines how to use the visual language of Shuimo in this project without blindly importing another stack or turning the game into a decorative dashboard.

The goal is:

- keep the current Vue 3 + Naive UI + Pixi architecture
- absorb Shuimo's `ink-wash`, `rice-paper`, `seal`, and `calligraphic` feel
- redesign the UI into a commercial-grade xianxia product identity

## 2. What We Should Borrow from Shuimo

From the official site and exported styles, the most useful qualities are:

- paper-like textured surfaces
- muted but expressive ink-and-mineral color palette
- brushstroke framing and dividers
- ornamental headers and seal-like accents
- strong cultural identity instead of generic SaaS panels
- restrained motion rather than hyperactive micro-animation

We should borrow the language, not copy the implementation wholesale.

## 3. What We Should Not Do

- do not try to embed Shuimo as a direct dependency and fight framework mismatch
- do not replace game readability with decoration
- do not make every panel heavy, dark, and noisy
- do not turn map gameplay into a static art board
- do not apply brush textures on top of dense tiny text

## 4. Product-Level UI Goals

The UI should make the game feel like:

- a living chronicle
- a strategist's scroll
- a sect archive and omen board

The UI should stop feeling like:

- a debug console
- a data dashboard
- a passive log viewer

## 5. Recommended Visual Pillars

### 5.1 Material language

Primary materials:

- rice paper
- ink wash
- mineral pigment
- carved seal lacquer
- aged silk and wood

Recommended use:

- panels feel like layered paper or silk sheets
- modal frames feel like scrolls or study boards
- important buttons feel like stamped seals or lacquer plaques

### 5.2 Color system

Recommended base palette derived from Shuimo-style tones:

- `Paper`: `#eae4d1`
- `Soft paper`: `#dfd7c2`
- `Ink`: `#151d29`
- `Ink soft`: `#2b333e`
- `Slate`: `#6b798e`
- `Mist blue`: `#a3bbdb`
- `Jade teal`: `#6ca8af`
- `Pine green`: `#446a37`
- `Earth brown`: `#945635`
- `Seal red`: `#a81c2b`
- `Alert red`: `#861717`
- `Gold accent`: `#da9233`

Semantic mapping:

- neutral surfaces use paper, ink soft, slate
- authority / premium uses seal red + gold accent
- cultivation / nature uses pine green + jade teal
- danger uses alert red, never the same hue as premium reward
- clickable hover states should shift tone, not glow neon

### 5.3 Typography

Use typography with hierarchy, not one default sans stack everywhere.

Recommended structure:

- display font: calligraphic or serif-with-culture for titles only
- body font: readable UI font for dense information
- numeral font: stable, legible numerals for stats and resources

Rules:

- titles can be expressive
- logs, stats, and detailed tables must prioritize readability
- avoid using brushy fonts in long paragraphs

### 5.4 Shape language

- rectangles should feel framed, bordered, or paper-mounted
- corners can be slightly cut or ornamented
- important modules can use seal tabs or hanging labels
- dividers should feel like brush lines or ornamental rails

## 6. UX Principles for This Game

### 6.1 Decision-first, not information-first

Every important screen should answer:

- what happened
- why it matters
- what I can do now

### 6.2 One primary action per context

Each panel must have one obvious next step.

Examples:

- on recap screen: `Respond`
- on disciple screen: `Sponsor`
- on sect threat screen: `Intervene`
- on world opportunity screen: `Commit`

### 6.3 Chronicle over clutter

Event feeds should read like a chronicle, not like a noisy console.

Recommended treatment:

- major events large and illustrated with icon/seal
- minor events collapsed and batch summarized
- story events visually distinct from factual events

### 6.4 World map remains the heart

Do not bury the map under panels.

The map should still feel like:

- the living world surface
- the first thing the player emotionally reads

Panels should orbit the map, not replace it.

## 7. Screen-by-Screen Direction

### 7.1 Splash / entry

Desired feeling:

- opening a scroll in a study

Recommended elements:

- paper wash background with animated ink bloom
- logo lockup with seal accent
- two to three strong entry actions only
- subtle motion in clouds, dust, or water ink

### 7.2 Main world screen

Desired feeling:

- a world atlas with active omens

Recommended layout:

- central map remains dominant
- status bar becomes a lacquered or paper-mounted ritual strip
- right column becomes `chronicle` instead of generic event list
- left or bottom quick actions become compact talismans / command slips

### 7.3 Sect dashboard

Desired feeling:

- archive room + strategic planning desk

Recommended modules:

- sect prestige
- treasury
- disciples in danger / rising stars
- current agenda
- rivalry / diplomacy
- upcoming world opportunities

Avoid:

- flat card grids with equal weight

### 7.4 Main disciple detail

Desired feeling:

- dossier + fate record

Recommended treatment:

- portrait framed like a hanging scroll or seal-stamped profile
- tabs styled as dossier dividers, not web app tabs
- cultivation path, bonds, and danger markers prioritized over exhaustive raw data

### 7.5 Event chronicle

Desired feeling:

- historical ledger with bursts of dramatic brushwork

Recommended structure:

- factual event line
- story expansion on demand
- seal markers for major world moments
- filters hidden behind a compact "scribe tools" affordance

## 8. Motion Direction

### 8.1 Motion rules

Motion should suggest ink, paper, and ritual, not generic app transitions.

Recommended motion motifs:

- paper unfold
- seal stamp
- ink spread
- brush swipe reveal
- mist drift

### 8.2 Motion budget

Use motion sparingly on:

- entering menus
- receiving major events
- confirming interventions
- transitioning between strategic contexts

Avoid:

- constant bounce
- excessive parallax
- dozens of competing shimmer effects

## 9. Component Strategy for Current Stack

### 9.1 Keep existing architecture

Current stack:

- Vue 3
- Pinia
- Naive UI
- Pixi / Vue3-Pixi

Recommended strategy:

- keep Naive UI for system behavior, forms, and stable primitives
- wrap or reskin it with project tokens
- use Pixi for world-layer atmospherics and high-value effects

### 9.2 Design token plan

Introduce a dedicated token layer for the commercial visual system.

Recommended files:

- `web/src/styles/tokens/shuimo.css`
- `web/src/styles/themes/shuimo-theme.ts`
- `web/src/styles/mixins/paper-panels.scss`

Recommended token groups:

- color
- typography
- spacing
- borders and ornaments
- shadows
- motion timing
- texture opacity

### 9.3 Naive UI integration plan

Use Naive UI as the interaction skeleton, but re-theme:

- buttons
- modal shells
- tabs
- dropdowns
- inputs
- pagination

Rules:

- system settings can stay cleaner and more utilitarian
- player-facing strategic surfaces should get the full art direction

### 9.4 Pixi integration plan

Use Pixi for:

- cloud and mist overlays
- water shimmer
- omen pulses
- hidden domain reveals
- large event transitions

Do not use Pixi to simulate every panel ornament if simple CSS can do it cheaper.

## 10. Recommended Art Asset Backlog

Need early:

- paper texture set
- ink wash gradient set
- seal stamp pack
- ornamental border pack
- tab labels / hanging tags
- icon set in a consistent family

Need later:

- world event illustrations
- sect emblem variants
- seasonal overlays
- premium cosmetic frames

## 11. Accessibility and Performance

### 11.1 Accessibility

- all decorative contrast must still preserve readable text
- provide a low-texture mode
- provide reduced-motion mode
- preserve strong hover/focus states
- major information cannot rely on color alone

### 11.2 Performance

- paper textures should be reused and cached
- avoid stacking many full-screen blend layers
- prefer tokenized CSS over huge image-heavy components
- keep map rendering optimization rules from `docs/frontend.md`

## 12. Visual Hierarchy Rules

Use three levels of emphasis only:

- major: player-critical decision or world-changing event
- medium: current context and progress
- minor: secondary metadata

Common current risk:

- too many modules shouting at once

Fix:

- one hero focus
- one supporting column
- one background layer

## 13. Suggested First Implementation Pass

The first Shuimo pass should focus on shell and rhythm, not full screen-by-screen perfection.

### Pass 1

- splash screen
- status bar
- system menu shell
- event chronicle shell
- primary buttons

### Pass 2

- sect dashboard
- disciple detail
- world intervention drawer
- recap presentation

### Pass 3

- monetization surfaces
- cosmetics previews
- private world creation flow
- seasonal world event effects

## 14. Monetization Surface Guidelines

Paid surfaces must feel tasteful and thematic.

Recommended:

- cosmetics presented as seals, robes, banners, archives
- private world product presented as opening a personal realm
- premium chronicle as a collector edition archive

Avoid:

- loud shop banners
- flashing CTA spam
- modern ad-like cards that break immersion

## 15. Final Design Thesis

The commercial version should look like:

- `an interactive xianxia chronicle`

not like:

- `a debug-heavy sim tool with decorative assets glued on top`

Shuimo is the right direction if we use it as a visual philosophy:

- material
- pace
- restraint
- cultural identity

It is the wrong direction if we treat it like a copy-paste component library migration.
