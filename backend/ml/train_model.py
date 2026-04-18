import pandas as pd
import numpy as np
import joblib
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from features import calculate_features
import os

def train():
    print("Loading dataset...")
    dataset_path = 'data/dataset.xlsx'
    if not os.path.exists(dataset_path):
        dataset_path = '../data/dataset.xlsx'
    
    df = pd.read_excel(dataset_path)
    
    # Mapping columns
    df = df.rename(columns={
        'entry_flow_rate_pax_per_min': 'entry_count',
        'exit_flow_rate_pax_per_min': 'exit_count',
        'vehicle_count': 'vehicle_arrivals',
        'corridor_width_m': 'corridor_width'
    })
    
    # Process features
    print("Engineering features...")
    df = calculate_features(df)
    
    # Prepare training data for Prediction Engine
    # We want to predict future_pressure (8-12 mins ahead)
    # Target: pressure_index shifted by -10 mins
    df['target_pressure'] = df['pressure_index'].shift(-10)
    df = df.dropna()
    
    features = [
        'entry_rate', 'exit_rate', 'vehicle_arrivals', 
        'density', 'pressure_index', 'rolling_mean_pressure', 
        'pressure_gradient', 'capacity_utilization'
    ]
    
    X = df[features]
    y = df['target_pressure']
    
    # Time-series Split (Chronological, NO shuffling to prevent data leakage)
    split_1 = int(len(X) * 0.70)
    split_2 = int(len(X) * 0.85)
    
    X_train, y_train = X.iloc[:split_1], y.iloc[:split_1]
    X_val, y_val = X.iloc[split_1:split_2], y.iloc[split_1:split_2]
    X_test, y_test = X.iloc[split_2:], y.iloc[split_2:]
    
    print(f"Dataset splits -> Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    print("Training XGBoost Model in chronological order...")
    model = XGBRegressor(n_estimators=200, max_depth=6, learning_rate=0.05, random_state=42, n_jobs=-1, eval_metric="mae")
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    
    def evaluate(model, X_split, y_split, name):
        preds = model.predict(X_split)
        r2 = r2_score(y_split, preds)
        mae = mean_absolute_error(y_split, preds)
        print(f"--- {name} set ---")
        print(f"Accuracy (R-Squared): {r2*100:.2f}%")
        print(f"Mean Absolute Error: {mae:.2f} pressure units\n")
        
    evaluate(model, X_train, y_train, "Train")
    evaluate(model, X_val, y_val, "Validation")
    evaluate(model, X_test, y_test, "Test")
    
    # Save model and feature list
    model_dir = 'models'
    if not os.path.exists(model_dir) and os.path.exists('../models'):
        model_dir = '../models'
    
    os.makedirs(model_dir, exist_ok=True)
    joblib.dump(model, f'{model_dir}/pressure_model.pkl')
    joblib.dump(features, f'{model_dir}/feature_columns.pkl')
    print(f"Model saved to {model_dir}/pressure_model.pkl")

if __name__ == "__main__":
    train()
