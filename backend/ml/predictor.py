import joblib
import pandas as pd
import os

class PressurePredictor:
    def __init__(self, model_path='models/pressure_model.pkl'):
        if os.path.exists(model_path):
            self.model = joblib.load(model_path)
            self.features = joblib.load('models/feature_columns.pkl')
        else:
            self.model = None
            self.features = []

    def predict(self, current_data_df):
        """
        Input: DF with latest features
        Output: predicted pressure in 10 mins
        """
        if self.model is None:
            return 0.0
            
        X = current_data_df[self.features].tail(1)
        prediction = self.model.predict(X)[0]
        return max(0.0, float(prediction))
