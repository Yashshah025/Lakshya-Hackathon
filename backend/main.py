from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import pandas as pd
from ml.predictor import PressurePredictor
from ml.features import calculate_features
from engine import AlertEngine
from simulation.simulator import CrowdSimulator
import os

app = FastAPI(title="Crowd Crush Prevention API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
predictor = PressurePredictor()
alert_engine = AlertEngine()
simulator = CrowdSimulator()
current_state = {"latest_tick": None, "predicted_pressure": 0.0}

def simulation_callback(tick):
    global current_state
    
    # Run Prediction
    # We need a small history for the predictor if it uses rolling features
    history_df = simulator.get_replay_data()
    pred = predictor.predict(history_df)
    
    # Process Risk & Alerts
    alert = alert_engine.process_state(tick, pred)
    
    current_state["latest_tick"] = tick
    current_state["predicted_pressure"] = pred

@app.on_event("startup")
async def startup_event():
    simulator.load_data()

@app.get("/status")
def get_status():
    return {
        "status": "online",
        "simulation_running": simulator.is_running,
        "latest_data": current_state["latest_tick"],
        "predicted_pressure": current_state["predicted_pressure"]
    }

@app.post("/simulation/start")
def start_sim():
    if not simulator.is_running:
        simulator.start(simulation_callback)
    return {"message": "Simulation started"}

@app.post("/simulation/stop")
def stop_sim():
    simulator.stop()
    return {"message": "Simulation stopped"}

@app.post("/simulation/burst")
def trigger_burst():
    simulator.trigger_burst()
    return {"message": "What-if scenario triggered: Burst injected"}

@app.get("/alerts")
def get_alerts():
    return alert_engine.get_active_alerts()

@app.post("/alerts/acknowledge")
def acknowledge_alert(alert_id: int, agency: str):
    success = alert_engine.acknowledge(alert_id, agency)
    return {"success": success}

@app.get("/replay")
def get_replay():
    df = simulator.get_replay_data()
    if df.empty:
        return []
    return df.to_dict('records')

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
