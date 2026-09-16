from datetime import date, datetime, timedelta
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.extensions import db
from app.models import Crop, Farm, Listing, Message, Reservation, Scan, User

RECORD_COUNT = 20


def seed_database():
    app = create_app()
    with app.app_context():
        tables = (User, Farm, Crop, Scan, Listing, Reservation, Message)
        existing = {model.__tablename__: model.query.count() for model in tables}
        if any(existing.values()):
            raise RuntimeError(
                f"Database is not empty: {existing}. Seed data was not added."
            )

        users = []
        for index in range(1, RECORD_COUNT + 1):
            if index <= 10:
                role = "farmer"
            elif index < RECORD_COUNT:
                role = "buyer"
            else:
                role = "admin"
            user = User(
                name=f"AgroSphere User {index}",
                email=f"user{index}@agrosphere.test",
                role=role,
            )
            user.set_password("Password123!")
            users.append(user)
        db.session.add_all(users)
        db.session.flush()

        farms = [
            Farm(
                owner_id=users[(index - 1) % 10].id,
                name=f"AgroSphere Farm {index}",
                location=f"District {((index - 1) % 5) + 1}",
                image_path=f"images/uploads/farms/farm_{index}.jpg",
            )
            for index in range(1, RECORD_COUNT + 1)
        ]
        db.session.add_all(farms)
        db.session.flush()

        crop_types = (
            "Tomato", "Maize", "Cassava", "Beans", "Potato",
            "Pepper", "Cabbage", "Onion", "Carrot", "Plantain",
        )
        crops = [
            Crop(
                farm_id=farms[index - 1].id,
                crop_type=crop_types[(index - 1) % len(crop_types)],
                planting_date=date(2026, 1, 1) + timedelta(days=index * 7),
                image_path=f"images/uploads/crops/crop_{index}.jpg",
            )
            for index in range(1, RECORD_COUNT + 1)
        ]
        db.session.add_all(crops)
        db.session.flush()

        diseases = ("Healthy", "Leaf Blight", "Powdery Mildew", "Unknown")
        scans = [
            Scan(
                crop_id=crops[index - 1].id,
                image_path=f"images/uploads/scans/scan_{index}.jpg",
                predicted_disease=diseases[(index - 1) % len(diseases)],
                confidence_score=round(0.62 + ((index - 1) % 8) * 0.04, 2),
                recommendation="Continue routine monitoring."
                if index % 4 == 1
                else "Inspect affected leaves and follow the recommended treatment.",
                timestamp=datetime(2026, 3, 1) + timedelta(days=index),
            )
            for index in range(1, RECORD_COUNT + 1)
        ]
        db.session.add_all(scans)
        db.session.flush()

        listings = [
            Listing(
                farmer_id=users[(index - 1) % 10].id,
                crop_type=crops[index - 1].crop_type,
                harvest_date=date(2026, 6, 1) + timedelta(days=index * 2),
                quantity=float(50 + index * 5),
                price=float(10 + index),
                availability_status="available" if index <= 16 else "reserved",
                image_path=f"images/uploads/listings/listing_{index}.jpg",
            )
            for index in range(1, RECORD_COUNT + 1)
        ]
        db.session.add_all(listings)
        db.session.flush()

        reservations = [
            Reservation(
                listing_id=listings[index - 1].id,
                buyer_id=users[10 + ((index - 1) % 9)].id,
                status="requested" if index <= 10 else "confirmed",
                timestamp=datetime(2026, 4, 1) + timedelta(days=index),
            )
            for index in range(1, RECORD_COUNT + 1)
        ]
        db.session.add_all(reservations)
        db.session.flush()

        messages = [
            Message(
                sender_id=users[10 + ((index - 1) % 9)].id,
                receiver_id=users[(index - 1) % 10].id,
                listing_id=listings[index - 1].id,
                content=f"Hello, I am interested in listing {index}.",
                timestamp=datetime(2026, 5, 1) + timedelta(days=index),
            )
            for index in range(1, RECORD_COUNT + 1)
        ]
        db.session.add_all(messages)

        db.session.commit()
        print(f"Seeded {RECORD_COUNT} records into each database table.")


if __name__ == "__main__":
    seed_database()
