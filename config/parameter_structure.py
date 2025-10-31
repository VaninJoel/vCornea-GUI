parameter_structure = {
    "Cells Parameters": {
        "STEM": {
            "InitSTEM_LambdaSurface": "How strongly a stem cell regulates its surface area towards a desired size.",
            "InitSTEM_TargetSurface": "The ideal surface area each stem cell tries to maintain.",
            "InitSTEM_LambdaVolume": "How strongly a stem cell regulates its volume towards a desired size.",
            "InitSTEM_TargetVolume": "The ideal volume each stem cell tries to maintain.",
            "DensitySTEM_HalfMaxValue": "The cell density at which stem cells achieve half of their maximum growth response.",
            "EGF_STEM_HalfMaxValue": "The EGF concentration at which stem cells achieve half of their maximum growth response.",
            "STEM_beta_EGF": "How sensitive stem cells are to changes in EGF levels.",
            "InitSTEM_LambdaChemo": "How strongly stem cells move toward areas of higher chemoattractant (like EGF)."
        },
        "BASAL": {
            "InitBASAL_LambdaSurface": "How strongly a basal cell regulates its surface area towards a desired size.",
            "InitBASAL_TargetSurface": "The ideal surface area each basal cell tries to maintain.",
            "InitBASAL_LambdaVolume": "How strongly a basal cell regulates its volume towards a desired size.",
            "InitBASAL_TargetVolume": "The ideal volume each basal cell tries to maintain.",
            "InitBASAL_LambdaChemo": "How strongly basal cells move toward areas with more chemoattractant.",
            "InitBASAL_Division": "How many times a basal cell can divide before it stops proliferating.",
            "DensityBASAL_HalfMaxValue": "The cell density at which basal cells achieve half of their maximum growth response.",
            "EGF_BASAL_HalfMaxValue": "The EGF concentration at which basal cells achieve half of their maximum growth response.",
            "BASAL_beta_EGF": "How sensitive basal cells are to changes in EGF levels."
        },
        "WING": {
            "InitWING_LambdaSurface": "How strongly a wing cell regulates its surface area towards a desired size.",
            "InitWING_TargetSurface": "The ideal surface area each wing cell tries to maintain.",
            "InitWING_LambdaVolume": "How strongly a wing cell regulates its volume towards a desired size.",
            "InitWING_TargetVolume": "The ideal volume each wing cell tries to maintain.",
            "InitWING_EGFLambdaChemo": "How strongly wing cells move toward regions with higher EGF concentration."
        },
        "SUPERFICIAL": {
            "InitSUPER_LambdaSurface": "How strongly a superficial cell regulates its surface area towards a desired size.",
            "InitSUPER_TargetSurface": "The ideal surface area each superficial cell tries to maintain.",
            "InitSUPER_LambdaVolume": "How strongly a superficial cell regulates its volume towards a desired size.",
            "InitSUPER_TargetVolume": "The ideal volume each superficial cell tries to maintain.",
            "EGF_SUPERDiffCoef": "How quickly EGF diffuses (spreads) through superficial cells."
        }
    },
    "Fields": {
        "Movement Bias": {
            "MovementBiasScreteAmount": "The constant amount of chemoattractant secreted by the boundary (Bowman's membrane) to guide cell movement.",
            "MovementBiasUptake": "How quickly basal cells absorb (take up) this chemoattractant."
        },
        "EGF": {
            "EGF_ScreteAmount": "The constant amount of EGF introduced into the system (e.g., from tear fluid).",
            "EGF_FieldUptakeBASAL": "How quickly basal cells consume EGF from their surroundings.",
            "EGF_FieldUptakeSTEM": "How quickly stem cells consume EGF from their surroundings.",
            "EGF_FieldUptakeSuper": "How quickly superficial cells consume EGF.",
            "EGF_FieldUptakeWing": "How quickly wing cells consume EGF.",
            "EGF_GlobalDecay": "The overall rate at which EGF naturally breaks down (decays) over time."
        }
    },
    "Links": {
        "SUPER-WALL": {
            "LINKWALL_lambda_distance": "How strongly the link between superficial cells and the simulation boundary tries to maintain a set distance.",
            "LINKWALL_target_distance": "The desired resting length of the link between superficial cells and the boundary.",
            "LINKWALL_max_distance": "The maximum length the link between superficial cells and the boundary can stretch before it breaks or no longer applies."
        },
        "SUPER-SUPER": {
            "LINKSUPER_lambda_distance": "How strongly the link between two superficial cells tries to maintain a set distance.",
            "LINKSUPER_target_distance": "The desired resting length of the link between superficial cells.",
            "LINKSUPER_max_distance": "The maximum length the link between superficial cells can stretch before it breaks.",
            "AutoAdjustLinks": "If enabled, the link properties are automatically adjusted to keep the tension stable over time.",
            "Lambda_link_adjustment": "When auto-adjusting links, determines if the tension coefficient (lambda) or the target distance is modified to maintain consistent tension.",
            "Tension_link_SS": "The constant tension force that the links between superficial cells should maintain."
        }
    },
    "Wound Parameters": {
        "ENABLES INJURY, DEFINE TIME AND TYPE OF INJURY": {
            "IsInjury": "Enable or disable the injury feature in the simulation.",
            "InjuryType": "Choose the type of injury (e.g., ablation or chemical).",
            "InjuryTime": "The simulation time at which the injury event occurs."
        },
        "ABLATION": {
            "InjuryX_Center": "The x-coordinate of the ablation injury center.",
            "InjuryY_Center": "The y-coordinate of the ablation injury center.",
            "InjuryRadius": "How far from the center cells are affected by the ablation (a radius)."
        },
        "CHEMICAL": {
            "SLS_Injury": "Enable or disable a chemical-based injury using SLS (for testing how chemicals spread and affect cells).",
            "SLS_X_Center": "The x-coordinate of the center of the chemical source.",
            "SLS_Y_Center": "The y-coordinate of the center of the chemical source.",
            "SLS_Concentration": "The initial strength or concentration of the chemical introduced.",
            "SLS_Gaussian_pulse": "Whether the chemical is introduced as a concentrated 'droplet' (Gaussian) or as a uniform 'coating'.",
            "SLS_STEMDiffCoef": "How quickly the chemical spreads inside stem cells.",
            "SLS_BASALDiffCoef": "How quickly the chemical spreads inside basal cells.",
            "SLS_WINGDiffCoef": "How quickly the chemical spreads inside wing cells.",
            "SLS_SUPERDiffCoef": "How quickly the chemical spreads inside superficial cells.",
            "SLS_MEMBDiffCoef": "How quickly the chemical spreads in the Bowman's membrane (periphery).",
            "SLS_LIMBDiffCoef": "How quickly the chemical spreads in the Bowman's membrane (limbal region).",
            "SLS_TEARDiffCoef": "How quickly the chemical spreads in the tear layer.",
            "SLS_Threshold_Method": "If enabled, cells will die when the chemical level surpasses a certain threshold.",
            "SLS_Threshold": "The chemical concentration limit above which cells are considered dead."
        }
    },
    "Fuctions Control": {
        "TURN OFF FUNCTIONS FOR DEBUGGING": {
            "GrowthControl": "Enable or disable cell growth processes for debugging.",
            "MitosisControl": "Enable or disable cell division (mitosis) for debugging.",
            "DeathControl": "Enable or disable cell death mechanisms for debugging.",
            "DifferentiationControl": "Enable or disable cell differentiation processes for debugging."
        }
    },
    "Plots": {
        "DATA COLECTION AND REAL-TIME PLOTS": {
            "CC3D_PLOT": "Enable or disable real-time visualization in CC3D.",
            "CellCount": "Collect and plot the number of cells over time.",
            "CellCountScale": "Cell Count Scale Mode (Absolute, Percentage, PctChangeFromMean)",        
            "PressureTracker": "Show a real-time plot of pressure in the simulation.",
            "EGF_SeenByCell": "Track and plot the EGF concentration experienced by each cell.",
            "SLS_SeenByCell": "Track and plot the chemical concentration experienced by each cell.",
            "CenterBias": "Track and plot the chemoattractant concentration at the boundary in real-time.",
            "ThicknessPlot": "Collect and plot data on the tissue thickness over time.",
            "ThicknessScale": "Thickness Plot Scale Mode (Absolute, Percentage, PctChangeFromMean)",
            "SurfactantTracking": "Track and plot surfactant distribution over time.",
            "SnapShot": "Take snapshots of the simulation state at regular intervals."
        }
    },
    "Simulation Time": {
        "END OF SIMULATION TIME": {
            "SimTime": "How long the simulation runs before it stops (in days)."
        }
    }
}

