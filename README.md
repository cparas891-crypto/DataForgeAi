# DataForge AI

**DataForge AI** is a full-stack data profiling, quality analysis, cleaning, visualization, and reporting platform built with Python and FastAPI.

It provides a streamlined workflow for taking raw structured or semi-structured datasets through ingestion, profiling, cleaning, analysis, and export.

> **INGEST → PROFILE → CLEAN → ANALYZE → EXPORT**

---

## Overview

DataForge AI was built as a portfolio project to demonstrate practical data engineering, data quality, backend development, and analytics skills.

The platform allows users to upload datasets, automatically inspect their structure and quality, clean common data problems, visualize numerical data, maintain dataset history, and export cleaned results.

### Core Workflow

1. **Ingest** CSV, JSON, XLSX, or ZIP datasets
2. **Profile** structure and data quality
3. **Clean** duplicates, nulls, text, and column names
4. **Analyze** dataset and platform metrics
5. **Export** cleaned datasets and reports

---

## Features

### Multi-Format Data Ingestion

DataForge currently supports:

- CSV
- JSON
- JSON Lines / NDJSON
- Excel XLSX
- ZIP archives containing supported datasets

ZIP archives are inspected for supported dataset files before processing.

---

### Automated Data Profiling

Uploaded datasets are automatically analyzed for:

- Row count
- Column count
- Column data types
- Missing values
- Duplicate records
- Memory usage
- Descriptive statistics
- Numerical distributions
- Overall data-quality score

Users receive an immediate profile after uploading a dataset.

---

## Data Cleaning Studio

The **Cleaning Studio** provides a configurable transformation pipeline for previously uploaded datasets.

Current cleaning operations include:

- Remove duplicate rows
- Drop rows containing missing values
- Drop columns containing missing values
- Fill missing numeric values with:
  - Zero
  - Mean
  - Median
- Fill missing text values with:
  - Most common value
  - Custom replacement value
- Trim leading and trailing whitespace
- Standardize column names
- Reset row indexes

DataForge preserves the original dataset while generating a separate cleaned version.

### Before-and-After Quality Analysis

After the cleaning pipeline runs, DataForge compares:

- Original rows vs. cleaned rows
- Original missing values vs. cleaned missing values
- Original duplicates vs. cleaned duplicates
- Original quality score vs. cleaned quality score

The Cleaning Studio also displays previews of both versions.

---

## Dataset Export

Cleaned datasets can currently be exported as:

- CSV
- Excel XLSX

Generated files are stored separately from the original uploads.

---

## Dataset History

DataForge maintains persistent dataset metadata using SQLite.

The dataset catalog displays information including:

- Dataset name
- Upload date
- Rows
- Columns
- Missing values
- Duplicate rows
- Quality score
- Memory usage

This provides a simple history of datasets processed through the platform.

---

## Analytics Dashboard

The analytics dashboard provides cumulative platform metrics such as:

- Total datasets processed
- Average data-quality score
- Total rows processed
- Total memory analyzed

This provides a higher-level view of the datasets processed through DataForge.

---

## Visualizations

DataForge uses Plotly to generate interactive visualizations for numerical dataset columns.

The current profiling workflow automatically generates a distribution histogram when a usable numerical column is available.

---

## AI Analyst

DataForge includes an **AI Analyst** interface for guided data-analysis questions.

The current version provides structured recommendations around topics such as:

- Missing-value analysis
- Duplicate detection
- Data types
- Outlier analysis
- Data-quality validation
- Automated quality checks
- ETL considerations

> **Note:** The current AI Analyst is a guided analysis component and does not yet connect to an external LLM or AI API.

A future version is planned to make the analyst dataset-aware and capable of analyzing the selected dataset directly.

---

## PDF Reporting

DataForge can generate an executive PDF report for the latest processed dataset.

Reports include core profiling and quality metrics such as:

- Dataset name
- Rows
- Columns
- Missing values
- Duplicate rows
- Quality score
- Memory usage

---

## Technology Stack

### Backend

- Python
- FastAPI
- Uvicorn

### Data Processing

- Pandas
- OpenPyXL

### Data Storage

- SQLite

### Visualization

- Plotly

### Frontend

- Jinja2
- HTML
- CSS
- JavaScript

### Reporting

- ReportLab

### Packaging

- PyInstaller
- PowerShell

---

## Application Architecture

```text
                     ┌─────────────────────┐
                     │      Browser        │
                     └──────────┬──────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │      FastAPI        │
                     │     DataForge AI    │
                     └──────────┬──────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
          ▼                     ▼                     ▼
 ┌────────────────┐   ┌─────────────────┐   ┌─────────────────┐
 │ Data Ingestion │   │ Data Profiling  │   │ Cleaning Studio │
 │                │   │                 │   │                 │
 │ CSV            │   │ Missing Values  │   │ Deduplication   │
 │ JSON           │   │ Duplicates      │   │ Null Handling   │
 │ XLSX           │   │ Schema          │   │ Normalization   │
 │ ZIP            │   │ Quality Score   │   │ Transformation  │
 └───────┬────────┘   └────────┬────────┘   └────────┬────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               │
                               ▼
                     ┌─────────────────────┐
                     │       SQLite        │
                     │   Dataset History   │
                     └──────────┬──────────┘
                                │
              ┌─────────────────┼──────────────────┐
              │                 │                  │
              ▼                 ▼                  ▼
       ┌────────────┐    ┌────────────┐    ┌────────────┐
       │ Analytics  │    │ CSV / XLSX │    │ PDF Report │
       │ Dashboard  │    │   Export   │    │ Generation │
       └────────────┘    └────────────┘    └────────────┘
```

---

## Project Structure

```text
DataForgeAI/
│
├── app.py
├── launcher.py
├── DataForgeAI.spec
├── build.ps1
├── requirements.txt
├── README.md
├── .gitignore
│
├── templates/
│   ├── index.html
│   ├── upload.html
│   ├── profile.html
│   ├── datasets.html
│   ├── clean.html
│   ├── analytics.html
│   └── ai.html
│
├── sample_data/
│
├── screenshots/
│
├── uploads/
│   └── .gitkeep
│
├── cleaned/
│   └── .gitkeep
│
└── reports/
    └── .gitkeep
```

---

# Installation

## 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/DataForgeAI.git
```

Move into the project:

```bash
cd DataForgeAI
```

---

## 2. Create a Virtual Environment

### Windows PowerShell

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

---

## 3. Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

If you are installing the packages individually:

```powershell
python -m pip install fastapi uvicorn jinja2 python-multipart pandas plotly reportlab openpyxl pyinstaller
```

---

# Running DataForge

## Option 1: Run the Application Directly

```powershell
python app.py
```

Then open:

```text
http://127.0.0.1:8010
```

---

## Option 2: Use the DataForge Launcher

```powershell
python launcher.py
```

The launcher starts the local DataForge server and opens the application in the default browser.

---

## Application Pages

| Page | Route |
|---|---|
| Dashboard | `/` |
| Dataset Upload | `/upload` |
| Dataset History | `/datasets` |
| Cleaning Studio | `/clean` |
| Analytics | `/analytics` |
| AI Analyst | `/ai` |
| PDF Report | `/report` |
| Health Check | `/health` |

---

# Windows Executable

DataForge includes a PyInstaller build configuration for creating a standalone Windows distribution.

## Build

From the project directory:

```powershell
.\build.ps1
```

Or run PyInstaller directly:

```powershell
python -m PyInstaller --clean --noconfirm DataForgeAI.spec
```

After a successful build, the Windows application is generated under:

```text
dist/
└── DataForgeAI/
    └── DataForgeAI.exe
```

Run:

```powershell
.\dist\DataForgeAI\DataForgeAI.exe
```

The executable launches the local FastAPI application and opens DataForge in the default browser.

---

# Data Quality Scoring

DataForge calculates a simplified quality score based on two currently measured quality dimensions:

- Missing-value ratio
- Duplicate-record ratio

Missing values receive a larger weighting in the current scoring model.

The score is designed as a convenient application-level indicator rather than a universal data-quality standard.

Future versions may extend the score with:

- Schema violations
- Invalid data types
- Outliers
- Business-rule failures
- Referential-integrity violations
- Custom validation rules

---

# Screenshots

Create a `screenshots` directory and add your application screenshots.

Recommended screenshots:

### Dashboard

```markdown
![DataForge Dashboard](screenshots/dashboard.png)
```

### Dataset Profile

```markdown
![Dataset Profile](screenshots/profile.png)
```

### Cleaning Studio

```markdown
![Cleaning Studio](screenshots/cleaning-studio.png)
```

### Cleaning Results

```markdown
![Cleaning Results](screenshots/cleaning-results.png)
```

### Analytics

```markdown
![Analytics Dashboard](screenshots/analytics.png)
```

> Remove the code fences around the image Markdown after adding your actual screenshot files.

---

# Example Workflow

A typical DataForge workflow looks like:

```text
1. Upload raw dataset
        ↓
2. DataForge profiles dataset
        ↓
3. Review quality issues
        ↓
4. Open Cleaning Studio
        ↓
5. Configure transformations
        ↓
6. Run cleaning pipeline
        ↓
7. Compare before/after metrics
        ↓
8. Download cleaned dataset
        ↓
9. Review analytics or generate report
```

---

# Supported File Formats

| Format | Upload | Profile | Clean | Export |
|---|---:|---:|---:|---:|
| CSV | ✅ | ✅ | ✅ | ✅ |
| JSON | ✅ | ✅ | ✅ | CSV/XLSX |
| JSON Lines | ✅ | ✅ | ✅ | CSV/XLSX |
| XLSX | ✅ | ✅ | ✅ | ✅ |
| ZIP | ✅ | ✅ | ✅ | CSV/XLSX |

ZIP archives must contain at least one supported dataset.

---

# Security and File Handling

DataForge includes defensive file-handling logic for uploaded datasets and ZIP archives.

Runtime-generated files are excluded from the repository through `.gitignore`, including:

```text
uploads/
cleaned/
reports/
dataforge.db
```

Never commit sensitive datasets, API keys, credentials, passwords, or `.env` files to the repository.

---

# Roadmap

## Completed

- [x] Multi-format dataset ingestion
- [x] CSV support
- [x] JSON / JSON Lines support
- [x] XLSX support
- [x] ZIP ingestion
- [x] Automated dataset profiling
- [x] Missing-value analysis
- [x] Duplicate detection
- [x] Data-quality scoring
- [x] Dataset history
- [x] SQLite persistence
- [x] Plotly visualization
- [x] Analytics dashboard
- [x] PDF reporting
- [x] Cleaning Studio
- [x] Before-and-after quality comparison
- [x] CSV cleaned-data export
- [x] XLSX cleaned-data export
- [x] PyInstaller Windows build configuration

## Planned

- [ ] Dataset-specific detail pages
- [ ] Custom data validation rules
- [ ] Schema validation
- [ ] Dataset-aware AI Analyst
- [ ] Automated testing
- [ ] GitHub Actions CI/CD
- [ ] Docker containerization
- [ ] PostgreSQL support
- [ ] Cloud object storage
- [ ] Cloud deployment
- [ ] Authentication and user accounts

---

# Future Cloud Architecture

A future version of DataForge is planned around a cloud-ready architecture:

```text
Browser
   ↓
FastAPI Application
   ↓
┌───────────────┬─────────────────┐
│               │                 │
▼               ▼                 ▼
Database    Object Storage    Data Processing
│
▼
Analytics / Reporting
```

The goal is to preserve local development while allowing the same application architecture to evolve toward containerized and cloud-hosted deployment.

---

# Why I Built DataForge

DataForge was created as a hands-on portfolio project to demonstrate practical experience across several areas of modern data engineering and application development:

- Python application development
- Backend API development
- Structured and semi-structured data ingestion
- Data profiling
- Data cleaning
- Data-quality analysis
- Data transformation
- Persistent storage
- Interactive visualization
- Reporting
- Error handling
- Application packaging
- User-interface development

Rather than building a single-purpose script, the goal was to ssing workflow.

---

# Author

**Cameron Parascondola**

GitHub: [cparas891-crypto](https://github.com/cparas891-crypto)

---

## Project Status

**Active Development**

Current milestone:

**Phase 6: Data Cleaning Studio + Windows Packaging**

Next major milestone:

**Cloud-Ready Architecture, Testing, and Deployment**