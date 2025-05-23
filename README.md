# Cable Conduit Fill Simulator

## Introduction
This application provides a visual simulation of single-core and multi-core cables being placed inside a conduit. It aims to help visualize cable packing and will be updated to calculate conduit fill percentages and check compliance with AS/NZS standards.

## Features
*   Visual simulation of cables in a circular conduit using Pygame.
*   Physics-based interactions for cables using Pymunk.
*   Support for different cable types:
    *   Single-core
    *   Three-core
    *   Four-core
*   A PySide6 GUI for controlling aspects of the simulation:
    *   Changing core, sheath, and background colors.
    *   Spawning new cables.
    *   Resetting the simulation view.
    *   Detailed list of active cables in the conduit, showing ID and type.
    *   Ability to select and remove specific cables from the conduit via the GUI.
    *   Dynamic adjustment of conduit radius during simulation.
*   Keyboard controls in the simulation window to select cable types to be spawned.
*   Calculation of conduit fill percentage and AS/NZS compliance status displayed in the GUI.

## Dependencies
*   Python 3.x
*   Pygame (`pip install pygame`)
*   Pymunk (`pip install pymunk`)
*   PySide6 (`pip install pyside6`)

## Setup and Installation
1.  Ensure Python 3 is installed on your system.
2.  Install the required Python libraries using pip:
    ```bash
    pip install pygame pymunk pyside6
    ```
3.  Clone or download the source code for this application.

## How to Run
Navigate to the directory containing the application files and run:
```bash
python cable_gui.py
```
This will launch the GUI, which in turn starts the Pygame simulation window.

## How to Use

### GUI Controls (`cable_gui.py`):
*   **Color Pickers ("Core Color", "Sheath Color", "Background Color"):** Click these buttons to open a color dialog and change the respective colors in the simulation. Note: "Core Color" currently primarily affects single-core cables or the default for new types.
*   **"Spawn Cable" Button:** Spawns a cable of the type currently selected by keyboard (1,2,3) at a predetermined position near the top of the conduit.
*   **"Reset View" Button:** Clears all cables from the simulation, resets the physics space, and resets the cable ID counter.
*   **Active Cables List:** Displays a list of all cables currently in the conduit. Each entry shows a unique ID and the cable type (e.g., "ID: 1 - Type: SINGLE"). You can click to select a single cable or use Ctrl+Click (or Shift+Click for a range) to select multiple cables.
*   **"Remove Selected Cables" Button:** After selecting one or more cables from the "Active Cables List", click this button to remove them from the simulation and the list.
*   **Conduit Radius (mm) Input Field (SpinBox):** Allows you to enter a new desired radius for the conduit in millimeters (default range 50-500mm).
*   **"Apply Conduit Size" Button:** Click this button after changing the value in the "Conduit Radius" input field. This will resize the conduit in the simulation, update the physics, and recalculate fill percentages. Existing cables will adapt to the new boundary.

### Simulation Window (Pygame):
*   **Mouse Click:** Spawns a cable of the currently selected type at the mouse cursor's X-coordinate, near the top of the conduit.
*   **Keyboard Controls:**
    *   **1:** Select Single-core cable type for spawning.
    *   **2:** Select Three-core cable type for spawning.
    *   **3:** Select Four-core cable type for spawning.

## Future Development
*   More detailed user inputs for individual cable parameters (e.g., specific core sizes, sheath thicknesses per cable).
*   Advanced configuration options for physics and simulation parameters.
*   Saving and loading simulation states.

## Contributing
(Placeholder for contribution guidelines if the project becomes open to it)

## License
(Placeholder for license information - e.g., MIT, GPL)

## Further Potential Improvements

This application provides a solid foundation for conduit fill simulation. Here are some areas for potential future enhancements:

*   **More Granular Cable Definition:**
    *   Allow users to define custom cables by specifying conductor size (e.g., mm² or AWG), insulation thickness, and sheath thickness directly.
    *   Support for different materials affecting cable properties.
    *   Different insulation types (e.g., XLPE, PVC) with standard thicknesses.

*   **Advanced AS/NZS Standards Implementation:**
    *   Incorporate more detailed rules from AS/NZS 3000/3084 (e.g., different fill for conduit types, derating factors for length/bends, specific rules for cable types).
    *   Allow selection of the applicable standard or scenario.

*   **Enhanced Physics and Visuals:**
    *   More realistic cable packing algorithms.
    *   Visual representation of cable flexibility for multi-core cables.
    *   Support for different conduit shapes (e.g., square, rectangular).
    *   Zoom/pan functionality in the simulation window.

*   **GUI and Usability:**
    *   **Predefined Cable Library:** A library of common AS/NZS cable sizes/types to select from.
    *   **Save/Load Simulation State:** Allow users to save and load their work.
    *   **Report Generation:** Output a summary report (e.g., text or PDF).
    *   Improved error handling and user feedback within the GUI.

*   **Code and Structure:**
    *   More comprehensive error handling throughout the application.
    *   Use of a configuration file (e.g., JSON, YAML) for advanced settings or cable libraries.
    *   Performance optimization for simulations with a very large number of cables.
