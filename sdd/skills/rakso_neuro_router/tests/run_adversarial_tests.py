import os
import sys
import pytest

def main():
    log_path = r"c:\Users\oskco\SSD+\sdd-plus\.agents\challenger_neuro_router_1\verification_run.log"
    print(f"Running pytest and redirecting output to {log_path}...")
    
    # We will redirect stdout and stderr to the log file to capture all details
    with open(log_path, "w", encoding="utf-8") as log_file:
        # Save original stdout/stderr
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr
        sys.stdout = log_file
        sys.stderr = log_file
        
        try:
            exit_code = pytest.main([
                "sdd/skills/rakso_neuro_router/tests/test_adversarial.py",
                "-v"
            ])
            print(f"\nPytest exited with code: {exit_code}", file=log_file)
        except Exception as e:
            print(f"\nException occurred: {e}", file=log_file)
            exit_code = 1
        finally:
            # Restore stdout/stderr
            sys.stdout = orig_stdout
            sys.stderr = orig_stderr
            
    print(f"Done. Exit code: {exit_code}")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
