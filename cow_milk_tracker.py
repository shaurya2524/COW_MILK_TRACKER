import streamlit as st
import pandas as pd
from datetime import datetime, date
import gspread
from google.oauth2.service_account import Credentials
import json

# Configure page
st.set_page_config(
    page_title="Dairy Farm Management System",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Google Sheets Integration Functions
@st.cache_resource
# Replace your initialize_gsheets_connection function with this updated version:

@st.cache_resource
def initialize_gsheets_connection():
    """Initialize Google Sheets connection using gspread"""
    try:
        # Check if secrets are available
        if "connections" not in st.secrets or "gsheet" not in st.secrets["connections"]:
            st.warning("⚠️ Google Sheets credentials not found. Running in local mode.")
            return None
            
        # Define the scope
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Get credentials from Streamlit secrets (updated path)
        gsheet_config = st.secrets["connections"]["gsheet"]
        credentials_dict = {
            "type": gsheet_config["type"],
            "project_id": gsheet_config["project_id"],
            "private_key_id": gsheet_config["private_key_id"],
            "private_key": gsheet_config["private_key"],
            "client_email": gsheet_config["client_email"],
            "client_id": gsheet_config["client_id"],
            "auth_uri": gsheet_config["auth_uri"],
            "token_uri": gsheet_config["token_uri"],
            "auth_provider_x509_cert_url": gsheet_config.get("auth_provider_x509_cert_url", "https://www.googleapis.com/oauth2/v1/certs"),
            "client_x509_cert_url": gsheet_config.get("client_x509_cert_url", f"https://www.googleapis.com/robot/v1/metadata/x509/{gsheet_config['client_email']}")
        }
        
        # Create credentials
        credentials = Credentials.from_service_account_info(credentials_dict, scopes=scope)
        
        # Authorize and return the client
        gc = gspread.authorize(credentials)
        
        # Open the spreadsheet using the ID from secrets
        spreadsheet_id = gsheet_config["spreadsheet"]
        sheet = gc.open_by_key(spreadsheet_id)
        
        st.success("✅ Successfully connected to Google Sheets!")
        return sheet
        
    except Exception as e:
        st.error(f"Failed to connect to Google Sheets: {e}")
        st.info("💡 The app will continue to work in local mode (data won't be saved to Google Sheets)")
        return None

def get_worksheet(sheet, worksheet_name):
    """Get or create a worksheet"""
    try:
        return sheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        # Create the worksheet if it doesn't exist
        return sheet.add_worksheet(title=worksheet_name, rows=1000, cols=10)

def load_workers_from_sheets(sheet):
    """Load workers from Google Sheets"""
    try:
        worksheet = get_worksheet(sheet, "workers")
        data = worksheet.get_all_records()
        
        if not data:
            # Initialize with default workers
            default_workers = ["John Doe", "Mary Smith", "David Johnson", "Sarah Wilson"]
            worksheet.clear()
            worksheet.append_row(["name"])
            for worker in default_workers:
                worksheet.append_row([worker])
            return default_workers
        
        return [row['name'] for row in data if row.get('name')]
    except Exception as e:
        st.error(f"Error loading workers: {e}")
        return ["John Doe", "Mary Smith", "David Johnson", "Sarah Wilson"]

def save_workers_to_sheets(sheet, workers):
    """Save workers to Google Sheets"""
    try:
        worksheet = get_worksheet(sheet, "workers")
        worksheet.clear()
        worksheet.append_row(["name"])
        for worker in workers:
            worksheet.append_row([worker])
        return True
    except Exception as e:
        st.error(f"Failed to save workers: {e}")
        return False

def load_cow_assignments_from_sheets(sheet):
    """Load cow assignments from Google Sheets"""
    try:
        worksheet = get_worksheet(sheet, "cow_assignments")
        data = worksheet.get_all_records()
        
        if not data:
            return {}
        
        assignments = {}
        for row in data:
            if row.get('cow_number') and row.get('worker_name'):
                try:
                    cow_num = int(row['cow_number'])
                    assignments[cow_num] = row['worker_name']
                except ValueError:
                    continue
        
        return assignments
    except Exception as e:
        st.error(f"Error loading cow assignments: {e}")
        return {}

def save_cow_assignments_to_sheets(sheet, assignments):
    """Save cow assignments to Google Sheets"""
    try:
        worksheet = get_worksheet(sheet, "cow_assignments")
        worksheet.clear()
        worksheet.append_row(["cow_number", "worker_name"])
        
        for cow_number, worker_name in assignments.items():
            worksheet.append_row([cow_number, worker_name])
        
        return True
    except Exception as e:
        st.error(f"Failed to save cow assignments: {e}")
        return False

def load_milk_data_from_sheets(sheet):
    """Load milk data from Google Sheets"""
    try:
        worksheet = get_worksheet(sheet, "milk_data")
        data = worksheet.get_all_records()
        
        if not data:
            return []
        
        # Clean and validate data
        clean_data = []
        for row in data:
            if row.get('date') and row.get('cow_number') and row.get('milk_liters'):
                try:
                    # Ensure numeric values are properly converted
                    row['cow_number'] = int(row['cow_number'])
                    row['milk_liters'] = float(row['milk_liters'])
                    clean_data.append(row)
                except (ValueError, TypeError):
                    continue
        
        return clean_data
    except Exception as e:
        st.error(f"Error loading milk data: {e}")
        return []

def save_milk_data_to_sheets(sheet, milk_data):
    """Save all milk data to Google Sheets"""
    try:
        worksheet = get_worksheet(sheet, "milk_data")
        worksheet.clear()
        
        if milk_data:
            # Get headers from first record
            headers = list(milk_data[0].keys())
            worksheet.append_row(headers)
            
            # Add data rows
            for record in milk_data:
                row = [record.get(header, '') for header in headers]
                worksheet.append_row(row)
        else:
            # Just add headers if no data
            headers = ['date', 'time', 'cow_number', 'milk_liters', 'worker', 'notes', 'timestamp']
            worksheet.append_row(headers)
        
        return True
    except Exception as e:
        st.error(f"Failed to save milk data: {e}")
        return False

def load_system_config_from_sheets(sheet):
    """Load system config from Google Sheets"""
    try:
        worksheet = get_worksheet(sheet, "system_config")
        data = worksheet.get_all_records()
        
        if not data:
            # Initialize with default config
            worksheet.clear()
            worksheet.append_row(["total_cows", "last_updated"])
            worksheet.append_row([50, datetime.now().isoformat()])
            return 50
        
        return int(data[0].get('total_cows', 50))
    except Exception as e:
        st.error(f"Error loading system config: {e}")
        return 50

def save_system_config_to_sheets(sheet, total_cows):
    """Save system config to Google Sheets"""
    try:
        worksheet = get_worksheet(sheet, "system_config")
        worksheet.clear()
        worksheet.append_row(["total_cows", "last_updated"])
        worksheet.append_row([total_cows, datetime.now().isoformat()])
        return True
    except Exception as e:
        st.error(f"Failed to save system config: {e}")
        return False
# Password protection system
def check_password():
    """Returns True if password is correct, False otherwise"""
    
    def password_entered():
        if st.session_state["password"] == "1687":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Clear password from session
        else:
            st.session_state["password_correct"] = False

    # Check if password is already verified
    if st.session_state.get("password_correct", False):
        return True
    
    # Show password input
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 2rem; border-radius: 15px; margin: 2rem 0; 
                text-align: center; color: white;">
        <h1>🔒 Dairy Farm Management System</h1>
        <p>Please enter the access password to continue</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.text_input(
            "Enter Password", 
            type="password", 
            on_change=password_entered, 
            key="password",
            placeholder="Enter your access password",
            help="Contact your administrator if you don't have the password"
        )
        
        # Show error if password is incorrect
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("❌ Incorrect password. Please try again.")
    
    return False

# NEW FUNCTION - Add this after the check_password function
def check_supervisor_password():
    """Returns True if supervisor password is correct, False otherwise"""
    
    def supervisor_password_entered():
        if st.session_state["supervisor_password"] == "7441":
            st.session_state["supervisor_password_correct"] = True
            del st.session_state["supervisor_password"]  # Clear password from session
        else:
            st.session_state["supervisor_password_correct"] = False

    # Check if supervisor password is already verified
    if st.session_state.get("supervisor_password_correct", False):
        return True
    
    # Show supervisor password input
    st.markdown("""
    <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%); 
                padding: 2rem; border-radius: 15px; margin: 2rem 0; 
                text-align: center; color: white;">
        <h1>👔 Supervisor Access</h1>
        <p>Please enter the supervisor password to continue</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.text_input(
            "Enter Supervisor Password", 
            type="password", 
            on_change=supervisor_password_entered, 
            key="supervisor_password",
            placeholder="Enter supervisor password",
            help="Only supervisors have access to this password"
        )
        
        # Show error if password is incorrect
        if "supervisor_password_correct" in st.session_state and not st.session_state["supervisor_password_correct"]:
            st.error("❌ Incorrect supervisor password. Please try again.")
        
        # Add back button
        if st.button("← Back to Role Selection", use_container_width=True):
            st.session_state.role = None
            st.session_state.current_user = None
            # Clear supervisor password states
            if "supervisor_password_correct" in st.session_state:
                del st.session_state["supervisor_password_correct"]
            st.rerun()
    
    return False
# Initialize session state with Google Sheets
def initialize_session_state():
    if 'role' not in st.session_state:
        st.session_state.role = None
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'gsheets_conn' not in st.session_state:
        st.session_state.gsheets_conn = initialize_gsheets_connection()
    
    if st.session_state.gsheets_conn:
        # Load data from Google Sheets
        if 'workers' not in st.session_state:
            st.session_state.workers = load_workers_from_sheets(st.session_state.gsheets_conn)
        if 'cow_assignments' not in st.session_state:
            st.session_state.cow_assignments = load_cow_assignments_from_sheets(st.session_state.gsheets_conn)
        if 'milk_data' not in st.session_state:
            st.session_state.milk_data = load_milk_data_from_sheets(st.session_state.gsheets_conn)
        if 'cows' not in st.session_state:
            total_cows = load_system_config_from_sheets(st.session_state.gsheets_conn)
            st.session_state.cows = list(range(1, total_cows + 1))
    else:
        # Fallback to default values if connection fails
        if 'workers' not in st.session_state:
            st.session_state.workers = ["John Doe", "Mary Smith", "David Johnson", "Sarah Wilson"]
        if 'cow_assignments' not in st.session_state:
            st.session_state.cow_assignments = {}
        if 'milk_data' not in st.session_state:
            st.session_state.milk_data = []
        if 'cows' not in st.session_state:
            st.session_state.cows = list(range(1, 51))

initialize_session_state()

# Auto-save functions
def auto_save_workers():
    if st.session_state.gsheets_conn:
        return save_workers_to_sheets(st.session_state.gsheets_conn, st.session_state.workers)
    return False

def auto_save_cow_assignments():
    if st.session_state.gsheets_conn:
        return save_cow_assignments_to_sheets(st.session_state.gsheets_conn, st.session_state.cow_assignments)
    return False

def auto_save_milk_data():
    if st.session_state.gsheets_conn:
        return save_milk_data_to_sheets(st.session_state.gsheets_conn, st.session_state.milk_data)
    return False

def auto_save_system_config():
    if st.session_state.gsheets_conn:
        return save_system_config_to_sheets(st.session_state.gsheets_conn, len(st.session_state.cows))
    return False

# Custom CSS
st.markdown("""
<style>
    .role-selector {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        text-align: center;
        color: white;
    }
    .supervisor-header {
        background: linear-gradient(90deg, #ff6b6b, #ee5a52);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .worker-header {
        background: linear-gradient(90deg, #4CAF50, #45a049);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .worker-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #4CAF50;
    }
    .cow-assignment-card {
        background: linear-gradient(135deg, #e3f2fd, #bbdefb);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .metric-card {
        background: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Role Selection Page
def show_role_selection():
    st.markdown("""
    <div class="role-selector">
        <h1>🐄 Dairy Farm Management System</h1>
        <p>Select your role to continue</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Choose Your Role")
        
        col_sup, col_work = st.columns(2)
        
        with col_sup:
            if st.button("👔 Supervisor", use_container_width=True, type="primary"):
                st.session_state.role = "supervisor"
                st.rerun()
        
        with col_work:
            if st.button("👨‍🌾 Worker", use_container_width=True):
                st.session_state.role = "worker"
                st.rerun()

# Worker Selection Page
def show_worker_selection():
    st.markdown("""
    <div class="worker-header">
        <h2>👨‍🌾 Worker Login</h2>
        <p>Select your name to continue</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        selected_worker = st.selectbox(
            "Select Your Name",
            st.session_state.workers,
            help="Choose your name from the list"
        )
        
        if st.button("Continue as Worker", use_container_width=True, type="primary"):
            st.session_state.current_user = selected_worker
            st.rerun()
        
        if st.button("← Back to Role Selection", use_container_width=True):
            st.session_state.role = None
            st.session_state.current_user = None
            st.rerun()

# Supervisor Dashboard
def show_supervisor_dashboard():
    st.markdown("""
    <div class="supervisor-header">
        <h1>👔 Supervisor Dashboard</h1>
        <p>Manage workers, assign cows, and monitor production</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Connection status
    if st.session_state.gsheets_conn:
        st.success("✅ Connected to Google Sheets")
    else:
        st.error("❌ Google Sheets connection failed - data will be stored locally only")
    
    # Logout button
    if st.button("🚪 Logout", key="supervisor_logout"):
        st.session_state.role = None
        st.session_state.current_user = None
        st.rerun()
    
    # Tabs for different supervisor functions
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["👥 Manage Workers", "🐄 Assign Cows", "📊 Production Reports", "📋 Daily Records", "⚙️ System Settings"])
    
    with tab1:
        st.subheader("Worker Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Current Workers")
            for i, worker in enumerate(st.session_state.workers):
                col_name, col_action = st.columns([3, 1])
                with col_name:
                    st.markdown(f"**{worker}**")
                with col_action:
                    if st.button("Remove", key=f"remove_{i}"):
                        st.session_state.workers.remove(worker)
                        # Remove cow assignments for this worker
                        st.session_state.cow_assignments = {k: v for k, v in st.session_state.cow_assignments.items() if v != worker}
                        # Save to Google Sheets
                        if auto_save_workers() and auto_save_cow_assignments():
                            st.success(f"Removed {worker} successfully")
                        st.rerun()
        
        with col2:
            st.markdown("#### Add New Worker")
            new_worker_name = st.text_input("Worker Name", placeholder="Enter worker's full name")
            if st.button("Add Worker") and new_worker_name:
                if new_worker_name not in st.session_state.workers:
                    st.session_state.workers.append(new_worker_name)
                    # Save to Google Sheets
                    if auto_save_workers():
                        st.success(f"Added {new_worker_name} as a worker")
                    else:
                        st.error("Failed to save to Google Sheets")
                    st.rerun()
                else:
                    st.error("Worker already exists")
    
    with tab2:
        st.subheader("Cow Assignments")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Assign Cows to Workers")
            
            selected_worker = st.selectbox("Select Worker", st.session_state.workers)
            
            # Multi-select for cow numbers
            available_cows = [cow for cow in st.session_state.cows if cow not in st.session_state.cow_assignments]
            
            selected_cows = st.multiselect(
                "Select Cows to Assign",
                available_cows,
                help="Select multiple cows to assign to this worker"
            )
            
            if st.button("Assign Cows"):
                for cow in selected_cows:
                    st.session_state.cow_assignments[cow] = selected_worker
                # Save to Google Sheets
                if auto_save_cow_assignments():
                    st.success(f"Assigned {len(selected_cows)} cows to {selected_worker}")
                else:
                    st.error("Failed to save assignments to Google Sheets")
                st.rerun()
        
        with col2:
            st.markdown("#### Current Assignments")
            
            if st.session_state.cow_assignments:
                # Group assignments by worker
                assignments_by_worker = {}
                for cow, worker in st.session_state.cow_assignments.items():
                    if worker not in assignments_by_worker:
                        assignments_by_worker[worker] = []
                    assignments_by_worker[worker].append(cow)
                
                for worker, cows in assignments_by_worker.items():
                    with st.expander(f"{worker} ({len(cows)} cows)"):
                        cows_str = ", ".join([f"#{cow}" for cow in sorted(cows)])
                        st.write(cows_str)
                        
                        # Option to remove all assignments for this worker
                        if st.button(f"Remove all assignments for {worker}", key=f"remove_all_{worker}"):
                            st.session_state.cow_assignments = {k: v for k, v in st.session_state.cow_assignments.items() if v != worker}
                            if auto_save_cow_assignments():
                                st.success(f"Removed all assignments for {worker}")
                            st.rerun()
            else:
                st.info("No cow assignments yet")
    
    with tab3:
        st.subheader("Production Reports")
        
        if st.session_state.milk_data:
            df = pd.DataFrame(st.session_state.milk_data)
            df['date'] = pd.to_datetime(df['date'])
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Production", f"{df['milk_liters'].sum():.1f}L")
            with col2:
                st.metric("Average per Session", f"{df['milk_liters'].mean():.1f}L")
            with col3:
                st.metric("Active Cows", df['cow_number'].nunique())
            with col4:
                st.metric("Total Records", len(df))
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Daily production
                st.markdown("#### Daily Production Trend")
                daily_production = df.groupby('date')['milk_liters'].sum().reset_index()
                daily_production['date'] = pd.to_datetime(daily_production['date'])
                daily_production = daily_production.sort_values('date')
                st.line_chart(daily_production.set_index('date')['milk_liters'])
            
            with col2:
                # Worker performance
                st.markdown("#### Production by Worker")
                worker_production = df.groupby('worker')['milk_liters'].sum().reset_index()
                st.bar_chart(worker_production.set_index('worker')['milk_liters'])
            
            # Top performing cows
            st.subheader("Top Performing Cows")
            cow_performance = df.groupby('cow_number')['milk_liters'].agg(['sum', 'mean', 'count']).round(2)
            cow_performance.columns = ['Total (L)', 'Average (L)', 'Sessions']
            cow_performance = cow_performance.sort_values('Total (L)', ascending=False)
            st.dataframe(cow_performance.head(10), use_container_width=True)
            
        else:
            st.info("No production data available yet")
    
    with tab4:
        st.subheader("Daily Records")
        
        if st.session_state.milk_data:
            df = pd.DataFrame(st.session_state.milk_data)
            
            # Filter by date
            selected_date = st.date_input("Select Date", value=date.today())
            
            daily_records = df[df['date'] == str(selected_date)]
            
            if not daily_records.empty:
                st.dataframe(daily_records[['cow_number', 'milk_liters', 'worker', 'time', 'notes']], 
                           use_container_width=True)
                
                # Daily summary
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Milk", f"{daily_records['milk_liters'].sum():.1f}L")
                with col2:
                    st.metric("Cows Milked", daily_records['cow_number'].nunique())
                with col3:
                    st.metric("Sessions", len(daily_records))
            else:
                st.info(f"No records found for {selected_date}")
        else:
            st.info("No records available")
    
    with tab5:
        st.subheader("System Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Manage Cows")
            total_cows = st.number_input("Total Number of Cows", min_value=1, max_value=1000, value=len(st.session_state.cows))
            
            if st.button("Update Cow Count"):
                st.session_state.cows = list(range(1, total_cows + 1))
                # Remove assignments for cows that no longer exist
                st.session_state.cow_assignments = {k: v for k, v in st.session_state.cow_assignments.items() if k <= total_cows}
                # Save to Google Sheets
                if auto_save_system_config() and auto_save_cow_assignments():
                    st.success(f"Updated to {total_cows} cows")
                else:
                    st.error("Failed to save changes to Google Sheets")
                st.rerun()
        
        with col2:
            st.markdown("#### Data Management")
            
            if st.session_state.milk_data:
                csv = pd.DataFrame(st.session_state.milk_data).to_csv(index=False)
                st.download_button(
                    label="📄 Export All Data",
                    data=csv,
                    file_name=f"dairy_data_{date.today()}.csv",
                    mime="text/csv"
                )
            
            if st.button("🗑️ Clear All Production Data"):
                if st.checkbox("Confirm deletion"):
                    st.session_state.milk_data = []
                    if auto_save_milk_data():
                        st.success("All production data cleared")
                    else:
                        st.error("Failed to clear data from Google Sheets")
                    st.rerun()

# Worker Dashboard
def show_worker_dashboard():
    worker_name = st.session_state.current_user
    
    st.markdown(f"""
    <div class="worker-header">
        <h1>👨‍🌾 Worker Dashboard</h1>
        <p>Welcome, {worker_name}!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Connection status
    if st.session_state.gsheets_conn:
        st.success("✅ Connected to Google Sheets")
    else:
        st.error("❌ Google Sheets connection failed - data will be stored locally only")
    
    # Logout button
    if st.button("🚪 Logout", key="worker_logout"):
        st.session_state.role = None
        st.session_state.current_user = None
        st.rerun()
    
    # Get assigned cows for this worker
    assigned_cows = [cow for cow, worker in st.session_state.cow_assignments.items() if worker == worker_name]
    
    if not assigned_cows:
        st.warning("⚠️ No cows assigned to you yet. Please contact your supervisor.")
        return
    
    # Show assigned cows
    st.subheader(f"Your Assigned Cows ({len(assigned_cows)} cows)")
    assigned_cows_str = ", ".join([f"#{cow}" for cow in sorted(assigned_cows)])
    st.info(f"**Assigned Cows:** {assigned_cows_str}")
    
    # Tabs for worker functions
    tab1, tab2, tab3 = st.tabs(["🥛 Log Milk", "📊 My Records", "🐄 Cow Status"])
    
    with tab1:
        st.subheader("Log Milk Production")
        
        col1, col2 = st.columns(2)
        
        with col1:
            cow_number = st.selectbox(
                "Select Cow Number",
                sorted(assigned_cows),
                format_func=lambda x: f"Cow #{x}",
                help="You can only log milk for your assigned cows"
            )
            
            milk_amount = st.number_input(
                "Milk Amount (Liters)",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=0.1,
                format="%.1f"
            )
        
        with col2:
            milking_date = st.date_input("Date", value=date.today())
            
            milking_time = st.selectbox(
                "Milking Session",
                ["Morning", "Evening"]
            )
            
            notes = st.text_area(
                "Notes (Optional)",
                placeholder="Any observations about the cow or milk quality...",
                height=100
            )
        
        if st.button("🥛 Log Milk Production", type="primary", use_container_width=True):
            if milk_amount > 0:
                new_record = {
                    'date': str(milking_date),
                    'time': milking_time,
                    'cow_number': cow_number,
                    'milk_liters': milk_amount,
                    'worker': worker_name,
                    'notes': notes,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                st.session_state.milk_data.append(new_record)
                # Save to Google Sheets
                if auto_save_milk_data():
                    st.success(f"✅ Successfully logged {milk_amount}L from Cow #{cow_number}")
                    st.balloons()
                else:
                    st.error("Failed to save to Google Sheets, but data saved locally")
            else:
                st.error("Please enter a milk amount greater than 0")
    
    with tab2:
        st.subheader("My Production Records")
        
        if st.session_state.milk_data:
            df = pd.DataFrame(st.session_state.milk_data)
            worker_records = df[df['worker'] == worker_name]
            
# Add this to complete your code after the last line "worker_records = df[df['worker'] == worker_name]"

            if not worker_records.empty:
                # Summary metrics for worker
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Milk Logged", f"{worker_records['milk_liters'].sum():.1f}L")
                with col2:
                    st.metric("Average per Session", f"{worker_records['milk_liters'].mean():.1f}L")
                with col3:
                    st.metric("Sessions Logged", len(worker_records))
                
                # Recent records
                st.markdown("#### Recent Records")
                recent_records = worker_records.sort_values('timestamp', ascending=False).head(10)
                st.dataframe(
                    recent_records[['date', 'time', 'cow_number', 'milk_liters', 'notes']], 
                    use_container_width=True
                )
            else:
                st.info("No records found. Start logging milk production!")
        else:
            st.info("No production data available yet")
    
    with tab3:
        st.subheader("Cow Status Overview")
        
        if st.session_state.milk_data:
            df = pd.DataFrame(st.session_state.milk_data)
            worker_records = df[df['worker'] == worker_name]
            
            if not worker_records.empty:
                # Performance by cow
                cow_performance = worker_records.groupby('cow_number')['milk_liters'].agg(['sum', 'mean', 'count']).round(2)
                cow_performance.columns = ['Total (L)', 'Average (L)', 'Sessions']
                cow_performance = cow_performance.sort_values('Total (L)', ascending=False)
                
                st.markdown("#### Your Cows' Performance")
                st.dataframe(cow_performance, use_container_width=True)
                
                # Show which assigned cows haven't been milked recently
                recent_date = pd.Timestamp.now() - pd.Timedelta(days=1)
                worker_records['date'] = pd.to_datetime(worker_records['date'])
                recently_milked = worker_records[worker_records['date'] >= recent_date]['cow_number'].unique()
                not_milked = [cow for cow in assigned_cows if cow not in recently_milked]
                
                if not_milked:
                    st.warning(f"⚠️ Cows not milked in last 24 hours: {', '.join([f'#{cow}' for cow in not_milked])}")
                else:
                    st.success("✅ All assigned cows have been milked recently")
            else:
                st.info("No milking records yet to show cow status")
        else:
            st.info("No data available")

# Main Application Flow
def main():
    # Check password first
    if not check_password():
        return
    
    # Show role selection if no role is selected
    if st.session_state.role is None:
        show_role_selection()
    
    # Handle supervisor role
    elif st.session_state.role == "supervisor":
        # Check supervisor password before showing dashboard
        if not check_supervisor_password():
            return
        show_supervisor_dashboard()
    
    # Handle worker role
    elif st.session_state.role == "worker":
        if st.session_state.current_user is None:
            show_worker_selection()
        else:
            show_worker_dashboard()

# Run the application
if __name__ == "__main__":
    main()