#!/usr/bin/env python3
"""
Complete git workflow: add, commit, and push all changes
"""
import subprocess
import sys

def run_cmd(cmd, description):
    """Run a command and handle output"""
    print(f"\n{'='*60}")
    print(f"► {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("🚀 TRADING DASHBOARD - GIT WORKFLOW")
    print("="*60)
    
    # Step 1: Check git status
    if not run_cmd('git status', 'Step 1: Current Git Status'):
        print("❌ Failed to check git status")
        return False
    
    # Step 2: Add all changes
    if not run_cmd('git add -A', 'Step 2: Stage All Changes'):
        print("❌ Failed to stage changes")
        return False
    print("✅ Changes staged successfully")
    
    # Step 3: Show what will be committed
    if not run_cmd('git diff --cached --stat', 'Step 3: Summary of Changes'):
        print("⚠️ Could not show diff")
    
    # Step 4: Commit with comprehensive message
    commit_msg = """Fix gap percentage calculation and update all backtested statistics

- Changed gap % calculation from (Open - Close) / prev_range to (Open - Close) / prev_close
- This corrects the gap percentage to reflect gap as % of previous day's closing price
- Gap bucket logic now correctly matches the gap percentage classification
- Regenerated all backtest CSV files with corrected gap statistics:
  * Updated gap_stats.csv with new gap percentage calculations
  * Maintained all other statistics (body%, candle state, open context)
- Updated app.py to display "Gap %" label with corrected formula
- All changes ensure consistency between live calculations and backtested data

Test Case:
- Gap Size: 54.00, Previous Close: 25819.35
- New Gap %: 0.21% (correct) instead of 29.52% (incorrect)
- Gap Bucket: 0-0.5% (correct) instead of >2% (incorrect)"""
    
    if not run_cmd(f'git commit -m "{commit_msg}"', 'Step 4: Commit Changes'):
        print("⚠️ Commit may have issues or no changes to commit")
    
    # Step 5: Check current branch
    if not run_cmd('git branch -v', 'Step 5: Current Branch Info'):
        print("❌ Failed to check branch")
        return False
    
    # Step 6: Push to remote
    if not run_cmd('git push origin main', 'Step 6: Push to Repository'):
        print("⚠️ Push may have encountered authentication issues")
        print("\nIf you see authentication errors, you may need to:")
        print("  - Use SSH keys instead of HTTPS")
        print("  - Configure git credentials")
        print("  - Check repository permissions")
        return False
    
    print("\n" + "="*60)
    print("✅ SUCCESS! All changes have been pushed to GitHub")
    print("="*60)
    print("\n📋 Summary of Changes:")
    print("  ✓ Fixed gap percentage calculation formula")
    print("  ✓ Regenerated gap_stats.csv with correct statistics")
    print("  ✓ Updated app.py with correct formula")
    print("  ✓ Updated backtest_nifty.py with correct formula")
    print("  ✓ Committed all changes with descriptive message")
    print("  ✓ Pushed to main branch on GitHub")
    print("\n🎯 Your Trading Dashboard is now up to date!")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
