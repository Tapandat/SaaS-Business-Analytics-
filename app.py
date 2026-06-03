# Paste Parts 1 to 6 here
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sqlite3
st.set_page_config(
    page_title="SaaS Business Analytics Platform",
    page_icon="📊",
    layout="wide"
)

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from streamlit_oauth import OAuth2Component

from sklearn.preprocessing import (
    LabelEncoder,
    StandardScaler
)

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    roc_auc_score,
    confusion_matrix
)

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import (
    getSampleStyleSheet
)

from io import BytesIO
# ==================================================
# SQLITE DATABASE
# ==================================================

import sqlite3

conn = sqlite3.connect(
    "users.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password TEXT
)
""")

conn.commit()

# ==================================================
# DATABASE FUNCTIONS
# ==================================================

def register_user(email, password):

    try:

        cursor.execute(
            """
            INSERT INTO users(email,password)
            VALUES(?,?)
            """,
            (email, password)
        )

        conn.commit()

        return True

    except:

        return False


def login_user(email, password):

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE email=?
        AND password=?
        """,
        (email, password)
    )

    return cursor.fetchone()


# ==================================================
# SESSION STATE
# ==================================================

if "logged_in" not in st.session_state:

    st.session_state.logged_in = False

if "user_email" not in st.session_state:

    st.session_state.user_email = ""


# ==================================================
# UI STYLING
# ==================================================

st.markdown("""
<style>

.main-title{
    text-align:center;
    font-size:45px;
    font-weight:bold;
    color:#1E88E5;
}

.sub-title{
    text-align:center;
    font-size:18px;
    color:gray;
}

</style>
""", unsafe_allow_html=True)

st.markdown(
"""
<div class='main-title'>
📊 SaaS Business Analytics Platform
</div>
""",
unsafe_allow_html=True
)

st.markdown(
"""
<div class='sub-title'>
Predict Churn • Segment Customers • Forecast Revenue
</div>
""",
unsafe_allow_html=True
)

st.markdown("---")


# ==================================================
# AUTHENTICATION MENU
# ==================================================

auth_option = st.selectbox(
    "Authentication",
    [
        "Login",
        "Register",
        "Google Login"
    ]
)


# ==================================================
# LOGIN
# ==================================================

if auth_option == "Login":

    st.subheader("Login")

    email = st.text_input(
        "Email"
    )

    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button("Login"):

        user = login_user(
            email,
            password
        )

        if user:

            st.session_state.logged_in = True

            st.session_state.user_email = email

            st.success(
                "Login Successful"
            )

            st.rerun()

        else:

            st.error(
                "Invalid Credentials"
            )


# ==================================================
# REGISTER
# ==================================================

elif auth_option == "Register":

    st.subheader(
        "Create Account"
    )

    email = st.text_input(
        "Email"
    )

    password = st.text_input(
        "Password",
        type="password"
    )

    confirm = st.text_input(
        "Confirm Password",
        type="password"
    )

    if st.button(
        "Register"
    ):

        if password != confirm:

            st.error(
                "Passwords do not match"
            )

        else:

            success = register_user(
                email,
                password
            )

            if success:

                st.success(
                    "Registration Successful"
                )

            else:

                st.error(
                    "User already exists"
                )


# ==================================================
# GOOGLE LOGIN
# ==================================================

# ==================================================
# GOOGLE LOGIN
# ==================================================
elif auth_option == "Google Login":

    st.subheader(
        "Google Sign In"
    )

    CLIENT_ID = st.secrets[
        "GOOGLE_CLIENT_ID"
    ]

    CLIENT_SECRET = st.secrets[
        "GOOGLE_CLIENT_SECRET"
    ]

    AUTHORIZE_URL = (
        "https://accounts.google.com/o/oauth2/auth"
    )

    TOKEN_URL = (
        "https://oauth2.googleapis.com/token"
    )

    REVOKE_URL = (
        "https://oauth2.googleapis.com/revoke"
    )

    oauth2 = OAuth2Component(
        CLIENT_ID,
        CLIENT_SECRET,
        AUTHORIZE_URL,
        TOKEN_URL,
        TOKEN_URL,
        REVOKE_URL
    )

    result = oauth2.authorize_button(
        name="Continue with Google",
        redirect_uri=
        "https://jebqftjqbrdyz3xwhpn74q.streamlit.app/component/streamlit_oauth.authorize_button/index.html",
        scope="openid email profile",
        key="google_login"
    )

    st.write(
        "OAuth Result:",
        result
    )

    if result:

        st.success(
            "OAuth callback received"
        )

        st.write(
            result
        )

        st.stop()


# ==================================================
# SIDEBAR
# ==================================================

if st.session_state.logged_in:

    with st.sidebar:

        st.success(
            f"Logged in as\n\n{st.session_state.user_email}"
        )

        if st.button(
            "Logout"
        ):

            st.session_state.logged_in = False

            st.session_state.user_email = ""

            st.rerun()


# ==================================================
# ACCESS CONTROL
# ==================================================

if not st.session_state.logged_in:

    st.warning(
        "Please Login To Continue"
    )

    st.stop()

# ==================================================
# FILE UPLOAD
# ==================================================

uploaded_file = st.file_uploader(
    "Upload Telco Customer Churn Dataset",
    type=["csv","xlsx"]
)

if uploaded_file is not None:

    try:

        if uploaded_file.name.endswith(
            ".csv"
        ):

            df = pd.read_csv(
                uploaded_file
            )

        else:

            df = pd.read_excel(
                uploaded_file
            )

        st.success(
            "Dataset Uploaded Successfully"
        )

        # ==================================
        # CLEAN TOTAL CHARGES
        # ==================================

        if "TotalCharges" in df.columns:

            df["TotalCharges"] = (
                pd.to_numeric(
                    df["TotalCharges"],
                    errors="coerce"
                )
            )

            df["TotalCharges"] = (
                df["TotalCharges"]
                .fillna(0)
            )

        # ==================================
        # GLOBAL VARIABLES
        # ==================================

        total_customers = len(df)

        churn_rate = 0

        if "Churn" in df.columns:

            churn_rate = (
                (
                    df["Churn"] == "Yes"
                ).mean()
                * 100
            )

        accuracy = 0
        precision = 0
        recall = 0
        auc = 0

        forecast_value = 0

        importance = None

        high_risk_customers = None

        top_feature = "N/A"

        tabs = st.tabs(
            [
                "Dashboard",
                "Analytics",
                "Churn Prediction",
                "Customer Intelligence",
                "Segmentation",
                "Forecasting",
                "Insights"
            ]
        )

        (
            tab1,
            tab2,
            tab3,
            tab4,
            tab5,
            tab6,
            tab7
        ) = tabs
                # ==================================================
        # DASHBOARD
        # ==================================================

        with tab1:

            st.subheader(
                "Dataset Overview"
            )

            st.dataframe(
                df.head(10),
                use_container_width=True
            )

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "Total Customers",
                total_customers
            )

            c2.metric(
                "Churn Rate",
                f"{churn_rate:.2f}%"
            )

            if "MonthlyCharges" in df.columns:

                c3.metric(
                    "Average Monthly Charges",
                    f"${df['MonthlyCharges'].mean():.2f}"
                )

            if "TotalCharges" in df.columns:

                c4.metric(
                    "Average Total Charges",
                    f"${df['TotalCharges'].mean():.2f}"
                )

            st.subheader(
                "Dataset Information"
            )

            info_df = pd.DataFrame({
                "Column": df.columns,
                "Data Type": [
                    str(df[col].dtype)
                    for col in df.columns
                ]
            })

            st.dataframe(
                info_df,
                use_container_width=True
            )

            st.subheader(
                "Missing Values"
            )

            missing_df = pd.DataFrame({
                "Column": df.columns,
                "Missing Values":
                df.isnull().sum().values
            })

            st.dataframe(
                missing_df,
                use_container_width=True
            )

        # ==================================================
        # ANALYTICS
        # ==================================================

        with tab2:

            st.subheader(
                "Customer Churn Distribution"
            )

            if "Churn" in df.columns:

                fig1 = px.pie(
                    df,
                    names="Churn",
                    title="Customer Churn Breakdown"
                )

                st.plotly_chart(
                    fig1,
                    use_container_width=True
                )

            # ==========================================
            # CONTRACT ANALYSIS
            # ==========================================

            if "Contract" in df.columns:

                st.subheader(
                    "Contract Type Analysis"
                )

                contract_df = (
                    df["Contract"]
                    .value_counts()
                    .reset_index()
                )

                contract_df.columns = [
                    "Contract",
                    "Count"
                ]

                fig2 = px.bar(
                    contract_df,
                    x="Contract",
                    y="Count",
                    title="Customer Contracts"
                )

                st.plotly_chart(
                    fig2,
                    use_container_width=True
                )

            # ==========================================
            # TENURE ANALYSIS
            # ==========================================

            if "tenure" in df.columns:

                st.subheader(
                    "Customer Tenure Distribution"
                )

                fig3 = px.histogram(
                    df,
                    x="tenure",
                    nbins=30,
                    title="Customer Tenure"
                )

                st.plotly_chart(
                    fig3,
                    use_container_width=True
                )

            # ==========================================
            # MONTHLY CHARGES
            # ==========================================

            if "MonthlyCharges" in df.columns:

                st.subheader(
                    "Monthly Charges Distribution"
                )

                fig4 = px.histogram(
                    df,
                    x="MonthlyCharges",
                    nbins=30,
                    title="Monthly Charges"
                )

                st.plotly_chart(
                    fig4,
                    use_container_width=True
                )

            # ==========================================
            # CHURN VS CONTRACT
            # ==========================================

            if (
                "Contract" in df.columns
                and "Churn" in df.columns
            ):

                st.subheader(
                    "Churn by Contract Type"
                )

                churn_contract = pd.crosstab(
                    df["Contract"],
                    df["Churn"]
                )

                st.dataframe(
                    churn_contract,
                    use_container_width=True
                )

                fig5 = px.bar(
                    churn_contract,
                    barmode="group",
                    title="Contract Type vs Churn"
                )

                st.plotly_chart(
                    fig5,
                    use_container_width=True
                )

            # ==========================================
            # REVENUE ANALYSIS
            # ==========================================

            if (
                "MonthlyCharges" in df.columns
                and "Churn" in df.columns
            ):

                st.subheader(
                    "Revenue Analysis"
                )

                fig6 = px.box(
                    df,
                    y="MonthlyCharges",
                    color="Churn",
                    title="Monthly Charges by Churn"
                )

                st.plotly_chart(
                    fig6,
                    use_container_width=True
                )

            # ==========================================
            # ANALYTICS SUMMARY
            # ==========================================

            st.subheader(
                "Analytics Summary"
            )

            st.info(
                f"""
                Total Customers Analysed:
                {total_customers}

                Current Churn Rate:
                {churn_rate:.2f}%

                Customers with month-to-month
                contracts generally show
                higher churn behaviour.

                Long-tenure customers tend
                to remain loyal and generate
                higher lifetime value.

                Revenue trends indicate that
                customer retention directly
                impacts future revenue growth.
                """
            )
                    # ==================================================
        # CHURN PREDICTION
        # ==================================================

        with tab3:

            st.subheader(
                "AI Churn Prediction Engine"
            )

            if "Churn" in df.columns:

                ml_df = df.copy()

                if "customerID" in ml_df.columns:

                    ml_df = ml_df.drop(
                        columns=["customerID"]
                    )

                # ==================================
                # ENCODE TARGET
                # ==================================

                target_encoder = LabelEncoder()

                ml_df["Churn"] = (
                    target_encoder.fit_transform(
                        ml_df["Churn"]
                    )
                )

                # ==================================
                # ENCODE FEATURES
                # ==================================

                for col in ml_df.columns:

                    if ml_df[col].dtype == "object":

                        encoder = LabelEncoder()

                        ml_df[col] = (
                            encoder.fit_transform(
                                ml_df[col].astype(str)
                            )
                        )

                X = ml_df.drop(
                    columns=["Churn"]
                )

                y = ml_df["Churn"]

                X_train, X_test, y_train, y_test = (
                    train_test_split(
                        X,
                        y,
                        test_size=0.20,
                        random_state=42
                    )
                )

                # ==================================
                # RANDOM FOREST
                # ==================================

                churn_model = (
                    RandomForestClassifier(
                        n_estimators=200,
                        random_state=42
                    )
                )

                churn_model.fit(
                    X_train,
                    y_train
                )

                predictions = (
                    churn_model.predict(
                        X_test
                    )
                )

                # ==================================
                # MODEL METRICS
                # ==================================

                accuracy = (
                    accuracy_score(
                        y_test,
                        predictions
                    )
                )

                precision = (
                    precision_score(
                        y_test,
                        predictions
                    )
                )

                recall = (
                    recall_score(
                        y_test,
                        predictions
                    )
                )

                auc = (
                    roc_auc_score(
                        y_test,
                        churn_model.predict_proba(
                            X_test
                        )[:,1]
                    )
                )

                m1,m2,m3,m4 = st.columns(4)

                m1.metric(
                    "Accuracy",
                    f"{accuracy*100:.2f}%"
                )

                m2.metric(
                    "Precision",
                    f"{precision:.3f}"
                )

                m3.metric(
                    "Recall",
                    f"{recall:.3f}"
                )

                m4.metric(
                    "ROC AUC",
                    f"{auc:.3f}"
                )

                st.success(
                    "Random Forest Model Trained Successfully"
                )

                # ==================================
                # FEATURE IMPORTANCE
                # ==================================

                importance = pd.DataFrame(
                    {
                        "Feature": X.columns,
                        "Importance":
                        churn_model.feature_importances_
                    }
                )

                importance = (
                    importance
                    .sort_values(
                        "Importance",
                        ascending=False
                    )
                )

                top_feature = (
                    importance.iloc[0]["Feature"]
                )

                st.subheader(
                    "Top Churn Drivers"
                )

                fig_imp = px.bar(
                    importance.head(10),
                    x="Importance",
                    y="Feature",
                    orientation="h",
                    title="Features Driving Churn"
                )

                st.plotly_chart(
                    fig_imp,
                    use_container_width=True
                )

                # ==================================
                # CONFUSION MATRIX
                # ==================================

                st.subheader(
                    "Confusion Matrix"
                )

                cm = confusion_matrix(
                    y_test,
                    predictions
                )

                cm_df = pd.DataFrame(
                    cm,
                    columns=[
                        "Predicted No",
                        "Predicted Yes"
                    ],
                    index=[
                        "Actual No",
                        "Actual Yes"
                    ]
                )

                st.dataframe(
                    cm_df,
                    use_container_width=True
                )

                # ==================================
                # CHURN PROBABILITY
                # ==================================

                probabilities = (
                    churn_model.predict_proba(
                        X
                    )
                )

                ml_df[
                    "Churn_Probability"
                ] = probabilities[:,1]

                st.subheader(
                    "Churn Probability Distribution"
                )

                fig_prob = px.histogram(
                    ml_df,
                    x="Churn_Probability",
                    nbins=30,
                    title="Predicted Churn Probability"
                )

                st.plotly_chart(
                    fig_prob,
                    use_container_width=True
                )

                # ==================================
                # HIGH RISK CUSTOMERS
                # ==================================

                high_risk_customers = (
                    ml_df[
                        ml_df[
                            "Churn_Probability"
                        ] > 0.70
                    ]
                )

                st.metric(
                    "High Risk Customers",
                    len(high_risk_customers)
                )

                display_cols = []

                for col in [
                    "tenure",
                    "MonthlyCharges",
                    "TotalCharges",
                    "Churn_Probability"
                ]:

                    if col in high_risk_customers.columns:

                        display_cols.append(
                            col
                        )

                st.subheader(
                    "High Risk Customer Sample"
                )

                st.dataframe(
                    high_risk_customers[
                        display_cols
                    ].head(20),
                    use_container_width=True
                )

            else:

                st.error(
                    "Churn column not found."
                )
                        # ==================================================
        # CUSTOMER INTELLIGENCE
        # ==================================================

        with tab4:

            st.subheader(
                "AI Customer Intelligence Engine"
            )

            if high_risk_customers is not None:

                st.success(
                    f"{len(high_risk_customers)} High Risk Customers Identified"
                )

                st.info(
                    f"""
                    Machine Learning Analysis indicates
                    '{top_feature}'
                    is currently the strongest predictor
                    of customer churn.
                    """
                )

                st.subheader(
                    "Customer-Level Churn Analysis"
                )

                customer_count = 1

                for idx, row in (
                    high_risk_customers
                    .head(20)
                    .iterrows()
                ):

                    reasons = []

                    recommendations = []

                    # ==========================
                    # TENURE ANALYSIS
                    # ==========================

                    if (
                        "tenure" in row.index
                        and row["tenure"] < 12
                    ):

                        reasons.append(
                            "Customer tenure is low, indicating weak loyalty."
                        )

                        recommendations.append(
                            "Provide onboarding support and retention incentives."
                        )

                    # ==========================
                    # MONTHLY CHARGES
                    # ==========================

                    if (
                        "MonthlyCharges" in row.index
                        and row["MonthlyCharges"]
                        > df["MonthlyCharges"].mean()
                    ):

                        reasons.append(
                            "Monthly charges are above the customer average."
                        )

                        recommendations.append(
                            "Offer loyalty discounts or bundled plans."
                        )

                    # ==========================
                    # TOTAL CHARGES
                    # ==========================

                    if (
                        "TotalCharges" in row.index
                        and row["TotalCharges"]
                        < df["TotalCharges"].mean()
                    ):

                        reasons.append(
                            "Customer lifetime value is relatively low."
                        )

                        recommendations.append(
                            "Increase engagement through personalized offers."
                        )

                    # ==========================
                    # CONTRACT ANALYSIS
                    # ==========================

                    if (
                        "Contract" in top_feature
                    ):

                        reasons.append(
                            "Contract structure appears strongly linked to churn."
                        )

                        recommendations.append(
                            "Encourage migration to annual contracts."
                        )

                    # ==========================
                    # RISK SCORE
                    # ==========================

                    risk_score = (
                        row["Churn_Probability"]
                        * 100
                    )

                    narrative = f"""
                    Customer #{customer_count}

                    Churn Probability:
                    {risk_score:.2f}%

                    Analysis:

                    {' '.join(reasons)}

                    Recommended Actions:

                    {' '.join(recommendations)}
                    """

                    st.error(
                        narrative
                    )

                    customer_count += 1

                # ====================================
                # HIGH RISK SUMMARY
                # ====================================

                st.subheader(
                    "High Risk Customer Summary"
                )

                avg_risk = (
                    high_risk_customers[
                        "Churn_Probability"
                    ]
                    .mean()
                    * 100
                )

                st.metric(
                    "Average High Risk Probability",
                    f"{avg_risk:.2f}%"
                )

                # ====================================
                # RISK DISTRIBUTION
                # ====================================

                risk_df = (
                    high_risk_customers.copy()
                )

                risk_df["Risk_Level"] = pd.cut(
                    risk_df[
                        "Churn_Probability"
                    ],
                    bins=[
                        0,
                        0.5,
                        0.7,
                        1
                    ],
                    labels=[
                        "Low",
                        "Medium",
                        "High"
                    ]
                )

                fig_risk = px.pie(
                    risk_df,
                    names="Risk_Level",
                    title="Risk Distribution"
                )

                st.plotly_chart(
                    fig_risk,
                    use_container_width=True
                )

                # ====================================
                # CUSTOMER VALUE MATRIX
                # ====================================

                if (
                    "MonthlyCharges"
                    in risk_df.columns
                ):

                    st.subheader(
                        "Customer Value Matrix"
                    )

                    fig_value = px.scatter(
                        risk_df,
                        x="MonthlyCharges",
                        y="Churn_Probability",
                        title="Revenue vs Churn Risk"
                    )

                    st.plotly_chart(
                        fig_value,
                        use_container_width=True
                    )

            else:

                st.warning(
                    "Run Churn Prediction First"
                )
                        # ==================================================
        # CUSTOMER SEGMENTATION
        # ==================================================

        with tab5:

            st.subheader(
                "Customer Segmentation (KMeans)"
            )

            seg_df = df.copy()

            if "customerID" in seg_df.columns:

                seg_df = seg_df.drop(
                    columns=["customerID"]
                )

            for col in seg_df.columns:

                if seg_df[col].dtype == "object":

                    encoder = LabelEncoder()

                    seg_df[col] = (
                        encoder.fit_transform(
                            seg_df[col].astype(str)
                        )
                    )

            numeric_cols = (
                seg_df
                .select_dtypes(
                    include=np.number
                )
                .columns
            )

            if len(numeric_cols) >= 2:

                scaler = StandardScaler()

                scaled_data = (
                    scaler.fit_transform(
                        seg_df[numeric_cols]
                    )
                )

                kmeans = KMeans(
                    n_clusters=3,
                    random_state=42,
                    n_init=10
                )

                seg_df["Segment"] = (
                    kmeans.fit_predict(
                        scaled_data
                    )
                )

                st.success(
                    "3 Customer Segments Generated Successfully"
                )

                # ==================================
                # SEGMENT VISUALIZATION
                # ==================================

                x_col = (
                    "MonthlyCharges"
                    if "MonthlyCharges"
                    in seg_df.columns
                    else numeric_cols[0]
                )

                y_col = (
                    "tenure"
                    if "tenure"
                    in seg_df.columns
                    else numeric_cols[1]
                )

                fig_seg = px.scatter(
                    seg_df,
                    x=x_col,
                    y=y_col,
                    color="Segment",
                    title="Customer Segmentation Map"
                )

                st.plotly_chart(
                    fig_seg,
                    use_container_width=True
                )

                # ==================================
                # SEGMENT SUMMARY
                # ==================================

                st.subheader(
                    "Segment Summary"
                )

                segment_summary = (
                    seg_df
                    .groupby("Segment")
                    [numeric_cols]
                    .mean()
                    .round(2)
                )

                st.dataframe(
                    segment_summary,
                    use_container_width=True
                )

                # ==================================
                # SEGMENT DISTRIBUTION
                # ==================================

                fig_pie = px.pie(
                    seg_df,
                    names="Segment",
                    title="Segment Distribution"
                )

                st.plotly_chart(
                    fig_pie,
                    use_container_width=True
                )

                # ==================================
                # CUSTOMER PERSONAS
                # ==================================

                st.subheader(
                    "Customer Personas"
                )

                overall_tenure = (
                    seg_df["tenure"].mean()
                    if "tenure" in seg_df.columns
                    else 0
                )

                overall_monthly = (
                    seg_df["MonthlyCharges"].mean()
                    if "MonthlyCharges"
                    in seg_df.columns
                    else 0
                )

                for segment in sorted(
                    seg_df["Segment"].unique()
                ):

                    segment_data = (
                        seg_df[
                            seg_df["Segment"]
                            == segment
                        ]
                    )

                    avg_tenure = (
                        segment_data["tenure"].mean()
                        if "tenure"
                        in segment_data.columns
                        else 0
                    )

                    avg_monthly = (
                        segment_data[
                            "MonthlyCharges"
                        ].mean()
                        if "MonthlyCharges"
                        in segment_data.columns
                        else 0
                    )

                    customer_count = (
                        len(segment_data)
                    )

                    if (
                        avg_monthly
                        > overall_monthly
                    ):

                        persona = (
                            "High Value Customers"
                        )

                        description = """
                        These customers generate
                        above-average revenue and
                        should be prioritized for
                        retention and premium
                        service offerings.
                        """

                    elif (
                        avg_tenure
                        < overall_tenure
                    ):

                        persona = (
                            "At-Risk Customers"
                        )

                        description = """
                        These customers have lower
                        loyalty and require targeted
                        retention campaigns.
                        """

                    else:

                        persona = (
                            "Growth Customers"
                        )

                        description = """
                        These customers show
                        long-term potential and
                        should be nurtured with
                        upsell opportunities.
                        """

                    st.info(
                        f"""
                        Segment {segment}

                        Persona:
                        {persona}

                        Customers:
                        {customer_count}

                        Average Tenure:
                        {avg_tenure:.2f}

                        Average Monthly Charges:
                        {avg_monthly:.2f}

                        Insight:
                        {description}
                        """
                    )

                # ==================================
                # SEGMENT RECOMMENDATIONS
                # ==================================

                st.subheader(
                    "Segment Recommendations"
                )

                st.success(
                    """
                    High Value Customers:
                    Offer premium plans and
                    loyalty rewards.
                    """
                )

                st.warning(
                    """
                    At-Risk Customers:
                    Launch retention campaigns
                    and onboarding programs.
                    """
                )

                st.info(
                    """
                    Growth Customers:
                    Focus on upselling and
                    cross-selling opportunities.
                    """
                )

            else:

                st.error(
                    "Not enough numeric columns available for segmentation."
                )
                        # ==================================================
        # REVENUE FORECASTING
        # ==================================================

        with tab6:

            st.subheader(
                "Revenue Forecasting"
            )

            if (
                "MonthlyCharges" in df.columns
                and "tenure" in df.columns
            ):

                forecast_df = df.copy()

                forecast_df = (
                    forecast_df
                    .sort_values(
                        by="tenure"
                    )
                )

                X_forecast = (
                    forecast_df[
                        ["tenure"]
                    ]
                )

                y_forecast = (
                    forecast_df[
                        "MonthlyCharges"
                    ]
                )

                forecast_model = (
                    LinearRegression()
                )

                forecast_model.fit(
                    X_forecast,
                    y_forecast
                )

                next_tenure = (
                    forecast_df[
                        "tenure"
                    ].max()
                    + 1
                )

                forecast_value = (
                    forecast_model.predict(
                        [[next_tenure]]
                    )[0]
                )

                st.metric(
                    "Predicted Future Revenue",
                    f"${forecast_value:.2f}"
                )

                forecast_df[
                    "Predicted"
                ] = (
                    forecast_model.predict(
                        X_forecast
                    )
                )

                fig_forecast = px.line(
                    forecast_df,
                    x="tenure",
                    y=[
                        "MonthlyCharges",
                        "Predicted"
                    ],
                    title="Revenue Forecast Trend"
                )

                st.plotly_chart(
                    fig_forecast,
                    use_container_width=True
                )

                growth_rate = (
                    (
                        forecast_value
                        -
                        forecast_df[
                            "MonthlyCharges"
                        ].mean()
                    )
                    /
                    forecast_df[
                        "MonthlyCharges"
                    ].mean()
                ) * 100

                st.metric(
                    "Expected Growth %",
                    f"{growth_rate:.2f}%"
                )

                if growth_rate > 0:

                    st.success(
                        "Revenue growth is expected."
                    )

                else:

                    st.warning(
                        "Revenue growth appears weak."
                    )

            else:

                st.warning(
                    "MonthlyCharges and tenure columns required."
                )

        # ==================================================
        # EXECUTIVE INSIGHTS
        # ==================================================

        with tab7:

            st.subheader(
                "Executive Business Insights"
            )

            st.success(
                f"Total Customers Analysed: {total_customers}"
            )

            st.info(
                f"Overall Churn Rate: {churn_rate:.2f}%"
            )

            st.success(
                f"Model Accuracy: {accuracy*100:.2f}%"
            )

            st.success(
                f"Precision: {precision:.3f}"
            )

            st.success(
                f"Recall: {recall:.3f}"
            )

            st.success(
                f"ROC AUC: {auc:.3f}"
            )

            if importance is not None:

                st.subheader(
                    "Top Churn Drivers"
                )

                for feature in (
                    importance
                    .head(5)
                    ["Feature"]
                    .tolist()
                ):

                    st.write(
                        f"• {feature}"
                    )

                st.warning(
                    f"""
                    Strongest Churn Driver:

                    {top_feature}
                    """
                )

            # ==================================
            # AI EXECUTIVE REPORT
            # ==================================

            st.subheader(
                "AI Generated Executive Report"
            )

            executive_report = f"""
            The SaaS Business Analytics Platform
            analysed {total_customers}
            customer records.

            The observed churn rate is
            {churn_rate:.2f}%.

            A Random Forest machine learning
            model was trained for customer
            churn prediction and achieved
            an accuracy of
            {accuracy*100:.2f}%.

            The most influential churn factor
            identified was:
            {top_feature}.

            Customer segmentation using
            KMeans clustering identified
            High Value,
            Growth,
            and At-Risk customer groups.

            Revenue forecasting was performed
            using Linear Regression to estimate
            future customer revenue behaviour.

            Customer Intelligence analysis
            generated individual churn
            explanations and retention
            recommendations.

            Management should prioritize
            retention strategies for
            high-risk customers and
            improve long-term customer
            engagement.
            """

            st.success(
                executive_report
            )

            # ==================================
            # BUSINESS RECOMMENDATIONS
            # ==================================

            st.subheader(
                "Business Recommendations"
            )

            st.write(
                "1. Focus retention campaigns on high-risk customers."
            )

            st.write(
                "2. Promote annual contracts over month-to-month plans."
            )

            st.write(
                "3. Create loyalty reward programs."
            )

            st.write(
                "4. Improve onboarding for low-tenure customers."
            )

            st.write(
                "5. Upsell premium services to high-value segments."
            )

            st.write(
                "6. Monitor churn drivers continuously."
            )

        # ==================================================
        # PDF DOWNLOAD
        # ==================================================

        st.markdown("---")

        pdf_buffer = create_pdf_report(
            total_customers,
            churn_rate,
            accuracy * 100,
            precision,
            recall,
            auc,
            forecast_value,
            top_feature
        )

        st.download_button(
            label="📄 Download Business Report",
            data=pdf_buffer,
            file_name="Business_Analytics_Report.pdf",
            mime="application/pdf"
        )

    except Exception as e:

        st.error(
            f"Application Error: {e}"
        )
      
