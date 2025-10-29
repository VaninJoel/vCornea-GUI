import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path

class PlotManager:
   
    def __init__(self, Data_DIR, Stable_time, Max_time, SimTime_mcs, Out_DIR=None):
        self.data_dir = Path(Data_DIR)
        self.out_dir = Path(Out_DIR) if Out_DIR else self.data_dir    

        # Define color codes and other constants
        self.color_codes = ['#55ffff','#0055ff', '#ffbe99', '#ff007f']
        self.stable_time = Stable_time #15 * 24  # Time in hours for stability
        self.max_time = Max_time #720  # Maximum time limit
        self.SimTime_mcs = SimTime_mcs

        # Collect and load data
        self.Param_file, self.Count_file, self.Thickness_file = self.collect_files(Data_DIR)
        self.memb_bins = self.load_memb_data() 
        # print(self.memb_bins) 
        self.count_data = self.data_collection(self.Count_file)
        self.thickness_data = self.data_collection(self.Thickness_file)
    
    def collect_files(self, directory):    
        sim_suffix = int((self.SimTime_mcs) + 1)
        parameter_files = []    
        count_files = []
        thickness_bins_files = []              
               
        directory = Path(directory)
        cell_count_file = directory / "Simulation" / f"cell_count_{sim_suffix}.csv"
        thickness_file = directory / "Simulation" /f"thickness_rep_{sim_suffix}.parquet"
        print(cell_count_file)
        print(thickness_file)
         # Check if they exist
        if cell_count_file.exists():
            count_files.append(str(cell_count_file))
        if thickness_file.exists():
            thickness_bins_files.append(str(thickness_file))

        # Also look for Parameters.py (assuming it doesn't have suffix)
        for file in directory.rglob("Parameters.py"):
            parameter_files.append(str(file))       

        return parameter_files, count_files, thickness_bins_files

    def data_collection(self, file):
        """
        Collect data from multiple files, supporting both CSV and Parquet formats.
        
        Args:
            file: List of file paths
            
        Returns:
            dict: Dictionary containing DataFrames with keys based on file path components
        """
        # Load data
        data_dict = {}
        
        for data_path in file:
            file_extension = Path(data_path).suffix.lower()
            
            try:
                # Read file based on its extension
                if file_extension == '.csv':
                    data = pd.read_csv(data_path)
                elif file_extension == '.parquet':
                    data = pd.read_parquet(data_path)
                else:
                    raise ValueError(f"Unsupported file format: {file_extension}. Only .csv and .parquet files are supported.")
                
                # Create key from path components (assuming you want to keep the same naming convention)
                key = f"{str(Path(data_path).parts[-4])}_{str(Path(data_path).parts[-3])}"
                data_dict[key] = data
                
            except Exception as e:
                print(f"Error reading file {data_path}: {str(e)}")
                continue
                
        return data_dict
    
    def load_memb_data(self):        
        memb_data = {}
        try:
            memb_file = Path(self.data_dir).joinpath("membrane_height.csv")           
            rows = pd.read_csv(memb_file, header=None)
            for index, row in rows.iterrows():
                memb_data[row[0]] = row[1]
                
            bin_size = 200 / 10        
            bin_indexes = list(range(10))
            bins_memb = {index: [] for index in bin_indexes}
            
            for key in memb_data.keys():           
                bin_index_memb = int(key // bin_size)          
                bins_memb[bin_index_memb].append(memb_data[key])
            for bin_index_memb in bins_memb.keys():
                bins_memb[bin_index_memb] = np.mean(bins_memb[bin_index_memb]) if bins_memb[bin_index_memb] else 0
        except Exception as e:
            print(f"Warning: Could not load membrane data: {str(e)}")
            # print(memb_file)
            bins_memb = None
        return bins_memb
    
    def plot_count_old(self, data_dict):
        # Data handling
        combined_data = pd.concat(data_dict.values())
        combined_data = combined_data[combined_data['Time'] <= self.max_time]
        combined_stable_data = combined_data[combined_data['Time'] >= self.stable_time]
        mean_data = combined_data.groupby('Time').mean().reset_index()

        # Create figure and axes
        fig, axes = plt.subplots(4, 2, figsize=(14, 12))
        axes[0, 0].axis('off')
        axes[0, 1].axis('off')
        axes[3, 0].axis('off')
        axes[3, 1].axis('off')

        ax_longitudinal = plt.subplot2grid((4, 2), (0, 0), colspan=2)  
        ax_qq_combined = plt.subplot2grid((4, 2), (3, 0), colspan=2, rowspan=1)

            # Plot the mean data on the longitudinal plot        
        for i, column in enumerate(mean_data.columns[1:5]):        
            ax_longitudinal.plot(mean_data["Time"]/24, mean_data[column], label=f'Mean {column}', color=self.color_codes[i], linewidth=2) 
        
            row = (i // 2) + 1
            col = i % 2            
            ax_hist = axes[row, col]

            # Combine all stable data for the current column
            all_stable_data = np.concatenate([data[(data['Time'] >= self.stable_time) & (data['Time'] <= self.max_time)][column].values for data in data_dict.values()])
            
            # Calculate bin edges
            bin_edges = np.arange(int(all_stable_data.min()) - 0.5, int(all_stable_data.max()) + 1.5, 1)

            # Plot individual distributions and calculate mean
            all_hists = []
            for Comb, data in data_dict.items():
                stable_data = data[(data['Time'] >= self.stable_time) & (data['Time'] <= self.max_time)]
                hist, _, _ = ax_hist.hist(stable_data[column], bins=bin_edges, color=self.color_codes[i], alpha=0.075)
                all_hists.append(hist)

            # Calculate mean histogram
            mean_hist = np.mean(all_hists, axis=0)
            
            ax_hist.grid(True, linewidth=0.1) 
            ax_hist.set_title(f'Variation of {column}-Cell Number in Time and Between Replicates')
            ax_hist.set_xlabel('Number of Cells per Time')
            ax_hist.set_ylabel('Frequency')

            # Calculate and display skewness and kurtosis
            skewness = skew(all_stable_data)
            print(f'{column} Skewness: {skewness:.2f}')
            print(f'{column} Kurtosis: {kurtosis(all_stable_data):.2f}')

            # Kolmogorov-Smirnov test
            ks_stat, ks_p = kstest(all_stable_data, 'norm', args=(np.mean(all_stable_data), np.std(all_stable_data)))
            print(f'{column} KS stat: {ks_stat:.2f}')
            print(f'{column} KS p-value: {ks_p:.2e}')

            # Shapiro-Wilk test
            sw_stat, sw_p = shapiro(all_stable_data)
            print(f'{column} SW stat: {sw_stat:.2f}')
            print(f'{column} SW p-value: {sw_p:.2e}')

            result = stats.anderson(all_stable_data, dist='norm')
            print(f'{column} A stat:', result.statistic)
            print(f'{column} A Crit:', result.critical_values)
            print(f'{column} A signi:', result.significance_level)

            # Q-Q plot       
            (osm, osr), (slope, intercept, r) = probplot(combined_stable_data[column], dist="norm", plot=ax_qq_combined)
            
            lines = ax_qq_combined.get_lines()
            if len(lines) >= 2 * (i + 1):  # Ensure there are enough lines
                observed_line = lines[2 * i]
                expected_line = lines[2 * i + 1]
                # Style observed data points
                observed_line.set_color(self.color_codes[i])
                observed_line.set_alpha(0.25)
                observed_line.set_label(f'{column}')
                # Style expected line
                expected_line.set_color('black')
                expected_line.set_linestyle('dashed')
                # Calculate and print statistics
                differences = np.abs(osm - osr)
                mean_difference = np.mean(differences)
                max_difference = np.max(differences)
                print(f'{column} Q-Q Slope: {slope:.2f}, Intercept: {intercept:.2f}, R: {r:.2f}')
                print(f'{column} Q-Q Mean difference: {mean_difference:.2f}, Max difference: {max_difference:.2f}')
                print()
                
        expected_line.set_label(f'Normal Distribution')    
        ax_qq_combined.set_title('Combined Q-Q Plots')
        ax_qq_combined.grid(True, linewidth=0.1)
        ax_qq_combined.legend()
        data = data[data['Time'] <= self.max_time]

        for Comb, data in data_dict.items():        
            # Filter the data to include only times less than 720
            filtered_data = data[data['Time'] < self.max_time]  
            for i, column in enumerate(filtered_data.columns[0:4]):                     
                ax_longitudinal.plot(filtered_data['Time']/24, filtered_data[column], color=self.color_codes[i], alpha=0.075, linewidth=2)

        ax_longitudinal.axvline(self.stable_time/24, color='black', linestyle='dashed', linewidth=1, label="Stability Time")
        ax_longitudinal.legend(loc='center right')
        ax_longitudinal.grid(True, linewidth=0.1)
        # ax_longitudinal.title('Longitudinal Cell Count')
        # ax_longitudinal.xlabel('Time (Days)')
        # ax_longitudinal.ylabel('Number of Cells')
        ax_longitudinal.set_title('Longitudinal Cell Count')
        ax_longitudinal.set_xlabel('Time (Days)')
        ax_longitudinal.set_ylabel('Number of Cells')

        plt.tight_layout()
        plt.subplots_adjust(hspace=0.40)
        plt.show()
    
    def plot_count(self, data_dict, scale_option="Absolute", is_injury=False, injury_time_mcs=0):
        """
        Example: highlight injury time by recentering x-axis and drawing a vertical line
        plus a 'homeostasis' horizontal line from pre-injury average.
        """
        # 1) Combine data
        combined_data = pd.concat(data_dict.values())
        combined_data = combined_data[combined_data['Time'] <= self.max_time]
        mean_data = combined_data.groupby('Time').mean().reset_index()

        # 2) Identify your cell type columns (assuming [Time, STEM, BASAL, WING, SUPERFICIAL])
        cell_types = mean_data.columns[1:5]

        # 3) Possibly apply scaling (Percentage, PctChangeFromMean, etc.) as before
        if scale_option == "Percentage":
            total_counts = mean_data[cell_types].sum(axis=1)
            mean_data[cell_types] = mean_data[cell_types].div(total_counts, axis=0).fillna(0)*100
        elif scale_option == "PctChangeFromMean":
            for c in cell_types:
                baseline = mean_data[c].mean()
                mean_data[c] = (mean_data[c] - baseline)/baseline*100

        # 4) Convert MCS to days and SHIFT if there's an injury
        #    If is_injury == True, we re-center so that injury_time is 0.
        #    If is_injury == False, just plot normally from 0..(SimTime/24).
        time_mcs = mean_data["Time"].values
        if is_injury:
            # user has indicated an injury event
            # shift time so that t=0 is the injury day
            injury_time_days = injury_time_mcs / 240.0
            time_in_days = (time_mcs / 24.0) - injury_time_days
        else:
            time_in_days = time_mcs / 24.0

        # 5) Compute 'homeostasis' for pre-injury times if desired
        #    We can define "homeostasis" as the average from, say, time<InjuryTime.
        #    For example, the total cell count or a particular cell type.
        homeostasis_dict = {}
        if is_injury:
            # Just as an example, let's compute the sum of all cell types as "total"
            # or do it individually for each cell type. Up to you.
            pre_injury_data = mean_data[mean_data["Time"] < injury_time_mcs]
            if not pre_injury_data.empty:
                for c in cell_types:
                    homeostasis_dict[c] = pre_injury_data[c].mean()
            else:
                # If there's no data pre_injury, fallback to 0
                for c in cell_types:
                    homeostasis_dict[c] = 0
        # else, do nothing.

        # 6) Plot: Combined with WING on a secondary axis
        fig, ax_main = plt.subplots(figsize=(12,6))
        ax_wing = ax_main.twinx()

        for i, c in enumerate(cell_types):
            if c.upper() == "WING":
                ax_wing.plot(time_in_days, mean_data[c], label=f"{c}", color=self.color_codes[i], linewidth=2)
            else:
                ax_main.plot(time_in_days, mean_data[c], label=f"{c}", color=self.color_codes[i], linewidth=2)

        # 7) Mark the injury time with a vertical line at x=0
        if is_injury:
            ax_main.axvline(0, color='red', linestyle='--', label='Injury')

        # 8) Optionally, overlay a horizontal line for homeostasis
        #    For example, let's do a single line for "STEM" homeostasis or "total" homeostasis.
        #    Or we can do separate lines for each cell type if you like.
        #    Example: single 'total' line:
        if is_injury and "STEM" in cell_types:
            # We can choose "STEM" for demonstration:
            h_value = homeostasis_dict.get("STEM", 0)
            ax_main.axhline(y=h_value, color='green', linestyle=':', label='STEM Homeostasis')

        ax_main.set_xlabel("Days Relative to Injury" if is_injury else "Time (Days)")
        if scale_option == "Percentage":
            ax_main.set_ylabel("Cell Percentage (%)")
            ax_wing.set_ylabel("Wing Percentage (%)")
        elif scale_option == "PctChangeFromMean":
            ax_main.set_ylabel("% Change from Mean")
            ax_wing.set_ylabel("% Change from Mean (Wing)")
        else:
            ax_main.set_ylabel("Cell Count (non-wing)")
            ax_wing.set_ylabel("Wing Cell Count")

        ax_main.legend(loc="upper left")
        ax_wing.legend(loc="upper right")
        ax_main.set_title("Cell Count with Injury Highlight" if is_injury else "Cell Count")
        ax_main.grid(True)
        plt.tight_layout()
        plt.show()
    # def plot_count(self, data_dict, scale_option="PctChangeFromMean"):
    #     """
    #     Plot cell counts for STEM, BASAL, WING, and SUPERFICIAL over time.
        
    #     scale_option can be one of:
    #     1. "Count": Raw cell counts (default).
    #     2. "Percentage": Each cell type is shown as percentage of the total at each time point.
    #     3. "PctChangeFromMean": Each cell type is shown as % change from its own mean over the entire dataset.
    #     """
    #     # Combine data from all replicates and restrict to time <= max_time
    #     combined_data = pd.concat(data_dict.values())
    #     combined_data = combined_data[combined_data['Time'] <= self.max_time]
    #     mean_data = combined_data.groupby('Time').mean().reset_index()

    #     # The columns after 'Time' are assumed to be: [STEM, BASAL, WING, SUPERFICIAL].
    #     # Confirm your actual CSV has them in that order; if not, adjust indices or rename columns.
    #     cell_types = mean_data.columns[1:5]  # e.g. 'STEM', 'BASAL', 'WING', 'SUPERFICIAL'

    #     # --- 1) Apply the requested scaling to the "mean_data" used for the combined lines ---
    #     if scale_option == "Percentage":
    #         # Convert each cell type to a % of the total
    #         total_counts = mean_data[cell_types].sum(axis=1)
    #         for col in cell_types:
    #             mean_data[col] = (mean_data[col] / total_counts) * 100.0

    #     elif scale_option == "PctChangeFromMean":
    #         # For each cell type, compute baseline mean and convert to % difference from that mean
    #         for col in cell_types:
    #             baseline = mean_data[col].mean()  # Could also use stable-time subset if desired
    #             mean_data[col] = (mean_data[col] - baseline) / baseline * 100.0
    #     # if scale_option == "Count", no changes needed

    #     # --- 2) Create a combined plot with a secondary y-axis for WING ---
    #     fig, ax_long = plt.subplots(figsize=(12, 6))
    #     wing_ax = ax_long.twinx()

    #     # We’ll plot STEM, BASAL, and SUPERFICIAL on ax_long; WING on wing_ax
    #     for i, col in enumerate(cell_types):
    #         if col.upper() == "WING":
    #             # Wing on secondary axis
    #             wing_ax.plot(mean_data["Time"]/24, mean_data[col],
    #                         label=f'Mean {col}', color=self.color_codes[i], linewidth=2)
    #         else:
    #             # All others on the primary axis
    #             ax_long.plot(mean_data["Time"]/24, mean_data[col],
    #                         label=f'Mean {col}', color=self.color_codes[i], linewidth=2)

    #     # Add vertical line at stable_time (if you want to highlight it)
    #     ax_long.axvline(self.stable_time/24, color='black',
    #                     linestyle='dashed', linewidth=1,
    #                     label="Stability Time")

    #     # Labels depend on scale
    #     if scale_option == "Percentage":
    #         ax_long.set_ylabel("Cell Percentage (%)")
    #         wing_ax.set_ylabel("Wing Cell Percentage (%)")
    #     elif scale_option == "PctChangeFromMean":
    #         ax_long.set_ylabel("% Change from Mean")
    #         wing_ax.set_ylabel("Wing: % Change from Mean")
    #     else:
    #         ax_long.set_ylabel("Cell Count (Non-wing)")
    #         wing_ax.set_ylabel("Wing Cell Count")

    #     ax_long.set_xlabel("Time (Days)")
    #     ax_long.set_title("Combined Plot of Cell Counts")
    #     ax_long.legend(loc="upper left")
    #     wing_ax.legend(loc="upper right")
    #     ax_long.grid(True, linewidth=0.1)
    #     plt.tight_layout()
    #     plt.show()

    #     # --- 3) Individual Time Series Plots by Cell Type ---
    #     # We’ll create separate subplots, each focusing on just one cell type.
    #     # Here we can optionally apply the same transform or a different one.
    #     # For simplicity, let's apply the *same* scale_option logic.
    #     # But if you prefer "PctChangeFromMean" only on the separate subplots,
    #     # you could handle that differently here.

    #     # If we also need the replicate-level lines, we'd re-compute or re-transform each replicate;
    #     # for brevity, we’ll just show the mean lines. Adjust as needed.

    #     # Re-do the transformation for a fresh copy, if we want the same logic on the subplots:
    #     subplots_data = combined_data.groupby('Time').mean().reset_index()
    #     if scale_option == "Percentage":
    #         total_counts = subplots_data[cell_types].sum(axis=1)
    #         for col in cell_types:
    #             subplots_data[col] = (subplots_data[col] / total_counts) * 100.0
    #     elif scale_option == "PctChangeFromMean":
    #         for col in cell_types:
    #             baseline = subplots_data[col].mean()
    #             subplots_data[col] = (subplots_data[col] - baseline) / baseline * 100.0
        
    #     fig_types, axs = plt.subplots(nrows=len(cell_types), figsize=(10, 3 * len(cell_types)), sharex=True)
    #     if len(cell_types) == 1:
    #         axs = [axs]  # Ensure axs is iterable if only one cell type

    #     for ax, col in zip(axs, cell_types):
    #         # Plot the (mean) time series
    #         ax.plot(subplots_data["Time"] / 24, subplots_data[col],
    #                 label=col, color=self.color_codes[cell_types.tolist().index(col)], linewidth=2)

    #         if scale_option == "Percentage":
    #             ax.set_ylabel("Percentage (%)")
    #         elif scale_option == "PctChangeFromMean":
    #             ax.set_ylabel("% Change from Mean")
    #         else:
    #             ax.set_ylabel("Cell Count")
            
    #         ax.set_title(f"{col} Over Time")
    #         ax.grid(True, linewidth=0.1)
    #         ax.legend()

    #     axs[-1].set_xlabel("Time (Days)")
    #     plt.tight_layout()
    #     plt.show()

    def plot_thickness(self, data_dict, scale_option="Absolute"):
        """
        Create thickness vs. time plots for each bin (like "0-20μm", "20-40μm", etc.).
        
        scale_option in {"Absolute", "Percentage", "PctChangeFromMean"}:
        - "Absolute": Raw (mean) thickness by bin over time.
        - "Percentage": Each bin's thickness is shown as a fraction of the
                        sum of all bins at a given time (x100).
        - "PctChangeFromMean": For each bin, thickness is shown as % change
                                from that bin's own mean thickness.

        We do two plots:
        1. A combined line plot (time on X axis, one line per bin).
        2. A subplot per bin, each with time on X axis.
        """
        # ---------------------------------------------------------
        # 1) Combine thickness data from all replicates
        # ---------------------------------------------------------
        # data_dict is e.g. { "rep1": df1, "rep2": df2, ... },
        # each df has at least columns: "Time", "Bin", "Height".
        all_data = pd.concat(data_dict.values(), ignore_index=True)

        # Optional: filter to self.max_time if needed
        all_data = all_data[all_data['Time'] <= self.max_time]

        # Group by (Time, Bin), compute mean across replicates
        grouped = all_data.groupby(['Time', 'Bin'], as_index=False)['Height'].mean()

        # Sort by Time so the pivot is in chronological order
        grouped = grouped.sort_values(by='Time')

        # Pivot so columns = Bin, index = Time, values = mean(Height)
        pivot_df = grouped.pivot(index='Time', columns='Bin', values='Height')

        # If your Time is in MCS, convert it to days for plotting
        # (Remove /24 if you already have hours or something else.)
        time_in_days = pivot_df.index / 24.0  

        # ---------------------------------------------------------
        # 2) Rename columns so they reflect the actual X-coord range
        # ---------------------------------------------------------
        # Example: If you had 10 bins across 200μm => each bin is 20μm wide.
        bin_size = 200 / 10.0  # change if your domain is different
        old_bin_ids = pivot_df.columns.tolist()  # e.g. [0,1,2,...,9]

        # Generate new labels like "0–20", "20–40", etc.
        new_bin_labels = []
        for b in old_bin_ids:
            start_x = int(b * bin_size)
            end_x = int(start_x + bin_size)
            new_bin_labels.append(f"{start_x}-{end_x}")  # e.g. "0-20", "20-40", etc.

        # Rename columns in the pivoted DataFrame
        pivot_df.columns = new_bin_labels  # so pivot_df has columns "0–20", "20–40", etc.

        # ---------------------------------------------------------
        # 3) Apply scale_option
        # ---------------------------------------------------------
        if scale_option == "Percentage":
            # At each time, sum across bins => pivot_df.sum(axis=1)
            # Then divide each bin by that sum, multiply by 100
            total_per_time = pivot_df.sum(axis=1)
            # Watch out for any zero sums => if all bins=0 at some time
            pivot_df = pivot_df.div(total_per_time, axis=0).fillna(0) * 100.0

        elif scale_option == "PctChangeFromMean":
            # For each bin, compute mean (over entire times).
            # If you only want stable-time, you can filter pivot_df first:
            # stable_times = pivot_df.index >= self.stable_time
            # bin_means = pivot_df.loc[stable_times].mean(axis=0)
            # pivot_df = (pivot_df - bin_means) / bin_means * 100.0
            # Otherwise, entire time range:
            bin_means = pivot_df.mean(axis=0)
            pivot_df = (pivot_df - bin_means) / bin_means * 100.0

        # If scale_option == "Absolute", do nothing (raw thickness).

        # ---------------------------------------------------------
        # 4) Plot #1: Single figure with a line per bin
        # ---------------------------------------------------------
        fig, ax = plt.subplots(figsize=(12, 6))

        # Let’s use a color palette.  If you have more than 10 bins,
        # you may want "tab20" or something else.
        palette = sns.color_palette("husl", len(new_bin_labels))

        for i, bin_label in enumerate(new_bin_labels):
            ax.plot(time_in_days, pivot_df[bin_label],
                    color=palette[i], linewidth=2,
                    label=f"X Coord. {bin_label}")

        # Mark stability time, if desired
        ax.axvline(self.stable_time / 24.0, color='black', linestyle='--',
                linewidth=1, label="Stability Time")

        # X label is time in days
        ax.set_xlabel("Time (Days)")
        # Y label depends on scale
        if scale_option == "Absolute":
            ax.set_ylabel("Thickness (raw)")
        elif scale_option == "Percentage":
            ax.set_ylabel("Thickness as % of Total")
        else:  # "PctChangeFromMean"
            ax.set_ylabel("% Change from X Coord. Mean")

        ax.set_title("Combined Thickness by X Coord.")
        ax.grid(True, linewidth=0.1)
        ax.legend(loc="best")
        plt.tight_layout()
        plt.show()

        # ---------------------------------------------------------
        # 5) Plot #2: One subplot per bin
        # ---------------------------------------------------------
        n_bins = len(new_bin_labels)
        fig2, axs = plt.subplots(n_bins, 1, figsize=(10, 3 * n_bins), sharex=True)
        if n_bins == 1:
            axs = [axs]  # Ensure iterable if only 1 bin

        for ax_bin, bin_label in zip(axs, new_bin_labels):
            ax_bin.plot(time_in_days, pivot_df[bin_label],
                        color=palette[new_bin_labels.index(bin_label)],
                        linewidth=2, label=f"X Coord. {bin_label}")

            ax_bin.axvline(self.stable_time / 24.0, color='black', linestyle='--', linewidth=1)
            
            if scale_option == "Absolute":
                ax_bin.set_ylabel("Thickness")
            elif scale_option == "Percentage":
                ax_bin.set_ylabel("% of Total")
            else:  # "PctChangeFromMean"
                ax_bin.set_ylabel("% from Mean")

            ax_bin.set_title(f"Time Series for X Coord. {bin_label}")
            ax_bin.grid(True, linewidth=0.1)
            ax_bin.legend()

        axs[-1].set_xlabel("Time (Days)")
        plt.tight_layout()
        plt.show()

    def plot_thickness_old(self, data_dict, bin_memb):
        unique_bins = set()
        for data in data_dict.values():
            unique_bins.update(data['Bin'].unique())
        unique_bins = sorted(unique_bins)
        color_palette = sns.color_palette("colorblind", len(unique_bins))
        bin_color_map = {bin_key: color_palette[i] for i, bin_key in enumerate(unique_bins)}
        bins_size = 200 // len(unique_bins)  # Size in μm
        bin_x = {bin_key: [] for _, bin_key in enumerate(unique_bins)}

        for key in bin_x.keys():
            bin_x[key] = [i for i in range(key * bins_size, int((key + 1) * bins_size))]
            bin_x[key] = np.mean(bin_x[key])  # Position in μm
        bin_actual = []
        bin_relative = []

        # if suplemental:
        #     fig, ax = plt.subplots(3, figsize=(14, 17))
        # else:
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
        
        # if suplemental:
        #     for bin_key in unique_bins:
        #         bin_data = combined_data[combined_data['Bin'] == bin_key]
        #         bin_data_stable = bin_data[bin_data['Time'] >= self.stable_time]        
        #         adjusted_height = (bin_data_stable['Height'] - bin_memb[bin_key]) * 2  # Full thickness in μm
                
        #         sns.kdeplot((bin_data_stable['Height'])*2, ax=ax[2], label=f'Rel. H. X {bin_key * bins_size}-{int((bin_key + 1) * bins_size) - 1}',
        #                     linestyle='--', alpha=0.5, color=bin_color_map[bin_key])
                
        #         sns.kdeplot(adjusted_height, ax=ax[2], label=f'Act. Thic. X {bin_key * bins_size}-{int((bin_key + 1) * bins_size) - 1}',
        #                     fill=True, alpha=0.5, color=bin_color_map[bin_key])
            
        #     ax[2].set_title('Stable Tissue Top Possition and Thickness Distribution of Tissue Sections')
        #     ax[2].set_xlabel('Thickness (μm)')
        #     ax[2].set_ylabel('Density')
        #     ax[2].legend(title='Bins', loc='upper left')
        #     ax[2].grid(True, linewidth=0.1)

        plt.tight_layout()
        plt.subplots_adjust(hspace=0.20)
        # plt.savefig(f"{out_dir}/Thickness.png")
        plt.show()    
