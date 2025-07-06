import { Menu, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface HeaderProps {
  onExport: () => void;
  refreshRate: number;
  onRefreshRateChange: (rate: number) => void;
}

export function Header({ onExport, refreshRate, onRefreshRateChange }: HeaderProps) {
  return (
    <header className="bg-secondary-dark border-b border-surface p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-primary-light">
            BCI Emotional State Monitor
          </h1>
          <p className="text-secondary-light mt-1">
            Real-time valence and arousal tracking
          </p>
        </div>
        <div className="flex items-center space-x-4">
          {/* Mobile menu button */}
          <Button
            variant="outline"
            size="icon"
            className="lg:hidden bg-surface"
          >
            <Menu className="h-4 w-4" />
          </Button>

          {/* Refresh Rate Selector */}
          <Select
            value={refreshRate.toString()}
            onValueChange={(value) => onRefreshRateChange(parseInt(value))}
          >
            <SelectTrigger className="w-24 bg-surface border-surface text-sm">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="100">100ms</SelectItem>
              <SelectItem value="500">500ms</SelectItem>
              <SelectItem value="1000">1s</SelectItem>
            </SelectContent>
          </Select>

          {/* Export Button */}
          <Button
            onClick={onExport}
            className="bg-accent-cyan hover:bg-accent-cyan/80 text-primary-dark"
          >
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </div>
      </div>
    </header>
  );
}
