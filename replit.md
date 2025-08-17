# BCI Emotional State Monitor

## Overview
This project is a real-time Brain-Computer Interface (BCI) application for emotion recognition. It processes EEG data to predict valence and arousal values, providing a robust solution for real-time emotional state monitoring. The system integrates a Python-based inference engine, a Node.js/Express backend for data management, and a React frontend for visualization and control. Its core capabilities include real-time processing of 62-channel EEG data, ONNX model predictions, and comprehensive emotion recognition training using full datasets. The project also incorporates Integrated Information Theory (IIT) Φ calculation for consciousness measurement, multi-device EEG support (Muse2, X.on, OpenBCI Cyton, Standard 10-20), and advanced feature extraction techniques. The business vision is to provide a deployable, scalable solution for real-time emotional and consciousness state monitoring, with potential applications in mental health, human-computer interaction, and neurofeedback.

## User Preferences
Preferred communication style: Simple, everyday language.
Documentation preference: English-only consolidated documentation.

## System Architecture

### Frontend Architecture
- **Framework**: React with TypeScript (Vite build tool)
- **UI Library**: Shadcn/ui components (Radix UI primitives)
- **Styling**: Tailwind CSS (dark theme, custom BCI color palette)
- **State Management**: React hooks with custom WebSocket hook
- **Routing**: Wouter for client-side routing
- **Data Fetching**: TanStack Query for API interactions

### Backend Architecture
- **Server**: Express.js with TypeScript, Helmet security middleware, rate limiting
- **Database**: PostgreSQL with Drizzle ORM
- **Real-time Communication**: WebSocket server with heartbeat monitoring
- **Session Management**: Express sessions with PostgreSQL store
- **Security**: Path traversal protection, request validation with Zod schemas, process management
- **Modular Design**: Separated concerns (analysis, validation, websocket) for maintainability

### Python Analysis Engine
- **Core Script**: `analyze_set_file_onnx.py` for SET file processing
- **ML Framework**: ONNX Runtime for emotion prediction inference
- **Signal Processing**: SciPy for filtering and feature extraction (`src/preprocess.py`)
- **Model**: CNN-TCN hybrid architecture (`model/va_regressor.onnx`)
- **Communication**: REST API integration with WebSocket broadcasting
- **Device Adaptation**: Multi-device support with automatic channel mapping and resampling
- **Enhanced Features**: Spatial structure preservation, parameterized FAA, differential entropy
- **IIT Integration**: Consciousness measurement via Integrated Information Theory Φ calculation

### System Design Choices
- **Data Processing Pipeline**:
    - **LSL Receiver**: Ingests real-time EEG data.
    - **Preprocessor**: Applies bandpass filtering and z-score normalization.
    - **Feature Extractor**: Generates spectrograms and differential entropy features.
    - **ONNX Runner**: Performs emotion recognition inference.
    - **Multi-channel Output**: Broadcasts results via WebSocket, MQTT, and REST API.
- **Training System**:
    - **Dataset Handlers**: Supports EEGLAB .set files with label management.
    - **Model Architecture**: CNN-TCN hybrid model (optional EfficientNet support).
    - **Training Pipeline**: Configurable with CCC/MSE/mixed loss functions, cross-validation (LOSO, K-fold), and model export.
    - **Data Organization**: Subject-based data structure with JSON label files.
    - **Performance Monitoring**: TensorBoard integration.
- **Data Flow**:
    - **Real-time Inference**: EEG data → LSL → Ring Buffer → Preprocessing → Feature Extraction → ONNX Model → Results Broadcasting.
    - **Training Data Flow**: Upload .set files → Subject organization → Label assignment → Feature extraction → Model training → ONNX export.
    - **Frontend Data Flow**: WebSocket connection → Real-time updates → State management → Component updates → Visualization.
    - **API Data Flow**: REST endpoints for model upload, training control, and data export; database storage for session and user data.
- **Deployment Strategy**:
    - **Development**: Vite (frontend), tsx (backend), direct Python execution, Drizzle migrations.
    - **Production**: Vite build (frontend), esbuild compilation (backend), standalone Python, environment-based DB connection.
    - **Configuration**: Environment variables, YAML files for Python inference parameters, separate configs for dev/prod.

## External Dependencies

### Python Dependencies
- **Signal Processing**: `scipy`, `numpy`, `mne`
- **Machine Learning**: `onnxruntime`, `torch`
- **Communication**: `pylsl`, `paho-mqtt`, `websockets`, `fastapi`
- **Data Handling**: `pandas`

### Node.js Dependencies
- **Database**: `@neondatabase/serverless`, `drizzle-orm`, `connect-pg-simple`
- **UI Framework**: `React`, `@radix-ui/components`, `tailwindcss`
- **Development**: `vite`, `typescript`, `tsx`
- **Communication**: `ws`

### External Services
- **Database**: Neon PostgreSQL
- **Real-time EEG Streaming**: Lab Streaming Layer (LSL)
- **Message Broker**: MQTT (optional)
- **EEG Hardware**: Muse2, X.on, OpenBCI Cyton, Standard 10-20 systems
- **Model Inference**: ONNX Runtime
- **Consciousness Measurement**: PyPhi (optional)

## Recent Updates (August 2025)

### Production-Ready Unified Analysis System with Real Φ Support (Latest)
- **Comprehensive File Format Support**: Tests/analyze_file_onnx.py now handles .set/.fif/.csv with epochs fallback, automatic sampling rate detection, and NaN/Inf cleaning
- **Enhanced Security Architecture**: Task mutex system prevents double-click analysis conflicts, unified file type whitelist across frontend/backend
- **GPU/CPU Dual Provider ONNX**: Automatic CUDA fallback with session optimization and provider configuration for maximum performance
- **Real-Time LSL Integration**: Multi-device EEG support (Muse2, X.on, OpenBCI) with auto-reconnection and 256Hz resampling for consistent processing
- **Production Validation Tools**: Complete dependency checking, system resource validation, and ONNX provider verification for deployment readiness
- **Sample Distribution System**: Static file serving for training data download and sharing via /samples endpoint
- **Real Φ Computation Support**: Enhanced PyPhi integration with requirements_phi.txt (numpy<1.23 compatibility), install_pyphi.py script, comprehensive IIT calculator (src/iit_phi_calculator.py), unified import strategy in tests/analyze_file_onnx.py prioritizing real Φ computation over enhanced simulation, Quick Test API using actual Φ computation instead of random demos, and automatic graceful fallback for stability

### Multi-Format EEG Support (Completed)
- **Multi-Format EEG Support**: Implemented unified file analysis system supporting SET (EEGLAB), FIF (MNE), and CSV formats with automatic format detection
- **Enhanced Upload System**: Updated file upload to accept .set, .fif, .csv, .npz, .edf, .txt files with 200MB limit for larger EEG datasets
- **Unified Analysis Pipeline**: Created tests/analyze_file_onnx.py script replacing analyze_set_file_onnx.py for seamless multi-format processing with MNE-Python integration
- **Frontend Multi-Format UI**: Updated interface to display file format badges and support all EEG formats in file selection dialogs
- **Production Environment Fixes**: Resolved missing ONNX Runtime dependency in production, added automatic dependency installation tools

### Unified EEG Analysis System & Production Readiness (Latest)
- **Unified File Analysis Script**: Replaced analyze_set_file_onnx.py with tests/analyze_file_onnx.py supporting .set/.fif/.csv formats with automatic detection
- **Multi-Format Upload System**: Enhanced frontend and backend to accept .set/.fif/.csv/.npz/.edf/.txt files with 200MB limit for larger datasets
- **Task Mutex System**: Implemented analysis locking with 10-minute timeout protection preventing concurrent analysis conflicts
- **Enhanced ONNX Runner**: Created src/onnx_runner.py with automatic GPU/CPU provider fallback and performance optimization
- **LSL Streaming Support**: Added src/stream_xon.py with auto-reconnection and resampling to 256Hz for real-time EEG devices
- **Production Dependencies**: Created requirements_prod.txt and tools/check_production.py for deployment validation and health checks
- **Unified Whitelist System**: Consistent file type validation across frontend (.set,.fif,.csv,.npz,.edf,.txt) and backend security
- **Sample Download Endpoint**: Added /samples static route for training data access and distribution

### Frontend Enhancement & Type Safety (January 2025)
- **Enhanced Type System**: Implemented type-safe BciMsg interface with shared types across client/server for consistency
- **Performance Optimization**: Added lodash throttling (100ms) for chart updates to prevent UI lag during real-time data streaming
- **Phi Control System**: Created comprehensive consciousness measurement controls with Off/Mock/IIT3.0/IIT4.0_light options
- **Analysis Mode Selection**: Implemented offline/live analysis mode selection with RadioGroup interface controls
- **Error Handling Enhancement**: Added 409 status handling with button disable states and user feedback for concurrent analysis prevention
- **Multi-Format Consistency**: Fixed upload/analysis type mismatches - standardized .set/.fif/.csv support across frontend and backend
- **Production Dependencies**: Enhanced install_production_deps.py and tools/check_production.py to include mne, pandas, pylsl for complete EEG support

### System Stability & Production Readiness (August 2025)
- **Analysis Mutex System**: Implemented process locking with 10-minute timeout protection in server/analysis.ts to prevent double-click conflicts
- **Enhanced Security**: Added Helmet middleware, stricter rate limiting (120/min), and comprehensive Zod validation with regex patterns and path traversal protection
- **WebSocket Heartbeat Monitoring**: Enhanced connection cleanup with 30-second ping/pong cycle to detect and terminate dead connections
- **GPU/CPU Dual Provider ONNX**: Enhanced ONNX Runtime with automatic CUDA/CPU fallback, provider configuration, and performance optimization
- **EMA Curve Smoothing**: Implemented exponential moving average (α=0.2) for valence/arousal/phi curves creating beautiful demo visuals
- **Chart Throttling**: Added 100ms throttled updates with data batching to prevent browser frame drops during real-time streaming
- **Enhanced Validation**: Strict filename validation with regex patterns, file extension verification, and parameter sanitization
- **Production Environment**: Created requirements_prod.txt, .env.example, and tools/check_production.py for deployment validation