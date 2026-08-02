# **UI/UX Architecture & State Management Specification: Smart Home Climate Control Interface**

## **Document Overview & Architecture Scope**

This document defines the definitive production specification for the visual refinement, state management, and interaction design of the Smart Home Climate Control system interface. Operating within the Home Assistant ecosystem and tailored for high-density mobile displays (such as Super Retina XDR displays on modern devices), this system prioritizes extreme visual elegance, deterministic state management, sub-millisecond perceived latency, and complete resilience against race conditions or hardware asynchronous delays.l









All visual styling specifications are expressed strictly through architectural design tokens, spatial constraints, and business logic abstractions rather than fixed platform-specific style declarations, enabling seamless implementation across native or web-based frontend renderers.

 

## **Section 1: Active Timer Architecture & Circular Geometry Preservation**



### **1.1 Problem Statement & Visual Domain Model**

The legacy implementation utilized an overlay circular progress bar that intersected with the segment borders of the radial button ring. This introduced visual conflict, disrupted the glassmorphic aesthetic (liquid glass design language), and degraded spatial legibility. The new design preserves the circular geometry by integrating the progress indicator directly into the outer tick ring of the existing radial structure as an **Ambient Conic Track**.

### **1.2 Layer Stack & Glassmorphic Composite Architecture**

The timer component consists of three synchronized visual sub-layers rendered within the radial menu container:

- **Base Outer Ring (Static Tick Track):** A 360-degree radial ring composed of discrete tick marks set to low opacity (20% nominal opacity) establishing the static spatial boundary.
- **Active Progress Track (Conic Gradient Ring):** A dynamic sweeping fill layer utilizing a conic gradient that expands or contracts clockwise around the perimeter. The layer resides beneath the top glass glassmorphic filter, creating an illusion of colored fluid encapsulated within translucent glass. It features an inner radial glow that accentuates depth.
- **Leading Edge (Soft Gaussian Point):** A localized highlight positioned at the active terminus of the conic fill. It applies a soft Gaussian blur effect to simulate specular light refraction inside the glass shell, providing a precise yet subtle visual marker of current elapsed time.



### **1.3 Timer Finite State Machine (FSM) Matrix**

The active timer system operates under a multi-state machine defined below:


| **State Name**        | **Trigger / Event**                                              | **Visual Behavior & Glass Effects**                                                                                           | **Interaction & Motion Rules**                                                                                                        |
| --------------------- | ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| **Idle**              | No active countdown set.                                         | Static outer tick ring at 20% opacity. Inner progress ring hidden (0% opacity). Leading edge invisible.                       | Timer icon segment acts as an interactive button to initiate setup.                                                                    |
| **Configuration**     | User drags across radial ring or selects discrete time interval. | Active progress track illuminates dynamically as touch point rotates. Inner glow intensity scales with time duration.         | Rotational gesture snap-to-grid with spring physics (15-minute interval quantization). Live numeric overlay displayed in central node. |
| **Active_Tracking**   | Timer execution initiated by server/user confirmation.           | Conic fill ring smoothly recedes counter-clockwise (or clockwise depletion depending on mode). Soft leading edge glow active. | Linear interpolation easing applied across tick intervals to guarantee sub-pixel smooth visual decay without stutter.                  |
| **Threshold_Warning** | Remaining duration reaches < 10% (or < 5 minutes).               | Color token morphs smoothly into warm accent hue. Opacity breathing animation applied to leading edge (1.5s period).          | Non-blocking visual alert. Countdown continues uninterrupted.                                                                          |
| **Completion**        | Countdown reaches zero (Backend Event).                          | Flash luminance boost (+100% brightness spike for 200ms) followed by a exponential fade-out (500ms) to Idle state.            | Haptic feedback trigger; interface returns to standard climate monitoring view.                                                        |




### **1.4 Typography & Numeric Anti-Jitter Rules**

To maintain visual stability in the central display area during active countdown tracking, numeric values MUST enforce tabular/monospaced digit alignment (Font Feature Settings: 'tnum'). Standard proportional font rendering causes layout jitter (horizontal shaking) as digits fluctuate in width (e.g., '1' vs '8'). The main temperature digits remain prominent ("21°"), while the timer countdown is rendered as an auxiliary monospaced sub-label ("01:45:00") directly below the primary status string ("Холод") with reduced visual weight.

 

## **Section 2: Global State Management, Concurrency Control & Optimistic UI**



### **2.1 Architectural Paradigm: Single Source of Truth & Asynchronous Bus**

In distributed IoT environments, physical actuators (HVAC compressors, fans, valves) exhibit inherent latency (from 500ms up to several seconds) due to safety cycles and network delays. The frontend architecture MUST treat the backend Home Assistant event bus as the ultimate Single Source of Truth (SSoT), while employing local optimistic state mutations to deliver instant visual response.

### **2.2 Component-Level Isolation vs. Global Locking**

A critical flaw in naive interfaces is applying a full-screen or global modal lock ("Please wait") during hardware state changes. This ruins multi-device interaction. Under this specification, locking is strictly applied at the **Individual Climate Entity Level** (Component-Level Scope). Interacting with the climate control unit in the "Office" locks only the "Office" widget controls, leaving all other rooms and system controls fully interactive.

### **2.3 Optimistic UI Pattern with Graceful Rollback & Eventual Consistency**

When an action is taken (e.g., toggling power or changing target temperature):

1. **Instant Optimistic Mutation (0ms):** The client interface immediately updates visual state to reflect the intended outcome. Button background glow activates, temperature digits update, and secondary controls enter a pending transition state.
2. **State Lock & Event Suppression:** Interactive controls within the affected climate entity enter a non-clickable state `pointer-events: none`). Further tap events are intercepted and discarded to prevent event flooding or duplicate payloads.
3. **Asynchronous Dispatch:** The mutation request is transmitted via WebSocket API to Home Assistant.
4. **Reconciliation Loop:**

- *Positive Acknowledgement (ACK Received):* When state update event is published from backend, the entity transitions smoothly from Optimistic state to Confirmed state. Component locks are released.
- *Timeout / Failure (NACK or Timeout > 5000ms):* If no confirmation arrives within the defined window, the system initiates a **Graceful Rollback**. The local UI animates back to the verified backend state, accompanied by a subtle error notification feedback.



### **2.4 Complete Entity State Machine & Interaction Rules Matrix**


| **Current State**   | **User Action / Event**    | **Target State**   | **Visual & Glass Animation Behavior**                                                                                                                                                             | **Concurrency Lock Scope**                                                     |
| ------------------- | -------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| **Off (Confirmed)** | Tap Power Icon             | **Optimistic_On**  | Power icon lights up instantly. A indeterminate pulse ring (subtle breathing animation) appears inside the inner boundary ring. Central text displays target temperature with reduced saturation. | Power button and all mode/fan segments locked `pointer-events: none`).          |
| **Optimistic_On**   | Backend Event State = On   | **Confirmed_On**   | Indeterminate pulse ring fades out gracefully (300ms ease-out). Full vibrant glass highlights restore across all radial buttons. Status string updates to active mode ("Холод").                  | Lock released. All buttons become fully interactive.                            |
| **Optimistic_On**   | Timeout (>5s) or Error ACK | **Error_Rollback** | Inner node border flashes soft warning red (200ms). Horizontal subtle shake effect (4px displacement, 3 cycles). Visuals morph back to Off state.                                                 | Lock released after rollback completion (total execution 600ms).                |
| **Confirmed_On**    | Tap Power Icon             | **Optimistic_Off** | Interface immediately desaturates. Radial buttons dim to 30% opacity. Central display shows subtle closing contraction animation. Indeterminate dim pulse active.                                 | All entity controls locked `pointer-events: none`).                             |
| **Optimistic_Off**  | Backend Event State = Off  | **Confirmed_Off**  | Indeterminate pulse ceases. Radial buttons enter dormant glass state. Central display shows power off indicator.                                                                                  | Lock released on Power button only. Mode controls remain disabled in Off state. |




### **2.5 Throttling, Debouncing & Event Delegation Rules**

To eliminate multi-click storms (where a user repeatedly taps a slow-responding interface), the frontend implements strict event delegation and command queuing rules:

- **Hard Tap Lockout:** Upon registering an input tap, the event handler ignores all subsequent tap gestures on that entity until the active state transition resolves or hits the 5-second timeout safeguard.
- **Debounced Continuous Inputs:** Continuous interactions (such as dragging a target temperature slider or fan speed dial) use a leading-edge optimistic visual update combined with a 300ms trailing-edge network payload debounce. This ensures fluid 60fps/120fps UI rendering while emitting only a single command to the WebSocket backend upon gesture completion.

 

## **Section 3: Micro-Interactions, Edge Cases & Haptic Protocol**



### **3.1 Tactile Feedback Mapping Protocol (Haptic Engine)**

Because glassmorphic interfaces lack physical tactile affordance, precise haptic patterns are mandatory to anchor visual feedback to physical sensation. The table below specifies the required haptic profile mappings:


| **Interaction Event**                          | **Haptic Feedback Token**    | **Physical Characteristics & Perception Goal**                                                                                       |
| ---------------------------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| **Discrete Segment Tap** (Mode/Power select)   | `Light_Impact`               | Short, crisp click feeling (10ms transient). Confirms gesture capture immediately.                                                    |
| **Rotational Slider Drag** (Timer/Temp change) | `Selection_Change`           | Ultra-soft micro tick emitted upon crossing each step quantization threshold (e.g., each 0.5°C or 15m). Simulated mechanical ratchet. |
| **Backend Confirmation ACK**                   | `Medium_Impact`              | Slightly deeper impulse (20ms transient). Signals successful hardware execution without requiring user to watch screen.               |
| **Rollback / Network Error**                   | `Error_Notification_Pattern` | Double heavy burst pulse. Synchronized with visual red border flash and horizontal shake animation.                                   |




### **3.2 Fault Tolerance: Network Partitioning & Degraded State Rendering**

Smart home mobile applications are inherently subject to intermittent connectivity loss (e.g., leaving Wi-Fi range or router restarts). The client maintains an active WebSocket Heartbeat Monitor `ping/pong` cycle every 3000ms).

- **Degraded State Trigger:** If two consecutive heartbeat responses fail, the climate control entity enters `Degraded_Offline` state.
- **Visual Masking:** The widget applies an elevated glass blur backdrop filter (increased blur radius) and a grayscale filter across all controls. Interactive elements transition to 20% opacity.
- **Interaction Guard:** Tapping any button on a degraded widget suppresses optimistic mutation entirely. Instead, a contextual glass floating toast message appears: *"Connection to Home Assistant lost. Reconnecting..."*
- **Auto Re-synchronization:** When WebSocket connection is re-established, the client triggers an explicit state pull payload `get_states`). The local UI synchronizes strictly to backend data before removing the degraded mask layer.



### **3.3 Motion Physics & Transition Curves Matrix**

Linear motion curves feel robotic and unnatural in high-end interfaces. All state transitions MUST conform to standardized physics cubic bezier curves specified below:


| **Transition Type**                   | **Bezier / Physics Token**                       | **Duration Specification**         | **Design Intent**                                                                                 |
| ------------------------------------- | ------------------------------------------------ | ---------------------------------- | -------------------------------------------------------------------------------------------------- |
| **Standard State Morph**              | `cubic-bezier(0.4, 0.0, 0.2, 1)`                 | 300 ms                             | Standard smooth acceleration/deceleration for color, glass specular highlight, and opacity shifts. |
| **Radial Ring Snap / Elastic Adjust** | `spring(mass: 1.0, stiffness: 180, damping: 12)` | Dynamic physics duration (~450 ms) | Elastic physical snap effect when adjusting rotational slider or releasing timer control.          |
| **Error Shake & Rollback**            | `cubic-bezier(0.36, 0.07, 0.19, 0.97)`           | 400 ms                             | Rapid decaying displacement oscillation indicating rejection of user action.                       |


