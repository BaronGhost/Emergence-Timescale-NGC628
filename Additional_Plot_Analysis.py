import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.optimize import curve_fit

# ============================================
# Load your clean JWST catalog
# ============================================

df = pd.read_csv('outputs/NGC628_multi_band_catalog_clean.csv')

print(f"Total sources: {len(df)}")
print(df['class'].value_counts())

output = 'outputs/plots/'
# ============================================
# 1. Spatial Distribution of Classes (RA vs Dec)
# ============================================

fig, ax = plt.subplots(figsize=(10, 8))
colors = {'eYSCI':'red', 'eYSCII':'orange', 'oYSC':'blue'}
for cls, color in colors.items():
    sub = df[df['class'] == cls]
    ax.scatter(sub['RA'], sub['Dec'], c=color, s=5, alpha=0.6, label=f'{cls} ({len(sub)})')
ax.set_xlabel('RA (deg)')
ax.set_ylabel('Dec (deg)')
ax.invert_xaxis()  # astronomical convention
ax.legend(markerscale=2)
ax.set_title('Spatial Distribution of Star Clusters in NGC 628')
plt.tight_layout()
plt.savefig(f'{output}spatial_map.png', dpi=150)
plt.show()

# ============================================
# 2. Flux Histograms per Class (Key Filters)
# ============================================

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
filters = ['f187n', 'f335m']
titles = ['Paα (F187N) flux', 'PAH (F335M) flux']
for i, f in enumerate(filters):
    for cls, color in colors.items():
        sub = df[df['class'] == cls]
        axes[i].hist(np.log10(sub[f'{f}_flux']), bins=30, alpha=0.5,
                     color=color, label=cls, density=True)
    axes[i].set_xlabel(f'log({titles[i]})')
    axes[i].set_ylabel('Density')
    axes[i].legend()
    axes[i].grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{output}flux_histograms.png', dpi=150)
plt.show()

# ============================================
# 3. Luminosity vs. Class (Boxplot)
# ============================================

fig, ax = plt.subplots(figsize=(8, 6))
df['log_lum'] = np.log10(df['f444w_flux'])
df.boxplot(column='log_lum', by='class', ax=ax,
                 boxprops=dict(alpha=0.7), patch_artist=True)
ax.set_ylabel(r'$\log$(F444W flux) [mass proxy]')
ax.set_xlabel('Class')
ax.set_title('Luminosity Distribution per Class')
plt.suptitle('')  # remove automatic title
plt.tight_layout()
plt.savefig(f'{output}lum_vs_class_boxplot.png', dpi=150)
plt.show()

# ============================================
# 4. Timescale vs. Luminosity with Power‑Law Fit
# ============================================

# Remove the lowest bin (τ=10 Myr artifact) if desired
mc = pd.read_csv('outputs/timescale_mc_results.csv')
mc = mc[mc['mid'] > -7.0]

# Define power-law: tau = a * L^b
def power_law(L, a, b):
    return a * (10**L) ** b

xdata = mc['mid'].values
ydata = mc['tau_TOT'].values
popt, _ = curve_fit(power_law, xdata, ydata, p0=[1, -1])
a, b = popt
print(f"Best fit: τ_TOT = {a:.2f} * L^{b:.2f}")

# Plot with fit
plt.figure(figsize=(8,6))
plt.errorbar(mc['mid'], mc['tau_TOT'], yerr=mc['tau_TOT_std'],
             fmt='o', label='Data')
L_plot = np.linspace(mc['mid'].min(), mc['mid'].max(), 100)
plt.plot(L_plot, power_law(L_plot, *popt), 'r--',
         label=f'$\\tau = {a:.1f} L^{{{b:.2f}}}$')
plt.xlabel(r'$\log$(F444W flux)')
plt.ylabel('τ_TOT (Myr)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.title('Timescale vs. Luminosity with Power‑Law Fit')
plt.tight_layout()
plt.savefig(f'{output}timescale_fit.png', dpi=150)
plt.show()
