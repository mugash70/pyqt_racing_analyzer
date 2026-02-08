# HKJC Race Analysis - PyQt Edition

**Native Python GUI for horse racing prediction and analysis**

This is a **separate PyQt implementation** of the racing analysis UI that matches the Electron.js styling but runs as a **native Python application** with **direct ML integration**.

## 🚀 Key Features

- ✅ **Single Executable**: No external dependencies required
- ✅ **Direct ML Integration**: No Flask API needed
- ✅ **Native Performance**: Faster than web-based Electron
- ✅ **Professional UI**: Matches Electron.js design
- ✅ **Real-time Analysis**: Live ML predictions with demo fallback
- ✅ **Cross-platform**: Works on Windows, macOS, Linux

## 🏗️ Architecture

```
pyqt_racing_analyzer/
├── main.py              # Main PyQt tabbed application
├── ml/
│   └── ml_service.py    # Direct ML model integration
├── ui/
│   ├── race_overview.py # Race header component
│   ├── contenders_matrix.py # Analysis table with probability bars
│   ├── icons.py         # Professional SVG icons (no emojis)
│   └── styles.py        # Electron-matching dark theme
├── requirements.txt     # Python dependencies
├── build.py            # PyInstaller build script
└── README.md           # This file
```

## 📦 Installation

1. **Install Dependencies**
```bash
cd pyqt_racing_analyzer
pip install -r requirements.txt
```

2. **Train ML Model** (if not already done)
```bash
cd ..
python train_ml_model.py --days 30
```

## 🎯 Usage

### Development Mode
```bash
cd pyqt_racing_analyzer
python main.py
```

### Production Build
```bash
python build.py
```

This creates a single executable in `dist/HKJC_Race_Analysis`

## 🎨 UI Features

### Race Overview Dashboard
```
🏆 CONSENSUS PICK: Horse X (32% confidence)
📊 MARKET VIEW: Favorite 4/1 | Longshot 50/1
⚡ PACE SETUP: Fast pace predicted
```

### Win Analysis Matrix
```
┌────────────────┬─────────┬─────────┬─────────┬─────────┐
│    HORSE       │  MODEL  │  ODDS   │  VALUE  │  EDGE   │
├────────────────┼─────────┼─────────┼─────────┼─────────┤
│ 1. Iron Dragon│  32%    │  3.8    │  +8%    │  HIGH   │
│ 2. Lucky Star │  18%    │  6.5    │  +4%    │  MEDIUM │
└────────────────┴─────────┴─────────┴─────────┴─────────┘
```

### Probability Distribution
```
WIN PROBABILITY HEATMAP
1️⃣ Iron Dragon ████████████████████ 32%
2️⃣ Lucky Star ████████████ 18%
3️⃣ Others ████████████ 50%
```

## 🔧 Technical Details

### ML Integration
- **Direct Import**: ML models loaded directly in Python
- **No API Calls**: Instant predictions
- **Threaded Processing**: UI stays responsive during analysis
- **Graceful Fallback**: Demo mode when ML unavailable

### UI Components
- **PyQt5**: Professional native widgets
- **Custom Styling**: Matches Electron.js dark theme
- **Responsive Layout**: Adapts to window size
- **Status Indicators**: Real-time analysis progress

### Data Sources
- **SQLite Database**: Direct access to race data
- **ML Models**: Ensemble of XGBoost + LightGBM + Neural Network
- **Feature Engineering**: Real-time calculation from raw data

## 🚀 Deployment

### Single Executable Distribution
```bash
python build.py
# Creates: dist/HKJC_Race_Analysis (single file)
```

### What Gets Included
- ✅ **ML Models**: Trained ensemble models
- ✅ **Race Database**: Historical race data
- ✅ **Python Runtime**: Embedded interpreter
- ✅ **All Dependencies**: No external requirements

### Distribution Size
- **Development**: ~200MB (with source)
- **Production**: ~80MB (single executable + data)

## 🔄 Comparison with Electron Version

| Feature | Electron.js | PyQt (This Version) |
|---------|-------------|-------------------|
| **Deployment** | 2 processes | Single executable |
| **Performance** | Web-based | Native speed |
| **Dependencies** | Node.js + Python | Python only |
| **UI Responsiveness** | Good | Excellent |
| **File Size** | ~150MB | ~80MB |
| **Platform Native** | Web wrapper | True native |

## 🐛 Troubleshooting

### ML Model Not Found
```bash
# Train model first
cd ..
python train_ml_model.py --days 30
```

### Missing Dependencies
```bash
pip install PyQt5 pandas numpy scikit-learn xgboost lightgbm pyinstaller
```

### Build Issues
- Ensure all ML models are trained
- Check database file exists
- Use Python 3.8+ for best compatibility

## 🎊 Result

You now have **two complete implementations**:

1. **Electron.js Version**: Web-based, easy development, multi-process
2. **PyQt Version**: Native Python GUI, single executable, direct ML integration

Both provide the same professional racing analysis experience but with different deployment characteristics.

**Choose PyQt for simplified deployment and native performance!**