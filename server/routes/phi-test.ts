import express from 'express';
import { spawn } from 'child_process';
import path from 'path';

const router = express.Router();

// IIT Φ 快速测试 API
router.post('/test-phi', async (req, res) => {
  try {
    const { method = 'mock', maxChannels = 8, testSamples = 4 } = req.body;
    
    console.log(`Starting Φ test: method=${method}, channels=${maxChannels}, samples=${testSamples}`);
    
    // 创建测试脚本
    const testScript = `
import sys
import os
import torch
import numpy as np
import json

# 添加 src 目录到路径
sys.path.append('src')

try:
    from phi_estimator import PhiEstimator
    
    # 创建计算器
    estimator = PhiEstimator(
        method='${method}',
        max_channels=${maxChannels}
    )
    
    # 生成测试数据 (batch, channels, time)
    test_data = torch.randn(${testSamples}, ${maxChannels}, 256)
    
    # 计算 Φ 值
    phi_values = estimator.compute(test_data)
    
    # 输出结果
    result = {
        'success': True,
        'method': '${method}',
        'maxChannels': ${maxChannels},
        'testSamples': ${testSamples},
        'phiValues': phi_values.tolist(),
        'avgPhi': phi_values.mean().item(),
        'minPhi': phi_values.min().item(),
        'maxPhi': phi_values.max().item(),
        'estimatorInfo': estimator.get_info()
    }
    
    print(json.dumps(result))
    
except Exception as e:
    error_result = {
        'success': False,
        'error': str(e),
        'method': '${method}',
        'maxChannels': ${maxChannels}
    }
    print(json.dumps(error_result))
`;

    // 写入临时脚本文件
    const scriptPath = path.join(process.cwd(), 'temp_phi_test.py');
    require('fs').writeFileSync(scriptPath, testScript);
    
    // 执行 Python 脚本
    const pythonProcess = spawn('python3', [scriptPath], {
      cwd: process.cwd(),
      stdio: ['pipe', 'pipe', 'pipe']
    });
    
    let output = '';
    let errorOutput = '';
    
    pythonProcess.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    pythonProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });
    
    pythonProcess.on('close', (code) => {
      // 清理临时文件
      try {
        require('fs').unlinkSync(scriptPath);
      } catch (err) {
        console.warn('Failed to clean up temp script:', err);
      }
      
      if (code === 0) {
        try {
          const result = JSON.parse(output.trim());
          if (result.success) {
            res.json(result);
          } else {
            res.status(500).json({ 
              error: 'Φ calculation failed', 
              details: result.error 
            });
          }
        } catch (parseError) {
          console.error('Failed to parse Python output:', output);
          res.status(500).json({ 
            error: 'Failed to parse test results',
            output: output,
            stderr: errorOutput
          });
        }
      } else {
        console.error('Python script failed:', errorOutput);
        res.status(500).json({ 
          error: 'Python script execution failed',
          code: code,
          stderr: errorOutput,
          stdout: output
        });
      }
    });
    
    // 设置超时
    setTimeout(() => {
      pythonProcess.kill();
      res.status(408).json({ error: 'Φ test timeout' });
    }, 30000); // 30 秒超时
    
  } catch (error) {
    console.error('Φ test error:', error);
    res.status(500).json({ 
      error: 'Internal server error', 
      details: error.message 
    });
  }
});

export default router;