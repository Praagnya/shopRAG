# Digital Ocean Droplet Setup for 10k Product Ingestion

This guide walks you through setting up a Digital Ocean droplet to process 10,000 products efficiently.

## 1. Create Digital Ocean Droplet

### Recommended Specs:
- **Type**: CPU-Optimized or Regular Droplet
- **Size**: 4 vCPUs, 8GB RAM minimum (or 8 vCPUs, 16GB for faster processing)
- **Storage**: 100GB SSD minimum (dataset is ~10-20GB, plus ChromaDB storage)
- **OS**: Ubuntu 22.04 LTS
- **Region**: Choose closest to you for lower latency

### Estimated Costs:
- 4 vCPU, 8GB RAM: ~$0.071/hour (~$1.70 for 24 hours)
- 8 vCPU, 16GB RAM: ~$0.143/hour (~$3.43 for 24 hours)
- You can destroy the droplet after ingestion is complete!

## 2. Initial Server Setup

### SSH into your droplet:
```bash
ssh root@YOUR_DROPLET_IP
```

### Update system packages:
```bash
apt update && apt upgrade -y
```

### Install required system packages:
```bash
apt install -y python3-pip python3-venv git build-essential
```

## 3. Setup Project

### Clone your repository:
```bash
cd /root
git clone YOUR_REPO_URL shopRAG
cd shopRAG
```

### Install uv (Python package manager):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

### Install Python dependencies:
```bash
uv sync
```

## 4. Configure for 10k Products

### Update configuration in `backend/config/settings.py`:
```python
MAX_PRODUCTS_TO_LOAD = 10000  # For 10k products
MAX_REVIEWS_PER_PRODUCT = 50   # Limit to 50 reviews per product (optional)
MAX_REVIEWS_TO_PROCESS = None  # No overall limit
BATCH_SIZE = 512               # Already optimized
```

### Set up environment variables:
```bash
# Create .env file
cat > .env << EOF
OPENAI_API_KEY=your_openai_key_here
EOF
```

## 5. Run Ingestion in Background

### Option A: Using nohup (Simple):
```bash
nohup uv run python backend/scripts/ingest_reviews.py > ingestion.log 2>&1 &
```

### Option B: Using tmux (Recommended - you can reconnect):
```bash
# Install tmux
apt install -y tmux

# Start tmux session
tmux new -s ingestion

# Run the script
uv run python backend/scripts/ingest_reviews.py

# Detach: Press Ctrl+B, then D
# Reattach later: tmux attach -t ingestion
```

### Option C: Using screen:
```bash
# Install screen
apt install -y screen

# Start screen session
screen -S ingestion

# Run the script
uv run python backend/scripts/ingest_reviews.py

# Detach: Press Ctrl+A, then D
# Reattach later: screen -r ingestion
```

## 6. Monitor Progress

### View logs (if using nohup):
```bash
tail -f ingestion.log
```

### Check resource usage:
```bash
# Install htop
apt install -y htop

# Monitor CPU/RAM
htop
```

### Check disk space:
```bash
df -h
```

## 7. Expected Timeline for 10k Products

**First Run** (includes dataset download):
- Dataset download: 30-60 mins (one-time, ~10-20GB)
- Dataset filtering: 5-10 mins
- Embedding & storage: 30-90 mins (depending on reviews/product)

**Subsequent Runs** (uses cached dataset):
- Dataset loading: 2-5 mins (from cache)
- Dataset filtering: 5-10 mins
- Embedding & storage: 30-90 mins

**Total Time Estimates**:
- **With MAX_REVIEWS_PER_PRODUCT = 50**: ~500k reviews
  - First run: 1.5-3 hours total
  - Subsequent runs: 40-105 mins

- **With all reviews** (~1-2M reviews):
  - First run: 2-4 hours total
  - Subsequent runs: 1-2 hours

## 8. Download Results

### Option A: SCP to local machine:
```bash
# From your local machine
scp -r root@YOUR_DROPLET_IP:/root/shopRAG/data ./
```

### Option B: Use rsync (faster for large files):
```bash
# From your local machine
rsync -avz --progress root@YOUR_DROPLET_IP:/root/shopRAG/data ./
```

### Option C: Upload to S3/Cloud Storage:
```bash
# Install AWS CLI on droplet
apt install -y awscli

# Configure AWS
aws configure

# Upload to S3
aws s3 sync /root/shopRAG/data s3://your-bucket/shopRAG-data/
```

## 9. Clean Up

### After downloading your data:
```bash
# Exit the droplet
exit

# Destroy the droplet from Digital Ocean dashboard or CLI
doctl compute droplet delete DROPLET_ID
```

## 10. Cost Optimization Tips

1. **Start with fewer products first** (1000) to test the pipeline
2. **Use MAX_REVIEWS_PER_PRODUCT = 50** to reduce processing time
3. **Destroy droplet immediately** after downloading data
4. **Use snapshots** if you need to pause and resume later
5. **Monitor with `htop`** to ensure you're not over/under-provisioned

## Troubleshooting

### Out of Memory:
- Reduce `BATCH_SIZE` to 256 or 128
- Reduce `MAX_REVIEWS_PER_PRODUCT`
- Upgrade to larger droplet

### Out of Disk Space:
- ChromaDB can get large. Monitor with `df -h`
- Clean up unnecessary files
- Resize droplet storage

### Process Killed:
- Check logs: `tail -f ingestion.log`
- Likely OOM (Out of Memory) - reduce batch size
- The checkpoint system will help you know where it stopped

### Network Issues:
- HuggingFace dataset download might fail
- Retry the script - it will resume from checkpoint
- Use a different region closer to HuggingFace servers

## Performance Monitoring

Watch for these checkpoint messages every 1000 reviews:
```
[Checkpoint] Processed 1000 reviews so far...
  Products with reviews: 45
  Total in ChromaDB: 1000
```

This confirms progress and helps you estimate completion time.
