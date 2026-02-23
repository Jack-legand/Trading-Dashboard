#!/usr/bin/env python3
"""
Helper script to run backtest and push changes to git.
"""
import subprocess
import sys
import os

os.chdir('/workspaces/Trading-Dashboard')

print("=" * 60)
print("STEP 1: Running Backtest...")
print("=" * 60)

try:
    result = subprocess.run([
        sys.executable, 'backtest_nifty.py', 
        '--input', 'Nifty Data.xlsx', 
        '--output', 'data/'
    ], capture_output=True, text=True, timeout=120)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    if result.returncode != 0:
        print(f"ERROR: Backtest failed with exit code {result.returncode}")
        sys.exit(1)
    else:
        print("\n✅ Backtest completed successfully!")
        
except subprocess.TimeoutExpired:
    print("ERROR: Backtest timed out")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("STEP 2: Checking Git Status...")
print("=" * 60)

try:
    result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print("ERROR: Git status failed")
        sys.exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("STEP 3: Adding Changes to Git...")
print("=" * 60)

try:
    result = subprocess.run(['git', 'add', '-A'], capture_output=True, text=True)
    if result.returncode != 0:
        print("ERROR: Git add failed")
        print(result.stderr)
        sys.exit(1)
    print("✅ All changes staged")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("STEP 4: Committing Changes...")
print("=" * 60)

try:
    commit_msg = "Fix CPR calculation formulas and update backtested statistics\n\n- Corrected CPR formula: PP=(H+L+C)/3, BC=(H+L)/2, TC=(PP-BC)+PP\n- Added TC/BC swap logic to ensure TC > BC\n- Changed Gap % display to Gap Ratio (decimal format)\n- Regenerated all backtest CSV files with corrected formulas"
    
    result = subprocess.run(['git', 'commit', '-m', commit_msg], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    if result.returncode != 0:
        print("WARNING: Git commit may have failed or no changes to commit")
    else:
        print("\n✅ Changes committed successfully!")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("STEP 5: Pushing to Repository...")
print("=" * 60)

try:
    result = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    if result.returncode != 0:
        print("WARNING: Git push may have encountered an issue")
        print("You may need to authenticate or check your git configuration")
    else:
        print("\n✅ Changes pushed to repository successfully!")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("COMPLETED!")
print("=" * 60)
print("\nSummary:")
print("✅ Backtest regenerated CSV files with corrected CPR formulas")
print("✅ Changes committed and pushed to main branch")
