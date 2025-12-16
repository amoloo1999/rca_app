"""
RCA Competitor Analysis - Streamlit Web Application

A web-based interface for the Rate Comparison Analysis tool that:
1. Finds subject store and competitors via StorTrack API
2. Analyzes historical rate data from local database and API
3. Provides interactive data visualization and CSV export
"""

import streamlit as st
import pandas as pd
import os
import sys
from datetime import date, datetime
from typing import Dict, List, Any, Optional
import logging
from io import StringIO, BytesIO
from dotenv import load_dotenv

# Import from the original script
from RCA_CompetitorAnalysis import (
    StorTrackAPIClient,
    RatesDBManager,
    format_competitor_report,
    analyze_date_gaps,
    parse_api_rate_data,
    convert_db_rates_to_records,
    filter_unit_type,
    generate_csv2_report,
)

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="RCA Competitor Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better table display
st.markdown("""
<style>
    .stDataFrame {
        width: 100%;
    }
    .dataframe {
        font-size: 12px;
    }
    .css-1d391kg {
        padding-top: 1rem;
    }
    .step-header {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        'step': 1,
        'subject_store': None,
        'competitors': [],
        'selected_stores': [],
        'store_metadata': {},
        'rankings': {},
        'adjustment_factors': {},
        'name_mapping': {},
        'feature_mapping': {},
        'rates_data': [],
        'api_records': [],
        'db_records': [],
        'final_records': [],
        'output_csv1': None,
        'output_csv2': None,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# Setup logging
@st.cache_resource
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

setup_logging()

# Initialize API and DB clients
@st.cache_resource
def get_api_client():
    """Get cached StorTrack API client."""
    return StorTrackAPIClient(
        base_url=os.getenv('STORTRACK_API_URL', 'https://api.stortrack.com/api/'),
        username=os.getenv('STORTRACK_USERNAME', ''),
        password=os.getenv('STORTRACK_PASSWORD', ''),
        timeout=60
    )

@st.cache_resource
def get_db_manager():
    """Get cached database manager."""
    return RatesDBManager(
        server=os.getenv('DB_SERVER', ''),
        username=os.getenv('DB_USERNAME', ''),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_DATABASE', 'Stortrack'),
        driver=os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
    )


def render_step_header(step_num: int, title: str, description: str = ""):
    """Render a step header with consistent styling."""
    st.markdown(f"""
    <div class="step-header">
        <h2>Step {step_num}: {title}</h2>
        {f'<p>{description}</p>' if description else ''}
    </div>
    """, unsafe_allow_html=True)


def step1_search_subject_store():
    """Step 1: Search for subject store by address."""
    render_step_header(
        1, 
        "Find Subject Store",
        "Enter the address information to find your subject store"
    )
    
    with st.form("search_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            street_address = st.text_input("Street Address", placeholder="123 Main St")
            city = st.text_input("City*", placeholder="New York")
            zip_code = st.text_input("ZIP Code*", placeholder="10001")
            store_name = st.text_input("Store Name (optional)", placeholder="Public Storage")
        
        with col2:
            country = st.text_input("Country", value="United States")
            state = st.text_input("State*", placeholder="NY")
            company_name = st.text_input("Company Name (optional)", placeholder="Public Storage")
            radius = st.number_input("Search Radius (miles)", min_value=0.5, max_value=50.0, value=5.0, step=0.5)
        
        submitted = st.form_submit_button("🔍 Search for Subject Store", use_container_width=True)
        
        if submitted:
            if not city or not state:
                st.error("Please provide at least City and State")
                return
            
            with st.spinner("Searching for stores..."):
                api = get_api_client()
                stores = api.find_stores_by_address(
                    country=country,
                    state=state,
                    city=city,
                    zip_code=zip_code,
                    store_name=store_name,
                    company_name=company_name
                )
                
                if not stores:
                    st.error("No stores found. Please refine your search criteria.")
                    return
                
                # Store search results in session state
                st.session_state.search_results = stores
                st.session_state.radius = radius
                st.session_state.search_params = {
                    'city': city,
                    'state': state,
                    'zip': zip_code
                }
                st.success(f"Found {len(stores)} store(s)")
    
    # Display search results if available
    if 'search_results' in st.session_state and st.session_state.search_results:
        st.markdown("### Select Your Subject Store")
        
        # Create a nice display of stores
        store_options = []
        for store in st.session_state.search_results:
            label = f"{store.get('storename', 'Unknown')} - {store.get('address', '')}, {store.get('city', '')}, {store.get('state', '')} {store.get('zip', '')}"
            store_options.append(label)
        
        selected_idx = st.selectbox(
            "Choose the subject store:",
            range(len(store_options)),
            format_func=lambda i: store_options[i]
        )
        
        if st.button("✅ Confirm Subject Store", use_container_width=True):
            st.session_state.subject_store = st.session_state.search_results[selected_idx]
            st.session_state.step = 2
            st.rerun()


def step2_find_competitors():
    """Step 2: Find competitors around subject store."""
    render_step_header(
        2,
        "Find Competitors",
        f"Finding competitors within {st.session_state.radius} miles of the subject store"
    )
    
    subject = st.session_state.subject_store
    
    # Display subject store info
    st.markdown("### Subject Store")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Store Name", subject.get('storename', 'N/A'))
    with col2:
        st.metric("City", subject.get('city', 'N/A'))
    with col3:
        st.metric("State", subject.get('state', 'N/A'))
    
    st.write(f"**Address:** {subject.get('address', 'N/A')}, {subject.get('city', 'N/A')}, {subject.get('state', 'N/A')} {subject.get('zip', 'N/A')}")
    
    if st.button("🔍 Find Competitors", use_container_width=True):
        with st.spinner(f"Searching for competitors within {st.session_state.radius} miles..."):
            api = get_api_client()
            subject_id = subject.get('storeid')
            
            competitor_data = api.find_competitors(
                storeid=subject_id,
                coverage_zone=st.session_state.radius
            )
            
            if not competitor_data:
                st.error("Failed to retrieve competitor data")
                return
            
            # Parse competitors from response
            if isinstance(competitor_data, dict):
                competitors = competitor_data.get('competitorstores', [])
            elif isinstance(competitor_data, list):
                competitors = []
                for item in competitor_data:
                    if isinstance(item, dict):
                        nested_comps = item.get('competitorstores', [])
                        if nested_comps:
                            competitors.extend(nested_comps)
                        elif item.get('storeid') and item.get('storeid') != subject_id:
                            competitors.append(item)
            else:
                competitors = []
            
            st.session_state.competitors = competitors
            st.success(f"Found {len(competitors)} competitor(s)")
            st.session_state.show_competitor_report = True
    
    # Display competitor report if available
    if st.session_state.get('show_competitor_report') and st.session_state.competitors:
        st.markdown("### Competitor Report")
        
        # Format and display the report
        report = format_competitor_report(st.session_state.subject_store, st.session_state.competitors)
        st.text(report)
        
        # Create DataFrame for better visualization
        comp_df_data = []
        for comp in st.session_state.competitors:
            comp_df_data.append({
                'Store Name': comp.get('storename', 'N/A'),
                'Address': comp.get('address', 'N/A'),
                'City': comp.get('city', 'N/A'),
                'State': comp.get('state', 'N/A'),
                'ZIP': comp.get('zip', 'N/A'),
                'Distance (mi)': comp.get('distance', 'N/A'),
                'Store ID': comp.get('storeid', 'N/A'),
            })
        
        if comp_df_data:
            df = pd.DataFrame(comp_df_data)
            st.dataframe(df, use_container_width=True)
        
        if st.button("▶️ Continue to Rate Analysis", use_container_width=True):
            st.session_state.step = 3
            st.rerun()


def step3_select_stores():
    """Step 3: Select stores for rate analysis."""
    render_step_header(
        3,
        "Select Stores for Analysis",
        "Choose which stores to include in the rate comparison"
    )
    
    # Always include subject store
    all_stores = [st.session_state.subject_store] + st.session_state.competitors
    
    st.markdown("### Available Stores")
    st.info("💡 The subject store is automatically included. Select competitors to analyze.")
    
    # Create selection interface
    selected_indices = []
    
    for idx, store in enumerate(all_stores):
        is_subject = (idx == 0)
        store_label = f"{store.get('storename', 'Unknown')} - {store.get('city', '')}, {store.get('state', '')} ({store.get('distance', '0.0')} mi)"
        
        if is_subject:
            st.checkbox(
                f"✨ **SUBJECT:** {store_label}",
                value=True,
                disabled=True,
                key=f"store_select_{idx}"
            )
            selected_indices.append(idx)
        else:
            if st.checkbox(store_label, key=f"store_select_{idx}"):
                selected_indices.append(idx)
    
    if st.button("✅ Confirm Store Selection", use_container_width=True):
        if len(selected_indices) == 0:
            st.error("Please select at least the subject store")
            return
        
        st.session_state.selected_stores = [all_stores[i] for i in selected_indices]
        st.success(f"Selected {len(st.session_state.selected_stores)} store(s) for analysis")
        st.session_state.step = 4
        st.rerun()


def step4_store_metadata():
    """Step 4: Collect store metadata (Year Built, SF, Distance)."""
    render_step_header(
        4,
        "Store Metadata",
        "Provide additional information about each store"
    )
    
    st.markdown("### Enter Store Details")
    st.info("💡 This information will be used for comparative analysis. Leave blank if unknown.")
    
    metadata = {}
    
    for store in st.session_state.selected_stores:
        store_id = store.get('storeid')
        store_name = store.get('storename', 'Unknown')
        
        st.markdown(f"#### {store_name}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            year_built = st.number_input(
                "Year Built",
                min_value=1900,
                max_value=datetime.now().year,
                value=None,
                key=f"year_{store_id}",
                help="Enter 4-digit year"
            )
        
        with col2:
            square_footage = st.number_input(
                "Square Footage",
                min_value=0,
                value=None,
                key=f"sf_{store_id}",
                help="Total rentable square feet"
            )
        
        with col3:
            distance = st.number_input(
                "Distance (miles)",
                min_value=0.0,
                value=float(store.get('distance', 0.0)),
                step=0.1,
                key=f"dist_{store_id}",
                help="Distance from subject store"
            )
        
        metadata[store_id] = {
            'year_built': year_built,
            'square_footage': square_footage,
            'distance': distance
        }
    
    if st.button("✅ Continue", use_container_width=True):
        st.session_state.store_metadata = metadata
        st.session_state.step = 5
        st.rerun()


def step5_store_rankings():
    """Step 5: Collect store rankings."""
    render_step_header(
        5,
        "Store Rankings",
        "Rate each store across key categories (1-5, where 5 is best)"
    )
    
    st.markdown("### Ranking Categories")
    st.info("💡 Rate each store from 1 (Poor) to 5 (Excellent) for each category")
    
    categories = [
        ("Location", "Overall location quality and market position"),
        ("Visibility", "How visible the facility is from main roads"),
        ("Access", "Ease of access and entry/exit convenience"),
        ("Curb Appeal", "External appearance and attractiveness"),
        ("Competition", "Competitive position in the market (5 = less competition)"),
        ("Signage", "Quality and effectiveness of signage"),
        ("Security", "Security features and perception"),
        ("Technology", "Website, online booking, and tech features"),
    ]
    
    rankings = {}
    
    for store in st.session_state.selected_stores:
        store_id = store.get('storeid')
        store_name = store.get('storename', 'Unknown')
        
        st.markdown(f"#### {store_name}")
        
        rankings[store_id] = {}
        
        cols = st.columns(4)
        for idx, (category, description) in enumerate(categories):
            with cols[idx % 4]:
                rank = st.selectbox(
                    category,
                    options=[1, 2, 3, 4, 5],
                    index=2,  # Default to 3
                    key=f"rank_{store_id}_{category}",
                    help=description
                )
                rankings[store_id][category] = rank
        
        st.divider()
    
    if st.button("✅ Continue", use_container_width=True):
        st.session_state.rankings = rankings
        st.session_state.step = 6
        st.rerun()


def step6_adjustment_factors():
    """Step 6: Collect adjustment factors."""
    render_step_header(
        6,
        "Adjustment Factors",
        "Enter percentage adjustments for various market factors"
    )
    
    st.markdown("### Market Adjustment Factors")
    st.info("💡 Enter adjustments as percentages (e.g., 2.5 for 2.5%). Can be positive or negative.")
    
    factors = [
        "Location",
        "Visibility",
        "Access",
        "Curb Appeal",
        "Competition",
        "Signage",
        "Security",
        "Technology",
        "Size",
        "Age",
        "Other",
    ]
    
    adjustment_factors = {}
    
    cols = st.columns(3)
    for idx, factor in enumerate(factors):
        with cols[idx % 3]:
            value = st.number_input(
                f"{factor} (%)",
                min_value=-100.0,
                max_value=100.0,
                value=0.0,
                step=0.1,
                key=f"adj_{factor}",
                help=f"Adjustment percentage for {factor}"
            )
            adjustment_factors[factor] = value / 100.0  # Convert to decimal
    
    if st.button("✅ Continue", use_container_width=True):
        st.session_state.adjustment_factors = adjustment_factors
        st.session_state.step = 7
        st.rerun()


def step7_custom_names():
    """Step 7: Edit store names for CSV output."""
    render_step_header(
        7,
        "Customize Store Names",
        "Edit how store names will appear in the output files"
    )
    
    st.markdown("### Store Name Mapping")
    st.info("💡 Customize store names for easier identification in reports. Leave blank to keep original.")
    
    name_mapping = {}
    
    for store in st.session_state.selected_stores:
        store_id = store.get('storeid')
        original_name = store.get('storename', 'Unknown')
        
        custom_name = st.text_input(
            f"**{original_name}**",
            value=original_name,
            key=f"name_{store_id}",
            help="Enter custom name or keep original"
        )
        
        name_mapping[store_id] = custom_name
    
    if st.button("✅ Continue", use_container_width=True):
        st.session_state.name_mapping = name_mapping
        st.session_state.step = 8
        st.rerun()


def step8_fetch_data():
    """Step 8: Fetch rate data from database and API."""
    render_step_header(
        8,
        "Fetch Rate Data",
        "Retrieving historical rate data from database and API"
    )
    
    # Define date range
    to_date = date.today()
    from_date = date(2024, 12, 1)  # Trailing 12 months starting Dec 1, 2024
    
    st.markdown(f"### Analysis Period")
    st.info(f"📅 **From:** {from_date.strftime('%Y-%m-%d')} | **To:** {to_date.strftime('%Y-%m-%d')}")
    
    selected_ids = [s.get('storeid') for s in st.session_state.selected_stores]
    
    if st.button("🔍 Fetch Data", use_container_width=True):
        # Step 8a: Query database
        with st.spinner("Querying database for existing rate data..."):
            db = get_db_manager()
            rates_by_store, dates_by_store = db.get_trailing_12_month_rates(
                selected_ids,
                from_date,
                to_date
            )
            
            total_db_records = sum(len(rates) for rates in rates_by_store.values())
            st.success(f"✓ Found {total_db_records} rate records in database")
            
            st.session_state.rates_by_store = rates_by_store
            st.session_state.dates_by_store = dates_by_store
        
        # Step 8b: Analyze gaps
        with st.spinner("Analyzing data gaps..."):
            gaps_by_store = analyze_date_gaps(dates_by_store, from_date, to_date)
            st.session_state.gaps_by_store = gaps_by_store
        
        # Display gap analysis
        st.markdown("### Data Gap Analysis")
        
        gap_data = []
        total_missing_days = 0
        
        for store in st.session_state.selected_stores:
            store_id = store.get('storeid')
            store_name = st.session_state.name_mapping.get(store_id, store.get('storename', 'Unknown'))
            missing_dates = gaps_by_store.get(store_id, [])
            
            gap_data.append({
                'Store': store_name,
                'Store ID': store_id,
                'Missing Days': len(missing_dates),
                'Coverage %': f"{((365 - len(missing_dates)) / 365 * 100):.1f}%"
            })
            
            total_missing_days += len(missing_dates)
        
        gap_df = pd.DataFrame(gap_data)
        st.dataframe(gap_df, use_container_width=True)
        
        # API fetch option
        if total_missing_days > 0:
            st.markdown("### API Data Fetch")
            st.warning(f"⚠️ Total missing days across all stores: {total_missing_days}")
            
            estimated_cost = total_missing_days * 12.50
            st.info(f"💰 Estimated API cost: ${estimated_cost:,.2f} ({total_missing_days} days × $12.50/day)")
            
            fetch_option = st.radio(
                "Would you like to fetch missing data from the API?",
                ["No - Use database data only", "Yes - Fetch all missing data", "Select specific stores"],
                key="api_fetch_option"
            )
            
            if fetch_option == "Yes - Fetch all missing data":
                if st.button(f"💳 Confirm API Fetch (${estimated_cost:,.2f})", use_container_width=True):
                    fetch_api_data(selected_ids, gaps_by_store, from_date, to_date)
                    st.session_state.step = 9
                    st.rerun()
            
            elif fetch_option == "Select specific stores":
                st.markdown("#### Select Stores for API Fetch")
                
                api_store_ids = []
                for store in st.session_state.selected_stores:
                    store_id = store.get('storeid')
                    store_name = st.session_state.name_mapping.get(store_id, store.get('storename', 'Unknown'))
                    missing_days = len(gaps_by_store.get(store_id, []))
                    
                    if missing_days > 0:
                        if st.checkbox(
                            f"{store_name} - {missing_days} missing days (${missing_days * 12.50:,.2f})",
                            key=f"api_select_{store_id}"
                        ):
                            api_store_ids.append(store_id)
                
                if api_store_ids:
                    selected_cost = sum(len(gaps_by_store.get(sid, [])) * 12.50 for sid in api_store_ids)
                    if st.button(f"💳 Confirm API Fetch for Selected (${selected_cost:,.2f})", use_container_width=True):
                        fetch_api_data(api_store_ids, gaps_by_store, from_date, to_date)
                        st.session_state.step = 9
                        st.rerun()
            
            else:  # No API fetch
                if st.button("✅ Continue with Database Data Only", use_container_width=True):
                    st.session_state.api_records = []
                    st.session_state.step = 9
                    st.rerun()
        
        else:
            st.success("✓ No data gaps found! All data available in database.")
            if st.button("✅ Continue", use_container_width=True):
                st.session_state.api_records = []
                st.session_state.step = 9
                st.rerun()


def fetch_api_data(store_ids: List[int], gaps_by_store: Dict, from_date: date, to_date: date):
    """Fetch missing data from API for specified stores."""
    api = get_api_client()
    api_records = []
    
    # Build store info map
    api_store_info = {}
    for store in st.session_state.selected_stores:
        sid = store.get('storeid')
        api_store_info[sid] = {
            'store_id': sid,
            'store_name': store.get('storename', ''),
            'address': store.get('address', ''),
            'city': store.get('city', ''),
            'state': store.get('state', ''),
            'zip': store.get('zip', ''),
            'distance': store.get('distance', '')
        }
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_stores = len(store_ids)
    
    for idx, store_id in enumerate(store_ids):
        missing_dates = gaps_by_store.get(store_id, [])
        if not missing_dates:
            continue
        
        store_name = st.session_state.name_mapping.get(store_id, f"Store {store_id}")
        status_text.text(f"Fetching data for {store_name}... ({idx+1}/{total_stores})")
        
        # Group consecutive dates into ranges
        ranges = []
        start = missing_dates[0]
        end = missing_dates[0]
        for d in missing_dates[1:]:
            if (d - end).days == 1:
                end = d
            else:
                ranges.append((start, end))
                start = end = d
        ranges.append((start, end))
        
        # Fetch each range
        for range_start, range_end in ranges:
            api_data = api.fetch_historical_data(
                store_id,
                range_start.strftime('%Y-%m-%d'),
                range_end.strftime('%Y-%m-%d')
            )
            
            if api_data:
                parsed_records = parse_api_rate_data(api_data, api_store_info)
                api_records.extend(parsed_records)
        
        progress_bar.progress((idx + 1) / total_stores)
    
    status_text.text(f"✓ API fetch complete: {len(api_records)} records retrieved")
    st.session_state.api_records = api_records


def step9_feature_codes():
    """Step 9: Assign feature codes to unit sizes."""
    render_step_header(
        9,
        "Feature Code Assignment",
        "Assign feature codes (CC, DU, etc.) to different unit sizes"
    )
    
    # Combine DB and API records
    db_records = convert_db_rates_to_records(
        st.session_state.rates_by_store,
        {s.get('storeid'): s for s in st.session_state.selected_stores}
    )
    
    all_records = db_records + st.session_state.api_records
    
    # Filter to Unit type only
    all_records = filter_unit_type(all_records, "Unit")
    
    # Apply name mapping
    for record in all_records:
        store_id = record.get('store_id')
        if store_id in st.session_state.name_mapping:
            record['store_name'] = st.session_state.name_mapping[store_id]
    
    st.session_state.all_records = all_records
    
    st.markdown("### Unit Size & Feature Codes")
    st.info("💡 Assign feature codes like 'CC' (Climate Controlled), 'DU' (Drive Up), etc. to each unit size")
    
    # Get unique size/feature combinations
    unique_combos = {}
    for record in all_records:
        size = record.get('size', 'Unknown')
        cc = record.get('climate_controlled', False)
        du = record.get('drive_up', False)
        
        key = (size, cc, du)
        if key not in unique_combos:
            unique_combos[key] = {
                'size': size,
                'cc': cc,
                'du': du,
                'suggested': []
            }
            
            # Auto-suggest codes
            if cc:
                unique_combos[key]['suggested'].append('CC')
            if du:
                unique_combos[key]['suggested'].append('DU')
    
    feature_mapping = {}
    
    st.markdown("#### Assign Codes")
    for idx, (key, info) in enumerate(unique_combos.items()):
        size = info['size']
        suggested = '-'.join(info['suggested']) if info['suggested'] else ''
        
        col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
        
        with col1:
            st.text(f"Size: {size}")
        with col2:
            st.text(f"CC: {'✓' if info['cc'] else '✗'}")
        with col3:
            st.text(f"DU: {'✓' if info['du'] else '✗'}")
        with col4:
            code = st.text_input(
                "Feature Code",
                value=suggested,
                key=f"feature_{idx}",
                placeholder="CC-DU",
                help="Enter feature codes separated by hyphens"
            )
            feature_mapping[key] = code
    
    if st.button("✅ Continue", use_container_width=True):
        # Apply feature codes to records
        for record in all_records:
            size = record.get('size', 'Unknown')
            cc = record.get('climate_controlled', False)
            du = record.get('drive_up', False)
            key = (size, cc, du)
            record['feature_code'] = feature_mapping.get(key, '')
        
        st.session_state.final_records = all_records
        st.session_state.step = 10
        st.rerun()


def step10_export_results():
    """Step 10: Export and display results."""
    render_step_header(
        10,
        "Results & Export",
        "View and download your rate analysis results"
    )
    
    if not st.session_state.final_records:
        st.error("No data available for export")
        return
    
    # Generate output filenames
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    city_slug = st.session_state.search_params.get('city', 'unknown').replace(' ', '_').lower()
    output_file_csv1 = f"RCA_{city_slug}_{timestamp}_data.csv"
    output_file_csv2 = f"RCA_{city_slug}_{timestamp}_summary.csv"
    
    # Create DataFrames
    st.markdown("### 📊 CSV #1: Full Data Dump")
    
    # Prepare CSV1 data
    csv1_data = []
    for record in st.session_state.final_records:
        csv1_data.append({
            'Store Name': record.get('store_name', ''),
            'Store ID': record.get('store_id', ''),
            'Address': record.get('address', ''),
            'City': record.get('city', ''),
            'State': record.get('state', ''),
            'ZIP': record.get('zip', ''),
            'Distance (mi)': record.get('distance', ''),
            'Size': record.get('size', ''),
            'Feature Code': record.get('feature_code', ''),
            'Regular Rate': record.get('regular_rate', ''),
            'Online Rate': record.get('online_rate', ''),
            'Date Collected': record.get('date_collected', ''),
            'Climate Controlled': record.get('climate_controlled', False),
            'Drive Up': record.get('drive_up', False),
            'Promo': record.get('promo', ''),
        })
    
    df1 = pd.DataFrame(csv1_data)
    
    # Display with pagination
    st.dataframe(df1, use_container_width=True, height=400)
    
    # Download button for CSV1
    csv1_buffer = StringIO()
    df1.to_csv(csv1_buffer, index=False)
    st.download_button(
        label="📥 Download CSV #1 (Full Data)",
        data=csv1_buffer.getvalue(),
        file_name=output_file_csv1,
        mime="text/csv",
        use_container_width=True
    )
    
    st.divider()
    
    # Generate CSV2
    st.markdown("### 📈 CSV #2: Summary with Adjustments")
    
    # Create CSV2 using the existing function
    csv2_path = output_file_csv2
    generate_csv2_report(
        st.session_state.final_records,
        st.session_state.selected_stores,
        st.session_state.rankings,
        st.session_state.adjustment_factors,
        csv2_path
    )
    
    # Read and display CSV2
    df2 = pd.read_csv(csv2_path)
    st.dataframe(df2, use_container_width=True, height=400)
    
    # Download button for CSV2
    with open(csv2_path, 'r') as f:
        csv2_content = f.read()
    
    st.download_button(
        label="📥 Download CSV #2 (Summary Report)",
        data=csv2_content,
        file_name=output_file_csv2,
        mime="text/csv",
        use_container_width=True
    )
    
    # Summary statistics
    st.divider()
    st.markdown("### 📊 Analysis Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", len(st.session_state.final_records))
    with col2:
        st.metric("Stores Analyzed", len(st.session_state.selected_stores))
    with col3:
        db_count = len(st.session_state.all_records) - len(st.session_state.api_records)
        st.metric("DB Records", db_count)
    with col4:
        st.metric("API Records", len(st.session_state.api_records))
    
    # Reset button
    if st.button("🔄 Start New Analysis", use_container_width=True):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()


def main():
    """Main application logic."""
    
    # Header
    st.title("📊 RCA Competitor Analysis")
    st.markdown("*Rate Comparison Analysis for Self-Storage Facilities*")
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("## Navigation")
        st.markdown("---")
        
        steps = [
            "1️⃣ Find Subject Store",
            "2️⃣ Find Competitors",
            "3️⃣ Select Stores",
            "4️⃣ Store Metadata",
            "5️⃣ Store Rankings",
            "6️⃣ Adjustment Factors",
            "7️⃣ Custom Names",
            "8️⃣ Fetch Data",
            "9️⃣ Feature Codes",
            "🏁 Export Results"
        ]
        
        for i, step in enumerate(steps, 1):
            if i == st.session_state.step:
                st.markdown(f"**➡️ {step}**")
            elif i < st.session_state.step:
                st.markdown(f"✅ {step}")
            else:
                st.markdown(f"⚪ {step}")
        
        st.markdown("---")
        
        # Debug info
        if st.checkbox("Show Debug Info"):
            st.json({
                'step': st.session_state.step,
                'selected_stores': len(st.session_state.selected_stores),
                'final_records': len(st.session_state.final_records) if st.session_state.final_records else 0
            })
    
    # Main content - route to appropriate step
    step_functions = {
        1: step1_search_subject_store,
        2: step2_find_competitors,
        3: step3_select_stores,
        4: step4_store_metadata,
        5: step5_store_rankings,
        6: step6_adjustment_factors,
        7: step7_custom_names,
        8: step8_fetch_data,
        9: step9_feature_codes,
        10: step10_export_results,
    }
    
    current_step = st.session_state.step
    if current_step in step_functions:
        step_functions[current_step]()
    else:
        st.error(f"Invalid step: {current_step}")


if __name__ == "__main__":
    main()
