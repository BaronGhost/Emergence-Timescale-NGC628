import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ============================================
# 1. Load your clean JWST catalog
# ============================================

df = pd.read_csv('outputs/NGC628_multi_band_catalog_clean.csv')

print(f"Total sources: {len(df)}")
print(df['class'].value_counts())

# ============================================
# 2. Generate ages for oYSCs (2-8 Myr, peaked around 5 Myr)
# ============================================

np.random.seed(42)
n_oYSC = (df['class'] == 'oYSC').sum()

# Random ages from a truncated normal distribution (2-8 Myr, mean=5, sigma=1.5)
ages = np.random.normal(5, 1.5, n_oYSC)
ages = np.clip(ages, 2, 8)  # clip to 2-8 Myr

df.loc[df['class'] == 'oYSC', 'age'] = ages
# eYSCI and eYSCII are young by definition (<3 Myr)
df.loc[df['class'] == 'eYSCI', 'age'] = np.random.uniform(0.5, 2, (df['class'] == 'eYSCI').sum())
df.loc[df['class'] == 'eYSCII', 'age'] = np.random.uniform(1, 3, (df['class'] == 'eYSCII').sum())

# ============================================
# 3. MONTE CARLO SAMPLING OF AGES
# ============================================

n_iterations = 1000  # same as paper
n_bins = 5

# Store results from each iteration
all_tau_TOT = []
all_tau_PDR = []
all_bin_edges = []

for i in range(n_iterations):
    if i % 100 == 0:
        print(f"Iteration {i}/{n_iterations}")

    # Sample ages with uncertainties
    df_sampled = df.copy()

    # For oYSCs: add random noise to ages (if age uncertainties available)
    if 'age_err' in df_sampled.columns:
        # Use actual uncertainties
        age_err = df_sampled['age_err']
    else:
        # Use typical uncertainty of ±1.5 Myr
        age_err = 1.5

    # Add random noise to oYSC ages
    oYSC_mask = df_sampled['class'] == 'oYSC'
    n_oYSC = oYSC_mask.sum()
    noise = np.random.normal(0, age_err, n_oYSC)
    df_sampled.loc[oYSC_mask, 'age_sampled'] = df_sampled.loc[oYSC_mask, 'age'] + noise
    df_sampled.loc[oYSC_mask, 'age_sampled'] = df_sampled.loc[oYSC_mask, 'age_sampled'].clip(0, 10)  # keep <10 Myr

    # For eYSCI and eYSCII: keep ages as is (they are young)
    df_sampled.loc[~oYSC_mask, 'age_sampled'] = df_sampled.loc[~oYSC_mask, 'age']

    # Check which oYSCs are still <10 Myr (should be all, but just in case)
    df_sampled['is_oYSC_valid'] = (df_sampled['class'] == 'oYSC') & (df_sampled['age_sampled'] < 10)

    # Counts for this iteration
    n_eYSCI = (df_sampled['class'] == 'eYSCI').sum()
    n_eYSCII = (df_sampled['class'] == 'eYSCII').sum()
    n_oYSC_valid = df_sampled['is_oYSC_valid'].sum()

    total = n_eYSCI + n_eYSCII + n_oYSC_valid

    if total > 0:
        tau_TOT = (n_eYSCI + n_eYSCII) / total * 10
        tau_PDR = n_eYSCI / total * 10
        all_tau_TOT.append(tau_TOT)
        all_tau_PDR.append(tau_PDR)

# Convert to arrays
all_tau_TOT = np.array(all_tau_TOT)
all_tau_PDR = np.array(all_tau_PDR)

# Compute statistics
mean_tau_TOT = np.mean(all_tau_TOT)
std_tau_TOT = np.std(all_tau_TOT)
mean_tau_PDR = np.mean(all_tau_PDR)
std_tau_PDR = np.std(all_tau_PDR)

print("\n" + "=" * 50)
print("MONTE CARLO RESULTS (1000 iterations)")
print("=" * 50)
print(f"τ_TOT: {mean_tau_TOT:.2f} ± {std_tau_TOT:.2f} Myr")
print(f"τ_PDR: {mean_tau_PDR:.2f} ± {std_tau_PDR:.2f} Myr")
print("=" * 50)

# ============================================
# 4. PLOT WITH MONTE CARLO SHADING
# ============================================

# Get bin edges from your data
df_sampled = df.copy()
df_sampled['log_lum'] = np.log10(df_sampled['f444w_flux'])
df_sampled['lum_bin'], bin_edges = pd.cut(df_sampled['log_lum'], bins=n_bins,
                                          include_lowest=True, retbins=True)
bin_midpoints = (bin_edges[:-1] + bin_edges[1:]) / 2


# Function to compute timescales per bin for a given sample
def compute_bin_timescales(df_sample, bin_edges):
    results = {}
    for i in range(len(bin_edges) - 1):
        # Get sources in this bin
        mask = (df_sample['log_lum'] >= bin_edges[i]) & (df_sample['log_lum'] < bin_edges[i + 1])
        bin_data = df_sample[mask]
        if len(bin_data) == 0:
            results[bin_midpoints[i]] = {'tau_TOT': np.nan, 'tau_PDR': np.nan}
            continue
        n_eYSCI = (bin_data['class'] == 'eYSCI').sum()
        n_eYSCII = (bin_data['class'] == 'eYSCII').sum()
        n_oYSC = (bin_data['class'] == 'oYSC').sum()
        total = n_eYSCI + n_eYSCII + n_oYSC
        if total == 0:
            results[bin_midpoints[i]] = {'tau_TOT': np.nan, 'tau_PDR': np.nan}
        else:
            results[bin_midpoints[i]] = {
                'tau_TOT': (n_eYSCI + n_eYSCII) / total * 10,
                'tau_PDR': n_eYSCI / total * 10
            }
    return results

# Monte Carlo for each bin
n_iterations = 1000
bin_results = {mid: {'tau_TOT': [], 'tau_PDR': []} for mid in bin_midpoints}

for i in range(n_iterations):
    if i % 100 == 0:
        print(f"Bin MC iteration {i}/{n_iterations}")

    # Sample ages (same as above)
    df_sample = df.copy()
    oYSC_mask = df_sample['class'] == 'oYSC'
    noise = np.random.normal(0, 1.5, oYSC_mask.sum())
    df_sample.loc[oYSC_mask, 'age'] = df_sample.loc[oYSC_mask, 'age'] + noise
    df_sample.loc[oYSC_mask, 'age'] = df_sample.loc[oYSC_mask, 'age'].clip(0, 10)

    # Reclassify based on sampled age (oYSC only if age < 10 Myr)
    df_sample['class_sampled'] = df_sample['class']
    df_sample.loc[oYSC_mask & (df_sample['age'] >= 10), 'class_sampled'] = 'removed'

    # --- ADD THIS LINE ---
    df_sample['log_lum'] = np.log10(df_sample['f444w_flux'])

    # Compute bin timescales
    results = compute_bin_timescales(df_sample[df_sample['class_sampled'] != 'removed'], bin_edges)
    for mid in bin_midpoints:
        if not np.isnan(results[mid]['tau_TOT']):
            bin_results[mid]['tau_TOT'].append(results[mid]['tau_TOT'])
        if not np.isnan(results[mid]['tau_PDR']):
            bin_results[mid]['tau_PDR'].append(results[mid]['tau_PDR'])

# Compute mean and std per bin
bin_means = {'mid': [], 'tau_TOT': [], 'tau_PDR': [], 'tau_TOT_std': [], 'tau_PDR_std': []}
for mid in bin_midpoints:
    if len(bin_results[mid]['tau_TOT']) > 0:
        bin_means['mid'].append(mid)
        bin_means['tau_TOT'].append(np.mean(bin_results[mid]['tau_TOT']))
        bin_means['tau_PDR'].append(np.mean(bin_results[mid]['tau_PDR']))
        bin_means['tau_TOT_std'].append(np.std(bin_results[mid]['tau_TOT']))
        bin_means['tau_PDR_std'].append(np.std(bin_results[mid]['tau_PDR']))

# Plot
plt.figure(figsize=(8, 6))

plt.errorbar(bin_means['mid'], bin_means['tau_TOT'],
             yerr=bin_means['tau_TOT_std'], fmt='o',
             label=r'$\tau_{\mathrm{TOT}}$', capsize=3, markersize=8)
plt.errorbar(bin_means['mid'], bin_means['tau_PDR'],
             yerr=bin_means['tau_PDR_std'], fmt='s',
             label=r'$\tau_{\mathrm{PDR}}$', capsize=3, markersize=8)

plt.xlabel(r'$\log$(F444W flux) [proxy for mass]', fontsize=12)
plt.ylabel('Timescale (Myr)', fontsize=12)
plt.legend()
plt.grid(True, alpha=0.3)
plt.title('NGC 628 - Emerging Timescale vs Luminosity [Mass Proxy]', fontsize=14)
plt.tight_layout()
plt.savefig(f'{'outputs/plots/'}timescale_mc.png', dpi=150)
plt.show()

# ============================================
# 5. Colour Colour Diagram
# ============================================

fig, ax = plt.subplots(figsize=(10, 8))

# Define class colours (matching the paper)
class_colors = {
    'eYSCI': 'red',
    'eYSCII': 'orange',
    'oYSC': 'blue'
}

# Plot each class with counts in the label
for cls, color in class_colors.items():
    subset = df[df['class'] == cls]
    if len(subset) > 0:
        ax.scatter(
            subset['log_Pa'], subset['log_PAH'],
            c=color,
            label=f'{cls} (n={len(subset)})',   # <── Counts appear here
            s=10,
            alpha=0.6,
            edgecolors='none'
        )

# Optional: Add threshold lines (if you have Pa_excess/PAH_excess)
if 'Pa_excess' in df.columns and 'PAH_excess' in df.columns:
    pa_thresh = df['Pa_excess'].quantile(0.7)
    pah_thresh = df['PAH_excess'].quantile(0.6)
    ax.axvline(x=np.log10(pa_thresh), color='black', linestyle='--', alpha=0.5)
    ax.axhline(y=np.log10(pah_thresh), color='black', linestyle='--', alpha=0.5)

# Labels and legend
ax.set_xlabel(r'$\log$(Pa$\alpha$ excess) = $\log$(F187N / F444W)', fontsize=12)
ax.set_ylabel(r'$\log$(PAH excess) = $\log$(F335M / F444W)', fontsize=12)
ax.legend(markerscale=2, fontsize=11, loc='upper left')
ax.grid(True, alpha=0.3)
ax.set_title('NGC 628 – Colour-Colour Diagram with Cluster Counts', fontsize=14)

# Save (optional)
plt.tight_layout()
plt.savefig(f'{'outputs/plots/'}colour_colour_diagram_counts.png', dpi=150, bbox_inches='tight')
plt.show()


# Save results
output = 'outputs/'
pd.DataFrame(bin_means).to_csv(f'{output}timescale_mc_results.csv', index=False)
print("\nResults saved to 'timescale_mc_results.csv'")