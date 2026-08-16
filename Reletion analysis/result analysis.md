# Monsoon Wind Prediction Analysis Results

Based on the prompt you provided, I have written and executed the analysis script `analysis.py`. Here are the findings from the SouthWest Monsoon period (May-September) at Bandaranaike International Airport.

## Mutual Information Scores

The Mutual Information (MI) score measures how much "information" a feature provides about the Wind Speed. Higher scores mean stronger predictive power, even if the relationship is highly non-linear.

| Feature | MI Score |
| :--- | :--- |
| **Dry Temp(0C)** | `0.185256` |
| **RH(%)** | `0.162352` |
| **QNH(hPa)** | `0.006779` |

> [!TIP]
> Temperature (`Dry Temp`) and Relative Humidity (`RH`) show the strongest predictive relationship with Wind Speed during the monsoon period. Surprisingly, `QNH` has a much lower MI score in this dataset, indicating it might not be the primary driver on its own without additional time-based context.

## Visualizations

### 1. Feature Information Gain
![Mutual Information Scores](/Users/Ashan/.gemini/antigravity/brain/52bb0b23-a731-4131-a9f8-f9afee2e848a/artifacts/mutual_information_scores.png)

### 2. Coupled Relationships (Scatter Plots)
These plots show the relationship between Pressure (QNH) vs. Wind Speed and Temperature vs. Wind Speed. A red trend line indicates the general direction of the correlation.

![Scatter Plots](/Users/Ashan/.gemini/antigravity/brain/52bb0b23-a731-4131-a9f8-f9afee2e848a/artifacts/scatter_plots_monsoon.png)

### 3. Non-Linear Connections (Spearman Correlation)
The Spearman heatmap uncovers both linear and curved relationships. Notice the impact of the 3-hour lag features (`_lag_3h`) we generated!

![Spearman Correlation Heatmap](/Users/Ashan/.gemini/antigravity/brain/52bb0b23-a731-4131-a9f8-f9afee2e848a/artifacts/spearman_correlation_heatmap.png)

> [!NOTE]
> The Python script used to generate these results has been saved to `analysis.py` in your workspace. You can run it again anytime using `python analysis.py`.
