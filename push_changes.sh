#!/bin/bash
# Simple git workflow script

echo "=================================================="
echo "🚀 Trading Dashboard - Git Workflow"
echo "=================================================="

echo ""
echo "Step 1: Checking git status..."
git status --short

echo ""
echo "Step 2: Staging all changes..."
git add -A
echo "✅ Changes staged"

echo ""
echo "Step 3: Committing changes..."
git commit -m "Fix gap percentage calculation and update backtested statistics

- Changed gap % calculation: (Open - Close) / prev_close (not prev_range)
- Gap % now correctly reflects gap as percentage of previous close price
- Gap bucket classification now matches gap percentage correctly
- Regenerated all backtest CSV files with corrected gap statistics
- Updated app.py and backtest_nifty.py with correct formulas

Example: Gap 54.00, Prev Close 25819.35
  New Gap %: 0.21% (correct) instead of 29.52% (incorrect)  
  Gap Bucket: 0-0.5% (correct) instead of >2% (incorrect)"

echo ""
echo "Step 4: Pushing to main branch..."
git push origin main

echo ""
echo "=================================================="
echo "✅ SUCCESS! Changes pushed to GitHub"
echo "=================================================="
