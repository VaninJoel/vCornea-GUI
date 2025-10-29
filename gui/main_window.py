from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, QSpinBox, QApplication,
                           QMessageBox, QHBoxLayout, QLabel, QPushButton, QScrollArea, QProgressBar,
                           QFileDialog, QProgressDialog , QComboBox, QGroupBox, QCheckBox, QLineEdit)
from PyQt5.QtCore import Qt, QThread
from gui.simulation_worker import SimulationWorker
from gui.widgets.collapsible_group import CollapsibleGroupBox
from gui.widgets.parameter_item import ParameterItemWidget

# from config.parameter_structure import parameter_structure
# from config.display_mapping import display_name_mapping

from analysis.plot_manager import PlotManager

from utils.schema_utils import *
from vivarium_vcornea import VCorneaProcess

# from utils.file_handlers import (load_parameter_defaults, load_original_parameters,
#                                read_parameters_file, save_parameters_file)

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
            "Epithelium Homeostasis": "Local/Project/paper_version",
            "Epithelium Initiation": "Local/Project/paper_version_STEM_ONLY",           
        }
       
        self.current_script_directory = Path(__file__).parent.parent.absolute()
        self.gui_config_file = self.current_script_directory / "gui_config.json"
       
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

        self.schema = {}
        self.parameter_structure = {}
        self.display_name_mapping = {}
        self.global_defaults = {}
        self.cell_type_defaults = {}
        self.parameters = {} 
        self._loading_config = False # Flag to prevent redundant loads
        
        self.init_ui()

        self._loading_config = True
        self.load_gui_config()  
        self._loading_config = False
        
        # # --- Load schema after GUI is built and config is loaded ---
        # # This will populate self.parameters, etc. and update widgets
        # if not self.model_path_line_edit.text():
        #      QMessageBox.warning(self, "Configuration Missing", 
        #         "Please select your vCornea Repository Path in the Configuration section.")
        # else:
        #     try:
        #         self.load_schema_and_parameters()
        #     except Exception as e:
        #          QMessageBox.critical(self, "Error", 
        #             f"Failed to load VCornea model schema: {str(e)}\n"
        #             "Please check the repository path and ensure the 'vcornea_process.py' file is correct.")
        
        # --- Load schema only if config didn't trigger it ---
        # And if path is actually set
        if not self.schema and self.model_path_line_edit.text():
             print("Loading schema explicitly after config load.") # Debug
             try:
                 # Ensure model selection combo matches loaded path if possible
                 # (This assumes config loads path BEFORE schema)
                 self.load_schema_and_parameters()
             except Exception as e:
                  QMessageBox.critical(self, "Initial Schema Load Error",
                     f"Failed to load VCornea model schema on startup: {str(e)}\n"
                     "Please check the repository path.")
        elif not self.model_path_line_edit.text():
             QMessageBox.warning(self, "Configuration Missing",
                "Please select your vCornea Repository Path in the Configuration section.")

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
        # self.model_path_line_edit.editingFinished.connect(self.on_repo_path_changed)
        self.model_path_line_edit.returnPressed.connect(self.on_repo_path_changed)

        browse_repo_button = QPushButton("Browse...")
        browse_repo_button.clicked.connect(self.browse_for_model_path)
        path_selection_layout.addWidget(path_label)
        path_selection_layout.addWidget(self.model_path_line_edit)
        path_selection_layout.addWidget(browse_repo_button)
        path_group_layout.addLayout(path_selection_layout)
        self._last_repo_path = ""
        
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
        # button_layout.addWidget(save_button)
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

    def load_schema_and_parameters(self):
        """
        Instantiates VCorneaProcess, extracts the schema, and populates
        all GUI parameter configurations from it.
        """
        if self._loading_config:
            print("Skipping schema load because config is loading.") # Debug
            return

        base_path_str = self.model_path_line_edit.text()
        if not base_path_str:
            raise FileNotFoundError("vCornea Repository Path is not set.")
            
        base_path = Path(base_path_str)
        selected_model_key = self.model_selection_combo.currentText()
        model_sub_path = self.model_mapping.get(selected_model_key)
        
        if not model_sub_path:
            raise ValueError(f"No model sub-path found for '{selected_model_key}'")
            
        full_project_path = str(base_path / model_sub_path)
        print(f"Attempting to load schema from: {full_project_path}")
        
        # 1. Instantiate the process to get its schema
        # This is the core of the new dynamic loading
        try:
            package_dir = base_path.parent # Assuming vivarium_vcornea is sibling to vCornea repo
            sys.path.insert(0, str(package_dir))
            print(f"Temporarily added to sys.path: {package_dir}")
            
            process_instance = VCorneaProcess({'vcornea_project_path': full_project_path})
            self.schema = process_instance.ports_schema()

        except ModuleNotFoundError:
             raise ModuleNotFoundError(
                 f"Could not find 'vivarium_vcornea' package. "
                 f"Ensure it's installed in the '{self.conda_env_line_edit.text()}' environment "
                 f"or located correctly relative to '{base_path_str}'. "
                 f"Tried adding '{package_dir}' to sys.path."
             )    
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise Exception(f"Failed to instantiate VCorneaProcess from path '{full_project_path}': {e}")
        finally:
            # Clean up sys.path
            if str(package_dir) in sys.path:
                sys.path.pop(0)
                print(f"Removed from sys.path: {package_dir}")

        if not self.schema or 'inputs' not in self.schema:
            raise Exception("Loaded schema is empty or invalid.")
        print("Schema loaded successfully.")

        # 2. Use schema_utils to populate GUI data structures
        self.parameter_structure = get_parameter_structure(self.schema)
        self.display_name_mapping = get_display_name_mapping(self.schema)
        self.global_defaults, self.cell_type_defaults = load_parameter_defaults_from_schema(self.schema)
        print("GUI data structures populated from schema.")
        print("Parameter Structure:", json.dumps(self.parameter_structure, indent=2)) # Debug
        
        # 3. Load the model defaults as the "current" parameters
        self.parameters = get_model_defaults(self.schema)
        print("Model default parameters loaded.")
        
        # 4. Rebuild or update GUI
        print("Rebuilding GUI tabs...")
        self.tab_widget.clear()
        self.parameter_widgets = {}
        self.is_injury_checkbox = None
        self.injury_parameter_widgets = []
        self.injury_type_widget = None
        self.wound_parameters_group_boxes = {}
        self.create_tabs()
        print("GUI tabs rebuilt.")
        print(f"Successfully loaded schema and parameters for: '{selected_model_key}'")

    def create_tabs(self):
        """Creates tabs and parameter widgets based on self.parameter_structure."""
        print("--- Starting create_tabs ---") # Debug
        if not self.parameter_structure:
             print("Warning: parameter_structure is empty, cannot create tabs.")
             return
        
        for main_category, subcategories in self.parameter_structure.items():
            print(f"Creating Tab: {main_category}") # Debug
            tab = QWidget()
            tab_layout = QVBoxLayout()
            tab.setLayout(tab_layout)

            # --- Tab-level Default Reversion Controls ---
            default_layout = QHBoxLayout()
            default_ref_label = QLabel("Default Reference:")
            all_refs = set(k for p in self.global_defaults.values() for k in p if k != 'default')
            all_refs.update(k for ct in self.cell_type_defaults.values() for p in ct.values() for k in p if k != 'default')
            sorted_refs = sorted(list(all_refs))

            default_combo = QComboBox()
            default_combo.addItem("custom") # Add custom option
            default_combo.addItems(sorted_refs)

            revert_button = QPushButton("Revert Tab to Defaults")
            revert_button.clicked.connect(
                lambda _, tab_name=main_category, combo=default_combo: self.revert_tab_to_defaults(tab_name, combo.currentText())
            )
            default_layout.addWidget(default_ref_label)
            default_layout.addWidget(default_combo)
            default_layout.addWidget(revert_button)
            tab_layout.addLayout(default_layout)

            # --- Scroll Area for Parameters ---
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
                    
                    cell_reversion_layout = QHBoxLayout()
                    cell_reversion_label = QLabel("Cell Type Default Reference:")
                    cell_reversion_combo = QComboBox()
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
                            label = QLabel(self.display_name_mapping.get(param, param))
                            label.setToolTip(description)
                            param_layout = QHBoxLayout()
                            param_layout.addWidget(label)
                            param_layout.addWidget(widget)
                            group_layout.addLayout(param_layout)

                    scroll_layout.addWidget(group_box)
            elif main_category == "Wound Parameters":
                print(f"  Processing Wound Parameters subcategories: {list(subcategories.keys())}") # Debug
                
                current_wound_group_boxes = {
                    'Mechanical Injury': None,
                    'Chemical Injury': None,
                    'Chemical Diffusion': None,
                    # Add others if needed
                }
                # Reset injury widgets list for THIS CALL
                current_injury_widgets = []
                current_is_injury_checkbox = None
                current_injury_type_widget = None

                for subcategory, params in subcategories.items():
                    print(f"    Processing subcategory: {subcategory}") # Debug
                    # Create group box for this subcategory
                    group_box = QGroupBox(subcategory) # Use schema subcategory name
                    group_layout = QVBoxLayout()
                    group_box.setLayout(group_layout)

                    # --- Process Parameters for this Subcategory ---
                    for param, description in params.items():
                        if param in self.parameters:
                            # Get default info for the ParameterItemWidget
                            defaults_for_param = self.global_defaults.get(param, {})

                            # --- Special Handling ---
                            if param == "IsInjury":
                                widget = QCheckBox()
                                widget.setChecked(bool(self.parameters[param]))
                                # Connect signal AFTER storing reference
                                current_is_injury_checkbox = widget # Store locally first
                                widget.stateChanged.connect(self.update_wound_parameters_enablement)
                                self.parameter_widgets[param] = widget # Store in main dict

                                label = QLabel(self.display_name_mapping.get(param, param))
                                label.setToolTip(description)
                                param_layout = QHBoxLayout()
                                param_layout.addWidget(label)
                                param_layout.addWidget(widget)
                                group_layout.addLayout(param_layout)

                            elif param == "InjuryType":
                                widget = ParameterItemWidget(param, self.parameters[param], description, defaults_for_param)
                                self.parameter_widgets[param] = widget
                                current_injury_type_widget = widget # Store locally first

                                if hasattr(widget.value_widget, "currentTextChanged"):
                                    # Connect signal AFTER storing reference
                                    widget.value_widget.currentTextChanged.connect(
                                        lambda text: self.update_wound_parameters_visibility(selected_text=text)
                                    )
                                else:
                                     print(f"      Warning: InjuryType widget has no currentTextChanged signal.")

                                current_injury_widgets.append(widget) # Add to local list

                                label = QLabel(self.display_name_mapping.get(param, param))
                                label.setToolTip(description)
                                param_layout = QHBoxLayout()
                                param_layout.addWidget(label, 0) # Stretch 0
                                param_layout.addWidget(widget, 1) # Stretch 1
                                group_layout.addLayout(param_layout)

                            else: # Standard ParameterItemWidget
                                widget = ParameterItemWidget(param, self.parameters[param], description, defaults_for_param)
                                self.parameter_widgets[param] = widget

                                # Add relevant params to local list for enable/disable
                                if subcategory in ['Timing', 'Mechanical Injury', 'Chemical Injury', 'Chemical Diffusion']:
                                     current_injury_widgets.append(widget)

                                label = QLabel(self.display_name_mapping.get(param, param))
                                label.setToolTip(description)
                                param_layout = QHBoxLayout()
                                param_layout.addWidget(label, 0) # Stretch 0
                                param_layout.addWidget(widget, 1) # Stretch 1
                                group_layout.addLayout(param_layout)

                    # Add the group box to the layout
                    scroll_layout.addWidget(group_box)

                    # --- Store Group Box Reference using schema subcategory name as key ---
                    if subcategory in current_wound_group_boxes:
                        current_wound_group_boxes[subcategory] = group_box
                        print(f"      Stored reference to '{subcategory}' group box locally.") # Debug

                # --- Assign local references to instance variables AFTER loop ---
                self.wound_parameters_group_boxes = current_wound_group_boxes
                self.injury_parameter_widgets = current_injury_widgets
                self.is_injury_checkbox = current_is_injury_checkbox
                self.injury_type_widget = current_injury_type_widget
                print("  Assigned local wound widget/group references to instance.") # Debug

                # Set initial state *after* all group boxes AND references are assigned
                print("  Setting initial enablement/visibility for Wound Parameters.") # Debug
                if self.is_injury_checkbox:
                    self.update_wound_parameters_enablement() # Call first
                else:
                    print("  Error: is_injury_checkbox not set after creating Wound Params tab.")
            elif main_category == "Plots":
                 # (This section seems okay, just ensure stretch factor is added)
                for subcategory, params in subcategories.items():
                    group_box = QGroupBox(subcategory)
                    group_layout = QVBoxLayout()
                    group_box.setLayout(group_layout)

                    for param, description in params.items():
                        if param in self.parameters:
                            defaults_for_param = self.global_defaults.get(param, {})
                            # Special handling for scale combos - they are not ParameterItemWidgets
                            if param in ["CellCountScale", "ThicknessScale"]:
                                continue # Skip adding them as ParameterItemWidget

                            widget = ParameterItemWidget(param, self.parameters[param],
                                                        description, defaults_for_param)
                            self.parameter_widgets[param] = widget
                            label = QLabel(self.display_name_mapping.get(param, param))
                            label.setToolTip(description)
                            param_layout = QHBoxLayout()
                            param_layout.addWidget(label) # Default stretch 0
                            param_layout.addWidget(widget, 1) # Stretch 1
                            group_layout.addLayout(param_layout)

                    # --- Add Scale Combo Boxes ---
                    # Cell Count Scale
                    cc_scale_label = QLabel("Cell Count Scale:")
                    self.cell_count_scale_combo = QComboBox()
                    self.cell_count_scale_combo.addItems(["Absolute", "Percentage", "PctChangeFromMean"])
                    current_cc_scale = self.parameters.get("CellCountScale", "Absolute") # Use .get for safety
                    idx_cc = self.cell_count_scale_combo.findText(current_cc_scale)
                    if idx_cc >= 0: self.cell_count_scale_combo.setCurrentIndex(idx_cc)
                    self.cell_count_scale_combo.currentTextChanged.connect(
                        lambda val: self.parameters.update({"CellCountScale": val})
                    )
                    cc_scale_layout = QHBoxLayout()
                    cc_scale_layout.addWidget(cc_scale_label)
                    cc_scale_layout.addWidget(self.cell_count_scale_combo, 1) # Add stretch
                    group_layout.addLayout(cc_scale_layout)

                    # Thickness Scale
                    thickness_scale_label = QLabel("Thickness Scale:")
                    self.thickness_scale_combo = QComboBox()
                    self.thickness_scale_combo.addItems(["Absolute", "Percentage", "PctChangeFromMean"])
                    current_th_scale = self.parameters.get("ThicknessScale", "Absolute") # Use .get for safety
                    idx_th = self.thickness_scale_combo.findText(current_th_scale)
                    if idx_th >= 0: self.thickness_scale_combo.setCurrentIndex(idx_th)
                    self.thickness_scale_combo.currentTextChanged.connect(
                        lambda val: self.parameters.update({"ThicknessScale": val})
                    )
                    th_scale_layout = QHBoxLayout()
                    th_scale_layout.addWidget(thickness_scale_label)
                    th_scale_layout.addWidget(self.thickness_scale_combo, 1) # Add stretch
                    group_layout.addLayout(th_scale_layout)

                    scroll_layout.addWidget(group_box)
            else: # Generic handling for other tabs
                for subcategory, params in subcategories.items():
                    group_box = QGroupBox(subcategory)
                    group_layout = QVBoxLayout()
                    group_box.setLayout(group_layout)

                    for param, description in params.items():
                        if param in self.parameters:
                            defaults_for_param = self.global_defaults.get(param, {})
                            widget = ParameterItemWidget(param, self.parameters[param],
                                                            description, defaults_for_param)
                            self.parameter_widgets[param] = widget
                            label = QLabel(self.display_name_mapping.get(param, param))
                            label.setToolTip(description)
                            param_layout = QHBoxLayout()
                            param_layout.addWidget(label) # Default stretch 0
                            param_layout.addWidget(widget, 1) # Stretch 1
                            group_layout.addLayout(param_layout)

                    scroll_layout.addWidget(group_box)

            # --- Finalize Tab ---
            scroll_layout.addStretch() # Add stretch at the end of the scroll layout
            scroll_area.setWidget(scroll_widget)
            scroll_area.setWidgetResizable(True)
            tab_layout.addWidget(scroll_area)
            self.tab_widget.addTab(tab, main_category)
        print("--- Finished create_tabs ---") # Debug

    def update_wound_parameters_visibility(self, selected_text=None):
        """Shows/hides Mechanical Injury, Chemical Injury, Chemical Diffusion groups."""

        # Get current selection if not provided
        if selected_text is None:
            if self.injury_type_widget and hasattr(self.injury_type_widget, 'value_widget') and hasattr(self.injury_type_widget.value_widget, 'currentText'):
                selected_text = self.injury_type_widget.value_widget.currentText()
            else:
                # print("Warning: InjuryType widget not ready for visibility update.") # Can be noisy
                return

        print(f"[Visibility Update] Selected Type: '{selected_text}'") # Debug

        # Expected values from combo box: 'ABLATION' or 'CHEMICAL'
        show_mechanical = (selected_text == 'ABLATION')
        show_chemical = (selected_text == 'CHEMICAL')

        # Define the keys based on schema subcategories
        mechanical_key = 'Mechanical Injury'
        chemical_injury_key = 'Chemical Injury'
        chemical_diffusion_key = 'Chemical Diffusion' # <-- Added this key
        # --- Explicitly Show/Hide Each Group ---
        mech_group = self.wound_parameters_group_boxes.get(mechanical_key)
        if mech_group: mech_group.setVisible(show_mechanical)
        # else: print(f"  Warning: '{mechanical_key}' group box not found.")

        chem_inj_group = self.wound_parameters_group_boxes.get(chemical_injury_key)
        if chem_inj_group: chem_inj_group.setVisible(show_chemical)
        # else: print(f"  Warning: '{chemical_injury_key}' group box not found.")

        # Chemical Diffusion - Visible ONLY when Chemical Injury is selected
        chem_diff_group = self.wound_parameters_group_boxes.get(chemical_diffusion_key)
        if chem_diff_group: chem_diff_group.setVisible(show_chemical)
        # else: print(f"  Warning: '{chemical_diffusion_key}' group box not found.")

        print(f"  Set Visibility: Mech={show_mechanical}, ChemInj={show_chemical}, ChemDiff={show_chemical}") # Debug
        # # --- Explicitly Show/Hide Each Group ---
        # # Mechanical
        # mech_group = self.wound_parameters_group_boxes.get(mechanical_key)
        # if mech_group:
        #     mech_group.setVisible(show_mechanical)
        #     print(f"  Setting '{mechanical_key}' visibility: {show_mechanical}") # Debug
        # else:
        #     print(f"  Warning: '{mechanical_key}' group box not found.") # Debug

        # # Chemical Injury
        # chem_inj_group = self.wound_parameters_group_boxes.get(chemical_injury_key)
        # if chem_inj_group:
        #     chem_inj_group.setVisible(show_chemical)
        #     print(f"  Setting '{chemical_injury_key}' visibility: {show_chemical}") # Debug
        # else:
        #     print(f"  Warning: '{chemical_injury_key}' group box not found.") # Debug

        # # Chemical Diffusion - Visible ONLY when Chemical Injury is selected
        # chem_diff_group = self.wound_parameters_group_boxes.get(chemical_diffusion_key)
        # if chem_diff_group:
        #     chem_diff_group.setVisible(show_chemical) # Show/Hide along with Chemical Injury
        #     print(f"  Setting '{chemical_diffusion_key}' visibility: {show_chemical}") # Debug
        # else:
        #     print(f"  Warning: '{chemical_diffusion_key}' group box not found.") # Debug

    def update_wound_parameters_enablement(self):
        """Enables/disables relevant widgets AND sets visibility based on IsInjury checkbox."""
        if self.is_injury_checkbox is None:
            # print("Debug: IsInjury checkbox not ready for enablement update.")
            return

        is_injury_enabled = self.is_injury_checkbox.isChecked()
        print(f"[Enablement Update] IsInjury={is_injury_enabled}") # Debug

        # Enable/disable all widgets specifically listed for injury control
        # (This includes InjuryType, InjuryTime, and all params in Mech/Chem/Diffusion groups)
        # print(f"  Updating enablement for {len(self.injury_parameter_widgets)} injury-related widgets...") # Debug
        for widget in self.injury_parameter_widgets:
            if widget:
                try:
                    widget.setEnabled(is_injury_enabled)
                except RuntimeError: # Handle case where widget might be deleted
                    print(f"  Warning: Could not set enablement for a (likely deleted) widget.")

        # --- Update Visibility ---
        mechanical_key = 'Mechanical Injury'
        chemical_injury_key = 'Chemical Injury'
        chemical_diffusion_key = 'Chemical Diffusion'

        if is_injury_enabled:
            # If injury is ON, call visibility function to show the *correct* specific groups
            print("  Injury enabled, updating specific group visibility...") # Debug
            self.update_wound_parameters_visibility() # Gets current value from combo box
        else:
            # If injury is OFF, explicitly hide ALL injury-specific groups
            print("  Injury disabled, hiding specific injury groups...") # Debug
            mech_group = self.wound_parameters_group_boxes.get(mechanical_key)
            chem_inj_group = self.wound_parameters_group_boxes.get(chemical_injury_key)
            chem_diff_group = self.wound_parameters_group_boxes.get(chemical_diffusion_key)

            if mech_group: mech_group.setVisible(False)
            if chem_inj_group: chem_inj_group.setVisible(False)
            if chem_diff_group: chem_diff_group.setVisible(False)
            print(f"  Hiding specific groups: Mech={mech_group is not None}, ChemInj={chem_inj_group is not None}, ChemDiff={chem_diff_group is not None}") # Debug

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
            active_threads = []
            for thread, worker in self.simulation_threads:
                if thread.isRunning():
                    try:
                        thread.terminate() # Abruptly stops the thread
                        thread.wait(1000) # Waits up to 1 sec
                        print(f"  Terminated thread {thread}")
                    except Exception as e:
                        print(f"  Error terminating thread {thread}: {e}")
                else:
                     print(f"  Thread {thread} already finished.")
                # Keep track even if finished to potentially clean up later
                active_threads.append((thread, worker))


            # Optionally clear the list or wait for signals if needed
            self.simulation_threads = [] # Clear the list after attempting termination

            QMessageBox.information(self, "Cancelled", "Attempted to cancel all simulation runs.")
            # Finalize immediately as termination is forceful
            self.finalize_sweep(was_cancelled=True)

    def save_parameters(self):
        """
        Updates the internal self.parameters dictionary from the GUI widgets.
        Does NOT perform unit conversions here; that happens before simulation run.
        """
        print("Saving parameters from GUI to internal dictionary...") # Debug
        try:
            for param_name, widget in self.parameter_widgets.items():
                if isinstance(widget, ParameterItemWidget):
                    value = widget.get_value()
                    # print(f"  Updating '{param_name}' to: {value} (type: {type(value)})") # Debug
                    self.parameters[param_name] = value
                elif isinstance(widget, QCheckBox): # Handle IsInjury directly
                    checked = widget.isChecked()
                    # print(f"  Updating '{param_name}' to: {checked} (type: {type(checked)})") # Debug
                    self.parameters[param_name] = checked
                # Handle scale combos separately if needed, though they update self.parameters directly via lambda

            # print("Internal parameters updated from GUI.")
            # Note: Unit conversion (Days to MCS) is now handled in run_simulation/save_sweep_parameters

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error updating parameters from GUI: {str(e)}")
            print(f"Error in save_parameters: {e}") # Debug
            # Re-raise or handle as appropriate

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
        Reads parameters from GUI, identifies sweep lists, prepares base parameters,
        AND performs unit conversions (Days to MCS) for simulation.
        Updates self.sweep_parameters and self.base_parameters.
        """
        print("Identifying sweep parameters and converting units...") # Debug
        self.sweep_parameters = {}
        self.base_parameters = {}
        temp_gui_params = {} # Store raw GUI values first

        # 1. Get raw values from GUI widgets
        for param_name, widget in self.parameter_widgets.items():
            if isinstance(widget, ParameterItemWidget):
                temp_gui_params[param_name] = widget.get_value()
            elif isinstance(widget, QCheckBox): # Handle IsInjury directly
                temp_gui_params[param_name] = widget.isChecked()

        # Add scale combo values (they modify self.parameters directly, but read here for consistency)
        temp_gui_params["CellCountScale"] = self.cell_count_scale_combo.currentText()
        temp_gui_params["ThicknessScale"] = self.thickness_scale_combo.currentText()

        # 2. Identify sweeps and perform conversions
        for param_name, value in temp_gui_params.items():
            converted_value = value # Start with original value

            # Apply Days -> MCS conversion *before* checking for sweeps
            if param_name == 'SimTime':
                try:
                    sim_time_days = float(value)
                    converted_value = int(sim_time_days * 240)
                    # print(f"  Converted SimTime: {value} days -> {converted_value} MCS") # Debug
                except ValueError:
                    QMessageBox.warning(self, "Conversion Error", f"Invalid value for SimTime: '{value}'. Using 0.")
                    converted_value = 0
            elif param_name == 'InjuryTime':
                 try:
                    injury_time_days = float(value)
                    converted_value = int(injury_time_days * 240)
                    # print(f"  Converted InjuryTime: {value} days -> {converted_value} MCS") # Debug
                 except ValueError:
                    QMessageBox.warning(self, "Conversion Error", f"Invalid value for InjuryTime: '{value}'. Using 0.")
                    converted_value = 0

            # Check for comma-separated string *after* potential conversion
            current_value_str = str(converted_value) # Use string representation for check
            if isinstance(current_value_str, str) and ',' in current_value_str:
                try:
                    # Parse the potentially converted value string
                    value_list = [self.convert_to_number(v.strip()) for v in current_value_str.split(',')]
                    self.sweep_parameters[param_name] = value_list
                    self.base_parameters[param_name] = value_list[0]  # Use first value as base
                    print(f"  Identified sweep for '{param_name}': {value_list}") # Debug
                except Exception as e:
                    QMessageBox.warning(self, "Parse Error", f"Could not parse list for {param_name} (value: '{current_value_str}'): {e}")
                    self.base_parameters[param_name] = converted_value # Treat as single (converted) value
            else:
                self.base_parameters[param_name] = converted_value # Store single (converted) value

        # Update self.parameters with the single, converted base values for non-sweep runs
        self.parameters = self.base_parameters.copy()

        print(f"Sweep Parameters identified: {self.sweep_parameters}") # Debug
        print(f"Base Parameters (for simulation): {self.base_parameters}") # Debug
        return bool(self.sweep_parameters)

    def generate_sweep_combinations(self):
        """Generates list of parameter dictionaries for sweep runs."""
        if not self.sweep_parameters:
            # If no sweeps, return a list containing just the base parameters
            print("No sweep parameters found, generating single combination.") # Debug
            return [self.base_parameters.copy()]

        from itertools import product
        param_names = list(self.sweep_parameters.keys())
        param_values = [self.sweep_parameters[name] for name in param_names]
        print(f"Generating combinations for: {param_names}") # Debug

        combinations = []
        for i, value_combination in enumerate(product(*param_values)):
            combination = self.base_parameters.copy() # Start with base
            for name, value in zip(param_names, value_combination):
                combination[name] = value # Override with sweep value
            combinations.append(combination)
            # print(f"  Generated Combination {i+1}: {combination}") # Debug - can be verbose

        print(f"Generated {len(combinations)} parameter combinations.") # Debug
        return combinations

    def export_parameters(self):
        """Exports the current internal parameter state (in GUI units) to JSON."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Parameters", "", "JSON Files (*.json)")
        if file_path:
            try:
                # Create a temporary dict with GUI units (convert MCS back to Days)
                export_params = self.parameters.copy() # Start with current state
                if 'SimTime' in export_params:
                    export_params['SimTime'] = float(export_params['SimTime']) / 240.0
                if 'InjuryTime' in export_params:
                     export_params['InjuryTime'] = float(export_params['InjuryTime']) / 240.0

                with open(file_path, "w") as json_file:
                    json.dump(export_params, json_file, indent=4)
                QMessageBox.information(self, "Success", f"Parameters exported to '{file_path}' successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error exporting parameters: {str(e)}")

    def import_parameters(self):
        """Imports parameters from JSON (expects GUI units) and updates GUI."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Parameters", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, "r") as json_file:
                    imported_params = json.load(json_file)

                # Assume imported file uses GUI units (Days)
                # Update internal self.parameters
                self.parameters.update(imported_params)

                QMessageBox.information(self, "Success", f"Parameters imported from '{file_path}'.")
                # Update the GUI widgets to reflect the imported values
                self.update_parameter_widgets(self.parameters)

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error importing parameters: {str(e)}")

    def load_gui_config(self):
        """Loads GUI settings like paths from JSON."""
        if self.gui_config_file.exists():
            try:
                with open(self.gui_config_file, 'r') as f:
                    config = json.load(f)

                last_path = config.get("vcornea_repository_path")
                if last_path: # Don't check exists here, let load_schema handle invalid path
                    self.model_path_line_edit.setText(last_path)
                    print(f"Loaded saved repository path: {last_path}")
                    # Schema loading now happens AFTER this in __init__

                last_conda_env = config.get("conda_env_name")
                if last_conda_env:
                    self.conda_env_line_edit.setText(last_conda_env)

                last_output_dir = config.get("output_directory")
                if last_output_dir:
                    self.output_dir_line_edit.setText(last_output_dir)

            except Exception as e:
                print(f"Could not load GUI config: {e}")

    def save_gui_config(self):
        """Saves current GUI path settings."""
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

    def on_repo_path_changed(self):
        """Apply repo path change only if it actually changed."""
        new_path = self.model_path_line_edit.text().strip()
        if not new_path:
            QMessageBox.warning(self, "Repository Path Missing", "Select Repository Path first.")
            return
        if new_path == self._last_repo_path:
            # No change → do nothing (prevents blip)
            return

        self._last_repo_path = new_path
        self.save_gui_config()
        try:
            print("Reloading schema due to repo path change.")
            self.load_schema_and_parameters()
        except Exception as e:
            QMessageBox.warning(self, "Schema Load Error",
                f"Could not load schema for the new path:\n{e}\nPlease ensure the path is correct.")
        
    def browse_for_model_path(self):
        """Opens directory dialog for repository path."""
        directory = QFileDialog.getExistingDirectory(self, "Select vCornea Repository Folder")
        if directory:
            self.model_path_line_edit.setText(directory)
            # Manually trigger the update after browsing
            self.on_repo_path_changed()

    def browse_for_output_dir(self):
        """Opens directory dialog for output path."""
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.output_dir_line_edit.setText(directory)
            self.save_gui_config()

    def reset_parameters(self):
        """Resets internal parameters and GUI widgets to schema defaults."""
        if not self.schema:
             QMessageBox.warning(self, "Error", "Schema not loaded. Cannot reset parameters.")
             return
        try:
            # Get defaults (these are in GUI units - Days)
            original_params = get_model_defaults(self.schema)
            # Update internal state
            self.parameters = original_params
            # Update GUI widgets
            self.update_parameter_widgets(self.parameters)
            QMessageBox.information(self, "Success", "Parameters have been reset to model defaults!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not reset parameters: {str(e)}")

    def on_model_selection_change(self):
        """Reloads schema and parameters when model version changes."""
        print("Model selection changed.") # Debug
        # Prevent reload if config is being loaded initially
        if self._loading_config:
             print("Skipping schema reload during initial config load.") # Debug
             return
        if not self.model_path_line_edit.text():
             QMessageBox.warning(self, "Repository Path Missing", "Select Repository Path first.")
             return
        try:
            print("Reloading schema due to model selection change.") # Debug
            self.load_schema_and_parameters()
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Could not load parameters for selected model:\n{str(e)}")

    def update_parameter_widgets(self, params_to_load):
        """Updates all GUI widgets to match the values in params_to_load (expects GUI units)."""
        print("Updating parameter widgets from dictionary...") # Debug
        if not self.parameter_widgets:
             print("Warning: No parameter widgets found to update.") # Debug
             return

        for param_name, widget in self.parameter_widgets.items():
            if param_name in params_to_load:
                value = params_to_load[param_name]
                try:
                    if isinstance(widget, ParameterItemWidget):
                        # print(f"  Setting '{param_name}' widget to: {value}") # Debug
                        widget.set_value(value)
                    elif isinstance(widget, QCheckBox): # Handle IsInjury directly
                        # print(f"  Setting '{param_name}' checkbox to: {bool(value)}") # Debug
                        widget.setChecked(bool(value))
                    # Note: Scale combos update self.parameters directly, no need to set here
                    # else: # Debug
                    #     print(f"  Skipping widget for '{param_name}' - type {type(widget)}")
                except Exception as e:
                     print(f"Error updating widget for '{param_name}' with value '{value}': {e}") # Debug

            # else: # Debug
            #      print(f"  Parameter '{param_name}' not in params_to_load, widget not updated.")


        # Trigger visibility/enablement updates AFTER setting all values
        print("Triggering post-update visibility/enablement checks...") # Debug
        self.update_wound_parameters_enablement()
        # self.update_wound_parameters_visibility() # Enablement handles visibility

    def validate_time_parameters(self):
        """Validates SimTime and InjuryTime (expects GUI units - Days)."""
        # (This logic seems okay, ensures values are floats before comparison)
        STABLE_TIME_DAYS = 2.0
        MIN_PRE_INJURY_MEASUREMENT_DAYS = 1.0
        MIN_POST_INJURY_MEASUREMENT_DAYS = 7.0
        MIN_NO_INJURY_MEASUREMENT_DAYS = 7.0

        try:
            sim_time_widget = self.parameter_widgets.get('SimTime')
            is_injury_widget = self.parameter_widgets.get('IsInjury')
            injury_time_widget = self.parameter_widgets.get('InjuryTime')

            if not sim_time_widget: return True # Cannot validate if widget missing

            sim_time_days = float(sim_time_widget.get_value())

            is_injury = False
            if isinstance(is_injury_widget, QCheckBox): is_injury = is_injury_widget.isChecked()
            elif is_injury_widget: is_injury = is_injury_widget.get_value()

            issues = []
            corrections = {}

            if not is_injury:
                min_sim_time = STABLE_TIME_DAYS + MIN_NO_INJURY_MEASUREMENT_DAYS
                if sim_time_days < min_sim_time:
                    issues.append(f"• Simulation time ({sim_time_days}d) < minimum ({min_sim_time}d) for no injury.")
                    corrections['SimTime'] = min_sim_time
            else:
                 if not injury_time_widget: return True # Cannot validate if widget missing
                 injury_time_days = float(injury_time_widget.get_value())

                 min_injury_time = STABLE_TIME_DAYS + MIN_PRE_INJURY_MEASUREMENT_DAYS
                 if injury_time_days < min_injury_time:
                     issues.append(f"• Injury time ({injury_time_days}d) < minimum ({min_injury_time}d).")
                     corrections['InjuryTime'] = min_injury_time
                     injury_time_days = min_injury_time # Use corrected for next check

                 time_after_injury = sim_time_days - injury_time_days
                 if time_after_injury < MIN_POST_INJURY_MEASUREMENT_DAYS:
                     required_sim_time = injury_time_days + MIN_POST_INJURY_MEASUREMENT_DAYS
                     issues.append(f"• Post-injury time ({time_after_injury:.1f}d) < minimum ({MIN_POST_INJURY_MEASUREMENT_DAYS}d). Requires SimTime >= {required_sim_time}d.")
                     corrections['SimTime'] = required_sim_time
                     sim_time_days = required_sim_time # Use corrected

                 min_total_sim_time = STABLE_TIME_DAYS + MIN_PRE_INJURY_MEASUREMENT_DAYS + MIN_POST_INJURY_MEASUREMENT_DAYS
                 if sim_time_days < min_total_sim_time:
                     issues.append(f"• Total SimTime ({sim_time_days}d) < minimum ({min_total_sim_time}d) for injury.")
                     corrections['SimTime'] = min_total_sim_time

            if issues:
                error_msg = "Time Parameter Validation Failed:\n\n" + "\n".join(issues) + "\n\nCorrections applied:\n"
                for param, value in corrections.items():
                    error_msg += f"  • {param}: {value} days\n"
                    self.parameter_widgets[param].set_value(value)
                    self.parameters[param] = value # Update internal dict too
                QMessageBox.warning(self, "Invalid Time Parameters", error_msg)
                return False

            return True
        except Exception as e:
            QMessageBox.critical(self, "Validation Error", f"Error during time validation: {e}")
            return False # Fail validation on error

    def run_simulation(self):
        """Prepares parameters (including unit conversion) and starts the sweep/run."""
        try:
            from datetime import datetime

            if not self.validate_time_parameters():
                reply = QMessageBox.question(self, "Continue?", "Time parameters corrected. Continue?", QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.No: return

            # 1. Prepare parameters for simulation (gets sweep/base, converts units)
            is_sweep = self.save_sweep_parameters()
            self.parameter_combinations = self.generate_sweep_combinations() # Uses self.base_parameters, self.sweep_parameters
            self.total_combinations = len(self.parameter_combinations)

            if self.total_combinations == 0:
                QMessageBox.warning(self, "Error", "No parameter combinations generated.")
                return

            # --- Setup UI for running ---
            self.run_simulation_button.setEnabled(False)
            self.cancel_button.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(self.total_combinations)
            self.progress_bar.setValue(0)
            self.statusBar().showMessage(f"Starting {('sweep with ' + str(self.total_combinations) + ' combinations') if is_sweep else 'single run'}...")
            QApplication.processEvents()

            # 2. Setup Output Directory
            base_output_dir = Path(self.output_dir_line_edit.text())
            custom_name = self.run_name_line_edit.text().strip()
            folder_name = custom_name.replace(' ', '_') if custom_name else f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.sweep_output_folder = base_output_dir / folder_name
            self.sweep_output_folder.mkdir(parents=True, exist_ok=True)
            print(f"Run results will be saved in: {self.sweep_output_folder}")

            # 3. Initialize counters/threads
            self.simulation_threads = []
            self.completed_combinations = 0
            # QMessageBox.information(self, "Run Started", f"Launching {self.total_combinations} combination(s).")

            # 4. Launch Worker Threads
            conda_env = self.conda_env_line_edit.text()
            replicates_per_combo = self.replicate_input.value()
            base_repo_path = Path(self.model_path_line_edit.text())
            selected_model_key = self.model_selection_combo.currentText()
            model_sub_path = self.model_mapping.get(selected_model_key)
            source_project_path = str(base_repo_path / model_sub_path)

            for i, sim_params_mcs in enumerate(self.parameter_combinations):
                print(f"Launching thread for Combination {i+1}...")
                # Parameters are already in MCS from save_sweep_parameters/generate_sweep_combinations

                process_config = {
                    'vcornea_project_path': source_project_path,
                    'cc3d_conda_env_name': conda_env,
                    'output_base_dir': str(self.sweep_output_folder),
                    'replicates': replicates_per_combo,
                    # Unique ID for this specific combination within the sweep/run
                    'run_id': f'combo_{i+1:03d}' if self.total_combinations > 1 else 'run_1'
                }

                thread = QThread()
                # Pass parameters already in simulation units (MCS)
                worker = SimulationWorker(process_config, sim_params_mcs)
                worker.moveToThread(thread)

                thread.started.connect(worker.run)
                worker.finished.connect(self.on_run_finished)
                worker.error.connect(self.on_run_error)
                worker.finished.connect(thread.quit)
                worker.finished.connect(worker.deleteLater)
                thread.finished.connect(thread.deleteLater)

                thread.start()
                self.simulation_threads.append((thread, worker))

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to start simulation run/sweep: {str(e)}")
            # Reset UI if setup failed
            self.run_simulation_button.setEnabled(True)
            self.cancel_button.setEnabled(False)
            self.progress_bar.setVisible(False)

    def on_run_finished(self, output):
        """SLOT: Handles successful completion of one combination."""
        self.completed_combinations += 1
        run_name = output.get('outputs', {}).get('run_metadata', {}).get('run_name', 'unknown_run')
        print(f"SUCCESS: Combination '{run_name}' finished. Progress: {self.completed_combinations}/{self.total_combinations}")

        self.progress_bar.setValue(self.completed_combinations)
        self.statusBar().showMessage(f"Completed {self.completed_combinations} of {self.total_combinations} combinations.")
        QApplication.processEvents()

        if self.completed_combinations >= self.total_combinations:
            self.finalize_sweep()

    def on_run_error(self, error_message):
        """SLOT: Handles failed completion of one combination."""
        self.completed_combinations += 1
        # Extract run_id if possible from the error message or worker (needs modification to SimulationWorker)
        # run_id_info = error_message.get('run_id', 'unknown') # Assuming error is a dict
        print(f"FAILURE: A combination failed. Progress: {self.completed_combinations}/{self.total_combinations}")
        print(f"ERROR DETAILS: {error_message}")

        self.progress_bar.setValue(self.completed_combinations)
        self.statusBar().showMessage(f"Completed {self.completed_combinations} of {self.total_combinations} (with errors).")
        QApplication.processEvents()

        if self.completed_combinations >= self.total_combinations:
            self.finalize_sweep()

    def finalize_sweep(self, was_cancelled=False):
        """Cleans up UI after all combinations finish or are cancelled."""
        if was_cancelled:
            status_message = f"Run Cancelled. {self.completed_combinations} of {self.total_combinations} processed."
        else:
            status_message = f"Run Complete! {self.completed_combinations} of {self.total_combinations} processed."

        self.statusBar().showMessage(status_message)
        # Ensure progress bar shows complete even if cancelled
        self.progress_bar.setValue(self.total_combinations)

        self.run_simulation_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

        print("Run finalize.")
        if not was_cancelled:
            QMessageBox.information(self, "Run Complete",
                f"The run/sweep has finished.\n"
                f"{self.completed_combinations}/{self.total_combinations} combinations processed.\n"
                f"Results in: {self.sweep_output_folder}")

        # Clear thread list only after finalization
        self.simulation_threads = []

    def get_plot_settings(self):
        """Gets plot-related settings from internal parameters."""
        # This seems okay, uses self.parameter_structure and self.parameters
        plot_settings = {}
        try:
            # Check if Plots structure exists
            if "Plots" in self.parameter_structure and \
               "DATA COLECTION AND REAL-TIME PLOTS" in self.parameter_structure["Plots"]:
                 plots_params = self.parameter_structure["Plots"]["DATA COLECTION AND REAL-TIME PLOTS"]
                 for param in plots_params.keys():
                     plot_settings[param] = self.parameters.get(param) # Use .get for safety
            else:
                 print("Warning: Plot structure not found in parameter_structure.")
                 # Manually check for known plot params if structure is missing
                 for param in ['CellCount', 'ThicknessPlot', 'CellCountScale', 'ThicknessScale']:
                      if param in self.parameters:
                           plot_settings[param] = self.parameters[param]


            # Add scale settings directly from combos
            plot_settings['CellCountScale'] = self.cell_count_scale_combo.currentText()
            plot_settings['ThicknessScale'] = self.thickness_scale_combo.currentText()

            print("Plot settings retrieved:", plot_settings)
            return plot_settings

        except KeyError as e:
             print(f"Error accessing plot settings structure: {e}")
             return {} # Return empty dict on error
        except Exception as e:
            print(f"Error getting plot settings: {e}")
            return {}

    def plot_results(self):
        """Opens dialog to select output dir and plots results using PlotManager."""
        # (This logic seems okay, relies on PlotManager reading metadata)
        start_dir = self.output_dir_line_edit.text()
        if not start_dir or not Path(start_dir).exists(): start_dir = str(Path.home())

        directory_to_plot = QFileDialog.getExistingDirectory(self,"Select Output Directory to Plot", start_dir)
        if not directory_to_plot: return

        try:
            plot_manager = PlotManager(Data_DIR=directory_to_plot, Out_DIR=directory_to_plot)

            # Get plot selections from current GUI state (widgets)
            cell_count_widget = self.parameter_widgets.get('CellCount')
            thickness_widget = self.parameter_widgets.get('ThicknessPlot')

            plot_cell_count = cell_count_widget.get_value() if cell_count_widget else False
            plot_thickness = thickness_widget.get_value() if thickness_widget else False

            cell_count_scale = self.cell_count_scale_combo.currentText()
            thickness_scale = self.thickness_scale_combo.currentText()

            generated_plots = []
            if plot_cell_count:
                print("Plotting Cell Count...")
                plot_manager.plot_count( mode='full', scale_option=cell_count_scale)
                generated_plots.append("Cell Count")

            if plot_thickness:
                print("Plotting Thickness...")
                plot_manager.plot_thickness(scale_option=thickness_scale)
                generated_plots.append("Thickness")

            if not generated_plots:
                QMessageBox.information(self, "Plotting", "No plot types selected in GUI.")
            else:
                info_msg = f"Plots generated for: {', '.join(generated_plots)}\nData Source: {directory_to_plot}\n\n"
                info_msg += f"Metadata Params:\n"
                info_msg += f"  Injury: {'Yes' if plot_manager.is_injury else 'No'}"
                if plot_manager.is_injury: info_msg += f" at {plot_manager.injury_time_mcs/240:.1f} days"
                info_msg += f"\n  Sim Time: {plot_manager.sim_time_mcs/240:.1f} days"
                QMessageBox.information(self, "Plotting Complete", info_msg)

        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Plotting Error", f"Error during plotting: {str(e)}")

    def revert_tab_to_defaults(self, tab_name, reference):
        """Reverts parameters in a tab to defaults for a specific reference."""
        print(f"Reverting tab '{tab_name}' to defaults for reference '{reference}'") # Debug
        if reference == "custom":
            # QMessageBox.information(self, "Reversion", "Select a specific reference to revert.")
            return # Don't revert if custom is selected

        reverted_params = []
        try:
            if tab_name not in self.parameter_structure:
                 print(f"Warning: Tab '{tab_name}' not found in parameter structure.")
                 return

            for subcategory, params in self.parameter_structure[tab_name].items():
                 # Map schema subcat back to old cell type key for defaults lookup if needed
                cell_type_key_for_defaults = SCHEMA_SUBCAT_TO_CELL_TYPE.get(subcategory) if tab_name == "Cells Parameters" else None

                for param in params.keys():
                    if param in self.parameter_widgets:
                        defaults_source = None
                        # Check cell-specific defaults first
                        if cell_type_key_for_defaults and cell_type_key_for_defaults in self.cell_type_defaults and param in self.cell_type_defaults[cell_type_key_for_defaults]:
                             defaults_source = self.cell_type_defaults[cell_type_key_for_defaults][param]
                        # Fallback to global defaults
                        elif param in self.global_defaults:
                             defaults_source = self.global_defaults[param]

                        if defaults_source and reference in defaults_source:
                            default_val = defaults_source[reference]
                            widget = self.parameter_widgets[param]
                            widget.set_value(default_val) # This updates widget & sets ref dropdown
                            self.parameters[param] = default_val # Update internal dict
                            reverted_params.append(param)
                        # else: # Debug
                        #      print(f"  No default found for '{param}' with reference '{reference}'")

            if reverted_params:
                QMessageBox.information(self, "Reversion", f"Reverted parameters in '{tab_name}' to defaults for '{reference}'.")
                print(f"  Reverted: {reverted_params}") # Debug
            else:
                 QMessageBox.warning(self, "Reversion", f"No default values found for reference '{reference}' in tab '{tab_name}'.")

        except Exception as e:
             QMessageBox.critical(self, "Reversion Error", f"Error reverting defaults: {e}")
             print(f"Error in revert_tab_to_defaults: {e}") # Debug

    def revert_cell_type_defaults(self, subcategory, ref, params_dict):
        """Reverts parameters for a specific cell type group to defaults."""
        print(f"Reverting cell type '{subcategory}' to defaults for reference '{ref}'") # Debug
        if ref == "custom":
            # QMessageBox.information(self, "Reversion", f"Select a specific reference.")
            return

        # Map schema subcat back to old cell type key for defaults lookup
        cell_type_key_for_defaults = SCHEMA_SUBCAT_TO_CELL_TYPE.get(subcategory)
        if not cell_type_key_for_defaults or cell_type_key_for_defaults not in self.cell_type_defaults:
             QMessageBox.warning(self, "Reversion Error", f"No cell type defaults found for '{subcategory}'.")
             return

        defaults_for_cell = self.cell_type_defaults[cell_type_key_for_defaults]
        reverted_params = []
        try:
            for param in params_dict.keys(): # Iterate through params in this group
                if param in self.parameter_widgets and param in defaults_for_cell:
                    defaults_source = defaults_for_cell[param]
                    if ref in defaults_source:
                        default_val = defaults_source[ref]
                        widget = self.parameter_widgets[param]
                        widget.set_value(default_val) # Updates widget & dropdown
                        self.parameters[param] = default_val # Update internal dict
                        reverted_params.append(param)
                    # else: # Debug
                    #      print(f"  No default found for '{param}' (cell type {subcategory}) with reference '{ref}'")


            if reverted_params:
                QMessageBox.information(self, "Reversion", f"Reverted '{subcategory}' to defaults for '{ref}'.")
                print(f"  Reverted: {reverted_params}") # Debug
            else:
                 QMessageBox.warning(self, "Reversion", f"No default values found for reference '{ref}' for cell type '{subcategory}'.")

        except Exception as e:
             QMessageBox.critical(self, "Reversion Error", f"Error reverting cell type defaults: {e}")
             print(f"Error in revert_cell_type_defaults: {e}") # Debug  
  
# ----------------------------------------------------------------------------------------------------------------------------------------------
