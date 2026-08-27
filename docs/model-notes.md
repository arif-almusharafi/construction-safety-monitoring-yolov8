# 🦺 Construction Site Safety Monitoring System (YOLOv8)

## 📌 Project Overview

This project implements an AI-based construction site safety monitoring system using YOLOv8.

The system detects:

- 👷 Person
- 🪖 Hardhat / NO-Hardhat
- 😷 Mask / NO-Mask
- 🦺 Safety Vest / NO-Safety Vest

It does not stop at object detection.  
It includes:

- Rule-based safety engine
- Compliance rate calculation
- Risk scoring system (0–100)
- Persistent violation alerts
- CSV logging for dashboard integration
- ONNX export for deployment

This project was developed for Graduation Project 102.

---

# 📂 Kaggle Notebooks

The project is divided into two main notebooks:

### 🔹 Sections 1–5 (Training & Evaluation)
https://www.kaggle.com/code/trmoath/yolo8-section-1-5

### 🔹 Sections 6–10 (Deployment & Safety System)
https://www.kaggle.com/code/trmoath/yolo8-section-6-10

---

# 🏗 Project Structure

---

## ✅ Sections 1–5 — Model Development

These sections focus on training and evaluation.

### Section 1 — Dataset Setup
- Load construction safety dataset
- Organize images and labels

### Section 2 — Data Exploration
- Visualize samples
- Check class balance

### Section 3 — Model Training
- Train YOLOv8 variants (n, s, m)
- Tune parameters

### Section 4 — Evaluation
- mAP
- Precision
- Recall
- Performance comparison

### Section 5 — Best Model Selection
- Select best performing model
- Save `best.pt`

Output:
- Final trained model (`best.pt`)

---

## 🔍 Section 6 — Model Diagnostics

Purpose:
Analyze safety-critical detection errors.

Includes:
- False positive analysis
- Missed violation analysis
- Visual inspection of difficult cases

This ensures reliability in safety monitoring.

---

## 🎥 Section 7 — Video Deployment Demo

Purpose:
Simulate real-world monitoring.

Includes:
- Inference on SAFE video
- Inference on VIOLATION video
- Annotated video export
- FPS / latency estimation

Demonstrates real-time capability.

---

## ⚙ Section 8 — Rule Engine (Safety Intelligence)

Purpose:
Convert raw detections into safety decisions.

Includes:
- Frame-based violation analysis
- Compliance rate calculation
- Risk score computation
- Persistent violation detection
- Alert triggering system

This transforms detection into an intelligent monitoring system.

---

## 📊 Section 9 — Logging & Reporting

Purpose:
Create structured outputs for dashboards.

Includes:
- Video safety summary (CSV)
- Incident report with risk level
- Dashboard KPI metrics
- Executive summary text

Outputs are dashboard-ready.

---

## 🚀 Section 10 — Deployment & Packaging

Purpose:
Prepare system for production use.

Includes:
- Export model to ONNX format
- Copy logs and demo outputs
- Create FINAL_PACKAGE folder
- Generate deployment README

Final package contains:
- best.pt
- best.onnx
- CSV logs
- Annotated demo videos

---

# 🧠 System Workflow

1. Input (Image / Video)
2. YOLOv8 Detection
3. Rule Engine Processing
4. Risk Score Calculation
5. Alert Triggering
6. CSV Logging
7. Dashboard Integration

---

# 🖥 How To Run

### Option 1 — Kaggle
1. Open Sections 1–5 notebook
2. Train model
3. Open Sections 6–10 notebook
4. Run deployment pipeline

### Option 2 — Windows + AMD GPU
Use exported `best.onnx` with ONNX Runtime (DirectML).

---

# 📈 Key Features

✔ Real-time PPE detection  
✔ Intelligent safety rule engine  
✔ Persistent violation monitoring  
✔ Risk scoring system  
✔ Dashboard-ready reporting  
✔ Deployment-ready export  

---

# 👥 Team Members

(Add your team names here)

---

# 🎯 Final Result

This project is not just an object detection model.

It is a complete AI-powered construction site safety monitoring pipeline ready for real-world deployment.

---

# 📌 Conclusion

The system demonstrates how deep learning combined with rule-based logic can create an intelligent, automated safety monitoring solution for construction environments.