# **UI/UX Architecture Specification: Interface Polish & Standardization**

This document serves as the comprehensive source of truth for the final UI/UX polish of the smart home dashboard. It is written specifically for implementation via **custom:button-card** abstractions within the ecosystem. The specification defines deterministic business logic, interactive physics, and layout geometries without relying on hardcoded styles, ensuring scalability across varying device dimensions and high-end mobile viewports.

## **1. Radial Timer Interface Refinement**

### **1.1 Architectural Concept**

The continuous arc progress bar is to be deprecated in favor of a segmented, radial tick-based indicator (clock-face metaphor). This skeletal, glassmorphism-compatible approach improves the cognitive mapping of time while maintaining a clean, minimalist aesthetic.

### **1.2 Geometric Specifications & Mapping**

The radial track consists of individual segments mapped to the time remaining. The generation of these ticks must follow a strict mathematical loop.

- **Total Ticks:** Exactly 60 evenly spaced radial lines distributed across a 360-degree SVG coordinate space.
- **Tick Hierarchy:** Every 15th tick (representing the 12, 3, 6, and 9 o'clock positions) is designated as a "Quarter Tick". All other ticks are "Standard Ticks".
- **Track Geometry:** The center of the radial track must perfectly align with the absolute center of the widget card. The outer boundary of the ticks defines the widget's active radius.


| Tick Type     | Relative Length | Relative Thickness | Geometric Logic                                                  |
| ------------- | --------------- | ------------------ | ----------------------------------------------------------------- |
| Standard Tick | Base Unit (1x)  | Base Unit (1x)     | Evenly distributed at 6-degree intervals, excluding quarter axes. |
| Quarter Tick  | 1.25x Base Unit | 1.5x Base Unit     | Positioned exactly at 0, 90, 180, and 270 degrees.                |


  


### **1.3 Animation & State Transitions**

The transition of ticks from an active to an inactive state must be tied to the entity's time-remaining attribute, proceeding counter-clockwise.

- **Active State:** Ticks representing the remaining time maintain 100% target opacity (solid white/bright).
- **Inactive State (Track Ring):** Ticks that fall outside the remaining time window do not disappear. Instead, their opacity shifts to 15-20%. This creates a persistent, translucent underlying track that defines the widget's shape against the blurred background.
- **Transition Interpolation:** As the timer decreases, the state change of a tick from Active to Inactive must not be a binary snap. It requires a linear interpolation (fade-out) over the duration of that specific tick's time slice, providing a fluid, analog feel.

// Logical Abstraction for custom:button-card template  
IF (tick_index  *time_per_tick) < time_elapsed THEN*  
    *Apply Inactive State (Translucent)*  
*ELSE IF (tick_index*  time_per_tick) == current_active_tick THEN  
    Apply Interpolating Fade State  
ELSE  
    Apply Active State (Opaque)  
END IF  
  


## **2. Temperature Control Widget Standardization**

### **2.1 Dimensional Unification**

To establish a cohesive design system, the spatial relationship between the inner display orb and the outer control track must be identical across both the Timer and Temperature widgets.

1. Calculate the distance (Delta R) between the outer bounding box of the central information circle and the inner bounding box of the interactive track on the Timer widget.
2. Apply this exact Delta R to the Temperature widget.
3. The thickness of the Temperature track must be mathematically uniform and matched to the visual weight of the Timer's tick track.

### **2.2 Semantic Gradient & Scale Logic**

The background of the temperature track must provide immediate semantic feedback regarding the target climate state.

- **Gradient Mapping:** The track utilizes a smooth color transition. The lowest point of the logical scale is anchored with a cool hue (e.g., #00B4DB / Blue), transitioning smoothly to a warm hue (e.g., #FF4B2B / Red) at the maximum point of the scale.
- **Visual Ticks:** Implement subtle, tick-based markers (without numeric labels) mapped to the magnetic snapping increments (e.g., every 0.5° or 1°). These ticks act as visual anchors for the snapping behavior.

### **2.3 Interactive Physics (Thumb Squish)**

The interactive handle (thumb) requires micro-interaction physics to confirm user engagement, leveraging touch-screen paradigms.


| Interaction Event        | Thumb Element Behavior                                                                                                 | Track Element Behavior                           | Easing Function                         |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ | ---------------------------------------- |
| Touch Start / Mouse Down | Scale uniformly by +15% from the origin center.                                                                        | Strictly 0% mutation. Remains completely static. | Ease-Out (Fast response)                 |
| Drag / Move              | Maintain +15% scale. Snap to nearest logical tick interval. Trigger system haptic feedback on snap event if available. | Strictly 0% mutation.                            | Linear (Follows pointer)                 |
| Touch End / Mouse Up     | Return to base scale (100%).                                                                                           | Strictly 0% mutation.                            | Ease-Out-Back (Slight bounce on release) |


  


## **3. Timer Sub-Menu Optical Alignment**

### **3.1 Typography: Tabular Alignment**

The countdown timer text (e.g., "00:04:54") inherently changes character widths as it ticks down (e.g., the number '1' is narrower than '0'). To prevent horizontal layout jitter, the typography engine must be explicitly instructed to use tabular, monospaced numeric features.

- **Font Feature Specification:** Enforce tabular-nums for the specific text node rendering the countdown. This ensures that every character occupies the exact same horizontal space, freezing the bounding box width.

### **3.2 Optical Centering Logic**

Centering an asymmetrical group (Icon + Text) geometrically often results in the text appearing off-center to the human eye. We must employ optical centering.

1. **Anchor the Text:** The text node containing the countdown must be positioned so that its own center point aligns perfectly with the absolute vertical and horizontal center of the parent modal container.
2. **Offset the Icon:** The hourglass icon is positioned to the left of the text node. It must be placed on the exact same horizontal baseline axis as the text to ensure vertical equilibrium.
3. **Negative Margin / Absolute Positioning:** To prevent the icon from pushing the text to the right, the icon should be taken out of the standard flex flow (using absolute positioning relative to the text block) OR the entire container must be shifted left by exactly half the width of the icon plus its gap, ensuring the text remains optically dead-center on the screen.
4. **Icon Scale:** The icon bounding box should be scaled up by approximately 10-15% relative to its current state to better match the visual weight (cap height) of the adjacent timer typography.

