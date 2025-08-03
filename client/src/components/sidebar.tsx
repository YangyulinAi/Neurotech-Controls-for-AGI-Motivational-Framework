import { Brain, ChartLine, History, Download, Settings, Circle } from 'lucide-react';
import { ConnectionStatus } from '@/types/bci';

interface SidebarProps {
  connectionStatus: ConnectionStatus;
}

export function Sidebar({ connectionStatus, dataFlowStatus }: SidebarProps & { dataFlowStatus?: any }) {
  return (
    <div className="w-64 bg-secondary-dark border-r border-surface p-6 hidden lg:block">
      <div className="flex items-center mb-8">
        <div className="w-8 h-8 bg-accent-cyan rounded-lg flex items-center justify-center mr-3">
          <Brain className="text-primary-dark text-sm" size={16} />
        </div>
        <h1 className="text-xl font-semibold text-primary-light">BCI Monitor</h1>
      </div>

      <nav className="space-y-2">
        <a
          href="#"
          className="flex items-center px-4 py-3 text-primary-light bg-surface rounded-lg"
        >
          <ChartLine className="mr-3 text-accent-cyan" size={16} />
          Real-time Data
        </a>
        <a
          href="#"
          className="flex items-center px-4 py-3 text-secondary-light hover:text-primary-light hover:bg-surface rounded-lg transition-colors"
        >
          <History className="mr-3" size={16} />
          Historical Analysis
        </a>
        <a
          href="#"
          className="flex items-center px-4 py-3 text-secondary-light hover:text-primary-light hover:bg-surface rounded-lg transition-colors"
        >
          <Download className="mr-3" size={16} />
          Export Data
        </a>
        <a
          href="#"
          className="flex items-center px-4 py-3 text-secondary-light hover:text-primary-light hover:bg-surface rounded-lg transition-colors"
        >
          <Settings className="mr-3" size={16} />
          Settings
        </a>
      </nav>

      {/* Connection Status */}
      <div className="mt-8 p-4 bg-surface rounded-lg">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-secondary-light">System Status</span>
          <Circle
            className={`w-3 h-3 rounded-full ${
              connectionStatus.connected && dataFlowStatus?.isReceivingData
                ? 'text-accent-green connection-pulse'
                : connectionStatus.connected && !dataFlowStatus?.isReceivingData  
                ? 'text-accent-orange'
                : connectionStatus.error
                ? 'text-accent-red'
                : 'text-muted-light'
            }`}
            fill="currentColor"
          />
        </div>
        <div className="text-xs text-muted-light space-y-1">
          <div>
            WebSocket:{' '}
            <span
              className={
                connectionStatus.connected
                  ? 'text-accent-green'
                  : connectionStatus.error
                  ? 'text-accent-orange'
                  : 'text-muted-light'
              }
            >
              {connectionStatus.connected
                ? 'Connected'
                : connectionStatus.error
                ? 'Error'
                : 'Disconnected'}
            </span>
          </div>
          <div>
            Data Flow:{' '}
            <span
              className={
                dataFlowStatus?.isReceivingData
                  ? 'text-accent-green'
                  : dataFlowStatus?.analysisActive
                  ? 'text-accent-yellow'
                  : 'text-accent-red'
              }
            >
              {dataFlowStatus?.isReceivingData
                ? 'Active'
                : dataFlowStatus?.analysisActive
                ? 'Processing'
                : 'No Data'}
            </span>
          </div>
          <div>
            Last Data:{' '}
            <span>
              {dataFlowStatus?.lastDataTime
                ? dataFlowStatus.lastDataTime.toLocaleTimeString()
                : '--:--:--'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
