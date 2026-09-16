# AgroSphere

AgroSphere is a digital agriculture platform designed to support farmers, buyers, and administrators with tools for farm management, crop health monitoring, trade, and communication. The system combines a web application, AI-powered crop disease detection, and marketplace features in a single platform.

## Project Overview

AgroSphere helps farmers manage their farms and crops, scan plant leaves for disease detection, review historical scan results, and connect with buyers through a marketplace. Buyers can browse available produce, reserve listings, and message farmers. Administrators can manage users, listings, and system content.

## Key Features

- User authentication and role-based access
- Farm and crop management
- AI-based crop disease detection using uploaded leaf images
- Scan history and recommendations
- Community or dashboard interactions
- Product listings and buying/reservation flow
- Messaging between buyers and farmers
- Admin moderation and management tools

## Tech Stack

- Python
- Flask
- SQLite
- HTML / CSS / JavaScript
- Bootstrap
- Machine learning model integration for disease detection

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
├── README.md
└── requirements.txt (if added later)
```

## Main Modules

- Authentication and user management
- Farm and crop dashboards
- Disease detection scanning
- Marketplace listing and reservation flow
- Messaging system
- Admin panel

## Setup Instructions

1. Open a terminal in the project folder.
2. Create and activate a virtual environment:

```bash
python -m venv venv
```

On Windows:

```bash
venv\Scripts\activate
```

On macOS/Linux:

```bash
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

If a `requirements.txt` file is not present yet, install the required packages manually such as:

```bash
pip install flask
```

4. Run the app:

```bash
python run.py
```

If the project uses Flask app factory configuration, the app may be started with:

```bash
flask run
```

## Environment Notes

- The app currently uses SQLite for the database layer.
- AI model files and inference logic are stored in the `ai_model` and `app/ai` areas.
- Static assets and templates are organized under the `app/static` and `app/templates` folders.

## Purpose

This project is intended as a practical agricultural technology platform for smart farm monitoring, crop disease intervention, and digital market access. It is structured to support academic, demo, and development use cases.

## License

This project does not yet include a formal license file. Add one before publication or distribution.
