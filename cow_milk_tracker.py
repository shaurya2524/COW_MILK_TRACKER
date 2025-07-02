import streamlit as st
import pandas as pd
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go

# Configure page
st.set_page_config(
    page_title="Dairy Farm Management System",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
def initialize_session_state():
    if 'role' not in st.session_state:
        st.session_state.role = None
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'workers' not in st.session_state:
        st.session_state.workers = ["John Doe", "Mary Smith", "David Johnson", "Sarah Wilson"]
    if 'cow_assignments' not in st.session_state:
        st.session_state.cow_assignments = {}
    if 'milk_data' not in st.session_state:
        st.session_state.milk_data = []
    if 'cows' not in st.session_state:
        st.session_state.cows = list(range(1, 51))  # Default 50 cows

initialize_session_state()

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
                st.session_state.current_user = "Supervisor"
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
                        st.rerun()
        
        with col2:
            st.markdown("#### Add New Worker")
            new_worker_name = st.text_input("Worker Name", placeholder="Enter worker's full name")
            if st.button("Add Worker") and new_worker_name:
                if new_worker_name not in st.session_state.workers:
                    st.session_state.workers.append(new_worker_name)
                    st.success(f"Added {new_worker_name} as a worker")
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
            assigned_to_worker = [cow for cow, worker in st.session_state.cow_assignments.items() if worker == selected_worker]
            
            selected_cows = st.multiselect(
                "Select Cows to Assign",
                available_cows,
                help="Select multiple cows to assign to this worker"
            )
            
            if st.button("Assign Cows"):
                for cow in selected_cows:
                    st.session_state.cow_assignments[cow] = selected_worker
                st.success(f"Assigned {len(selected_cows)} cows to {selected_worker}")
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
                daily_production = df.groupby('date')['milk_liters'].sum().reset_index()
                fig_daily = px.line(daily_production, x='date', y='milk_liters',
                                  title='Daily Production Trend')
                st.plotly_chart(fig_daily, use_container_width=True)
            
            with col2:
                # Worker performance
                worker_production = df.groupby('worker')['milk_liters'].sum().reset_index()
                fig_worker = px.bar(worker_production, x='worker', y='milk_liters',
                                  title='Production by Worker')
                st.plotly_chart(fig_worker, use_container_width=True)
            
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
                st.success(f"Updated to {total_cows} cows")
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
                    st.success("All production data cleared")
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
                st.success(f"✅ Successfully logged {milk_amount}L from Cow #{cow_number}")
                st.balloons()
            else:
                st.error("Please enter a milk amount greater than 0")
    
    with tab2:
        st.subheader("My Production Records")
        
        if st.session_state.milk_data:
            df = pd.DataFrame(st.session_state.milk_data)
            worker_records = df[df['worker'] == worker_name]
            
            if not worker_records.empty:
                # Worker's summary
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Milk Logged", f"{worker_records['milk_liters'].sum():.1f}L")
                with col2:
                    st.metric("Average per Session", f"{worker_records['milk_liters'].mean():.1f}L")
                with col3:
                    st.metric("Total Sessions", len(worker_records))
                with col4:
                    st.metric("Cows Milked", worker_records['cow_number'].nunique())
                
                # Recent records
                st.subheader("Recent Records")
                recent_records = worker_records.sort_values('timestamp', ascending=False).head(10)
                display_cols = ['date', 'time', 'cow_number', 'milk_liters', 'notes']
                st.dataframe(recent_records[display_cols], use_container_width=True)
                
                # Production trend
                daily_production = worker_records.groupby('date')['milk_liters'].sum().reset_index()
                if len(daily_production) > 1:
                    fig = px.line(daily_production, x='date', y='milk_liters',
                                title='Your Daily Production Trend')
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No records found. Start logging milk production!")
        else:
            st.info("No production data available yet")
    
    with tab3:
        st.subheader("Cow Status Overview")
        
        if st.session_state.milk_data:
            df = pd.DataFrame(st.session_state.milk_data)
            worker_records = df[df['worker'] == worker_name]
            
            # Show status for each assigned cow
            for cow in sorted(assigned_cows):
                cow_data = worker_records[worker_records['cow_number'] == cow]
                
                with st.expander(f"Cow #{cow}"):
                    if not cow_data.empty:
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Total Milk", f"{cow_data['milk_liters'].sum():.1f}L")
                        with col2:
                            st.metric("Sessions", len(cow_data))
                        with col3:
                            last_milked = cow_data['date'].max()
                            st.metric("Last Milked", last_milked)
                        
                        # Recent records for this cow
                        recent_cow_records = cow_data.sort_values('timestamp', ascending=False).head(5)
                        st.dataframe(recent_cow_records[['date', 'time', 'milk_liters', 'notes']], 
                                   use_container_width=True)
                    else:
                        st.info("No records for this cow yet")
        else:
            st.info("No production data available")

# Main app logic
def main():
    if st.session_state.role is None:
        show_role_selection()
    elif st.session_state.role == "worker" and st.session_state.current_user is None:
        show_worker_selection()
    elif st.session_state.role == "supervisor":
        show_supervisor_dashboard()
    elif st.session_state.role == "worker" and st.session_state.current_user:
        show_worker_dashboard()

if __name__ == "__main__":
    main()