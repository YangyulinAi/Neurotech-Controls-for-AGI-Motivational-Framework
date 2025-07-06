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

  // Start real data analysis with selected SET file
  app.post('/api/start-analysis', (req, res) => {
    try {
      const { filename } = req.body;
      if (!filename) {
        return res.status(400).json({ error: 'Filename is required' });
      }

      // Only SET files are supported
      if (!filename.startsWith('set/')) {
        return res.status(400).json({ error: 'Only SET files are supported for analysis' });
      }

      const setFile = filename.replace('set/', '');
      const dataPath = path.resolve('./data/training set', setFile);
      if (!fs.existsSync(dataPath)) {
        return res.status(404).json({ error: 'SET data file not found' });
      }
      
      // Use SET file analyzer with actual ML processing
      const analysisPath = path.resolve('./analyze_set_file.py');
      const analysisArgs = [dataPath, '0.5'];

      console.log('Starting real data analysis with ML model...');
      
      const analysisProcess = spawn('python', [analysisPath, ...analysisArgs], {
        stdio: 'inherit',
        detached: false
      });

      analysisProcess.on('error', (error) => {
        console.error('Failed to start analysis:', error);
      });

      analysisProcess.on('exit', (code) => {
        console.log(`Analysis completed with code ${code}`);
        // Broadcast completion message to all WebSocket clients
        wss.clients.forEach(client => {
          if (client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify({
              type: 'analysis_complete',
              filename: filename,
              message: 'Real data analysis completed'
            }));
          }
        });
      });

      console.log(`Started real data analysis with file: ${filename}`);
      
      res.json({ 
        message: `Real data analysis started successfully`,
        filename,
        status: 'running',
        source: 'real_data'
      });
    } catch (error) {
      console.error('Analysis start error:', error);
      res.status(500).json({ error: 'Failed to start real data analysis' });
    }
  });

  // Endpoint for analysis scripts to broadcast WebSocket messages
  app.post("/api/bci/broadcast", async (req, res) => {
    try {
      const message = req.body;
      
      // Validate the message contains required fields
      if (typeof message.valence !== 'number' || typeof message.arousal !== 'number') {
        return res.status(400).json({ error: "Invalid message format" });
      }
      
      // Broadcast to all connected WebSocket clients
      wss.clients.forEach(client => {
        if (client.readyState === WebSocket.OPEN) {
          client.send(JSON.stringify(message));
        }
      });
      
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

  return httpServer;
}
