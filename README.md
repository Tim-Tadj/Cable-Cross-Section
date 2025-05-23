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
*   Keyboard controls in the simulation window to select cable types to be spawned.
*   (Upcoming) Calculation of conduit fill percentage.
*   (Upcoming) AS/NZS compliance checks for conduit fill.

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
*   **"Spawn Cable":** Clicks this button to add a cable of the currently selected type (see Keyboard Controls below) into the simulation. The cable will spawn near the top of the conduit.
*   **"Reset View":** Clears all cables from the simulation and resets the physics space.

### Simulation Window (Pygame):
*   **Mouse Click:** Spawns a cable of the currently selected type at the mouse cursor's X-coordinate, near the top of the conduit.
*   **Keyboard Controls:**
    *   **1:** Select Single-core cable type for spawning.
    *   **2:** Select Three-core cable type for spawning.
    *   **3:** Select Four-core cable type for spawning.

## Future Development
*   Implementation of accurate cross-sectional area calculations for cables and conduits.
*   Display of conduit fill percentage and AS/NZS compliance status.
*   More detailed user inputs for cable and conduit parameters.

## Contributing
(Placeholder for contribution guidelines if the project becomes open to it)

## License
(Placeholder for license information - e.g., MIT, GPL)
