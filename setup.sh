#!/bin/bash
# setup.sh – Full installation and run script

echo "=================================================="
echo "NGC 628 Emergence Timescale Pipeline"
echo "Reproduction of Pedrini et al. (2026)"
echo "=================================================="

# Clone (skip if already cloned)
if [ ! -d "emergence-timescale-ngc628" ]; then
    git clone https://github.com/yourusername/emergence-timescale-ngc628.git
    cd emergence-timescale-ngc628
else
    cd emergence-timescale-ngc628
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run pipeline
echo "Running pipeline..."
python main.py

echo "=================================================="
echo "Pipeline complete. Check outputs/ and outputs/plots/"
echo "=================================================="