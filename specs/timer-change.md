# UI/UX Architecture & Business Logic Specification: AC Control Widget Watch Bezel Timer & Spatial Geometry Contract (v3.0)

## 1. Executive Summary & Architectural Scope

Document Purpose: Master business logic and spatial constraint specification for the active timer redesign within the Home Assistant Climate Control card (custom:button-card / Liquid Glass UI Architecture).

Core Objective: Replace platform-specific CSS/DOM implementations with deterministic UI/UX business rules, finite state machines (FSM), and relative spatial contracts. All visual attributes must inherit strictly from the project's Design System Tokens and Architectural Decision Records (ADRs) without hardcoded style overrides.



---



## 2. Spatial Domain Model & Geometry Contracts

### 2.1 The Watch Bezel (Безель / Люнет) Abstraction

The active timer progress bar is defined as a coaxial Analog Watch Bezel Layer superimposed onto the radial control structure.

- Tick Hierarchy Contract:
  - 360° Circular Continuum: Divided into 60 discrete angular ticks (6° step).
  - Quarter Markers (0°, 90°, 180°, 270°): Mapped to major directional axes (12, 3, 6, 9 o'clock). Inherits Token.Tick_Major dimensions.
  - Five-Minute Interval Markers (30° step): Inherits Token.Tick_Medium dimensions.
  - Standard Minute Markers: Inherits Token.Tick_Minor dimensions.
- Bezel Progress Track Abstraction:
  - The progress track exists as a coaxial arc layer bounded by R_bezel_inner and R_bezel_outer.
  - Relative Track Thickness Rule: The track width W_bezel is defined proportionally relative to the radial menu button width (W_radial_button) or specified by Token.Bezel_Track_Weight (W_bezel = k_weight * W_radial_button), ensuring visual prominence over thin lines while preserving scale across viewports.

### 2.2 Relational Equidistant Geometry Contract (Zero Hardcode Rule)

To maintain spatial equilibrium across device viewports, physical pixel values are strictly forbidden. All distances are expressed as relational constraints bound to Design System Tokens:

Let:

- G_radial = Inter-segment gap token between adjacent radial menu wedges (Token.Radial_Gap).
- R_radial_outer = Outer bounding radius of the radial menu button ring.
- D_bezel_gap = Radial clearance distance between R_radial_outer and the inner boundary of the watch bezel ring (R_bezel_inner).

Equidistant Clearance Contract:

D_bezel_gap = G_radial

Therefore:

R_bezel_inner = R_radial_outer + G_radial

R_bezel_outer = R_bezel_inner + W_bezel

Container Geometry Preservation Contract:

The outer bezel boundary MUST NOT displace or clip parent container boundaries:

R_bezel_outer + Padding_container <= R_card_boundary_limit



---



## 3. Finite State Machine (FSM) & Business Logic Rules

### 3.1 Active Timer Bezel State Matrix

- IDLE State: (timer_state == 'idle' or time_remaining == 0)
  - Bezel progress track opacity = 0. Tick ring renders at Token.Opacity_Dormant as background track.
  - Functional: Timer icon on radial menu acts as initiator for TIMER_CONFIG state.
- COUNTDOWN_ACTIVE State: (timer_state == 'active')
  - Bezel progress arc sweeps proportional to time_remaining / total_duration. Arc inherits Token.Active_Mode_Color.
  - Functional: Tapping glowing Timer radial button opens TIMER_MANAGE overlay. Main climate controls remain functional.
- WARNING_THRESHOLD State: (time_remaining < Threshold_warning)
  - Arc color interpolates to Token.Color_Warning. Leading edge point applies breathing pulse animation.
  - Functional: Non-blocking visual feedback. Countdown continues.
- EXPIRATION_EVENT State: (timer_state == 'expired')
  - Flash luminance impulse on bezel ring, followed by smooth decay transition to IDLE state.
  - Functional: Backend state synchronization trigger; haptic pattern dispatched.

### 3.2 Dynamic Mode Color Inheritance Contract

The Bezel progress track DOES NOT hardcode colors. It dynamically inherits its visual profile from the active HVAC state machine (climate.entity.hvac_action):

- HVAC Action = cooling: Inherits Token.Cooling_Primary_Color + Token.Cooling_Glow_Profile.
- HVAC Action = heating: Inherits Token.Heating_Primary_Color + Token.Heating_Glow_Profile.
- HVAC Action = fan / dry / idle: Inherits Token.Neutral_Active_Color + Token.Neutral_Specular_Profile.

### 3.3 Central Display Typography & Anti-Jitter Contract

- Tabular Numerals Mandate: When rendering remaining time (00:55:59) or target temperature, the central text node MUST enforce tabular/monospaced digit alignment (Token.Font_Feature_Tabular_Nums) to eliminate horizontal layout jitter during live updates.



---



## 4. Integration Directives for AI Orchestration Agents

For automated consumption by Cursor / AI Coding Agents in the GitOps pipeline:

- 1. Zero Hardcoded CSS Injections: Do NOT inject raw pixel values (px) or static hex codes in component templates. Reference abstract Design System Tokens or CSS variables specified by the parent theme/ADR.
- 2. Relational Geometry Binding: Bind SVG element coordinates dynamically using the mathematical relationships defined in Section 2.2.
- 3. Contract Compliance Validation:
  - Verify D_bezel_gap == G_radial.
  - Verify zero layout shift or boundary clipping of parent card container during state transitions.

  
