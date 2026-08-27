import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import numpy as np
from ultralytics import YOLO
from datetime import datetime, timedelta
import io
import sys
from pathlib import Path
from database import SafetyDatabase
import cv2

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

# ----------------------------------
# Page Configuration
# ----------------------------------
st.set_page_config(layout="wide", page_title="Safety Detection Dashboard")

# ----------------------------------
# Load Model (cached)
# ----------------------------------
@st.cache_resource
def load_model():
    return YOLO("best.pt")

@st.cache_resource
def load_database():
    return SafetyDatabase()

model = load_model()
db = load_database()
st.write(model.names)

# ----------------------------------
# Tracking Memory
# ----------------------------------
last_saved_time = {}
person_counter = 0
tracked_people = {}

PERSON_DISTANCE_THRESHOLD = 80
PERSON_TIMEOUT_SECONDS = 10

# ----------------------------------
# Database Query Functions
# ----------------------------------
def get_alerts_dataframe():
    """Get alerts from database as DataFrame"""
    alerts = db.get_all_alerts(limit=100)
    if not alerts:
        # Return empty dataframe with correct columns
        return pd.DataFrame(columns=["Time", "Camera", "Zone", "Violation", "Risk", "Confidence", "Status"])

    df = pd.DataFrame(alerts)
    # Rename columns to match dashboard
    if "created_at" in df.columns:
        df["Time"] = pd.to_datetime(df["created_at"])
    else:
        df["Time"] = datetime.now()

    df["Violation"] = df["violation_type"]
    df["Risk"] = df["risk_level"]
    df["Confidence"] = df["confidence"]
    df["Camera"] = df["camera_name"]
    df["Zone"] = df["zone_name"]
    df["Status"] = df["status"]

    return df[["Time", "Camera", "Zone", "Violation", "Risk", "Confidence", "Status"]]

def get_hourly_violations():
    """Get hourly violations from database"""
    hourly_data = db.get_hourly_violations()
    if hourly_data:
        return pd.DataFrame(hourly_data)
    else:
        # Return empty dataframe
        hours = [f"{i:02d}:00" for i in range(24)]
        counts = [0] * 24
        return pd.DataFrame({"Hour": hours, "Violations": counts})

def get_compliance_trend():
    """Calculate 7-day compliance trend from detections"""
    conn = db.get_connection()
    cursor = conn.cursor()

    data = []
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).date()
        cursor.execute('''
            SELECT
                COUNT(*) as total_persons,
                SUM(violations_count) as total_violations
            FROM detections
            WHERE DATE(created_at) = ?
        ''', (str(date),))

        result = cursor.fetchone()
        total_persons = result[0] or 0
        total_violations = result[1] or 0

        if total_persons > 0:
            compliance = ((total_persons - total_violations) / total_persons) * 100
        else:
            compliance = 100

        data.append({
            "Day": date.strftime("%A"),
            "Compliance %": compliance
        })

    conn.close()
    return pd.DataFrame(list(reversed(data)))

def get_kpi_metrics():
    """Calculate KPI metrics from database"""
    alerts = db.get_all_alerts()
    pending = len(db.get_alerts_by_status("Pending"))
    high_risk = len([a for a in alerts if a["risk_level"] == "High"])

    cameras = db.get_camera_status()
    online_cameras = len([c for c in cameras if c["status"] == "Online"])
    total_cameras = len(cameras) if cameras else 1

    compliance = db.get_daily_compliance()

    return {
        "active_alerts": len(alerts),
        "high_risk": high_risk,
        "compliance": compliance,
        "cameras_online": online_cameras,
        "total_cameras": total_cameras
    }

# ----------------------------------
# PAGE 1: LIVE MONITORING + IMAGE DETECTION
# ----------------------------------
def page_live_monitoring():
    st.title("Safety Detection Dashboard")

    # Tabs
    tab1, tab2, tab3, tab4= st.tabs(["Live Camera Detection", "Dashboard", "Site Insights", "Reports & Evidence"])

    # ======================== TAB 2: DASHBOARD ========================
    with tab2:
        # Get KPI data from database
        kpis = get_kpi_metrics()

        # KPI Strip
        st.subheader("Key Performance Indicators")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("🚨 Active Alerts", int(kpis["active_alerts"]))
        with col2:
            st.metric("⚠️ High Risk", int(kpis["high_risk"]))
        with col3:
            st.metric("✅ Compliance Today", f"{kpis['compliance']:.1f}%")
        with col4:
            st.metric("📹 Cameras Online", f"{kpis['cameras_online']}/{kpis['total_cameras']}")

        st.divider()

        # Filters
        st.subheader("Filters")
        col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)

        with col_filter1:
            date_filter = st.date_input("Select Date", value=datetime.now())
        with col_filter2:
            all_alerts = db.get_all_alerts()
            cameras = sorted(list(set([a["camera_name"] for a in all_alerts if a["camera_name"]])))
            cameras = ["All"] + cameras if cameras else ["All"]
            site_filter = st.selectbox("Site/Zone/Camera", cameras)
        with col_filter3:
            violation_types = ["All", "NO-Hardhat", "NO-Mask", "NO-Safety Vest"]
            violation_filter = st.selectbox("Violation Type", violation_types)
        with col_filter4:
            risk_filter = st.selectbox("Risk Level", ["All", "High", "Medium", "Low"])

        status_filter = st.multiselect("Status", ["Acknowledged", "Pending", "Resolved"], default=["Pending"])

        st.divider()

        # Alerts Table
        st.subheader("Alerts Table")
        alerts_df = get_alerts_dataframe()

        if len(alerts_df) > 0:

            alerts_df["Time"] = pd.to_datetime(alerts_df["Time"])

            alerts_df = alerts_df[alerts_df["Time"].dt.date == date_filter]

            if site_filter != "All":
                alerts_df = alerts_df[alerts_df["Camera"] == site_filter]
            
            if violation_filter != "All":
                alerts_df = alerts_df[alerts_df["Violation"] == violation_filter]
            
            if risk_filter != "All":
                alerts_df = alerts_df[alerts_df["Risk"] == risk_filter]
            
            if status_filter:
                alerts_df = alerts_df[alerts_df["Status"].isin(status_filter)]
            
            st.dataframe(alerts_df, use_container_width=True, hide_index=True)

    # ======================== TAB 1: Live Camera Detection ========================
    with tab1:
        st.subheader("Live Camera Detection")

        run_camera = st.checkbox("Start Camera")

        FRAME_WINDOW = st.image([])

        if run_camera:
            cap = cv2.VideoCapture(0)

            global person_counter

            while run_camera:
                ret, frame = cap.read()

                if not ret:
                    st.error("Failed to access camera")
                    break

                # =========================
                # YOLO Tracking
                # =========================
                results = model.track(
                    frame,
                    persist=True,
                    tracker="bytetrack.yaml"
                )

                annotated_frame = results[0].plot()

                current_time = datetime.now()

                # =========================
                # Read detections
                # =========================
                boxes = results[0].boxes

                if boxes is not None:

                    classes = boxes.cls.cpu().numpy().astype(int)
                    confs = boxes.conf.cpu().numpy()
                    xyxy_list = boxes.xyxy.cpu().numpy()

                    

                    violation_classes = [
                        "NO-Hardhat",
                        "NO-Mask",
                        "NO-Safety Vest"
                    ]


                    for i, (cls_id, conf) in enumerate(zip(classes, confs)):

                        class_name = model.names[cls_id]

                        # فقط المخالفات
                        if class_name not in violation_classes:
                            continue

                        x1, y1, x2, y2 = xyxy_list[i]

                        center_x = int((x1 + x2) / 2)
                        center_y = int((y1 + y2) / 2)

                        matched_person = None

                        # محاولة مطابقة الشخص الحالي بشخص سابق
                        for person_id, data in tracked_people.items():

                            old_x = data["x"]
                            old_y = data["y"]
                            last_seen = data["last_seen"]

                            distance = (
                                ((center_x - old_x) ** 2) +
                                ((center_y - old_y) ** 2)
                            ) ** 0.5

                            if (
                                distance < PERSON_DISTANCE_THRESHOLD and
                                (current_time - last_seen).total_seconds() < PERSON_TIMEOUT_SECONDS
                            ):
                                matched_person = person_id
                                break

                        # شخص جديد
                        if matched_person is None:
                            person_counter += 1
                            matched_person = person_counter

                        tracked_people[matched_person] = {
                            "x": center_x,
                            "y": center_y,
                            "last_seen": current_time
                        }

                        person_number = matched_person

                        # لا تحفظ نفس الشخص إلا كل 30 ثانية
                        last_time = last_saved_time.get(person_number)

                        if (
                            last_time is None or
                            (current_time - last_time).total_seconds() >= 30
                        ):

                            last_saved_time[person_number] = current_time

                            Path("evidence").mkdir(exist_ok=True)

                            image_path = (
                                f"evidence/person_{person_number}_"
                                f"{current_time.strftime('%Y%m%d_%H%M%S')}.jpg"
                            )

                            is_saved = cv2.imwrite(image_path, annotated_frame)

                            if is_saved:

                                detection_id = db.add_detection(
                                    camera_name="Camera 1",
                                    source_file="Live Camera",
                                    source_type="video",
                                    total_persons=1,
                                    violations_count=1,
                                    confidence_avg=float(conf),
                                    zone_name="Person",
                                    image_path=image_path
                                )

                                db.add_alert(
                                    detection_id=detection_id,
                                    violation_type=class_name,
                                    risk_level="High",
                                    confidence=float(conf),
                                    camera_name="Camera 1",
                                    zone_name="Person",
                                    image_path=image_path
                                )

                                st.success("Saved Person")  

                            else:
                                st.error("Image not saved")



                # =========================
                # Display
                # =========================
                FRAME_WINDOW.image(
                    annotated_frame,
                    channels="BGR",
                    use_container_width=True
                )

            cap.release()

# ----------------------------------
# PAGE 2: SITE INSIGHTS
# ----------------------------------
    with tab3:
        st.title("📈 Site Insights")

        # Get data from database
        all_alerts = db.get_all_alerts()
        top_violations = db.get_top_violations()
        top_cameras = db.get_alerts_by_camera()

        # Violation Breakdown Treemap
        st.subheader("Violation Breakdown by Camera")

        if all_alerts:

            alerts_df = pd.DataFrame(all_alerts)

            if (
                len(alerts_df) > 0 and
                "violation_type" in alerts_df.columns and
                "camera_name" in alerts_df.columns
            ):

                treemap_df = (
                    alerts_df
                    .groupby(["camera_name", "violation_type"])
                    .size()
                    .reset_index(name="count")
                )

                fig = px.treemap(
                    treemap_df,
                    path=["camera_name", "violation_type"],
                    values="count",
                    color="count",
                    title="Violation Breakdown by Camera",
                    hover_data={
                        "camera_name": True,
                        "violation_type": True,
                        "count": True
                    }
                )

                fig.update_traces(
                    textinfo="label+value+percent parent"
                )

                fig.update_layout(
                    height=520,
                    margin=dict(t=50, l=10, r=10, b=10)
                )

                st.plotly_chart(fig, use_container_width=True)

            else:
                st.info("No violation data available")

        else:
            st.info("No violation data available")

        # Top Violations and Top Zones/Cameras
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Top 5 Violations")
            if top_violations:
                violation_df = pd.DataFrame(top_violations)
                fig_viol = px.bar(
                    violation_df,
                    x="count",
                    y="violation_type",
                    orientation="h",
                    labels={"count": "Count", "violation_type": "Violation Type"},
                    color="count",
                    color_continuous_scale="Reds"
                )
                st.plotly_chart(fig_viol, use_container_width=True)
            else:
                st.info("No violation data available")

        with col2:
            st.subheader("Top 5 Zones/Cameras by Violations")
            if top_cameras:
                camera_df = pd.DataFrame(top_cameras)
                fig_zones = px.bar(
                    camera_df,
                    x="count",
                    y="camera_name",
                    orientation="h",
                    labels={"count": "Violation Count", "camera_name": "Camera"},
                    color="count",
                    color_continuous_scale="Blues"
                )
                st.plotly_chart(fig_zones, use_container_width=True)
            else:
                st.info("No camera data available")

        st.divider()

        # Compliance Trend (7 days)
        st.subheader("7-Day Compliance Trend")
        compliance_df = get_compliance_trend()
        if len(compliance_df) > 0:
            fig_compliance = px.line(
                compliance_df,
                x="Day",
                y="Compliance %",
                markers=True,
                line_shape="spline",
                title="Compliance Rate Over 7 Days"
            )
            fig_compliance.update_yaxes(range=[0, 100])
            st.plotly_chart(fig_compliance, use_container_width=True)
        else:
            st.info("No compliance data available")

        st.divider()

        # Hourly Violations
        st.subheader("Hourly Violations Distribution")
        hourly_df = get_hourly_violations()
        if len(hourly_df) > 0 and hourly_df["Violations"].sum() > 0:
            fig_hourly = px.bar(
                hourly_df,
                x="Hour",
                y="Violations",
                title="Violations by Hour",
                color="Violations",
                color_continuous_scale="Oranges"
            )
            st.plotly_chart(fig_hourly, use_container_width=True)
        else:
            st.info("No hourly data available")

# ----------------------------------
# PAGE 3: REPORTS & EVIDENCE
# ----------------------------------
    with tab4:
        st.title("Reports & Evidence")



        # Generate Report Button
        col_btn1, col_btn2 = st.columns(2)

        # Get alerts data
        alerts_for_export = db.get_all_alerts()


        with col_btn1:
            if alerts_for_export:
                # Create dataframe from alerts
                export_df = pd.DataFrame(alerts_for_export)
                export_df = export_df[["created_at", "camera_name", "zone_name", "violation_type", "risk_level", "confidence", "status"]]
                export_df.columns = ["Timestamp", "Camera", "Zone", "Violation", "Risk", "Confidence", "Status"]

                csv = export_df.to_csv(index=False)
                st.download_button(
                    label="📥 Export as CSV",
                    data=csv,
                    file_name=f"safety_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("No data to export")

        with col_btn2:
            st.info("PDF export requires reportlab library")

        st.divider()

        # Summary Statistics
        st.subheader("Report Summary")
        col1, col2, col3, col4 = st.columns(4)

        all_alerts = db.get_all_alerts()
        open_alerts = len(db.get_alerts_by_status("Pending"))
        closed_alerts = len(db.get_alerts_by_status("Resolved"))

        # Average time to close (simulated)
        avg_time_to_close = 45 if closed_alerts > 0 else 0

        with col1:
            st.metric("📂 Open Alerts", open_alerts)
        with col2:
            st.metric("✓ Closed Alerts", closed_alerts)
        with col3:
            st.metric("⏱️ Avg Time to Close", f"{avg_time_to_close} min")
        with col4:
            st.metric("📊 Total Incidents", len(all_alerts))

        st.divider()

        # Evidence Gallery
        st.subheader("Evidence Gallery")

        # Get alerts with image paths
        alerts_with_images = [a for a in all_alerts if a.get("image_path")]

        if alerts_with_images:
            # Display first 3 alerts as evidence
            col_gallery1, col_gallery2, col_gallery3 = st.columns(3)

            for idx, alert in enumerate(alerts_with_images[:3]):
                with [col_gallery1, col_gallery2, col_gallery3][idx]:
                    st.info(f"Evidence {idx + 1}")
                    try:
                        if alert.get("image_path") and Path(alert["image_path"]).exists():
                            img = Image.open(alert["image_path"])
                            st.image(img, caption=f"Violation: {alert['violation_type']}")
                        else:
                            placeholder_img = Image.new('RGB', (300, 300), color=['lightblue', 'lightcoral', 'lightgreen'][idx])
                            st.image(placeholder_img, caption=f"Evidence - {alert['created_at']}")
                    except:
                        placeholder_img = Image.new('RGB', (300, 300), color=['lightblue', 'lightcoral', 'lightgreen'][idx])
                        st.image(placeholder_img, caption=f"Evidence - {alert['created_at']}")
        else:
            st.info("No evidence images available")
# ----------------------------------
# Main App Navigation
# ----------------------------------
st.sidebar.title("Safety Detection Dashboard")

# Data Processing Section
st.sidebar.divider()


page = st.sidebar.radio(
    "Select Page",
    ["Safety Detection Dashboard"]
)

# Route to selected page
if page == "Safety Detection Dashboard":
    page_live_monitoring()

st.sidebar.divider()

st.sidebar.button("clear database", on_click=db.clear_all_data)
