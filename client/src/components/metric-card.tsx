import { ReactNode } from 'react';
import { Card, CardContent } from '@/components/ui/card';

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: ReactNode;
  color: string;
  subtitle?: string;
  showProgress?: boolean;
  progressValue?: number;
  progressOffset?: number;
}

export function MetricCard({
  title,
  value,
  icon,
  color,
  subtitle,
  showProgress = false,
  progressValue = 0,
  progressOffset = 0,
}: MetricCardProps) {
  return (
    <Card className="bg-secondary-dark data-card">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-secondary-light">{title}</h3>
          <div className={`${color}`}>{icon}</div>
        </div>
        <div className="text-2xl font-bold font-mono metric-value text-primary-light break-words">
          {value}
        </div>
        {subtitle && (
          <div className="text-xs text-muted-light mt-2">{subtitle}</div>
        )}
        {showProgress && (
          <div className="mt-3 h-2 bg-surface rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-300 ${color.replace('text-', 'bg-')}`}
              style={{
                width: `${Math.abs(progressValue - 50) * 2}%`,
                transform: `translateX(${progressOffset}%)`,
              }}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
