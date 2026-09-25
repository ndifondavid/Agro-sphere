# AgroSphere

AgroSphere is a Flask-based agricultural platform for farmers to manage farms, track crops, and review plant health data. The current build includes farm and crop management, crop scans, dashboard reporting, a marketplace flow, and role-based access for farmer and buyer users.

## What works now

- Farmer dashboard and farm overview screens
- Farm creation, farm management, crop creation, crop editing, and crop deletion tied to the logged-in farmer
- Image upload validation for farm and crop photos, with safe local storage under the app upload folder
- Disease-scan workflow with historical scan results and treatment guidance views
- Marketplace browsing and listing creation for farmers; buyer reservation flow for available listings
- Community posts and replies scoped to the listing or community thread context
- Settings page for profile updates and notification preferences stored under the user record
- Basic README and local setup guidance for running the project in development

## What is still planned or external

The app does not yet include production-ready integrations for the following services and features:

- Live weather alerts and advisories
- Email, SMS, WhatsApp, and push notification delivery
- Support ticket backend or live helpdesk system
- Video tutorial hosting and playback content
- Model-backed disease detection pipeline that is trained and deployed externally
- Payment processing or billing integration

These controls are present as placeholders or planned features and should be treated as unavailable unless an external service is explicitly connected.

## Current architecture and model integration point

The trained disease model is expected to plug into the AI detection flow at the application boundary in `app/ai/disease_detector.py` and the related configuration under `config.py`. The current app includes a fallback response so local development can continue even when the model file is absent, but it is not a substitute for the real trained model.

## Local setup

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

The app runs locally at:

```text
http://127.0.0.1:5000
```

## Environment notes

- The default database is SQLite for local development.
- The app uses `instance/agrosphere.db` unless a different `DATABASE_URL` is configured.
- Production variables such as `SECRET_KEY` and `DATABASE_URL` must be set before deployment.
- Uploads are stored locally in the app upload folder and must be protected from untrusted public access.
- Do not treat the current demo model or notification placeholders as ready for production use.

## Testing

Run the relevant tests with:

```bash
python -m pytest
```

## Future work

- Connect the trained disease model behind the current detection service abstraction
- Replace placeholder notification toggles with real delivery providers
- Connect support and help center workflows to a real ticketing backend
- Add documentation for deployed configuration, model versioning, and operational monitoring

## License

This project does not yet include a production license file. Add one before public distribution or deployment.
