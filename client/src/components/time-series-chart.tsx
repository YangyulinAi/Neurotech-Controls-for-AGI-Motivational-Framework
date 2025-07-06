import { useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { BciDataPoint } from '@/types/bci';

declare global {
  interface Window {
    Chart: any;
  }
}

interface TimeSeriesChartProps {
  dataHistory: BciDataPoint[];
  timeRange: number;
  onTimeRangeChange: (range: number) => void;
}

export function TimeSeriesChart({
  dataHistory,
  timeRange,
  onTimeRangeChange,
}: TimeSeriesChartProps) {
  const chartRef = useRef<HTMLCanvasElement>(null);
  const chartInstanceRef = useRef<any>(null);

  useEffect(() => {
    // Load Chart.js dynamically
    if (typeof window !== 'undefined' && !window.Chart) {
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
      script.onload = initChart;
      document.head.appendChild(script);
    } else {
      initChart();
    }

    return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy();
      }
    };
  }, []);

  useEffect(() => {
    if (chartInstanceRef.current) {
      updateChart();
    }
  }, [dataHistory, timeRange]);

  const initChart = () => {
    if (!chartRef.current || !window.Chart) return;

    const ctx = chartRef.current.getContext('2d');
    if (!ctx) return;

    chartInstanceRef.current = new window.Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'Valence',
            data: [],
            borderColor: '#00BCD4',
            backgroundColor: 'rgba(0, 188, 212, 0.1)',
            borderWidth: 2,
            fill: false,
            tension: 0.4,
          },
          {
            label: 'Arousal',
            data: [],
            borderColor: '#FF5722',
            backgroundColor: 'rgba(255, 87, 34, 0.1)',
            borderWidth: 2,
            fill: false,
            tension: 0.4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          intersect: false,
          mode: 'index',
        },
        plugins: {
          legend: {
            labels: {
              color: '#B0B0B0',
              font: { family: 'Inter' },
            },
          },
        },
        scales: {
          x: {
            grid: { color: '#4A4A4A' },
            ticks: { color: '#B0B0B0', font: { family: 'Inter' } },
          },
          y: {
            min: -1,
            max: 1,
            grid: { color: '#4A4A4A' },
            ticks: { color: '#B0B0B0', font: { family: 'Inter' } },
          },
        },
      },
    });

    updateChart();
  };

  const updateChart = () => {
    if (!chartInstanceRef.current) return;

    const maxPoints = timeRange * 2; // Assuming 2 points per second
    const recentData = dataHistory.slice(-maxPoints);

    if (recentData.length === 0) return;

    const labels = recentData.map((_, index) => {
      const secondsAgo = (recentData.length - index - 1) * 0.5;
      return secondsAgo === 0 ? 'now' : `-${secondsAgo}s`;
    });

    chartInstanceRef.current.data.labels = labels;
    chartInstanceRef.current.data.datasets[0].data = recentData.map((p) => p.valence);
    chartInstanceRef.current.data.datasets[1].data = recentData.map((p) => p.arousal);
    chartInstanceRef.current.update('none');
  };

  return (
    <Card className="bg-secondary-dark">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold text-primary-light">
            Time Series
          </CardTitle>
          <Select
            value={timeRange.toString()}
            onValueChange={(value) => onTimeRangeChange(parseInt(value))}
          >
            <SelectTrigger className="w-32 bg-surface border-surface text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="60">Last 60s</SelectItem>
              <SelectItem value="300">Last 5min</SelectItem>
              <SelectItem value="900">Last 15min</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-80">
          <canvas ref={chartRef} />
        </div>
      </CardContent>
    </Card>
  );
}
