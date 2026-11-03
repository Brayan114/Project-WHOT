import os
import zipfile

output_zip = 'WHOT-ML-Software-v1.0.2.zip'
root_dir = os.path.abspath('.')

# Explicit top-level files to include
top_files = [
    'README.md',
    'LICENSE',
    'CITATION.cff',
    'requirements-paper1.txt',
    'CHANGELOG.md',
    'pyproject.toml'
]

# Explicit directories to walk
include_dirs = ['whot_ml', 'tests', 'experiments']

def should_exclude(rel_path):
    normalized = rel_path.replace('\\', '/')
    parts = normalized.split('/')
    if any(p in ['.git', '__pycache__', '.pytest_cache', 'paper', 'docs', 'tools', 'staging'] for p in parts):
        return True
    if 'runs' in parts:
        return True
    if any(normalized.endswith(ext) for ext in ['.pt', '.zip', '.pdf', '.pyc', '.pyo']):
        return True
    return False

files_to_add = []

for f in top_files:
    if os.path.exists(f):
        files_to_add.append((f, f))

for d in include_dirs:
    for root, dirs, files in os.walk(d):
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, root_dir)
            if not should_exclude(rel_path):
                files_to_add.append((full_path, rel_path))

files_to_add.sort(key=lambda x: x[1])

print(f"Total files to add: {len(files_to_add)}")

with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
    for full_path, rel_path in files_to_add:
        zf.write(full_path, rel_path)

zip_size = os.path.getsize(output_zip)
print(f"Created {output_zip} successfully!")
print(f"Path: {os.path.abspath(output_zip)}")
print(f"Size: {zip_size} bytes ({zip_size / (1024*1024):.2f} MB / {zip_size / 1024:.2f} KB)")
