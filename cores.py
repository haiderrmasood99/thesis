import multiprocessing
cores = multiprocessing.cpu_count()
print(f"Number of CPU cores: {cores}")

# Alternatively, using the 'os' module:
import os
cores_os = os.cpu_count()
print(f"Number of CPU cores (os module): {cores_os}")
