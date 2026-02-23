#!/usr/bin/env python3
"""Final cleanup for v2.1 consolidation"""
import os
import subprocess
import shutil

def main():
    files_to_delete = [
        'complete_backtest_and_push.py',
        'execute_backtest.py',
        'git_workflow.py',
        'push_changes.sh',
        'run_backtest_and_push.py',
    ]
    
    dirs_to_delete = ['imghdr_pkg']
    
    # Delete files
    for f in files_to_delete:
        if os.path.exists(f):
            os.remove(f)
            print(f"Deleted: {f}")
    
    # Delete directories
    for d in dirs_to_delete:
        if os.path.isdir(d):
            shutil.rmtree(d)
            print(f"Deleted: {d}/")
    
    # Stage all changes
    subprocess.run(['git', 'add', '-A'], check=True)
    print("Staged all changes")
    
    # Create commit
    subprocess.run([
        'git', 'commit', '-m',
        'v2.1: Repository consolidation - removed 15 noise files, updated to version 2.1'
    ], check=True)
    print("Committed changes")
    
    # Push to GitHub
    subprocess.run(['git', 'push', 'origin', 'main'], check=True)
    print("Pushed to GitHub")
    
    # Show final status
    subprocess.run(['git', 'status'], check=True)
    print("\n✅ v2.1 consolidation complete!")

if __name__ == '__main__':
    main()
