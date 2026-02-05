# RegAlert — MedTech Regulatory & Research Monitor

RegAlert is a professional data pipeline and dashboard designed to monitor global medical device regulations and academic research trends. It focuses on the intersection of Medical Devices (MDR/IVDR), AI-based software (SaMD), and clinical evidence.

## Features
- **Global Ingestion Pipeline**: Automated sourcing from FDA (510k clearances), EMA, MHRA, and PubMed.
- **Evidence Gap Analysis**: Visual comparison between regulatory approvals and academic publication volume.
- **Real-time Monitoring**: RSS and API-driven updates to track the latest safety alerts and guidance.
- **Advanced Categorization**: Smart filtering for AI, Cyber, and Digital Health topics.

## Project Structure
- `/ingestors`: Modular Python scripts for each data source (OOP-based).
- `runner.py`: The orchestrator that synchronizes all sources with a single command.
- `app.py`: Interactive Streamlit/Dash dashboard for data visualization.
- `data/`: SQLite master database containing 8,000+ records.

## How to Run
1. **Setup Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate