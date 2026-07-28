  


Unified UI/UX Business Logic: Liquid Glass System

## **1. Conceptual Architecture (Container Hierarchy)**

To eliminate visual fragmentation, the UI must strictly adhere to a three-tier hierarchy. Frontend implementation details (CSS/Plugins/DOM structure) are delegated to the frontend engineers via their established ADRs. This document defines the deterministic interaction behavior and logical structure.

- **Layer 1: The Glass Plate (Dashboard Context):** The foundational background. Serves strictly as a blurred, translucent canvas. No interactive logic resides here.
- **Layer 2: The Device Card (Grouping Context):** Logical containers for specific domains (e.g., "Kitchen Lights" or "Bedroom AC"). Provides spatial grouping and semantic isolation.
- **Layer 3: The Interactive Node (Action Context):** The atomic unit of interaction. Whether it's a lighting pill or a wedge on the AC dial, *every* interactive element is a Node and must inherit the Universal State Machine.

## **2. The Universal State Machine (Interactive Nodes)**

Every Interactive Node, regardless of its shape or function, must deterministically map to the following states. This ensures the AC dial and Lighting pills feel conceptually identical in operation.


| **Logical State**      | **Trigger / Condition**                 | **UX / Visual Response Contract**                                                                                                                                                                         |
| ---------------------- | --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Idle (Off)**         | Entity state is 'off' or '0'.           | Neutral base transparency. No active glow. Iconography reflects off-state desaturation.                                                                                                                    |
| **Press (Transition)** | User initiates TouchDown / PointerDown. | Immediate tactile compression (scale down). Illusion of depth via inner shadowing. Trigger precise haptic feedback for physical confirmation (optimized for the Taptic Engine on flagship mobile devices). |
| **Active (On)**        | Entity state is 'on', 'heat', 'cool'.   | Return to base scale. Inject context-aware external glow (e.g., warm yellow for lights, blue/orange for AC). Icon color syncs to state.                                                                    |
| **Disabled / Error**   | Entity unavailable or offline.          | Opacity heavily reduced. Interactions strictly blocked. Error iconography replaces standard icon.                                                                                                          |


## **3. Component-Specific Behavioral Mapping**

### **3.1. Lighting Nodes (The Pills)**

- **Structure:** A single, unified Interactive Node.
- **Behavior:** Tapping anywhere on the pill triggers the Press transition. The glow effect upon reaching the Active state originates from the icon and bleeds across the volume of the pill.

### **3.2. Climate Control (The Radial Menu)**

The legacy flat graphic is deprecated. The dial must be conceptually deconstructed into a matrix of Independent Nodes.

- **The Hub (Center Display):** A passive node. Displays state. When Active, it inverts its depth profile (appears sunken into the glass) to visually anchor the active state.
- **The Orbital Segments (Ring Controls):** Each action (Power, Fan, Timer, Mode) is an isolated Interactive Node.
- **Isolation Rule:** Pressing the 'Fan' segment ONLY triggers the Press transition on that specific segment. The rest of the ring remains static. This standardizes the tactile feel, making a curved wedge feel exactly like a flat lighting pill.

## **4. Motion & Animation Principles**

To achieve a unified tactile aesthetic, linear transitions are prohibited for physical interactions.

- **State Toggles (Color/Glow):** Smooth, eased crossfades to prevent jarring visual pops when an entity changes state.
- **Physical Geometry (Presses):** Spring-based physics. The Node must compress instantly on touch, but rebound with a slight elastic curve on release, mimicking a physical glass button returning to its resting state.

