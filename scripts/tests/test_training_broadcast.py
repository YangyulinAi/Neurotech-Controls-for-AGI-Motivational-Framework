#!/usr/bin/env python3
"""
Test script to verify training progress broadcast is working correctly.
"""

import requests
import json
import time

def test_training_broadcast():
    url = "http://localhost:5000/api/bci/broadcast"
    
    # Test training progress message
    training_data = {
        "type": "training_progress",
        "epoch": 1,
        "total_epochs": 10,
        "loss": 0.3456,
        "best_loss": 0.3456,
        "learning_rate": 0.0001,
        "epoch_time": 15.2,
        "progress_percentage": 10.0
    }
    
    print("Testing training progress broadcast...")
    print(f"Sending data: {json.dumps(training_data, indent=2)}")
    
    try:
        response = requests.post(url, json=training_data, timeout=5)
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 200:
            print("✓ Training progress broadcast successful!")
        else:
            print("✗ Training progress broadcast failed!")
            
    except Exception as e:
        print(f"✗ Request failed: {e}")

    # Test BCI data message
    bci_data = {
        "valence": 0.5,
        "arousal": -0.2,
        "timestamp": int(time.time() * 1000)
    }
    
    print("\nTesting BCI data broadcast...")
    print(f"Sending data: {json.dumps(bci_data, indent=2)}")
    
    try:
        response = requests.post(url, json=bci_data, timeout=5)
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 200:
            print("✓ BCI data broadcast successful!")
        else:
            print("✗ BCI data broadcast failed!")
            
    except Exception as e:
        print(f"✗ Request failed: {e}")

if __name__ == "__main__":
    test_training_broadcast()