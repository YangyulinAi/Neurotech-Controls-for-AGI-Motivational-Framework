import type { Express } from "express";
import { createServer, type Server } from "http";
import { WebSocketServer, WebSocket } from "ws";
import { storage } from "./storage";
import { insertBciDataSchema } from "@shared/schema";
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';

// ES module __dirname equivalent
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Unified file type whitelist - consistent with frontend (enhanced for multi-format support)
const allowedExt = new Set([".set", ".fif", ".csv", ".npz", ".edf", ".txt"]);

// Configure multer for file uploads with enhanced security
const modelStorage = multer.diskStorage({
  destination: (req, file, cb) => {
    const modelDir = path.resolve('./model/model_onnx');
    if (!fs.existsSync(modelDir)) {
      fs.mkdirSync(modelDir, { recursive: true });
    }
    cb(null, modelDir);
  },
  filename: (req, file, cb) => {
    // Replace the existing model with the uploaded one
    cb(null, 'va_regressor.onnx');
  }
});

const dataStorage = multer.diskStorage({
  destination: (req, file, cb) => {
    // Find the next available subject folder
    const trainingDir = path.resolve('./data/training set');
    if (!fs.existsSync(trainingDir)) {
      fs.mkdirSync(trainingDir, { recursive: true });
    }
    
    // Find highest existing subject number
    const subjects = fs.readdirSync(trainingDir)
      .filter(dir => fs.statSync(path.join(trainingDir, dir)).isDirectory())
      .filter(dir => /^s\d+$/.test(dir))
      .map(dir => parseInt(dir.substring(1)))
      .filter(num => !isNaN(num));
    
    const nextSubjectNum = subjects.length > 0 ? Math.max(...subjects) + 1 : 1;
    const subjectDir = path.join(trainingDir, `s${nextSubjectNum}`);
    
    if (!fs.existsSync(subjectDir)) {
      fs.mkdirSync(subjectDir, { recursive: true });
    }
    
    cb(null, subjectDir);
  },
  filename: (req, file, cb) => {
    // Keep original filename
    cb(null, file.originalname);
  }
});

const uploadModel = multer({ 
  storage: modelStorage,
  fileFilter: (req, file, cb) => {
    if (file.originalname.endsWith('.onnx')) {
      cb(null, true);
    } else {
      cb(new Error('Only ONNX files are allowed') as any, false);
    }
  }
});

// Enhanced upload configuration with unified whitelist and security
const uploadData = multer({ 
  storage: dataStorage,
  limits: { 
    fileSize: 200 * 1024 * 1024, // 200MB limit for large EEG datasets
    files: 10 // Maximum 10 files per upload
  },
  fileFilter: (req, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase();
    if (!allowedExt.has(ext)) {
      return cb(new Error("Unsupported file type") as any, false);
    }
    if (file.originalname.includes("..") || file.originalname.includes("/")) {
      return cb(new Error("Bad filename") as any, false);
    }
    cb(null, true);
  }
});

export async function registerRoutes(app: Express): Promise<Server> {
  // File upload routes
  app.post("/api/upload-model", uploadModel.single('model'), (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({ error: "No file uploaded" });
      }
      
      console.log(`Model uploaded: ${req.file.filename}`);
      res.json({ 
        message: "Model uploaded successfully",
        filename: req.file.filename,
        path: req.file.path
      });
    } catch (error) {
      console.error("Model upload error:", error);
      res.status(500).json({ error: "Failed to upload model" });
    }
  });

  app.post("/api/upload-data", uploadData.array('data'), (req, res) => {
    try {
      if (!req.files || req.files.length === 0) {
        return res.status(400).json({ error: "No files uploaded" });
      }
      
      const uploadedFiles = req.files.map((file: any) => ({
        filename: file.filename,
        originalname: file.originalname,
        path: file.path
      }));
      
      // Get the subject directory from the first uploaded file
      const firstFilePath = uploadedFiles[0].path;
      const subjectDir = path.dirname(firstFilePath);
      const subjectName = path.basename(subjectDir);
      
      // Create a default labels.json file if it doesn't exist
      const labelsPath = path.join(subjectDir, 'labels.json');
      if (!fs.existsSync(labelsPath)) {
        const defaultLabels = {
          subject_id: subjectName,
          description: `EEG data for ${subjectName} - emotion recognition experiment`,
          label_type: "continuous",
          valence_range: [-1, 1],
          arousal_range: [-1, 1],
          files: {}
        };
        
        // Add default labels for each uploaded file
        uploadedFiles.forEach((file, index) => {
          defaultLabels.files[file.filename] = {
            valence: Math.random() * 2 - 1, // Random between -1 and 1
            arousal: Math.random() * 2 - 1,
            emotion: "unknown",
            duration_seconds: 0 // Will be updated when analyzed
          };
        });
        
        fs.writeFileSync(labelsPath, JSON.stringify(defaultLabels, null, 2));
        console.log(`Created default labels.json for ${subjectName}`);
      }
      
      console.log(`Data files uploaded to ${subjectName}: ${uploadedFiles.length} files`);
      res.json({ 
        message: `${uploadedFiles.length} data files uploaded successfully to ${subjectName}`,
        subject: subjectName,
        files: uploadedFiles
      });
    } catch (error) {
      console.error("Data upload error:", error);
      res.status(500).json({ error: "Failed to upload data files" });
    }
  });

  // Get list of data files (NPZ and subject folders)
  app.get('/api/data-files', (req, res) => {
    try {
      const { type = 'all' } = req.query;
      let files: string[] = [];
      
      // Support multiple EEG formats: SET, FIF, CSV
      
      // Include subject folders for EEG files
      {
        const trainingDir = path.resolve('./data/training set');
        if (fs.existsSync(trainingDir)) {
          const subjectDirs = fs.readdirSync(trainingDir)
            .filter(dir => {
              const fullPath = path.join(trainingDir, dir);
              return fs.statSync(fullPath).isDirectory() && /^s\d+$/.test(dir);
            })
            .sort((a, b) => {
              const numA = parseInt(a.substring(1));
              const numB = parseInt(b.substring(1));
              return numA - numB;
            });
          
          // For each subject directory, get all supported EEG files
          subjectDirs.forEach(subjectDir => {
            const subjectPath = path.join(trainingDir, subjectDir);
            const eegFiles = fs.readdirSync(subjectPath)
              .filter(file => ['.set', '.fif', '.csv'].includes(path.extname(file).toLowerCase()))
              .map(file => `set/${subjectDir}/${file}`);
            files = files.concat(eegFiles);
          });
        }
      }
      
      res.json(files);
    } catch (error) {
      res.status(500).json({ error: 'Failed to read data directory' });
    }
  });

  // Get list of subjects for training
  app.get('/api/training-subjects', (req, res) => {
    try {
      const trainingDir = path.resolve('./data/training set');
      if (!fs.existsSync(trainingDir)) {
        return res.json([]);
      }
      
      const subjects = fs.readdirSync(trainingDir)
        .filter(dir => {
          const fullPath = path.join(trainingDir, dir);
          return fs.statSync(fullPath).isDirectory() && /^s\d+$/.test(dir);
        })
        .map(subjectDir => {
          const subjectPath = path.join(trainingDir, subjectDir);
          const labelsPath = path.join(subjectPath, 'labels.json');
          
          let hasLabels = false;
          let fileCount = 0;
          
          if (fs.existsSync(labelsPath)) {
            hasLabels = true;
          }
          
          fileCount = fs.readdirSync(subjectPath)
            .filter(file => ['.set', '.fif', '.csv'].includes(path.extname(file).toLowerCase())).length;
          
          return {
            id: subjectDir,
            name: subjectDir,
            hasLabels,
            fileCount,
            path: subjectPath
          };
        })
        .sort((a, b) => {
          const numA = parseInt(a.id.substring(1));
          const numB = parseInt(b.id.substring(1));
          return numA - numB;
        });
      
      res.json(subjects);
    } catch (error) {
      res.status(500).json({ error: 'Failed to read training subjects' });
    }
  });

  // REMOVED: Old duplicate start-analysis endpoint with incorrect path validation

  // Production environment diagnostic endpoints
  app.get('/api/diagnostic/production-check', (req, res) => {
    try {
      const diagnosticPath = path.resolve('./scripts/tools/check_production.py');
      
      if (!fs.existsSync(diagnosticPath)) {
        return res.status(404).json({ error: 'Production check script not found' });
      }

      console.log('Running production environment diagnostic...');
      
      const diagnosticProcess = spawn('python3', [diagnosticPath], {
        stdio: ['pipe', 'pipe', 'pipe'],
        env: { ...process.env, PYTHONPATH: process.cwd() }
      });

      let output = '';
      let errorOutput = '';

      diagnosticProcess.stdout?.on('data', (data) => {
        output += data.toString();
      });

      diagnosticProcess.stderr?.on('data', (data) => {
        errorOutput += data.toString();
      });

      diagnosticProcess.on('close', (code) => {
        res.json({
          success: code === 0,
          exitCode: code,
          output: output,
          errors: errorOutput,
          timestamp: new Date().toISOString()
        });
      });

      diagnosticProcess.on('error', (error) => {
        res.status(500).json({ 
          error: 'Failed to run production check', 
          details: error.message 
        });
      });

    } catch (error) {
      console.error('Production check error:', error);
      res.status(500).json({ error: 'Failed to start production check' });
    }
  });

  app.get('/api/diagnostic/backend-test', (req, res) => {
    try {
      const testPath = path.resolve('./scripts/tools/test_backend.py');
      
      if (!fs.existsSync(testPath)) {
        return res.status(404).json({ error: 'Backend test script not found' });
      }

      console.log('Running backend functionality test...');
      
      const testProcess = spawn('python3', [testPath], {
        stdio: ['pipe', 'pipe', 'pipe'],
        env: { ...process.env, PYTHONPATH: process.cwd() }
      });

      let output = '';
      let errorOutput = '';

      testProcess.stdout?.on('data', (data) => {
        output += data.toString();
      });

      testProcess.stderr?.on('data', (data) => {
        errorOutput += data.toString();
      });

      testProcess.on('close', (code) => {
        res.json({
          success: code === 0,
          exitCode: code,
          output: output,
          errors: errorOutput,
          timestamp: new Date().toISOString()
        });
      });

      testProcess.on('error', (error) => {
        res.status(500).json({ 
          error: 'Failed to run backend test', 
          details: error.message 
        });
      });

    } catch (error) {
      console.error('Backend test error:', error);
      res.status(500).json({ error: 'Failed to start backend test' });
    }
  });

  // Test Φ calculation endpoint
  app.post('/api/test-phi', async (req, res) => {
    try {
      const { method = 'mock', maxChannels = 8, testSamples = 4 } = req.body;
      
      console.log('Starting Φ test: method=' + method + ', channels=' + maxChannels + ', samples=' + testSamples);
      
      // Check if phi_estimator.py exists
      const testPath = path.resolve('./scripts/phi_estimator.py');
      
      if (!fs.existsSync(testPath)) {
        console.log('Φ estimator not found at:', testPath);
        return res.status(404).json({ error: 'Φ estimator not found at ' + testPath });
      }

      // Create a simple test script file
      const testScript = `
import sys
import os
import numpy as np

# Add scripts directory to path
sys.path.insert(0, '${path.resolve('./scripts').replace(/\\/g, '/')}')

# Enhanced Φ import strategy: prioritize real Φ (PyPhi), fallback to enhanced simulation
try:
    from phi_estimator import PhiEstimator as _PhiEstimator  # Real Φ (PyPhi)
    _HAVE_REAL = True
    print("[PHI] Real PyPhi-based Φ estimator loaded for testing")
except Exception as e:
    from phi_estimator_enhanced import PhiEstimatorEnhanced as _PhiEstimator  # Approximated Φ
    _HAVE_REAL = False
    print(f"[PHI] PyPhi not available ({e}), using enhanced simulation for testing")

try:
    # Initialize estimator with unified interface
    if _HAVE_REAL:
        estimator = _PhiEstimator(method='${method}', max_channels=${maxChannels})
    else:
        estimator = _PhiEstimator(method='${method}', alpha=0.2)  # EMA smoothing for enhanced
    
    # Get estimator info
    info = getattr(estimator, "get_info", lambda: {"available": _HAVE_REAL, "backend_ready": _HAVE_REAL})()
    print(f"[PHI] backend_ready={info.get('backend_ready', _HAVE_REAL)}, method=${method}")
    
    # Generate ${testSamples} test samples with realistic EEG patterns
    phi_values = []
    for i in range(${testSamples}):
        # Simulate realistic EEG data: ${maxChannels} channels × 256 samples (1 second at 256Hz)
        # Add realistic EEG frequency components (alpha, beta, theta)
        t = np.linspace(0, 1, 256)
        alpha_wave = 0.5 * np.sin(2 * np.pi * 10 * t)  # 10Hz alpha
        beta_wave = 0.3 * np.sin(2 * np.pi * 20 * t)   # 20Hz beta
        theta_wave = 0.2 * np.sin(2 * np.pi * 6 * t)   # 6Hz theta
        
        test_data = np.zeros((${maxChannels}, 256))
        for ch in range(${maxChannels}):
            # Each channel gets slightly different phase and amplitude
            phase_shift = ch * 0.1
            test_data[ch] = (alpha_wave + beta_wave + theta_wave) * (0.8 + 0.4 * np.random.rand()) + \\
                           0.1 * np.random.randn(256) + phase_shift
        
        # Compute Φ with real calculation (not random demo values)
        if _HAVE_REAL:
            # Real Φ estimator - actual PyPhi computation
            phi_val = float(estimator.estimate_phi(test_data))
        else:
            # Enhanced estimator - sophisticated simulation
            result = estimator.estimate_phi(test_data, 256)
            phi_val = result["phi"] if isinstance(result, dict) else result
        
        phi_values.append(float(phi_val))
        print(f"Test {i+1}: Φ = {phi_val:.6f}")
    
    avg_phi = np.mean(phi_values)
    min_phi = np.min(phi_values)
    max_phi = np.max(phi_values)
    
    print(f"Average Φ: {avg_phi:.6f}")
    print(f"Min Φ: {min_phi:.6f}")
    print(f"Max Φ: {max_phi:.6f}")
    print(f"METHOD: ${method}")
    print(f"SAMPLES: ${testSamples}")
    print(f"ESTIMATOR_INFO: {info}")
    
except Exception as e:
    print(f"ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
`;

      const testProcess = spawn('python3', ['-c', testScript], {
        stdio: ['pipe', 'pipe', 'pipe'],
        env: { 
          ...process.env, 
          PYTHONPATH: path.resolve('./scripts')
        }
      });

      let output = '';
      let errorOutput = '';

      testProcess.stdout?.on('data', (data) => {
        output += data.toString();
      });

      testProcess.stderr?.on('data', (data) => {
        errorOutput += data.toString();
      });

      testProcess.on('close', (code) => {
        console.log(`Φ test process exited with code ${code}`);
        console.log('Output:', output);
        if (errorOutput) console.log('Errors:', errorOutput);
        
        if (code === 0 && !output.includes('ERROR:')) {
          // Parse results from output
          const avgMatch = output.match(/Average Φ: ([\d.]+)/);
          const minMatch = output.match(/Min Φ: ([\d.]+)/);
          const maxMatch = output.match(/Max Φ: ([\d.]+)/);
          const infoMatch = output.match(/ESTIMATOR_INFO: ({.*})/);
          
          const avgPhi = avgMatch ? parseFloat(avgMatch[1]) : 0;
          const minPhi = minMatch ? parseFloat(minMatch[1]) : 0;
          const maxPhi = maxMatch ? parseFloat(maxMatch[1]) : 0;
          
          let estimatorInfo = {};
          if (infoMatch) {
            try {
              estimatorInfo = JSON.parse(infoMatch[1].replace(/'/g, '"'));
            } catch (e) {
              console.log('Failed to parse estimator info:', e);
            }
          }
          
          // Extract phi values from output
          const phiMatches = output.match(/Test \d+: Φ = ([\d.]+)/g);
          const phiValues = phiMatches ? phiMatches.map(match => parseFloat(match.match(/([\d.]+)/)[1])) : [];
          
          res.json({
            success: true,
            method: method,
            maxChannels: maxChannels,
            testSamples: testSamples,
            phiValues: phiValues,
            avgPhi: avgPhi,
            minPhi: minPhi,
            maxPhi: maxPhi,
            estimatorInfo: estimatorInfo,
            output: output,
            timestamp: new Date().toISOString()
          });
        } else {
          res.status(500).json({
            error: 'Φ test failed',
            exitCode: code,
            output: output,
            errors: errorOutput,
            details: 'Python process failed or returned error'
          });
        }
      });

      testProcess.on('error', (error) => {
        console.log('Φ test process error:', error);
        res.status(500).json({ 
          error: 'Failed to run Φ test', 
          details: error.message,
          pythonPath: 'python3'
        });
      });

    } catch (error) {
      console.error('Φ test error:', error);
      res.status(500).json({ 
        error: 'Failed to start Φ test',
        details: error.message
      });
    }
  });

  // Analysis mutex system for preventing concurrent analysis
  let ANALYSIS_RUNNING = false;

  // Start analysis endpoint with mode support (offline/live)
  app.post('/api/start-analysis', async (req, res) => {
    try {
      const { filename, computePhi, phiMethod, outputInterval, mode } = req.body ?? {};
      
      // Mutex protection - prevent concurrent analysis
      if (ANALYSIS_RUNNING) {
        return res.status(409).json({ 
          error: "Analysis already running",
          message: "Please wait for current analysis to complete"
        });
      }

      // Phi method whitelist fallback
      const allowedPhi = new Set(["mock", "IIT3.0", "IIT4.0_light"]);
      const safePhi = allowedPhi.has(phiMethod) ? phiMethod : "mock";
      
      console.log('=== Server Analysis Request Debug ===');
      console.log('Analysis mode:', mode);
      console.log('Request body full:', req.body);
      console.log('Server environment:', {
        NODE_ENV: process.env.NODE_ENV,
        CWD: process.cwd(),
        PYTHONPATH: process.env.PYTHONPATH
      });

      // Set analysis running flag
      ANALYSIS_RUNNING = true;
      
      let args: string[] = [];
      
      // Choose script based on analysis mode
      if (mode === "live") {
        // Real-time EEG device connection
        console.log('Starting live EEG device analysis...');
        args = ["scripts/main.py"];
        
        // For live mode, we don't need a filename - it connects to EEG devices via LSL
        if (computePhi) {
          // Pass phi options via environment variables for main.py
          process.env.COMPUTE_PHI = "true";
          process.env.PHI_METHOD = safePhi;
        }
      } else {
        // Offline file analysis mode
        if (!filename) {
          ANALYSIS_RUNNING = false;
          return res.status(400).json({ error: "Missing filename for offline analysis" });
        }

        console.log('Starting offline file analysis for:', filename);
        
        // Simplified path resolution for training data
        const analysisFilename = path.join(__dirname, "../data/training set", filename.replace('set/', ''));
        
        if (!fs.existsSync(analysisFilename)) {
          ANALYSIS_RUNNING = false;
          return res.status(404).json({ 
            error: "Data file not found: " + analysisFilename 
          });
        }

        args = ["scripts/tests/analyze_file_onnx.py", analysisFilename];
        if (computePhi) {
          args.push("--compute_phi", "--phi_method", safePhi);
        }
        
        // Add output interval if specified (default to 0.1s for real-time feel)
        const interval = outputInterval && outputInterval > 0 ? outputInterval : 0.1;
        args.push("--output_interval", interval.toString());
      }

      // Spawn Python analysis process
      const py = spawn(process.env.PYTHON || "python", args, { 
        env: process.env,
        stdio: ['pipe', 'pipe', 'pipe']
      });
      
      // 10-minute timeout protection
      const killTimer = setTimeout(() => { 
        try { 
          py.kill("SIGKILL"); 
          console.log("Analysis killed due to timeout");
        } catch {} 
      }, 10 * 60 * 1000);

      // Process output handling
      py.stdout.on("data", (data) => {
        const output = data.toString().trim();
        console.log("[ANALYSIS-OUT]", output);
      });
      
      py.stderr.on("data", (data) => {
        const error = data.toString().trim();
        console.error("[ANALYSIS-ERR]", error);
      });
      
      py.on("close", (code) => { 
        clearTimeout(killTimer); 
        ANALYSIS_RUNNING = false; 
        console.log("Analysis process exited with code:", code);
      });

      return res.json({ 
        success: true,
        message: "Analysis started successfully",
        pid: py.pid,
        args: args
      });

    } catch (error: any) {
      ANALYSIS_RUNNING = false;
      console.error('Failed to start analysis:', error);
      res.status(500).json({ 
        error: 'Failed to start analysis: ' + (error?.message || "Unknown error")
      });
    }
  });

  // Add analysis status and control endpoints
  app.get('/api/analysis/status', async (req, res) => {
    const { getAnalysisStatus } = await import('./analysis');
    return getAnalysisStatus(res);
  });

  app.post('/api/analysis/stop', async (req, res) => {
    const { stopAnalysis } = await import('./analysis');
    return stopAnalysis(res);
  });

  // Endpoint for analysis scripts to broadcast WebSocket messages
  app.post("/api/bci/broadcast", async (req, res) => {
    try {
      const message = req.body;
      
      // Enhanced debug logging for production troubleshooting
      console.log('=== Server Broadcast Debug ===');
      console.log('Received broadcast message:', JSON.stringify(message, null, 2));
      console.log('Message timestamp:', new Date().toISOString());
      
      // Validate the message contains required fields for BCI data OR training progress
      const isBciData = typeof message.valence === 'number' && typeof message.arousal === 'number';
      const isTrainingProgress = message.type === 'training_progress' && typeof message.epoch === 'number';
      const isAnalysisComplete = message.type === 'analysis_complete';
      
      console.log('Broadcast message validation:', { isBciData, isTrainingProgress, isAnalysisComplete, messageType: message.type });
      
      if (!isBciData && !isTrainingProgress && !isAnalysisComplete) {
        console.log('Invalid message format:', message);
        return res.status(400).json({ error: "Invalid message format" });
      }
      
      // Broadcast to all connected WebSocket clients directly
      let successCount = 0;
      let failCount = 0;
      
      wss.clients.forEach((client: ExtendedWebSocket) => {
        if (client.readyState === WebSocket.OPEN) {
          try {
            client.send(JSON.stringify(message));
            successCount++;
          } catch (error) {
            console.error('Failed to send to WebSocket client:', error);
            failCount++;
          }
        }
      });
      
      const broadcastResult = {
        success: true,
        clientCount: wss.clients.size,
        successCount,
        failCount
      };
      
      console.log('Broadcast summary:', `${broadcastResult.successCount} successful, ${broadcastResult.failCount} failed`);
      
      res.json({ 
        success: true, 
        message: "Message broadcasted",
        clientCount: broadcastResult.clientCount,
        successCount: broadcastResult.successCount,
        failCount: broadcastResult.failCount
      });
    } catch (error) {
      console.error('Broadcast error:', error);
      res.status(500).json({ error: "Failed to broadcast message" });
    }
  });

  // API routes
  app.get("/api/bci/recent/:minutes", async (req, res) => {
    try {
      const minutes = parseInt(req.params.minutes) || 30;
      const data = await storage.getRecentBciData(minutes);
      res.json(data);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch BCI data" });
    }
  });

  app.get("/api/bci/session/:sessionId", async (req, res) => {
    try {
      const sessionId = req.params.sessionId;
      const data = await storage.getBciDataBySession(sessionId);
      res.json(data);
    } catch (error) {
      res.status(500).json({ error: "Failed to fetch session data" });
    }
  });

  // Training API routes
  let trainingStatus = {
    isTraining: false,
    progress: 0,
    completed: false,
    bestLoss: null as number | null,
    error: null as string | null
  };

  app.post("/api/train-model", async (req, res) => {
    try {
      const { 
        dataFiles, 
        epochs, 
        datasetType = 'set',
        batchSize = 16,
        learningRate = 0.0001,
        windowSize = 5.0,
        overlap = 0.5
      } = req.body;
      
      if (!dataFiles || !Array.isArray(dataFiles) || dataFiles.length === 0) {
        return res.status(400).json({ error: 'Data files are required' });
      }

      if (trainingStatus.isTraining) {
        return res.status(400).json({ error: 'Training is already in progress' });
      }

      // Reset training status
      trainingStatus = {
        isTraining: true,
        progress: 0,
        completed: false,
        bestLoss: null,
        error: null
      };

      console.log(`Starting model training with ${dataFiles.length} files...`);
      console.log(`Dataset type: ${datasetType}, Batch size: ${batchSize}, LR: ${learningRate}`);

      // Use the new labeled training script for subject-based training
      const trainingScript = 'scripts/train/train_labeled.py';
      
      // Build training arguments
      const trainingArgs = [
        trainingScript,
        '--data_dir', 'data/training set',
        '--epochs', epochs.toString(),
        '--batch_size', batchSize.toString(),
        '--lr', learningRate.toString(),
        '--window_size', windowSize.toString(),
        '--overlap', overlap.toString()
      ];

      // Start training process in background
      const trainingProcess = spawn('python', trainingArgs, {
        stdio: 'pipe',
        detached: false
      });

      // Monitor training progress
      trainingProcess.stdout?.on('data', (data) => {
        const output = data.toString();
        console.log('Training output:', output);
        
        // Parse progress from output (e.g., "E5/30 loss=0.1234" or "E5/30 Batch 10/86 loss=0.1234")
        const progressMatch = output.match(/E(\d+)\/(\d+)/);
        if (progressMatch) {
          const currentEpoch = parseInt(progressMatch[1]);
          const totalEpochs = parseInt(progressMatch[2]);
          const calculatedProgress = (currentEpoch / totalEpochs) * 100;
          trainingStatus.progress = Math.round(calculatedProgress * 100) / 100; // Round to 2 decimal places
          console.log(`Progress updated: ${currentEpoch}/${totalEpochs} = ${trainingStatus.progress}%`);
        }

        // Parse loss from output (handles both "loss=0.1234" and "loss=0.1234 time=14.8s")
        const lossMatch = output.match(/loss=([\d.]+)/);
        if (lossMatch) {
          const currentLoss = parseFloat(lossMatch[1]);
          // Only update best loss if it's better (lower)
          if (trainingStatus.bestLoss === null || currentLoss < trainingStatus.bestLoss) {
            trainingStatus.bestLoss = currentLoss;
            console.log(`Best loss updated: ${trainingStatus.bestLoss}`);
          }
        }

        // Parse completion status
        if (output.includes('Training completed') || output.includes('ONNX exported')) {
          trainingStatus.progress = 100;
          console.log('Training completion detected, progress set to 100%');
        }
      });

      trainingProcess.stderr?.on('data', (data) => {
        console.error('Training error:', data.toString());
        trainingStatus.error = data.toString();
      });

      trainingProcess.on('close', async (code) => {
        console.log(`Training process exited with code ${code}`);
        
        if (code === 0) {
          // Check if ONNX model was already exported by training script
          const modelPath = 'model/model_onnx/va_regressor.onnx';
          const trainModelPath = 'model/model_onnx/va_regressor_temp.onnx';
          
          if (fs.existsSync(trainModelPath)) {
            // Training script already exported the model, just copy it to the correct location
            console.log('ONNX model already exported by training script, deploying...');
            try {
              // Backup old model if it exists
              const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
              const backupName = `va_regressor_backup_${timestamp}.onnx`;
              
              if (fs.existsSync(modelPath)) {
                fs.renameSync(modelPath, `model/model_onnx/${backupName}`);
                console.log(`Old model backed up as ${backupName}`);
              }
              
              // Copy new model from training directory
              fs.copyFileSync(trainModelPath, modelPath);
              console.log('New model deployed successfully from training script output');
              
              trainingStatus.completed = true;
              trainingStatus.isTraining = false;
              trainingStatus.progress = 100;
              trainingStatus.error = null;
              
            } catch (error) {
              console.error('Error deploying new model:', error);
              trainingStatus.error = `Failed to deploy new model: ${error}`;
              trainingStatus.isTraining = false;
            }
          } else {
            // Training script didn't export, try separate export process
            console.log('Training script did not export ONNX, running separate export...');
            const exportProcess = spawn('python', [
              'scripts/tools/export_onnx.py',
              '--ckpt', 'model/model_weight/ckpt.pt',
              '--out', 'model/model_onnx/va_regressor_new.onnx'
            ], {
              stdio: 'pipe',
              detached: false
            });

            exportProcess.on('close', async (exportCode) => {
              if (exportCode === 0) {
                // Backup old model and replace with new one
              try {
                const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                const backupName = `va_regressor_backup_${timestamp}.onnx`;
                
                // Backup old model
                if (fs.existsSync('model/model_onnx/va_regressor.onnx')) {
                  fs.renameSync('model/model_onnx/va_regressor.onnx', `model/model_onnx/${backupName}`);
                  console.log(`Old model backed up as ${backupName}`);
                }
                
                // Replace with new model
                fs.renameSync('model/model_onnx/va_regressor_new.onnx', 'model/model_onnx/va_regressor.onnx');
                console.log('New model deployed successfully');
                
                trainingStatus.completed = true;
                trainingStatus.isTraining = false;
                trainingStatus.progress = 100;
              } catch (error) {
                console.error('Error deploying new model:', error);
                trainingStatus.error = `Failed to deploy new model: ${error}`;
                trainingStatus.isTraining = false;
              }
            } else {
              trainingStatus.error = 'Failed to export model to ONNX';
              trainingStatus.isTraining = false;
            }
            });
          }
        } else {
          trainingStatus.error = `Training failed with exit code ${code}`;
          trainingStatus.isTraining = false;
        }
      });

      res.json({ 
        message: 'Training started successfully',
        dataFiles: dataFiles,
        epochs: epochs,
        datasetType: datasetType,
        batchSize: batchSize,
        learningRate: learningRate,
        status: 'running'
      });

    } catch (error) {
      console.error('Training start error:', error);
      trainingStatus.error = `Failed to start training: ${error}`;
      trainingStatus.isTraining = false;
      res.status(500).json({ error: 'Failed to start training' });
    }
  });

  app.get("/api/training-status", async (req, res) => {
    res.json(trainingStatus);
  });

  const httpServer = createServer(app);

  // WebSocket server for real-time BCI data with heartbeat monitoring
  const wss = new WebSocketServer({ server: httpServer, path: '/ws' });

  interface ExtendedWebSocket extends WebSocket {
    isAlive?: boolean;
  }

  wss.on('connection', (ws: ExtendedWebSocket) => {
    console.log('BCI WebSocket client connected');
    ws.isAlive = true;

    // Send welcome message
    ws.send(JSON.stringify({
      type: 'connection',
      message: 'Connected to BCI data stream',
      timestamp: new Date().toISOString()
    }));

    // Production environment ready for analysis

    // Ready to receive real BCI data from your local project

    ws.on('message', (message: Buffer) => {
      try {
        const data = JSON.parse(message.toString());
        
        // Validate incoming BCI data
        if (data.type === 'bci_data') {
          const validatedData = insertBciDataSchema.parse(data.payload);
          
          // Save to storage
          storage.saveBciData(validatedData);
          
          // Broadcast to all connected clients
          wss.clients.forEach((client) => {
            if (client.readyState === WebSocket.OPEN) {
              client.send(JSON.stringify({
                valence: validatedData.valence,
                arousal: validatedData.arousal,
                timestamp: new Date().toISOString()
              }));
            }
          });
        }
      } catch (error) {
        console.error('Invalid WebSocket message:', error);
        ws.send(JSON.stringify({
          type: 'error',
          message: 'Invalid data format',
          timestamp: new Date().toISOString()
        }));
      }
    });

    // Handle pong responses for heartbeat
    ws.on('pong', () => {
      ws.isAlive = true;
    });

    ws.on('close', () => {
      console.log('BCI WebSocket client disconnected');
    });

    ws.on('error', (error) => {
      console.error('WebSocket error:', error);
    });
  });

  // Heartbeat mechanism to detect dead connections
  const heartbeatInterval = setInterval(() => {
    wss.clients.forEach((ws: ExtendedWebSocket) => {
      if (!ws.isAlive) {
        console.log('Terminating dead WebSocket connection');
        return ws.terminate();
      }
      
      ws.isAlive = false;
      ws.ping();
    });
  }, 30000); // 30 seconds

  // Cleanup on server close
  wss.on('close', () => {
    clearInterval(heartbeatInterval);
  });

  console.log('WebSocket server initialized with heartbeat monitoring');

  // Install production dependencies API
  app.post('/api/install-production-deps', async (req, res) => {
    try {
      console.log('Installing production dependencies...');
      
      const installProcess = spawn('python3', ['install_production_deps.py'], {
        stdio: ['pipe', 'pipe', 'pipe'],
        env: { 
          ...process.env, 
          PYTHONPATH: process.cwd()
        }
      });

      let output = '';
      let errorOutput = '';

      installProcess.stdout?.on('data', (data) => {
        output += data.toString();
        console.log('Install output:', data.toString());
      });

      installProcess.stderr?.on('data', (data) => {
        errorOutput += data.toString();
        console.log('Install error:', data.toString());
      });

      installProcess.on('close', (code) => {
        console.log('Installation completed with code:', code);
        res.json({
          success: code === 0,
          output: output,
          error: errorOutput,
          exitCode: code
        });
      });

      installProcess.on('error', (error) => {
        res.status(500).json({
          success: false,
          error: `Failed to run installation: ${error.message}`
        });
      });

    } catch (error) {
      res.status(500).json({
        success: false,
        error: `Installation failed: ${error.message}`
      });
    }
  });

  // Production environment debug API
  app.post('/api/debug-production', async (req, res) => {
    try {
      console.log('Running production environment debug test...');
      
      const debugProcess = spawn('python3', ['debug_production_analysis.py'], {
        stdio: ['pipe', 'pipe', 'pipe'],
        env: { 
          ...process.env, 
          PYTHONPATH: process.cwd()
        }
      });

      let output = '';
      let errorOutput = '';

      debugProcess.stdout?.on('data', (data) => {
        output += data.toString();
      });

      debugProcess.stderr?.on('data', (data) => {
        errorOutput += data.toString();
      });

      debugProcess.on('close', (code) => {
        console.log('Debug test completed with code:', code);
        res.json({
          success: code === 0,
          output: output,
          error: errorOutput,
          exitCode: code,
          environment: {
            NODE_ENV: process.env.NODE_ENV,
            CWD: process.cwd(),
            PYTHONPATH: process.env.PYTHONPATH
          }
        });
      });

      debugProcess.on('error', (error) => {
        res.status(500).json({
          success: false,
          error: `Failed to run debug test: ${error.message}`
        });
      });

    } catch (error) {
      res.status(500).json({
        success: false,
        error: `Debug test failed: ${error.message}`
      });
    }
  });

  // IIT Φ Test API
  app.post('/api/test-phi', async (req, res) => {
    try {
      const { method = 'mock', maxChannels = 8, testSamples = 4 } = req.body;
      
      console.log(`Starting Φ test: method=${method}, channels=${maxChannels}, samples=${testSamples}`);
      
      // Create test script
      const testScript = `
import sys
import os
import torch
import numpy as np
import json

# Add src directory to path
sys.path.append('src')

try:
    from phi_estimator import PhiEstimator
    
    # Create estimator
    estimator = PhiEstimator(
        method='${method}',
        max_channels=${maxChannels}
    )
    
    # Generate test data (batch, channels, time)
    test_data = torch.randn(${testSamples}, ${maxChannels}, 256)
    
    # Calculate Φ values
    phi_values = estimator.compute(test_data)
    
    # Output results
    result = {
        'success': True,
        'method': '${method}',
        'maxChannels': ${maxChannels},
        'testSamples': ${testSamples},
        'phiValues': phi_values.tolist(),
        'avgPhi': phi_values.mean().item(),
        'minPhi': phi_values.min().item(),
        'maxPhi': phi_values.max().item(),
        'estimatorInfo': estimator.get_info()
    }
    
    print(json.dumps(result))
    
except Exception as e:
    error_result = {
        'success': False,
        'error': str(e),
        'method': '${method}',
        'maxChannels': ${maxChannels}
    }
    print(json.dumps(error_result))
`;

      // Write temporary script file
      const scriptPath = path.join(process.cwd(), 'temp_phi_test.py');
      fs.writeFileSync(scriptPath, testScript);
      
      // Execute Python script
      const pythonProcess = spawn('python3', [scriptPath], {
        cwd: process.cwd(),
        stdio: ['pipe', 'pipe', 'pipe']
      });
      
      let output = '';
      let errorOutput = '';
      
      pythonProcess.stdout.on('data', (data) => {
        output += data.toString();
      });
      
      pythonProcess.stderr.on('data', (data) => {
        errorOutput += data.toString();
      });
      
      pythonProcess.on('close', (code) => {
        // Clean up temporary file
        try {
          fs.unlinkSync(scriptPath);
        } catch (err) {
          console.warn('Failed to clean up temp script:', err);
        }
        
        if (code === 0) {
          try {
            // Extract JSON from output (handle log messages before JSON)
            const lines = output.trim().split('\n');
            const jsonLine = lines.find(line => line.startsWith('{'));
            
            if (jsonLine) {
              const result = JSON.parse(jsonLine);
              if (result.success) {
                res.json(result);
              } else {
                res.status(500).json({ 
                  error: 'Φ calculation failed', 
                  details: result.error 
                });
              }
            } else {
              throw new Error('No JSON found in output');
            }
          } catch (parseError) {
            console.error('Failed to parse Python output:', output);
            res.status(500).json({ 
              error: 'Failed to parse test results',
              output: output,
              stderr: errorOutput
            });
          }
        } else {
          console.error('Python script failed:', errorOutput);
          res.status(500).json({ 
            error: 'Python script execution failed',
            code: code,
            stderr: errorOutput,
            stdout: output
          });
        }
      });
      
      // Set timeout
      const timeoutId = setTimeout(() => {
        pythonProcess.kill();
        if (!res.headersSent) {
          res.status(408).json({ error: 'Φ test timeout' });
        }
      }, 30000); // 30 second timeout
      
      pythonProcess.on('close', () => {
        clearTimeout(timeoutId);
      });
      
    } catch (error) {
      console.error('Φ test error:', error);
      res.status(500).json({ 
        error: 'Internal server error', 
        details: error.message 
      });
    }
  });

  return httpServer;
}
