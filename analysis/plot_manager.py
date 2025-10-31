# Save this as your new plot_manager.py

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.colors as mcolors
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
import json
from scipy.stats import probplot, skew, kurtosis, kstest, shapiro, anderson

class PlotManager:
    def __init__(self, Data_DIR, Out_DIR,  CurrentParam):
        self.data_dir = Path(Data_DIR)
        # self.out_dir = Path(Out_DIR)
        # self.parameters = CurrentParam  
        self.out_dir = Path(Out_DIR) if Out_DIR else self.data_dir
              
        self.memb_bins = self.load_memb_data()

        self.sim_time_mcs = 7700  # Default
        self.is_injury = False    # Default
        self.injury_time_mcs = 0  # Default
        self.stable_time = 480      # Default

        # Define color codes
        # self.color_codes = ['#ff007f', '#ffbe99', '#0055ff', '#55ffff'] # Stem, Basal, Wing, Super

        self.cell_color_map = {
            'Superficial': '#55ffff',
            'Wing': '#0055ff',
            'Basal': '#ffbe99',
            'Stem': '#ff007f'
        }
        
        # Collect data files using 
        self.Count_file, self.Thickness_file, self.metadata_files = self.collect_files_recursively(self.data_dir)
        
        # Extract simulation parameters
        self._load_parameters_from_metadata()
        self.max_time = self.sim_time_mcs
        
        # Load data into dictionaries of DataFrames
        self.count_data = self.data_collection(self.Count_file) if self.Count_file else {}
        self.thickness_data = self.data_collection(self.Thickness_file) if self.Thickness_file else {}

        if self.thickness_data:
            self.thick_mMEMB = self.convert_to_actual_thickness(self.thickness_data, self.memb_bins, double=True)

        # Generate the summary text from all found metadata files
        self.summary_text = self.generate_metadata_summary()

        if not self.count_data and not self.thickness_data:
            raise FileNotFoundError(f"No valid cell_count or thickness files found in {self.data_dir}")

    def _load_parameters_from_metadata(self):
        """
        Loads simulation parameters (SimTime, InjuryTime, etc.) from the first
        run_metadata.json file found in the directory.
        """
        if not self.metadata_files:
            print("Warning: No 'run_metadata.json' file found. Using default simulation parameters.")
            return

        try:
            # Use the first metadata file as the reference for simulation parameters
            with open(self.metadata_files[0]) as f:
                metadata = json.load(f)

            # Extract key parameters, with fallbacks to defaults
            config = metadata.get("simulation_config", {})
            key_params = metadata.get("key_parameters", {})

            self.is_injury = config.get("has_injury", False)
            self.sim_time_mcs = key_params.get("SimTime", 7700)
            self.injury_time_mcs = key_params.get("InjuryTime", 0)
            
            print("Successfully loaded simulation parameters from metadata:")
            print(f"  - Is Injury: {self.is_injury}")
            print(f"  - Sim Time (MCS): {self.sim_time_mcs}")
            print(f"  - Injury Time (MCS): {self.injury_time_mcs}")

        except Exception as e:
            print(f"Error reading metadata file: {e}. Using default parameters.")
    
    def collect_files_recursively(self, directory):
        """
        Recursively collects data files and metadata from a directory using rglob.
        """
        base_path = Path(directory)
        count_files = [str(p) for p in base_path.rglob("cell_count_*.csv")]
        thickness_files = [str(p) for p in base_path.rglob("thickness_rep_*.parquet")]
        metadata_files = [p for p in base_path.rglob("run_metadata.json")]
        
        print(f"Found {len(count_files)} cell count files.")
        print(f"Found {len(thickness_files)} thickness files.")
        print(f"Found {len(metadata_files)} metadata files.")
        
        return count_files, thickness_files, metadata_files

    def data_collection(self, files):
        """
        Collect data from multiple files, supporting both CSV and Parquet formats.
        
        Args:
            file: List of file paths
            
        Returns:
            dict: Dictionary containing DataFrames with keys based on file path components
        """ 
        # Load data
        grouped_data = {}
        for file_path_str in files:
            data_path = Path(file_path_str)
            try:
                if data_path.parent.name.startswith('replicate_'):
                    combo_key = data_path.parent.parent.name
                else:
                    combo_key = data_path.parent.name
                if combo_key not in grouped_data:
                    grouped_data[combo_key] = []
                if data_path.suffix.lower() == '.csv':
                    df = pd.read_csv(data_path)
                elif data_path.suffix.lower() == '.parquet':
                    df = pd.read_parquet(data_path)
                else: continue
                grouped_data[combo_key].append(df)
            except Exception as e:
                print(f"Error processing file {data_path}: {e}")
        return grouped_data
    
    def load_memb_data(self):        
        memb_data = {}
        try:
            # Data from membrane_height.csv has been embedded directly as a dictionary.
            memb_data = {
                0:10, 1:10, 2:10, 3:10, 4:10, 5:10, 6:10, 7:10, 8:10, 9:10, 10:10,
                11:10, 12:10, 13:10, 14:10, 15:10, 16:10, 17:10, 18:10, 19:10, 20:10,
                21:10, 22:10, 23:10, 24:10, 25:10, 26:10, 27:10, 28:10, 29:10, 30:10,
                31:10, 32:10, 33:10, 34:10, 35:10, 36:10, 37:10, 38:10, 39:10, 40:10,
                41:10, 42:10, 43:10, 44:10, 45:10, 46:10, 47:10, 48:10, 49:10, 50:10,
                51:10, 52:10, 53:10, 54:10, 55:10, 56:10, 57:10, 58:10, 59:10, 60:10,
                61:10, 62:10, 63:10, 64:10, 65:10, 66:10, 67:10, 68:10, 69:10, 70:10,
                71:10, 72:10, 73:10, 74:10, 75:10, 76:10, 77:10, 78:10, 79:10, 80:10,
                81:10, 82:10, 83:10, 84:10, 85:10, 86:10, 87:10, 88:10, 89:10, 90:10,
                91:10, 92:10, 93:10, 94:10, 95:10, 96:10, 97:10, 98:10, 99:10, 100:10,
                101:10, 102:10, 103:10, 104:10, 105:10, 106:10, 107:10, 108:10, 109:10, 110:10,
                111:10, 112:10, 113:10, 114:10, 115:10, 116:10, 117:10, 118:10, 119:10, 120:10,
                121:10, 122:10, 123:10, 124:10, 125:10, 126:10, 127:10, 128:10, 129:10, 130:10,
                131:10, 132:10, 133:10, 134:10, 135:10, 136:10, 137:10, 138:10, 139:10, 140:10,
                141:10, 142:10, 143:10, 144:10, 145:10, 146:10, 147:10, 148:10, 149:10, 150:10,
                151:10, 152:10, 153:10, 154:10, 155:10, 156:10, 157:10, 158:10, 159:10, 160:10,
                161:10, 162:10, 163:10, 164:10, 165:10, 166:10, 167:10, 168:10, 169:10, 170:10,
                171:10, 172:10, 173:10, 174:10, 175:10, 176:10, 177:10, 178:10, 179:10, 180:10,
                181:10, 182:10, 183:10, 184:10, 185:10, 186:10, 187:10, 188:10, 189:10, 190:10,
                191:10, 192:10, 193:10, 194:10, 195:10, 196:10, 197:10, 198:10, 199:10
            }                
            bin_size = 200 / 10        
            bin_indexes = list(range(10))
            bins_memb = {index: [] for index in bin_indexes}
            
            for key in memb_data.keys():           
                bin_index_memb = int(key // bin_size)          
                bins_memb[bin_index_memb].append(memb_data[key])
            for bin_index_memb in bins_memb.keys():
                bins_memb[bin_index_memb] = np.mean(bins_memb[bin_index_memb]) if bins_memb[bin_index_memb] else 0
            return bins_memb
    
        except Exception as e:
            print(f"Error processing embedded membrane data: {e}")
            return None

    def convert_to_actual_thickness(self, data_dict, memb_bins, double):
        """
        Converts top-position-based 'Height' columns in a dictionary of DataFrames
        into actual thickness values using the provided membrane positions.

        Parameters:
        -----------
        data_dict : Dict[str, pd.DataFrame]
            A dictionary where each value is a DataFrame containing 'Bin' and 'Height' columns.
        memb_bins : Dict[int, float]
            A dictionary mapping bin indices (keys) to membrane vertical positions (values).
        double : bool
            If True, multiply the thickness by 2 (useful if the simulation stores half-thickness).

        Returns:
        --------
        Dict[str, pd.DataFrame]
            A new dictionary of DataFrames, each having a 'Thickness' column with computed values.
        """
        if memb_bins is None:
            print("Warning: Cannot calculate actual thickness because membrane data is missing. Plotting raw height.")
            for combo_key, df_list in data_dict.items():
                for i, df in enumerate(df_list):
                    df_list[i]['Thickness'] = df['Height']
            return data_dict

        result_dict = {}
        for combo_key, df_list in data_dict.items():
            result_dict[combo_key] = []
            for df in df_list:
                df_copy = df.copy()
                if double:                
                    df_copy["Thickness"] = (df_copy["Height"] - df_copy["Bin"].map(memb_bins)).clip(lower=0) * 2.0
                else:
                    df_copy["Thickness"] = (df_copy["Height"] - df_copy["Bin"].map(memb_bins)).clip(lower=0)
                result_dict[combo_key].append(df_copy)
        return result_dict

    def generate_metadata_summary(self):       
        if not self.metadata_files:
            return "No metadata found."
        all_metadata = [json.load(open(f)) for f in self.metadata_files]
        # No longer need ref_meta as a primary source for default values
        summary_lines = [f"METADATA SUMMARY ({self.data_dir.name})", f"Runs Analyzed: {len(all_metadata)}", "---"]
        common_changes, varying_changes = {}, {}
        all_changed_keys = set().union(*(m.get("parameter_changes", {}).keys() for m in all_metadata))
        
        for key in sorted(list(all_changed_keys)):
            all_values = set()
            for meta in all_metadata:
                if key in meta.get("parameter_changes", {}):
                    val = meta["parameter_changes"][key]["current_value"]
                    all_values.add(round(val, 4) if isinstance(val, float) else val)
            
            if len(all_values) == 1:
                # **FIX:** Find the first metadata file containing the key to get its default value.
                # We can't assume the first file (ref_meta) has it.
                source_meta = next((meta for meta in all_metadata if key in meta.get("parameter_changes", {})), None)
                
                if source_meta:
                    change_info = source_meta["parameter_changes"][key]
                    common_changes[key] = f"{change_info['default_value']} -> {list(all_values)[0]}"

            elif len(all_values) > 1: # Ensure we don't process empty sets
                varying_changes[key] = sorted(list(all_values))

        if varying_changes:
            summary_lines.append("Swept Variable(s):")
            for key, values in varying_changes.items(): summary_lines.append(f"  - {key}: {values}")
        if common_changes:
            summary_lines.append("\nCommon Change(s):")
            for key, change_str in common_changes.items(): summary_lines.append(f"  - {key}: {change_str}")
        return "\n".join(summary_lines)
        
        # if not self.metadata_files:
        #     return "No metadata found."
        # all_metadata = [json.load(open(f)) for f in self.metadata_files]
        # ref_meta = all_metadata[0]
        # summary_lines = [f"METADATA SUMMARY ({self.data_dir.name})", f"Runs Analyzed: {len(all_metadata)}", "---"]
        # common_changes, varying_changes = {}, {}
        # all_changed_keys = set().union(*(m.get("parameter_changes", {}).keys() for m in all_metadata))
        # for key in sorted(list(all_changed_keys)):
        #     all_values = set()
        #     for meta in all_metadata:
        #         if key in meta.get("parameter_changes", {}):
        #             val = meta["parameter_changes"][key]["current_value"]
        #             all_values.add(round(val, 4) if isinstance(val, float) else val)
        #     if len(all_values) == 1:
        #         change_info = ref_meta["parameter_changes"][key]
        #         common_changes[key] = f"{change_info['default_value']} -> {list(all_values)[0]}"
        #     else:
        #         varying_changes[key] = sorted(list(all_values))
        # if varying_changes:
        #     summary_lines.append("Swept Variable(s):")
        #     for key, values in varying_changes.items(): summary_lines.append(f"  - {key}: {values}")
        # if common_changes:
        #     summary_lines.append("\nCommon Change(s):")
        #     for key, change_str in common_changes.items(): summary_lines.append(f"  - {key}: {change_str}")
        # return "\n".join(summary_lines)

    def generate_color_variations(self, base_color, n_variations):
        """
        Generate n variations of a base color by adjusting saturation and lightness.
        
        Parameters:
        -----------
        base_color : str or tuple
            Base color (hex, named color, or RGB tuple)
        n_variations : int
            Number of color variations to generate
        
        Returns:
        --------
        list of RGB tuples
        """
        # Convert base color to RGB if needed
        rgb = mcolors.to_rgb(base_color)
        
        # Convert RGB to HSV for easier manipulation
        hsv = mcolors.rgb_to_hsv(rgb)
        h, s, v = hsv[0], hsv[1], hsv[2]
        
        variations = []
        
        if n_variations == 1:
            return [rgb]
        
        # Strategy: vary both saturation and value (lightness)
        # Create a range that goes from darker/more saturated to lighter/less saturated
        for i in range(n_variations):
            # Interpolation factor
            t = i / (n_variations - 1) if n_variations > 1 else 0
            
            # Vary saturation: from high to moderate
            sat = s * (1.0 - 0.5 * t)  # Reduces saturation by up to 50%
            
            # Vary value: from darker to lighter
            # Don't go too dark or too light
            val = v * (0.7 + 0.4 * t)  # Range from 70% to 110% of original
            val = min(val, 0.95)  # Cap at 95% to avoid pure white
            
            # Create new HSV and convert back to RGB
            new_hsv = np.array([h, sat, val])
            new_rgb = mcolors.hsv_to_rgb(new_hsv)
            variations.append(new_rgb)
        
        return variations

    def plot_count(self, mode='individual', is_injury=False, injury_time_mcs=0, 
               scale_option="Absolute", max_combinations_per_figure=6):
        """
        Plot cell counts with multiple visualization modes for comparing homeostasis disruption.
        
        Parameters:
        -----------
        mode : str
            'individual' - One figure per combination showing replicates and mean
            'comparison' - All combinations overlaid (means only) 
            'matrix' - Grid of subplots for many combinations
            'statistics' - Statistical comparison between combinations
            'full' - Generates all visualization types
        is_injury : bool
            Whether to center time axis on injury event
        injury_time_mcs : float
            Time of injury in MCS units
        scale_option : str
            'Absolute', 'Percentage', or 'PctChangeFromBaseline'
        max_combinations_per_figure : int
            For 'matrix' mode, max subplots before creating new figure
        """
        if not self.count_data:
            print("No cell count data to plot.")
            return
        
        # Generate meaningful names for combinations from metadata
        combo_names = self._generate_combination_names()
        
        if mode == 'full':
            # Generate all visualization types
            self.plot_count(mode='individual', is_injury=is_injury, 
                        injury_time_mcs=injury_time_mcs, scale_option=scale_option)
            self.plot_count(mode='comparison', is_injury=is_injury, 
                        injury_time_mcs=injury_time_mcs, scale_option=scale_option)
            if len(self.count_data) > 1:                
                self.plot_count(mode='statistics', is_injury=is_injury, 
                            injury_time_mcs=injury_time_mcs, scale_option=scale_option)
            return
        
        elif mode == 'individual':
            self._plot_individual_combinations(combo_names, is_injury, injury_time_mcs, scale_option)
        
        elif mode == 'comparison':
            self._plot_comparison(combo_names, is_injury, injury_time_mcs, scale_option) 
        
        elif mode == 'statistics':
            self._plot_statistics(combo_names, is_injury, injury_time_mcs)
        
        else:
            raise ValueError(f"Unknown mode: {mode}. Use 'individual', 'comparison', 'matrix', 'statistics', or 'full'")

    def _generate_combination_names(self):
        """Generate meaningful names for combinations based on metadata."""
        combo_names = {}
        
        # Parse metadata to find what varies between combinations
        if hasattr(self, 'metadata_files') and self.metadata_files:
            # Extract varying parameters from metadata
            all_metadata = []
            for f in self.metadata_files:
                with open(f) as mf:
                    all_metadata.append(json.load(mf))
            
            # Find parameters that vary
            varying_params = {}
            for meta in all_metadata:
                combo_dir = Path(meta.get('output_directory', '')).parent.name
                if 'parameter_changes' in meta:
                    for param, info in meta['parameter_changes'].items():
                        if combo_dir not in varying_params:
                            varying_params[combo_dir] = {}
                        varying_params[combo_dir][param] = info['current_value']
            
            # Create descriptive names
            for combo_key in self.count_data.keys():
                if combo_key in varying_params:
                    # Use the most important varying parameter for the name
                    params = varying_params[combo_key]
                    if params:
                        # Take first parameter and its value
                        param_name = list(params.keys())[0]
                        param_value = params[param_name]
                        # Shorten parameter name for display
                        short_name = param_name.replace('_', ' ').title()
                        if len(short_name) > 15:
                            short_name = ''.join([w[0].upper() for w in short_name.split()])
                        combo_names[combo_key] = f"{short_name}: {param_value:.3g}"
                    else:
                        combo_names[combo_key] = combo_key
                else:
                    combo_names[combo_key] = combo_key
        else:
            # Fallback to directory names
            combo_names = {k: k for k in self.count_data.keys()}
        
        return combo_names

    def _plot_individual_combinations(self, combo_names, is_injury, injury_time_mcs, scale_option):
        """Plot each combination separately with proper injury time centering."""
        
        for combo_key, df_list in self.count_data.items():
            fig, axes = plt.subplots(4, 2, figsize=(15, 12))
            
            # Hide corner axes
            axes[0, 0].axis('off')
            axes[0, 1].axis('off')
            axes[3, 0].axis('off')
            axes[3, 1].axis('off')
            
            ax_longitudinal = plt.subplot2grid((4, 2), (0, 0), colspan=2)
            ax_wing = ax_longitudinal.twinx()
            ax_qq = plt.subplot2grid((4, 2), (3, 0), colspan=1)
            ax_text = plt.subplot2grid((4, 2), (3, 1), colspan=1)
            
            # Combine replicates for this combination
            combo_data = pd.concat(df_list, ignore_index=True)
            
            # Transform time to days
            combo_data['Time_Days'] = combo_data['Time'] / 24.0
            
            # Center on injury if specified
            if is_injury:
                injury_time_days = injury_time_mcs / 240.0
                combo_data['Time_Relative'] = combo_data['Time_Days'] - injury_time_days
                time_column = 'Time_Relative'
                
                # Adjust stability time relative to injury
                stable_time_relative = (self.stable_time / 240.0) - injury_time_days
                max_time_relative = (self.max_time / 240.0) - injury_time_days
            else:
                combo_data['Time_Relative'] = combo_data['Time_Days']
                time_column = 'Time_Relative'
                stable_time_relative = self.stable_time / 240.0
                max_time_relative = self.max_time / 240.0            
            
            combo_data_filtered = combo_data[combo_data['Time_Relative'] <= max_time_relative].copy() 
            mean_data = combo_data_filtered.groupby(time_column).mean().reset_index()
            std_data = combo_data_filtered.groupby(time_column).std().reset_index()
            stable_data = combo_data_filtered[combo_data_filtered[time_column] >= stable_time_relative]
            cell_types = ['Superficial', 'Wing', 'Basal', 'Stem']
            
            # if scale_option == "Percentage":
            #     total_counts = mean_data[cell_types].sum(axis=1)
            #     for cell_type in cell_types:
            #         if cell_type in mean_data.columns:
            #             mean_data[cell_type] = (mean_data[cell_type] / total_counts) * 100
            #             std_data[cell_type] = (std_data[cell_type] / total_counts) * 100
            # elif scale_option == "PctChangeFromBaseline":
            #     # Use pre-injury as baseline if injury, otherwise use early time points
            #     if is_injury:
            #         baseline_data = combo_data_filtered[combo_data_filtered[time_column] < 0]
            #     else:
            #         baseline_data = combo_data_filtered[combo_data_filtered[time_column] < stable_time_relative]
                
            #     for cell_type in cell_types:
            #         if cell_type in mean_data.columns and len(baseline_data) > 0:
            #             baseline = baseline_data[cell_type].mean()
            #             if baseline > 0:
            #                 mean_data[cell_type] = ((mean_data[cell_type] - baseline) / baseline) * 100
            #                 std_data[cell_type] = (std_data[cell_type] / baseline) * 100
            
            # # Plot longitudinal data with confidence bands
            # for i, cell_type in enumerate(cell_types):
            #     if cell_type not in mean_data.columns:
            #         continue
            baseline_means = {}
            if scale_option == "PctChangeFromBaseline":
                if is_injury:
                    baseline_data = combo_data_filtered[combo_data_filtered[time_column] < 0]
                else:
                    baseline_data = combo_data_filtered[combo_data_filtered[time_column] < stable_time_relative]
                
                if len(baseline_data) > 0:
                    baseline_means = baseline_data[cell_types].mean().to_dict()
                else:
                    baseline_means = {ct: 0 for ct in cell_types}

            # Apply scaling to the main combined dataframe *before* aggregation
            if scale_option == "Percentage":
                total_counts = combo_data_filtered[cell_types].sum(axis=1)
                for cell_type in cell_types:
                    if cell_type in combo_data_filtered.columns:
                        # Avoid 0/0, replace with 0
                        combo_data_filtered[cell_type] = (combo_data_filtered[cell_type] / total_counts).fillna(0) * 100
            
            elif scale_option == "PctChangeFromBaseline":
                for cell_type in cell_types:
                    if cell_type in combo_data_filtered.columns and cell_type in baseline_means:
                        baseline = baseline_means[cell_type]
                        if baseline > 0:
                            combo_data_filtered[cell_type] = ((combo_data_filtered[cell_type] - baseline) / baseline) * 100
                        else:
                            combo_data_filtered[cell_type] = 0 # Set to 0 if baseline is 0

            # Now, calculate mean, std, and stable_data from the *scaled* data
            mean_data = combo_data_filtered.groupby(time_column).mean().reset_index()
            std_data = combo_data_filtered.groupby(time_column).std().reset_index()
            stable_data = combo_data_filtered[combo_data_filtered[time_column] >= stable_time_relative]
            # --- END FIX ---
            
            
            # Plot longitudinal data with confidence bands
            for i, cell_type in enumerate(cell_types):
                if cell_type not in mean_data.columns:
                    continue   
                # # Plot mean line with confidence band
                # ax_longitudinal.plot(mean_data[time_column], mean_data[cell_type],
                #                 label=f'{cell_type}',
                #                 color=self.cell_color_map[cell_type],
                #                 linewidth=2, zorder=3)
                
                # ax_longitudinal.fill_between(mean_data[time_column],
                #                             mean_data[cell_type] - std_data[cell_type],
                #                             mean_data[cell_type] + std_data[cell_type],
                #                             color=self.cell_color_map[cell_type],
                #                             alpha=0.2, zorder=2)
                
                # Determine which axis to plot on
                target_ax = ax_wing if cell_type == 'Wing' else ax_longitudinal
                
                # Use target_ax for plotting
                target_ax.plot(mean_data[time_column], mean_data[cell_type],
                                label=f'{cell_type}',
                                color=self.cell_color_map[cell_type],
                                linewidth=2, zorder=3)
                
                # Use target_ax for fill_between
                target_ax.fill_between(mean_data[time_column],
                                        mean_data[cell_type] - std_data[cell_type],
                                        mean_data[cell_type] + std_data[cell_type],
                                        color=self.cell_color_map[cell_type],
                                        alpha=0.05, zorder=2)
                
                # Plot individual replicates with transformed time
                for df in df_list:
                    df_copy = df.copy()
                    df_copy['Time_Days'] = df_copy['Time'] / 24.0
                    
                    if is_injury:
                        df_copy['Time_Relative'] = df_copy['Time_Days'] - injury_time_days
                    else:
                        df_copy['Time_Relative'] = df_copy['Time_Days']
                    
                    # Filter to plotting range
                    df_copy = df_copy[df_copy['Time_Relative'] <= max_time_relative]
                    
                    if cell_type in df_copy.columns:
                        # ax_longitudinal.plot(df_copy['Time_Relative'], df_copy[cell_type],
                        #                 color=self.cell_color_map[cell_type],
                        #                 alpha=0.15, linewidth=0.5, zorder=1)
                        # target_ax.plot(df_copy['Time_Relative'], df_copy[cell_type],
                        #         color=self.cell_color_map[cell_type],
                        #         alpha=0.15, linewidth=0.5, zorder=1)
                        df_to_plot = df_copy.copy()

                        if scale_option == "Percentage":
                            total_counts_rep = df_to_plot[cell_types].sum(axis=1)
                            for ct in cell_types: # Scale all columns first
                                if ct in df_to_plot.columns:
                                    df_to_plot[ct] = (df_to_plot[ct] / total_counts_rep).fillna(0) * 100
                        
                        elif scale_option == "PctChangeFromBaseline":
                            if cell_type in baseline_means:
                                baseline = baseline_means[cell_type]
                                if baseline > 0:
                                    df_to_plot[cell_type] = ((df_to_plot[cell_type] - baseline) / baseline) * 100
                                else:
                                    df_to_plot[cell_type] = 0
                            else:
                                 df_to_plot[cell_type] = 0
                        
                        # Plot the *scaled* data
                        target_ax.plot(df_to_plot['Time_Relative'], df_to_plot[cell_type],
                                color=self.cell_color_map[cell_type],
                                alpha=0.15, linewidth=0.5, zorder=1)
                        
                # Individual histograms for stable phase
                row = (i // 2) + 1
                col = i % 2
                ax_hist = axes[row, col]
                
                if cell_type in stable_data.columns:
                    stable_values = stable_data[cell_type].values
                    if len(stable_values) > 0:
                        if scale_option == "Absolute":
                            bin_edges = np.arange(int(stable_values.min()) - 0.5, 
                                int(stable_values.max()) + 1.5, 1)
                        else:
                            bin_edges = 'auto'
                        all_hists = []
                        for df in df_list:
                            df_copy = df.copy()
                            df_copy['Time_Days'] = df_copy['Time'] / 24.0
                            if is_injury:
                                df_copy['Time_Relative'] = df_copy['Time_Days'] - injury_time_days
                            else:
                                df_copy['Time_Relative'] = df_copy['Time_Days']

                            # replicate_stable = df_copy[df_copy['Time_Relative'] >= stable_time_relative]
                            replicate_stable = df_copy.loc[df_copy['Time_Relative'] >= stable_time_relative].copy()

                            if scale_option == "Percentage":
                                total_counts_stable = replicate_stable[cell_types].sum(axis=1)
                                for ct in cell_types:
                                    if ct in replicate_stable.columns:
                                        replicate_stable.loc[:, ct] = (replicate_stable[ct] / total_counts_stable).fillna(0) * 100
                            
                            elif scale_option == "PctChangeFromBaseline":
                                for ct in cell_types:
                                    if ct in replicate_stable.columns and ct in baseline_means:
                                        baseline = baseline_means[ct]
                                        if baseline > 0:
                                            replicate_stable.loc[:, ct] = ((replicate_stable[ct] - baseline) / baseline) * 100
                                        else:
                                            replicate_stable.loc[:, ct] = 0
                                # if cell_type in baseline_means:
                                #     baseline = baseline_means[cell_type]
                                #     if baseline > 0:
                                #         replicate_stable[cell_type] = ((replicate_stable[cell_type] - baseline) / baseline) * 100
                                #     else:
                                #         replicate_stable[cell_type] = 0
                                # else:
                                #     replicate_stable[cell_type] = 0
                            
                            if cell_type in replicate_stable.columns and len(replicate_stable) > 0:
                                if not replicate_stable[cell_type].empty:
                                    hist, dynamic_bins, _ = ax_hist.hist(replicate_stable[cell_type], 
                                                            bins=bin_edges,
                                                            color=self.cell_color_map[cell_type],
                                                            alpha=0.075, 
                                                            edgecolor='none', 
                                                            density=True)
                                    all_hists.append(hist)
                                    if isinstance(bin_edges, str):
                                        bin_edges = dynamic_bins

                        if len(all_hists) > 0:
                            min_bins = min([len(h) for h in all_hists])
                            all_hists = [h[:min_bins] for h in all_hists]

                            mean_hist = np.mean(all_hists, axis=0)
                            if isinstance(bin_edges, str):
                                print(f"Warning: Could not determine bin edges for {cell_type}. Skipping mean histogram.")
                            else:
                                bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

                                if len(mean_hist) == len(bin_centers):
                            
                                    ax_hist.bar(bin_centers, mean_hist, 
                                            width=np.diff(bin_edges),
                                            color=self.cell_color_map[cell_type],
                                            alpha=0.1, edgecolor='magenta', linewidth=0.85,
                                            label=f'{cell_type} (mean of replicates)')
                                else:
                                    print(f"Warning: Mismatch in histogram lengths for {cell_type}. Skipping mean histogram.")

                        ax_hist.set_title(f'{cell_type} Distribution (Stable Phase)')
                        ax_hist.set_xlabel('Cell Count')
                        ax_hist.set_ylabel('Probability Density')
                        ax_hist.grid(True, alpha=0.3)
                        ax_hist.legend(loc='upper right', fontsize=8)
                        
                        # Add statistics annotation
                        mean_val = stable_values.mean()
                        std_val = stable_values.std()
                        ax_hist.axvline(mean_val, color='red', linestyle='--', linewidth=1)
                        x_position = 0.05 if mean_val > (stable_values.min() + stable_values.max()) / 2 else 0.60
                        ax_hist.text(x_position, 0.95, f'μ={mean_val:.1f}\nσ={std_val:.1f}',
                                    transform=ax_hist.transAxes, fontsize=9,
                                    verticalalignment='top',
                                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
                
                # Q-Q plot for stable phase
                if cell_type in stable_data.columns and len(stable_data[cell_type]) > 1:
                    from scipy.stats import probplot
                    probplot(stable_data[cell_type], dist="norm", plot=ax_qq)
            
            # Format Q-Q plot
            lines = ax_qq.get_lines()
            for i in range(0, min(len(lines), len(cell_types)*2), 2):
                if i//2 < len(cell_types):
                    lines[i].set_color(self.cell_color_map[cell_types[i//2]])
                    lines[i].set_alpha(0.6)
                    if i+1 < len(lines):
                        lines[i+1].set_color('black')
                        lines[i+1].set_linestyle('--')
                        lines[i+1].set_linewidth(0.5)
            
            ax_qq.set_title('Q-Q Plot (Stable Phase)')
            ax_qq.grid(True, alpha=0.3)
            
            # Add vertical markers for key time points
            if is_injury:
                # Mark injury time at t=0
                ax_longitudinal.axvline(0, color='red', linestyle='--',
                                    linewidth=2, label='Injury', zorder=4)
                
                # Add shaded region for pre-injury period
                ax_longitudinal.axvspan(mean_data[time_column].min(), 0, 
                                    color='gray', alpha=0.1, label='Pre-injury')
            
            # Mark stability time
            ax_longitudinal.axvline(stable_time_relative, color='black', linestyle='--',
                                linewidth=1, label='Stability Time', alpha=0.5, zorder=4)
            
            # Format main plot
            ax_longitudinal.set_title(f'Cell Dynamics: {combo_names[combo_key]}')
            
            if is_injury:
                ax_longitudinal.set_xlabel('Days Relative to Injury')
                # Set x-axis to show negative values clearly
                x_min = mean_data[time_column].min()
                x_max = mean_data[time_column].max()                
                
                ax_longitudinal.grid(True, alpha=0.3)
                ax_longitudinal.grid(axis='x', which='major', alpha=0.5)
            else:
                ax_longitudinal.set_xlabel('Time (Days)')
                ax_longitudinal.set_xlim(0, max_time_relative)
                ax_longitudinal.grid(True, alpha=0.3)

            ylabel_main = 'Cell Count (Non-wing)'
            ylabel_wing = 'Wing Cell Count'
            if scale_option == "Percentage":
                ylabel_main = 'Percentage (%)'
                ylabel_wing = 'Wing Percentage (%)'
            elif scale_option == "PctChangeFromBaseline":
                ylabel_main = '% Change from Baseline'
                ylabel_wing = '% Change from Baseline (Wing)'            
            
            ax_longitudinal.set_ylabel(ylabel_main)
            ax_wing.set_ylabel(ylabel_wing)

            # ax_longitudinal.legend(loc='best', fontsize=9)
            handles_main, labels_main = ax_longitudinal.get_legend_handles_labels()
            handles_wing, labels_wing = ax_wing.get_legend_handles_labels()
            ax_longitudinal.legend(handles_main + handles_wing, labels_main + labels_wing, loc='best', fontsize=9)
            
            # Add metadata text
            ax_text.axis('off')
            combo_info = self._get_combination_info(combo_key)
            
            # Add injury time info if applicable
            if is_injury:
                combo_info += f"\n\nInjury Time: {injury_time_mcs} MCS"
                combo_info += f"\n({injury_time_mcs/240:.1f} days)"
                combo_info += f"\nPre-injury: {x_min:.1f} to 0 days"
                combo_info += f"\nPost-injury: 0 to {x_max:.1f} days"
            
            ax_text.text(0.05, 0.95, combo_info,
                        transform=ax_text.transAxes,
                        fontsize=8, fontfamily='monospace',
                        verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='aliceblue', alpha=0.7))
            
            # Add title with injury info
            title = f'Homeostasis Analysis: {combo_names[combo_key]}'
            if is_injury:
                title += f' (Injury at t=0)'
            plt.suptitle(title, fontsize=14, y=1.02)
            
            plt.tight_layout()
            
            if self.out_dir:
                safe_name = combo_names[combo_key].replace(':', '_').replace(' ', '_')
                suffix = '_injury_centered' if is_injury else ''
                plt.savefig(self.out_dir / f'individual_{safe_name}{suffix}.png', 
                        dpi=300, bbox_inches='tight')
            
            plt.show()    

    def _plot_comparison(self, combo_names, is_injury, injury_time_mcs, scale_option):
        """Overlay all combinations with proper injury time centering."""
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        cell_types = ['Superficial', 'Wing', 'Basal', 'Stem']
        
        # Use different line styles for many combinations
        line_styles = ['-', '--', '-.', ':']
        n_combos = len(self.count_data)

        # combo_colors = plt.cm.tab20(np.linspace(0, 1, len(self.count_data)))
        
        for cell_idx, cell_type in enumerate(cell_types):
            ax = axes[cell_idx // 2, cell_idx % 2]

            # Generate color variations for this cell type
            base_color = self.cell_color_map[cell_type]
            color_variations = self.generate_color_variations(base_color, n_combos)
        
            for combo_idx, (combo_key, df_list) in enumerate(self.count_data.items()):
                # Aggregate this combination's replicates
                combo_data = pd.concat(df_list, ignore_index=True)
                
                # Transform time FIRST
                combo_data['Time_Days'] = combo_data['Time'] / 24.0
                
                if is_injury:
                    injury_time_days = injury_time_mcs / 240.0
                    combo_data['Time_Relative'] = combo_data['Time_Days'] - injury_time_days
                    time_column = 'Time_Relative'
                    max_time_relative = (self.max_time / 240.0) - injury_time_days
                else:
                    combo_data['Time_Relative'] = combo_data['Time_Days']
                    time_column = 'Time_Relative'
                    max_time_relative = self.max_time / 240.0
                
                # Filter data
                combo_data = combo_data[combo_data[time_column] <= max_time_relative]
                
                # Apply scaling
                if scale_option == "Percentage":
                    total_counts = combo_data[cell_types].sum(axis=1)
                    for ct in cell_types:
                        if ct in combo_data.columns:
                            combo_data[ct] = (combo_data[ct] / total_counts).fillna(0) * 100
                elif scale_option == "PctChangeFromBaseline":
                    if is_injury:
                        baseline_data = combo_data[combo_data[time_column] < 0]
                    else:
                        baseline_data = combo_data[combo_data[time_column] < self.stable_time / 240.0]
                    
                    baseline_means = {}
                    if len(baseline_data) > 0:
                        baseline_means = baseline_data[cell_types].mean().to_dict()

                    for ct in cell_types:
                        if ct in combo_data.columns and ct in baseline_means:
                            baseline = baseline_means[ct]
                            if baseline > 0:
                                combo_data[ct] = ((combo_data[ct] - baseline) / baseline) * 100
                            else:
                                combo_data[ct] = 0

                # Calculate statistics
                mean_data = combo_data.groupby(time_column).mean().reset_index()
                std_data = combo_data.groupby(time_column).std().reset_index()
                
                if cell_type not in mean_data.columns:
                    continue
                
                
                # Plot with unique style
                linestyle = line_styles[combo_idx % len(line_styles)]
                # color = combo_colors[combo_idx] if len(self.count_data) > 4 else self.cell_color_map[cell_type]
                color = color_variations[combo_idx]

                ax.plot(mean_data[time_column], mean_data[cell_type],
                    label=combo_names[combo_key],
                    color=color,
                    linestyle=linestyle,
                    linewidth=2)
                
                # Add subtle confidence band
                ax.fill_between(mean_data[time_column],
                            mean_data[cell_type] - std_data[cell_type],
                            mean_data[cell_type] + std_data[cell_type],
                            color=color, alpha=0.1)
            
            # Format subplot
            ax.set_title(f'{cell_type} Cells')
            
            if is_injury:
                ax.set_xlabel('Days Relative to Injury')
                ax.axvline(0, color='red', linestyle='--', alpha=0.7, linewidth=1.5)
                # Ensure x-axis shows negative values
            #     x_limits = ax.get_xlim()
            #     if x_limits[0] >= -1:
            #         ax.set_xlim(left=-2)
            else:
                ax.set_xlabel('Time (Days)')
            #     ax.set_xlim(left=0)
            
            ylabel = 'Cell Count'
            if scale_option == "Percentage":
                ylabel = 'Percentage (%)'
            elif scale_option == "PctChangeFromBaseline":
                ylabel = '% Change from Baseline'
            ax.set_ylabel(ylabel)
            
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=8, loc='best')
            
            # Mark stability time
            if self.stable_time:
                if is_injury:
                    stab_days_relative = (self.stable_time / 240.0) - (injury_time_mcs / 240.0)
                else:
                    stab_days_relative = self.stable_time / 240.0
                ax.axvline(stab_days_relative, color='black', linestyle='--', alpha=0.3, linewidth=0.8)
        
        title = 'Combination Comparison: Homeostasis Disruption'
        if is_injury:
            title += f' (Injury at t=0, {injury_time_mcs/240:.1f} days into simulation)'
        plt.suptitle(title, fontsize=14)
        plt.tight_layout()
        
        if self.out_dir:
            suffix = '_injury_centered' if is_injury else ''
            plt.savefig(self.out_dir / f'comparison_all_combinations{suffix}.png', 
                    dpi=300, bbox_inches='tight')
        
        plt.show()    

    def _plot_statistics(self, combo_names, is_injury, injury_time_mcs):
        """Statistical comparison between combinations."""
        
        from scipy import stats
        
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        
        # Collect stable phase statistics for each combination
        stable_stats = {}
        cell_types = ['Superficial', 'Wing', 'Basal', 'Stem']
        
        for combo_key, df_list in self.count_data.items():
            combo_data = pd.concat(df_list, ignore_index=True)
            stable_data = combo_data[(combo_data['Time'] >= self.stable_time) & 
                                    (combo_data['Time'] <= self.max_time)]
            
            stable_stats[combo_key] = {
                'Total': stable_data[cell_types].sum(axis=1).values,
                'Stem': stable_data['Stem'].values if 'Stem' in stable_data else np.array([]),
                'Basal': stable_data['Basal'].values if 'Basal' in stable_data else np.array([]),
                'Wing': stable_data['Wing'].values if 'Wing' in stable_data else np.array([]),
                'Superficial': stable_data['Superficial'].values if 'Superficial' in stable_data else np.array([]),
                'CV': stable_data[cell_types].sum(axis=1).std() / stable_data[cell_types].sum(axis=1).mean()
            }
        
        # 1. Box plots for total cell count
        ax = axes[0, 0]
        box_data = [stable_stats[k]['Total'] for k in self.count_data.keys()]
        box_labels = [combo_names[k] for k in self.count_data.keys()]
        bp = ax.boxplot(box_data, labels=box_labels, patch_artist=True)
        for patch, color in zip(bp['boxes'], plt.cm.tab10.colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        ax.set_title('Total Cell Count Distribution (Stable Phase)')
        ax.set_ylabel('Total Cells')
        ax.tick_params(axis='x', rotation=45)
        ax.set_xticklabels(box_labels, rotation=45, ha='right')
        
        # 2. Coefficient of Variation comparison
        ax = axes[0, 1]
        cv_values = [stable_stats[k]['CV'] for k in self.count_data.keys()]
        colors = plt.cm.tab10.colors[:len(cv_values)]
        bars = ax.bar(range(len(cv_values)), cv_values, color=colors, alpha=0.7)
        ax.set_xticks(range(len(cv_values)))
        ax.set_xticklabels(box_labels, rotation=45, ha='right')
        ax.set_title('Coefficient of Variation (Homeostasis Stability)')
        ax.set_ylabel('CV')
        ax.axhline(y=0.1, color='red', linestyle='--', label='CV = 0.1')
        ax.legend()
        
        # 3. Heatmap of pairwise comparisons (Kruskal-Wallis)
        ax = axes[0, 2]
        n_combos = len(self.count_data)
        p_matrix = np.ones((n_combos, n_combos))
        
        combo_keys = list(self.count_data.keys())
        for i, key1 in enumerate(combo_keys):
            for j, key2 in enumerate(combo_keys):
                if i != j:
                    stat, p_val = stats.mannwhitneyu(stable_stats[key1]['Total'],
                                                    stable_stats[key2]['Total'],
                                                    alternative='two-sided')
                    p_matrix[i, j] = p_val
        
        im = ax.imshow(p_matrix, cmap='RdYlGn_r', vmin=0, vmax=0.1)
        ax.set_xticks(range(n_combos))
        ax.set_yticks(range(n_combos))
        ax.set_xticklabels([combo_names[k] for k in combo_keys], rotation=45, ha='right')
        ax.set_yticklabels([combo_names[k] for k in combo_keys])
        ax.set_title('Pairwise Statistical Comparison (p-values)')
        plt.colorbar(im, ax=ax)
        
        # 4. Cell type proportions
        ax = axes[1, 0]
        width = 0.8 / len(cell_types)
        x = np.arange(len(self.count_data))
        
        for i, cell_type in enumerate(cell_types):
            means = []
            for combo_key in self.count_data.keys():
                if len(stable_stats[combo_key][cell_type]) > 0:
                    means.append(stable_stats[combo_key][cell_type].mean())
                else:
                    means.append(0)
            
            ax.bar(x + i * width, means, width, label=cell_type,
                color=self.cell_color_map[cell_type], alpha=0.8)
        
        ax.set_xlabel('Combination')
        ax.set_ylabel('Mean Cell Count')
        ax.set_title('Cell Type Distribution by Combination')
        ax.set_xticks(x + width * 1.5)
        ax.set_xticklabels(box_labels, rotation=45, ha='right')
        ax.legend()
        
        # 5. Stability time analysis (time to reach stable CV)
        ax = axes[1, 1]
        stability_times = []
        
        for combo_key, df_list in self.count_data.items():
            combo_data = pd.concat(df_list, ignore_index=True)
            grouped = combo_data.groupby('Time')[cell_types].sum().sum(axis=1)
            
            # Calculate rolling CV
            window = 10  # 10 time points
            rolling_cv = grouped.rolling(window).std() / grouped.rolling(window).mean()
            
            # Find first time CV stays below threshold
            threshold = 0.15
            stable_idx = np.where(rolling_cv < threshold)[0]
            if len(stable_idx) > 0:
                stability_times.append(grouped.index[stable_idx[0]] / 240.0)  # Convert to days
            else:
                stability_times.append(np.nan)
        
        bars = ax.bar(range(len(stability_times)), stability_times, color=colors, alpha=0.7)
        ax.set_xticks(range(len(stability_times)))
        ax.set_xticklabels(box_labels, rotation=45, ha='right')
        ax.set_title('Time to Reach Stability (CV < 0.15)')
        ax.set_ylabel('Days')
        
        # 6. Summary table
        ax = axes[1, 2]
        ax.axis('tight')
        ax.axis('off')
        
        # Create summary statistics table
        table_data = []
        max_name_length = max(len(combo_names[k]) for k in self.count_data.keys())
        for combo_key in self.count_data.keys():
            total_mean = stable_stats[combo_key]['Total'].mean()
            total_std = stable_stats[combo_key]['Total'].std()
            cv = stable_stats[combo_key]['CV']
            table_data.append([combo_names[combo_key][:20], f'{total_mean:.0f}±{total_std:.0f}', f'{cv:.3f}'])
        
        table = ax.table(cellText=table_data,
                        colLabels=['Combination', 'Total Cells', 'CV'],
                        cellLoc='center',
                        loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(8)

        table.auto_set_column_width([0, 1, 2])

        scale_x = 1.5 if max_name_length > 30 else 1.2
        table.scale(scale_x, 1.8)

        # Style the header
        for i in range(3):
            table[(0, i)].set_facecolor('#40466e')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Alternate row colors for better readability
        for i in range(1, len(table_data) + 1):
            for j in range(3):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#f0f0f0')
        
        plt.suptitle('Statistical Analysis: Homeostasis Disruption', fontsize=14)
        plt.tight_layout()
        
        if self.out_dir:
            plt.savefig(self.out_dir / 'statistical_comparison.png', dpi=150, bbox_inches='tight')
        
        plt.show()

    def _get_combination_info(self, combo_key):
        """Extract detailed information for a specific combination."""
        info_lines = [f"Combination: {combo_key}", "=" * 30]
        
        # Add replicate count
        n_reps = len(self.count_data[combo_key])
        info_lines.append(f"Replicates: {n_reps}")
        
        # Extract parameter changes if available
        if hasattr(self, 'metadata_files'):
            for meta_file in self.metadata_files:
                if combo_key in str(meta_file):
                    with open(meta_file) as f:
                        meta = json.load(f)
                        if 'parameter_changes' in meta:
                            info_lines.append("\nParameter Changes:")
                            for param, details in meta['parameter_changes'].items():
                                info_lines.append(f"  {param}:")
                                info_lines.append(f"    {details['default_value']} → {details['current_value']}")
                        break
        
        return '\n'.join(info_lines) 
    
    def plot_thickness(self, is_injury=False, injury_time_mcs=0, scale_option="Absolute"):
        
        if not self.thick_mMEMB:
            print("No thickness data to plot.")
            return
        
        # fig = plt.figure(figsize=(15, 8))
        # gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1])
        # ax = fig.add_subplot(gs[0, 0])
        # ax_text = fig.add_subplot(gs[0, 1])
        fig = plt.figure(figsize=(16, 10))
        gs = gridspec.GridSpec(2, 2, figure=fig, width_ratios=[3, 1.5], height_ratios=[1,1])

        ax_longitudinal = fig.add_subplot(gs[0, :])
        ax_boxplot = fig.add_subplot(gs[1, 0])
        ax_text = fig.add_subplot(gs[1, 1])

        # --- Data Prep ---
        all_data = pd.concat([df for df_list in self.thick_mMEMB.values() for df in df_list], ignore_index=True)
        all_data = all_data[all_data['Time'] <= self.max_time]
        
        unique_bins = sorted(all_data['Bin'].unique())
        bin_palette = sns.color_palette("husl", len(unique_bins))
        combo_linestyles = ['-', '--', ':', '-.']

        for i, (combo_key, df_list) in enumerate(self.thick_mMEMB.items()):
            combined_data = pd.concat(df_list, ignore_index=True)
            median_data = combined_data.groupby(['Time', 'Bin'])['Thickness'].median().reset_index()
            
            linestyle = combo_linestyles[i % len(combo_linestyles)]
            
            for j, bin_id in enumerate(unique_bins):
                bin_data = median_data[median_data['Bin'] == bin_id]
                time_days = bin_data['Time'] / 240.0
                ax_longitudinal.plot(time_days, bin_data['Thickness'], color=bin_palette[j],
                                     linestyle=linestyle, label=f'{combo_key}' if j == 0 else '_nolegend_')

        ax_longitudinal.set_title('Longitudinal Median Tissue Thickness')
        ax_longitudinal.set_xlabel('Time (Days)')
        ax_longitudinal.set_ylabel('Thickness (μm)')
        ax_longitudinal.grid(True, linewidth=0.3)
        # Create custom legend for bins and linestyles
        from matplotlib.lines import Line2D
        bin_legend = [Line2D([0], [0], color=bin_palette[j], lw=2, label=f'Bin {j}') for j in unique_bins]
        combo_legend = [Line2D([0], [0], color='k', linestyle=combo_linestyles[i], label=key) for i, key in enumerate(self.thick_mMEMB.keys())]
        ax_longitudinal.legend(handles=bin_legend + combo_legend, title='Legend', loc='best')

        # --- Box Plot ---
        stable_data = all_data[all_data['Time'] >= self.stable_time]
        sns.boxplot(ax=ax_boxplot, x='Bin', y='Thickness', data=stable_data, palette=bin_palette, showfliers=False)
        ax_boxplot.set_title('Stable Tissue Thickness Distribution Across Bins')
        ax_boxplot.set_xlabel('Bin ID')
        ax_boxplot.set_ylabel('Thickness (μm)')
        ax_boxplot.grid(True, linewidth=0.3)

        # --- Metadata Panel ---
        ax_text.axis('off')
        ax_text.text(0.05, 0.95, self.summary_text, transform=ax_text.transAxes, fontsize=9,
                     fontfamily='monospace', verticalalignment='top',
                     bbox=dict(boxstyle='round,pad=0.5', fc='aliceblue', alpha=0.5))

        plt.tight_layout(pad=2.0)
        plt.show()




    def plot_thickness_old(self, data_dict,scale_option="Absolute",is_injury=False,injury_time_mcs=0):
        # def plot_thickness(self, data_dict,scale_option="Absolute",is_injury=False,injury_time_mcs=0):
        """
        Create thickness vs. time plots for each bin, optionally highlighting injury time.
        
        scale_option in {"Absolute", "Percentage", "PctChangeFromMedian"}:
            - "Absolute": raw thickness
            - "Percentage": each bin's thickness is shown as fraction of total thickness at that time
            - "PctChangeFromMedian": each bin's thickness shown as % change from the bin's own median
        If is_injury=True, the time axis is shifted so that the injury event is at t=0,
        and a vertical red dashed line is placed at x=0.
        """

        # 1) Combine thickness data
        all_data = pd.concat(data_dict.values(), ignore_index=True)
        # Restrict to max_time if desired
        all_data = all_data[all_data['Time'] <= self.max_time]

        # Group by (Time, Bin), compute median thickness
        grouped = all_data.groupby(['Time', 'Bin'], as_index=False)['Thickness'].median()
        grouped = grouped.sort_values(by='Time')
      
        homeostasis_dict = {}

        if is_injury:
            pre_injury_data = grouped[grouped['Time'] < injury_time_mcs]
            if not pre_injury_data.empty:
                for bin_num in pre_injury_data['Bin'].unique():
                    bin_data = pre_injury_data[pre_injury_data['Bin'] == bin_num]
                    homeostasis_dict[bin_num] = bin_data['Thickness'].median()
            else:
                Warning("No injury is done at day 0.")
        else:
            for bin_num in grouped['Bin'].unique():
                homeostasis_dict[bin_num] = grouped[grouped['Bin'] == bin_num]['Thickness'].median()
        # Convert MCS to days; SHIFT if there's an injury
        # If is_injury is True, subtract (injury_time_mcs / 24) from the time in hours
        # which effectively places t_injury = 0 on the x-axis.
        if is_injury:
            # Shift time so that (Time in hours - injury_time_mcs) / 24 => days from injury
            injury_time_days = injury_time_mcs / 240.0
            grouped['TimeDays'] = (grouped['Time']/ 24.0) - injury_time_days
        else:
            grouped['TimeDays'] = grouped['Time'] / 24.0

        # Pivot so that columns=Bin, index=TimeDays, values=median(Thickness)
        pivot_df = grouped.pivot(index='TimeDays', columns='Bin', values='Thickness')

        old_bin_numbers = pivot_df.columns.tolist()
        n_bins = len(old_bin_numbers)
        bin_size = 200.0 / float(n_bins)
        new_labels = []
        bin_label_mapping = {}
        for b in old_bin_numbers:
            start_x = int(b * bin_size)
            end_x = int(start_x + bin_size)
            new_label = f"{start_x}-{end_x}"
            new_labels.append(new_label)
            bin_label_mapping[b] = new_label
        pivot_df.columns = new_labels

        # Remap homeostasis_dict keys to the new bin labels
        homeostasis_dict = { bin_label_mapping[k]: v for k, v in homeostasis_dict.items() }

        # 2) Apply the chosen scaling
        if scale_option == "Percentage":
            # At each time, total = sum of all bins
            total_per_time = pivot_df.sum(axis=1)
            pivot_df = pivot_df.div(total_per_time, axis=0).fillna(0) * 100.0
            if is_injury:
                # Convert homeostasis values to percentages
                total_homeostasis = sum(homeostasis_dict.values())
                homeostasis_dict = {k: (v/total_homeostasis)*100 for k, v in homeostasis_dict.items()}
            else:
                homeostasis_dict = pivot_df.median(axis=0).to_dict()

        elif scale_option == "PctChangeFromMedian":
            # For each bin, compute median across all times
            bin_medians = pivot_df.median(axis=0)
            # Normalize each value by its bin's median first
            normalized_df = pivot_df.div(bin_medians)
            # Then calculate the percent change from the normalized median (which is 1)
            pivot_df = (normalized_df - 1) * 100.0
            if is_injury:
                # Convert homeostasis values to percent change from median
                homeostasis_dict = {k: ((v/bin_medians[k]) - 1)*100 for k, v in homeostasis_dict.items()}
            else:
                homeostasis_dict = {k: 0 for k in pivot_df.columns}

        # 6) Plot #1: Combined plot for all bins
        fig, ax = plt.subplots(figsize=(12, 6))
        palette = sns.color_palette("husl", n_bins)
        for i, bin_label in enumerate(new_labels):
            ax.plot(pivot_df.index, pivot_df[bin_label], label=bin_label, color=palette[i], linewidth=2)
            # Now the keys in homeostasis_dict match the new bin labels
            ax.axhline(y=homeostasis_dict[bin_label], color=palette[i],
                    linestyle=':', alpha=0.5, label=f'{bin_label} Baseline')
        if is_injury:
            ax.axvline(0, color='Black', linestyle='--', linewidth=1.5, label='Injury')
        if scale_option == "Absolute":
            ax.set_ylabel("Thickness (μm)")
        elif scale_option == "Percentage":
            ax.set_ylabel("Thickness (% of total)")
        else:
            ax.set_ylabel("% Change from Each Bin's Median")
        ax.set_xlabel("Days Relative to Injury" if is_injury else "Time (Days)")
        ax.set_title("Combined Tissue Thickness by X-Coordinate")
        ax.grid(True, linewidth=0.1)
        ax.legend(loc="best")
        plt.tight_layout()
        plt.show()

        # 7) Plot #2: Individual subplots for each bin
        fig2, axes = plt.subplots(n_bins, 1, figsize=(10, 4 * n_bins + 1), sharex=True)
        if n_bins == 1:
            axes = [axes]
        for i, bin_label in enumerate(new_labels):
            ax_bin = axes[i]
            ax_bin.plot(pivot_df.index, pivot_df[bin_label], label=bin_label,
                        color=palette[i], linewidth=2)
            # Use the corresponding baseline for this bin
            ax_bin.axhline(y=homeostasis_dict[bin_label], color=palette[i],
                        linestyle=':', alpha=0.5, label='Baseline')
            if is_injury:
                ax_bin.axvline(0, color='black', linestyle='--', linewidth=1.5)
            if scale_option == "Absolute":
                ax_bin.set_ylabel("Thickness (μm)")
            elif scale_option == "Percentage":
                ax_bin.set_ylabel("% of Total")
            else:
                ax_bin.set_ylabel("% from Median")
            ax_bin.grid(True, linewidth=0.1)
            ax_bin.legend()
        axes[-1].set_xlabel("Days Relative to Injury" if is_injury else "Time (Days)")
        fig2.suptitle("Thickness by X-Coordinate (Individual Subplots)", y=0.99)
        plt.subplots_adjust(hspace=0.1, top=0.97, bottom=0.1)
        plt.show()

    def plot_thickness_old(self, data_dict, bin_memb):
        unique_bins = set()
        for data in data_dict.values():
            unique_bins.update(data['Bin'].unique())
        unique_bins = sorted(unique_bins)
        color_palette = sns.color_palette("spectral", len(unique_bins))
        bin_color_map = {bin_key: color_palette[i] for i, bin_key in enumerate(unique_bins)}
        bins_size = 200 // len(unique_bins)  # Size in μm
        bin_x = {bin_key: [] for _, bin_key in enumerate(unique_bins)}

        for key in bin_x.keys():
            bin_x[key] = [i for i in range(key * bins_size, int((key + 1) * bins_size))]
            bin_x[key] = np.mean(bin_x[key])  # Position in μm
        bin_actual = []
        bin_relative = []
        
        fig, ax = plt.subplots(2, figsize=(14, 12))

        all_data = []

        for comb, data in data_dict.items():
            all_data.append(data)

            for bin_key in unique_bins:
                bin_data = data[data['Bin'] == bin_key]
                ax[0].plot(bin_data['Time'] / 24, bin_data['Height']*2,  # Convert hours to days, half-thickness to full thickness
                        alpha=0.075, linewidth=1, color=bin_color_map[bin_key])

        combined_data = pd.concat(all_data)
        mean_data = combined_data.groupby(['Time', 'Bin']).mean().reset_index()
        std_data = combined_data.groupby(['Time', 'Bin']).std().reset_index()

        for bin_key in unique_bins:
            bin_mean_data = mean_data[mean_data['Bin'] == bin_key]
            bin_std_data = std_data[std_data['Bin'] == bin_key]

            stable_bin_data = combined_data[(combined_data['Bin'] == bin_key) & (combined_data['Time'] >= self.stable_time)]

            bin_actual.append((stable_bin_data['Height'].mean() - bin_memb[bin_key])*2)  # Full thickness in μm
            bin_relative.append((stable_bin_data['Height'].mean())*2)  # Full height in μm
            ax[0].plot(bin_mean_data['Time'] / 24, bin_mean_data['Height']*2, label=f'X Coord. {bin_key * bins_size}-{int((bin_key + 1) * bins_size) - 1}',
                    linewidth=1, color=bin_color_map[bin_key])

            # Adjust box plot positions
            box_position = bin_x[bin_key] * 2  # Multiply by 2 to match the new x-axis scale

            ax[1].boxplot((stable_bin_data['Height']-bin_memb[bin_key])*2, positions=[box_position], widths=6, patch_artist=True,
                        boxprops=dict(facecolor='tab:red', color='black', linewidth=0.5),
                        medianprops=dict(color='black', linewidth=0.5), whiskerprops=dict(color='black', linewidth=0.5),
                        capprops=dict(color='black', linewidth=0.5), flierprops=dict(marker='.',color='red', markersize=1,markeredgewidth=0.5, linewidth=0.5, alpha=0.5))
            ax[1].boxplot((stable_bin_data['Height'])*2, positions=[box_position], widths=6, patch_artist=True,
                        boxprops=dict(facecolor='tab:blue', color='black', linewidth=0.5),
                        medianprops=dict(color='black', linewidth=0.5), whiskerprops=dict(color='black', linewidth=0.5),
                        capprops=dict(color='black', linewidth=0.5), flierprops=dict(marker='.',color='red', markersize=1,markeredgewidth=0.5, linewidth=0.5, alpha=0.5))
            
        ax[0].axvline(self.stable_time / 24, color='black', linestyle='dashed', linewidth=1, label="Stability Time")
        ax[0].set_title('Longitudinal Variation of Tissue Top Position Over Six Months')
        ax[0].set_xlabel('Time (Days)')
        ax[0].set_ylabel('Vertical Position (μm)')
        ax[0].legend(title='Bins', loc='lower right')
        ax[0].grid(True, linewidth=0.1)

        x_values = [val * 2 for val in bin_x.values()]  # Convert to full width in μm
        ax[1].plot(x_values, bin_actual, color='tab:red', linestyle='dotted', linewidth=1, label="Tissue Thickness")
        ax[1].plot(x_values, bin_relative, color='tab:blue', linestyle='dotted', linewidth=1, label="Tissue Top Position")

        ax[1].set_title('Stable Tissue Top Possition and Thickness Across Sections')
        ax[1].set_xlabel('Horizontal Position (μm)')
        ax[1].set_ylabel('Vertical Position / Thickness (μm)')
        ax[1].legend(title='Bins', loc='center right')
        ax[1].grid(True, linewidth=0.1) 

        plt.tight_layout()
        plt.subplots_adjust(hspace=0.20)        
        plt.show()    

    def compute_thickness_regrowth(self, data_dict, is_injury=False, injury_time_day=0):
        """
        Compute thickness changes centered around 0%, where:
        - 0% represents homeostasis/baseline
        - Negative values show reduction from baseline
        - Positive values show growth above baseline
        
        Parameters:
        data_dict: Dictionary containing DataFrames with Time and Height columns
        is_injury: Boolean indicating if this is an injury scenario
        injury_time_day: Time of injury in days
        
        Returns:
        DataFrame with Time, MedianThickness, PctRegrowth, and confidence intervals
        """
        # Combine all thickness data from different simulations
        all_data = pd.concat(data_dict.values(), ignore_index=True)
        
        # Calculate median thickness for each time point
        df_median_thickness = (all_data.groupby('Time', as_index=False)
                            .agg({
                                'Thickness': ['median', 'std', 'count']
                            }))
        
        # Flatten multi-level columns if they exist
        if isinstance(df_median_thickness.columns, pd.MultiIndex):
            df_median_thickness.columns = ['Time', 'MedianThickness', 'StdThickness', 'Count']
        
        if is_injury:
            # Get pre-injury data
            pre_injury_df = df_median_thickness[df_median_thickness['Time'] < injury_time_day]
            
            if len(pre_injury_df) == 0:
                raise ValueError(f"No data before injury time {injury_time_day}")
            
            # Use median of pre-injury period as baseline (0%)
            baseline_thickness = pre_injury_df['MedianThickness'].median()
            
            # Calculate percentage change relative to baseline
            # (current - baseline) / baseline * 100
            df_median_thickness['PctRegrowth'] = (
                (df_median_thickness['MedianThickness'] - baseline_thickness) / 
                baseline_thickness * 100.0
            )
            
            # Calculate confidence intervals
            df_median_thickness['CI_Lower'] = df_median_thickness['PctRegrowth'] - (
                1.96 * df_median_thickness['StdThickness'] / 
                np.sqrt(df_median_thickness['Count']) * 100.0 / baseline_thickness
            )
            df_median_thickness['CI_Upper'] = df_median_thickness['PctRegrowth'] + (
                1.96 * df_median_thickness['StdThickness'] / 
                np.sqrt(df_median_thickness['Count']) * 100.0 / baseline_thickness
            )
            
        else:
            # No injury case: use initial median as baseline
            baseline_thickness = df_median_thickness['MedianThickness'].median()
            if baseline_thickness == 0:
                raise ValueError("Initial thickness cannot be zero")
            
            # Calculate percentage change from baseline
            df_median_thickness['PctRegrowth'] = (
                (df_median_thickness['MedianThickness'] - baseline_thickness) / 
                baseline_thickness * 100.0
            )
            
            # Calculate confidence intervals
            df_median_thickness['CI_Lower'] = df_median_thickness['PctRegrowth'] - (
                1.96 * df_median_thickness['StdThickness'] / 
                np.sqrt(df_median_thickness['Count']) * 100.0 / baseline_thickness
            )
            df_median_thickness['CI_Upper'] = df_median_thickness['PctRegrowth'] + (
                1.96 * df_median_thickness['StdThickness'] / 
                np.sqrt(df_median_thickness['Count']) * 100.0 / baseline_thickness
            )
        
        return df_median_thickness

    def plot_regrowth_ki67_division(self, df_thickness, df_ki67, df_division, df_count, is_injury=False, injury_time_day=0):
        """
        Create visualization of tissue dynamics including thickness changes, Ki67 expression,
        and cell division rates.
        
        Parameters:
        df_thickness: DataFrame with Time, MedianThickness, PctRegrowth and confidence intervals
        df_ki67: Dictionary of DataFrames with Ki67 data
        df_division: Dictionary of DataFrames with division rate data
        injury_time_hours: Time of injury in DAYS. If None, treats as no-injury case
        """
        color_codes = [ '#ff007f','#ffbe99',]
        cell_types = ["Basal", "Stem"]

        # Process Ki67 data
        all_ki67_data = pd.concat(df_ki67.values(), ignore_index=True)        
        # Process division data
        all_division_data = pd.concat(df_division.values(), ignore_index=True)
       
        # ---Smoothing ----
        all_ki67_data['Time'] = (all_ki67_data['Time'] // 12) * 12
        all_division_data['Time'] = (all_division_data['Time'] // 12) * 12

        # Group by the 8-hour bin and sum the values.
        # Then divide by 8 to get the average over that period.
        smoothed_ki67 = all_ki67_data.groupby('Time').sum().reset_index()
        smoothed_division = all_division_data.groupby('Time').sum().reset_index()

        # Identify all numeric columns (other than the grouping column)
        numeric_cols_ki67 = smoothed_ki67.columns.drop('Time')
        numeric_cols_div = smoothed_division.columns.drop('Time')

        # Divide the summed values by 8.
        smoothed_ki67[numeric_cols_ki67] = smoothed_ki67[numeric_cols_ki67] / 8
        smoothed_division[numeric_cols_div] = smoothed_division[numeric_cols_div] / 8        

        # Use the smoothed data from here on.
        all_ki67_data = smoothed_ki67.copy()
        all_division_data = smoothed_division.copy()
        # --- end smoothing ---


        if isinstance(df_count, dict):
            all_count_data = pd.concat(df_count.values(), ignore_index=True)
        else:
            all_count_data = df_count.copy()
        # all_count_data["Day"] = (all_count_data["Time"] // 24).astype(int)
        count_daily = all_count_data.groupby("Time", as_index=False)[cell_types].mean()

        fraction_df = pd.DataFrame({"Time": all_division_data["Time"]})
        homeostasis_dict = {}

        for c in cell_types:
            # fraction dividing
            fraction_df[f"{c}_frac_dividing"] = (
                # mean_division[c] / count_daily[c]
                all_division_data[c]/ count_daily[c]
            )
            # fraction Ki67
            fraction_df[f"{c}_frac_ki67"] = (
                # mean_ki67[c] / count_daily[c]
                all_ki67_data[c] / count_daily[c]
            )

        # if is_injury:
        #     pre_injury_mask = fraction_df['Time'] < (injury_time_day * 24)
        #     if pre_injury_mask.any():
        #         # homeostasis_dict[f"{c}_dividing"] = fraction_df.loc[pre_injury_mask, f"{c}_frac_dividing"].median()
        #         homeostasis_dict[f"{c}_dividing"] = fraction_df.loc[pre_injury_mask, f"{c}_frac_dividing"].mean()
        #         # homeostasis_dict[f"{c}_ki67"] = fraction_df.loc[pre_injury_mask, f"{c}_frac_ki67"].median()
        #         homeostasis_dict[f"{c}_ki67"] = fraction_df.loc[pre_injury_mask, f"{c}_frac_ki67"].mean()
        #         # homeostasis_dict['Thickness'] = df_thickness[pre_injury_mask, 'PctRegrowth'].mean()
        #     else:
        #         # homeostasis_dict[f"{c}_dividing"] = fraction_df[f"{c}_frac_dividing"].median()
        #         homeostasis_dict[f"{c}_dividing"] = fraction_df[f"{c}_frac_dividing"].mean()
        #         # homeostasis_dict[f"{c}_ki67"] = fraction_df[f"{c}_frac_ki67"].median()
        #         homeostasis_dict[f"{c}_ki67"] = fraction_df[f"{c}_frac_ki67"].mean()
        #         # homeostasis_dict['Thickness'] = df_thickness['PctRegrowth'].mean()

        # Calculate time axis
        if is_injury:
            df_thickness['TimeSinceInjury'] = df_thickness['Time']/24 - injury_time_day            
            fraction_df['TimeSinceInjury'] = fraction_df['Time']/24 - injury_time_day
            time_label = "Time Since Injury (days)"
            title = "Tissue Recovery Dynamics"
        else:
            df_thickness['TimeSinceInjury'] = df_thickness['Time']/24            
            fraction_df['TimeSinceInjury'] = fraction_df['Time']/24
            time_label = "Time (days)"
            title = "Tissue Dynamics Over Time"

        # Create figure
        fig, (ax1, ax2, ax3) = plt.subplots(nrows=3, ncols=1, figsize=(12, 12), sharex=True)
        
        # 1) Thickness/Regrowth plot with confidence intervals
        ax1.plot(df_thickness['TimeSinceInjury'], df_thickness['PctRegrowth'],
                color='blue', label='Thickness Change', linewidth=2)
        ax1.fill_between(df_thickness['TimeSinceInjury'],
                        df_thickness['CI_Lower'],
                        df_thickness['CI_Upper'],
                        color='blue', alpha=0.2)
        ax1.axhline(0, color='gray', linestyle='--', label='Baseline')
        
        if is_injury:
            ax1.axvline(0, color='Black', linestyle='--', label='Injury')
            
        # else:
        #     ax1.axhline(y=0, color='gray', linestyle='--', label='Baseline')

        ax1.set_ylabel("Relative Thickness (%)")
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        # 2) Ki67 expression
        ax2.plot(fraction_df['TimeSinceInjury'], fraction_df['Basal_frac_ki67']*100,
                color=color_codes[1], label='Ki67+ Basal', linewidth=2)
        ax2.plot(fraction_df['TimeSinceInjury'], fraction_df['Basal_frac_dividing']*100,
                color='purple', label='Divisions: Basal', linewidth=2)
        #TODO change for the pre injury values in case of injury
        ax2.axhline(y=fraction_df['Basal_frac_ki67'].mean()*100, color='green', linestyle=':', label='Ki67 Baseline')
        ax2.axhline(y=fraction_df['Basal_frac_dividing'].mean()*100, color='orange', linestyle=':', label='Dividing Baseline')
        if is_injury:
            ax2.axvline(0, color='Black', linestyle='--', label='Injury')
        
        # else:
        #     ax2.axhline(y=0, color='gray', linestyle='--', label='Baseline')

        ax2.set_ylabel("% of Cells")
        ax2.grid(True, alpha=0.3)
        ax2.legend()

        # 3) Division rates        
        ax3.plot(fraction_df['TimeSinceInjury'], fraction_df['Stem_frac_ki67']*100,
                 color='red', label='Ki67+ Stem', linewidth=2)
        ax3.plot(fraction_df['TimeSinceInjury'], fraction_df['Stem_frac_dividing']*100,
                color=color_codes[0], label='Divisions: Stem', linewidth=2)
        #TODO change for the pre injury values in case of injury
        ax3.axhline(y=fraction_df['Stem_frac_ki67'].mean()*100, color='green', linestyle=':', label='Ki67 Baseline')
        ax3.axhline(y=fraction_df['Stem_frac_dividing'].mean()*100, color='orange', linestyle=':', label='Dividing Baseline')
        if is_injury:
            ax3.axvline(0, color='Black', linestyle='--', label='Injury')
            
        ax3.set_xlabel(time_label)
        ax3.set_ylabel("% of Cells")
        ax3.grid(True, alpha=0.3)
        ax3.legend()

        plt.suptitle(title)
        plt.tight_layout()
        plt.show()