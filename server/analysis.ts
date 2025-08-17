import { spawn, ChildProcess } from 'child_process';
import path from 'path';

// Analysis task management
let runningAnalysis: ChildProcess | null = null;
let isAnalysisRunning = false;

interface AnalysisConfig {
  filename: string;
  computePhi: boolean;
  phiMethod: string;
}

export function startAnalysis(config: AnalysisConfig, res: any) {
  if (isAnalysisRunning) {
    return res.status(409).json({ 
      error: "Analysis already running", 
      message: "Please wait for current analysis to complete" 
    });
  }

  isAnalysisRunning = true;

  // Build arguments
  const args = ["tests/analyze_file_onnx.py", config.filename];
  if (config.computePhi) {
    args.push("--compute_phi", "--phi_method", config.phiMethod);
  }

  console.log('Starting analysis with args:', args);

  // Spawn Python process
  const pythonExec = process.env.PYTHON || "python3";
  const analysisProcess = spawn(pythonExec, args, {
    env: { 
      ...process.env, 
      PYTHONPATH: process.cwd() 
    },
    stdio: ['pipe', 'pipe', 'pipe']
  });

  // Set timeout (10 minutes max)
  const timeout = setTimeout(() => {
    console.log('Analysis timeout - killing process');
    analysisProcess.kill('SIGKILL');
    isAnalysisRunning = false;
  }, 10 * 60 * 1000);

  // Handle process output
  analysisProcess.stdout?.on('data', (data) => {
    const text = data.toString().trim();
    console.log('[ANALYSIS-OUT]', text);
  });

  analysisProcess.stderr?.on('data', (data) => {
    const text = data.toString().trim();
    console.error('[ANALYSIS-ERR]', text);
  });

  // Handle process exit
  analysisProcess.on('close', (code) => {
    clearTimeout(timeout);
    isAnalysisRunning = false;
    runningAnalysis = null;
    console.log(`Analysis process exited with code: ${code}`);
  });

  analysisProcess.on('error', (error) => {
    clearTimeout(timeout);
    isAnalysisRunning = false;
    runningAnalysis = null;
    console.error('Analysis process error:', error);
  });

  runningAnalysis = analysisProcess;

  return res.json({
    success: true,
    message: "Analysis started successfully",
    pid: analysisProcess.pid,
    args: args
  });
}

export function stopAnalysis(res: any) {
  if (!isAnalysisRunning || !runningAnalysis) {
    return res.status(404).json({ 
      error: "No analysis running",
      message: "No active analysis process to stop"
    });
  }

  try {
    runningAnalysis.kill('SIGTERM');
    isAnalysisRunning = false;
    runningAnalysis = null;
    
    return res.json({
      success: true,
      message: "Analysis stopped successfully"
    });
  } catch (error) {
    return res.status(500).json({
      error: "Failed to stop analysis",
      details: error.message
    });
  }
}

export function getAnalysisStatus(res: any) {
  return res.json({
    isRunning: isAnalysisRunning,
    pid: runningAnalysis?.pid || null
  });
}