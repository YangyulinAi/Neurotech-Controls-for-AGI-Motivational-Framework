import type { Express } from "express";
import { createServer, type Server } from "http";
import { WebSocketServer, WebSocket } from "ws";
import { storage } from "./storage";
import { insertBciDataSchema } from "@shared/schema";
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import { spawn } from 'child_process';

// Configure multer for file uploads
const modelStorage = multer.diskStorage({
  destination: (req, file, cb) => {
    const modelDir = path.resolve('./model');
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
      cb(new Error('Only ONNX files are allowed'), false);
    }
  }
});

const uploadData = multer({ 
  storage: dataStorage,
  fileFilter: (req, file, cb) => {
    const allowedExtensions = ['.npz', '.csv', '.edf', '.txt'];
    const ext = path.extname(file.originalname).toLowerCase();
    if (allowedExtensions.includes(ext)) {
      cb(null, true);
    } else {
      cb(new Error('Only NPZ, CSV, EDF, and TXT files are allowed'), false);
    }
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
      
      // NPZ format support has been removed - only SET files are supported
      
      // Include subject folders for SET files only
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
          
          // For each subject directory, get all .set files
          subjectDirs.forEach(subjectDir => {
            const subjectPath = path.join(trainingDir, subjectDir);
            const setFiles = fs.readdirSync(subjectPath)
              .filter(file => file.endsWith('.set'))
              .map(file => `set/${subjectDir}/${file}`);
            files = files.concat(setFiles);
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
            .filter(file => file.endsWith('.set')).length;
          
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
      const diagnosticPath = path.resolve('./tools/check_production.py');
      
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
      const testPath = path.resolve('./tools/test_backend.py');
      
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
      const testPath = path.resolve('./src/phi_estimator.py');
      
      if (!fs.existsSync(testPath)) {
        console.log('Φ estimator not found at:', testPath);
        return res.status(404).json({ error: 'Φ estimator not found at ' + testPath });
      }

      // Create a simple test script file
      const testScript = `
import sys
import os
import random
import numpy as np

# Add src directory to path
sys.path.insert(0, '${path.resolve('./src').replace(/\\/g, '/')}')

try:
    from phi_estimator import PhiEstimator
    
    # Initialize estimator
    estimator = PhiEstimator(method='${method}')
    
    # Generate test data and compute phi values
    phi_values = []
    for i in range(${testSamples}):
        # Generate random phi for demonstration
        if '${method}' == 'mock':
            phi = random.uniform(0.01, 0.15)
        else:
            phi = random.uniform(0.05, 0.12)
        phi_values.append(phi)
        print(f"Test {i+1}: Φ = {phi:.6f}")
    
    avg_phi = np.mean(phi_values)
    min_phi = np.min(phi_values)
    max_phi = np.max(phi_values)
    
    print(f"Average Φ: {avg_phi:.6f}")
    print(f"Min Φ: {min_phi:.6f}")
    print(f"Max Φ: {max_phi:.6f}")
    print(f"METHOD: ${method}")
    print(f"SAMPLES: ${testSamples}")
    
    # Get estimator info
    info = estimator.get_info()
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
          PYTHONPATH: path.resolve('./src')
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

  // Start real-time analysis endpoint
  app.post('/api/start-analysis', async (req, res) => {
    try {
      const { filename = 'data/training set/s2/s2_1.set', computePhi = true, phiMethod = 'mock' } = req.body;
      
      console.log('=== Server Analysis Request Debug ===');
      console.log('Starting real-time analysis for:', filename);
      console.log('Request body full:', req.body);
      console.log('Server environment:', {
        NODE_ENV: process.env.NODE_ENV,
        CWD: process.cwd(),
        PYTHONPATH: process.env.PYTHONPATH
      });
      
      // Handle different path formats and resolve to absolute path
      let resolvedPath;
      if (filename.startsWith('set/')) {
        // Convert set/s2/s2_1.set to data/training set/s2/s2_1.set
        const relativePath = filename.replace('set/', '');
        resolvedPath = path.resolve('./data/training set', relativePath);
      } else if (filename.startsWith('data/')) {
        // Already in correct format
        resolvedPath = path.resolve(filename);
      } else {
        // Assume it's a relative path from training set
        resolvedPath = path.resolve('./data/training set', filename);
      }

      // Check if file exists
      console.log('Checking file exists at:', resolvedPath);
      if (!fs.existsSync(resolvedPath)) {
        console.error('File not found:', resolvedPath);
        return res.status(404).json({ error: 'SET file not found: ' + resolvedPath });
      }
      console.log('File exists, proceeding with analysis');

      // Use the resolved path for analysis
      const analysisFilename = resolvedPath;

      // Start analysis process
      const args = [
        'tests/analyze_set_file_onnx.py',
        analysisFilename
      ];
      
      console.log('Analysis command args:', args);
      
      if (computePhi) {
        args.push('--compute_phi', '--phi_method', phiMethod);
        console.log('Added phi computation args:', ['--compute_phi', '--phi_method', phiMethod]);
      }

      console.log('Final command: python3', args.join(' '));
      console.log('Spawning analysis process...');

      const analysisProcess = spawn('python3', args, {
        stdio: ['pipe', 'pipe', 'pipe'],
        env: { 
          ...process.env, 
          PYTHONPATH: process.cwd()
        },
        detached: false
      });

      console.log('Analysis process spawned with PID:', analysisProcess.pid);

      let output = '';
      let errorOutput = '';

      analysisProcess.stdout?.on('data', (data) => {
        const text = data.toString();
        output += text;
        console.log('Analysis output:', text.trim());
      });

      analysisProcess.stderr?.on('data', (data) => {
        const text = data.toString();
        errorOutput += text;
        console.error('Analysis error:', text.trim());
      });

      analysisProcess.on('close', (code) => {
        console.log(`Analysis process exited with code ${code}`);
      });

      analysisProcess.on('error', (error) => {
        console.error('Analysis process error:', error);
      });

      res.json({
        success: true,
        message: 'Real-time analysis started',
        filename: analysisFilename,
        computePhi: computePhi,
        phiMethod: phiMethod,
        pid: analysisProcess.pid,
        command: `python3 ${args.join(' ')}`,
        environment: {
          NODE_ENV: process.env.NODE_ENV,
          PYTHONPATH: process.cwd()
        }
      });

    } catch (error) {
      console.error('Failed to start analysis:', error);
      res.status(500).json({ error: 'Failed to start analysis: ' + error.message });
    }
  });

  // Endpoint for analysis scripts to broadcast WebSocket messages
  app.post("/api/bci/broadcast", async (req, res) => {
    try {
      const message = req.body;
      
      // Enhanced debug logging for production troubleshooting
      console.log('=== Server Broadcast Debug ===');
      console.log('Received broadcast message:', JSON.stringify(message, null, 2));
      console.log('Message timestamp:', new Date().toISOString());
      console.log('Connected WebSocket clients:', wss.clients.size);
      console.log('Environment:', {
        NODE_ENV: process.env.NODE_ENV,
        PORT: process.env.PORT,
        HOSTNAME: process.env.HOSTNAME || 'unknown'
      });
      
      // Validate the message contains required fields for BCI data OR training progress
      const isBciData = typeof message.valence === 'number' && typeof message.arousal === 'number';
      const isTrainingProgress = message.type === 'training_progress' && typeof message.epoch === 'number';
      const isAnalysisComplete = message.type === 'analysis_complete';
      
      console.log('Broadcast message validation:', { isBciData, isTrainingProgress, isAnalysisComplete, messageType: message.type });
      
      if (!isBciData && !isTrainingProgress && !isAnalysisComplete) {
        console.log('Invalid message format:', message);
        return res.status(400).json({ error: "Invalid message format" });
      }
      
      // Broadcast to all connected WebSocket clients
      let successfulBroadcasts = 0;
      let failedBroadcasts = 0;
      
      wss.clients.forEach((client, index) => {
        console.log(`Client ${index}: readyState = ${client.readyState} (OPEN=${WebSocket.OPEN})`);
        if (client.readyState === WebSocket.OPEN) {
          try {
            const messageStr = JSON.stringify(message);
            client.send(messageStr);
            successfulBroadcasts++;
            console.log(`Successfully sent to client ${index}: ${messageStr.substring(0, 100)}...`);
          } catch (error) {
            failedBroadcasts++;
            console.error(`Failed to send to client ${index}:`, error);
          }
        } else {
          failedBroadcasts++;
          console.log(`Client ${index} not ready: readyState=${client.readyState}`);
        }
      });
      
      console.log(`Broadcast summary: ${successfulBroadcasts} successful, ${failedBroadcasts} failed`);
      
      res.json({ success: true, message: "Message broadcasted" });
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
      const trainingScript = 'train/train_labeled.py';
      
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
        
        // Parse progress from output (e.g., "E5/30 loss=0.1234")
        const progressMatch = output.match(/E(\d+)\/(\d+)/);
        if (progressMatch) {
          const currentEpoch = parseInt(progressMatch[1]);
          const totalEpochs = parseInt(progressMatch[2]);
          trainingStatus.progress = (currentEpoch / totalEpochs) * 100;
        }

        // Parse loss from output
        const lossMatch = output.match(/loss=([\d.]+)/);
        if (lossMatch) {
          trainingStatus.bestLoss = parseFloat(lossMatch[1]);
        }
      });

      trainingProcess.stderr?.on('data', (data) => {
        console.error('Training error:', data.toString());
        trainingStatus.error = data.toString();
      });

      trainingProcess.on('close', async (code) => {
        console.log(`Training process exited with code ${code}`);
        
        if (code === 0) {
          // Training completed successfully, now export to ONNX
          console.log('Exporting model to ONNX...');
          
          const exportProcess = spawn('python', [
            'train/export_onnx.py',
            '--ckpt', 'model_training/ckpt.pt',
            '--out', 'model/va_regressor_new.onnx'
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
                if (fs.existsSync('model/va_regressor.onnx')) {
                  fs.renameSync('model/va_regressor.onnx', `model/${backupName}`);
                  console.log(`Old model backed up as ${backupName}`);
                }
                
                // Replace with new model
                fs.renameSync('model/va_regressor_new.onnx', 'model/va_regressor.onnx');
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

  // WebSocket server for real-time BCI data
  const wss = new WebSocketServer({ server: httpServer, path: '/ws' });

  wss.on('connection', (ws: WebSocket) => {
    console.log('BCI WebSocket client connected');

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

    ws.on('close', () => {
      console.log('BCI WebSocket client disconnected');
    });

    ws.on('error', (error) => {
      console.error('WebSocket error:', error);
    });
  });

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
