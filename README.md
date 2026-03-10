# RegAlert — MedTech Regulatory & Research Monitor

![Main Dashboard Performance](assets/dashboard_main.png)

RegAlert is an enterprise-grade data pipeline and interactive analytics dashboard designed to monitor global medical device regulations (MDR/IVDR) and academic research trends (PubMed) in real-time. It specifically focuses on high-growth sectors: **AI/ML as a Medical Device (SaMD), Cybersecurity, and Digital Health**.

---

##  Tech Stack & Architecture
## Tech Stack & Architecture

* **Backend:** Python 3.x
* **Data Orchestration:** Modular OOP-based ingestors for automated ETL from FDA, EMA, MHRA, and PubMed.
* **Database:** SQLite master database managing over 8,000+ normalized records.
* **Analytics & Frontend:** Plotly Dash for high-performance interactive visualizations and Dash Bootstrap Components for responsive UI.
* **Deployment:** Production-ready WSGI configuration (Gunicorn) deployed on Render.

---

<<<<<<< HEAD
##  Key Technical Features
=======
## Key Technical Features
>>>>>>> 29ed7b0404223d228e5e90c9bafb1df9d52515a7

### 1. Automated ETL Pipeline
* **Modular Ingestors:** Each data source has a dedicated class-based ingestor to handle specific API/RSS structures.
* **Smart Deduplication:** Custom logic to prevent record duplication during frequent updates.
* **Advanced Categorization:** Regex-based engine that maps raw text to regulatory domains (e.g., 510k, PMA, AI Act).
* **Database Layer:** Utilizes Python DB-API with SQLite for robust data persistence and SQL-based filtering.

### 2. Advanced Analytics Dashboard
* **Evidence Gap Analysis:** A dual-axis time-series chart comparing the volume of scientific publications vs. regulatory approvals.
![Evidence Gap Analysis](assets/evidence_gap_analysis.png)

* **Recall Radar:** A polar (spider) chart analyzing safety incidents across categories like Software, Sterility, and Battery issues.
![Recall Radar](assets/recall_radar_charts.png)

* **Trend Exploration:** Real-time calculation of data influx and domain concentration.
![Domain Trends](assets/domain_trends.png)

### 3. Professional UX/UI
* **Responsive Grid:** Custom CSS Flexbox implementation to ensure seamless usability on both mobile and desktop.
* **Records Explorer:** Interactive data table with advanced filtering, sorting, and drill-down capabilities.
![Records Explorer](assets/records_explorer.png)

---
<<<<<<< HEAD
##  Installation & Setup
=======
## Installation & Setup
>>>>>>> 29ed7b0404223d228e5e90c9bafb1df9d52515a7

### 1. Clone the repository:

git clone [https://github.com/adrianIT96/regalert-dashboard.git](https://github.com/adrianIT96/regalert-dashboard.git)

cd regalert-dashboard

### 2. Setup Virtual Environment:

python -m venv venv

source venv/bin/activate  # On Windows: venv\Scripts\activate

### 3. Install Dependencies:

pip install -r requirements.txt

### 4. Run the Application:

python app.py

<<<<<<< HEAD
##  Project Structure
=======
## Project Structure
>>>>>>> 29ed7b0404223d228e5e90c9bafb1df9d52515a7

```text
├── /ingestors   # OOP scripts for data sourcing (FDA, PubMed, etc.)
├── runner.py    # Main orchestrator for data synchronization
├── app.py       # Interactive Dash/Streamlit application
├── data/        # SQLite database & data storage
└── assets/      # Custom CSS & static images```

