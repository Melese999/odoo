import scipy.stats as st
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 1. --- Data Preparation ---
np.random.seed(42)
return_data = st.skewnorm.rvs(a=5, loc=0.01, scale=0.02, size=1000)

# 2. --- Statistical Calculations ---
skew = st.skew(return_data)
kurt = st.kurtosis(return_data, fisher=False)
jb_stat, jb_p = st.jarque_bera(return_data)

# 3. --- Visualization ---
sns.set_style('whitegrid')
# Create a figure with 3 subplots in 1 row
fig, axes = plt.subplots(1, 3, figsize=(20, 6))
fig.suptitle('Comprehensive Analysis of Returns Data', fontsize=20)

# Plot 1: Histogram
sns.histplot(return_data, kde=True, bins=30, ax=axes[0])
axes[0].set_title('Distribution of Returns')

# Plot 2: Box Plot
sns.boxplot(y=return_data, ax=axes[1])
axes[1].set_title('Box Plot for Outlier Detection')

# Plot 3: Q-Q Plot
st.probplot(return_data, dist="norm", plot=axes[2])
axes[2].set_title('Q-Q Plot for Normality')


# Add the statistics as text on the plot for a nice summary
stats_text = (f"Skewness: {skew:.2f}\n"
              f"Kurtosis: {kurt:.2f}\n"
              f"Jarque-Bera p-value: {jb_p:.3f}")
fig.text(0.5, 0.92, stats_text, ha='center', va='center', fontsize=12, bbox={"facecolor":"white", "alpha":0.5, "pad":5})


plt.tight_layout(rect=[0, 0, 1, 0.9]) # Adjust layout to make room for suptitle and text
plt.show()