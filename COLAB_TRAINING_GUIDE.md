# Google Colab Training Guide

This guide explains how to use the `colab_train_models.ipynb` notebook to train your trading models in Google Colab.

## 📋 Prerequisites

1. Google account with access to Google Colab
2. Delta Exchange API credentials (API Key and API Secret)
3. Your project files ready to upload (as ZIP) or hosted on GitHub

## 🚀 Getting Started

### Step 1: Open the Notebook in Google Colab

1. Go to [Google Colab](https://colab.research.google.com/)
2. Click **File → Upload notebook**
3. Upload `colab_train_models.ipynb`
4. Alternatively, if your project is on GitHub, you can open it directly from there

### Step 2: Prepare Your Project

You have two options to get your project files into Colab:

**Option A: Upload ZIP File**
1. Create a ZIP file of your project containing:
   - `src/` folder with all Python modules
   - `config/` folder with `config.yaml`
2. When the notebook prompts, choose option `1` and upload the ZIP file

**Option B: Clone from GitHub**
1. Push your project to a GitHub repository
2. When the notebook prompts, choose option `2` and enter your repository URL

### Step 3: Configure API Credentials

The notebook will ask for your Delta Exchange API credentials. You can provide them in two ways:

**Method 1: Colab Secrets (Recommended)**
1. Click the 🔑 key icon in the left sidebar
2. Add two secrets:
   - Name: `DELTA_API_KEY`, Value: your API key
   - Name: `DELTA_API_SECRET`, Value: your API secret
3. The notebook will automatically use these

**Method 2: Manual Input**
1. The notebook will prompt you to enter credentials
2. They will be securely masked as you type

### Step 4: Run the Notebook

1. Click **Runtime → Run all** to execute all cells
2. Or run cells one by one using Shift+Enter

The notebook will:
- ✅ Install TA-Lib and all dependencies (~5-10 minutes)
- ✅ Fetch historical data from Delta Exchange
- ✅ Engineer features and create target labels
- ✅ Train XGBoost models for each timeframe (15m, 1h, 4h)
- ✅ Generate performance visualizations
- ✅ Package everything into a ZIP file
- ✅ Download the ZIP to your local machine

### Step 5: Download Trained Models

After training completes:
1. The ZIP file will automatically download to your browser's download folder
2. Extract the ZIP file on your local machine
3. You'll find:
   - `models/xgboost_BTCUSDT_15m.pkl`
   - `models/xgboost_BTCUSDT_1h.pkl`
   - `models/xgboost_BTCUSDT_4h.pkl`
   - `training_summary.csv` (metrics and details)
   - `training_summary.png` (performance charts)

### Step 6: Use the Trained Models

1. Copy the `.pkl` files to your local project's `models/` directory
2. Update your `config/config.yaml` to point to the model files
3. Run your trading bot with the trained models

## ⚙️ Configuration

### Training Parameters

You can modify these in the notebook's configuration cell:

```python
SYMBOL = 'BTCUSDT'              # Trading symbol
TIMEFRAMES = ['15m', '1h', '4h'] # Timeframes to train
HISTORICAL_DAYS = 365           # Days of historical data

# Model hyperparameters
MODEL_PARAMS = {
    'n_estimators': 200,        # Number of trees
    'max_depth': 6,             # Tree depth
    'learning_rate': 0.1,       # Learning rate
    # ... more parameters
}

# Data split ratios
TRAIN_RATIO = 0.7               # 70% for training
VAL_RATIO = 0.15                # 15% for validation
TEST_RATIO = 0.15               # 15% for testing
```

### Target Label Thresholds

Modify in the `create_target` function:

```python
buy_threshold = 0.01   # 1% gain → BUY signal
sell_threshold = -0.01 # 1% loss → SELL signal
```

## 📊 What the Notebook Does

### 1. Environment Setup
- Installs TA-Lib (technical analysis library)
- Installs Python packages (XGBoost, pandas, scikit-learn, etc.)

### 2. Data Pipeline
- Fetches OHLC data from Delta Exchange API
- Validates data quality (handles missing values, outliers, etc.)
- Creates 60+ technical indicators (RSI, MACD, Bollinger Bands, etc.)
- Generates target labels (BUY/SELL/HOLD) based on future returns

### 3. Model Training
- Splits data chronologically (preserves time order)
- Trains XGBoost classifier for each timeframe
- Evaluates on train/validation/test sets
- Saves feature importance rankings

### 4. Results & Packaging
- Displays training metrics in a summary table
- Creates performance visualizations
- Packages all models and results into a ZIP file
- Downloads to your local machine

## ⏱️ Expected Runtime

- **TA-Lib Installation**: ~5-10 minutes (one-time)
- **Data Fetching**: ~2-5 minutes (depends on API speed)
- **Feature Engineering**: ~1-2 minutes per timeframe
- **Model Training**: ~30-60 seconds per timeframe
- **Total**: ~15-20 minutes for complete pipeline

## 🔧 Troubleshooting

### Issue: TA-Lib installation fails
**Solution**: Re-run the TA-Lib installation cell. Sometimes it needs multiple attempts.

### Issue: API authentication error
**Solution**: Verify your API credentials are correct. Check that you have API permissions on Delta Exchange.

### Issue: No data fetched
**Solution**: Check if the symbol name is correct (must match Delta Exchange exactly). Try reducing `HISTORICAL_DAYS`.

### Issue: Out of memory error
**Solution**: 
- Reduce `HISTORICAL_DAYS` (e.g., to 180)
- Use fewer timeframes
- Restart runtime and clear outputs

### Issue: Model download doesn't start
**Solution**: 
- Check browser's download settings
- Try manually downloading from Colab's files panel (left sidebar)
- Look for the ZIP file in `/content/` directory

## 📝 Notes

- **Free Colab**: Has resource limits (~12GB RAM, ~4 hours runtime)
- **Colab Pro**: Provides more resources and longer runtime
- **Data**: Fetches 1 year of historical data by default
- **Models**: Each trained model is ~1-5 MB
- **Reproducibility**: Fixed random seed (42) ensures consistent results

## 🎯 Next Steps

After downloading your models:

1. **Backtest**: Use `scripts/backtest.py` to evaluate on historical data
2. **Paper Trading**: Test with `src/trading/paper_engine.py`
3. **Live Trading**: Deploy with proper risk management
4. **Retraining**: Schedule regular retraining (weekly/monthly)

## 💡 Tips

1. **Save to Google Drive**: Mount Drive to save intermediate results
2. **Monitor Training**: Watch the accuracy metrics for overfitting
3. **Feature Analysis**: Review top features to understand model behavior
4. **Experiment**: Try different hyperparameters and thresholds
5. **Version Control**: Keep track of model versions and training dates

## 📚 Resources

- [Google Colab Documentation](https://colab.research.google.com/notebooks/intro.ipynb)
- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [TA-Lib Indicators](https://ta-lib.org/function.html)
- [Delta Exchange API](https://docs.delta.exchange/)

---

**Happy Training! 🚀**

