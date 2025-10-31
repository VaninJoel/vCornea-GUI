import json
import pandas as pd
from pathlib import Path
from typing import Dict, Union, Tuple, Any

def read_parameters_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Read parameters from a Python file containing parameter assignments.
    
    Args:
        file_path: Path to the parameters file
        
    Returns:
        Dictionary containing parameter names and values
    """
    parameters = {}
    file_path = Path(file_path)
    
    try:
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

        # Convert MCS to days for GUI display
        if "SimTime" in parameters:
            parameters["SimTime"] = parameters["SimTime"] / 240.0
        if "InjuryTime" in parameters:
            parameters["InjuryTime"] = parameters["InjuryTime"] / 240.0

        return parameters
    except Exception as e:
        raise ValueError(f"Error reading parameters file: {str(e)}")

def save_parameters_file(file_path: Union[str, Path], params: Dict[str, Any]) -> None:
    """
    Save parameters to a Python file.
    
    Args:
        file_path: Path where to save the parameters
        params: Dictionary of parameters to save
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(file_path, 'w') as file:
            for key, value in params.items():
                if isinstance(value, str):
                    value = f"'{value}'"
                file.write(f"{key} = {value}\n")
    except Exception as e:
        raise ValueError(f"Error saving parameters file: {str(e)}")

def export_parameters_json(file_path: Union[str, Path], params: Dict[str, Any]) -> None:
    """
    Export parameters to a JSON file.
    
    Args:
        file_path: Path where to save the JSON file
        params: Dictionary of parameters to export
    """
    try:
        with open(file_path, "w") as json_file:
            json.dump(params, json_file, indent=4)
    except Exception as e:
        raise ValueError(f"Error exporting parameters to JSON: {str(e)}")

def import_parameters_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Import parameters from a JSON file.
    
    Args:
        file_path: Path to the JSON file to import
        
    Returns:
        Dictionary containing the imported parameters
    """
    try:
        with open(file_path, "r") as json_file:
            params = json.load(json_file)
            
        # Convert MCS to days for GUI display
        if "SimTime" in params:
            params["SimTime"] = params["SimTime"] / 240.0
        if "InjuryTime" in params:
            params["InjuryTime"] = params["InjuryTime"] / 240.0
            
        return params
    except Exception as e:
        raise ValueError(f"Error importing parameters from JSON: {str(e)}")

def read_csv_file(file_path: Union[str, Path]) -> pd.DataFrame:
    """
    Read data from a CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        pandas DataFrame containing the CSV data
    """
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {str(e)}")

def read_parquet_file(file_path: Union[str, Path]) -> pd.DataFrame:
    """
    Read data from a Parquet file.
    
    Args:
        file_path: Path to the Parquet file
        
    Returns:
        pandas DataFrame containing the Parquet data
    """
    try:
        return pd.read_parquet(file_path)
    except Exception as e:
        raise ValueError(f"Error reading Parquet file: {str(e)}")
    
def load_json_file(file_path: Path) -> Dict:
    """Generic JSON file loader with error handling."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise ValueError(f"Error loading JSON file {file_path}: {str(e)}")

def load_parameter_defaults(file_path: Path) -> Tuple[Dict, Dict]:
    """
    Load parameter defaults from JSON file.
    Returns tuple of (global_defaults, cell_type_defaults)
    """
    try:
        data = load_json_file(file_path)
        
        # Remove the "default" key from each parameter mapping
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
    except Exception as e:
        raise ValueError(f"Error processing parameter defaults: {str(e)}")

def load_original_parameters(file_path: Path) -> Dict[str, Any]:
    """
    Load original parameters from JSON file and convert time units if needed.
    """
    try:
        original_params = load_json_file(file_path)
        
        # Convert MCS to days for GUI display
        if "SimTime" in original_params:
            original_params["SimTime"] = original_params["SimTime"] / 240.0
        if "InjuryTime" in original_params:
            original_params["InjuryTime"] = original_params["InjuryTime"] / 240.0
            
        return original_params
    except Exception as e:
        raise ValueError(f"Error loading original parameters: {str(e)}")