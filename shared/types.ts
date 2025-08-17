// Enhanced type definitions for BCI emotion analysis system
export type BciMsg = {
  timestamp: number;
  valence: number;
  arousal: number;
  phi?: number;
  type?: 'bci_data' | 'training_progress' | 'analysis_complete';
};

export type PhiMethod = 'off' | 'mock' | 'IIT3.0' | 'IIT4.0_light';

export type AnalysisMode = 'offline' | 'live';

export type AnalysisConfig = {
  filename: string;
  computePhi: boolean;
  phiMethod: PhiMethod;
  mode: AnalysisMode;
};

export type TrainingProgress = {
  type: 'training_progress';
  epoch: number;
  loss: number;
  progress: number;
  bestLoss?: number;
};

export type AnalysisComplete = {
  type: 'analysis_complete';
  message: string;
  avg_valence: number;
  avg_arousal: number;
  total_windows: number;
};

export type WebSocketMessage = BciMsg | TrainingProgress | AnalysisComplete;

// Re-export for backward compatibility
export type BciDataPoint = BciMsg;
export type ConnectionStatus = {
  connected: boolean;
  lastUpdate: Date | null;
  error: string | null;
};