# In gui/simulation_worker.py

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from vivarium.core.engine import Engine
from vivarium_vcornea.composites.vcornea_composer import VCorneaComposer

class SimulationWorker(QObject):
    """
    A worker that runs a Vivarium experiment in the background.
    Communicates back to the main GUI thread via signals.
    """
    
    finished = pyqtSignal(dict)    
    error = pyqtSignal(str)

    def __init__(self, process_config, sim_params):
        super().__init__()
        self.process_config = process_config
        self.sim_params = sim_params

    @pyqtSlot()
    def run(self):
        """The main method executed on the background thread."""
        try:
            print("Background worker started... Using Vivarium Engine.")
            
            # 1. Create the Vivarium Composer with the GUI's configuration
            # This config contains the model path, conda env, etc.
            composer = VCorneaComposer({'vcornea': self.process_config})
            composite = composer.generate()

            # 2. Define the initial state for the Vivarium simulation
            # The 'inputs' dictionary will be passed to the VCorneaProcess
            initial_state = {
                'inputs': self.sim_params,
                'outputs': {}
            }

            # 3. Create the Vivarium Engine
            sim = Engine(
                composite=composite,
                initial_state=initial_state
            )

            # 4. Run the simulation for a single step to trigger the VCorneaProcess
            # The process itself runs the entire CC3D simulation internally.
            sim.update(1.0)
            
            # 5. Get the final data from the emitter
            final_output_data = sim.emitter.get_data()
            final_results = final_output_data.get(1.0, {}) # Get data at time 1.0

            print("Background worker finished Vivarium simulation successfully.")

            # 6. Emit the 'finished' signal with the results
            self.finished.emit(final_results)

        except Exception as e:
            import traceback
            error_str = f"{str(e)}\n\n{traceback.format_exc()}"
            print(f"Background worker encountered an error: {error_str}")
            self.error.emit(error_str)

