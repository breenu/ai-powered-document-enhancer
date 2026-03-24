"""Verify Tesseract OCR installation and accessibility."""

import shutil
import subprocess
import sys


def verify_tesseract() -> bool:
    tesseract_path = shutil.which("tesseract")

    if tesseract_path:
        print(f"[OK] Tesseract found on PATH: {tesseract_path}")
    else:
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]
        for p in common_paths:
            import os
            if os.path.isfile(p):
                tesseract_path = p
                print(f"[OK] Tesseract found at: {p}")
                print("     (Not on PATH -- add its directory to PATH or configure in app Settings)")
                break

    if not tesseract_path:
        print("[WARN] Tesseract OCR not found.")
        print("       Install from: https://github.com/tesseract-ocr/tesseract")
        print("       On Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        print("       After installing, add the install directory to your system PATH,")
        print("       or configure the path in the application Settings page.")
        return False

    try:
        result = subprocess.run(
            [tesseract_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        version_line = result.stdout.strip().split("\n")[0] if result.stdout else result.stderr.strip().split("\n")[0]
        print(f"[OK] Tesseract version: {version_line}")
        return True
    except Exception as e:
        print(f"[ERROR] Could not run Tesseract: {e}")
        return False


if __name__ == "__main__":
    success = verify_tesseract()
    sys.exit(0 if success else 1)
