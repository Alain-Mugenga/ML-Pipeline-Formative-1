# Household Power Consumption: EDA and Forecasting

This project explores the Individual Household Electric Power Consumption dataset and builds a model to forecast household electricity demand one hour ahead.

## Objective

Predict the hourly mean of `Global_active_power` (kW) using historical consumption, sensor readings, and calendar features. The notebook examines missing data, demand patterns, seasonality, lag relationships, and model performance.

## Dataset

The data contains household electricity measurements recorded every minute from December 2006 to November 2010. It includes active and reactive power, voltage, current intensity, and three sub-metering measurements.

The dataset is from the [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption). The raw data file is included at `data/household_power_consumption.txt`.

## Project contents

- `Task1_Time_Series_EDA_and_Modeling.ipynb` — exploratory analysis, preprocessing, feature engineering, model experiments, and evaluation.
- `preprocessing.py` — reusable data-loading, cleaning, hourly aggregation, and feature-building functions.
- `data/household_power_consumption.txt` — raw minute-level data.
- `data/hourly_clean.csv` — processed hourly data.
- `data/experiment_table.csv` — model experiment results.
- `figures/` — plots produced during the analysis.
- `models/best_model.joblib` — saved best-performing model.
- `models/feature_columns.json` — model feature names, target, and test metrics.

## Preprocessing and modeling

The notebook parses the date and time into a datetime index, treats `?` as missing data, and aggregates the minute readings into hourly means. Short missing gaps are interpolated; longer gaps are filled using the same hour from the previous week, with fallback filling for remaining values.

The forecasting features include past demand lags, rolling statistics, previous-hour sensor readings, and calendar features. The data is split chronologically: training through December 2009 and testing on 2010. Models are compared using time-series cross-validation and held-out test metrics. The final model is selected by cross-validation RMSE on the training period.

## Results

The selected HistGradientBoosting model achieved a test RMSE of **0.463 kW**, MAE of **0.316 kW**, and R² of **0.65**. Compared with the persistence baseline, it reduced RMSE by about 25%.

The model captures typical demand patterns but tends to under-predict sudden high-demand peaks, particularly in the evening.

## Run the notebook

Run Jupyter from this project directory so the notebook can find the relative `data/`, `figures/`, and `models/` paths. Install the required Python packages if they are not already available:

```bash
pip install numpy pandas matplotlib seaborn statsmodels scikit-learn scipy joblib jupyter