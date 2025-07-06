# Neurotech Controls for AGI Motivational Framework

## Overview

This is a comprehensive EEG-based emotion prediction system that combines offline analysis with real-time monitoring capabilities. The system uses machine learning models to classify emotions from EEG signals and provides both a Streamlit web interface for data analysis and a real-time inference pipeline for live EEG data processing.

*Developed by Neural Axis*

## System Architecture

The system is a comprehensive EEG emotion prediction platform with the following components:

### Frontend Dashboard (React/TypeScript)
- **Location**: `client/` directory
- **Framework**: React with TypeScript, Vite, TailwindCSS
- **Features**: Real-time emotion visualization, data analysis controls, file upload interface
- **Communication**: WebSocket for real-time data, REST API for controls

### Backend Server (Node.js/Express)
- **Location**: `server/` directory
- **Framework**: Express.js with TypeScript
- **Features**: File upload, analysis control, WebSocket server, REST API endpoints
- **Database**: In-memory storage for session data

### Machine Learning Pipeline (Python)
- **Training**: `train/` directory - PyTorch CNN-TCN model training
- **Inference**: `src/` directory - ONNX runtime for real-time predictions
- **Analysis**: `analyze_set_file.py` - SET file processing and ML inference
- **Models**: `model/` directory - Trained ONNX models

## Key Components

### Data Processing (`utils/data_processor.py`)
- Handles multiple EEG file formats (CSV, EDF, TXT)
- Provides data loading and basic preprocessing capabilities
- Manages EEG channel mapping and sampling rate configuration

### Machine Learning Models (`utils/ml_models.py`)
- Implements multiple classification algorithms (Random Forest, SVM, MLP, Gradient Boosting)
- Provides emotion classification with labels: 快乐 (Happy), 悲伤 (Sad), 平静 (Calm), 焦虑 (Anxious)
- Includes model training, evaluation, and performance metrics

### Signal Processing (`utils/signal_processing.py`)
- Implements EEG signal preprocessing (bandpass filtering, notch filtering)
- Provides artifact removal and signal quality enhancement
- Supports configurable frequency bands and filtering parameters

### Visualization (`utils/visualization.py`)
- Creates interactive Plotly visualizations for EEG signals
- Provides multi-channel signal plotting and emotion classification results
- Supports real-time data visualization capabilities

### Real-time Processing Pipeline
- **LSL Receiver** (`src/lsl_receiver.py`): Captures live EEG data streams
- **ONNX Runner** (`src/onnx_runner.py`): Performs model inference using ONNX runtime
- **Preprocessor** (`src/preprocess.py`): Real-time signal filtering and feature extraction
- **Communication Layer**: WebSocket, MQTT, and REST API endpoints

## Data Flow

### Offline Analysis Flow
1. User uploads EEG data file via Streamlit interface
2. Data is processed and validated by EEGDataProcessor
3. Signal preprocessing applied (filtering, artifact removal)
4. Features extracted and emotion labels assigned
5. Machine learning model trained and evaluated
6. Results visualized through interactive plots

### Real-time Inference Flow
1. EEG data streamed via LSL protocol
2. Data buffered in ring buffer for windowed processing
3. Signal preprocessing applied (bandpass filtering, normalization)
4. Features extracted (spectrogram, differential entropy)
5. ONNX model performs emotion prediction
6. Results broadcast via WebSocket, MQTT, and REST API

## External Dependencies

### Core Libraries
- **Streamlit**: Web application framework for offline analysis
- **FastAPI**: REST API framework for real-time results
- **PyLSL**: Lab Streaming Layer for real-time data acquisition
- **ONNX Runtime**: Model inference engine
- **Plotly**: Interactive visualization library

### Data Processing
- **Pandas/NumPy**: Data manipulation and numerical computing
- **SciPy**: Signal processing algorithms
- **Scikit-learn**: Machine learning algorithms and utilities

### Communication
- **WebSockets**: Real-time bidirectional communication
- **Paho MQTT**: Message queuing telemetry transport
- **Uvicorn**: ASGI server for FastAPI

## Deployment Strategy

The system is designed for flexible deployment:

### Development Setup
- Streamlit app runs on default port for offline analysis
- FastAPI server on port 8000 for REST API
- WebSocket server for real-time communication
- MQTT broker integration for message distribution

### Production Considerations
- ONNX models enable cross-platform deployment
- Configurable sampling rates and processing parameters
- Scalable architecture supporting multiple concurrent users
- Thread-safe ring buffer for real-time data handling

## Changelog

- July 05, 2025: Initial setup
- July 05, 2025: Cleaned project structure and fixed WebSocket connectivity
  - Removed duplicate files and organized directories
  - Fixed frontend-backend WebSocket communication 
  - BCI client now correctly sends data to web frontend
  - System successfully displays real-time emotion data
- July 05, 2025: Created comprehensive English Home page
  - Built feature-rich landing page with navigation to dashboard
  - Added file upload functionality for ONNX models and data files
  - Implemented multer-based API endpoints for secure file uploads
  - Created intuitive UI with system status indicators
  - Added options for real-time device connection and configuration
- July 05, 2025: Resolved working directory issues
  - Moved web application files from web/ subdirectory to root directory
  - Fixed file upload paths to correctly point to model/ and data/ directories
  - Updated frontend workflow to run from root directory on port 5000
  - Eliminated TypeScript errors and simplified icon usage with emojis
  - Successfully restored system functionality with proper path configuration
- July 06, 2025: Implemented authentic NPZ data simulation
  - Replaced mock Dashboard with "Run Simulated Data" and "Real-time Device" features
  - Created NPZ data simulator that loads real valence/arousal from .npz files
  - Built file selection dialog showing all available NPZ files in data directory
  - Backend API integration to start authentic data simulation from selected files
  - System now uses actual emotion labels from NPZ 'y' data instead of random values
- July 06, 2025: Enhanced to true ML inference pipeline
  - Fixed TypeScript ES module syntax errors in backend API
  - Created npz_ml_simulator.py that uses actual ONNX model predictions
  - Implemented spectrogram resizing to match model input requirements (224x224)
  - Added proper data normalization using tanh function for realistic valence/arousal ranges
  - System now processes NPZ features (spec, de) through real ML model instead of reading labels directly
  - Successfully validated ML predictions showing diverse emotion values across different NPZ files
- July 06, 2025: Fixed SET file training issues and enhanced training system
  - Resolved PyTorch ReduceLROnPlateau 'verbose' parameter compatibility issue
  - Fixed .set file data loading by correcting MATLAB file structure parsing
  - Successfully created 342 training windows from 12 .set files with real-time feature extraction
  - Enhanced training API with intelligent script selection (train.py for NPZ, train_set.py for SET)
  - Added comprehensive training parameter support (batch size, learning rate, window size, overlap)
  - Implemented advanced training features: AdamW optimizer, learning rate scheduling, early stopping
- July 06, 2025: Fixed NPZ simulation data processing and model output normalization
  - Resolved issue where all ML predictions showed near-zero values (0.001, -0.001)
  - Fixed normalization algorithm: replaced division by 100 with multiplication by 2 for proper scaling
  - NPZ simulations now show diverse emotion values and complete quickly as expected
  - Enhanced simulation API to support both NPZ (ML inference) and SET (mock data) file types
  - Verified authentic ML pipeline: NPZ files -> ONNX model -> realistic valence/arousal predictions
- July 06, 2025: Removed all simulated/mock data, implemented real-data-only system
  - Completely deleted mock_bci_server.py and simulate_npz_data.py files
  - Removed BCI Client workflow that generated fake emotion data
  - Updated frontend to only support "Real Data Analysis" with NPZ files
  - Replaced /api/start-simulation with /api/start-analysis for authentic data processing
  - Added completion notifications: toast popup when NPZ analysis finishes
  - System now exclusively uses real EEG data with trained ML models, no simulation allowed
- July 06, 2025: Restructured training system with subject-based organization and real emotion labels
  - Implemented subject-folder structure: data/training set/s1/, s2/, etc.
  - Each subject folder contains .set files and required labels.json with valence/arousal annotations
  - Created train_labeled.py script that reads emotion labels from labels.json for supervised learning
  - Updated data upload API to automatically create subject folders (s1, s2, s3...) with default labels.json
  - Added /api/training-subjects endpoint to list available subjects with label validation
  - Training now uses authentic emotion labels instead of synthetic data for proper model learning
  - Enhanced SET file analysis with analyze_set_file.py for real EEG data processing
- July 06, 2025: Completely removed NPZ format support
  - Deleted npz_ml_simulator.py and all NPZ-related files
  - Removed all .npz files from data directory
  - Updated frontend to only support SET format files from subject folders
  - Modified /api/data-files to only return SET files from training subjects
  - Updated /api/start-analysis to only accept SET files for real data analysis
  - Removed train.py and dataset.py (NPZ training scripts)
  - System now exclusively supports SET format EEG data with subject-based organization
- July 06, 2025: Fixed WebSocket communication and completed system integration
  - Resolved issue where frontend couldn't receive ML predictions from analysis process
  - Modified analyze_set_file.py to use HTTP POST instead of direct WebSocket connection
  - Added /api/bci/broadcast endpoint for analysis scripts to send predictions to frontend
  - Fixed analysis timing from 0.5s to 2.5s intervals to match real EEG data windows
  - Successfully tested complete pipeline: SET files → ML inference → frontend display
  - Cleaned up project structure: removed duplicate web/ folder, backup files, cache files
  - System now works end-to-end with real predictions displayed on frontend dashboard
  - Created comprehensive deployment documentation with one-click setup scripts
  - Added cross-platform support: Linux/macOS shell scripts, Windows batch files, Docker
  - Built complete user manual (README.md) with detailed installation and usage instructions
- July 06, 2025: Unified port configuration and converted all interfaces to English
  - Changed all platforms to use port 5000 for consistency and Replit compatibility
  - Converted all Chinese interfaces, error messages, and documentation to English
  - Enhanced Python startup scripts with automatic dependency management and error handling
  - Fixed app crash issue by removing platform-specific port detection
  - Simplified deployment process with universal port configuration
- July 06, 2025: Updated system branding and naming
  - Changed system name to "Neurotech Controls for AGI Motivational Framework"
  - Updated company branding to "Neural Axis"
  - Modified all documentation, scripts, and frontend interfaces with new branding
  - Updated home page, startup scripts, and system headers across all platforms
- July 06, 2025: Fixed Windows startup dependency issue
  - Installed missing multer and @types/multer packages for file upload functionality
  - Resolved Windows Python startup error: ERR_MODULE_NOT_FOUND for multer package
  - Enhanced header layout with gradient brain icon and improved visual hierarchy
  - Simplified footer to show only copyright notice as requested

## User Preferences

Preferred communication style: Simple, everyday language.