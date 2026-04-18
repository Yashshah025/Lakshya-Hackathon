import numpy as np
import pandas as pd

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def calculate_features(df, corridor_width=10, corridor_length=50, safe_density=2.0):
    """
    Computes core and derived features for crowd pressure analysis.
    df must contain: entry_count, exit_count, vehicle_arrivals
    """
    # 1. Core Features
    df['entry_rate'] = df['entry_count']
    df['exit_rate'] = df['exit_count']
    df['net_flow'] = df['entry_rate'] - df['exit_rate']
    
    # Cumulative people in corridor (assuming starts at 0 if no initial_count)
    df['current_people'] = df['net_flow'].cumsum().clip(lower=0)
    
    # Queue length (cumulative backlog - simulation of bottleneck)
    df['queue_length'] = (df['entry_rate'] * 0.2).cumsum() # Mock queue growth logic
    
    # 2. Geometry Features
    df['corridor_width'] = corridor_width
    df['corridor_length'] = corridor_length
    df['capacity'] = corridor_width * corridor_length * safe_density
    
    # 3. Derived Features
    df['density'] = df['current_people'] / (corridor_width * corridor_length)
    df['capacity_utilization'] = df['current_people'] / df['capacity']
    
    # Pressure Index Calculation
    # burst_factor: derived from vehicle arrivals (e.g., 5 people per vehicle burst)
    burst_factor = df['vehicle_arrivals'] * 5
    
    raw_pressure = (df['entry_rate'] + burst_factor) / corridor_width
    congestion_factor = sigmoid(df['queue_length'] / 100) # Normalized sigmoid
    
    df['pressure_index'] = raw_pressure * congestion_factor
    
    # Rolling Features
    df['rolling_mean_pressure'] = df['pressure_index'].rolling(window=5, min_periods=1).mean()
    df['pressure_gradient'] = df['pressure_index'].diff().fillna(0)
    
    # Sudden Spike Flag
    df['sudden_spike_flag'] = (df['pressure_gradient'] > 0.3).astype(int)
    
    return df

def classify_risk(row):
    """
    Logic:
    IF pressure increases continuously for 5+ minutes AND density is high: REAL CRUSH RISK
    ELSE: TEMPORARY SURGE
    """
    # Note: Continuous increase check requires windowing, which is better done in the engine
    # Here we do a simpler row-wise risk classification for the model to learn
    
    if row['pressure_index'] > 0.8:
        return 2  # HIGH RISK
    elif row['pressure_index'] > 0.5:
        return 1  # WARNING
    else:
        return 0  # SAFE
