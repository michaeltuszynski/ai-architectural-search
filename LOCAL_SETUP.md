# 🏗️ AI Architectural Search - Local Setup Guide

Quick guide to run the AI Architectural Search system on your local machine.

## Prerequisites

- **Python 3.9+** (Python 3.9, 3.10, or 3.11 recommended)
- **Git** (to clone the repository)
- **8GB+ RAM** (for running CLIP model)
- **2GB+ free disk space** (for dependencies and images)

## Quick Start (5 minutes)

### 1. Clone the Repository

```bash
git clone https://github.com/michaeltuszynski/ai-architectural-search.git
cd ai-architectural-search
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- PyTorch (AI framework)
- CLIP (OpenAI's vision-language model)
- Streamlit (web interface)
- Other required packages

**Note**: First install may take 5-10 minutes depending on your internet speed.

### 4. Verify Setup

Check that everything is installed correctly:

```bash
python health_check.py
```

You should see a JSON output with `"overall_health": "healthy"`.

### 5. Run the Application

```bash
streamlit run app.py
```

The app will automatically open in your browser at `http://localhost:8501`

**That's it!** 🎉 You should now see the AI Architectural Search interface.

---

## Usage

### Search for Buildings

1. Enter a natural language query like:
   - "red brick buildings"
   - "modern glass facades"
   - "buildings with large windows"
   - "stone columns"

2. Click **Search** or press Enter

3. View results ranked by AI confidence

### Example Queries

Try these pre-configured examples:
- Red brick buildings
- Glass and steel facades
- Stone columns
- Flat roof structures
- Large windows
- Modern office buildings

---

## Advanced Setup

### Adding Your Own Images

If you want to add more architectural images:

#### Option 1: Download from Pexels (Recommended)

```bash
# Get a free API key from https://www.pexels.com/api/
export PEXELS_API_KEY='your_api_key_here'

# Download images
python download_pexels_images.py
```

#### Option 2: Add Images Manually

1. Place images in the `images/` directory:
   ```
   images/
   ├── brick_buildings/
   ├── glass_steel/
   ├── stone_facades/
   └── mixed_materials/
   ```

2. Generate embeddings:
   ```bash
   python run_offline_processing.py
   ```

This will:
- Process all images in the `images/` directory
- Generate AI embeddings using CLIP
- Save metadata to `image_metadata.json`
- Take ~1 minute per image

### Regenerate Embeddings

If you modify the image dataset:

```bash
python run_offline_processing.py
```

---

## Troubleshooting

### Port Already in Use

If port 8501 is already in use:

```bash
streamlit run app.py --server.port 8502
```

### Out of Memory

If you get memory errors:

1. Close other applications
2. Reduce batch size in `config.py`:
   ```python
   batch_size: int = 5  # Reduce from 32
   ```

### CLIP Model Download Issues

The first run downloads the CLIP model (~350MB). If it fails:

1. Check your internet connection
2. Try again - the download will resume
3. Or manually download from: https://github.com/openai/CLIP

### Import Errors

If you see `ModuleNotFoundError`:

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

---

## Project Structure

```
ai-architectural-search/
├── app.py                          # Main entry point
├── run_app.py                      # Production entry point
├── run_offline_processing.py       # Embedding generation
├── config.py                       # Configuration
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker configuration
├── src/                            # Core application code
│   ├── models/                     # Data models
│   ├── processors/                 # AI processing
│   ├── storage/                    # Data storage
│   └── web/                        # Web interface
├── images/                         # Image dataset
│   ├── brick_buildings/
│   ├── glass_steel/
│   ├── stone_facades/
│   └── mixed_materials/
├── image_metadata.json             # Pre-computed embeddings
└── tests/                          # Test files
```

---

## Performance Tips

### Speed Up Searches

1. **Use GPU** (if available):
   - PyTorch will automatically use CUDA if available
   - 10x faster than CPU

2. **Pre-compute embeddings**:
   - Run `python run_offline_processing.py` after adding images
   - Searches will be instant (< 1 second)

3. **Reduce image count**:
   - Fewer images = faster searches
   - Start with 20-50 images for testing

### Reduce Memory Usage

1. Lower batch size in `config.py`
2. Use smaller images (resize to 512x512)
3. Close other applications

---

## Development

### Run Tests

```bash
python run_tests.py
```

### Check Code Health

```bash
python health_check.py
```

### View Logs

Logs are written to `app.log` in the project directory.

---

## Stopping the Application

Press `Ctrl+C` in the terminal where Streamlit is running.

---

## Next Steps

- **Read the User Guide**: `USER_GUIDE.md`
- **Demo Instructions**: `DEMO_INSTRUCTIONS.md`
- **Deployment Guide**: `DEPLOYMENT_GUIDE.md`

---

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review `health_check.py` output
3. Check `app.log` for error messages
4. Ensure all prerequisites are met

---

## System Requirements

**Minimum:**
- Python 3.9+
- 4GB RAM
- 2GB disk space
- CPU: Any modern processor

**Recommended:**
- Python 3.10+
- 8GB+ RAM
- 5GB disk space
- GPU with CUDA support (optional, for faster processing)

---

**Happy searching!** 🏗️✨
