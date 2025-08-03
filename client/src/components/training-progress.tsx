import { useState, useEffect } from 'react';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Clock, TrendingDown, Zap } from 'lucide-react';

interface TrainingData {
  type: string;
  epoch: number;
  total_epochs: number;
  loss: number;
  best_loss: number;
  learning_rate: number;
  epoch_time: number;
  progress_percentage: number;
  phi?: number;  // IIT Φ (Integrated Information) value
}

interface TrainingProgressProps {
  onTrainingData?: (data: TrainingData) => void;
}

export function TrainingProgress({ onTrainingData }: TrainingProgressProps) {
  const [trainingData, setTrainingData] = useState<TrainingData | null>(null);
  const [isTraining, setIsTraining] = useState(false);
  const [lossHistory, setLossHistory] = useState<number[]>([]);

  useEffect(() => {
    // Connect to the main WebSocket endpoint
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('Training progress WebSocket connected to', wsUrl);
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('Training progress component received data:', data);
        
        if (data.type === 'training_progress') {
          console.log('Processing training progress data:', data);
          setTrainingData(data);
          setIsTraining(true);
          setLossHistory(prev => [...prev.slice(-20), data.loss]); // Keep last 20 losses
          
          if (onTrainingData) {
            onTrainingData(data);
          }
        }
      } catch (error) {
        console.error('Failed to parse training data:', error);
      }
    };

    ws.onclose = () => {
      console.log('Training progress WebSocket disconnected');
      setIsTraining(false);
    };

    ws.onerror = (error) => {
      console.error('Training progress WebSocket error:', error);
    };

    return () => {
      ws.close();
    };
  }, [onTrainingData]);

  if (!trainingData && !isTraining) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            Training Progress
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">
            No training in progress. Start training from the Upload page.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Zap className="h-5 w-5" />
          Training Progress
          {isTraining && <Badge variant="secondary">Training</Badge>}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {trainingData && (
          <>
            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Epoch {trainingData.epoch} / {trainingData.total_epochs}</span>
                <span>{trainingData.progress_percentage.toFixed(1)}%</span>
              </div>
              <Progress value={trainingData.progress_percentage} className="h-2" />
            </div>

            {/* Training Metrics */}
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <div className="flex items-center justify-center gap-1 text-sm text-muted-foreground mb-1">
                  <TrendingDown className="h-4 w-4" />
                  Current Loss
                </div>
                <div className="text-lg font-semibold">
                  {trainingData.loss.toFixed(4)}
                </div>
              </div>
              
              <div className="text-center">
                <div className="flex items-center justify-center gap-1 text-sm text-muted-foreground mb-1">
                  <TrendingDown className="h-4 w-4" />
                  Best Loss
                </div>
                <div className="text-lg font-semibold text-green-600">
                  {trainingData.best_loss.toFixed(4)}
                </div>
              </div>
              
              <div className="text-center">
                <div className="flex items-center justify-center gap-1 text-sm text-muted-foreground mb-1">
                  <Clock className="h-4 w-4" />
                  Epoch Time
                </div>
                <div className="text-lg font-semibold">
                  {trainingData.epoch_time.toFixed(1)}s
                </div>
              </div>
            </div>

            {/* Learning Rate */}
            <div className="text-center border-t pt-4">
              <div className="text-sm text-muted-foreground mb-1">Learning Rate</div>
              <div className="text-sm font-mono">
                {trainingData.learning_rate.toExponential(2)}
              </div>
            </div>

            {/* IIT Φ Value */}
            {trainingData.phi !== undefined && (
              <div className="text-center border-t pt-4">
                <div className="text-sm text-muted-foreground mb-1">IIT Φ (Consciousness)</div>
                <div className="text-sm font-mono text-cyan-600">
                  {trainingData.phi.toFixed(6)}
                </div>
              </div>
            )}

            {/* Mini Loss Chart */}
            {lossHistory.length > 1 && (
              <div className="border-t pt-4">
                <div className="text-sm text-muted-foreground mb-2">Loss Trend (Last 20 Epochs)</div>
                <div className="h-16 w-full relative">
                  <svg viewBox="0 0 100 40" className="w-full h-full">
                    <polyline
                      fill="none"
                      stroke="hsl(var(--primary))"
                      strokeWidth="1"
                      points={lossHistory.map((loss, index) => {
                        const x = (index / (lossHistory.length - 1)) * 100;
                        const minLoss = Math.min(...lossHistory);
                        const maxLoss = Math.max(...lossHistory);
                        const range = maxLoss - minLoss || 1;
                        const y = 35 - ((loss - minLoss) / range) * 30;
                        return `${x},${y}`;
                      }).join(' ')}
                    />
                  </svg>
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}