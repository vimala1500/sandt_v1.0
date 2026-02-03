# Railway Deployment Guide

This guide provides step-by-step instructions for deploying the Stock Analysis & Trading System to Railway.

## Prerequisites

- GitHub account
- Railway account (sign up at [railway.app](https://railway.app))
- Basic understanding of web deployments

## Quick Deploy (5 minutes)

### Step 1: Fork the Repository

1. Go to https://github.com/vimala1500/sandt_v1.0
2. Click "Fork" in the top right
3. Fork to your personal GitHub account

### Step 2: Connect to Railway

1. Log in to [Railway](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Authorize Railway to access your GitHub account
5. Select your forked `sandt_v1.0` repository

### Step 3: Configure Environment (Optional)

Railway will automatically use the defaults, but you can customize:

```
INDICATOR_PATH=./data/indicators
BACKTEST_PATH=./data/backtests
PORT=8050
DEBUG=false
```

To set environment variables:
1. Go to your project in Railway dashboard
2. Click "Variables" tab
3. Add the variables listed above

### Step 4: Deploy

Railway will automatically:
1. Detect Python and install dependencies from `requirements.txt`
2. Use `Procfile` to start gunicorn
3. Expose your app at a public URL (e.g., `https://your-app.up.railway.app`)

### Step 5: Access Your App

1. In Railway dashboard, click "Generate Domain"
2. Open the generated URL in your browser
3. You should see the Stock Scanner & Backtest Analyzer UI

## Data Persistence Strategies

⚠️ **Important**: Railway uses ephemeral storage by default. Data is lost on restart/redeploy.

### Option 1: Railway Volumes (Recommended for Production)

Railway offers persistent volumes:

1. In Railway dashboard, go to "Storage" tab
2. Click "New Volume"
3. Mount to `/app/data`
4. Update environment variables:
   ```
   INDICATOR_PATH=/app/data/indicators
   BACKTEST_PATH=/app/data/backtests
   ```

**Cost**: ~$5/month for 1GB

### Option 2: External Cloud Storage (AWS S3, GCS)

For large datasets, use cloud storage:

**AWS S3 Example**:
1. Create an S3 bucket
2. Add `boto3` to requirements.txt
3. Modify `data_loader.py` to read from S3
4. Set AWS credentials in Railway environment variables

**Benefits**: Scalable, shared across deployments, versioned

### Option 3: Pre-computed Results (Good for Demos)

For small demo datasets:

1. Run backtests locally:
   ```bash
   python test_local.py
   python main.py --mode full
   ```

2. Commit small result files:
   ```bash
   # Remove large files from .gitignore temporarily
   git add data/indicators/*.json
   git add data/backtests/summary.parquet
   git commit -m "Add pre-computed demo data"
   ```

3. Push to GitHub and redeploy

**Note**: Only suitable for small demo datasets (<10MB)

### Option 4: Database Backend

For production apps, replace file storage with a database:

1. Add Railway PostgreSQL service
2. Modify engines to store data in database
3. Use SQLAlchemy or similar ORM

**Benefits**: Persistent, queryable, scalable

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8050 | Server port (Railway sets automatically) |
| `HOST` | 0.0.0.0 | Server host |
| `INDICATOR_PATH` | ./data/indicators | Path to indicator storage |
| `BACKTEST_PATH` | ./data/backtests | Path to backtest results |
| `DEBUG` | false | Enable debug mode |

## Local Testing Before Deploy

Always test locally first:

```bash
# Clone and install
git clone https://github.com/YOUR_USERNAME/sandt_v1.0.git
cd sandt_v1.0
pip install -r requirements.txt

# Generate test data and run pipeline
python test_local.py

# Test web server
python app.py

# Test with gunicorn (production-like)
gunicorn app:server --bind 0.0.0.0:8050 --workers 2
```

Open http://localhost:8050 to verify everything works.

## Troubleshooting

### App Won't Start

**Symptom**: Deployment fails or crashes immediately

**Solutions**:
1. Check Railway logs for errors
2. Verify all dependencies in requirements.txt
3. Ensure Procfile is correct
4. Test locally with gunicorn

### UI Loads But No Data

**Symptom**: UI appears but shows "No data available"

**Solutions**:
1. Check if data directories exist
2. Verify INDICATOR_PATH and BACKTEST_PATH
3. Use Railway Volumes or pre-computed data
4. Check file permissions

### Slow Performance

**Symptom**: App is slow or times out

**Solutions**:
1. Increase gunicorn workers in Procfile (default: 2)
2. Increase timeout: `--timeout 300`
3. Upgrade Railway plan for more resources
4. Optimize data loading (cache, lazy loading)

### Memory Issues

**Symptom**: App crashes with memory errors

**Solutions**:
1. Reduce dataset size
2. Implement data pagination
3. Use streaming/chunked processing
4. Upgrade Railway plan (more memory)

## Advanced Configuration

### Custom Domain

1. In Railway dashboard, go to "Settings"
2. Add custom domain
3. Update DNS records as shown
4. SSL certificates are automatic

### Continuous Deployment

Railway automatically deploys on every push to main branch:

1. Make changes locally
2. Commit and push to GitHub
3. Railway detects changes and redeploys
4. Monitor deployment in Railway dashboard

### Multiple Environments

Create separate Railway projects for staging/production:

1. Deploy main branch to production
2. Deploy develop branch to staging
3. Use environment variables to differentiate

### Monitoring and Logs

View logs in Railway dashboard:
1. Click "Logs" tab
2. Real-time log streaming
3. Filter by level (info, error, etc.)
4. Download logs for analysis

## Cost Estimation

**Free Tier**:
- $5 credit/month
- Good for testing and demos
- Ephemeral storage only

**Hobby Plan** (~$10-20/month):
- 8GB RAM, 8 vCPU
- Persistent volumes available
- Custom domains
- Good for small production apps

**Pro Plan** (~$50+/month):
- More resources
- Advanced monitoring
- Team collaboration
- Priority support

## Security Best Practices

1. **Never commit secrets**: Use Railway environment variables
2. **Use HTTPS**: Railway provides automatic SSL
3. **Limit file uploads**: Validate and sanitize user inputs
4. **Regular updates**: Keep dependencies updated
5. **Monitor logs**: Watch for suspicious activity

## Support

- Railway Docs: https://docs.railway.app
- GitHub Issues: https://github.com/vimala1500/sandt_v1.0/issues
- Railway Discord: https://discord.gg/railway

## Next Steps

After deployment:
1. Upload your stock data (via API or manual)
2. Run indicator computation
3. Execute backtests
4. Use the scanner to find opportunities
5. Monitor performance and adjust parameters

## Migration from Colab

If migrating from Google Colab:

1. Export data from Google Drive:
   ```python
   # In Colab
   !zip -r data.zip /content/drive/MyDrive/stock_data
   ```

2. Upload to Railway Volume or S3

3. Update paths in environment variables

4. Test locally before deploying
