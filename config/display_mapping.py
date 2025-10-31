# Define a mapping from parameter variable names to user-friendly display names
display_name_mapping = {
    # Cells Parameters - STEM
    "InitSTEM_LambdaSurface": "Stem Surface Coefficient",
    "InitSTEM_TargetSurface": "Stem Target Surface",
    "InitSTEM_LambdaVolume": "Stem Volume Coefficient",
    "InitSTEM_TargetVolume": "Stem Target Volume",
    "DensitySTEM_HalfMaxValue": "Stem Density Half-Max",
    "EGF_STEM_HalfMaxValue": "Stem EGF Half-Max",
    "STEM_beta_EGF": "Stem EGF Sensitivity",
    "InitSTEM_LambdaChemo": "Movement Bias Stem Chemotaxis Coefficient",

    # Cells Parameters - BASAL
    "InitBASAL_LambdaSurface": "Basal Surface Coefficient",
    "InitBASAL_TargetSurface": "Basal Target Surface",
    "InitBASAL_LambdaVolume": "Basal Volume Coefficient",
    "InitBASAL_TargetVolume": "Basal Target Volume",
    "InitBASAL_LambdaChemo": "Movement Bias Basal Chemotaxis Coefficient",
    "InitBASAL_Division": "Basal Division Coefficient",
    "DensityBASAL_HalfMaxValue": "Basal Density Half-Max",
    "EGF_BASAL_HalfMaxValue": "Basal EGF Half-Max",
    "BASAL_beta_EGF": "Basal EGF Sensitivity",

    # Cells Parameters - WING
    "InitWING_LambdaSurface": "Wing Surface Coefficient",
    "InitWING_TargetSurface": "Wing Target Surface",
    "InitWING_LambdaVolume": "Wing Volume Coefficient",
    "InitWING_TargetVolume": "Wing Target Volume",
    "InitWING_EGFLambdaChemo": "EGF Wing Chemotaxis Coefficient",

    # Cells Parameters - SUPERFICIAL
    "InitSUPER_LambdaSurface": "Superficial Surface Coefficient",
    "InitSUPER_TargetSurface": "Superficial Target Surface",
    "InitSUPER_LambdaVolume": "Superficial Volume Coefficient",
    "InitSUPER_TargetVolume": "Superficial Target Volume",
    "EGF_SUPERDiffCoef": "Superficial EGF Diffusion Coefficient",

    # Fields - Movement Bias
    "MovementBiasScreteAmount": "Movement Bias Secretion",
    "MovementBiasUptake": "Movement Bias Uptake",

    # Fields - EGF
    "EGF_ScreteAmount": "EGF Secretion Amount",
    "EGF_FieldUptakeBASAL": "Basal EGF Uptake",
    "EGF_FieldUptakeSTEM": "Stem EGF Uptake",
    "EGF_FieldUptakeSuper": "Superficial EGF Uptake",
    "EGF_FieldUptakeWing": "Wing EGF Uptake",
    "EGF_GlobalDecay": "EGF Global Decay",

    # Links - SUPER-WALL
    "LINKWALL_lambda_distance": "Initial Link Superficial-Wall Lambda",
    "LINKWALL_target_distance": "Initial Link Superficial-Wall Target Distance",
    "LINKWALL_max_distance": "Link Superficial-Wall Max Distance",

    # Links - SUPER-SUPER
    "LINKSUPER_lambda_distance": "Initial Link Superficial-Superficial Lambda",
    "LINKSUPER_target_distance": "Initial Link Superficial-Superficial Target Distance",
    "LINKSUPER_max_distance": "Link Superficial-Superficial Maximum Distance",
    "AutoAdjustLinks": "Enable Auto Adjust Links",
    "Lambda_link_adjustment": "Lambda Link Adjustment",
    "Tension_link_SS": "Link Tension Between Superficial-Superficial Cells",

    # Wound Parameters - Injury Settings
    "IsInjury": "Enable Injury",
    "InjuryType": "Injury Type",
    "InjuryTime": "Injury Time (in days)",

    # Wound Parameters - Ablasion
    "InjuryX_Center": "Injury X Center",
    "InjuryY_Center": "Injury Y Center",
    "InjuryRadius": "Injury Radius",

    # Wound Parameters - Chemical
    "SLS_Injury": "Enable Chemical Injury",
    "SLS_X_Center": "Chemical X Center",
    "SLS_Y_Center": "Chemical Y Center",
    "SLS_Concentration": "Chemical Concentration",
    "SLS_Gaussian_pulse": "Chemical Distribution",
    "SLS_STEMDiffCoef": "Chemical Stem Diffusion",
    "SLS_BASALDiffCoef": "Chemical Basal Diffusion",
    "SLS_WINGDiffCoef": "Chemical Wing Diffusion",
    "SLS_SUPERDiffCoef": "Chemical Superficial Diffusion",
    "SLS_MEMBDiffCoef": "Chemical Membrane Diffusion",
    "SLS_LIMBDiffCoef": "Chemical Limbal Diffusion",
    "SLS_TEARDiffCoef": "Chemical Tear Diffusion",
    "SLS_Threshold_Method": "Enable Threshold Method Cell Death",
    "SLS_Threshold": "Chemical Threshold Value",

    # Debugging
    "GrowthControl": "Enable Growth",
    "MitosisControl": "Enable Mitosis",
    "DeathControl": "Enable Death",
    "DifferentiationControl": "Enable Differentiation",

    # Plots
    "CC3D_PLOT": "Enable CC3D Plots",
    "CellCount": "Cell Count",
    "PressureTracker": "Pressure Tracker",
    "EGF_SeenByCell": "Cell EGF Tracking",
    "SLS_SeenByCell": "Cell Chemical Tracking",
    "CenterBias": "Movement Bias Tracking",
    "ThicknessPlot": "Tissue Thickness Plot",
    "SurfactantTracking": "Chemical Tracking",
    "SnapShot": "Enable Snapshots",
    "SnapShot_time": "Snapshots Every (in hours)",

    # Simulation Time
    "SimTime": "Simulation Duration (in days)", 
}
