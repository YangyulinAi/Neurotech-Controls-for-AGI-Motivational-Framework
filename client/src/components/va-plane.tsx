import { useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Circle } from 'lucide-react';
import { BciDataPoint } from '@/types/bci';

interface VAPlaneProps {
  currentData: BciDataPoint | null;
  dataHistory: BciDataPoint[];
  onClear: () => void;
}

export function VAPlane({ currentData, dataHistory, onClear }: VAPlaneProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    drawVAPlane(ctx, canvas, currentData, dataHistory);
  }, [currentData, dataHistory]);

  const drawVAPlane = (
    ctx: CanvasRenderingContext2D,
    canvas: HTMLCanvasElement,
    current: BciDataPoint | null,
    history: BciDataPoint[]
  ) => {
    const width = canvas.width;
    const height = canvas.height;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Background
    ctx.fillStyle = '#1E1E1E';
    ctx.fillRect(0, 0, width, height);

    // Grid lines
    ctx.strokeStyle = '#4A4A4A';
    ctx.lineWidth = 1;

    // Vertical lines
    for (let i = 0; i <= 4; i++) {
      const x = (i / 4) * width;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }

    // Horizontal lines
    for (let i = 0; i <= 4; i++) {
      const y = (i / 4) * height;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    // Center axes (thicker)
    ctx.strokeStyle = '#00BCD4';
    ctx.lineWidth = 2;

    // Vertical center line
    ctx.beginPath();
    ctx.moveTo(width / 2, 0);
    ctx.lineTo(width / 2, height);
    ctx.stroke();

    // Horizontal center line
    ctx.beginPath();
    ctx.moveTo(0, height / 2);
    ctx.lineTo(width, height / 2);
    ctx.stroke();

    // Labels
    ctx.fillStyle = '#B0B0B0';
    ctx.font = '12px Inter';
    
    // Valence axis labels (horizontal)
    ctx.textAlign = 'center';
    ctx.fillText('-1', 40, height / 2 + 20);
    ctx.fillText('+1', width - 40, height / 2 + 20);
    ctx.fillText('Valence', width / 2, height - 15);

    // Arousal axis labels (vertical)
    ctx.fillText('+1', width / 2 - 30, 20);
    ctx.fillText('-1', width / 2 - 30, height - 10);
    
    // Rotated arousal axis label
    ctx.save();
    ctx.translate(15, height / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = 'center';
    ctx.fillText('Arousal', 0, 0);
    ctx.restore();

    // Draw historical trail points (smaller, faded)
    const trailPoints = history.slice(-20);
    trailPoints.forEach((point, index) => {
      const alpha = (index + 1) / 20 * 0.5;
      const x = (point.valence + 1) / 2 * width;
      const y = (1 - (point.arousal + 1) / 2) * height;

      ctx.fillStyle = `rgba(0, 188, 212, ${alpha})`;
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, Math.PI * 2);
      ctx.fill();
    });

    // Draw current point (larger, bright)
    if (current) {
      const x = (current.valence + 1) / 2 * width;
      const y = (1 - (current.arousal + 1) / 2) * height;

      // Glow effect
      ctx.shadowColor = '#00BCD4';
      ctx.shadowBlur = 15;
      ctx.fillStyle = '#00BCD4';
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;

      // Main point
      ctx.fillStyle = '#00BCD4';
      ctx.beginPath();
      ctx.arc(x, y, 8, 0, Math.PI * 2);
      ctx.fill();
    }
  };

  return (
    <Card className="bg-secondary-dark">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold text-primary-light">
            Valence-Arousal Plane
          </CardTitle>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onClear}
              className="text-xs bg-surface hover:bg-border"
            >
              Clear
            </Button>
            <Circle className="w-3 h-3 text-accent-cyan animate-pulse" fill="currentColor" />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex justify-center">
          <canvas
            ref={canvasRef}
            width={400}
            height={400}
            className="va-canvas border border-surface rounded-lg"
          />
        </div>

        {/* Quadrant Labels */}
        <div className="grid grid-cols-2 gap-4 mt-4 text-xs">
          <div className="text-center p-2 bg-surface rounded">
            <div className="font-semibold text-accent-green">High Arousal</div>
            <div className="text-muted-light">Excited • Alert</div>
          </div>
          <div className="text-center p-2 bg-surface rounded">
            <div className="font-semibold text-accent-cyan">Positive</div>
            <div className="text-muted-light">Happy • Pleasant</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
