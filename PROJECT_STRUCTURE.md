# 脑电波情绪预测系统 - 项目结构

## 核心目录结构

```
├── client/                 # React前端应用
│   ├── src/
│   │   ├── components/     # UI组件
│   │   ├── hooks/         # React hooks
│   │   ├── pages/         # 页面组件
│   │   └── types/         # TypeScript类型定义
│   └── index.html
├── server/                 # Express后端服务器
│   ├── index.ts           # 服务器入口
│   ├── routes.ts          # API路由
│   ├── storage.ts         # 数据存储
│   └── vite.ts           # Vite集成
├── src/                   # Python ML推理模块
│   ├── onnx_runner.py     # ONNX模型推理
│   ├── preprocess.py      # 信号预处理
│   ├── lsl_receiver.py    # LSL数据接收
│   └── utils/             # 工具函数
├── train/                 # 模型训练模块
│   ├── train_labeled.py   # 有监督训练脚本
│   ├── model_cnn_tcn.py   # CNN-TCN模型定义
│   ├── dataset_set.py     # SET文件数据集
│   └── export_onnx.py     # 模型导出
├── data/                  # 训练数据
│   └── training set/      # 按受试者组织的SET文件
│       ├── s1/           # 受试者1数据
│       ├── s2/           # 受试者2数据
│       └── ...
├── model/                 # 训练好的模型
│   └── va_regressor.onnx  # 情绪预测ONNX模型
├── model_training/        # 训练检查点
│   └── ckpt.pt           # PyTorch模型权重
├── tests/                 # 测试文件
└── analyze_set_file.py    # SET文件分析脚本
```

## 数据流

1. **训练数据准备**: SET文件 + labels.json → 训练集
2. **模型训练**: 训练集 → PyTorch模型 → ONNX导出
3. **实时分析**: SET文件 → 特征提取 → ONNX推理 → 前端显示

## 关键文件说明

- `analyze_set_file.py`: 主要分析脚本，处理SET文件并进行ML推理
- `train/train_labeled.py`: 使用真实情绪标签进行有监督学习
- `server/routes.ts`: API端点，包括文件上传和分析控制
- `client/src/hooks/use-websocket.ts`: 前端WebSocket通信
- `src/onnx_runner.py`: ONNX模型推理引擎
- `data/training set/*/labels.json`: 每个受试者的情绪标签

## 技术栈

- **前端**: React + TypeScript + TailwindCSS + Vite
- **后端**: Node.js + Express + TypeScript
- **ML**: Python + PyTorch + ONNX Runtime + NumPy + SciPy
- **通信**: WebSocket + REST API + HTTP POST
- **数据**: EEGLAB SET格式 + JSON标签