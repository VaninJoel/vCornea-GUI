from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QCheckBox, QComboBox
import math

class ParameterItemWidget(QWidget):
    """
    Composite widget that contains:
      - A value widget (QLineEdit, QCheckBox, or QComboBox) to hold the parameter value.
      - A literature reference dropdown to select the source of the default.
    When a literature reference (other than "custom") is selected, the default value is
    loaded into the value widget. If the user changes the value so that it no longer
    matches the default, the dropdown automatically changes to "custom."
    """
    def __init__(self, param, value, description, default_dict):
        super().__init__()
        self.param = param
        self.description = description
        self.defaults = default_dict if default_dict is not None else {}
        
        # Set up a horizontal layout with no margins
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create the value widget (using similar logic as before)
        self.value_widget = self.create_value_widget(param, value, description)
        layout.addWidget(self.value_widget)
        
        # Create the literature reference dropdown.
        # Options: always "custom" plus any references defined in self.defaults.
        self.ref_dropdown = QComboBox()
        self.ref_dropdown.addItem("custom")
        for ref in sorted(self.defaults.keys()):
            self.ref_dropdown.addItem(ref)
        layout.addWidget(self.ref_dropdown)
        
        # Set initial reference selection based on the current value.
        current_ref = self.find_matching_reference(value)
        self.ref_dropdown.setCurrentText(current_ref)
        
        # When the reference is changed, update the value widget.
        self.ref_dropdown.currentTextChanged.connect(self.on_ref_changed)
        
        # Connect changes from the value widget so that if the user edits it,
        # the dropdown will switch to "custom" if the value no longer matches the default.
        self.setup_value_change_handler()

    def create_value_widget(self, param, value, description):
        # Replicate the logic from your original create_widget() method.
        if param == 'InjuryType':
            widget = QComboBox()
            widget.addItems(['ABLATION', 'CHEMICAL'])
            index = 0 if value else 1
            widget.setCurrentIndex(index)
        elif param == 'SLS_Gaussian_pulse':
            widget = QComboBox()
            widget.addItems(['Droplet', 'Coating'])
            index = 0 if value else 1
            widget.setCurrentIndex(index)
        elif isinstance(value, bool):
            widget = QCheckBox()
            widget.setChecked(value)
        elif isinstance(value, (int, float)):
            widget = QLineEdit(str(value))
        elif isinstance(value, str):
            widget = QLineEdit(value)
        else:
            widget = QLabel("Unsupported type")
        widget.setToolTip(description)
        return widget

    def find_matching_reference(self, value):
        # Look through our defaults to see if any matches the provided value.
        for ref, default_val in self.defaults.items():
            if self.compare_values(value, default_val):
                return ref
        return "custom"
        
    def compare_values(self, v1, v2):
        # Try numeric comparison first; fall back to string comparison.
        try:
            return math.isclose(float(v1), float(v2), rel_tol=1e-9, abs_tol=1e-9)
        except (ValueError, TypeError):
            return str(v1).strip() == str(v2).strip()
            
    def on_ref_changed(self, ref):
        if ref != "custom":
            # If a literature reference is selected, update the value widget
            # to the default value for that reference.
            default_value = self.defaults.get(ref)
            self.set_value(default_value)
            
    def setup_value_change_handler(self):
        # Connect change signals from the value widget.
        if isinstance(self.value_widget, QLineEdit):
            self.value_widget.textChanged.connect(self.on_value_changed)
        elif isinstance(self.value_widget, QCheckBox):
            self.value_widget.stateChanged.connect(lambda _: self.on_value_changed())
        elif isinstance(self.value_widget, QComboBox):
            self.value_widget.currentIndexChanged.connect(lambda _: self.on_value_changed())
            
    def on_value_changed(self):
        # Check whether the current value still matches the default for the selected reference.
        current_ref = self.ref_dropdown.currentText()
        current_value = self.get_value()
        if current_ref != "custom":
            default_value = self.defaults.get(current_ref)
            if not self.compare_values(current_value, default_value):
                # If the value no longer matches, switch the dropdown to "custom"
                self.ref_dropdown.blockSignals(True)
                self.ref_dropdown.setCurrentText("custom")
                self.ref_dropdown.blockSignals(False)
                
    def get_value(self):
        # Return the current value from the value widget.
        if isinstance(self.value_widget, QLineEdit):
            text = self.value_widget.text()
            try:
                # Always attempt to convert text from a line edit to a number.
                f_val = float(text)
                # If it's a whole number, return it as an integer.
                if f_val.is_integer():
                    return int(f_val)
                # Otherwise, return it as a float.
                return f_val
            except ValueError:
                # If conversion fails (e.g., for a non-numeric string), return the text.
                return text
        elif isinstance(self.value_widget, QCheckBox):
            return self.value_widget.isChecked()
        elif isinstance(self.value_widget, QComboBox):
            # For your specific ComboBoxes, return the boolean value
            if self.param == 'InjuryType':
                return self.value_widget.currentText() == 'ABLATION'
            elif self.param == 'SLS_Gaussian_pulse':
                return self.value_widget.currentText() == 'Droplet'
            return self.value_widget.currentText()
        else:
            return None
            
    def set_value(self, value):
        # Set the value widget's content to the given value.
        if isinstance(self.value_widget, QLineEdit):
            self.value_widget.blockSignals(True)
            self.value_widget.setText(str(value))
            self.value_widget.blockSignals(False)
        elif isinstance(self.value_widget, QCheckBox):
            self.value_widget.blockSignals(True)
            self.value_widget.setChecked(bool(value))
            self.value_widget.blockSignals(False)
        elif isinstance(self.value_widget, QComboBox):
            self.value_widget.blockSignals(True)
            index = self.value_widget.findText(str(value))
            if index != -1:
                self.value_widget.setCurrentIndex(index)
            self.value_widget.blockSignals(False)

    def on_value_changed(self):
        # Determine the matching reference for the current value
        new_ref = self.find_matching_reference(self.get_value())
        # Only update if it differs from the current selection
        if new_ref != self.ref_dropdown.currentText():
            self.ref_dropdown.blockSignals(True)
            self.ref_dropdown.setCurrentText(new_ref)
            self.ref_dropdown.blockSignals(False)
