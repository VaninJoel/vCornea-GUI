"""
Utility module to extract parameter information from the VCorneaProcess schema
in the format expected by the existing GUI (main_window.py).

This replaces the need for:
- parameter_structure.py
- display_mapping.py
- parameter_defaults.json (via load_parameter_defaults)
- original_parameters.json (via get_model_defaults)
"""

# --- Mappings to bridge new schema with old GUI expectations ---

# Maps schema _category to the GUI Tab name
# This is crucial for main_window.py's special logic (e.g., for "Wound Parameters")
CATEGORY_TO_TAB_MAP = {
    'Cell Properties': 'Cells Parameters',
    'Growth Factors': 'Fields',
    'Tissue Guidance': 'Fields', # Merge into Fields tab
    'Tissue Mechanics': 'Links',
    'Injury Settings': 'Wound Parameters',
    'Simulation Control': 'Functions Control',
    'Visualization': 'Plots',
    'Data Collection': 'Plots', # Merge into Plots tab
    'Simulation Setup': 'Simulation Time',
    'General': 'General', # Fallback
}

# Defines the order of tabs in the GUI
TAB_ORDER = [
    'Cells Parameters',
    'Fields',
    'Links',
    'Wound Parameters',
    'Functions Control',
    'Plots',
    'Simulation Time',
]

# Maps schema _subcategory (for "Cell Properties") to the old cell_type keys
# This is crucial for main_window.py's default-loading logic
SCHEMA_SUBCAT_TO_CELL_TYPE = {
    'Stem Cells': 'STEM',
    'Basal Cells': 'BASAL',
    'Wing Cells': 'WING',
    'Superficial Cells': 'SUPERFICIAL',
}


def get_parameter_structure(schema):
    """
    Extracts the parameter structure (Tabs > Groups > Params) from the schema
    in the format expected by main_window.py's create_tabs method.
    (Replaces parameter_structure.py)
    
    Args:
        schema (dict): The ports schema from VCorneaProcess
    
    Returns:
        dict: {tab_name: {group_name: {param_name: description, ...}, ...}, ...}
    """
    # Initialize structure with the correct tab order
    structure = {tab: {} for tab in TAB_ORDER}
    
    if 'inputs' not in schema:
        return structure
        
    for param_name, param_info in schema['inputs'].items():
        category = param_info.get('_category', 'General')
        subcategory = param_info.get('_subcategory', 'Parameters')
        description = param_info.get('_description', '')
        
        # Map schema category to the GUI tab name
        tab_name = CATEGORY_TO_TAB_MAP.get(category, category)
        
        if tab_name not in structure:
            # Add any new/unmapped categories at the end
            structure[tab_name] = {}
            
        if subcategory not in structure[tab_name]:
            structure[tab_name][subcategory] = {}
            
        structure[tab_name][subcategory][param_name] = description
        
    # Clean up empty, pre-defined tabs
    return {tab: groups for tab, groups in structure.items() if groups}


def get_display_name_mapping(schema):
    """
    Extracts display name mappings from the schema.
    (Replaces display_mapping.py)
    
    Args:
        schema (dict): The ports schema from VCorneaProcess
    
    Returns:
        dict: {param_name: display_name, ...}
    """
    display_mapping = {}
    if 'inputs' in schema:
        for param_name, param_info in schema['inputs'].items():
            # Use _display_name if available, otherwise fallback to a formatted param_name
            fallback_name = param_name.replace('_', ' ').title()
            display_mapping[param_name] = param_info.get('_display_name', fallback_name)
    return display_mapping


def get_model_defaults(schema):
    """
    Extracts the single default value for each parameter.
    This replaces load_original_parameters() and is used for "Reset to Original".
    The GUI expects time values in 'days', which the schema _default provides.
    
    Args:
        schema (dict): The ports schema from VCorneaProcess
    
    Returns:
        dict: {param_name: default_value, ...}
    """
    defaults = {}
    if 'inputs' in schema:
        for param_name, param_info in schema['inputs'].items():
            if '_default' in param_info:
                defaults[param_name] = param_info['_default']
    return defaults


def load_parameter_defaults_from_schema(schema):
    """
    Extracts the nested default values (with references) in the format
    expected by main_window.py and parameter_item.py.
    
    This replaces the old load_parameter_defaults(json_file) function.
    
    Args:
        schema (dict): The ports schema from VCorneaProcess
    
    Returns:
        tuple: (global_defaults, cell_type_defaults)
            global_defaults = {param: {ref: val, 'default': ref}, ...}
            cell_type_defaults = {cell_type: {param: {ref: val, 'default': ref}, ...}, ...}
    """
    global_defaults = {}
    cell_type_defaults = {}
    
    if 'inputs' not in schema:
        return global_defaults, cell_type_defaults
        
    for param_name, param_info in schema['inputs'].items():
        subcategory = param_info.get('_subcategory')
        reference_info = param_info.get('_reference_paper')
        default_val = param_info.get('_default')
        
        defaults_for_param = {}
        default_ref_name = 'model_default' # Fallback ref name
        
        if reference_info and 'source' in reference_info and reference_info['source'] != 'Not specified':
            source = reference_info['source']
            
            # Use the value from the reference dict. If it's None, use the _default
            value = reference_info.get('value', default_val)
            if value is None:
                value = default_val
                
            defaults_for_param[source] = value
            default_ref_name = source
        else:
            # No reference, so just use the model's default
            defaults_for_param['model_default'] = default_val
        
        # Add the 'default' key that main_window.py expects (from parameter_defaults.json)
        defaults_for_param['default'] = default_ref_name
        
        # Assign to either global or cell-type dict based on mapped subcategory
        if subcategory in SCHEMA_SUBCAT_TO_CELL_TYPE:
            cell_type_key = SCHEMA_SUBCAT_TO_CELL_TYPE[subcategory]
            if cell_type_key not in cell_type_defaults:
                cell_type_defaults[cell_type_key] = {}
            cell_type_defaults[cell_type_key][param_name] = defaults_for_param
        else:
            global_defaults[param_name] = defaults_for_param
            
    return global_defaults, cell_type_defaults