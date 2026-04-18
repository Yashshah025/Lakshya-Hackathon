from datetime import datetime
import json

class AlertEngine:
    def __init__(self):
        self.alerts = []
        self.acknowledgements = {
            "Police": None,
            "Temple Trust": None,
            "Transport": None
        }

    def process_state(self, current_tick, predicted_pressure):
        """
        Determines risk level and generates alerts.
        """
        pressure = current_tick['pressure_index']
        gradient = current_tick['pressure_gradient']
        density = current_tick['density']
        
        risk_level = "SAFE"
        is_real_risk = False
        
        if pressure > 20.0 or predicted_pressure > 20.0:
            risk_level = "HIGH RISK"
            # Smart classification: REAL if sustained increase + high density
            if gradient > 1.0 and density > 0.3:
                is_real_risk = True
        elif pressure > 15.0:
            risk_level = "WARNING"
            
        if risk_level != "SAFE":
            alert = self.generate_alert(risk_level, is_real_risk, predicted_pressure)
            self.alerts.append(alert)
            return alert
        
        return None

    def generate_alert(self, level, is_real, pred_pressure):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        actions = {
            "Police": "Deploy personnel to corridor exit; manage flow.",
            "Temple Trust": "PAUSE DARSHAN ENTRY; clear holding areas.",
            "Transport": "HOLD all incoming buses for 15 mins."
        } if is_real else {
            "Police": "Increase monitoring; standby for deployment.",
            "Temple Trust": "Slow down entry gates.",
            "Transport": "Advise bus drivers of delay."
        }

        return {
            "id": len(self.alerts) + 1,
            "timestamp": timestamp,
            "level": level,
            "type": "REAL CRUSH RISK" if is_real else "TEMPORARY SURGE",
            "predicted_pressure": round(pred_pressure, 2),
            "confidence": 0.88 if is_real else 0.65,
            "actions": actions,
            "acknowledged": {"Police": False, "Temple Trust": False, "Transport": False}
        }

    def acknowledge(self, alert_id, agency):
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['acknowledged'][agency] = True
                alert[f'{agency}_ack_time'] = datetime.now().strftime("%H:%M:%S")
                return True
        return False

    def get_active_alerts(self):
        return self.alerts[-10:] # Return last 10 alerts
