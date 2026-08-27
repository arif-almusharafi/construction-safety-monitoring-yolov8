# AI-Powered Construction Site Safety Monitoring System

A graduation project that uses **YOLOv8** and a **Streamlit dashboard** to detect personal protective equipment (PPE) violations on construction sites, store incidents, and present safety analytics.

> This repository is a cleaned portfolio version of a collaborative graduation project. The application code and training notebooks are preserved without changing their logic. See the [original team repository](https://github.com/moathking000000009/Final-projct.ANT) for the complete project history and team contributions.

## Problem

Manual construction-site monitoring can miss safety violations and does not scale well across multiple cameras and work zones. This system demonstrates how computer vision can help identify PPE violations and turn detections into trackable alerts and safety insights.

## Key Features

- Real-time detection using YOLOv8
- PPE violation detection for missing hardhats, masks, and safety vests
- Live webcam monitoring and person tracking
- SQLite storage for alerts, detections, camera status, and media records
- Evidence capture for detected violations
- Dashboard KPIs and interactive Plotly charts
- Compliance trends and hourly violation analysis
- CSV report export
- Model comparison and training notebooks

## Detection Classes

The model is designed to detect:

- Person
- Hardhat / NO-Hardhat
- Mask / NO-Mask
- Safety Vest / NO-Safety Vest
- Safety Cone
- Machinery
- Vehicle

## Model Results

The repository includes a comparison of three YOLOv8 variants:

| Model | mAP50 | mAP50-95 | Precision | Recall |
|---|---:|---:|---:|---:|
| YOLOv8m | 0.875 | 0.622 | 0.913 | 0.807 |
| YOLOv8s | 0.856 | 0.580 | 0.954 | 0.769 |
| YOLOv8n | 0.799 | 0.499 | 0.881 | 0.731 |

These values are taken from `results/model_comparison.csv`.

## Tech Stack

- Python
- Ultralytics YOLOv8
- Streamlit
- OpenCV
- SQLite
- Pandas and NumPy
- Plotly
- Pillow
- Jupyter Notebook

## Repository Structure

```text
.
├── app/
│   ├── .streamlit/
│   │   └── config.toml
│   ├── database.py
│   ├── media_library.py
│   ├── style.css
│   └── web_app.py
├── notebooks/
│   ├── yolo-training-evaluation.ipynb
│   ├── yolo-deployment-safety-system.ipynb
│   └── yolo-supplementary-analysis.ipynb
├── results/
│   └── model_comparison.csv
├── .gitignore
├── requirements.txt
└── README.md
```

Generated files such as `safety_database.db`, `__pycache__`, uploaded media, evidence images, and trained weights are intentionally excluded.

## Model Weights

The dashboard loads the trained model from `best.pt`.

Because trained weights are large generated artifacts, they are not committed directly to this portfolio repository. Download `best.pt` from the [original project](https://github.com/moathking000000009/Final-projct.ANT/blob/main/FrontEnd/best.pt) and place it inside the `app/` directory:

```text
app/best.pt
```

## Installation

Clone the repository and enter the project directory:

```bash
git clone https://github.com/arif-almusharafi/construction-safety-monitoring-yolov8.git
cd construction-safety-monitoring-yolov8
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Add `best.pt` to the `app/` directory, then start the dashboard from that directory so the existing relative model path remains unchanged:

```bash
cd app
streamlit run web_app.py
```

The SQLite database is created automatically on the first run.

## System Workflow

1. A camera frame is captured.
2. YOLOv8 detects people and safety equipment.
3. The application identifies PPE violations.
4. Evidence and incident information are stored.
5. The dashboard displays alerts, KPIs, trends, and reports.

## My Contributions

My work focused on the software system surrounding the trained model:

- Developed the Streamlit dashboard and user interface
- Integrated live camera detection
- Implemented alert and evidence handling
- Built the SQLite database layer
- Connected detections with dashboard analytics and reporting
- Improved real-time processing to keep the application responsive

## Project Context

This was developed as a **collaborative graduation project at the University of Ha'il**. The source repository contains the full team history. This cleaned repository is maintained by **Arif Al-Musharafi** to present his implementation contributions and the completed system.

## Author

**Arif Al-Musharafi**  
Artificial Intelligence graduate interested in AI engineering, computer vision, data science, and software development.

[LinkedIn](https://www.linkedin.com/in/arif-almishrafi-45612b2a7) · [GitHub](https://github.com/arif-almusharafi)
