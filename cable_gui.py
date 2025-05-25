import sys
import threading
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton,
                               QColorDialog, QLabel, QSpinBox, QHBoxLayout, QGroupBox,
                               QListWidget, QAbstractItemView, QComboBox, QDoubleSpinBox) 
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, QTimer
import main  # Import your main.py file
from main import input_handler, update_simulation_conduit_radius, current_conduit_radius as main_current_conduit_radius
# Qt.UserRole is used with item.data() / item.setData()
from calculations import (
    calculate_conduit_cross_sectional_area,
    calculate_total_cable_area,
    calculate_conduit_fill_percentage,
    check_as_nzs_compliance
)
# CONDUIT_RADIUS is now main_current_conduit_radius, DEFAULT_CONDUIT_RADIUS is in config
from config import CORE_RADIUS, SHEATH_THICKNESS, MARGIN, CableType, DEFAULT_CONDUIT_RADIUS 

class CableGUI(QWidget):
    """
    Provides the main graphical user interface for the Cable Conduit Fill Simulator.
    It allows users to control simulation parameters like colors, spawn cables,
    reset the simulation, and view conduit fill calculations and compliance status.
    The GUI runs in a separate thread from the Pygame simulation.
    """
    def __init__(self):
        """
        Initializes the CableGUI widget, sets up UI elements,
        configures initial color values, and starts the Pygame simulation thread
        and a QTimer for periodic updates of calculation displays.
        """
        super().__init__()
        self.setWindowTitle("Cable Simulation GUI")

        self.core_color = QColor(*main.CORE_COLORS["single"])
        self.sheath_color = QColor(*main.CABLE_SHEATH_COLOR)
        self.background_color = QColor(*main.BACKGROUND_COLOR)

        self.initUI()
        # self.start_pygame_thread() # Moved after QTimer setup

        # Setup QTimer to periodically update calculations
        self.calc_update_timer = QTimer(self)
        self.calc_update_timer.timeout.connect(self.update_calculations_display)
        # The QTimer is set to trigger the update_calculations_display method
        # at regular intervals (currently 500ms). This ensures that the GUI's
        # displayed calculations (fill percentage, compliance) are periodically
        # refreshed to reflect the state of the simulation (main.cables list).
        self.calc_update_timer.start(500) # Update every 500ms (0.5 seconds)
        
        self.start_pygame_thread() # Ensure Pygame thread is started

    def initUI(self):
        """
        Sets up the user interface elements of the GUI, including buttons
        for color selection, spawning cables, resetting the view, and labels
        for displaying calculation results.
        """
        layout = QVBoxLayout()

        # Color selection buttons
        self.core_color_button = self.create_color_button("Core Color", self.core_color, self.set_core_color)
        self.sheath_color_button = self.create_color_button("Sheath Color", self.sheath_color, self.set_sheath_color)
        self.background_color_button = self.create_color_button("Background Color", self.background_color, self.set_background_color)

        layout.addWidget(self.core_color_button)
        layout.addWidget(self.sheath_color_button)
        layout.addWidget(self.background_color_button)

        # Cable Type Selection
        self.cable_type_label = QLabel("Cable Type:")
        layout.addWidget(self.cable_type_label)
        self.cable_type_combo = QComboBox()
        for cable_type in CableType:
            self.cable_type_combo.addItem(cable_type.name.replace("_", " ").title(), cable_type)
        layout.addWidget(self.cable_type_combo)

        # Outer Diameter Input
        self.outer_diameter_label = QLabel("Outer Diameter (mm):")
        layout.addWidget(self.outer_diameter_label)
        self.outer_diameter_spinbox = QDoubleSpinBox()
        self.outer_diameter_spinbox.setRange(10.0, 100.0)
        self.outer_diameter_spinbox.setValue(60.0) # Default: CORE_RADIUS * 2 for a single core
        self.outer_diameter_spinbox.setSingleStep(1.0)
        layout.addWidget(self.outer_diameter_spinbox)

        # Spawn Cable Button
        self.spawn_button = QPushButton("Spawn Cable")
        self.spawn_button.clicked.connect(self.spawn_cable)
        layout.addWidget(self.spawn_button)

        # Reset View Button
        self.reset_button = QPushButton("Reset View")
        self.reset_button.clicked.connect(self.reset_view)
        layout.addWidget(self.reset_button)

        # Create a group box for calculations display
        calculations_group = QGroupBox("Conduit Fill Calculations")
        calc_layout = QVBoxLayout()

        self.conduit_area_label = QLabel("Conduit Area: N/A")
        self.total_cable_area_label = QLabel("Total Cable Area: N/A")
        self.fill_percentage_label = QLabel("Fill Percentage: N/A")
        self.compliance_status_label = QLabel("Compliance: N/A")
        self.max_fill_label = QLabel("Max Allowable Fill: N/A")

        calc_layout.addWidget(self.conduit_area_label)
        calc_layout.addWidget(self.total_cable_area_label)
        calc_layout.addWidget(self.fill_percentage_label)
        calc_layout.addWidget(self.max_fill_label) 
        calc_layout.addWidget(self.compliance_status_label)

        # New additions for cable list and removal
        active_cables_label = QLabel("Active Cables in Conduit:")
        calc_layout.addWidget(active_cables_label)
        self.cable_list_widget = QListWidget()
        self.cable_list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection) 
        calc_layout.addWidget(self.cable_list_widget)

        self.remove_selected_button = QPushButton("Remove Selected Cables")
        self.remove_selected_button.clicked.connect(self.remove_selected_cables_from_gui)
        calc_layout.addWidget(self.remove_selected_button)

        # Conduit Radius Adjustment
        conduit_size_label = QLabel("Conduit Radius (mm):")
        calc_layout.addWidget(conduit_size_label)

        self.conduit_radius_spinbox = QSpinBox()
        self.conduit_radius_spinbox.setRange(50, 500) # Example range
        self.conduit_radius_spinbox.setValue(int(main_current_conduit_radius)) # Use imported initial value
        calc_layout.addWidget(self.conduit_radius_spinbox)

        self.apply_conduit_size_button = QPushButton("Apply Conduit Size")
        self.apply_conduit_size_button.clicked.connect(self.apply_new_conduit_size)
        calc_layout.addWidget(self.apply_conduit_size_button)
        
        calculations_group.setLayout(calc_layout)
        layout.addWidget(calculations_group)

        self.setLayout(layout)
        self.update_calculations_display() # Initial update to populate calculation labels

    def create_color_button(self, text: str, initial_color: QColor, callback: callable) -> QPushButton:
        """
        Creates a QPushButton configured for color selection.

        Args:
            text (str): The text to display on the button.
            initial_color (QColor): The initial color for the color dialog.
            callback (callable): The function to call when a new color is selected.

        Returns:
            QPushButton: The configured button.
        """
        button = QPushButton(text)
        button.clicked.connect(lambda: self.open_color_dialog(initial_color, callback))
        return button

    def open_color_dialog(self, initial_color: QColor, callback: callable):
        """
        Opens a QColorDialog to allow the user to select a color.
        If a valid color is selected, it calls the provided callback function
        with the chosen QColor object.

        Args:
            initial_color (QColor): The color to pre-select in the dialog.
            callback (callable): The function to execute with the selected color.
        """
        color = QColorDialog.getColor(initial_color, self)
        if color.isValid():
            callback(color)

    def set_core_color(self, color: QColor):
        """Updates the core color used for newly spawned single-core cables."""
        self.core_color = color
        # This directly modifies the color in main.py, affecting future single-core cables.
        # TODO: Consider a more robust way to manage color configurations if more types are involved.
        main.CORE_COLORS["single"] = (color.red(), color.green(), color.blue())

    def set_sheath_color(self, color: QColor):
        """Updates the global cable sheath color in main.py."""
        self.sheath_color = color
        main.CABLE_SHEATH_COLOR = (color.red(), color.green(), color.blue())

    def set_background_color(self, color: QColor):
        """Updates the Pygame simulation's background color in main.py."""
        self.background_color = color
        main.BACKGROUND_COLOR = (color.red(), color.green(), color.blue())

    def spawn_cable(self):
        """
        Spawns a new cable in the simulation.
        The cable type is determined by the current selection in `main.input_handler`
        (typically set via keyboard input in the Pygame window).
        The spawn position is also determined by `main.input_handler`, usually near the top.
        The actual spawning is delegated to `main.spawn_cable()`.
        GUI calculation updates are handled by the QTimer.
        """
        # Get outer diameter from the QDoubleSpinBox first, as it's needed for spawn position calculation
        outer_diameter_value = self.outer_diameter_spinbox.value()
        
        # Use the spawn logic from input_handler to be consistent with mouse clicks in Pygame window
        # Pass both conduit radius and the cable's outer diameter
        spawn_pos = main.input_handler.get_spawn_position(main_current_conduit_radius, outer_diameter_value)
        
        # Get cable type from the QComboBox
        selected_cable_type = self.cable_type_combo.currentData()
        
        main.spawn_cable(spawn_pos, selected_cable_type, outer_diameter_value) # Call the refactored main.spawn_cable
        # self.update_calculations_display() # This is now handled by the QTimer

    def reset_view(self):
        """
        Resets the simulation by clearing all cables from the Pygame simulation
        (via `main.reset_view()`) and then immediately updates the calculation
        displays in the GUI to reflect the cleared state.
        """
        main.reset_view() # This should clear main.cables in main.py
        self.update_calculations_display() # Keep for immediate update after reset

    def update_calculations_display(self):
        """
        Recalculates conduit fill, total cable area, and AS/NZS compliance status,
        then updates the respective QLabels in the GUI.
        This method fetches the current list of cables (`main.cables`) from the `main` module
        and uses the dynamic `main.current_conduit_radius` for conduit area calculations.
        It's typically called by the QTimer or after a reset/conduit size change.
        """
        # 1. Calculate and display conduit's total internal area
        # Use the dynamically updated conduit radius from main.py
        conduit_area = calculate_conduit_cross_sectional_area(main_current_conduit_radius) 
        self.conduit_area_label.setText(f"Conduit Area: {conduit_area:.2f} mm²")

        # 2. Prepare cable data for calculations.
        #    The `main.cables` list now stores tuples of (id, Pymunk body, Pymunk shape, CableType enum, outer_diameter).
        #    For calculation, we need a list of tuples: (CableType, outer_diameter).
        current_cables_data_for_calc = [] # Renamed to avoid confusion
        
        # Store current selection(s)
        selected_items_data = [item.data(Qt.UserRole) for item in self.cable_list_widget.selectedItems()]
        
        if hasattr(main, 'cables'): # Check if main.cables exists and is accessible
            self.cable_list_widget.clear() # Clear list before repopulating
            # Cable item in main.cables is now (id, body, shape, cable_type, outer_diameter)
            for cable_id, _body, _shape, cable_type_enum, outer_diameter in main.cables: 
                # For calculation data:
                current_cables_data_for_calc.append((cable_type_enum, outer_diameter))
                
                # For display in QListWidget:
                list_item_text = f"ID: {cable_id} - Type: {cable_type_enum.name} - OD: {outer_diameter:.1f}mm"
                list_widget_item = QListWidgetItem(list_item_text) 
                list_widget_item.setData(Qt.UserRole, cable_id) # Store ID with item
                self.cable_list_widget.addItem(list_widget_item)
            
            # Restore selection(s) after repopulating
            if selected_items_data: # Only proceed if there was a selection
                for i in range(self.cable_list_widget.count()):
                    item = self.cable_list_widget.item(i)
                    if item.data(Qt.UserRole) in selected_items_data:
                        item.setSelected(True)
        
        # 3. Calculate and display total cross-sectional area of all cables
        # The calculate_total_cable_area function will need to be updated to accept this new data format.
        # For now, we assume it's updated or this will cause an error.
        total_cable_area = calculate_total_cable_area(current_cables_data_for_calc)
        self.total_cable_area_label.setText(f"Total Cable Area: {total_cable_area:.2f} mm²")

        # 4. Calculate and display conduit fill percentage
        fill_percentage = calculate_conduit_fill_percentage(total_cable_area, conduit_area)
        self.fill_percentage_label.setText(f"Fill Percentage: {fill_percentage:.2f}%")

        # 5. Check AS/NZS compliance and display status
        num_cables = len(current_cables_data_for_calc) # Use the new list for count
        is_compliant, max_allowable_fill = check_as_nzs_compliance(fill_percentage, num_cables)
        
        self.max_fill_label.setText(f"Max Allowable Fill: {max_allowable_fill:.1f}% (AS/NZS)")
        status_text = "Compliant" if is_compliant else "Non-Compliant"
        self.compliance_status_label.setText(f"Compliance: {status_text}")
        
        # Change text color of compliance status for visual feedback
        if is_compliant:
            self.compliance_status_label.setStyleSheet("color: green")
        else:
            self.compliance_status_label.setStyleSheet("color: red")

    def start_pygame_thread(self):
        """
        Starts the Pygame simulation loop in a separate daemon thread.
        This allows the PySide6 GUI to remain responsive while the simulation runs.
        """
        pygame_thread = threading.Thread(target=main.main)
        pygame_thread.daemon = True # Ensures thread exits when main application exits
        pygame_thread.start()

    def remove_selected_cables_from_gui(self):
        """
        Removes the cables selected in the QListWidget from the simulation.
        It gets the IDs of the selected cables, calls main.remove_cables_by_ids,
        and relies on the QTimer to update the GUI list and calculations.
        """
        selected_items = self.cable_list_widget.selectedItems()
        if not selected_items:
            return # No items selected, do nothing

        ids_to_remove = []
        for item in selected_items:
            ids_to_remove.append(item.data(Qt.UserRole)) # Retrieve the stored cable ID

        if ids_to_remove:
            main.remove_cables_by_ids(ids_to_remove)
            # The QTimer (self.calc_update_timer) will periodically call
            # self.update_calculations_display(), which will refresh the
            # QListWidget and all calculation labels. No direct call needed here.
            
    def apply_new_conduit_size(self):
        """
        Applies the new conduit radius from the QSpinBox to the simulation.
        Calls main.update_simulation_conduit_radius to trigger the change in the physics space.
        The QTimer will handle updating the calculations display.
        """
        new_radius = float(self.conduit_radius_spinbox.value())
        update_simulation_conduit_radius(new_radius)
        # QTimer will call update_calculations_display, which now uses 
        # main.current_conduit_radius for its conduit area calculation.

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Need to ensure QListWidgetItem is available if not using FQCN
    from PySide6.QtWidgets import QListWidgetItem 
    gui = CableGUI()
    gui.show()
    sys.exit(app.exec())