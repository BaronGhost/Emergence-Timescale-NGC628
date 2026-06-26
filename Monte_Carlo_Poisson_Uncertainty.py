import numpy as np
import pandas as pd

# ============================================
# 1. Load your catalog
# ============================================
df = pd.read_csv('outputs/NGC628_multi_band_catalog_clean.csv')

# ============================================
# 2. Counts per class
# ============================================
N_eYSCI = (df['class'] == 'eYSCI').sum()
N_eYSCII = (df['class'] == 'eYSCII').sum()
N_oYSC = (df['class'] == 'oYSC').sum()

print(f"Counts: \n eYSCI = {N_eYSCI}\n eYSCII = {N_eYSCII}\n oYSC = {N_oYSC}")
print(f"Total: {N_eYSCI + N_eYSCII + N_oYSC}")

# ============================================
# 3. Poisson Monte Carlo
# ============================================
n_iter = 10000  # more stable than 1000
tau_TOT_samples = []
tau_PDR_samples = []

for i in range(n_iter):
    # Sample each count from a Poisson distribution
    n1 = np.random.poisson(N_eYSCI)
    n2 = np.random.poisson(N_eYSCII)
    n3 = np.random.poisson(N_oYSC)

    total = n1 + n2 + n3
    if total > 0:
        tau_TOT = (n1 + n2) / total * 10
        tau_PDR = n1 / total * 10
        tau_TOT_samples.append(tau_TOT)
        tau_PDR_samples.append(tau_PDR)

# ============================================
# 4. Results
# ============================================
tau_TOT_samples = np.array(tau_TOT_samples)
tau_PDR_samples = np.array(tau_PDR_samples)

tau_TOT_mean = np.mean(tau_TOT_samples)
tau_TOT_std = np.std(tau_TOT_samples)
tau_PDR_mean = np.mean(tau_PDR_samples)
tau_PDR_std = np.std(tau_PDR_samples)

print("\n" + "=" * 50)
print("POISSON MONTE CARLO RESULTS")
print("=" * 50)
print(f"τ_TOT = {tau_TOT_mean:.2f} ± {tau_TOT_std:.2f} Myr")
print(f"τ_PDR = {tau_PDR_mean:.2f} ± {tau_PDR_std:.2f} Myr")
print("=" * 50)