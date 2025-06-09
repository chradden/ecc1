import shutil
import subprocess

def check_dependency(binary_name):
    path = shutil.which(binary_name)
    if path:
        print(f"✅ {binary_name} found at {path}")
    else:
        print(f"❌ {binary_name} not found in PATH")

def check_poppler_and_tesseract():
    print("🔍 Checking Poppler and Tesseract dependencies...")
    check_dependency('pdfinfo')
    check_dependency('pdftoppm')
    check_dependency('tesseract')

    try:
        result = subprocess.run(["tesseract", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Tesseract Version: {result.stdout.splitlines()[0]}")
        else:
            print(f"❌ Tesseract not properly installed: {result.stderr}")
    except Exception as e:
        print(f"❌ Error checking Tesseract version: {e}")

check_poppler_and_tesseract()
