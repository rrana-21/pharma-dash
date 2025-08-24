import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import calendar

# Set page config
st.set_page_config(
    page_title="Clarus Pharmacy Analytics",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Clarus pharmacy styling with orange color scheme
st.markdown("""
<style>
    .main-header {
        font-size: 3.5rem;
        color: #d4650f;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .clarus-brand {
        font-size: 1.4rem;
        color: #b8540d;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #fef7f0;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 6px solid #d4650f;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .pharmacy-specific {
        background: linear-gradient(135deg, #d4650f 0%, #f97316 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin: 1.5rem 0;
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    .sidebar .sidebar-content {
        background-color: #fef7f0;
    }
    .upload-section {
        border: 3px dashed #d4650f;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        background-color: #fef7f0;
        margin-bottom: 1rem;
    }
    .insight-box {
        background-color: #fff7ed;
        border-left: 5px solid #d4650f;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    .compliance-alert {
        background-color: #fef3c7;
        border-left: 5px solid #f59e0b;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    .clinical-highlight {
        background-color: #ede9fe;
        border-left: 5px solid #7c3aed;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    .stMetric > div > div > div > div {
        font-size: 2rem !important;
        font-weight: bold !important;
    }
    .stMetric > div > div > div > div:first-child {
        font-size: 1.2rem !important;
        color: #d4650f !important;
        font-weight: 600 !important;
    }
    /* Tab styling similar to your image */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #f9fafb;
        padding: 4px;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        padding: 12px 20px;
        background-color: white;
        border: 1px solid #e5e7eb;
        color: #6b7280;
        font-weight: 500;
        font-size: 14px;
        border-radius: 6px;
        margin: 0 1px;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: #d4650f !important;
        color: white !important;
        border-color: #d4650f !important;
        font-weight: 600 !important;
    }
    .stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
        background-color: #f3f4f6;
        border-color: #d1d5db;
    }
    /* Mobile responsive improvements */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2.5rem;
        }
        .metric-card {
            padding: 1rem;
        }
        .pharmacy-specific {
            padding: 1rem;
        }
        /* Mobile chart title adjustments */
        .js-plotly-plot .gtitle {
            font-size: 12px !important;
        }
    }
    /* Improve chart readability and responsive titles */
    .js-plotly-plot {
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    /* Ensure chart titles don't get cut off */
    .js-plotly-plot .plotly-graph-div {
        overflow: visible !important;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(file_path_or_buffer):
    """Load and preprocess the pharmacy data"""
    try:
        # Handle both file paths and uploaded files
        if isinstance(file_path_or_buffer, str):
            if file_path_or_buffer.endswith('.xlsx'):
                df = pd.read_excel(file_path_or_buffer)
            else:
                df = pd.read_csv(file_path_or_buffer)
        else:
            if file_path_or_buffer.name.endswith('.xlsx'):
                df = pd.read_excel(file_path_or_buffer)
            else:
                df = pd.read_csv(file_path_or_buffer)
        
        # Convert Date to datetime
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Create additional date columns for easier filtering
        df['Month'] = df['Date'].dt.to_period('M')
        df['Year'] = df['Date'].dt.year
        df['Day_of_Week'] = df['Date'].dt.day_name()
        df['Month_Name'] = df['Date'].dt.strftime('%B %Y')
        df['Quarter'] = df['Date'].dt.to_period('Q')
        
        # Calculate pharmacy-specific metrics
        df['Revenue'] = df['TotalPrice']
        
        # Create service type categories
        df['Is_Prescription'] = df['ServiceType'].isin(['Prescription', 'Vaccination', 'Consultation', 'Medication Review'])
        df['Is_Clinical_Service'] = df['ServiceType'].isin(['Vaccination', 'Consultation', 'Medication Review'])
        
        # Create chronic medication flag
        chronic_conditions = ['Cardiovascular', 'Diabetes', 'Mental Health']
        df['Is_Chronic'] = df['MedicationCategory'].isin(chronic_conditions) & (df['ServiceType'] == 'Prescription')
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info("Please ensure your file has the required columns: TransactionID, Date, PatientID, ServiceType, MedicationCategory, Quantity, UnitPrice, InsuranceUsed, TotalPrice")
        return None

def check_data_availability(df):
    """Check if we have sufficient data for each analysis type"""
    availability = {}
    
    # Check for compliance data
    chronic_conditions = ['Cardiovascular', 'Diabetes', 'Mental Health']
    chronic_df = df[df['MedicationCategory'].isin(chronic_conditions) & (df['ServiceType'] == 'Prescription')]
    availability['compliance'] = len(chronic_df) > 0
    
    # Check for seasonal data
    seasonal_categories = ['Cold & Flu', 'Allergy', 'Vaccination']
    seasonal_df = df[df['MedicationCategory'].isin(seasonal_categories)]
    availability['seasonal'] = len(seasonal_df) > 0
    
    # Check for clinical services data
    clinical_df = df[df['ServiceType'].isin(['Vaccination', 'Consultation', 'Medication Review'])]
    availability['clinical'] = len(clinical_df) > 0
    
    return availability

def analyze_prescription_otc_mix(df):
    """Analyze prescription vs OTC sales mix"""
    prescription_revenue = df[df['Is_Prescription']]['TotalPrice'].sum()
    otc_revenue = df[df['ServiceType'] == 'OTC']['TotalPrice'].sum()
    total_revenue = prescription_revenue + otc_revenue
    
    if total_revenue > 0:
        prescription_pct = (prescription_revenue / total_revenue) * 100
        otc_pct = (otc_revenue / total_revenue) * 100
    else:
        prescription_pct = otc_pct = 0
    
    return {
        'prescription_revenue': prescription_revenue,
        'otc_revenue': otc_revenue,
        'prescription_pct': prescription_pct,
        'otc_pct': otc_pct
    }

def create_prescription_otc_chart(df):
    """Create prescription vs OTC revenue visualization"""
    analysis = analyze_prescription_otc_mix(df)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart for Rx vs OTC
        fig_pie = px.pie(
            values=[analysis['prescription_pct'], analysis['otc_pct']],
            names=['Prescription Services', 'OTC Products'],
            title="Revenue Split: Prescription vs OTC",
            color_discrete_sequence=['#d4650f', '#f97316']
        )
        fig_pie.update_traces(
            textposition="auto",
            textinfo="percent+label",
            textfont_size=12,
            hovertemplate='<b>%{label}</b><br>Revenue: %{percent}<br>Amount: $%{value:,.2f}<extra></extra>'
        )
        fig_pie.update_layout(
            title_font_size=13,
            title_x=0.5,
            title_y=0.95,
            title_font_color='#d4650f',
            height=350,
            margin=dict(t=60, b=20, l=20, r=20),
            font_size=10
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Service type breakdown
        service_revenue = df.groupby('ServiceType')['TotalPrice'].sum().reset_index()
        service_revenue = service_revenue.sort_values('TotalPrice', ascending=True)
        
        fig_service = px.bar(
            service_revenue,
            x='TotalPrice',
            y='ServiceType',
            orientation='h',
            title="Revenue by Service Type",
            color='TotalPrice',
            color_continuous_scale=['#fed7aa', '#d4650f']
        )
        fig_service.update_traces(
            hovertemplate='<b>%{y}</b><br>Revenue: $%{x:,.2f}<extra></extra>',
            texttemplate='$%{x:,.0f}',
            textposition='outside'
        )
        fig_service.update_layout(
            title_font_size=13,
            title_x=0.5,
            title_y=0.95,
            title_font_color='#d4650f',
            height=350,
            margin=dict(t=60, b=50, l=140, r=70),
            showlegend=False,
            font_size=10
        )
        st.plotly_chart(fig_service, use_container_width=True)

def create_top_medications_chart(df):
    """Create top medications and categories visualization"""
    category_analysis = df.groupby('MedicationCategory').agg({
        'TotalPrice': 'sum',
        'Quantity': 'sum',
        'TransactionID': 'count'
    }).reset_index()
    category_analysis = category_analysis.sort_values('TotalPrice', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top categories by revenue
        top_10_revenue = category_analysis.head(10)
        fig_revenue = px.bar(
            top_10_revenue,
            x='TotalPrice',
            y='MedicationCategory',
            orientation='h',
            title="Top Categories by Revenue",
            color='TotalPrice',
            color_continuous_scale=['#fed7aa', '#d4650f'],
            text='TotalPrice'
        )
        fig_revenue.update_traces(
            texttemplate='$%{text:,.0f}',
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Revenue: $%{x:,.2f}<br>Transactions: %{customdata}<extra></extra>',
            customdata=top_10_revenue['TransactionID']
        )
        fig_revenue.update_layout(
            title_font_size=13,
            title_x=0.5,
            title_y=0.95,
            title_font_color='#d4650f',
            height=400,
            margin=dict(t=70, b=50, l=170, r=80),
            showlegend=False,
            font_size=10
        )
        st.plotly_chart(fig_revenue, use_container_width=True)
    
    with col2:
        # Top categories by volume
        top_10_volume = category_analysis.sort_values('Quantity', ascending=False).head(10)
        fig_volume = px.bar(
            top_10_volume,
            x='Quantity',
            y='MedicationCategory',
            orientation='h',
            title="Top Categories by Volume",
            color='Quantity',
            color_continuous_scale=['#fef3c7', '#f59e0b'],
            text='Quantity'
        )
        fig_volume.update_traces(
            texttemplate='%{text:,}',
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Quantity: %{x:,}<br>Revenue: $%{customdata:,.2f}<extra></extra>',
            customdata=top_10_volume['TotalPrice']
        )
        fig_volume.update_layout(
            title_font_size=13,
            title_x=0.5,
            title_y=0.95,
            title_font_color='#f59e0b',
            height=400,
            margin=dict(t=70, b=50, l=170, r=80),
            showlegend=False,
            font_size=10
        )
        st.plotly_chart(fig_volume, use_container_width=True)

def analyze_patient_compliance(df):
    """Analyze patient refill compliance for chronic medications"""
    chronic_conditions = ['Cardiovascular', 'Diabetes', 'Mental Health']
    chronic_df = df[df['Is_Chronic']]
    
    if chronic_df.empty:
        return None, None
    
    # Calculate refill patterns by patient
    patient_refills = chronic_df.groupby(['PatientID', 'MedicationCategory']).agg({
        'Date': ['count', 'min', 'max'],
        'Quantity': 'mean'
    }).reset_index()
    
    patient_refills.columns = ['PatientID', 'Category', 'Refill_Count', 'First_Fill', 'Last_Fill', 'Avg_Days_Supply']
    
    # Calculate days between first and last fill
    patient_refills['Days_Between'] = (patient_refills['Last_Fill'] - patient_refills['First_Fill']).dt.days
    
    # Estimate compliance (simplified calculation)
    patient_refills['Expected_Refills'] = np.maximum(1, patient_refills['Days_Between'] / patient_refills['Avg_Days_Supply'])
    patient_refills['Compliance_Rate'] = np.minimum(100, (patient_refills['Refill_Count'] / patient_refills['Expected_Refills'] * 100))
    
    # Calculate summary metrics
    avg_compliance = patient_refills['Compliance_Rate'].mean()
    high_compliance_count = len(patient_refills[patient_refills['Compliance_Rate'] >= 80])
    total_chronic_patients = len(patient_refills)
    
    return patient_refills, {
        'avg_compliance': avg_compliance,
        'high_compliance_count': high_compliance_count,
        'total_chronic_patients': total_chronic_patients
    }

def create_compliance_charts(df):
    """Create patient compliance visualization"""
    compliance_data, summary = analyze_patient_compliance(df)
    
    if compliance_data is None:
        return False
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Compliance rate distribution
        fig_compliance = px.histogram(
            compliance_data,
            x='Compliance_Rate',
            nbins=15,
            title="Patient Compliance Rate Distribution",
            color_discrete_sequence=['#d4650f'],
            labels={'Compliance_Rate': 'Compliance Rate (%)', 'count': 'Number of Patients'}
        )
        fig_compliance.update_traces(
            hovertemplate='Compliance Rate: %{x}%<br>Patients: %{y}<extra></extra>'
        )
        fig_compliance.update_layout(
            title_font_size=13,
            title_x=0.5,
            title_y=0.95,
            title_font_color='#d4650f',
            height=350,
            margin=dict(t=70, b=50, l=50, r=50),
            font_size=10
        )
        st.plotly_chart(fig_compliance, use_container_width=True)
    
    with col2:
        # Compliance by category
        avg_compliance_by_category = compliance_data.groupby('Category')['Compliance_Rate'].mean().reset_index()
        fig_category = px.bar(
            avg_compliance_by_category,
            x='Category',
            y='Compliance_Rate',
            title="Average Compliance by Condition",
            color='Compliance_Rate',
            color_continuous_scale=['#fef3c7', '#d4650f']
        )
        fig_category.update_traces(
            texttemplate='%{y:.1f}%',
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Avg Compliance: %{y:.1f}%<extra></extra>'
        )
        fig_category.update_layout(
            title_font_size=13,
            title_x=0.5,
            title_y=0.95,
            title_font_color='#d4650f',
            height=350,
            margin=dict(t=70, b=50, l=50, r=50),
            showlegend=False,
            font_size=10
        )
        st.plotly_chart(fig_category, use_container_width=True)
    
    # Summary metrics only
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Average Compliance Rate", f"{summary['avg_compliance']:.1f}%")
    with col2:
        st.metric("High Adherence Patients", f"{summary['high_compliance_count']}")
    with col3:
        st.metric("Total Chronic Patients", f"{summary['total_chronic_patients']}")
    
    return True

def create_insurance_analysis(df):
    """Create insurance vs cash pay analysis"""
    insurance_breakdown = df.groupby('InsuranceUsed').agg({
        'TotalPrice': 'sum',
        'TransactionID': 'count'
    }).reset_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Insurance vs cash pie chart
        fig_insurance = px.pie(
            insurance_breakdown,
            values='TotalPrice',
            names='InsuranceUsed',
            title="Revenue: Insurance vs Cash Pay",
            color_discrete_sequence=['#f59e0b', '#d4650f']
        )
        fig_insurance.update_traces(
            textposition="auto",
            textinfo="percent+label",
            textfont_size=12,
            hovertemplate='<b>%{label}</b><br>Revenue: $%{value:,.2f}<br>Percentage: %{percent}<extra></extra>'
        )
        fig_insurance.update_layout(
            title_font_size=14,
            title_x=0.5,
            title_font_color='#d4650f',
            height=350
        )
        st.plotly_chart(fig_insurance, use_container_width=True)
    
    with col2:
        # Insurance usage by service type
        service_insurance = df.groupby(['ServiceType', 'InsuranceUsed']).agg({
            'TotalPrice': 'sum'
        }).reset_index()
        
        fig_service_insurance = px.bar(
            service_insurance,
            x='ServiceType',
            y='TotalPrice',
            color='InsuranceUsed',
            title="Insurance Usage by Service Type",
            color_discrete_map={'Yes': '#d4650f', 'No': '#f59e0b'},
            barmode='group'
        )
        fig_service_insurance.update_traces(
            hovertemplate='<b>%{x}</b><br>Revenue: $%{y:,.2f}<extra></extra>'
        )
        fig_service_insurance.update_layout(
            title_font_size=14,
            title_x=0.5,
            title_font_color='#d4650f',
            height=350,
            margin=dict(t=50, b=50, l=50, r=50),
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig_service_insurance, use_container_width=True)

def create_seasonality_analysis(df):
    """Create seasonality analysis for health conditions"""
    seasonal_categories = ['Cold & Flu', 'Allergy', 'Vaccination']
    seasonal_df = df[df['MedicationCategory'].isin(seasonal_categories)]
    
    if seasonal_df.empty:
        return False
    
    monthly_trends = seasonal_df.groupby([seasonal_df['Date'].dt.month, 'MedicationCategory']).agg({
        'TotalPrice': 'sum',
        'TransactionID': 'count'
    }).reset_index()
    monthly_trends['Month'] = monthly_trends['Date'].apply(lambda x: calendar.month_name[x])
    
    # Seasonal trends chart
    fig_seasonal = px.line(
        monthly_trends,
        x='Month',
        y='TotalPrice',
        color='MedicationCategory',
        title="Seasonal Health Condition Revenue Trends",
        markers=True,
        color_discrete_sequence=['#d4650f', '#f97316', '#fb923c']
    )
    fig_seasonal.update_traces(
        line_width=3,
        marker_size=8,
        hovertemplate='<b>%{fullData.name}</b><br>Month: %{x}<br>Revenue: $%{y:,.2f}<extra></extra>'
    )
    fig_seasonal.update_layout(
        title_font_size=16,
        title_x=0.5,
        title_font_color='#d4650f',
        height=400,
        margin=dict(t=60, b=50, l=80, r=50)
    )
    st.plotly_chart(fig_seasonal, use_container_width=True)
    return True

def create_clinical_services_analysis(df):
    """Create clinical services uptake analysis"""
    clinical_df = df[df['Is_Clinical_Service']]
    
    if clinical_df.empty:
        return False
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Clinical services revenue
        clinical_revenue = clinical_df.groupby('ServiceType')['TotalPrice'].sum().reset_index()
        fig_clinical_rev = px.bar(
            clinical_revenue,
            x='ServiceType',
            y='TotalPrice',
            title="Clinical Services Revenue",
            color='TotalPrice',
            color_continuous_scale=['#fed7aa', '#d4650f'],
            text='TotalPrice'
        )
        fig_clinical_rev.update_traces(
            texttemplate='$%{text:,.0f}',
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Revenue: $%{y:,.2f}<extra></extra>'
        )
        fig_clinical_rev.update_layout(
            title_font_size=14,
            title_x=0.5,
            title_font_color='#d4650f',
            height=350,
            showlegend=False
        )
        st.plotly_chart(fig_clinical_rev, use_container_width=True)
    
    with col2:
        # Clinical services volume
        clinical_volume = clinical_df.groupby('ServiceType')['TransactionID'].count().reset_index()
        fig_clinical_vol = px.pie(
            clinical_volume,
            values='TransactionID',
            names='ServiceType',
            title="Clinical Services Volume Distribution",
            color_discrete_sequence=['#d4650f', '#f97316', '#fb923c']
        )
        fig_clinical_vol.update_traces(
            textposition="auto",
            textinfo="percent+label",
            textfont_size=11,
            hovertemplate='<b>%{label}</b><br>Appointments: %{value}<br>Percentage: %{percent}<extra></extra>'
        )
        fig_clinical_vol.update_layout(
            title_font_size=14,
            title_x=0.5,
            title_font_color='#d4650f',
            height=350
        )
        st.plotly_chart(fig_clinical_vol, use_container_width=True)
    
    return True

def create_daily_sales_trend(df):
    """Create daily sales trend line chart for pharmacy"""
    daily_sales = df.groupby('Date')['Revenue'].sum().reset_index()
    
    fig = px.line(
        daily_sales,
        x='Date',
        y='Revenue',
        title='Daily Pharmacy Sales Trend',
        labels={'Revenue': 'Total Revenue ($)', 'Date': 'Date'},
        line_shape='spline'
    )
    
    fig.update_traces(
        line_color='#d4650f',
        line_width=4,
        hovertemplate='<b>Date:</b> %{x}<br><b>Revenue:</b> $%{y:,.2f}<extra></extra>',
        mode='lines+markers',
        marker=dict(size=6, color='#d4650f')
    )
    
    fig.update_layout(
        title_font_size=16,
        title_x=0.5,
        title_y=0.95,
        title_font_color='#d4650f',
        height=400,
        margin=dict(t=80, b=50, l=80, r=50),
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(tickformat='$,.0f'),
        font_size=11
    )
    
    return fig

def create_pharmacy_specific_metrics(df):
    """Create pharmacy specific metrics"""
    st.markdown("""
    <div class="pharmacy-specific">
        <h3>Pharmacy Business Insights</h3>
        <p>Key performance indicators specific to your pharmacy operations and patient care</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Average prescription value
        rx_avg = df[df['ServiceType'] == 'Prescription']['TotalPrice'].mean() if len(df[df['ServiceType'] == 'Prescription']) > 0 else 0
        st.metric("Avg Prescription Value", f"${rx_avg:.2f}")
    
    with col2:
        # Clinical services uptake rate
        clinical_pct = (len(df[df['Is_Clinical_Service']]) / len(df)) * 100 if len(df) > 0 else 0
        st.metric("Clinical Services Rate", f"{clinical_pct:.1f}%")
    
    with col3:
        # Insurance utilization rate
        insurance_pct = (len(df[df['InsuranceUsed'] == 'Yes']) / len(df)) * 100 if len(df) > 0 else 0
        st.metric("Insurance Utilization", f"{insurance_pct:.1f}%")
    
    with col4:
        # Chronic medication patients
        chronic_patients = df[df['Is_Chronic']]['PatientID'].nunique()
        st.metric("Chronic Care Patients", f"{chronic_patients:,}")

def main():
    """Main Clarus pharmacy dashboard function"""
    # Header
    st.markdown('<h1 class="main-header">Clarus Pharmacy Analytics</h1>', unsafe_allow_html=True)
    
    # Welcome message
    st.markdown("""
    <div style="background-color: #fef7f0; padding: 1rem; border-radius: 10px; border-left: 5px solid #d4650f; margin-bottom: 2rem;">
        <h4>Welcome to Clarus Pharmacy Analytics</h4>
        <p>Transform your pharmacy data into actionable business insights with comprehensive analytics designed for modern pharmaceutical operations and patient care optimization.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar - Data options
    st.sidebar.header("Data Source")
    
    data_option = st.sidebar.radio(
        "Choose your data:",
        ["View Sample Data", "Upload Your Data"],
        help="Select how you'd like to explore the Clarus Pharmacy Analytics platform"
    )
    
    if data_option == "Upload Your Data":
        st.sidebar.markdown("**Upload your pharmacy data:**")
        uploaded_file = st.sidebar.file_uploader(
            "Choose CSV or Excel file",
            type=['csv', 'xlsx'],
            help="Supports CSV and Excel (.xlsx) files"
        )
        st.sidebar.markdown("*Your data stays secure and private.*")
    else:
        uploaded_file = None
    
    # Load data based on user choice
    if uploaded_file is not None:
        df = load_data(uploaded_file)
        st.sidebar.success("Your data loaded successfully!")
        st.sidebar.info(f"Analyzing {len(df):,} transactions")
    else:
        # Try to load sample data - check for both CSV and Excel formats
        sample_data_loaded = False
        
        # Try CSV first
        try:
            df = load_data('synthetic_pharmacy_data.csv')
            if data_option == "View Sample Data":
                st.sidebar.success("Sample data loaded (CSV)")
            sample_data_loaded = True
        except:
            # Try Excel if CSV fails
            try:
                df = load_data('synthetic_pharmacy_data.xlsx')
                if data_option == "View Sample Data":
                    st.sidebar.success("Sample data loaded (Excel)")
                sample_data_loaded = True
            except:
                pass
        
        # If neither format works, show error
        if not sample_data_loaded:
            st.error("No sample data available. Please upload your pharmacy data to get started.")
            st.error("No sample data available. Please upload your pharmacy data to get started.")
            st.info("""
            **Required columns:** TransactionID, Date, PatientID, ServiceType, MedicationCategory, Quantity, UnitPrice, InsuranceUsed, TotalPrice
            """)
            return
    
    if df is None:
        return
    
    # Display data info
    st.sidebar.markdown("---")
    st.sidebar.subheader("Data Overview")
    st.sidebar.write(f"**Total Transactions:** {len(df):,}")
    st.sidebar.write(f"**Date Range:** {df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}")
    st.sidebar.write(f"**Total Revenue:** ${df['Revenue'].sum():,.2f}")
    st.sidebar.write(f"**Unique Patients:** {df['PatientID'].nunique():,}")
    
    # Sidebar filters
    st.sidebar.header("Filter Your Data")
    
    # Month filter
    months_available = sorted(df['Month'].unique())
    month_names = [str(month) for month in months_available]
    
    selected_month_idx = st.sidebar.selectbox(
        "Select Month",
        range(len(months_available)),
        format_func=lambda x: month_names[x],
        index=len(months_available)-1
    )
    selected_month = months_available[selected_month_idx]
    
    # Filter data by selected month
    filtered_df = df[df['Month'] == selected_month]
    
    # Date range filter within the month
    min_date = filtered_df['Date'].min()
    max_date = filtered_df['Date'].max()
    
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    
    if len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df['Date'] >= pd.to_datetime(date_range[0])) & 
            (filtered_df['Date'] <= pd.to_datetime(date_range[1]))
        ]
    
    # Key Metrics Dashboard
    st.header("Performance Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_revenue = filtered_df['Revenue'].sum()
        st.metric("Total Revenue", f"${total_revenue:,.2f}")
    
    with col2:
        total_transactions = filtered_df['TransactionID'].nunique()
        st.metric("Total Transactions", f"{total_transactions:,}")
    
    with col3:
        avg_transaction = filtered_df['Revenue'].mean()
        st.metric("Avg Transaction", f"${avg_transaction:.2f}")
    
    with col4:
        unique_patients = filtered_df['PatientID'].nunique()
        st.metric("Unique Patients", f"{unique_patients:,}")
    
    # Pharmacy specific metrics
    create_pharmacy_specific_metrics(filtered_df)
    
    # Check data availability and create dynamic tabs
    data_availability = check_data_availability(filtered_df)
    
    # Build tab list based on available data
    tab_configs = [
        ("Revenue Analysis", True),  # Always available
        ("Prescription vs OTC", True),  # Always available
        ("Top Categories", True),  # Always available
    ]
    
    # Add conditional tabs
    if data_availability['compliance']:
        tab_configs.append(("Patient Compliance", True))
    
    if data_availability['seasonal'] or len(filtered_df[filtered_df['InsuranceUsed'].isin(['Yes', 'No'])]) > 0:
        tab_configs.append(("Business Patterns", True))
    
    if data_availability['clinical']:
        tab_configs.append(("Clinical Services", True))
    
    # Create tabs dynamically
    tab_names = [config[0] for config in tab_configs]
    tabs = st.tabs(tab_names)
    
    # Content for each tab
    for i, (tab_name, _) in enumerate(tab_configs):
        with tabs[i]:
            if tab_name == "Revenue Analysis":
                st.header("Sales Trend Analysis")
                st.plotly_chart(create_daily_sales_trend(filtered_df), use_container_width=True)
            
            elif tab_name == "Prescription vs OTC":
                st.header("Prescription vs OTC Sales Analysis")
                create_prescription_otc_chart(filtered_df)
            
            elif tab_name == "Top Categories":
                st.header("Top Medications and Categories")
                create_top_medications_chart(filtered_df)
                
                # Detailed category performance table
                st.subheader("Category Performance Details")
                category_details = filtered_df.groupby('MedicationCategory').agg({
                    'TotalPrice': ['sum', 'mean'],
                    'Quantity': 'sum',
                    'TransactionID': 'count',
                    'PatientID': 'nunique'
                }).round(2)
                
                category_details.columns = ['Total Revenue', 'Avg Revenue', 'Total Quantity', 'Transactions', 'Unique Patients']
                category_details = category_details.sort_values('Total Revenue', ascending=False)
                
                st.dataframe(
                    category_details.style.format({
                        'Total Revenue': '${:,.2f}',
                        'Avg Revenue': '${:.2f}',
                        'Total Quantity': '{:,}',
                        'Transactions': '{:,}',
                        'Unique Patients': '{:,}'
                    }),
                    use_container_width=True
                )
            
            elif tab_name == "Patient Compliance":
                st.header("Patient Refill Compliance Analysis")
                create_compliance_charts(filtered_df)
            
            elif tab_name == "Business Patterns":
                st.header("Business Patterns Analysis")
                
                # Insurance Analysis Section
                if len(filtered_df[filtered_df['InsuranceUsed'].isin(['Yes', 'No'])]) > 0:
                    st.subheader("Insurance vs Cash Pay Trends")
                    create_insurance_analysis(filtered_df)
                
                # Seasonal Analysis Section
                if data_availability['seasonal']:
                    st.subheader("Seasonal Health Condition Patterns")
                    create_seasonality_analysis(filtered_df)
            
            elif tab_name == "Clinical Services":
                st.header("Clinical Services Performance")
                create_clinical_services_analysis(filtered_df)
    
    # Raw Data Section
    with st.expander("View Detailed Transaction Data"):
        st.subheader("Recent Pharmacy Transactions")
        display_df = filtered_df.sort_values('Date', ascending=False)
        
        # Show formatted transaction data
        formatted_display = display_df[['Date', 'PatientID', 'ServiceType', 'MedicationCategory', 
                                       'Quantity', 'UnitPrice', 'TotalPrice', 'InsuranceUsed']].head(50)
        
        st.dataframe(
            formatted_display.style.format({
                'UnitPrice': '${:.2f}',
                'TotalPrice': '${:.2f}',
                'Date': lambda x: x.strftime('%Y-%m-%d')
            }),
            use_container_width=True,
            height=400
        )
        
        if len(display_df) > 50:
            st.info(f"Showing first 50 of {len(display_df):,} transactions. Download complete report below.")
        
        # Download button
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download Pharmacy Analytics Report (CSV)",
            data=csv,
            file_name=f"clarus_pharmacy_analytics_{selected_month}.csv",
            mime="text/csv"
        )
    
    # Footer
    st.markdown("---")
    st.markdown("**© 2025 Clarus** | Empowering Data-Driven Insights")

if __name__ == "__main__":
    main()