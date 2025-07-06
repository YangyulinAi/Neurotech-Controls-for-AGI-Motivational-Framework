# 脑电波情绪预测系统 | EEG Emotion Prediction System

基于机器学习的综合性脑电波情绪预测平台，可以实时分析脑电信号并预测情绪。系统使用CNN-TCN神经网络从SET格式的脑电数据中预测效价(valence)和唤醒度(arousal)。

![系统界面](generated-icon.png)

## 🚀 功能特点

- **实时情绪分析**: 从脑电数据实时预测效价和唤醒度
- **机器学习管道**: 基于CNN-TCN模型训练的情绪预测系统
- **交互式界面**: 现代化React界面，支持实时可视化
- **SET格式支持**: 兼容EEGLAB SET文件格式
- **受试者组织**: 按受试者组织训练数据和情绪标签
- **模型训练**: 完整的自定义情绪预测模型训练流程

## 📋 系统要求

安装前请确保系统已安装以下软件：

- **Node.js** (v18或更高) - [下载地址](https://nodejs.org/)
- **Python** (3.8或更高) - [下载地址](https://python.org/)
- **Git** - [下载地址](https://git-scm.com/)

## 🔧 安装步骤

### 1. 克隆项目

```bash
git clone <repository-url>
cd eeg-emotion-prediction
```

### 2. 安装Node.js依赖

```bash
npm install
```

### 3. 安装Python依赖

```bash
pip install -r python-requirements.txt
```

或使用conda：

```bash
conda create -n eeg-emotion python=3.11
conda activate eeg-emotion
pip install -r python-requirements.txt
```

### 4. 配置训练数据（可选）

如果您有自己的脑电数据，请按以下结构组织：

```
data/training set/
├── s1/
│   ├── labels.json
│   └── *.set 文件
├── s2/
│   ├── labels.json
│   └── *.set 文件
└── ...
```

每个 `labels.json` 应包含情绪标签：

```json
{
  "filename1.set": {"valence": 0.5, "arousal": 0.7},
  "filename2.set": {"valence": -0.3, "arousal": 0.2}
}
```

## 🚀 一键部署启动

### 方式1: 自动化安装（推荐）

**Ubuntu/Linux (端口4000):**
```bash
chmod +x setup.sh start-ubuntu.sh
./setup.sh           # 安装所有依赖
./start-ubuntu.sh     # 启动系统（端口4000）
```

**Windows (端口5000):**
```cmd
setup.bat             # 安装所有依赖
start-windows.bat     # 启动系统（端口5000）
```

**Windows Python方式（推荐）:**
```cmd
python start-python-windows.py  # Python方式启动（自动处理依赖）

# 可选：先测试系统
python test-windows.py          # Windows系统测试（可选）
```

**通用启动脚本:**
```bash
# 自动检测系统类型和端口
./setup.sh
./start.sh            # Ubuntu使用4000端口，Windows/macOS使用5000端口
```

### 方式2: 手动安装

```bash
npm install
pip install -r python-requirements.txt
PORT=4000 npm run dev  # Ubuntu
PORT=5000 npm run dev  # Windows
```

### 方式3: Docker部署

```bash
docker-compose up -d
```

## 📖 使用指南

### 1. 访问系统界面

打开浏览器访问：
```
Ubuntu: http://localhost:4000
Windows: http://localhost:5000
```

### 2. 上传训练数据

1. 在主页点击 **"上传数据文件"**
2. 选择您的SET文件并上传
3. 系统会自动将其组织到受试者文件夹中
4. 默认情绪标签会被创建（您可以稍后修改）

### 3. 上传或训练模型

**方式A: 上传预训练模型**
1. 点击 **"上传模型"**
2. 选择您的 `.onnx` 模型文件
3. 模型将替换当前模型

**方式B: 训练新模型**
1. 确保您有带有正确标签的训练数据
2. 导航到训练部分
3. 配置训练参数：
   - 训练轮数: 30 (默认)
   - 批量大小: 16 (默认)
   - 学习率: 1e-4 (默认)
   - 窗口大小: 5.0秒
   - 重叠度: 0.5 (50%)
4. 点击 **"开始训练"**
5. 在日志中监控训练进度

### 4. 分析脑电数据

1. 点击 **"选择SET文件"**
2. 从已上传的数据中选择SET文件
3. 系统将：
   - 将脑电数据处理成5秒窗口
   - 提取频谱图和差分熵特征
   - 使用训练模型进行ML推理
   - 在仪表板上显示实时预测

### 5. 监控结果

仪表板显示：
- **当前效价/唤醒度**: 最新情绪预测
- **实时图表**: 时间序列和2D情绪空间可视化
- **统计信息**: 数据点计数、会话时间和历史趋势
- **调试控制台**: 连接状态和系统日志

## 🔧 系统配置

### 端口配置

系统根据操作系统自动选择端口：
- **Ubuntu/Linux**: 4000端口
- **Windows/macOS**: 5000端口

### 环境变量

创建 `.env` 文件：

```env
NODE_ENV=development
PORT=4000           # Ubuntu
# PORT=5000         # Windows
PYTHON_PATH=/usr/bin/python3
MODEL_PATH=./model/va_regressor.onnx
```

### 训练参数

在网页界面或脚本中修改训练设置：

```python
# 在 train/train_labeled.py 中
parser.add_argument('--epochs', type=int, default=30)
parser.add_argument('--batch_size', type=int, default=16)
parser.add_argument('--lr', type=float, default=1e-4)
parser.add_argument('--window_size', type=float, default=5.0)
parser.add_argument('--overlap', type=float, default=0.5)
```

## 📁 项目结构

```
├── client/                 # React前端应用
├── server/                 # Express后端服务器
├── src/                   # Python ML推理模块
├── train/                 # 模型训练模块
├── data/                  # 训练数据（按受试者组织）
├── model/                 # 训练好的模型
└── analyze_set_file.py    # 主要分析脚本
```

## 🐛 常见问题解决

### Ubuntu系统

**1. 端口4000被占用**
```bash
sudo lsof -i :4000
sudo kill -9 <PID>
```

**2. Python依赖问题**
```bash
sudo apt update
sudo apt install python3-pip
pip3 install -r python-requirements.txt
```

**3. Node.js权限问题**
```bash
sudo chown -R $USER:$USER ~/.npm
```

### Windows系统

**1. 端口5000被占用**
```cmd
netstat -ano | findstr :5000
taskkill /F /PID <PID>
```

**2. PowerShell执行策略**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**3. Python路径问题**
```cmd
where python
# 确保Python在PATH中
```

### 通用问题

**WebSocket连接失败**
- 检查服务器是否在正确端口运行
- 验证防火墙设置
- 尝试刷新浏览器

**分析无法启动**
- 确保SET文件格式正确
- 检查Python路径设置
- 验证模型文件存在

## 🔄 更新和维护

### 更新系统

```bash
git pull origin main
npm install
pip install -r python-requirements.txt
```

### 备份重要数据

定期备份：
- 训练数据: `data/training set/`
- 训练模型: `model/`
- 训练检查点: `model_training/`

## 📞 技术支持

如需技术支持或有疑问：
- 在仓库中创建issue
- 查看上述故障排除部分
- 检查系统日志获取错误详情

---

**系统使用 ❤️ 构建，基于 React、Node.js、Python 和 PyTorch**