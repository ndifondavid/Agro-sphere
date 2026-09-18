# AgroSphere

AgroSphere is a Flask-based agricultural platform for farmers to manage farms, track crops, and detect plant disease using image-based scanning. It also supports farmer dashboards, product marketplace flows, and role-based access for farmer, buyer, and admin users.

## Overview

AgroSphere helps farmers:
- create and manage farms
- add crops to each farm
- upload leaf images for disease diagnosis
- review recommendations and scan history
- monitor farm health through a dashboard

The platform also includes marketplace and communication features for buyers and administrators.

## Key Features

- Farmer dashboard and farm management UI
- Farm-first scan flow to ensure scans happen only with valid farm and crop data
- AI disease detection with fallback behavior when a model file is unavailable
- Scan history and treatment guidance
- Role-based authentication and access control
- Marketplace and reservation flows
- Messaging and admin support structure

## Tech Stack

- Python 3
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-Migrate
- SQLite
- Jinja2 templates
- HTML, CSS, JavaScript

## Project Structure

```text
Agrosphere/
├── app/
│   ├── ai/
│   ├── models/
│   ├── routes/
│   ├── static/
│   ├── templates/
│   ├── utils/
│   ├── __init__.py
│   └── extensions.py
├── ai_model/
├── database/
├── docs/
├── instance/
├── migrations/
├── tests/
├── config.py
├── run.py
├── README.md
├── requirements.txt
└── .venv/
```

## Local Setup

1. Clone the repository.
2. Open a terminal in the project root.
3. Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Run the app:

```bash
python run.py
```

The app should run locally at:

```text
http://127.0.0.1:5000
```

## App Flow

Typical farmer flow:
1. Log in as a farmer
2. Create a farm
3. Add at least one crop
4. Upload a leaf image for disease scanning
5. View diagnosis, recommendation, and treatment details
6. Save scan history

## Environment Notes

- The default database is SQLite.
- AI model paths and upload configuration are managed in `config.py`.
- The disease detector includes a fallback result to keep the app usable even when the model file is absent.

## Testing

Run the relevant tests with:

```bash
python -m pytest
```

## License

This project currently does not include a formal license file. Add one before public distribution or production deployment.
