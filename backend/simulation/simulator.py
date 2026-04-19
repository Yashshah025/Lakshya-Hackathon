import pandas as pd
import os
import time
import threading
from ml.features import calculate_features

class CrowdSimulator:
    def __init__(self, data_path='data/dataset.xlsx'):
        self.data_path = data_path
        self.df = None
        self.current_index = 0
        self.is_running = False
        self.history = []
        self.enriched_history = []
        self.burst_active = False
    #Loading data 
    def load_data(self):
        dataset_path = self.data_path
        if not os.path.exists(dataset_path):
            dataset_path = '../' + self.data_path
        
        df = pd.read_excel(dataset_path)
        # Standardize columns
        self.df = df.rename(columns={
            'entry_flow_rate_pax_per_min': 'entry_count',
            'exit_flow_rate_pax_per_min': 'exit_count',
            'vehicle_count': 'vehicle_arrivals',
            'corridor_width_m': 'corridor_width'
        })
        print(f"Simulator loaded {len(self.df)} rows.")

    def start(self, callback):
        self.is_running = True
        self.thread = threading.Thread(target=self._run, args=(callback,))
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.is_running = False

    def trigger_burst(self):
        self.burst_active = True
        print("WHAT-IF triggered: Sudden transport burst injected!")

    def _run(self, callback):
        while self.is_running and self.current_index < len(self.df):
            row = self.df.iloc[[self.current_index]].copy()
            
            
            if self.burst_active:
                row['vehicle_arrivals'] += 20
                self.burst_active = False # Reset burst
                
            self.history.append(row)
            
            # Re-calculate features on the history to get rolling metrics
            history_df = pd.concat(self.history)
            enriched_df = calculate_features(history_df)
            
            latest_tick = enriched_df.tail(1).to_dict('records')[0]
            self.enriched_history.append(latest_tick)
            callback(latest_tick)
            
            self.current_index += 1
            time.sleep(2) # 2 seconds = 1 minute simulation time
    #Replay the data
    def get_replay_data(self):
        if not self.enriched_history:
            return pd.DataFrame()
        return pd.DataFrame(self.enriched_history)
