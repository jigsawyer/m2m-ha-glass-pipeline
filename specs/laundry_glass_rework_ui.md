  


Architectural Specification: Smart Laundry UI (Washer & Dryer)

## **1. System Architecture & HACS Dependencies**

To implement the deterministic state machine and the Apple Liquid Glass visual language within Home Assistant, the following HACS dependencies are strictly required. No custom code is provided here; this is the declarative configuration logic.

- **custom:button-card:** The core wrapper for all interactive elements. Required for complex DOM manipulation, state-based icon switching, and applying the glassmorphism styles via its styling object.
- **layout-card:** Required for the responsive grid layout (CSS Grid). Ensures seamless transition between desktop (side-by-side) and mobile (stacked) views.
- **mushroom-cards:** Utilized for internal sliders (temperature, spin speed) and drop-down selectors. Provides a clean, rounded baseline that fits the Apple ecosystem aesthetic.
- **card-mod:** Required to inject the structural glassmorphism properties (backdrop-filter) into native HA components where custom:button-card cannot be applied.

## **2. Design Language: Apple Liquid Glass (Glassmorphism)**

The UI must adhere to the following strict visual principles. These are business requirements for the frontend implementation.

- **Background Material:** All cards must have a translucent background (white/gray with 10-15% opacity depending on dark/light mode).
- **Backdrop Blur:** A heavy blur (minimum 20px) must be applied to the layer behind the cards to create the frosted glass effect.
- **Borders:** A 1px solid border with high transparency (e.g., white at 20% opacity) must encapsulate every card to provide physical definition against the blurred background.
- **Shadows:** Subtle, diffuse drop shadows (e.g., 0 4px 30px rgba(0, 0, 0, 0.1)) must be used to elevate the cards from the dashboard background.
- **Geometry:** Strict adherence to continuous curves (squircle). Border-radius must be a minimum of 24px for main cards, and 16px for internal control elements.

## **3. Responsive Layout Strategy**

The layout engine must be configured using custom:layout-card with a Grid layout type.

### **Desktop View (Viewport width > 1024px)**

The workspace is split into two equal columns, maximizing screen real estate.

- **Column 1:** Washing Machine Interface.
- **Column 2:** Dryer Interface.
- **Gap:** 24px between columns.

### **Mobile View (Viewport width <= 1024px, optimized for modern high-res screens)**

The layout collapses into a single column. The structural hierarchy prioritizes vertical scrolling.

- **Row 1:** Washing Machine Interface.
- **Row 2:** Dryer Interface.
- **Width:** 100% of the viewport width minus 16px padding on left and right.

## **4. Entity Data Model (Contracts)**

The UI depends on the following Home Assistant entities existing for EACH appliance. If physical integrations lack these, template sensors/helpers must be created to satisfy this contract.


| Entity Type | Suffix/Name     | Description & Allowed States                                                 |
| ----------- | --------------- | ----------------------------------------------------------------------------- |
| sensor      | _state          | Main state machine: 'off', 'ready', 'running', 'paused', 'finished', 'error'. |
| sensor      | *time*remaining | Integer representing minutes left. 0 if not running.                          |
| select      | _program        | List of programs (e.g., Cotton, Synthetics, Quick Wash, Wool).                |
| number      | _temperature    | (Washer only) Target temperature in Celsius. Step: 10.                        |
| number      | *spin*speed     | (Washer only) Spin speed in RPM. Step: 200.                                   |
| number      | *dry*level      | (Dryer only) Target dryness (1: Iron, 2: Cupboard, 3: Extra).                 |
| datetime    | *delay*start    | Input datetime for scheduled execution.                                       |
| switch      | _power          | Main power toggle.                                                            |
| switch      | *child*lock     | Disables physical buttons on the device.                                      |


## **5. Component Specification: Main Appliance Card**

Both the Washer and Dryer follow identical structural paradigms to ensure a cohesive Single Page Application (SPA) feel.

### **5.1. Header Section (Top 20% of Card)**

- **Positioning:** Flexbox row, space-between alignment.
- **Left:** Appliance Icon (Washing Machine or Dryer vector). Size: 48x48px.
- **Center:** Appliance Name (e.g., "Washing Machine"). Font: System San Francisco/Arial, bold, 18px.
- **Right:** Power Switch. A custom toggle with liquid animations. When ON, switch background shifts to a vibrant accent color (e.g., iOS Green).

### **5.2. State Visualization Area (Middle 40% of Card)**

This is the focal point of the UI. It changes dynamically based on the _state entity.


| State   | Visual Output                                                                                                    | Animations                                                                                                                                    |
| ------- | ---------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| OFF     | Displays "Offline" or "Powered Off". Controls below are disabled (opacity 0.4).                                  | None. Monochrome styling.                                                                                                                      |
| READY   | Displays "Ready to Start". Selected program highlighted.                                                         | Subtle pulse on the Start button.                                                                                                              |
| RUNNING | Displays remaining time prominently (e.g., "01:25" in 42px font). A circular progress ring encompasses the time. | Progress ring animates stroke-dashoffset. Drum icon rotates continuously (2s linear infinite). Liquid wave background effect behind the timer. |
| PAUSED  | Time remaining is displayed, but blurred slightly. Text "Paused" overlaid.                                       | Rotation stops. Start button pulses amber.                                                                                                     |
| ERROR   | Red hue takes over the glass card. Error code displayed.                                                         | Card border breathes red. Alert icon shakes every 5 seconds.                                                                                   |


### **5.3. Control Panel (Bottom 40% of Card)**

When state is OFF or RUNNING, these controls are visible but locked (pointer-events: none, opacity: 0.5), except for Child Lock.

- **Program Selector:** A horizontal scrolling list of pills, or a clean dropdown if space is constrained. Active program has a solid translucent white background.
- **Sliders (Temp / Spin / Dryness):** Mushroom-style sliders.

- Thumb: Circular, mimics a physical knob with drop shadow.
- Track: Fills with an accent color (e.g., Blue for cold/temp, Orange for heat/dryer) as it moves left to right.

- **Delay Start:** A button that opens a native HA datetime picker modal. If a time is set, the button displays the scheduled time and pulses gently.
- **Action Button (Start/Pause):** Spans 100% width at the bottom.

- If READY: Text reads "Start Wash/Dry". Color: Blue.
- If RUNNING: Text reads "Pause". Color: Amber.
- Height: 56px (optimized for touch targets).

## **6. Detailed Interaction & Business Logic Rules**

- **State Propagation:** Any change in a slider (e.g., temperature) must wait for a 500ms debounce before sending the service call to HA to prevent flooding the appliance API.
- **Mutually Exclusive States:** If the *state is 'running', the* delay_start input must be hidden or forcibly disabled.
- **Haptic Feedback (Mobile):** If supported by the HA companion app, interactions with the Start/Pause button or the end of a slider drag must trigger a vibration event.
- **Responsive Scaling:** Font sizes must use clamp() functions (or equivalent logic in card-mod) to ensure text does not overflow when viewed on smaller screens or split-screen mode on desktop.

