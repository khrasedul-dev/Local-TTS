# 📚 Documentation Index

Quick reference for all documentation files.

## For New Users 👥

**Start here:**

1. [`QUICK_START.md`](QUICK_START.md) - 3 steps to launch (5 minutes)
2. [`README.md`](README.md) - Features & detailed setup

**If installation fails:**

- [`INSTALLATION.md`](INSTALLATION.md) - Troubleshooting solutions

## For Developers 👨‍💻

**Understanding the setup:**

1. [`SETUP_SUMMARY.md`](SETUP_SUMMARY.md) - What was fixed and why
2. [`PROJECT_STATUS.md`](PROJECT_STATUS.md) - Complete status report

**Quality assurance:**

- [`PRE_RELEASE_CHECKLIST.md`](PRE_RELEASE_CHECKLIST.md) - Verification checklist

## Installation Files 🔧

### Automated Setup (Recommended)

- **Windows:** Double-click [`install.bat`](install.bat)
- **macOS/Linux:** Run `chmod +x install.sh && ./install.sh`

### Quick Launch

- **Windows:** Double-click [`run_app.bat`](run_app.bat)
- **macOS/Linux:** `source .venv/bin/activate && python app.py`

### Configuration

- [`requirements.txt`](requirements.txt) - All dependencies
- [`.gitignore`](.gitignore) - Excluded files

## Application Files 📱

- [`app.py`](app.py) - Main Kokoro TTS application
- [`assets/`](assets/) - UI resources (icon, images)

---

## Troubleshooting Quick Links

**Common Issues:**

- [Python not found](INSTALLATION.md#python-command-not-found)
- [Module not found](INSTALLATION.md#module-not-found-errors-after-installation)
- [PyTorch errors](INSTALLATION.md#pytorch-dllimport-errors)
- [NumPy issues](INSTALLATION.md#numpy-compatibility-errors)
- [Slow installation](INSTALLATION.md#installation-very-slow)

---

## File Sizes

| File               | Size   | Purpose       |
| ------------------ | ------ | ------------- |
| `app.py`           | 47 KB  | Application   |
| `requirements.txt` | 1 KB   | Dependencies  |
| `install.bat`      | 3 KB   | Windows setup |
| `install.sh`       | 2 KB   | Unix setup    |
| `README.md`        | 6 KB   | Main guide    |
| Documentation      | ~15 KB | All guides    |

**After Installation:**

- Virtual environment: ~500 MB
- Dependencies: ~1.5 GB
- Models (on first run): ~2 GB

---

## Quick Commands

```bash
# One-time setup (choose one):
install.bat              # Windows
./install.sh             # macOS/Linux

# Every time you launch:
run_app.bat              # Windows
source .venv/bin/activate && python app.py  # macOS/Linux

# Verify installation:
python -c "from kokoro import KPipeline; print('✓ OK')"

# Update dependencies:
python -m pip install --upgrade -r requirements.txt
```

---

## Document Overview

### Quick Reference (5-10 min read)

- ✅ `QUICK_START.md` - Get running in 3 steps

### Getting Started (15-30 min read)

- ✅ `README.md` - Features & setup
- ✅ `INSTALLATION.md` - Troubleshooting

### Technical Overview (30+ min read)

- ✅ `SETUP_SUMMARY.md` - Technical details
- ✅ `PROJECT_STATUS.md` - Complete status
- ✅ `PRE_RELEASE_CHECKLIST.md` - Verification

---

## How to Use This Project

### For End Users

1. Read [`QUICK_START.md`](QUICK_START.md)
2. Run appropriate setup script
3. Read [`README.md`](README.md) for usage
4. If stuck, check [`INSTALLATION.md`](INSTALLATION.md)

### For Developers

1. Read [`SETUP_SUMMARY.md`](SETUP_SUMMARY.md) for changes
2. Review [`requirements.txt`](requirements.txt) for dependencies
3. Check [`PRE_RELEASE_CHECKLIST.md`](PRE_RELEASE_CHECKLIST.md) before shipping

### For Maintainers

1. Refer to [`PROJECT_STATUS.md`](PROJECT_STATUS.md)
2. Run checks from [`PRE_RELEASE_CHECKLIST.md`](PRE_RELEASE_CHECKLIST.md)
3. Update [`requirements.txt`](requirements.txt) for new versions

---

## Status

✅ **All documentation complete**
✅ **All setup scripts functional**
✅ **Project ready for distribution**

**Start with:** [`QUICK_START.md`](QUICK_START.md)

---

_Last Updated: November 22, 2025_
_For issues: Check INSTALLATION.md troubleshooting section_
