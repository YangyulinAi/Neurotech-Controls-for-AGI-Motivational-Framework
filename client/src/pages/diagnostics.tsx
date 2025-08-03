import { useState } from 'react';
import { ArrowLeft, Play, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { useLocation } from 'wouter';

interface DiagnosticResult {
  success: boolean;
  exitCode: number;
  output: string;
  errors: string;
  timestamp: string;
}

export default function Diagnostics() {
  const [, setLocation] = useLocation();
  const [productionResult, setProductionResult] = useState<DiagnosticResult | null>(null);
  const [backendResult, setBackendResult] = useState<DiagnosticResult | null>(null);
  const [loading, setLoading] = useState<{production: boolean, backend: boolean}>({
    production: false,
    backend: false
  });

  const runProductionCheck = async () => {
    setLoading(prev => ({ ...prev, production: true }));
    try {
      const response = await fetch('/api/diagnostic/production-check');
      const result = await response.json();
      setProductionResult(result);
    } catch (error) {
      setProductionResult({
        success: false,
        exitCode: -1,
        output: '',
        errors: `Failed to run diagnostic: ${error}`,
        timestamp: new Date().toISOString()
      });
    } finally {
      setLoading(prev => ({ ...prev, production: false }));
    }
  };

  const runBackendTest = async () => {
    setLoading(prev => ({ ...prev, backend: true }));
    try {
      const response = await fetch('/api/diagnostic/backend-test');
      const result = await response.json();
      setBackendResult(result);
    } catch (error) {
      setBackendResult({
        success: false,
        exitCode: -1,
        output: '',
        errors: `Failed to run test: ${error}`,
        timestamp: new Date().toISOString()
      });
    } finally {
      setLoading(prev => ({ ...prev, backend: false }));
    }
  };

  const getStatusIcon = (result: DiagnosticResult | null, isLoading: boolean) => {
    if (isLoading) return <AlertCircle className="w-5 h-5 text-yellow-500 animate-spin" />;
    if (!result) return null;
    return result.success 
      ? <CheckCircle className="w-5 h-5 text-green-500" />
      : <XCircle className="w-5 h-5 text-red-500" />;
  };

  return (
    <div className="min-h-screen bg-primary-dark text-primary-light p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center mb-8">
          <button
            onClick={() => setLocation('/')}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors mr-4"
          >
            <ArrowLeft size={16} />
            <span>Back to Home</span>
          </button>
          <h1 className="text-3xl font-bold">System Diagnostics</h1>
        </div>

        {/* Description */}
        <div className="bg-surface rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Diagnostic Tools</h2>
          <p className="text-secondary-light mb-4">
            Use these tools to diagnose production environment issues and backend functionality problems.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-secondary-dark p-4 rounded-lg">
              <h3 className="font-semibold text-accent-cyan mb-2">Production Check</h3>
              <p className="text-sm text-secondary-light">
                Verifies Python modules, file paths, demo data, and environment settings
              </p>
            </div>
            <div className="bg-secondary-dark p-4 rounded-lg">
              <h3 className="font-semibold text-accent-orange mb-2">Backend Test</h3>
              <p className="text-sm text-secondary-light">
                Tests module imports, ONNX model loading, Φ estimation, and WebSocket functionality
              </p>
            </div>
          </div>
        </div>

        {/* Diagnostic Controls */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Production Check */}
          <div className="bg-surface rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold flex items-center">
                Production Environment Check
                {getStatusIcon(productionResult, loading.production)}
              </h3>
              <button
                onClick={runProductionCheck}
                disabled={loading.production}
                className="flex items-center space-x-2 px-4 py-2 bg-accent-cyan hover:bg-accent-cyan/80 disabled:bg-gray-600 text-primary-dark rounded-lg transition-colors"
              >
                <Play size={16} />
                <span>{loading.production ? 'Running...' : 'Run Check'}</span>
              </button>
            </div>
            
            {productionResult && (
              <div className="mt-4">
                <div className={`p-3 rounded-lg mb-3 ${
                  productionResult.success 
                    ? 'bg-green-900/30 border border-green-500' 
                    : 'bg-red-900/30 border border-red-500'
                }`}>
                  <div className="flex items-center justify-between">
                    <span className="font-medium">
                      {productionResult.success ? 'Check Passed' : 'Check Failed'}
                    </span>
                    <span className="text-sm text-secondary-light">
                      Exit Code: {productionResult.exitCode}
                    </span>
                  </div>
                </div>
                
                <div className="bg-secondary-dark rounded-lg p-4 overflow-auto max-h-60">
                  <h4 className="text-sm font-medium text-accent-green mb-2">Output:</h4>
                  <pre className="text-xs text-secondary-light whitespace-pre-wrap">
                    {productionResult.output || 'No output'}
                  </pre>
                  
                  {productionResult.errors && (
                    <>
                      <h4 className="text-sm font-medium text-accent-red mb-2 mt-4">Errors:</h4>
                      <pre className="text-xs text-red-400 whitespace-pre-wrap">
                        {productionResult.errors}
                      </pre>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Backend Test */}
          <div className="bg-surface rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold flex items-center">
                Backend Functionality Test
                {getStatusIcon(backendResult, loading.backend)}
              </h3>
              <button
                onClick={runBackendTest}
                disabled={loading.backend}
                className="flex items-center space-x-2 px-4 py-2 bg-accent-orange hover:bg-accent-orange/80 disabled:bg-gray-600 text-primary-dark rounded-lg transition-colors"
              >
                <Play size={16} />
                <span>{loading.backend ? 'Testing...' : 'Run Test'}</span>
              </button>
            </div>
            
            {backendResult && (
              <div className="mt-4">
                <div className={`p-3 rounded-lg mb-3 ${
                  backendResult.success 
                    ? 'bg-green-900/30 border border-green-500' 
                    : 'bg-red-900/30 border border-red-500'
                }`}>
                  <div className="flex items-center justify-between">
                    <span className="font-medium">
                      {backendResult.success ? 'Tests Passed' : 'Tests Failed'}
                    </span>
                    <span className="text-sm text-secondary-light">
                      Exit Code: {backendResult.exitCode}
                    </span>
                  </div>
                </div>
                
                <div className="bg-secondary-dark rounded-lg p-4 overflow-auto max-h-60">
                  <h4 className="text-sm font-medium text-accent-green mb-2">Output:</h4>
                  <pre className="text-xs text-secondary-light whitespace-pre-wrap">
                    {backendResult.output || 'No output'}
                  </pre>
                  
                  {backendResult.errors && (
                    <>
                      <h4 className="text-sm font-medium text-accent-red mb-2 mt-4">Errors:</h4>
                      <pre className="text-xs text-red-400 whitespace-pre-wrap">
                        {backendResult.errors}
                      </pre>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-surface rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => {
                runProductionCheck();
                runBackendTest();
              }}
              className="flex items-center justify-center space-x-2 px-4 py-3 bg-accent-green hover:bg-accent-green/80 text-primary-dark rounded-lg transition-colors"
            >
              <span>Run All Tests</span>
            </button>
            
            <button
              onClick={() => {
                setProductionResult(null);
                setBackendResult(null);
              }}
              className="flex items-center justify-center space-x-2 px-4 py-3 bg-gray-600 hover:bg-gray-500 text-primary-light rounded-lg transition-colors"
            >
              <span>Clear Results</span>
            </button>
            
            <button
              onClick={() => setLocation('/dashboard')}
              className="flex items-center justify-center space-x-2 px-4 py-3 bg-accent-cyan hover:bg-accent-cyan/80 text-primary-dark rounded-lg transition-colors"
            >
              <span>View Dashboard</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}