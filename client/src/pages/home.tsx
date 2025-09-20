import { useState, useEffect } from 'react';
import { useLocation } from 'wouter';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { useToast } from '@/hooks/use-toast';
import type { PhiMethod, AnalysisMode } from '@/types/bci';

export default function Home() {
  const [, setLocation] = useLocation();
  const { toast } = useToast();
  const [isUploading, setIsUploading] = useState(false);
  const [showDataSelection, setShowDataSelection] = useState(false);
  const [showTrainingInterface, setShowTrainingInterface] = useState(false);
  const [dataFiles, setDataFiles] = useState<string[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [selectedTrainingFiles, setSelectedTrainingFiles] = useState<string[]>([]);
  const [isTraining, setIsTraining] = useState(false);
  const [trainingProgress, setTrainingProgress] = useState(0);
  const [lossHistory, setLossHistory] = useState<Array<{epoch: number, loss: number}>>([]);
  const [currentLoss, setCurrentLoss] = useState<number | null>(null);
  const [trainingEpochs, setTrainingEpochs] = useState(30);
  const [datasetType, setDatasetType] = useState<'set'>('set');
  const [batchSize, setBatchSize] = useState(16);
  const [learningRate, setLearningRate] = useState(0.0001);
  const [windowSize, setWindowSize] = useState(5.0);
  const [overlap, setOverlap] = useState(0.5);
  const [outputInterval, setOutputInterval] = useState(0.1);
  
  // Enhanced Φ controls and analysis mode
  const [phiMethod, setPhiMethod] = useState<PhiMethod>('off');
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>('offline');
  const [phiMaxChannels, setPhiMaxChannels] = useState(8);
  const [analysisInProgress, setAnalysisInProgress] = useState(false);
  const [analysisDisabledUntil, setAnalysisDisabledUntil] = useState<number | null>(null);

  // Check if analysis is currently disabled due to 409 error
  const isAnalysisDisabled = analysisDisabledUntil ? Date.now() < analysisDisabledUntil : false;

  // Fetch available data files for analysis
  const fetchDataFiles = async () => {
    setLoadingFiles(true);
    try {
      const response = await fetch('/api/data-files');
      if (response.ok) {
        const files = await response.json();
        setDataFiles(files);
      } else {
        toast({
          title: 'Error',
          description: 'Failed to load data files',
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to connect to server',
        variant: 'destructive',
      });
    } finally {
      setLoadingFiles(false);
    }
  };

  // Fetch training subjects for model training
  const fetchTrainingSubjects = async () => {
    setLoadingFiles(true);
    try {
      const response = await fetch('/api/training-subjects');
      if (response.ok) {
        const subjects = await response.json();
        setDataFiles(subjects.map((s: any) => s.id)); // Use subject IDs as file list
      } else {
        toast({
          title: 'Error',
          description: 'Failed to load training subjects',
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to connect to server',
        variant: 'destructive',
      });
    } finally {
      setLoadingFiles(false);
    }
  };

  // Load data files when dialog opens
  useEffect(() => {
    if (showDataSelection) {
      fetchDataFiles();
    } else if (showTrainingInterface) {
      fetchTrainingSubjects();
    }
  }, [showDataSelection, showTrainingInterface]);

  // Handle real data analysis
  const handleDataSelection = async (filename: string) => {
    console.log('=== Starting Analysis Debug ===');
    console.log('Selected file:', filename);
    console.log('Environment:', {
      protocol: window.location.protocol,
      host: window.location.host,
      pathname: window.location.pathname
    });
    
    try {
      const requestBody = { 
        filename,
        computePhi: phiMethod !== 'off',
        phiMethod: phiMethod === 'off' ? 'mock' : phiMethod,
        outputInterval: outputInterval,
        mode: 'offline'  // 强制设置为离线模式，因为这是文件分析
      };
      
      console.log('Sending analysis request:', requestBody);
      
      const response = await fetch('/api/start-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      console.log('Analysis response status:', response.status);
      console.log('Analysis response headers:', Object.fromEntries(response.headers.entries()));

      if (response.ok) {
        const result = await response.json();
        console.log('=== Analysis Started Successfully ===');
        console.log('Analysis response data:', result);
        console.log('Analysis PID:', result.pid);
        console.log('Analysis file path:', result.filename);
        console.log('Phi computation enabled:', result.computePhi);
        
        setShowDataSelection(false);
        setLocation('/dashboard?mode=offline');
        toast({
          title: 'Offline Analysis Started',
          description: result.message || `Analyzing EEG file: ${filename}`,
          duration: 8000,
        });
      } else if (response.status === 409) {
        // Handle 409 Conflict - analysis already running
        setAnalysisDisabledUntil(Date.now() + 5000); // Disable for 5 seconds
        toast({
          title: 'Analysis Already Running',
          description: 'Please wait for the current analysis to complete before starting a new one.',
          variant: 'destructive',
          duration: 5000,
        });
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        console.error('Analysis failed with response:', errorData);
        toast({
          title: 'Analysis Failed',
          description: errorData.error || `Server error: ${response.status}`,
          variant: 'destructive',
        });
      }
    } catch (error) {
      console.error('Error starting analysis:', error);
      toast({
        title: 'Connection Error',
        description: `Failed to start analysis: ${error instanceof Error ? error.message : 'Unknown error'}`,
        variant: 'destructive',
      });
    }
  };

  const handleModelUpload = async (event: any) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.onnx')) {
      toast({
        title: 'Invalid File Type',
        description: 'Please upload an ONNX model file (.onnx)',
        variant: 'destructive',
      });
      return;
    }

    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append('model', file);

      const response = await fetch('/api/upload-model', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        toast({
          title: 'Model Uploaded',
          description: 'ONNX model has been successfully uploaded and replaced.',
        });
      } else {
        throw new Error('Upload failed');
      }
    } catch (error) {
      toast({
        title: 'Upload Failed',
        description: 'Failed to upload model. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleDataUpload = async (event: any) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    try {
      const formData = new FormData();
      for (let i = 0; i < files.length; i++) {
        formData.append('data', files[i]);
      }

      const response = await fetch('/api/upload-data', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        toast({
          title: 'Data Uploaded',
          description: `${files.length} data files have been uploaded successfully.`,
        });
      } else {
        throw new Error('Upload failed');
      }
    } catch (error) {
      toast({
        title: 'Upload Failed',
        description: 'Failed to upload data files. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsUploading(false);
    }
  };

  // Handle training
  const handleStartTraining = async () => {
    if (selectedTrainingFiles.length === 0) {
      toast({
        title: 'No Files Selected',
        description: 'Please select at least one data file for training.',
        variant: 'destructive',
      });
      return;
    }

    setIsTraining(true);
    setTrainingProgress(0);
    setLossHistory([]);
    setCurrentLoss(null);

    try {
      const response = await fetch('/api/train-model', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          dataFiles: selectedTrainingFiles,
          epochs: trainingEpochs,
          datasetType: datasetType,
          batchSize: batchSize,
          learningRate: learningRate,
          windowSize: windowSize,
          overlap: overlap,
          computePhi: phiMethod !== 'off',
          phiMethod: phiMethod,
          phiMaxChannels: phiMaxChannels
        }),
      });

      if (response.ok) {
        const result = await response.json();
        toast({
          title: 'Training Started',
          description: `Model training has begun with ${selectedTrainingFiles.length} data files.`,
        });
        
        // Monitor training progress
        monitorTrainingProgress();
      } else {
        throw new Error('Training failed to start');
      }
    } catch (error) {
      toast({
        title: 'Training Failed',
        description: 'Failed to start model training. Please try again.',
        variant: 'destructive',
      });
    }
  };

  // Monitor training progress
  const monitorTrainingProgress = () => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch('/api/training-status');
        const status = await response.json();
        
        setTrainingProgress(status.progress || 0);
        
        if (status.bestLoss !== null && status.bestLoss !== currentLoss) {
          setCurrentLoss(status.bestLoss);
          const currentEpoch = Math.round((status.progress / 100) * trainingEpochs);
          if (currentEpoch > 0) {
            setLossHistory(prev => {
              const newHistory = [...prev];
              const existingIndex = newHistory.findIndex(item => item.epoch === currentEpoch);
              if (existingIndex >= 0) {
                newHistory[existingIndex] = { epoch: currentEpoch, loss: status.bestLoss };
              } else {
                newHistory.push({ epoch: currentEpoch, loss: status.bestLoss });
              }
              return newHistory.sort((a, b) => a.epoch - b.epoch);
            });
          }
        }
        
        if (status.completed) {
          clearInterval(interval);
          setIsTraining(false);
          setShowTrainingInterface(false);
          toast({
            title: 'Training Completed',
            description: `New model trained successfully! Final Loss: ${status.bestLoss?.toFixed(4)}`,
          });
        }
        
        if (status.error) {
          clearInterval(interval);
          setIsTraining(false);
          toast({
            title: 'Training Failed',
            description: status.error,
            variant: 'destructive',
          });
        }
      } catch (error) {
        console.error('Failed to check training status:', error);
      }
    }, 2000);
  };

  // Toggle file selection for training
  const toggleTrainingFile = (filename: string) => {
    setSelectedTrainingFiles(prev => 
      prev.includes(filename) 
        ? prev.filter(f => f !== filename)
        : [...prev, filename]
    );
  };

  // Select all files for training
  const selectAllTrainingFiles = () => {
    setSelectedTrainingFiles(dataFiles);
  };

  // Clear training file selection
  const clearTrainingSelection = () => {
    setSelectedTrainingFiles([]);
  };




  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <header className="border-b border-gray-700 bg-gray-800/50 backdrop-blur-sm">
        <div className="container mx-auto px-6 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl shadow-lg">
                <span className="text-white text-xl">🧠</span>
              </div>
              <div className="flex flex-col">
                <h1 className="text-2xl font-bold text-white leading-tight">
                  Neurotech Controls for AGI Motivational Framework
                </h1>
                <div className="flex items-center space-x-2 mt-1">
                  <span className="text-blue-400 font-medium text-sm">Neural Axis</span>
                  <span className="text-gray-500">•</span>
                  <span className="text-gray-400 text-sm">Real-time BCI emotion prediction</span>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="hidden md:flex flex-col items-end text-sm">
                <span className="text-gray-300 font-medium">AGI Framework</span>
                <span className="text-gray-500 text-xs">v2.0</span>
              </div>
              <Badge className="text-green-400 border-green-400/50 bg-green-400/10 px-3 py-1.5 shadow-lg">
                <span className="inline-block w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse shadow-sm"></span>
                System Online
              </Badge>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-12">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-white mb-4">
            Advanced EEG Emotion Recognition
          </h2>
          <p className="text-gray-300 text-lg max-w-2xl mx-auto">
            Leverage cutting-edge machine learning to analyze brain signals and predict emotional states 
            with high accuracy using valence and arousal dimensions.
          </p>
          <p className="text-gray-500 text-sm mt-2">
            Powered by Neural Axis Technology
          </p>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12 max-w-6xl mx-auto">
          {/* Real Data Analysis */}
          <Card className="bg-gray-800 border-gray-700 hover:bg-gray-750 transition-colors cursor-pointer group">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="h-8 w-8 text-blue-400 group-hover:text-blue-300 transition-colors">🧠</div>
                <Badge>Real Data</Badge>
              </div>
              <CardTitle className="text-white">Offline Analysis</CardTitle>
              <CardDescription className="text-gray-400">
                Analyze existing EEG files (SET, FIF, CSV formats) for testing and validation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button 
                onClick={() => setShowDataSelection(true)}
                className="w-full bg-blue-600 hover:bg-blue-700"
                disabled={isAnalysisDisabled}
              >
                {isAnalysisDisabled ? '⏳ Please Wait...' : '📊 Analyze File'}
              </Button>
            </CardContent>
          </Card>

          {/* Model Upload */}
          <Card className="bg-gray-800 border-gray-700 hover:bg-gray-750 transition-colors">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="h-8 w-8 text-purple-400">🧠</div>
                <Badge>ONNX</Badge>
              </div>
              <CardTitle className="text-white">Upload Model</CardTitle>
              <CardDescription className="text-gray-400">
                Replace the current ONNX model with your own trained emotion recognition model
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="relative">
                <Button 
                  className="w-full bg-purple-600 hover:bg-purple-700"
                  disabled={isUploading}
                  onClick={() => (document.getElementById('model-upload') as any)?.click()}
                >
                  📤 {isUploading ? 'Uploading...' : 'Upload ONNX Model'}
                </Button>
                <input
                  id="model-upload"
                  type="file"
                  accept=".onnx"
                  onChange={handleModelUpload}
                  className="hidden"
                />
              </div>
            </CardContent>
          </Card>

          {/* Data Upload */}
          <Card className="bg-gray-800 border-gray-700 hover:bg-gray-750 transition-colors">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="h-8 w-8 text-green-400">🗃️</div>
                <Badge>Multi-Format</Badge>
              </div>
              <CardTitle className="text-white">Upload Data</CardTitle>
              <CardDescription className="text-gray-400">
                Upload EEG data files (SET, FIF, CSV formats) to subject folders for analysis and training
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="relative">
                <Button 
                  className="w-full bg-green-600 hover:bg-green-700"
                  disabled={isUploading}
                  onClick={() => (document.getElementById('data-upload') as any)?.click()}
                >
                  📤 {isUploading ? 'Uploading...' : 'Upload Data Files'}
                </Button>
                <input
                  id="data-upload"
                  type="file"
                  accept=".set,.fif,.csv,.npz,.edf,.txt"
                  multiple
                  onChange={handleDataUpload}
                  className="hidden"
                />
              </div>
            </CardContent>
          </Card>

          {/* Train Model */}
          <Card className="bg-gray-800 border-gray-700 hover:bg-gray-750 transition-colors cursor-pointer group">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="h-8 w-8 text-orange-400 group-hover:text-orange-300 transition-colors">🔬</div>
                <Badge>Training</Badge>
              </div>
              <CardTitle className="text-white">Train Model</CardTitle>
              <CardDescription className="text-gray-400">
                Train a new emotion recognition model using your own data files
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button 
                onClick={() => setShowTrainingInterface(true)}
                className="w-full bg-orange-600 hover:bg-orange-700"
              >
                🧠 Start Training
              </Button>
            </CardContent>
          </Card>

          {/* Real-time Device */}
          <Card className="bg-gray-800 border-gray-700 hover:bg-gray-750 transition-colors">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="h-8 w-8 text-yellow-400">⚡</div>
                <Badge>Live</Badge>
              </div>
              <CardTitle className="text-white">Real-time Analysis</CardTitle>
              <CardDescription className="text-gray-400">
                Connect live EEG devices via Lab Streaming Layer (LSL) for real-time emotion monitoring
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button 
                className="w-full bg-yellow-600 hover:bg-yellow-700"
                onClick={() => setLocation('/dashboard?mode=realtime')}
              >
                ⚡ Start Real-time
              </Button>
            </CardContent>
          </Card>


          {/* Production Debug */}
          <Card className="bg-gray-800 border-gray-700 hover:bg-gray-750 transition-colors cursor-pointer group">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="h-8 w-8 text-red-400 group-hover:text-red-300 transition-colors">🔧</div>
                <Badge className="bg-red-600/20 text-red-300 border-red-500/50">Debug</Badge>
              </div>
              <CardTitle className="text-white">Production Debug</CardTitle>
              <CardDescription className="text-gray-400">
                Test production environment functionality, Python dependencies, and analysis pipeline
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Button 
                  onClick={async () => {
                    try {
                      console.log('Installing production dependencies...');
                      toast({
                        title: 'Installing Dependencies',
                        description: 'Installing onnxruntime and required packages...',
                      });
                      
                      const response = await fetch('/api/install-production-deps', { method: 'POST' });
                      const result = await response.json();
                      console.log('=== Installation Result ===');
                      console.log('Success:', result.success);
                      console.log('Output:', result.output);
                      console.log('Error:', result.error);
                      
                      toast({
                        title: result.success ? 'Dependencies Installed' : 'Installation Failed',
                        description: result.success ? 'ONNX Runtime and dependencies installed successfully' : 'Check console for details',
                        variant: result.success ? 'default' : 'destructive'
                      });
                    } catch (error) {
                      console.error('Installation error:', error);
                      toast({
                        title: 'Installation Error',
                        description: 'Failed to install dependencies',
                        variant: 'destructive'
                      });
                    }
                  }}
                  className="w-full bg-green-600 hover:bg-green-700"
                >
                  📦 Install Missing Dependencies
                </Button>
                
                <Button 
                  onClick={async () => {
                    try {
                      console.log('Starting production environment debug test...');
                      const response = await fetch('/api/debug-production', { method: 'POST' });
                      const result = await response.json();
                      console.log('=== Production Debug Result ===');
                      console.log('Success:', result.success);
                      console.log('Output:', result.output);
                      console.log('Error:', result.error);
                      console.log('Environment:', result.environment);
                      toast({
                        title: result.success ? 'Debug Test Passed' : 'Debug Test Failed',
                        description: result.success ? 'Production environment is working' : 'Check console for details',
                        variant: result.success ? 'default' : 'destructive'
                      });
                    } catch (error) {
                      console.error('Debug test error:', error);
                      toast({
                        title: 'Debug Test Error',
                        description: 'Failed to run production debug test',
                        variant: 'destructive'
                      });
                    }
                  }}
                  className="w-full bg-red-600 hover:bg-red-700"
                >
                  🔍 Test Production Environment
                </Button>
              </div>
            </CardContent>
          </Card>




        </div>

        {/* Quick Start Guide */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-4">Quick Start Guide</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-white mb-2">For Simulation Testing:</h4>
              <ol className="text-gray-300 space-y-1 text-sm">
                <li>1. Upload your ONNX model (optional)</li>
                <li>2. Upload EEG data files (SET/FIF/CSV formats)</li>
                <li>3. Select EEG file and view real-time results</li>
              </ol>
            </div>
            <div>
              <h4 className="font-medium text-white mb-2">For Real-time Analysis:</h4>
              <ol className="text-gray-300 space-y-1 text-sm">
                <li>1. Connect your EEG device via LSL</li>
                <li>2. Configure system parameters</li>
                <li>3. Start real-time monitoring</li>
              </ol>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-700 bg-gray-800/50 backdrop-blur-sm mt-12">
        <div className="container mx-auto px-6 py-6">
          <div className="text-center">
            <p className="text-gray-500 text-sm">© 2025 Neural Axis. Neurotech Controls for AGI Motivational Framework. All rights reserved.</p>
          </div>
        </div>
      </footer>



      {/* Training Interface Dialog */}
      <Dialog open={showTrainingInterface} onOpenChange={setShowTrainingInterface}>
        <DialogContent className="bg-gray-800 border-gray-700 text-white max-w-2xl">
          <DialogHeader>
            <DialogTitle>Train Model</DialogTitle>
            <DialogDescription className="text-gray-400">
              Select subjects to train a new emotion recognition model. Each subject must have labels.json.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            {/* File Selection */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-white">Training Subjects</h4>
                <div className="space-x-2">
                  <Button 
                    size="sm" 
                    variant="outline" 
                    onClick={selectAllTrainingFiles}
                    disabled={dataFiles.length === 0}
                    className="border-gray-600 text-gray-300 hover:bg-gray-700"
                  >
                    Select All
                  </Button>
                  <Button 
                    size="sm" 
                    variant="outline" 
                    onClick={clearTrainingSelection}
                    disabled={selectedTrainingFiles.length === 0}
                    className="border-gray-600 text-gray-300 hover:bg-gray-700"
                  >
                    Clear
                  </Button>
                </div>
              </div>
              
              <div className="border border-gray-600 rounded-lg p-3 max-h-48 overflow-y-auto">
                {loadingFiles ? (
                  <div className="text-center text-gray-400 py-4">
                    <div>Loading data files...</div>
                  </div>
                ) : dataFiles.length === 0 ? (
                  <div className="text-center text-gray-400 py-4">
                    <div>No data files available</div>
                    <div className="text-sm mt-1">Please upload SET files first</div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {dataFiles.map((file) => (
                      <div key={file} className="flex items-center space-x-2 p-1 hover:bg-gray-700 rounded">
                        <input
                          type="checkbox"
                          id={`train-${file}`}
                          checked={selectedTrainingFiles.includes(file)}
                          onChange={() => toggleTrainingFile(file)}
                          className="rounded text-orange-500 focus:ring-orange-500"
                        />
                        <label 
                          htmlFor={`train-${file}`} 
                          className="text-gray-300 cursor-pointer flex-1 text-sm"
                        >
                          📊 {file}
                        </label>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            
            {/* Training Configuration */}
            {!isTraining && (
              <div>
                <h4 className="font-medium text-white mb-3">Training Configuration</h4>
                <div className="space-y-3">
                  {/* Dataset Type - Only SET files supported */}
                  <div className="flex items-center space-x-3">
                    <label className="text-sm text-gray-400 w-20">Dataset:</label>
                    <div className="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-white text-sm w-32 cursor-not-allowed">
                      SET Files
                    </div>
                    <span className="text-xs text-gray-500">
                      Raw EEG data with emotion labels
                    </span>
                  </div>
                  
                  {/* Basic Parameters */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="flex items-center space-x-2">
                      <label htmlFor="epochs" className="text-sm text-gray-400 w-16">Epochs:</label>
                      <input
                        id="epochs"
                        type="number"
                        min="1"
                        max="200"
                        value={trainingEpochs}
                        onChange={(e) => setTrainingEpochs(Number(e.target.value))}
                        className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-white text-sm w-16 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                      />
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <label htmlFor="batch" className="text-sm text-gray-400 w-16">Batch:</label>
                      <input
                        id="batch"
                        type="number"
                        min="1"
                        max="64"
                        value={batchSize}
                        onChange={(e) => setBatchSize(Number(e.target.value))}
                        className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-white text-sm w-16 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                      />
                    </div>
                  </div>
                  
                  {/* Advanced Parameters for SET files */}
                  {(
                    <div className="border-t border-gray-600 pt-3 mt-3">
                      <h5 className="text-sm font-medium text-white mb-2">Advanced Settings</h5>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="flex items-center space-x-2">
                          <label className="text-sm text-gray-400 w-16">Window:</label>
                          <input
                            type="number"
                            min="1"
                            max="10"
                            step="0.5"
                            value={windowSize}
                            onChange={(e) => setWindowSize(Number(e.target.value))}
                            className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-white text-sm w-16 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                          />
                          <span className="text-xs text-gray-500">sec</span>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <label className="text-sm text-gray-400 w-16">Overlap:</label>
                          <input
                            type="number"
                            min="0"
                            max="0.9"
                            step="0.1"
                            value={overlap}
                            onChange={(e) => setOverlap(Number(e.target.value))}
                            className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-white text-sm w-16 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                          />
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <label className="text-sm text-gray-400 w-16">LR:</label>
                          <input
                            type="number"
                            min="0.00001"
                            max="0.01"
                            step="0.00001"
                            value={learningRate}
                            onChange={(e) => setLearningRate(Number(e.target.value))}
                            className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-white text-sm w-20 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                          />
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <label className="text-sm text-gray-400 w-16">Output:</label>
                          <select
                            value={outputInterval}
                            onChange={(e) => setOutputInterval(Number(e.target.value))}
                            className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-white text-sm w-16 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                          >
                            <option value={0.1}>0.1s</option>
                            <option value={0.5}>0.5s</option>
                            <option value={1.0}>1.0s</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Training Status */}
            {isTraining && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-400">Training Progress</span>
                    <span className="text-sm text-white">{Math.round(trainingProgress)}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div 
                      className="bg-orange-500 h-2 rounded-full transition-all duration-300" 
                      style={{ width: `${trainingProgress}%` }}
                    ></div>
                  </div>
                  {currentLoss !== null && (
                    <div className="text-sm text-gray-400">
                      Current Loss: <span className="text-white">{currentLoss.toFixed(4)}</span>
                    </div>
                  )}
                </div>

                {/* Loss Visualization */}
                {lossHistory.length > 0 && (
                  <div className="border border-gray-600 rounded-lg p-4 bg-gray-900">
                    <h5 className="text-sm font-medium text-white mb-3">Training Loss</h5>
                    <div className="h-32 relative">
                      <svg className="w-full h-full">
                        {/* Background grid */}
                        <defs>
                          <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                            <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#374151" strokeWidth="1" opacity="0.3"/>
                          </pattern>
                        </defs>
                        <rect width="100%" height="100%" fill="url(#grid)" />
                        
                        {/* Loss line */}
                        {lossHistory.length > 1 && (
                          <polyline
                            fill="none"
                            stroke="#fb923c"
                            strokeWidth="2"
                            points={lossHistory.map((point, index) => {
                              const x = (index / (lossHistory.length - 1)) * 100;
                              const maxLoss = Math.max(...lossHistory.map(p => p.loss));
                              const minLoss = Math.min(...lossHistory.map(p => p.loss));
                              const range = maxLoss - minLoss;
                              const y = range > 0 ? (1 - (point.loss - minLoss) / range) * 100 : 50;
                              return `${x}%,${y}%`;
                            }).join(' ')}
                          />
                        )}
                        
                        {/* Data points */}
                        {lossHistory.map((point, index) => {
                          const x = (index / Math.max(lossHistory.length - 1, 1)) * 100;
                          const maxLoss = Math.max(...lossHistory.map(p => p.loss));
                          const minLoss = Math.min(...lossHistory.map(p => p.loss));
                          const range = maxLoss - minLoss;
                          const y = range > 0 ? (1 - (point.loss - minLoss) / range) * 100 : 50;
                          return (
                            <circle
                              key={index}
                              cx={`${x}%`}
                              cy={`${y}%`}
                              r="3"
                              fill="#fb923c"
                              stroke="#1f2937"
                              strokeWidth="1"
                            />
                          );
                        })}
                      </svg>
                      
                      {/* Axis labels */}
                      <div className="absolute bottom-0 left-0 text-xs text-gray-400">
                        Epoch 1
                      </div>
                      <div className="absolute bottom-0 right-0 text-xs text-gray-400">
                        Epoch {trainingEpochs}
                      </div>
                      <div className="absolute top-0 left-0 text-xs text-gray-400">
                        {lossHistory.length > 0 ? Math.max(...lossHistory.map(p => p.loss)).toFixed(3) : '1.000'}
                      </div>
                      <div className="absolute bottom-0 left-0 text-xs text-gray-400 transform -translate-y-4">
                        {lossHistory.length > 0 ? Math.min(...lossHistory.map(p => p.loss)).toFixed(3) : '0.000'}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Selected Files Info */}
            <div className="text-sm text-gray-400">
              Selected: {selectedTrainingFiles.length} of {dataFiles.length} file(s)
              {dataFiles.length > 0 && (
                <span className="ml-2 text-blue-400">
                  ({dataFiles.length} available)
                </span>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-3 pt-4">
              <Button 
                variant="outline" 
                onClick={() => setShowTrainingInterface(false)}
                disabled={isTraining}
                className="border-gray-600 text-gray-300 hover:bg-gray-700"
              >
                Cancel
              </Button>
              <Button 
                onClick={handleStartTraining}
                disabled={isTraining || selectedTrainingFiles.length === 0}
                className="bg-orange-600 hover:bg-orange-700"
              >
                {isTraining ? 'Training...' : 'Start Training'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Enhanced Data Selection Dialog with Φ Controls */}
      <Dialog open={showDataSelection} onOpenChange={setShowDataSelection}>
        <DialogContent className="bg-gray-800 border-gray-700 text-white max-w-2xl">
          <DialogHeader>
            <DialogTitle>Enhanced Analysis Configuration</DialogTitle>
            <DialogDescription className="text-gray-400">
              Configure analysis mode and consciousness measurement options
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-6">
            {/* Analysis Mode Selection */}
            <div className="space-y-3">
              <Label className="text-white font-medium">Analysis Mode</Label>
              <RadioGroup value={analysisMode} onValueChange={(value: AnalysisMode) => setAnalysisMode(value)}>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="offline" id="offline" className="text-blue-500" />
                  <Label htmlFor="offline" className="text-gray-300">Offline Analysis (File-based)</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="live" id="live" className="text-green-500" />
                  <Label htmlFor="live" className="text-gray-300">Live Streaming (Real-time)</Label>
                </div>
              </RadioGroup>
            </div>

            {/* Φ Method Selection */}
            <div className="space-y-3">
              <Label className="text-white font-medium">Consciousness Measurement (IIT Φ)</Label>
              <RadioGroup value={phiMethod} onValueChange={(value: PhiMethod) => setPhiMethod(value)}>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="off" id="phi-off" className="text-gray-500" />
                  <Label htmlFor="phi-off" className="text-gray-300">Disabled</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="mock" id="phi-mock" className="text-yellow-500" />
                  <Label htmlFor="phi-mock" className="text-gray-300">Mock (Testing)</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="IIT3.0" id="phi-iit3" className="text-cyan-500" />
                  <Label htmlFor="phi-iit3" className="text-gray-300">IIT 3.0 (Standard)</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <RadioGroupItem value="IIT4.0_light" id="phi-iit4" className="text-purple-500" />
                  <Label htmlFor="phi-iit4" className="text-gray-300">IIT 4.0 Light (Fast)</Label>
                </div>
              </RadioGroup>
            </div>

            {/* File Selection */}
            <div className="space-y-3">
              <Label className="text-white font-medium">Select EEG File</Label>
              <div className="max-h-64 overflow-y-auto border border-gray-600 rounded-lg p-3">
                {loadingFiles ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="text-gray-400">Loading data files...</div>
                  </div>
                ) : dataFiles.length === 0 ? (
                  <div className="text-center py-8 text-gray-400">
                    No EEG files found. Upload SET, FIF, or CSV files to subject folders first.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {dataFiles.map((file) => {
                      const displayName = file.replace(/^set\//, '');
                      const format = file.split('.').pop()?.toUpperCase() || 'EEG';
                      
                      return (
                        <Button
                          key={file}
                          variant="outline"
                          className="w-full justify-between bg-gray-700 border-gray-600 hover:bg-gray-600 text-white"
                          onClick={() => handleDataSelection(file)}
                          disabled={analysisInProgress}
                        >
                          <span className="flex items-center">
                            📊 {displayName}
                          </span>
                          <Badge variant="secondary" className="bg-gray-600 text-gray-200">
                            {format}
                          </Badge>
                        </Button>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>

            {/* Status Display */}
            {analysisInProgress && (
              <div className="flex items-center space-x-2 text-blue-400">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-400"></div>
                <span>Starting analysis...</span>
              </div>
            )}
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <Button
              variant="outline"
              onClick={() => setShowDataSelection(false)}
              className="bg-gray-700 border-gray-600 hover:bg-gray-600 text-white"
              disabled={analysisInProgress}
            >
              Cancel
            </Button>
          </div>
        </DialogContent>
      </Dialog>

    </div>
  );
}