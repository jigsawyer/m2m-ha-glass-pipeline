# AC Interface: Core Interaction & Business Logic Specification

## 1. Architectural Paradigm & Finite State Machine (FSM)

The control interface operates as a strict Finite State Machine. The Central Hub is not just a display; it is the primary state router. The UI must decouple the *display state* from the *editing state* to prevent accidental inputs and reduce visual clutter.

## 2. State Definitions & Transitions (Central Hub)

The Central Hub dictates the visibility and context of the surrounding components (Radial Menu vs. Temperature Arc).


|                   |                          |                  |                                                                                                                                                                                              |
| ----------------- | ------------------------ | ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Current State** | **Trigger (User Input)** | **Target State** | **Execution Payload / Side Effects**                                                                                                                                                         |
| **OFF**           | Tap Central Hub          | **DEFAULT_ON**   | Transmit `turn_on` command to HA. Restore last known program/temp state.                                                                                                                     |
| **DEFAULT_ON**    | Tap Central Hub          | **EDIT_TEMP**    | 1. Hide Radial Menu. 2. Reveal Temperature Arc. 3. Apply semantic blur overlay constrained *only* to the parent container bounds. 4. Transform top-right Power button into Cancel (X). |
| **EDIT_TEMP**     | Tap Central Hub          | **DEFAULT_ON**   | 1. Commit new temperature value to HA. 2. Dismiss blur and hide Arc. 3. Reveal Radial Menu. 4. Restore top-right button to Power.                                                      |
| **EDIT_TEMP**     | Tap Cancel (X) Button    | **DEFAULT_ON**   | Abort operation. Revert to original temperature value. Dismiss blur/Arc, reveal Radial Menu.                                                                                                 |


## 3. Temperature Control Arc (The Horseshoe) Geometry & Logic

- **Arc Angle Constraint:** The arc must span exactly 270 degrees (horseshoe configuration). 180 degrees lacks sufficient touch resolution for fine temperature stepping. The 270-degree layout optimizes the tactile surface area.
- **Width Matching:** The stroke width and outer radius of the Temperature Arc must be mathematically identical to the outer boundaries of the hidden Radial Menu to maintain spatial consistency.
- **Data-to-Color Mapping (Gradient):** The arc requires a deterministic value-based gradient.
  - **Start (Min Temp):** Cold Blue (e.g., cooling context).
  - **End (Max Temp):** Warm Orange/Red (inheriting the visual token from the Timer component).
  - The slider thumb must dynamically update its fill color to match the exact interpolation point on the gradient based on the current temperature value.

## 4. Radial Menu Nodes: Tactile Contract

When the system is in **DEFAULT_ON** state, the radial menu segments must behave as independent Interactive Nodes, inheriting the tactile properties of the lighting dashboard pills.

- **Press Event (PointerDown):** Instant visual compression (scale down, simulate physical depth via inner shadow). Trigger mobile haptic feedback.
- **Release Event (PointerUp):** Spring-physics rebound to default scale.
- **Active State (Toggle On):** Injects contextual outer glow matching the entity's functional color.

