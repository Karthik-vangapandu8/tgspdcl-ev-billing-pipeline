import subprocess
import sys
from pathlib import Path

project_folder = Path(__file__).resolve().parent
steps = ["inspectdata.py", "builddataset.py", "load_data.py"]
for step in steps:
    script_path = project_folder / step
    print(f"\nRunning {step}...", flush=True)
    subprocess.run(
        [sys.executable, str(script_path)],
        cwd=project_folder,
        check=True,
    )

print("\nPipeline completed successfully.")