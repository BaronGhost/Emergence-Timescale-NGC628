import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from astropy.table import Table
import os

# ============================================
# 1. List of filters and base path
# ============================================
filters = ['f115w', 'f150w', 'f187n', 'f200w', 'f277w', 'f335m', 'f444w']
base = 'catalogs/jw01783-o904_t008_nircam_clear-'

# ============================================
# 2. Load and merge all catalogs
# ============================================
first_file = f'{base}{filters[0]}_cat.ecsv'
master = Table.read(first_file, format='ascii.ecsv')
df = master.to_pandas()

# Find columns
label_col = 'label' if 'label' in df.columns else df.columns[0]
ra_col = [c for c in df.columns if 'ra' in c.lower() and 'centroid' in c.lower()]
dec_col = [c for c in df.columns if 'dec' in c.lower() and 'centroid' in c.lower()]
if not ra_col:
    ra_col = [c for c in df.columns if 'ra' in c.lower()]
if not dec_col:
    dec_col = [c for c in df.columns if 'dec' in c.lower()]
ra_col = ra_col[0] if ra_col else None
dec_col = dec_col[0] if dec_col else None

cols_to_keep = [label_col]
if ra_col:
    cols_to_keep.append(ra_col)
if dec_col:
    cols_to_keep.append(dec_col)

df_merge = df[cols_to_keep].copy()
rename_map = {}
if ra_col:
    rename_map[ra_col] = 'RA'
if dec_col:
    rename_map[dec_col] = 'Dec'
df_merge.rename(columns=rename_map, inplace=True)

print(f"Initial sources: {len(df_merge)}")

# Merge fluxes
for f in filters:
    print(f"Loading {f}...")
    cat = Table.read(f'{base}{f}_cat.ecsv', format='ascii.ecsv')
    temp = cat.to_pandas()

    # Find flux column
    flux_col = None
    for col in ['aper_total_flux', 'aper50_flux', 'isophotal_flux']:
        if col in temp.columns:
            flux_col = col
            break
    if flux_col is None:
        print(f"  Warning: No flux column found in {f}, skipping")
        continue

    # Find error column (for S/N)
    err_col = None
    for col in [f'{flux_col}_err', 'aper_total_flux_err']:
        if col in temp.columns:
            err_col = col
            break

    # Rename and merge
    temp.rename(columns={flux_col: f'{f}_flux'}, inplace=True)
    if err_col:
        temp.rename(columns={err_col: f'{f}_flux_err'}, inplace=True)

    merge_cols = [label_col, f'{f}_flux']
    if err_col:
        merge_cols.append(f'{f}_flux_err')

    df_merge = df_merge.merge(temp[merge_cols], on=label_col, how='inner')

print(f"\nMerged catalog: {len(df_merge)} sources")

# ============================================
# 3. Compute S/N for key filters
# ============================================
print("\nComputing S/N...")
for f in ['f187n', 'f335m', 'f444w']:
    err_col = f'{f}_flux_err'
    if err_col in df_merge.columns:
        df_merge[f'{f}_snr'] = df_merge[f'{f}_flux'] / df_merge[err_col]
        print(f"  {f}: median S/N = {df_merge[f'{f}_snr'].median():.1f}")
    else:
        print(f"  Warning: {err_col} not found for {f}")

# ============================================
# 4. Apply Quality Cuts
# ============================================
print("\nApplying quality cuts...")
df_clean = df_merge.copy()

# Cut 1: S/N > 3 in key filters
snr_cut = 3.0
for f in ['f187n', 'f335m', 'f444w']:
    snr_col = f'{f}_snr'
    if snr_col in df_clean.columns:
        df_clean = df_clean[df_clean[snr_col] > snr_cut]
print(f"After S/N > {snr_cut}: {len(df_clean)} sources")

# Cut 2: Remove non-positive fluxes
for f in filters:
    flux_col = f'{f}_flux'
    if flux_col in df_clean.columns:
        df_clean = df_clean[df_clean[flux_col] > 0]
print(f"After positive flux cut: {len(df_clean)} sources")

# Cut 3: Morphological cuts (if available)
if 'sharpness' in df_clean.columns:
    df_clean = df_clean[(df_clean['sharpness'] > -0.5) & (df_clean['sharpness'] < 0.5)]
    print(f"After sharpness cut: {len(df_clean)} sources")
if 'roundness' in df_clean.columns:
    df_clean = df_clean[df_clean['roundness'] > 0.5]
    print(f"After roundness cut: {len(df_clean)} sources")

# ============================================
# 5. Compute excess ratios (NOW BEFORE DROPPING NaNs)
# ============================================
print("\nComputing excess ratios...")
df_clean['Pa_excess'] = df_clean['f187n_flux'] / df_clean['f444w_flux']
df_clean['PAH_excess'] = df_clean['f335m_flux'] / df_clean['f444w_flux']

# Remove infinities and NaNs
df_clean = df_clean.replace([np.inf, -np.inf], np.nan)
df_clean = df_clean.dropna(subset=['Pa_excess', 'PAH_excess'])
print(f"After removing NaNs: {len(df_clean)} sources")

# Log-transform
df_clean['log_Pa'] = np.log10(df_clean['Pa_excess'])
df_clean['log_PAH'] = np.log10(df_clean['PAH_excess'])

# ============================================
# 6. Classify
# ============================================
print("\nClassifying...")
pa_thresh = df_clean['Pa_excess'].quantile(0.7)
pah_thresh = df_clean['PAH_excess'].quantile(0.6)

print(f"Thresholds: Pa={pa_thresh:.3f}, PAH={pah_thresh:.3f}")

df_clean['class'] = 'oYSC'
df_clean.loc[(df_clean['Pa_excess'] > pa_thresh) & (df_clean['PAH_excess'] > pah_thresh), 'class'] = 'eYSCI'
df_clean.loc[(df_clean['Pa_excess'] > pa_thresh) & (df_clean['PAH_excess'] <= pah_thresh), 'class'] = 'eYSCII'

print("\nClassification counts:")
print(df_clean['class'].value_counts())

# ============================================
# 9. Compare before/after
# ============================================
print("\n" + "=" * 50)
print("COMPARISON: Before vs. After Quality Cuts")
print("=" * 50)
print(f"{'Class':<10} {'Before':<10} {'After':<10}")
print("-" * 30)

# We need the original classification before cuts
# Recompute original classification on df_merge
df_merge['Pa_excess'] = df_merge['f187n_flux'] / df_merge['f444w_flux']
df_merge['PAH_excess'] = df_merge['f335m_flux'] / df_merge['f444w_flux']
df_merge = df_merge.replace([np.inf, -np.inf], np.nan).dropna(subset=['Pa_excess', 'PAH_excess'])
pa_thresh_orig = df_merge['Pa_excess'].quantile(0.7)
pah_thresh_orig = df_merge['PAH_excess'].quantile(0.6)
df_merge['class'] = 'oYSC'
df_merge.loc[(df_merge['Pa_excess'] > pa_thresh_orig) & (df_merge['PAH_excess'] > pah_thresh_orig), 'class'] = 'eYSCI'
df_merge.loc[(df_merge['Pa_excess'] > pa_thresh_orig) & (df_merge['PAH_excess'] <= pah_thresh_orig), 'class'] = 'eYSCII'

for cls in ['eYSCI', 'eYSCII', 'oYSC']:
    before = (df_merge['class'] == cls).sum()
    after = (df_clean['class'] == cls).sum()
    print(f"{cls:<10} {before:<10} {after:<10}")
print("=" * 50)

# ============================================
# 10. Save clean catalog
# ============================================
output = 'outputs/'
df_clean.to_csv(f'{output}NGC628_multi_band_catalog_clean.csv', index=False)
print("\nClean catalog saved to 'NGC628_multi_band_catalog_clean.csv'")