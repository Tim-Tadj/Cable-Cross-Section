import sys
import threading
import signal
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QColorDialog,
    QLabel,
    QSpinBox,
    QHBoxLayout,
    QGroupBox,
    QListWidget,
    QAbstractItemView,
    QComboBox,
    QDoubleSpinBox,
    QListWidgetItem,
    QCheckBox,
    QLineEdit,
)
from PySide6.QtGui import QColor, QDoubleValidator
from PySide6.QtCore import Qt, QTimer, QLocale
import main  # Import your main.py file
from main import input_handler  # use input_handler from main
# Qt.UserRole is used with item.data() / item.setData()
from calculations import (
    calculate_conduit_cross_sectional_area,
    calculate_total_cable_area,
    calculate_conduit_fill_percentage,
    check_as_nzs_compliance
)
# CONDUIT_RADIUS is now main_current_conduit_radius, DEFAULT_CONDUIT_RADIUS is in config
from config import CORE_RADIUS, SHEATH_THICKNESS, MARGIN, CableType, DEFAULT_CONDUIT_DIAMETER, CORE_INSULATION_THICKNESS 

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

        # Initialize flags before building UI since recompute may be called during setup
        self.control_by_od = False
        self._updating_fields = False
        self.outer_diameter_step = 0.5
        self.outer_diameter_min = 0.0
        self.outer_diameter_max = 2000.0
        self._last_outer_diameter_value = 0.0
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

        self._pygame_thread = None
        if hasattr(main, 'register_exit_callback'):
            main.register_exit_callback(self._handle_simulation_exit_request)

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
        self.cable_type_combo.currentIndexChanged.connect(self.recompute_outer_diameter)

        # Core Area Input
        self.core_area_label = QLabel("Core Area (mm²):")
        layout.addWidget(self.core_area_label)
        self.core_area_spinbox = QDoubleSpinBox()
        self.core_area_spinbox.setRange(0.5, 1000.0)
        self.core_area_spinbox.setValue(25.0)
        self.core_area_spinbox.setSingleStep(1.0)
        layout.addWidget(self.core_area_spinbox)
        self.core_area_spinbox.valueChanged.connect(self.recompute_outer_diameter)

        # Sheath Thickness Input
        self.sheath_label = QLabel("Sheath Thickness (mm):")
        layout.addWidget(self.sheath_label)
        self.sheath_spinbox = QDoubleSpinBox()
        self.sheath_spinbox.setRange(0.1, 20.0)
        self.sheath_spinbox.setValue(SHEATH_THICKNESS)
        self.sheath_spinbox.setSingleStep(0.1)
        layout.addWidget(self.sheath_spinbox)
        self.sheath_spinbox.valueChanged.connect(self.recompute_outer_diameter)

        # Inner Sheath (Core Insulation) Thickness Input
        self.inner_sheath_label = QLabel("Inner Sheath (Core Insulation) (mm):")
        layout.addWidget(self.inner_sheath_label)
        self.inner_sheath_spinbox = QDoubleSpinBox()
        self.inner_sheath_spinbox.setRange(0.0, 10.0)
        self.inner_sheath_spinbox.setValue(CORE_INSULATION_THICKNESS)
        self.inner_sheath_spinbox.setSingleStep(0.1)
        layout.addWidget(self.inner_sheath_spinbox)
        self.inner_sheath_spinbox.valueChanged.connect(self.recompute_outer_diameter)

        # Margin Input
        self.margin_label = QLabel("Margin (mm):")
        layout.addWidget(self.margin_label)
        self.margin_spinbox = QDoubleSpinBox()
        self.margin_spinbox.setRange(0.0, 20.0)
        self.margin_spinbox.setValue(MARGIN)
        self.margin_spinbox.setSingleStep(0.1)
        layout.addWidget(self.margin_spinbox)
        self.margin_spinbox.valueChanged.connect(self.recompute_outer_diameter)

        # Outer Diameter controls (manual input with optional incremental buttons)
        self.outer_diameter_label = QLabel("Outer Diameter (mm):")
        layout.addWidget(self.outer_diameter_label)
        od_row = QHBoxLayout()
        self.outer_diameter_edit = QLineEdit()
        self.outer_diameter_edit.setAlignment(Qt.AlignRight)
        self.outer_diameter_edit.setText("0.00")
        self.outer_diameter_edit.setFocusPolicy(Qt.StrongFocus)
        od_validator = QDoubleValidator(0.0, 2000.0, 2, self.outer_diameter_edit)
        od_validator.setNotation(QDoubleValidator.StandardNotation)
        od_validator.setLocale(QLocale.c())
        self.outer_diameter_edit.setValidator(od_validator)
        self.outer_diameter_edit.editingFinished.connect(self.on_outer_diameter_editing_finished)
        od_row.addWidget(self.outer_diameter_edit)

        self.od_minus_button = QPushButton("-")
        self.od_minus_button.setFixedWidth(32)
        self.od_minus_button.clicked.connect(lambda: self.adjust_outer_diameter(-self.outer_diameter_step))
        od_row.addWidget(self.od_minus_button)

        self.od_plus_button = QPushButton("+")
        self.od_plus_button.setFixedWidth(32)
        self.od_plus_button.clicked.connect(lambda: self.adjust_outer_diameter(self.outer_diameter_step))
        od_row.addWidget(self.od_plus_button)

        layout.addLayout(od_row)
        self.recompute_outer_diameter()

        # Control by OD toggle
        od_toggle_row = QHBoxLayout()
        self.control_by_od_checkbox = QCheckBox("Control by OD (scale proportions)")
        self.control_by_od_checkbox.toggled.connect(self.toggle_control_by_od)
        od_toggle_row.addWidget(self.control_by_od_checkbox)
        layout.addLayout(od_toggle_row)
        # Initialize manual control off by default
        self.toggle_control_by_od(False)

        # Spawn Cable Button
        self.spawn_button = QPushButton("Spawn Cable")
        self.spawn_button.clicked.connect(self.spawn_cable)
        layout.addWidget(self.spawn_button)

        # Reset View Button
        self.reset_button = QPushButton("Reset View")
        self.reset_button.clicked.connect(self.reset_view)
        layout.addWidget(self.reset_button)

        # Zoom Control
        zoom_row = QHBoxLayout()
        zoom_label = QLabel("Zoom:")
        self.zoom_spinbox = QDoubleSpinBox()
        self.zoom_spinbox.setRange(0.25, 10.0)
        self.zoom_spinbox.setSingleStep(0.1)
        # Initialize from main if present
        initial_zoom = float(getattr(main, 'render_zoom', 1.0))
        self.zoom_spinbox.setValue(initial_zoom)
        self.zoom_spinbox.valueChanged.connect(self.apply_zoom_change)
        zoom_row.addWidget(zoom_label)
        zoom_row.addWidget(self.zoom_spinbox)
        layout.addLayout(zoom_row)

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

        # Conduit Diameter Adjustment (user-facing)
        conduit_size_label = QLabel("Conduit Diameter (mm):")
        calc_layout.addWidget(conduit_size_label)

        self.conduit_radius_spinbox = QSpinBox()
        self.conduit_radius_spinbox.setRange(50, 500) # Example range
        # Initialize spinbox with current diameter value exposed by main
        self.conduit_radius_spinbox.setValue(int(getattr(main, 'current_conduit_diameter', DEFAULT_CONDUIT_DIAMETER))) # Use dynamic value if present
        calc_layout.addWidget(self.conduit_radius_spinbox)

        self.apply_conduit_size_button = QPushButton("Apply Conduit Size")
        self.apply_conduit_size_button.clicked.connect(self.apply_new_conduit_size)
        calc_layout.addWidget(self.apply_conduit_size_button)
        
        calculations_group.setLayout(calc_layout)
        layout.addWidget(calculations_group)

        self.setLayout(layout)
        self.update_calculations_display() # Initial update to populate calculation labels

    def apply_zoom_change(self, value: float):
        """Apply zoom changes to the Pygame render via main.set_render_zoom."""
        if hasattr(main, 'set_render_zoom'):
            main.set_render_zoom(float(value))

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
        # Get outer diameter value for spawn position calculation
        outer_diameter_value = self.clamp_outer_diameter(self.get_outer_diameter_value())
        
        # Use the spawn logic from input_handler to be consistent with mouse clicks in Pygame window
        # Pass both conduit radius and the cable's outer diameter
        # Convert main's user-facing diameter to radius for the spawn position calculation
        spawn_pos = main.input_handler.get_spawn_position(getattr(main, 'current_conduit_diameter', DEFAULT_CONDUIT_DIAMETER) / 2.0, outer_diameter_value)
        
        # Get cable type from the QComboBox
        selected_cable_type = self.cable_type_combo.currentData()

        # Compute core radius from area to pass to main.spawn_cable
        import math
        core_area = self.core_area_spinbox.value()
        core_radius = math.sqrt(core_area / math.pi)
        sheath = self.sheath_spinbox.value()
        inner_ins = self.inner_sheath_spinbox.value()
        margin = self.margin_spinbox.value()
        main.spawn_cable(spawn_pos, selected_cable_type, outer_diameter_value, core_radius, sheath, margin, inner_ins)
        # self.update_calculations_display() # This is now handled by the QTimer

    def recompute_outer_diameter(self):
        if self.control_by_od:
            # In manual OD mode, do not overwrite the user's OD selection
            return
        # Compute OD from core area, sheath, margin, and cable type
        from cable import compute_outer_diameter_for_core_area
        selected_cable_type = self.cable_type_combo.currentData()
        core_area = self.core_area_spinbox.value()
        sheath = self.sheath_spinbox.value()
        inner_ins = self.inner_sheath_spinbox.value()
        margin = self.margin_spinbox.value()
        if selected_cable_type is None or core_area <= 0:
            self.set_outer_diameter_display(0.0)
            return
        od = compute_outer_diameter_for_core_area(selected_cable_type, core_area, sheath, margin, inner_ins)
        self.set_outer_diameter_display(od)

    def toggle_control_by_od(self, checked: bool):
        self.control_by_od = bool(checked)
        # Toggle OD editability and step buttons
        self.outer_diameter_edit.setPlaceholderText("Type OD and press Enter" if self.control_by_od else "")
        # Keep the field interactive at all times; just visually hint using palette
        if self.control_by_od:
            self.outer_diameter_edit.setStyleSheet("")
        else:
            self.outer_diameter_edit.setStyleSheet("background-color: palette(alternate-base);")
        self.od_minus_button.setEnabled(self.control_by_od)
        self.od_plus_button.setEnabled(self.control_by_od)
        if not self.control_by_od:
            # Sync OD back to computed value
            self.recompute_outer_diameter()
        else:
            # Ensure text is formatted when enabling manual mode
            self.set_outer_diameter_display(self.get_outer_diameter_value())
        self.outer_diameter_edit.setFocusPolicy(Qt.StrongFocus)

    def apply_manual_outer_diameter(self, new_value: float, update_display: bool = True):
        # Apply manual OD scaling when in control-by-OD mode
        if not self.control_by_od or self._updating_fields:
            return
        new_value = self.clamp_outer_diameter(float(new_value))
        from cable import compute_outer_diameter_for_core_area
        selected_cable_type = self.cable_type_combo.currentData()
        if selected_cable_type is None:
            return
        # Compute current OD based on present parameters to establish scale factor
        core_area = self.core_area_spinbox.value()
        sheath = self.sheath_spinbox.value()
        inner_ins = self.inner_sheath_spinbox.value()
        margin = self.margin_spinbox.value()
        current_od = compute_outer_diameter_for_core_area(selected_cable_type, core_area, sheath, margin, inner_ins)
        if current_od <= 0:
            return
        scale = float(new_value) / float(current_od)
        if scale <= 0:
            return
        # Scale parameters proportionally: radii scale by s; areas scale by s^2
        new_core_area = core_area * (scale ** 2)
        new_sheath = sheath * scale
        new_inner = inner_ins * scale
        new_margin = margin * scale
        # Apply without recursive loops
        prev_flag = self._updating_fields
        self._updating_fields = True
        try:
            self.core_area_spinbox.setValue(new_core_area)
            self.sheath_spinbox.setValue(new_sheath)
            self.inner_sheath_spinbox.setValue(new_inner)
            self.margin_spinbox.setValue(new_margin)
        finally:
            self._updating_fields = prev_flag
        if update_display:
            self.set_outer_diameter_display(new_value)

    def on_outer_diameter_editing_finished(self):
        # When typing and pressing enter/defocusing, apply scaling once with the final value
        if not self.control_by_od or self._updating_fields:
            return
        value = self.clamp_outer_diameter(self.get_outer_diameter_value())
        self.apply_manual_outer_diameter(value)

    def get_outer_diameter_value(self) -> float:
        text = self.outer_diameter_edit.text().strip()
        if not text:
            return self._last_outer_diameter_value
        try:
            value = float(text)
        except ValueError:
            value = self._last_outer_diameter_value
        return value

    def clamp_outer_diameter(self, value: float) -> float:
        return max(self.outer_diameter_min, min(self.outer_diameter_max, float(value)))

    def adjust_outer_diameter(self, delta: float):
        if not self.control_by_od:
            return
        current = self.clamp_outer_diameter(self.get_outer_diameter_value())
        new_value = self.clamp_outer_diameter(current + delta)
        self.apply_manual_outer_diameter(new_value)

    def set_outer_diameter_display(self, value: float):
        self._last_outer_diameter_value = float(value)
        prev_flag = self._updating_fields
        self._updating_fields = True
        try:
            self.outer_diameter_edit.setText(f"{float(value):.2f}")
        finally:
            self._updating_fields = prev_flag

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
        # Use the dynamically updated conduit diameter from main.py and convert to radius for the calculation
        conduit_area = calculate_conduit_cross_sectional_area(getattr(main, 'current_conduit_diameter', DEFAULT_CONDUIT_DIAMETER) / 2.0)
        self.conduit_area_label.setText(f"Conduit Area: {conduit_area:.2f} mm²")

        # 2. Prepare cable data for calculations.
        #    The `main.cables` list now stores tuples of (id, Pymunk body, Pymunk shape, CableType enum, outer_diameter).
        #    For calculation, we need a list of tuples: (CableType, outer_diameter).
        current_cables_data_for_calc = [] # Renamed to avoid confusion
        
        # Store current selection(s)
        selected_items_data = [item.data(Qt.UserRole) for item in self.cable_list_widget.selectedItems()]
        
        if hasattr(main, 'cables'): # Check if main.cables exists and is accessible
            self.cable_list_widget.clear() # Clear list before repopulating
            # Cable item in main.cables is now (id, body, shape, cable_type, outer_diameter, core_radius, sheath, margin)
            for cable_entry in main.cables:
                # Unpack safely to support older tuple sizes
                if len(cable_entry) >= 5:
                    cable_id = cable_entry[0]
                    cable_type_enum = cable_entry[3]
                    outer_diameter = cable_entry[4]
                else:
                    # Fallback for older tuple formats
                    cable_id, _body, _shape, cable_type_enum, outer_diameter = cable_entry
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
        self._pygame_thread = pygame_thread
        if hasattr(main, 'set_simulation_thread'):
            main.set_simulation_thread(pygame_thread)

    def _handle_simulation_exit_request(self):
        """Callback from the simulation thread when it finishes or is closed."""
        QTimer.singleShot(0, self._quit_application)

    def _quit_application(self):
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def closeEvent(self, event):
        """Ensure the simulation thread stops when the GUI window closes."""
        if hasattr(main, 'request_simulation_shutdown'):
            main.request_simulation_shutdown()
        if hasattr(main, 'join_simulation_thread'):
            main.join_simulation_thread(2.0)
        super().closeEvent(event)

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
        # Value in the spinbox represents diameter (user-facing)
        new_diameter = float(self.conduit_radius_spinbox.value())
        # Call the diameter-based update function in main
        if hasattr(main, 'update_simulation_conduit_diameter'):
            main.update_simulation_conduit_diameter(new_diameter)
        else:
            # Fall back to the radius-based API if needed
            if hasattr(main, 'update_simulation_conduit_radius'):
                main.update_simulation_conduit_radius(new_diameter / 2.0)
        # QTimer will call update_calculations_display, which now uses
        # main.current_conduit_radius for its conduit area calculation.

if __name__ == '__main__':
    app = QApplication(sys.argv)

    def _handle_sigint(sig, frame):
        if hasattr(main, 'request_simulation_shutdown'):
            main.request_simulation_shutdown()
        app.quit()

    signal.signal(signal.SIGINT, _handle_sigint)

    gui = CableGUI()
    gui.show()

    try:
        exit_code = app.exec()
    except KeyboardInterrupt:
        exit_code = 0
    finally:
        if hasattr(main, 'request_simulation_shutdown'):
            main.request_simulation_shutdown()
        if hasattr(main, 'join_simulation_thread'):
            main.join_simulation_thread(2.0)

    sys.exit(exit_code)
