from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, QSpinBox,
                           QMessageBox, QHBoxLayout, QLabel, QPushButton, QScrollArea, QProgressBar,
                           QFileDialog, QProgressDialog , QComboBox, QGroupBox, QCheckBox, QLineEdit)
from PyQt5.QtCore import Qt, QThread
from gui.simulation_worker import SimulationWorker
from gui.widgets.collapsible_group import CollapsibleGroupBox
from gui.widgets.parameter_item import ParameterItemWidget
from config.parameter_structure import parameter_structure
from config.display_mapping import display_name_mapping
from analysis.plot_manager import PlotManager
from utils.file_handlers import (load_parameter_defaults, load_original_parameters,
                               read_parameters_file, save_parameters_file)
from pathlib import Path
import sys
import os
import json
import subprocess
import shutil
from PyQt5.QtWidgets import (QApplication, QLineEdit, QFileDialog)


class ParameterGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VCornea Virtual Lab")
        self.setGeometry(100, 100, 900, 700)

        self.model_mapping = {
            "v1 Epi - Paper Version": "Local/Project/paper_version",
            "v1 Epi - Stem Cells Only": "Local/Project/paper_version_STEM_ONLY",           
        }
       
        self.current_script_directory = Path(__file__).parent.parent.absolute()
        self.gui_config_file = self.current_script_directory / "gui_config.json"
        self.config_directory = self.current_script_directory / "config"
        self.defaults_file_path = self.config_directory / "parameter_defaults.json"
        self.original_params_path = self.config_directory / "original_parameters.json"
        
        self.parameter_widgets = {}
        self.is_injury_checkbox = None
        self.injury_parameter_widgets = []
        self.injury_type_widget = None
        self.wound_parameters_group_boxes = {}        
        self.running_threads = []
        self.last_simulation_output_dir = None

        self.sweep_parameters = {}
        self.base_parameters = {}
        self.parameter_combinations = []
        self.completed_combinations = 0
        self.total_combinations = 0
        self.simulation_threads = [] 
        self.sweep_output_folder = None
        
        try:            
            self.global_defaults, self.cell_type_defaults = load_parameter_defaults(self.defaults_file_path)
            self.parameters = load_original_parameters(self.original_params_path)            
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                f"Failed to initialize required configurations: {str(e)}")           
            sys.exit(1)
        
        self.init_ui()
        self.load_gui_config()  

    def init_ui(self):
        # Create main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        path_groupbox = QGroupBox("Configuration")
        path_group_layout = QVBoxLayout()
        path_groupbox.setLayout(path_group_layout)

        # --- vCornea Repository Path ---
        path_selection_layout = QHBoxLayout()
        path_label = QLabel("vCornea Repository Path:")
        self.model_path_line_edit = QLineEdit()
        self.model_path_line_edit.setPlaceholderText("Select the root path of your cloned vCornea repository...")
        self.model_path_line_edit.editingFinished.connect(self.save_gui_config)
        browse_repo_button = QPushButton("Browse...")
        browse_repo_button.clicked.connect(self.browse_for_model_path)
        path_selection_layout.addWidget(path_label)
        path_selection_layout.addWidget(self.model_path_line_edit)
        path_selection_layout.addWidget(browse_repo_button)
        path_group_layout.addLayout(path_selection_layout)
        
        # --- Model Version Selection ---
        model_selection_layout = QHBoxLayout()
        model_label = QLabel("Select Model Version:")
        self.model_selection_combo = QComboBox()
        self.model_selection_combo.addItems(self.model_mapping.keys())
        self.model_selection_combo.currentIndexChanged.connect(self.on_model_selection_change)
        model_selection_layout.addWidget(model_label)
        model_selection_layout.addWidget(self.model_selection_combo)
        path_group_layout.addLayout(model_selection_layout)

        # --- Conda Environment Name ---
        conda_env_layout = QHBoxLayout()
        conda_label = QLabel("Conda Environment Name:")
        self.conda_env_line_edit = QLineEdit("v_cornea") 
        self.conda_env_line_edit.setToolTip("The name of the conda environment where CC3D is installed.")
        self.conda_env_line_edit.editingFinished.connect(self.save_gui_config)
        conda_env_layout.addWidget(conda_label)
        conda_env_layout.addWidget(self.conda_env_line_edit)
        path_group_layout.addLayout(conda_env_layout)

        # --- Output Directory Selection ---
        output_dir_layout = QHBoxLayout()
        output_label = QLabel("Output Directory:")
        self.output_dir_line_edit = QLineEdit(str(self.current_script_directory / "simulation_outputs"))
        self.output_dir_line_edit.editingFinished.connect(self.save_gui_config)
        browse_output_button = QPushButton("Browse...")
        browse_output_button.clicked.connect(self.browse_for_output_dir)
        output_dir_layout.addWidget(output_label)
        output_dir_layout.addWidget(self.output_dir_line_edit)
        output_dir_layout.addWidget(browse_output_button)
        path_group_layout.addLayout(output_dir_layout)

        # --- Custom Run Name ---
        run_name_layout = QHBoxLayout()
        run_name_label = QLabel("Custom Run/Sweep Name (Optional):")
        self.run_name_line_edit = QLineEdit()
        self.run_name_line_edit.setPlaceholderText("e.g., 'SLS_Concentration_Test'")
        run_name_layout.addWidget(run_name_label)
        run_name_layout.addWidget(self.run_name_line_edit)
        path_group_layout.addLayout(run_name_layout)

        main_layout.addWidget(path_groupbox)
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # --- Sweep Controls ---
        sweep_group = QGroupBox("Parameter Sweep / Replicate Settings")
        sweep_layout = QHBoxLayout() # Use QHBoxLayout for a single line

        replicate_label = QLabel("Number of Replicates per Run/Combination:")
        self.replicate_input = QSpinBox()
        self.replicate_input.setRange(1, 100)
        self.replicate_input.setValue(1) # Default to 1 replicate
        sweep_layout.addWidget(replicate_label)
        sweep_layout.addWidget(self.replicate_input)
        sweep_group.setLayout(sweep_layout)
        main_layout.addWidget(sweep_group)

        self.create_tabs()

        # --- Add Progress Bar ---
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False) 
        main_layout.addWidget(self.progress_bar)


        # --- Button Layout ---
        button_layout = QHBoxLayout()
        
        self.run_simulation_button = QPushButton("Run Simulation")
        self.run_simulation_button.clicked.connect(self.run_simulation)

        self.cancel_button = QPushButton("Cancel All Runs")
        self.cancel_button.setEnabled(False)  # Disabled by default
        self.cancel_button.clicked.connect(self.cancel_all_simulations)
        
        save_button = QPushButton("Save Parameters")
        save_button.clicked.connect(self.save_parameters)
        
        export_button = QPushButton("Export Parameters")
        export_button.clicked.connect(self.export_parameters)
        
        import_button = QPushButton("Import Parameters")
        import_button.clicked.connect(self.import_parameters)
        
        plot_results_button = QPushButton("Plot Results")
        plot_results_button.clicked.connect(self.plot_results)

        reset_button = QPushButton("Reset to Original")
        reset_button.clicked.connect(self.reset_parameters)

        button_layout.addWidget(self.run_simulation_button)        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(plot_results_button)
        button_layout.addWidget(save_button)
        button_layout.addWidget(export_button)
        button_layout.addWidget(import_button)
        button_layout.addWidget(reset_button)

        main_layout.addLayout(button_layout)

        # --- Initialize Status Bar ---
        self.statusBar().showMessage("Ready")

    def convert_to_number(self, val):
        """Try to convert a string to a float (or int if it is an integer). If not possible, return val as is."""
        try:
            f = float(val)
            # If the float is effectively an integer, return it as an int
            if f.is_integer():
                return int(f)
            else:
                return f
        except (ValueError, TypeError):
            return val

    def read_parameters(self, file_path):
        parameters = {}
        with open(file_path, 'r') as file:
            content = file.readlines()
            for line in content:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split('=', 1)
                if len(parts) == 2:
                    key, value = parts
                    key = key.strip()
                    value = value.strip()
                    try:
                        parameters[key] = eval(value)
                    except:
                        parameters[key] = value

        # Convert MCS back to days for GUI display
        if "SimTime" in parameters:
            parameters["SimTime"] = parameters["SimTime"] / 240.0
        if "InjuryTime" in parameters:
            parameters["InjuryTime"] = parameters["InjuryTime"] / 240.0

        return parameters
    
    def load_default_parameters(self):
        """
        Load the default parameter values from a JSON file.
        The file is expected to have a structure with two top-level keys:
          - "global": contains default values for parameters that are not cell type specific.
          - "cell_type": contains defaults grouped by cell type (e.g., STEM, BASAL, etc.)
        Each parameter mapping can have multiple references (e.g., "foo", "bar") and a "default" flag.
        This method returns two dictionaries: global_defaults and cell_type_defaults.
        In the dictionaries passed to the widgets, the "default" key is removed.
        """
        defaults_file = Path(__file__).parent.absolute() / "parameter_defaults.json"
        try:
            with open(defaults_file, "r") as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load default parameters file: {str(e)}")
            data = {"global": {}, "cell_type": {}}
        
        # Remove the "default" key from each parameter mapping.
        def clean_defaults(param_dict):
            cleaned = {}
            for param, ref_dict in param_dict.items():
                cleaned[param] = {k: v for k, v in ref_dict.items() if k != "default"}
            return cleaned

        global_defaults = clean_defaults(data.get("global", {}))
        cell_type_defaults = {}
        for cell_type, params in data.get("cell_type", {}).items():
            cell_type_defaults[cell_type] = clean_defaults(params)
        return global_defaults, cell_type_defaults

    def create_tabs(self):
        for main_category, subcategories in parameter_structure.items():
            tab = QWidget()
            tab_layout = QVBoxLayout()
            tab.setLayout(tab_layout)

            # At the start of each tab, add a header for tab‐level default reversion.
            default_layout = QHBoxLayout()
            default_ref_label = QLabel("Default Reference:")

            # Build a union of references from the global defaults.
            all_refs = set()
            for param, ref_dict in self.global_defaults.items():
                all_refs.update(ref_dict.keys())
            all_refs = sorted(all_refs)

            default_combo = QComboBox()
            # Optionally, you can add "custom" as a placeholder, but for reversion purposes you
            # may want to force a valid reference selection.
            default_combo.addItems(all_refs)  

            revert_button = QPushButton("Revert to Defaults")
            # When the button is clicked, call revert_tab_to_defaults with the current tab name and selected reference.
            revert_button.clicked.connect(
                lambda _, tab_name=main_category, combo=default_combo: self.revert_tab_to_defaults(tab_name, combo.currentText())
            )

            default_layout.addWidget(default_ref_label)
            default_layout.addWidget(default_combo)
            default_layout.addWidget(revert_button)
            tab_layout.addLayout(default_layout)
            # # Add a default reference dropdown and reversion button at the top of the tab
            # default_layout = QHBoxLayout()
            # default_ref_label = QLabel("Default Reference:")
            # default_combo = QComboBox()
            # default_combo.addItems(["foo"])  # For now only "foo"
            # revert_button = QPushButton("Revert to Defaults")
            # # Capture the current tab name and the default combo for use in the lambda:
            # revert_button.clicked.connect(lambda _, tab_name=main_category, combo=default_combo: self.revert_tab_to_defaults(tab_name, combo.currentText()))
            # default_layout.addWidget(default_ref_label)
            # default_layout.addWidget(default_combo)
            # default_layout.addWidget(revert_button)
            # tab_layout.addLayout(default_layout)            
            
            scroll_area = QScrollArea()
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout()
            scroll_widget.setLayout(scroll_layout)

            if main_category == "Cells Parameters":
                for subcategory, params in subcategories.items():
                    # Use CollapsibleGroupBox
                    group_box = CollapsibleGroupBox(subcategory)
                    group_layout = QVBoxLayout()
                    group_box.content_area.setLayout(group_layout)

                    # --- Add cell type–specific reversion controls at the top of this group ---
                    cell_reversion_layout = QHBoxLayout()
                    cell_reversion_label = QLabel("Cell Type Default Reference:")
                    cell_reversion_combo = QComboBox()
                    # Get union of references available for this cell type, if any.
                    ref_set = set()
                    if subcategory in self.cell_type_defaults:
                        for default_dict in self.cell_type_defaults[subcategory].values():
                            ref_set.update(default_dict.keys())
                    refs = sorted(ref_set)
                    cell_reversion_combo.addItem("custom")
                    for ref in refs:
                        cell_reversion_combo.addItem(ref)
                    revert_cell_type_button = QPushButton(f"Revert {subcategory} to Defaults")
                    # Capture current subcategory and its parameter dict in the lambda:
                    revert_cell_type_button.clicked.connect(lambda _, subcat=subcategory, combo=cell_reversion_combo, params=params: self.revert_cell_type_defaults(subcat, combo.currentText(), params))
                    cell_reversion_layout.addWidget(cell_reversion_label)
                    cell_reversion_layout.addWidget(cell_reversion_combo)
                    cell_reversion_layout.addWidget(revert_cell_type_button)
                    group_layout.addLayout(cell_reversion_layout)

                    for param, description in params.items():
                        if param in self.parameters:
                            # widget = self.create_widget(param, self.parameters[param], description)
                            if subcategory in self.cell_type_defaults and param in self.cell_type_defaults[subcategory]:
                                defaults_for_param = self.cell_type_defaults[subcategory][param]
                            else:
                                defaults_for_param = self.global_defaults.get(param, {})
                            widget = ParameterItemWidget(param, self.parameters[param],
                                                          description, defaults_for_param)
                            self.parameter_widgets[param] = widget
                            label = QLabel(display_name_mapping.get(param, param))
                            label.setToolTip(description)
                            param_layout = QHBoxLayout()
                            param_layout.addWidget(label)
                            param_layout.addWidget(widget)
                            group_layout.addLayout(param_layout)

                    scroll_layout.addWidget(group_box)

            elif main_category == "Wound Parameters":
                for subcategory, params in subcategories.items():
                    group_box = QGroupBox(subcategory)
                    group_layout = QVBoxLayout()
                    group_box.setLayout(group_layout)

                    if subcategory == "ENABLES INJURY, DEFINE TIME AND TYPE OF INJURY":
                        for param, description in params.items():
                            if param in self.parameters:
                                if param == "IsInjury":
                                    # Create a checkbox for 'IsInjury'
                                    widget = QCheckBox()
                                    widget.setChecked(self.parameters[param])
                                    widget.stateChanged.connect(self.update_wound_parameters_enablement)
                                    self.is_injury_checkbox = widget
                                elif param == "InjuryType":
                                    widget = ParameterItemWidget(param, self.parameters[param],
                                 description, self.global_defaults.get(param, {}))
                                    # Connect the inner QComboBox's currentIndexChanged signal
                                    if hasattr(widget.value_widget, "currentIndexChanged"):
                                        widget.value_widget.currentIndexChanged.connect(self.update_wound_parameters_visibility)
                                    self.injury_type_widget = widget
                                    self.injury_parameter_widgets.append(widget)                                    
                                else:
                                    # widget = self.create_widget(param, self.parameters[param], description)
                                    widget = ParameterItemWidget(param, self.parameters[param],
                                                          description, self.global_defaults.get(param, {}))
                                self.parameter_widgets[param] = widget
                                label = QLabel(display_name_mapping.get(param, param))
                                label.setToolTip(description)
                                param_layout = QHBoxLayout()
                                param_layout.addWidget(label)
                                param_layout.addWidget(widget)
                                group_layout.addLayout(param_layout)

                        scroll_layout.addWidget(group_box)

                    elif subcategory in ["ABLATION", "CHEMICAL"]:
                        for param, description in params.items():
                            if param in self.parameters:
                                # widget = self.create_widget(param, self.parameters[param], description)
                                widget = ParameterItemWidget(param, self.parameters[param],
                                                          description, self.global_defaults.get(param, {}))
                                self.parameter_widgets[param] = widget
                                label = QLabel(display_name_mapping.get(param, param))
                                label.setToolTip(description)
                                param_layout = QHBoxLayout()
                                param_layout.addWidget(label)
                                param_layout.addWidget(widget)
                                group_layout.addLayout(param_layout)
                        scroll_layout.addWidget(group_box)
                        # Store the group box for visibility control
                        self.wound_parameters_group_boxes[subcategory] = group_box
                # Set initial visibility
                self.update_wound_parameters_visibility()
            
            elif main_category == "Plots":
                # Create the main QGroupBox or CollapsibleGroupBox for "DATA COLECTION AND REAL-TIME PLOTS"
                for subcategory, params in subcategories.items():
                    group_box = QGroupBox(subcategory)
                    group_layout = QVBoxLayout()
                    group_box.setLayout(group_layout)
                    
                    # Existing code that creates the checkboxes or widgets for "CellCount", "ThicknessPlot", etc.
                    for param, description in params.items():
                        if param in self.parameters:
                            widget = ParameterItemWidget(param, self.parameters[param],
                                                        description, self.global_defaults.get(param, {}))
                            self.parameter_widgets[param] = widget
                            label = QLabel(display_name_mapping.get(param, param))
                            label.setToolTip(description)
                            param_layout = QHBoxLayout()
                            param_layout.addWidget(label)
                            param_layout.addWidget(widget)
                            group_layout.addLayout(param_layout)
                    
                    # ------------------------------
                    # Now add TWO combo boxes for scale:
                    #   1) Cell Count Scale
                    #   2) Thickness Scale
                    # ------------------------------
                    
                    # Cell Count Scale
                    cc_scale_label = QLabel("Cell Count Scale:")
                    self.cell_count_scale_combo = QComboBox()
                    self.cell_count_scale_combo.addItems(["Absolute", "Percentage", "PctChangeFromMean"])
                    
                    # If you want to remember the previous user selection (self.parameters["CellCountScale"]),
                    # set the combo box to that index. Otherwise default to "Absolute" or whatever you like.
                    current_cc_scale = self.parameters.get("CellCountScale", "Absolute")
                    idx_cc = self.cell_count_scale_combo.findText(current_cc_scale)
                    if idx_cc >= 0:
                        self.cell_count_scale_combo.setCurrentIndex(idx_cc)
                    
                    # When changed, store in self.parameters
                    self.cell_count_scale_combo.currentTextChanged.connect(
                        lambda val: self.parameters.update({"CellCountScale": val})
                    )
                    
                    # Layout for cell count scale
                    cc_scale_layout = QHBoxLayout()
                    cc_scale_layout.addWidget(cc_scale_label)
                    cc_scale_layout.addWidget(self.cell_count_scale_combo)
                    group_layout.addLayout(cc_scale_layout)
                    
                    # Thickness Scale
                    thickness_scale_label = QLabel("Thickness Scale:")
                    self.thickness_scale_combo = QComboBox()
                    self.thickness_scale_combo.addItems(["Absolute", "Percentage", "PctChangeFromMean"])
                    
                    current_th_scale = self.parameters.get("ThicknessScale", "Absolute")
                    idx_th = self.thickness_scale_combo.findText(current_th_scale)
                    if idx_th >= 0:
                        self.thickness_scale_combo.setCurrentIndex(idx_th)
                    
                    self.thickness_scale_combo.currentTextChanged.connect(
                        lambda val: self.parameters.update({"ThicknessScale": val})
                    )
                    
                    th_scale_layout = QHBoxLayout()
                    th_scale_layout.addWidget(thickness_scale_label)
                    th_scale_layout.addWidget(self.thickness_scale_combo)
                    group_layout.addLayout(th_scale_layout)
                    
                    # Add the group_box to the scroll layout as usual
                    scroll_layout.addWidget(group_box)

            else:
                for subcategory, params in subcategories.items():
                    group_box = QGroupBox(subcategory)
                    group_layout = QVBoxLayout()
                    group_box.setLayout(group_layout)

                    for param, description in params.items():
                        if param in self.parameters:
                            # widget = self.create_widget(param, self.parameters[param], description)
                            widget = ParameterItemWidget(param, self.parameters[param],
                                                          description, self.global_defaults.get(param, {}))
                            self.parameter_widgets[param] = widget
                            label = QLabel(display_name_mapping.get(param, param))
                            label.setToolTip(description)
                            param_layout = QHBoxLayout()
                            param_layout.addWidget(label)
                            param_layout.addWidget(widget)
                            group_layout.addLayout(param_layout)

                    scroll_layout.addWidget(group_box)

            scroll_layout.addStretch()
            scroll_area.setWidget(scroll_widget)
            scroll_area.setWidgetResizable(True)
            tab_layout.addWidget(scroll_area)
            
            self.tab_widget.addTab(tab, main_category) 
        
    def update_wound_parameters_enablement(self):
        if self.is_injury_checkbox is None:
            return
        is_injury_enabled = self.is_injury_checkbox.isChecked()
        # Enable or disable injury parameter widgets
        for widget in self.injury_parameter_widgets:
            widget.setEnabled(is_injury_enabled)
        # Update visibility of ABLATION and CHEMICAL groups
        if is_injury_enabled:
            self.update_wound_parameters_visibility()
        else:
            # Hide both groups
            for group_box in self.wound_parameters_group_boxes.values():
                group_box.hide()

    def cancel_all_simulations(self):
        """Terminates all running simulation threads."""
        reply = QMessageBox.question(
            self,
            "Confirm Cancellation",
            "Are you sure you want to cancel all ongoing simulations? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.statusBar().showMessage("Cancellation requested by user...")
            print("Attempting to cancel all simulation threads.")
            
            # Terminate each running thread
            for thread, worker in self.simulation_threads:
                if thread.isRunning():
                    thread.terminate() # Abruptly stops the thread
                    thread.wait()      # Waits for it to fully stop

            QMessageBox.information(self, "Cancelled", "All simulation runs have been cancelled.")
            self.finalize_sweep(was_cancelled=True) 

    def update_wound_parameters_visibility(self):
        if self.injury_type_widget is None:
            return
        # TODO delete after testing | selected_injury_type = self.injury_type_widget.currentText()
        selected_injury_type = self.injury_type_widget.value_widget.currentText()
        for subcategory, group_box in self.wound_parameters_group_boxes.items():
            if subcategory == selected_injury_type:
                group_box.show()
            else:
                group_box.hide()

    def save_parameters(self):
        """
        Updates the internal parameters dictionary from the GUI widgets
        and performs necessary unit conversions (e.g., Days to MCS).
        """
        try:
            # First, gather all current values from the GUI widgets
            for param_name, widget in self.parameter_widgets.items():
                if isinstance(widget, ParameterItemWidget):
                    self.parameters[param_name] = widget.get_value()
                elif isinstance(widget, QCheckBox):
                    self.parameters[param_name] = widget.isChecked()

            # --- CRITICAL FIX: Convert time units from Days (GUI) to MCS (Simulation) ---
            # The vCornea model expects time in Monte Carlo Steps (MCS).
            # Conversion factor: 1 Day = 240 MCS
            if 'SimTime' in self.parameters:
                # Ensure the value is treated as a number before multiplying
                sim_time_days = float(self.parameters['SimTime'])
                self.parameters['SimTime'] = int(sim_time_days * 240)
            
            if 'InjuryTime' in self.parameters:
                injury_time_days = float(self.parameters['InjuryTime'])
                self.parameters['InjuryTime'] = int(injury_time_days * 240)

            print("Internal parameters updated and units converted for simulation.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error updating parameters from GUI: {str(e)}")
            # Re-raise the exception to ensure a faulty run does not proceed
            raise
  
    def save_parameters_to_file(self, file_path, params):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as file:
            for key, value in params.items():
                if isinstance(value, str):
                    value = f"'{value}'"
                # if 'SimTime' in self.parameters:                    
                #     sim_time_days = float(self.parameters['SimTime'])
                #     self.parameters['SimTime'] = int(sim_time_days * 240)
                
                # if 'InjuryTime' in self.parameters:
                #     injury_time_days = float(self.parameters['InjuryTime'])
                #     self.parameters['InjuryTime'] = int(injury_time_days * 240)
                file.write(f"{key} = {value}\n")

    def save_sweep_parameters(self):
        """
        Identifies parameters to be swept (those with comma-separated lists)
        and separates them from single-value base parameters. This method now
        also updates self.parameters directly with the converted values.
        """
        self.sweep_parameters = {}
        self.base_parameters = {}
        
        # Temporarily hold parameters to update at the end
        temp_params = {}

        for param_name, widget in self.parameter_widgets.items():
            if isinstance(widget, ParameterItemWidget):
                value = widget.get_value()
                temp_params[param_name] = value # Store the raw value from the widget                
            elif isinstance(widget, QCheckBox):
                temp_params[param_name] = widget.isChecked()

        if 'SimTime' in self.parameters:                    
            sim_time_days = float(temp_params['SimTime'])
            temp_params['SimTime'] = int(sim_time_days * 240)
        if 'InjuryTime' in self.parameters:
            injury_time_days = float(temp_params['InjuryTime'])
            temp_params['InjuryTime'] = int(injury_time_days * 240)

        for param_name, value in temp_params.items():
            # Check for comma-separated string to treat as a list for sweeping
            if isinstance(value, str) and ',' in value:
                try:
                    # Convert comma-separated string to a list of numbers
                    value_list = [self.convert_to_number(v.strip()) for v in value.split(',')]
                    self.sweep_parameters[param_name] = value_list
                    self.base_parameters[param_name] = value_list[0]  # Use first value as base
                except Exception as e:
                    QMessageBox.warning(self, "Parse Error", f"Could not parse list for {param_name}: {e}")
                    self.base_parameters[param_name] = value # Treat as single value if parsing fails
            else:
                self.base_parameters[param_name] = value
        
        # Finally, update the main self.parameters dictionary
        self.parameters = self.base_parameters.copy()
        
        print(f"Sweep Parameters identified: {self.sweep_parameters}")
        return bool(self.sweep_parameters)

    def generate_sweep_combinations(self):
        """Generates all possible combinations of sweep parameters."""
        if not self.sweep_parameters:
            return [self.base_parameters.copy()]

        from itertools import product
        param_names = list(self.sweep_parameters.keys())
        param_values = [self.sweep_parameters[name] for name in param_names]

        combinations = []
        for value_combination in product(*param_values):
            combination = self.base_parameters.copy()
            for name, value in zip(param_names, value_combination):
                combination[name] = value
            combinations.append(combination)
            
        return combinations

    def export_parameters(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Parameters", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, "w") as json_file:
                    json.dump(self.parameters, json_file, indent=4)
                QMessageBox.information(self, "Success", f"Parameters exported to '{file_path}' successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error exporting parameters: {str(e)}")

    def import_parameters(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Parameters", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, "r") as json_file:
                    imported_params = json.load(json_file)

                # If imported params are in MCS, convert them to days for GUI
                if "SimTime" in imported_params:
                    imported_params["SimTime"] = imported_params["SimTime"] / 240.0
                if "InjuryTime" in imported_params:
                    imported_params["InjuryTime"] = imported_params["InjuryTime"] / 240.0

                self.parameters.update(imported_params)
                self.save_parameters_to_file(self.parameters_file_path, self.parameters)
                QMessageBox.information(self, "Success", f"Parameters imported from '{file_path}' and saved successfully!")
                # Reload the GUI to reflect the new parameters
                self.tab_widget.clear()
                self.create_tabs()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error importing parameters: {str(e)}")
    
    def load_gui_config(self):
        """Loads GUI settings like the last used path from a JSON file."""
        if self.gui_config_file.exists():
            try:
                with open(self.gui_config_file, 'r') as f:
                    config = json.load(f)
                
                # Load and set repository path
                last_path = config.get("vcornea_repository_path")
                if last_path and Path(last_path).exists():
                    self.model_path_line_edit.setText(last_path)
                    print(f"Loaded saved repository path: {last_path}")
                    self.on_model_selection_change()

                # Load and set conda environment name
                last_conda_env = config.get("conda_env_name")
                if last_conda_env:
                    self.conda_env_line_edit.setText(last_conda_env)
                
                # Load and set output directory
                last_output_dir = config.get("output_directory")
                if last_output_dir:
                    self.output_dir_line_edit.setText(last_output_dir)

            except Exception as e:
                print(f"Could not load GUI config: {e}")

    def save_gui_config(self):
        """Saves GUI settings to a JSON file."""
        try:
            config = {
                "vcornea_repository_path": self.model_path_line_edit.text(),
                "conda_env_name": self.conda_env_line_edit.text(),
                "output_directory": self.output_dir_line_edit.text()
            }
            with open(self.gui_config_file, 'w') as f:
                json.dump(config, f, indent=4)
            print(f"Saved GUI configuration.")
        except Exception as e:
            print(f"Could not save GUI config: {e}")
    
    def browse_for_model_path(self):
        """Opens a dialog to select the root vCornea model directory."""
        directory = QFileDialog.getExistingDirectory(self, "Select vCornea Repository Folder")
        if directory:
            self.model_path_line_edit.setText(directory) 
            self.save_gui_config()           
            self.on_model_selection_change()

    def browse_for_output_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir_line_edit.setText(directory)
            self.save_gui_config()

    def reset_parameters(self):
        """Reset parameters to the original values from original_parameters.json."""
        try:
            original_params = load_original_parameters(self.original_params_path)
            self.parameters = original_params
            self.tab_widget.clear()
            self.create_tabs()
            QMessageBox.information(self, "Success", "Parameters have been reset to original values!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not reset parameters: {str(e)}")
    
    def on_model_selection_change(self):
        base_path_str = self.model_path_line_edit.text()
        if not base_path_str:
            return
        base_path = Path(base_path_str)
        selected_model_key = self.model_selection_combo.currentText()
        model_sub_path = self.model_mapping.get(selected_model_key)
        if not model_sub_path:
            return
        params_file = base_path / model_sub_path / "Simulation" / "Parameters.py"
        try:
            if not params_file.exists():
                raise FileNotFoundError(f"Parameters.py not found for this model version.\nChecked path: {params_file}")
            new_params = read_parameters_file(params_file)
            self.parameters.update(new_params)
            self.update_parameter_widgets(self.parameters)
            print(f"Successfully loaded parameters for: '{selected_model_key}'")
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Could not load parameters for selected model:\n{str(e)}")

    def update_parameter_widgets(self, params_to_load):
        """Iterates through all parameter widgets and sets their values."""
        for param_name, widget in self.parameter_widgets.items():
            if param_name in params_to_load:
                value = params_to_load[param_name]
                if isinstance(widget, ParameterItemWidget):
                    widget.set_value(value)
                elif isinstance(widget, QCheckBox):                   
                    widget.setChecked(bool(value))
        
        # Trigger visibility updates for conditional sections like the wound parameters
        self.update_wound_parameters_enablement()
        self.update_wound_parameters_visibility()

    def validate_time_parameters(self):
        """
        Validate that simulation times are long enough to have meaningful data
        after the 2-day relaxation period.
        
        Timeline requirements:
        - No injury: [0-2 stable] + [2-9+ measurement] = minimum 9 days
        - With injury: [0-2 stable] + [2-3 pre-injury] + [3 injury] + [3-10+ post-injury] = minimum 10 days
        """
        STABLE_TIME_DAYS = 2.0  # Relaxation/equilibration period
        MIN_PRE_INJURY_MEASUREMENT_DAYS = 1.0  # Pre-injury measurement window
        MIN_POST_INJURY_MEASUREMENT_DAYS = 7.0  # Post-injury measurement window
        MIN_NO_INJURY_MEASUREMENT_DAYS = 7.0  # Measurement window when no injury
        
        # Get current values from GUI
        sim_time_days = float(self.parameter_widgets['SimTime'].get_value())
        is_injury_widget = self.parameter_widgets.get('IsInjury')
        
        if isinstance(is_injury_widget, QCheckBox):
            is_injury = is_injury_widget.isChecked()
        elif is_injury_widget:
            is_injury = is_injury_widget.get_value()
        else:
            is_injury = False
        
        issues = []
        corrections = {}
        
        # ===== NO INJURY VALIDATION =====
        if not is_injury:
            min_sim_time = STABLE_TIME_DAYS + MIN_NO_INJURY_MEASUREMENT_DAYS  # 2 + 7 = 9 days
            
            if sim_time_days < min_sim_time:
                issues.append(
                    f"• Simulation time too short: {sim_time_days} days\n"
                    f"  Minimum required: {min_sim_time} days\n"
                    f"  ({STABLE_TIME_DAYS} days equilibration + {MIN_NO_INJURY_MEASUREMENT_DAYS} days measurement)"
                )
                corrections['SimTime'] = min_sim_time
        
        # ===== WITH INJURY VALIDATION =====
        else:
            injury_time_days = float(self.parameter_widgets['InjuryTime'].get_value())
            
            # RULE 1: Injury must occur AFTER stable period + pre-injury measurement
            min_injury_time = STABLE_TIME_DAYS + MIN_PRE_INJURY_MEASUREMENT_DAYS  # 2 + 1 = 3 days
            
            if injury_time_days < min_injury_time:
                issues.append(
                    f"• Injury time too early: {injury_time_days} days\n"
                    f"  Minimum required: {min_injury_time} days\n"
                    f"  ({STABLE_TIME_DAYS} days equilibration + {MIN_PRE_INJURY_MEASUREMENT_DAYS} day pre-injury baseline)"
                )
                corrections['InjuryTime'] = min_injury_time
                # Update for subsequent checks
                injury_time_days = min_injury_time
            
            # RULE 2: Must have enough time AFTER injury for recovery measurement
            time_after_injury = sim_time_days - injury_time_days
            
            if time_after_injury < MIN_POST_INJURY_MEASUREMENT_DAYS:
                required_sim_time = injury_time_days + MIN_POST_INJURY_MEASUREMENT_DAYS
                issues.append(
                    f"• Insufficient post-injury time: {time_after_injury:.1f} days\n"
                    f"  Minimum required: {MIN_POST_INJURY_MEASUREMENT_DAYS} days\n"
                    f"  (Need {required_sim_time} days total simulation time)"
                )
                corrections['SimTime'] = required_sim_time
                # Update for subsequent checks
                sim_time_days = required_sim_time
            
            # RULE 3: Overall minimum simulation time with injury (sanity check)
            min_total_sim_time = STABLE_TIME_DAYS + MIN_PRE_INJURY_MEASUREMENT_DAYS + MIN_POST_INJURY_MEASUREMENT_DAYS
            
            if sim_time_days < min_total_sim_time:
                issues.append(
                    f"• Total simulation time too short: {sim_time_days} days\n"
                    f"  Minimum with injury: {min_total_sim_time} days\n"
                    f"  ({STABLE_TIME_DAYS} days equilibration + {MIN_PRE_INJURY_MEASUREMENT_DAYS} day pre-injury + {MIN_POST_INJURY_MEASUREMENT_DAYS} days post-injury)"
                )
                corrections['SimTime'] = min_total_sim_time
        
        # ===== APPLY ALL CORRECTIONS IF NEEDED =====
        if issues:
            # Build comprehensive error message
            error_msg = "Time Parameter Validation Failed\n\n"
            error_msg += "Issues found:\n" + "\n".join(issues) + "\n\n"
            error_msg += "Corrections applied:\n"
            
            for param, value in corrections.items():
                error_msg += f"  • {param}: {value} days\n"
                self.parameter_widgets[param].set_value(value)
                self.parameters[param] = value
            
            QMessageBox.warning(self, "Invalid Time Parameters", error_msg)
            return False
        
        # All validations passed
        return True

    def run_simulation(self):
        """
        Initializes and starts a fully parallel parameter sweep. It generates all
        combinations and launches a separate background thread for each one immediately.
        """
        try:
            from datetime import datetime

            if not self.validate_time_parameters():
                # Validation failed and was corrected - ask user if they want to continue
                reply = QMessageBox.question(
                    self,
                    "Continue with corrected values?",
                    "Time parameters were adjusted to meet minimum requirements.\n"
                    "Do you want to continue with the corrected values?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    self.run_simulation_button.setEnabled(True)
                    return

            # 1. Generate all parameter combinations
            self.save_sweep_parameters()
            self.parameter_combinations = self.generate_sweep_combinations()
            self.total_combinations = len(self.parameter_combinations)

            if self.total_combinations == 0:
                QMessageBox.warning(self, "Error", "No parameter combinations were generated.")
                return

            # --- SETUP PROGRESS INDICATION ---
            self.run_simulation_button.setEnabled(False)
            self.cancel_button.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(self.total_combinations)
            self.progress_bar.setValue(0)
            self.statusBar().showMessage(f"Starting sweep with {self.total_combinations} combination(s)...")
            QApplication.processEvents() # Force GUI to update immediately

            # 2. Create one main output folder for the entire sweep
            base_output_dir = Path(self.output_dir_line_edit.text())
            custom_name = self.run_name_line_edit.text().strip()

            if custom_name:
                safe_custom_name = "".join(c for c in custom_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
                folder_name = safe_custom_name.replace(' ', '_')
            else:
                # Fallback to the timestamped name
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                folder_name = f"parameter_sweep_{timestamp}"

            self.sweep_output_folder = base_output_dir / folder_name
            self.sweep_output_folder.mkdir(parents=True, exist_ok=True)
            print(f"Sweep results will be saved in: {self.sweep_output_folder}")

            # 3. Initialize counters and thread list
            self.simulation_threads = []
            self.completed_combinations = 0
            
            QMessageBox.information(self, "Sweep Started",
                f"Launching {self.total_combinations} parameter combination(s) in parallel.\n"
                f"The GUI will remain responsive. You will be notified upon completion.")

            # 4. Loop through all combinations and launch a worker thread for each
            conda_env = self.conda_env_line_edit.text()
            replicates_per_combo = self.replicate_input.value()
            
            base_repo_path = Path(self.model_path_line_edit.text())
            selected_model_key = self.model_selection_combo.currentText()
            model_sub_path = self.model_mapping.get(selected_model_key)
            source_project_path = str(base_repo_path / model_sub_path)

            for i, run_params in enumerate(self.parameter_combinations):
                print(f"Launching thread for Combination {i+1}...")                
                
                current_run_params = run_params.copy()

                # Convert time units from GUI (Days) to Simulation (MCS)
                if 'SimTime' in run_params:
                    run_params['SimTime'] = int(float(run_params['SimTime']) * 240)
                if 'InjuryTime' in run_params:
                    run_params['InjuryTime'] = int(float(run_params['InjuryTime']) * 240)

                process_config = {
                    'vcornea_project_path': source_project_path,
                    'cc3d_conda_env_name': conda_env,
                    'output_base_dir': str(self.sweep_output_folder), # Pass the main folder
                    'replicates': replicates_per_combo,
                    'run_id': f'combo_{i+1:03d}'
                }

                thread = QThread()
                worker = SimulationWorker(process_config, current_run_params)
                worker.moveToThread(thread)

                thread.started.connect(worker.run)
                worker.finished.connect(self.on_run_finished)
                worker.error.connect(self.on_run_error)

                # Connections for cleanup
                worker.finished.connect(thread.quit)
                worker.finished.connect(worker.deleteLater)
                thread.finished.connect(thread.deleteLater)

                thread.start()
                self.simulation_threads.append((thread, worker)) # Keep a reference

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to start parameter sweep: {str(e)}") 

    def on_run_finished(self, output):
        """This SLOT handles the successful completion of one parameter combination."""
        self.completed_combinations += 1
        run_name = output.get('outputs', {}).get('run_metadata', {}).get('run_name', 'unknown_run')
        print(f"SUCCESS: Combination '{run_name}' finished. Progress: {self.completed_combinations}/{self.total_combinations}")
        
        # --- UPDATE PROGRESS ---
        self.progress_bar.setValue(self.completed_combinations)
        self.statusBar().showMessage(f"Completed {self.completed_combinations} of {self.total_combinations} combinations.")
        QApplication.processEvents()

        print(f"SUCCESS: Combination '{run_name}' finished. Progress: {self.completed_combinations}/{self.total_combinations}")
    
        if self.completed_combinations >= self.total_combinations:
            self.finalize_sweep()        
        
    def on_run_error(self, error_message):
        """This SLOT handles a failed run."""
        self.completed_combinations += 1
        print(f"FAILURE: A combination failed. Progress: {self.completed_combinations}/{self.total_combinations}")
        print(f"ERROR DETAILS: {error_message}")
        
        # --- UPDATE PROGRESS ---
        self.progress_bar.setValue(self.completed_combinations)
        self.statusBar().showMessage(f"Completed {self.completed_combinations} of {self.total_combinations} (with errors).")
        QApplication.processEvents()

        print(f"FAILURE: A combination failed. Progress: {self.completed_combinations}/{self.total_combinations}")
        print(f"ERROR DETAILS: {error_message}")

        if self.completed_combinations >= self.total_combinations:
            self.finalize_sweep()

        # """This method is a SLOT that handles the 'error' signal from a worker."""
        # print(f"A simulation run has failed with an error: {error_message}")
        # QMessageBox.critical(self, "Simulation Error", f"A simulation failed to complete:\n\n{error_message}")

    def finalize_sweep(self, was_cancelled=False):
        """Called when all simulation threads have reported back or were cancelled."""
        if was_cancelled:
            status_message = f"Sweep Cancelled. {self.completed_combinations} of {self.total_combinations} combinations were processed."
        else:
            status_message = f"Sweep Complete! Processed {self.completed_combinations} of {self.total_combinations} combinations."

        self.statusBar().showMessage(status_message)
        self.progress_bar.setValue(self.total_combinations) # Fill the bar
        
        # Reset UI buttons
        self.run_simulation_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        
        print("All simulation threads have reported back or were cancelled.")
        if not was_cancelled:
            QMessageBox.information(self, "Sweep Complete",
                f"The parameter sweep has finished.\n"
                f"{self.completed_combinations} out of {self.total_combinations} combinations have been processed.\n"
                f"Results are organized in: {self.sweep_output_folder}")
        
        # Clean up thread list
        self.simulation_threads = []        
      
    def get_plot_settings(self):
        """Get the current plot settings from the Parameters section"""
        plot_settings = {}
        try:
            plots_params = parameter_structure["Plots"]["DATA COLECTION AND REAL-TIME PLOTS"]
            
            # Get all plot-related parameters
            for param in plots_params.keys():
                plot_settings[param] = self.parameters[param]
                
            print("Plot settings retrieved:", plot_settings)  # Debug print
            return plot_settings
            
        except Exception as e:
            print(f"Error getting plot settings: {e}")
            return None

    def plot_results(self):
        """
        Plot results from a selected directory. All plotting parameters (injury time,
        simulation time, etc.) are read from the metadata files in the selected directory,
        NOT from the current GUI state. This allows plotting previous simulations
        while a new one is running.
        """
        # # 1. Determine the starting directory for the file dialog
        # start_dir = ""
        # if self.sweep_output_folder and Path(self.sweep_output_folder).exists():
        #     start_dir = str(self.sweep_output_folder)
        # elif self.output_dir_line_edit.text() and Path(self.output_dir_line_edit.text()).exists():
        #     start_dir = self.output_dir_line_edit.text()
        # else:
        #     start_dir = str(Path.home()) # Fallback to user's home directory
       
       # 1. Determine a good starting directory for the dialog
        start_dir = self.output_dir_line_edit.text()
        if not start_dir or not Path(start_dir).exists():
            start_dir = str(Path.home())

        # 2. Open a dialog to ask the user for the directory
        directory_to_plot = QFileDialog.getExistingDirectory(
            self, 
            "Select Simulation or Sweep Output Directory to Plot",
            start_dir
        )

        if not directory_to_plot:
            return # User cancelled the dialog
         
        try:
            # for param_name, widget in self.parameter_widgets.items():
            #     if isinstance(widget, ParameterItemWidget):
            #         self.parameters[param_name] = widget.get_value()
            #     elif isinstance(widget, QCheckBox):
            #         self.parameters[param_name] = widget.isChecked()
            # plot_manager = PlotManager(Data_DIR=directory_to_plot)
            plot_manager = PlotManager(
                Data_DIR=directory_to_plot,
                Out_DIR=directory_to_plot,  # Save plots in same directory
                CurrentParam={}  # Pass current parameters
            )
            
            # Determine which plots to generate based on current GUI settings
            cell_count_is_checked = self.parameter_widgets.get('CellCount').get_value()
            thickness_is_checked = self.parameter_widgets.get('ThicknessPlot').get_value()
            
            cell_count_scale = self.cell_count_scale_combo.currentText()
            thickness_scale = self.thickness_scale_combo.currentText()
            
            if cell_count_is_checked:
                

                # plot_manager.plot_count(
                #     mode='individual',  # or 'full' for all visualization types
                #     is_injury=plot_manager.is_injury,  # From metadata, not GUI
                #     injury_time_mcs=plot_manager.injury_time_mcs,  # From metadata, not GUI
                #     scale_option=cell_count_scale
                # )

                # plot_manager.plot_count(
                #     mode='comparison',  # or 'full' for all visualization types
                #     is_injury=plot_manager.is_injury,  # From metadata, not GUI
                #     injury_time_mcs=plot_manager.injury_time_mcs,  # From metadata, not GUI
                #     scale_option=cell_count_scale
                # )

                # plot_manager.plot_count(
                #     mode='statistics',  # or 'full' for all visualization types
                #     is_injury=plot_manager.is_injury,  # From metadata, not GUI
                #     injury_time_mcs=plot_manager.injury_time_mcs,  # From metadata, not GUI
                #     scale_option=cell_count_scale
                # )

                plot_manager.plot_count(
                    mode='full',  # or 'full' for all visualization types
                    is_injury=plot_manager.is_injury,  # From metadata, not GUI
                    injury_time_mcs=plot_manager.injury_time_mcs,  # From metadata, not GUI
                    scale_option=cell_count_scale
                )
            
            if thickness_is_checked:
                
                plot_manager.plot_thickness(
                    is_injury=plot_manager.is_injury,  # From metadata, not GUI
                    injury_time_mcs=plot_manager.injury_time_mcs,  # From metadata, not GUI
                    scale_option=thickness_scale
                )
            
            if not cell_count_is_checked and not thickness_is_checked:
                QMessageBox.information(self, "Plotting", "No plot types (Cell Count, Thickness) were selected in the 'Plots' tab.")
            else:
                # QMessageBox.information(self, "Plotting Complete", f"Plots generated for data in:\n{directory_to_plot}")
                # Show info about what was plotted
                info_msg = f"Plots generated for data in:\n{directory_to_plot}\n\n"
                info_msg += f"Simulation parameters (from metadata):\n"
                info_msg += f"  - Injury: {'Yes' if plot_manager.is_injury else 'No'}\n"
                if plot_manager.is_injury:
                    info_msg += f"  - Injury Time: {plot_manager.injury_time_mcs} MCS ({plot_manager.injury_time_mcs/240:.1f} days)\n"
                info_msg += f"  - Simulation Time: {plot_manager.sim_time_mcs} MCS ({plot_manager.sim_time_mcs/240:.1f} days)"
                
                QMessageBox.information(self, "Plotting Complete", info_msg)

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Error plotting results: {str(e)}")

        # try:
        #     # 3. Get the current plot settings from the GUI
        #     # self.save_parameters() # Ensure self.parameters is up-to-date with GUI values
        #     sim_time_mcs = self.parameters.get("SimTime", 7700)
        #     is_injury = bool(self.parameters.get("IsInjury", False))
        #     injury_time_mcs = self.parameters.get("InjuryTime", 0)
            
        #     # 4. Instantiate the PlotManager with the selected directory and GUI parameters
        #     plot_manager = PlotManager(
        #         Data_DIR=directory_to_plot, 
        #         Out_DIR=directory_to_plot, # Save plots in the same folder
        #         CurrentParam=self.parameters
        #     )
            
        #     # 5. Call the plotting functions
        #     if self.parameters.get('CellCount'):
        #         scale_mode = self.cell_count_scale_combo.currentText()
        #         plot_manager.plot_count(is_injury=is_injury, injury_time_mcs=injury_time_mcs, scale_option=scale_mode)
            
        #     if self.parameters.get('ThicknessPlot'):
        #         scale_mode = self.thickness_scale_combo.currentText()
        #         plot_manager.plot_thickness(is_injury=is_injury, injury_time_mcs=injury_time_mcs, scale_option=scale_mode)
            
        #     QMessageBox.information(self, "Plotting Complete", f"Plots generated for data in:\n{directory_to_plot}")

        # except Exception as e:
        #     import traceback
        #     traceback.print_exc()
        #     QMessageBox.critical(self, "Error", f"Error plotting results: {str(e)}")
     
    def revert_tab_to_defaults(self, tab_name, reference):
        """Revert the parameters in the given tab to the default values for the selected reference."""
        if reference == "custom":
            QMessageBox.information(self, "Reversion", "No default reference selected.")
            return

        # For the 'Cells Parameters' tab, handle cell-type defaults.
        if tab_name == "Cells Parameters":
            # Loop over each cell type subcategory in the Cells Parameters tab.
            for cell_type, params in parameter_structure[tab_name].items():
                # Retrieve cell-type defaults if available; otherwise, fall back to global defaults.
                defaults_for_cell = self.cell_type_defaults.get(cell_type, {})
                for param in params:
                    if param in self.parameter_widgets:
                        widget = self.parameter_widgets[param]
                        # Prefer cell-type default if it exists, else check global.
                        if param in defaults_for_cell:
                            default_val = defaults_for_cell[param].get(reference)
                        else:
                            default_val = self.global_defaults.get(param, {}).get(reference)
                        if default_val is not None:
                            widget.set_value(default_val)
                            self.parameters[param] = default_val
            QMessageBox.information(self, "Reversion",
                f"'{tab_name}' parameters reverted to defaults for reference '{reference}'.")
        else:
            # For other tabs, revert using global defaults.
            for param, widget in self.parameter_widgets.items():
                if param in self.global_defaults:
                    default_val = self.global_defaults[param].get(reference)
                    if default_val is not None:
                        widget.set_value(default_val)
                        self.parameters[param] = default_val
            QMessageBox.information(self, "Reversion",
                f"'{tab_name}' parameters reverted to defaults for reference '{reference}'.")        

        # Iterate over parameters in the defaults and update their widget values.
        for param, default_value in defaults_for_cell.items():
            if param in self.parameter_widgets:
                widget = self.parameter_widgets[param]
                # Update widget based on its type.
                if isinstance(widget, QLineEdit):
                    widget.setText(str(default_value))
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(bool(default_value))
                elif isinstance(widget, QComboBox):
                    index = widget.findText(str(default_value))
                    if index != -1:
                        widget.setCurrentIndex(index)
                # Also update the underlying parameters dictionary.
                self.parameters[param] = default_value
            else:
                print(f"Widget for parameter {param} not found in tab {tab_name}")
        QMessageBox.information(self, "Reversion", f"Parameters in tab '{tab_name}' reverted to default values for reference '{reference}'")

    def revert_cell_type_defaults(self, cell_type, ref, params):
        if ref == "custom":
            QMessageBox.information(self, "Reversion", f"No default reference selected for cell type '{cell_type}'.")
            return
        # Get the defaults dictionary for this cell type.
        defaults_for_cell = self.cell_type_defaults.get(cell_type, {})
        for param in params:
            if param in self.parameter_widgets and param in defaults_for_cell:
                widget = self.parameter_widgets[param]
                default_val = defaults_for_cell[param].get(ref)
                if default_val is not None:
                    widget.set_value(default_val)
                    self.parameters[param] = default_val
        QMessageBox.information(self, "Reversion", f"Cell type '{cell_type}' parameters reverted to defaults for reference '{ref}'.")


   