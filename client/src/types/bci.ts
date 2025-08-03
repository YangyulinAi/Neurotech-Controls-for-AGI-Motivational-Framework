export interface BciDataPoint {
  valence: number;
  arousal: number;
  timestamp: number;
  phi?: number;  // IIT Φ (Integrated Information) value
}

export interface BciStatistics {
  mean: number;
  stdDev: number;
  range: number;
  min: number;
  max: number;
}

export interface BciStats {
  valence: BciStatistics;
  arousal: BciStatistics;
}

export interface ConnectionStatus {
  connected: boolean;
  lastUpdate: Date | null;
  error: string | null;
}

export interface WebSocketMessage {
  valence?: number;
  arousal?: number;
  timestamp?: string;
  type?: string;
  message?: string;
  error?: string;
  filename?: string;
  phi?: number;  // IIT Φ (Integrated Information) value
  payload?: {
    phi?: number;
    timestamp?: number;
    method?: string;
    error?: string;
  };
}
