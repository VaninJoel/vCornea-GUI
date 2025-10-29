# Save this as your new plot_manager.py

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
import json
from scipy.stats import probplot, skew, kurtosis, kstest, shapiro, anderson

class PlotManager:
    def __init__(self, Data_DIR, Out_DIR,  CurrentParam):
        self.data_dir = Path(Data_DIR)
        self.out_dir = Path(Out_DIR)
        self.parameters = CurrentParam        
        self.memb_bins = self.load_memb_data()
        self.stable_time = 0

        # Define color codes
        self.color_codes = ['#ff007f', '#ffbe99', '#0055ff', '#55ffff'] # Stem, Basal, Wing, Super

        self.cell_color_map = {
            'Superficial': '#55ffff',
            'Wing': '#0055ff',
            'Basal': '#ffbe99',
            'Stem': '#ff007f'
        }
        
        # Extract simulation parameters
        self.SimTime_mcs = self.parameters.get('SimTime', 7700)
        self.max_time = self.SimTime_mcs

        # Collect data files using 
        self.Count_file, self.Thickness_file, self.metadata_files = self.collect_files_recursively(self.data_dir)
        
        # Load data into dictionaries of DataFrames
        self.count_data = self.data_collection(self.Count_file) if self.Count_file else {}
        self.thickness_data = self.data_collection(self.Thickness_file) if self.Thickness_file else {}

        if self.thickness_data:
            self.thick_mMEMB = self.convert_to_actual_thickness(self.thickness_data, self.memb_bins, double=True)

        # Generate the summary text from all found metadata files
        self.summary_text = self.generate_metadata_summary()

        if not self.count_data and not self.thickness_data:
            raise FileNotFoundError(f"No valid cell_count or thickness files found in {self.data_dir}")

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
        ref_meta = all_metadata[0]
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
                change_info = ref_meta["parameter_changes"][key]
                common_changes[key] = f"{change_info['default_value']} -> {list(all_values)[0]}"
            else:
                varying_changes[key] = sorted(list(all_values))
        if varying_changes:
            summary_lines.append("Swept Variable(s):")
            for key, values in varying_changes.items(): summary_lines.append(f"  - {key}: {values}")
        if common_changes:
            summary_lines.append("\nCommon Change(s):")
            for key, change_str in common_changes.items(): summary_lines.append(f"  - {key}: {change_str}")
        return "\n".join(summary_lines)

    def plot_count(self, is_injury=False, injury_time_mcs=0, scale_option="Absolute"):
        
        if not self.count_data:
            print("No cell count data to plot.")
            return

        # fig = plt.figure(figsize=(15, 8))
        # gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1])
        # ax_main = fig.add_subplot(gs[0, 0])
        # ax_text = fig.add_subplot(gs[0, 1])
        # ax_wing = ax_main.twinx()
        fig = plt.figure(figsize=(16, 12))
        gs = gridspec.GridSpec(4, 2, figure=fig)
        
        ax_longitudinal = fig.add_subplot(gs[0, :])
        ax_hist_stem = fig.add_subplot(gs[1, 0])
        ax_hist_basal = fig.add_subplot(gs[1, 1])
        ax_hist_wing = fig.add_subplot(gs[2, 0])
        ax_hist_super = fig.add_subplot(gs[2, 1])
        ax_qq = fig.add_subplot(gs[3, 0])
        ax_text = fig.add_subplot(gs[3, 1])

        hist_axes = {'Stem': ax_hist_stem, 'Basal': ax_hist_basal, 'Wing': ax_hist_wing, 'Superficial': ax_hist_super}
        
        combo_palette = sns.color_palette("viridis", len(self.count_data))
        all_replicates_df = pd.concat([df for df_list in self.count_data.values() for df in df_list], ignore_index=True)
        all_replicates_df = all_replicates_df[all_replicates_df['Time'] <= self.max_time]

        # --- Longitudinal Plot ---
        for i, (combo_key, df_list) in enumerate(self.count_data.items()):
            combo_df = pd.concat(df_list, ignore_index=True)
            median_data = combo_df.groupby('Time').median().reset_index()
            time_days = (median_data['Time'] / 240.0)
            
            # Plot median line for this combination
            ax_longitudinal.plot(time_days, median_data['Stem'] + median_data['Basal'] + median_data['Wing'] + median_data['Superficial'],
                                 color=combo_palette[i], linewidth=2.5, label=combo_key)
            # Plot individual replicate lines with transparency
            for rep_df in df_list:
                rep_time_days = rep_df['Time'] / 240.0
                ax_longitudinal.plot(rep_time_days, rep_df.sum(axis=1), color=combo_palette[i], alpha=0.2)
        
        ax_longitudinal.set_title('Longitudinal Total Cell Count')
        ax_longitudinal.set_xlabel('Time (Days)')
        ax_longitudinal.set_ylabel('Total Number of Cells')
        ax_longitudinal.legend(title='Parameter Combinations')
        ax_longitudinal.grid(True, linewidth=0.3)

        # --- Histograms and Q-Q Plots (Aggregated across all runs) ---
        stable_data_df = all_replicates_df[all_replicates_df['Time'] >= self.stable_time]
        cell_types = ['Stem', 'Basal', 'Wing', 'Superficial']

        for cell_type in cell_types:
            if cell_type not in stable_data_df.columns: continue
            
            ax_hist = hist_axes[cell_type]
            data_series = stable_data_df[cell_type]
            color = self.cell_color_map[cell_type]

            # Histogram
            ax_hist.hist(data_series, bins=20, color=color, alpha=0.7, density=True)
            ax_hist.set_title(f'Distribution of {cell_type} Cells (Stable Phase)')
            ax_hist.set_xlabel('Number of Cells')
            ax_hist.set_ylabel('Density')
            ax_hist.grid(True, linewidth=0.3)

            # Q-Q Plot
            probplot(data_series, dist="norm", plot=ax_qq)
        
        # Style Q-Q plot lines
        qq_lines = ax_qq.get_lines()
        for i in range(len(cell_types)):
            if len(qq_lines) > i*2+1:
                qq_lines[i*2].set_markerfacecolor(self.cell_color_map[cell_types[i]])
                qq_lines[i*2].set_markeredgecolor(self.cell_color_map[cell_types[i]])
                qq_lines[i*2].set_markersize(4)
                qq_lines[i*2].set_label(cell_types[i])
                qq_lines[i*2+1].set_linestyle('--')
        ax_qq.set_title('Q-Q Plot of Cell Counts vs. Normal Distribution')
        ax_qq.legend()
        ax_qq.grid(True, linewidth=0.3)

        # --- Metadata Panel ---
        ax_text.axis('off')
        ax_text.text(0.05, 0.95, self.summary_text, transform=ax_text.transAxes, fontsize=9,
                     fontfamily='monospace', verticalalignment='top',
                     bbox=dict(boxstyle='round,pad=0.5', fc='aliceblue', alpha=0.5))
        
        plt.tight_layout(pad=2.0)
        plt.show()
        
        # palette = sns.color_palette("viridis", len(self.count_data))

        # for i, (combo_key, df_list) in enumerate(self.count_data.items()):
        #     combined_data = pd.concat(df_list, ignore_index=True)
        #     combined_data = combined_data[combined_data['Time'] <= self.max_time]
        #     median_data = combined_data.groupby('Time').median().reset_index()
        #     cell_types = [col for col in ['Stem', 'Basal', 'Wing', 'Superficial'] if col in median_data.columns]
        #     time_mcs = median_data["Time"].values
        #     time_in_days = (time_mcs / 240.0) - (injury_time_mcs / 240.0) if is_injury else (time_mcs / 240.0)

        #     for j, c_type in enumerate(cell_types):
        #         ax = ax_wing if c_type == "Wing" else ax_main
        #         ax.plot(time_in_days, median_data[c_type], color=palette[i], linewidth=2, 
        #                 label=f"{combo_key} - {c_type}" if j == 0 else "_nolegend_")
        #         for rep_df in df_list:
        #             rep_time_mcs = rep_df['Time'].values
        #             rep_time = (rep_time_mcs / 240.0) - (injury_time_mcs / 240.0) if is_injury else (rep_time_mcs / 240.0)
        #             if c_type in rep_df.columns:
        #               ax.plot(rep_time, rep_df[c_type], color=palette[i], alpha=0.15)

        # if is_injury:
        #     ax_main.axvline(0, color='black', linestyle='--', label='Injury Time', linewidth=1.5)
        # ax_main.set_xlabel("Days Relative to Injury" if is_injury else "Time (Days)")
        # ax_main.set_ylabel("Cell Count")
        # ax_wing.set_ylabel("Wing Cell Count")
        # ax_main.set_title("Median Cell Counts per Combination")
        # ax_main.grid(True, which='both', linestyle='--', linewidth=0.5)
        # lines, labels = ax_main.get_legend_handles_labels()
        # lines2, labels2 = ax_wing.get_legend_handles_labels()
        # ax_wing.legend(lines + lines2, labels + labels2, loc='best')

        # ax_text.axis('off')
        # ax_text.text(0.05, 0.95, self.summary_text, transform=ax_text.transAxes, fontsize=9,
        #              fontfamily='monospace', verticalalignment='top',
        #              bbox=dict(boxstyle='round,pad=0.5', fc='aliceblue', alpha=0.5))

        # plt.tight_layout()
        # plt.show()

    def plot_count_old(self, data_dict, scale_option="Absolute", is_injury=False, injury_time_mcs=0):
        """
        Example: highlight injury time by recentering x-axis and drawing a vertical line
        plus a 'homeostasis' horizontal line from pre-injury median.
        """
        # 1) Combine data
        combined_data = pd.concat(data_dict.values())
        combined_data = combined_data[combined_data['Time'] <= self.max_time]
        median_data = combined_data.groupby('Time').median().reset_index()

        # 2) Identify your cell type columns (assuming [Time, STEM, BASAL, WING, SUPERFICIAL])
        cell_types = median_data.columns[1:5]

        # 3) Possibly apply scaling (Percentage, PctChangeFromMedian, etc.)
        if scale_option == "Percentage":
            total_counts = median_data[cell_types].sum(axis=1)
            median_data[cell_types] = median_data[cell_types].div(total_counts, axis=0).fillna(0)*100
        elif scale_option == "PctChangeFromMedian":
            for c in cell_types:
                # Calculate the median for each cell type
                baseline = median_data[c].median()
                # Normalize by the median first
                normalized = median_data[c] / baseline
                # Calculate percent change from normalized median (which is 1)
                median_data[c] = (normalized - 1) * 100
        
        # if scale_option == "Absolute", no changes needed

        # 4) Convert MCS to days and SHIFT if there's an injury
        #    If is_injury == True, we re-center so that injury_time is 0.
        #    If is_injury == False, just plot normally from 0..(SimTime/24).
        time_mcs = median_data["Time"].values
        if is_injury:
            # user has indicated an injury event
            # shift time so that t=0 is the injury day
            injury_time_days = injury_time_mcs / 240.0
            time_in_days = (time_mcs / 24.0) - injury_time_days
        else:
            time_in_days = time_mcs / 24.0

        # 5) Compute 'homeostasis' for pre-injury times if desired
        #    We can define "homeostasis" as the median from time<InjuryTime.
        homeostasis_dict = {}
        if is_injury:
            # Calculate median values for pre-injury period for each cell type
            pre_injury_data = median_data[median_data["Time"] < injury_time_mcs]
            if not pre_injury_data.empty:
                for c in cell_types:
                    homeostasis_dict[c] = pre_injury_data[c].median()
            else:
                
                Warning("No injury is done at day 0.")
        else:
            # When there is no injury, set the baseline as:
            if scale_option == "Percentage":
                # Baseline is the median percentage (should be close to the overall median)
                homeostasis_dict = {c: median_data[c].median() for c in cell_types}
            elif scale_option == "PctChangeFromMedian":
                # By definition, the median percent change should be 0%
                homeostasis_dict = {c: 0 for c in cell_types}
            else:
                # For Absolute, use the median cell count
                homeostasis_dict = {c: median_data[c].median() for c in cell_types}


        # 6) Plot: Combined with WING on a secondary axis
        fig, ax_main = plt.subplots(figsize=(12,6))
        ax_wing = ax_main.twinx()

        for i, c in enumerate(cell_types):
            if c.upper() == "WING":
                ax_wing.plot(time_in_days, median_data[c], label=f"{c}", color=self.color_codes[i], linewidth=2)
                ax_wing.axhline(y=homeostasis_dict[c], color=self.color_codes[i], linestyle=':', 
                            alpha=0.5, label=f'{c} Baseline')
            else:
                ax_main.plot(time_in_days, median_data[c], label=f"{c}", color=self.color_codes[i], linewidth=2)
                ax_main.axhline(y=homeostasis_dict[c], color=self.color_codes[i], linestyle=':', 
                            alpha=0.5, label=f'{c} Baseline')            

        # 7) Mark the injury time with a vertical line at x=0
        if is_injury:
            ax_main.axvline(0, color='Black', linestyle='--', label='Injury', linewidth=1.5)

        # Set axis labels based on scale_option
        if scale_option == "Percentage":
            ax_main.set_ylabel("Cell Percentage (%)")
            ax_wing.set_ylabel("Wing Percentage (%)")
        elif scale_option == "PctChangeFromMedian":
            ax_main.set_ylabel("% Change from Median")
            ax_wing.set_ylabel("% Change from Median (Wing)")
        else:
            ax_main.set_ylabel("Cell Count (Non-wing)")
            ax_wing.set_ylabel("Wing Cell Count")

        ax_main.set_xlabel("Days Relative to Injury" if is_injury else "Time (Days)")
        ax_main.set_title("Cell Count (Injury-Centered)" if is_injury else "Cell Count")
        ax_main.grid(True, linewidth=0.1)

        ax_main.legend(loc="upper left")
        ax_wing.legend(loc="upper right")
        plt.tight_layout()
        plt.show()

        # ---------------------------------------------------------
        # SEPARATE SUBPLOTS for each cell type
        #    (still using the same scale_option and the shifted time)
        # ---------------------------------------------------------
        fig2, axs = plt.subplots(nrows=len(cell_types), figsize=(10, 3 * len(cell_types)), sharex=True)

        # If there's only one cell type, make sure axs is a list
        if len(cell_types) == 1:
            axs = [axs]

        for ax, ctype in zip(axs, cell_types):
            color_index = list(cell_types).index(ctype)
            ax.plot(time_in_days, median_data[ctype], color=self.color_codes[color_index], linewidth=2, label=ctype)
            ax.axhline(y=homeostasis_dict[ctype], color=self.color_codes[color_index], linestyle=':', 
                   alpha=0.5, label=f'Baseline')
            if is_injury:
                ax.axvline(x=0, color='Black', linestyle='--', linewidth=1.5)

            if scale_option == "Percentage":
                ax.set_ylabel("Percentage (%)")
            elif scale_option == "PctChangeFromMedian":
                ax.set_ylabel("% Change from Median")
            else:
                ax.set_ylabel("Cell Count")

            ax.set_title(f"{ctype} Over Time")
            ax.grid(True, linewidth=0.1)
            ax.legend()

        # Shared X-label
        axs[-1].set_xlabel("Days Relative to Injury" if is_injury else "Time (Days)")
        plt.tight_layout()
        plt.show()

    def plot_thickness(self, is_injury=False, injury_time_mcs=0, scale_option="Absolute"):
        
        if not self.thick_mMEMB:
            print("No thickness data to plot.")
            return
        
        # fig = plt.figure(figsize=(15, 8))
        # gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1])
        # ax = fig.add_subplot(gs[0, 0])
        # ax_text = fig.add_subplot(gs[0, 1])
        fig = plt.figure(figsize=(16, 10))
        gs = gridspec.GridSpec(2, 2, figure=fig, width_ratios=[3, 1.5])

        ax_longitudinal = fig.add_subplot(gs[0, :])
        ax_boxplot = fig.add_subplot(gs[1, 0])
        ax_text = fig.add_subplot(gs[1, 1])

        # --- Data Prep ---
        all_data = pd.concat([df for df_list in self.thick_mMEMB.values() for df in df_list], ignore_index=True)
        all_data = all_data[all_data['Time'] <= self.max_time]
        
        unique_bins = sorted(all_data['Bin'].unique())
        bin_palette = sns.color_palette("husl", len(unique_bins))
        combo_linestyles = ['-', '--', ':', '-.']

        
        # palette = sns.color_palette("viridis", len(self.thickness_data))

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

        #     median_data = combined_data.groupby(['Time', 'Bin']).median().reset_index()
            
        #     for bin_id in sorted(median_data['Bin'].unique()):
        #         bin_data = median_data[median_data['Bin'] == bin_id]
        #         time_in_days = (bin_data['Time'] / 240.0) - (injury_time_mcs / 240.0) if is_injury else (bin_data['Time'] / 240.0)
        #         # Plot only one label for the whole combination
        #         label = f"{combo_key} - Bin {bin_id}" if bin_id == 0 else "_nolegend_"
        #         ax.plot(time_in_days, bin_data['Height'], color=palette[i], label=label)

        # if is_injury:
        #     ax.axvline(0, color='black', linestyle='--', label='Injury Time', linewidth=1.5)
            
        # ax.set_title("Median Tissue Thickness Over Time")
        # ax.set_xlabel("Days Relative to Injury" if is_injury else "Time (Days)")
        # ax.set_ylabel("Thickness (μm)")
        # ax.legend()
        # ax.grid(True, which='both', linestyle='--', linewidth=0.5)

        # ax_text.axis('off')
        # ax_text.text(0.05, 0.95, self.summary_text, transform=ax_text.transAxes, fontsize=9,
        #              fontfamily='monospace', verticalalignment='top',
        #              bbox=dict(boxstyle='round,pad=0.5', fc='aliceblue', alpha=0.5))

        # plt.tight_layout()
        # plt.show()

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