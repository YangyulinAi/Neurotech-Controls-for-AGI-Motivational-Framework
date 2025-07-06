import { useState, useEffect, useCallback } from 'react';
import { Smile, Zap, Database, Clock } from 'lucide-react';
import { Sidebar } from '@/components/sidebar';
import { Header } from '@/components/header';
import { MetricCard } from '@/components/metric-card';
import { VAPlane } from '@/components/va-plane';
import { TimeSeriesChart } from '@/components/time-series-chart';
import { StatisticsPanel } from '@/components/statistics-panel';
import { DebugConsole } from '@/components/debug-console';
import { useWebSocket } from '@/hooks/use-websocket';
import { useToast } from '@/hooks/use-toast';

export default function Dashboard() {
  const [refreshRate, setRefreshRate] = useState(500);
  const [timeRange, setTimeRange] = useState(60);
  const [sessionStartTime] = useState(Date.now());
  const [sessionTime, setSessionTime] = useState('00:00');

  const { toast } = useToast();
  
  const {
    connectionStatus,
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
      <Sidebar connectionStatus={connectionStatus} />
      
      <div className="flex-1 overflow-auto">
        <Header
          onExport={handleExport}
          refreshRate={refreshRate}
          onRefreshRateChange={setRefreshRate}
        />

        <main className="p-6">
          {/* Current Metrics Row */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6 animate-fade-in">
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
              title="Data Points"
              value={totalDataPoints}
              icon={<Database size={20} />}
              color="text-accent-green"
              subtitle="Total received"
            />

            <MetricCard
              title="Session Time"
              value={sessionTime}
              icon={<Clock size={20} />}
              color="text-secondary-light"
              subtitle="Active monitoring"
            />
          </div>

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
