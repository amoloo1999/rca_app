# Quick Setup Guide - RCA Competitor Analysis App

## ⚡ Fast Setup (5 Minutes)

### Step 1: Configure Credentials

1. **Copy the environment template:**
   ```powershell
   copy .env.example .env
   ```

2. **Edit .env with your credentials:**
   ```powershell
   notepad .env
   ```

3. **Fill in these values:**
   ```
   STORTRACK_API_URL=https://api.stortrack.com/api/
   STORTRACK_USERNAME=your_username
   STORTRACK_PASSWORD=your_password
   DB_SERVER=your_sql_server
   DB_USERNAME=your_db_user
   DB_PASSWORD=your_db_pass
   DB_DATABASE=Stortrack
   ```

### Step 2: Run the App

**Option A - Quick Start (Recommended):**
```powershell
.\run.bat
```

**Option B - Manual:**
```powershell
pip install -r requirements.txt
streamlit run app.py
```

### Step 3: Use the App

1. Browser opens to `http://localhost:8501`
2. Enter address to find subject store
3. Find competitors
4. Follow the 10-step workflow
5. Download your CSV reports

## 🎯 All User Inputs Preserved

Every input from your original script is in the web app:

✅ Address search (street, city, state, ZIP, radius)
✅ Store selection (subject + competitors)
✅ Store metadata (Year Built, SF, Distance)
✅ Store rankings (8 categories × all stores)
✅ Adjustment factors (11 different percentages)
✅ Custom store names
✅ Feature code assignments
✅ API fetch decisions with cost approval

## 🚀 Ready for Replit

All files are configured for Replit deployment:
- `.replit` - Run configuration
- `pyproject.toml` - Dependency management
- Environment variables via Secrets tab

## 💡 Tips

- **Database Access**: Make sure your SQL Server allows connections from your IP
- **API Limits**: The app respects the 3000 calls/hour limit
- **Session State**: Your progress is saved as you go through steps
- **CSV Downloads**: Files are generated on-the-fly and downloadable

## 🐛 Troubleshooting

**"Module not found"**: Run `pip install -r requirements.txt`

**"Can't connect to database"**: Check DB credentials in `.env`

**"API authentication failed"**: Verify StorTrack credentials

**"Port already in use"**: Kill existing Streamlit process or use different port

## 📞 Need Help?

All features from your original script are preserved. The web interface just makes them more accessible and user-friendly!
