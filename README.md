
# Neurotech Controls for AGI Motivational Framework

This project is a prototype for a brain-computer interface (BCI) framework that links human emotional and cognitive states (such as valence and arousal measured from EEG, fNIRS, and heart rate data) with Artificial General Intelligence (AGI) motivational systems. The system enables real-time modulation of AI agents based on the user's brain activity.

---

## Overview

The project leverages neurocognitive and psychological models (e.g., OpenPsi, Dorner’s Psi Theory) to develop a robust mechanism for controlling AGI behavior. Through a sequence of experiments—including resting state and video-based emotion induction—the framework captures labeled brain data and uses it to modulate motivational parameters.

Data processing and model training are structured into three main layers:

- **Data Collection and Preprocessing**
- **Offline Training and Model Export**
- **Online Inference and Application Integration**

---

## Architecture Overview

```
Data Collection → Offline Training → Online Inference → API Layer → Application Layer
 (LSL/XDF)         (PyTorch/ONNX)       (ONNX Runtime)   (WS/REST/MQTT)  (Unity/Web/IoT)
```

| Layer             | Key Files                          | Description                                      |
|-------------------|-----------------------------------|--------------------------------------------------|
| **Data Collection** | `lsl_receiver.py`                  | Collects raw EEG/fNIRS data using LSL in real-time |
| **Offline Training** | `train.py`, `preprocess.py`       | Data preprocessing, feature extraction, PyTorch model training, ONNX export |
| **Online Inference** | `main.py`, `onnx_runner.py`       | Real-time ONNX model inference using EEG streams |
| **API Layer**      | `websocket_server.py`, `api_rest.py`, `mqtt_publisher.py` | Pushes predictions to WebSocket/REST/MQTT |
| **Application Layer** | `Unity/`, `web/index.html`         | Unity/Web apps consuming real-time predictions  |

---

## Data Processing and Preprocessing

Data processing involves a structured pipeline for EEG/fNIRS data, with a focus on extracting emotion-related features.

1. **Data Collection**
   - EEG and fNIRS data are collected using Lab Streaming Layer (LSL) and saved in `.xdf` format.
   - Event markers are embedded during specific phases (e.g., resting state, video stimulus) to label data segments.

2. **Data Preprocessing (`preprocess.py`)**
   - **Filtering:** 
     - Bandpass filter (0.5 - 45 Hz) to remove baseline drift and high-frequency noise.
   - **Artifact Removal:** 
     - Independent Component Analysis (ICA) to isolate and remove artifacts.
   - **Feature Extraction:**
     - Short-Time Fourier Transform (STFT) to generate time-frequency spectrograms.
     - Differential Entropy (DE) for frequency bands: delta, theta, alpha, beta, gamma.
     - Frontal Alpha Asymmetry (FAA) calculated as log ratio of left/right alpha power.

3. **Feature Structure:**
   - Spectrogram (3-channel, 224x224)
   - Differential Entropy (26-dimensional vector)

---

## Offline Training and Model Export

In the offline layer, the preprocessed data is used to train a regression model to predict **valence and arousal** scores.

1. **Model Architecture:**
   - Two-branch neural network:
     - **Spectrogram Branch:** Processes 3-channel spectrogram images.
     - **DE Branch:** Processes the 26-dimensional DE vector.

2. **Training Process (`train.py`):**
   - Input: Preprocessed EEG/fNIRS data.
   - Target: Valence and Arousal labels obtained through self-report or video stimuli.
   - Model Output: Continuous values for valence and arousal (range -1 to 1).

3. **Model Export:**
   - The trained PyTorch model is exported to ONNX format using the command:

     ```bash
     python train.py --input data/session.xdf --output models/va_regressor.onnx
     ```

---

## Online Inference and Streaming

The online layer serves as the real-time inference engine, which continuously processes incoming EEG data and pushes the predictions to the application layer.

1. **Data Acquisition (`lsl_receiver.py`):**
   - Listens for EEG/fNIRS streams via LSL.
   - Buffers data in a ring buffer for consistent data windows.

2. **Inference Pipeline (`main.py`):**
   - Loads the ONNX model using ONNX Runtime.
   - Applies the same preprocessing pipeline as the offline layer.
   - Extracts spectrogram and DE features from each data window.
   - Performs inference to predict valence and arousal.

3. **Data Push (`websocket_server.py`, `api_rest.py`, `mqtt_publisher.py`):**
   - WebSocket: Broadcasts JSON-encoded predictions in real time.
   - REST API: Provides the latest prediction on demand.
   - MQTT: Publishes predictions to the specified topic.

---

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/username/neurotech-agi.git
   cd neurotech-agi
   ```

2. **Install Python Dependencies:**

   ```bash
   conda create -n bci_env python=3.11
   conda activate bci_env
   pip install -r requirements.txt
   ```

3. **Open Unity Project:**
   - Open the project in Unity 2020.3 LTS or later.
   - Import the `LSL4Unity` package.
   - Assign the `BciWebSocketClient.cs` script to a GameObject.

4. **Build and Run:**
   - Run the server:

     ```bash
     python -m src.main
     ```

   - Open Unity, press **Play**, and monitor the console/logs for incoming data.

---

## Contributors

- **Yangyulin Ai, PhD(c)**
- **Gabriel Axel Montes, PhD**

---

## License


