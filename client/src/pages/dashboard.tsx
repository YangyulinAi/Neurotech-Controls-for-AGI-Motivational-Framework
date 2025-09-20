import { useState, useEffect, useCallback } from 'react';
import { Smile, Zap, Database, Clock, Home, Brain } from 'lucide-react';
import { useLocation } from 'wouter';
import { Sidebar } from '@/components/sidebar';
import { Header } from '@/components/header';
import { MetricCard } from '@/components/metric-card';
import { VAPlane } from '@/components/va-plane';
import { TimeSeriesChart } from '@/components/time-series-chart';
import { StatisticsPanel } from '@/components/statistics-panel';
import { DebugConsole } from '@/components/debug-console';
import { TrainingProgress } from '@/components/training-progress';
import { useWebSocket } from '@/hooks/use-websocket';
import { useToast } from '@/hooks/use-toast';

export default function Dashboard() {
  const [, setLocation] = useLocation();
  const [refreshRate, setRefreshRate] = useState(500);
  const [timeRange, setTimeRange] = useState(60);
  const [sessionStartTime] = useState(Date.now());
  const [sessionTime, setSessionTime] = useState('00:00');
  const [analysisMode, setAnalysisMode] = useState<'realtime' | 'offline'>('realtime');
  const [offlineResults, setOfflineResults] = useState<any>(null);
  const [lslStatus, setLslStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'streaming' | 'retrying' | 'error'>('disconnected');

  const { toast } = useToast();
  
  // Detect analysis mode from URL params and start real-time analysis
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const mode = urlParams.get('mode');
    if (mode === 'offline' || mode === 'realtime') {
      setAnalysisMode(mode);
      
      // Auto-start real-time analysis for live EEG device connection
      if (mode === 'realtime') {
        console.log('Starting real-time EEG device analysis...');
        setLslStatus('connecting');
        
        const startRealTimeAnalysis = async () => {
          try {
            const response = await fetch('/api/start-analysis', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                mode: 'live',
                computePhi: true,
                phiMethod: 'mock'
              }),
            });

            const data = await response.json();
            
            if (response.ok) {
              console.log('Real-time analysis started:', data);
              setLslStatus('connected');
              toast({
                title: 'Real-time Analysis Started',
                description: 'Connecting to EEG devices via LSL...',
                duration: 3000,
              });
            } else {
              console.error('Failed to start real-time analysis:', data);
              setLslStatus('error');
              toast({
                title: 'Connection Failed',
                description: data.error || 'Failed to connect to EEG devices',
                variant: 'destructive',
                duration: 5000,
              });
            }
          } catch (error) {
            console.error('Error starting real-time analysis:', error);
            setLslStatus('error');
            toast({
              title: 'Connection Error',
              description: 'Unable to start real-time EEG analysis',
              variant: 'destructive',
              duration: 5000,
            });
          }
        };

        startRealTimeAnalysis();
      }
    }
  }, [toast]);
  
  const {
    connectionStatus,
    dataFlowStatus,
    currentData,
    dataHistory,
    totalDataPoints,
    clearHistory,
    reconnect,
  } = useWebSocket();

  // Update session timer
  useEffect(() => {
    const interval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - sessionStartTime) / 1000);
      const minutes = Math.floor(elapsed / 60);
      const seconds = elapsed % 60;
      setSessionTime(`${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`);
    }, 1000);

    return () => clearInterval(interval);
  }, [sessionStartTime]);

  // Monitor for offline analysis completion and real-time data flow
  useEffect(() => {
    if (analysisMode === 'offline') {
      const checkAnalysisComplete = () => {
        // Check if we received analysis complete message
        if (dataHistory.length === 0 && totalDataPoints === 0) {
          // Show message that analysis is running
          toast({
            title: 'Offline Analysis Running',
            description: 'Processing EEG file... Results will appear when complete.',
            duration: 5000,
          });
        }
      };
      
      const timer = setTimeout(checkAnalysisComplete, 2000);
      return () => clearTimeout(timer);
    } else if (analysisMode === 'realtime') {
      // Monitor real-time data flow status
      if (dataFlowStatus?.isReceivingData && totalDataPoints > 0) {
        // We have real data flowing from EEG devices
        setLslStatus('streaming');
      } else if (lslStatus === 'connected') {
        // Connected but no data yet - this is normal, waiting for EEG device
        const noDataTimer = setTimeout(() => {
          if (!dataFlowStatus?.isReceivingData) {
            setLslStatus('error');
            toast({
              title: 'No EEG Device Detected',
              description: 'Please connect an EEG device (Muse2, X.on, OpenBCI) and start streaming.',
              variant: 'destructive',
              duration: 8000,
            });
          }
        }, 10000); // Wait 10 seconds for device connection
        
        return () => clearTimeout(noDataTimer);
      }
    }
  }, [analysisMode, dataHistory.length, totalDataPoints, dataFlowStatus?.isReceivingData, lslStatus, toast]);

  const handleExport = useCallback(() => {
    if (dataHistory.length === 0) {
      toast({
        title: 'No Data',
        description: 'No data available to export',
        variant: 'destructive',
      });
      return;
    }

    const csvContent = [
      'timestamp,valence,arousal',
      ...dataHistory.map(p => 
        `${new Date(p.timestamp).toISOString()},${p.valence},${p.arousal}`
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bci_data_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);

    toast({
      title: 'Export Successful',
      description: `Exported ${dataHistory.length} data points`,
    });
  }, [dataHistory, toast]);

  const getProgressValues = (value: number) => {
    const percent = ((value + 1) / 2) * 100;
    return {
      progressValue: percent,
      progressOffset: value < 0 ? (50 - percent) * 2 : 0,
    };
  };

  const valenceProgress = currentData ? getProgressValues(currentData.valence) : { progressValue: 50, progressOffset: 0 };
  const arousalProgress = currentData ? getProgressValues(currentData.arousal) : { progressValue: 50, progressOffset: 0 };

  return (
    <div className="min-h-screen flex bg-primary-dark">
      <Sidebar connectionStatus={connectionStatus} dataFlowStatus={dataFlowStatus} />
      
      <div className="flex-1 overflow-auto">
        {/* Return to Home Button */}
        <div className="p-4 border-b border-gray-700">
          <button
            onClick={() => setLocation('/')}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors"
          >
            <Home size={16} />
            <span>Return to Home</span>
          </button>
        </div>
        
        <Header
          onExport={handleExport}
          refreshRate={refreshRate}
          onRefreshRateChange={setRefreshRate}
        />

        <main className="p-6">
          {/* Current Metrics Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-6 animate-fade-in">
            <MetricCard
              title="Valence"
              value={currentData?.valence.toFixed(2) || '0.00'}
              icon={<Smile size={20} />}
              color="text-accent-cyan"
              subtitle="Range: -1.00 to +1.00"
              showProgress
              progressValue={valenceProgress.progressValue}
              progressOffset={valenceProgress.progressOffset}
            />

            <MetricCard
              title="Arousal"
              value={currentData?.arousal.toFixed(2) || '0.00'}
              icon={<Zap size={20} />}
              color="text-accent-orange"
              subtitle="Range: -1.00 to +1.00"
              showProgress
              progressValue={arousalProgress.progressValue}
              progressOffset={arousalProgress.progressOffset}
            />

            <MetricCard
              title="IIT Φ"
              value={currentData?.phi !== undefined ? currentData.phi.toFixed(4) : 'Computing'}
              icon={<Brain size={20} />}
              color="text-purple-400"
              subtitle="IIT Φ Index"
            />

            <MetricCard
              title={analysisMode === 'offline' ? 'Windows Processed' : 'Data Points'}
              value={totalDataPoints}
              icon={<Database size={20} />}
              color="text-accent-green"
              subtitle={analysisMode === 'offline' ? 'File analysis complete' : 'Total received'}
            />

            <MetricCard
              title="Session Time"
              value={sessionTime}
              icon={<Clock size={20} />}
              color="text-secondary-light"
              subtitle="Active monitoring"
            />
          </div>

          {/* Analysis Status */}
          {analysisMode === 'offline' ? (
            <div className="mb-6 animate-slide-up">
              <div className="bg-gray-800/50 border border-blue-500/30 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Brain className="h-5 w-5 text-blue-400" />
                    <span className="text-white font-medium">Offline Analysis Mode</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="h-2 w-2 bg-blue-400 rounded-full animate-pulse"></div>
                    <span className="text-blue-400 text-sm">
                      {totalDataPoints > 0 ? 'Analysis Complete' : 'Processing...'}
                    </span>
                  </div>
                </div>
                {totalDataPoints > 0 && (
                  <div className="mt-3 text-gray-300 text-sm">
                    File analysis completed successfully. {totalDataPoints} time windows were processed.
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="mb-6 animate-slide-up">
              <div className="bg-gray-800/50 border border-green-500/30 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Zap className="h-5 w-5 text-green-400" />
                    <span className="text-white font-medium">Real-time LSL Stream</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className={`h-2 w-2 rounded-full ${
                      lslStatus === 'streaming' ? 'bg-green-400' :
                      lslStatus === 'connected' ? 'bg-yellow-400' :
                      lslStatus === 'connecting' || lslStatus === 'retrying' ? 'bg-blue-400 animate-pulse' :
                      'bg-red-400'
                    }`}></div>
                    <span className={`text-sm ${
                      lslStatus === 'streaming' ? 'text-green-400' :
                      lslStatus === 'connected' ? 'text-yellow-400' :
                      lslStatus === 'connecting' || lslStatus === 'retrying' ? 'text-blue-400' :
                      'text-red-400'
                    }`}>
                      {lslStatus === 'streaming' ? 'Streaming Data' :
                       lslStatus === 'connected' ? 'Connected' :
                       lslStatus === 'connecting' ? 'Connecting...' :
                       lslStatus === 'retrying' ? 'Retrying...' :
                       lslStatus === 'error' ? 'Connection Error' :
                       'Disconnected'}
                    </span>
                  </div>
                </div>
                <div className="mt-3 text-gray-300 text-sm">
                  {lslStatus === 'streaming' ? 'EEG data streaming at 256Hz with auto-reconnect enabled.' :
                   lslStatus === 'connected' ? 'LSL stream connected. Waiting for data...' :
                   lslStatus === 'connecting' || lslStatus === 'retrying' ? 'Searching for EEG devices on Lab Streaming Layer...' :
                   lslStatus === 'error' ? 'Unable to connect to LSL stream. Check your EEG device.' :
                   'No LSL EEG stream detected. Ensure your device is streaming.'}
                </div>
              </div>
            </div>
          )}

          {/* Main Visualization Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6 animate-slide-up">
            <VAPlane
              currentData={currentData}
              dataHistory={dataHistory}
              onClear={clearHistory}
            />

            <TimeSeriesChart
              dataHistory={dataHistory}
              timeRange={timeRange}
              onTimeRangeChange={setTimeRange}
            />
          </div>

          {/* Training Progress */}
          <div className="animate-slide-up mb-6">
            <TrainingProgress />
          </div>

          {/* Statistics and Debug Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-slide-up">
            <StatisticsPanel dataHistory={dataHistory} />
            <DebugConsole connectionStatus={connectionStatus} />
          </div>
        </main>
      </div>
    </div>
  );
}
