#!/bin/bash
# deploy.sh – Full Git setup and push

echo "=================================================="
echo "Deploying to GitHub: NGC 628 Emergence Timescale"
echo "=================================================="

# 1. Initialize git
git init

# 2. Create .gitignore
cat > .gitignore << 'EOF'
__pycache__/
*.pyc
*.pyo
venv/
env/
.venv/
.DS_Store
*.fits
*.ecsv
catalogs/*.ecsv
outputs/*.csv
outputs/plots/*.png
*.pdf
Thumbs.db
EOF

git add .
git add -f outputs/plots/  # optionally force-add plots

git commit -m "Initial commit: NGC 628 emergence timescale reproduction"

git remote add origin https://github.com/BaronGhost/Emergence-Timeescale-NGC628.git

# 6. Push
git branch -M main
git push -u origin main

echo "=================================================="
echo "Deployment complete!"
echo "https://github.com/BaronGhost/Emergence-Timeescale-NGC628"
echo "=================================================="