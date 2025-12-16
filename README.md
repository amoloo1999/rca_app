# RCA Competitor Analysis - Streamlit Web App

A web-based interface for the Rate Comparison Analysis (RCA) tool that helps analyze self-storage facility rates and competitors.

## Features

- 🔍 **Subject Store Search**: Find your facility using address, city, state, or ZIP
- 🏢 **Competitor Discovery**: Automatically find competitors within a customizable radius
- 📊 **Rate Analysis**: Compare historical rates across multiple facilities
- 💾 **Data Sources**: Query local database (free) with option to fetch missing data via API
- 📈 **Interactive Visualizations**: View data in clean, readable tables
- 📥 **CSV Export**: Download full data dumps and summary reports
- ⚙️ **Customizable**: Edit store names, assign feature codes, and apply adjustment factors

## Project Structure

```
rca_app/
├── app.py                          # Main Streamlit application
├── RCA_CompetitorAnalysis.py       # Core business logic (original script)
├── requirements.txt                # Python dependencies
├── .env.example                    # Template for environment variables
├── .gitignore                      # Git ignore rules
└── README.md                       # This file
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- SQL Server with ODBC Driver 17
- StorTrack API credentials
- Database access credentials

### 2. Install Dependencies

```bash
# Create virtual environment (optional but recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 3. Configure Environment Variables

1. Copy the example environment file:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` and fill in your credentials:
   ```env
   # StorTrack API Credentials
   STORTRACK_API_URL=https://api.stortrack.com/api/
   STORTRACK_USERNAME=your_actual_username
   STORTRACK_PASSWORD=your_actual_password

   # SQL Server Database Credentials
   DB_SERVER=your_server_address
   DB_USERNAME=your_db_username
   DB_PASSWORD=your_db_password
   DB_DATABASE=Stortrack
   DB_DRIVER=ODBC Driver 17 for SQL Server
   ```

### 4. Run Locally

```bash
streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`

## Usage Guide

### Step-by-Step Workflow

#### **Step 1: Find Subject Store**
- Enter your facility's address information
- Set search radius (default: 5 miles)
- Click "Search for Subject Store"
- Select your facility from the results

#### **Step 2: Find Competitors**
- Review subject store details
- Click "Find Competitors"
- View competitor report with distances and details

#### **Step 3: Select Stores**
- Choose which competitors to include in analysis
- Subject store is automatically included

#### **Step 4: Store Metadata**
- Enter Year Built, Square Footage, and Distance for each store
- This data is optional but recommended for better analysis

#### **Step 5: Store Rankings**
- Rate each store (1-5) across 8 categories:
  - Location, Visibility, Access, Curb Appeal
  - Competition, Signage, Security, Technology

#### **Step 6: Adjustment Factors**
- Enter percentage adjustments for various factors
- Can be positive or negative (e.g., 2.5 for +2.5%)

#### **Step 7: Custom Names**
- Edit how store names appear in output files
- Makes reports more readable

#### **Step 8: Fetch Data**
- App queries local database first (FREE)
- View gap analysis showing missing data
- Option to fetch missing data from API ($12.50/day)
- Choose to fetch all or select specific stores

#### **Step 9: Feature Codes**
- Assign codes like "CC" (Climate Controlled), "DU" (Drive Up)
- App auto-suggests codes based on unit features

#### **Step 10: Export Results**
- View data in interactive tables
- Download two CSV files:
  - **CSV #1**: Full data dump with all rate records
  - **CSV #2**: Summary report with averages and adjustments

## Output Files

### CSV #1: Full Data Dump
Contains every rate record with columns:
- Store Name, ID, Address, City, State, ZIP
- Distance from subject store
- Unit Size and Feature Code
- Regular Rate, Online Rate, Promo
- Date Collected
- Feature flags (Climate Controlled, Drive Up, etc.)

### CSV #2: Summary Report
Grouped averages with:
- Store comparisons by unit size
- Applied ranking adjustments
- Market adjustment factors
- Calculated competitive positioning

## API Cost Management

The app provides transparent cost estimation:
- Database queries are **FREE**
- API calls cost **$12.50 per day of data**
- Gap analysis shows exactly what's missing
- Option to fetch all or select specific stores
- Confirmation required before API charges

## Deploying to Replit

### 1. Create New Repl

1. Go to [Replit](https://replit.com)
2. Click "Create Repl"
3. Choose "Python" template
4. Name it (e.g., "RCA-Competitor-Analysis")

### 2. Upload Files

Upload all project files:
- `app.py`
- `RCA_CompetitorAnalysis.py`
- `requirements.txt`
- `.env.example`

### 3. Configure Secrets

In Replit, go to "Secrets" (lock icon in left sidebar):

```
STORTRACK_API_URL = https://api.stortrack.com/api/
STORTRACK_USERNAME = your_username
STORTRACK_PASSWORD = your_password
DB_SERVER = your_server
DB_USERNAME = your_db_username
DB_PASSWORD = your_db_password
DB_DATABASE = Stortrack
DB_DRIVER = ODBC Driver 17 for SQL Server
```

### 4. Configure Run Command

Create or edit `.replit` file:

```toml
run = "streamlit run app.py --server.port 5000 --server.address 0.0.0.0"
```

### 5. Run the App

Click the "Run" button. Replit will:
- Install dependencies from `requirements.txt`
- Start the Streamlit server
- Provide a URL to access your app

## Troubleshooting

### Database Connection Issues

If you get "ODBC Driver not found":
- Install ODBC Driver 17 for SQL Server
- Windows: Download from Microsoft
- Linux/Replit: May need to use different driver or connection method

### API Authentication Errors

- Verify credentials in `.env` or Replit Secrets
- Check API URL is correct
- Ensure StorTrack account is active

### Import Errors

```bash
# Make sure all dependencies are installed
pip install -r requirements.txt --upgrade
```

### Port Already in Use

```bash
# Kill existing Streamlit processes
# Windows:
taskkill /F /IM streamlit.exe
# Mac/Linux:
pkill -f streamlit
```

## Development Notes

### Key Technologies

- **Streamlit**: Web framework for data apps
- **Pandas**: Data manipulation and CSV export
- **pyodbc**: SQL Server database connectivity
- **requests**: StorTrack API communication
- **python-dotenv**: Environment variable management

### Session State Management

The app uses Streamlit's session state to maintain:
- Current step in workflow
- Selected stores and metadata
- Fetched rate data
- User inputs across steps

### Caching Strategy

- API and DB clients are cached with `@st.cache_resource`
- Reduces redundant authentication and connections
- Improves performance across reruns

## Feature Examples to Review

Here are all the interactive features - let me know which to simplify:

### ✅ KEEP AS-IS (Core Features)
1. Address search for subject store
2. Competitor discovery with radius
3. Store selection for analysis
4. Database querying (free)
5. API cost estimation and confirmation
6. CSV export with download buttons
7. Interactive data tables

### 🤔 REVIEW FOR SIMPLIFICATION

#### **Store Metadata Entry** (Step 4)
- Manual entry of Year Built, Square Footage, Distance
- **Could simplify**: Make all optional, or auto-populate from database

#### **Store Rankings** (Step 5)
- Rate each store 1-5 across 8 categories
- **Could simplify**: Reduce to 3-4 key categories, or make optional

#### **Adjustment Factors** (Step 6)
- Enter 11 different percentage adjustments
- **Could simplify**: Pre-set common adjustments, reduce to 5 key factors

#### **Custom Store Names** (Step 7)
- Edit each store name for output
- **Could simplify**: Auto-generate readable names, skip this step

#### **Feature Code Assignment** (Step 9)
- Manually assign codes to each unit size/feature combo
- **Could simplify**: Fully automate based on flags (CC, DU, etc.)

Let me know which features you'd like to simplify or keep!

## License

Internal use only - Revenue Management tool

## Support

For issues or questions, contact the development team.
