import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BciDataPoint, BciStats } from '@/types/bci';

interface StatisticsPanelProps {
  dataHistory: BciDataPoint[];
}

export function StatisticsPanel({ dataHistory }: StatisticsPanelProps) {
  const statistics = useMemo(() => {
    if (dataHistory.length === 0) {
      const emptyStats = {
        mean: 0,
        stdDev: 0,
        range: 0,
        min: 0,
        max: 0,
      };
      return {
        valence: emptyStats,
        arousal: emptyStats,
      };
    }

    const valences = dataHistory.map((p) => p.valence);
    const arousals = dataHistory.map((p) => p.arousal);

    const calculateStats = (values: number[]) => {
      const mean = values.reduce((a, b) => a + b) / values.length;
      const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
      const stdDev = Math.sqrt(variance);
      const min = Math.min(...values);
      const max = Math.max(...values);
      const range = max - min;

      return { mean, stdDev, range, min, max };
    };

    return {
      valence: calculateStats(valences),
      arousal: calculateStats(arousals),
    };
  }, [dataHistory]);

  const StatItem = ({ label, value }: { label: string; value: number }) => (
    <div className="bg-surface rounded-lg p-3 text-center">
      <div className="text-xs text-muted-light">{label}</div>
      <div className="font-mono font-semibold text-primary-light">
        {value.toFixed(2)}
      </div>
    </div>
  );

  return (
    <Card className="bg-secondary-dark">
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-primary-light">
          Statistical Summary
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <h3 className="text-sm font-medium text-secondary-light mb-3">
            Valence Statistics
          </h3>
          <div className="grid grid-cols-3 gap-4">
            <StatItem label="Mean" value={statistics.valence.mean} />
            <StatItem label="Std Dev" value={statistics.valence.stdDev} />
            <StatItem label="Range" value={statistics.valence.range} />
          </div>
        </div>

        <div>
          <h3 className="text-sm font-medium text-secondary-light mb-3">
            Arousal Statistics
          </h3>
          <div className="grid grid-cols-3 gap-4">
            <StatItem label="Mean" value={statistics.arousal.mean} />
            <StatItem label="Std Dev" value={statistics.arousal.stdDev} />
            <StatItem label="Range" value={statistics.arousal.range} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
