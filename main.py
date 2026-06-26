#!/usr/bin/env python3
"""
main.py – Run the full NGC 628 emergence timescale pipeline.
Executes the four analysis scripts in sequence.
"""
import subprocess
import sys
import os

# Scripts to run in order
scripts = [
    "Classification_Catalog_Quality_Cuts.py",
    "Classification_Monte_Carlo.py",
    "Additional_Plot_Analysis.py",
    "Monte_Carlo_Poisson_Uncertainty.py"
]

def run_script(script_name):
    """Run a Python script and return exit code."""
    print("\n" + "="*60)
    print(f"RUNNING: {script_name}")
    print("="*60)

    if not os.path.exists(script_name):
        print(f"ERROR: {script_name} not found in current directory.")
        return 1

    result = subprocess.run([sys.executable, script_name], capture_output=False)
    return result.returncode


if __name__ == "__main__":
    print("\n" + "="*60)
    print("NGC 628 EMERGENCE TIMESCALE PIPELINE")
    print("Reproduction of Pedrini et al. (2026)")
    print("="*60)

    failed = False
    for script in scripts:
        code = run_script(script)
        if code != 0:
            print(f"\nERROR: {script} failed with exit code {code}")
            failed = True
            break

    if not failed:
        print("\n" + "="*60)
        print("ALL SCRIPTS COMPLETED SUCCESSFULLY.")
        print("Check 'outputs/' and 'outputs/plots/' for results.")
        print("="*60)
    else:
        print("\nPipeline terminated due to error.")
        sys.exit(1)