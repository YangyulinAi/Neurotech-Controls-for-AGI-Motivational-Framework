import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ConnectionStatus } from '@/types/bci';

interface DebugConsoleProps {
  connectionStatus: ConnectionStatus;
}

export function DebugConsole({ connectionStatus }: DebugConsoleProps) {
  return (
    <Card className="bg-secondary-dark">
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-primary-light">
          Connection Status
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="bg-primary-dark rounded-lg p-4 h-64 flex items-center justify-center">
          <div className="text-center">
            <div className={`text-2xl mb-4 ${
              connectionStatus.connected ? 'text-accent-green' : 'text-accent-orange'
            }`}>
              {connectionStatus.connected ? '● Connected' : '○ Disconnected'}
            </div>
            <div className="text-muted-light text-sm">
              WebSocket Status: {connectionStatus.connected ? 'Active' : 'Waiting for connection'}
            </div>
            {connectionStatus.error && (
              <div className="text-accent-orange text-xs mt-2">
                Error: {connectionStatus.error}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
