"""
Seed the database with sample events and an organizer account.
Run once:  python seed.py
"""
from datetime import datetime
from app.database import SessionLocal, Base, engine
from app import models, auth

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Bail out if already seeded
if db.query(models.User).filter_by(email="admin@jtickets.com").first():
    print("Database already seeded — skipping.")
    db.close()
    exit(0)

# ── Organizer account ────────────────────────────────────────────────────────
organizer = models.User(
    email="admin@jtickets.com",
    hashed_password=auth.hash_pw("jtickets2026"),
    role="organizer",
)
db.add(organizer)
db.commit()
db.refresh(organizer)

# ── Sample events ─────────────────────────────────────────────────────────────
EVENTS = [
    {
        "name": "Neon Dreamz Live 2026",
        "venue": "Starlight Arena, Mumbai",
        "event_date": datetime(2026, 8, 15, 20, 0),
        "total_tickets": 300,
        "category": "Music",
        "price": 2999,
        "image_url": "https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?auto=format&fit=crop&w=600&h=400&q=80",
    },
    {
        "name": "Studio Ghibli Night 🌿",
        "venue": "Moonlit Open Theatre, Bangalore",
        "event_date": datetime(2026, 7, 20, 19, 30),
        "total_tickets": 150,
        "category": "Movies",
        "price": 799,
        "image_url": "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=600&h=400&q=80",
    },
    {
        "name": "Sakura Pop Festival",
        "venue": "Riverside Grounds, Delhi",
        "event_date": datetime(2026, 9, 5, 16, 0),
        "total_tickets": 500,
        "category": "Music",
        "price": 1499,
        "image_url": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=600&h=400&q=80",
    },
    {
        "name": "The Great Backyard BBQ Bash 🍖",
        "venue": "Green Meadows, Pune",
        "event_date": datetime(2026, 7, 4, 12, 0),
        "total_tickets": 80,
        "category": "Social",
        "price": 499,
        "image_url": "https://images.unsplash.com/photo-1527529482837-4698179dc6ce?auto=format&fit=crop&w=600&h=400&q=80",
    },
    {
        "name": "Anime Movie Marathon 🍿",
        "venue": "CineWorld Premium, Hyderabad",
        "event_date": datetime(2026, 8, 1, 14, 0),
        "total_tickets": 120,
        "category": "Movies",
        "price": 999,
        "image_url": "https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=600&h=400&q=80",
    },
    {
        "name": "Jazz Under The Stars 🎷",
        "venue": "Rooftop at The Grand, Chennai",
        "event_date": datetime(2026, 8, 22, 19, 0),
        "total_tickets": 60,
        "category": "Music",
        "price": 1899,
        "image_url": "https://images.unsplash.com/photo-1506157786151-b8491531f063?auto=format&fit=crop&w=600&h=400&q=80",
    },
    {
        "name": "K-Pop Extravaganza 💜",
        "venue": "Dome Arena, Mumbai",
        "event_date": datetime(2026, 10, 12, 18, 0),
        "total_tickets": 1000,
        "category": "Music",
        "price": 3499,
        "image_url": "https://images.unsplash.com/photo-1429962714451-bb934ecdc4ec?auto=format&fit=crop&w=600&h=400&q=80",
    },
    {
        "name": "Horror Classics Night 🎃",
        "venue": "Retro Screen, Kolkata",
        "event_date": datetime(2026, 10, 31, 21, 0),
        "total_tickets": 100,
        "category": "Movies",
        "price": 599,
        "image_url": "https://images.unsplash.com/photo-1509347528160-9a9e33742cdb?auto=format&fit=crop&w=600&h=400&q=80",
    },
    {
        "name": "Acoustic Sessions: Indie Night 🎸",
        "venue": "The Loft Café, Goa",
        "event_date": datetime(2026, 7, 30, 20, 30),
        "total_tickets": 50,
        "category": "Music",
        "price": 699,
        "image_url": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=600&h=400&q=80",
    },
    {
        "name": "Rooftop Yoga & Chill 🧘",
        "venue": "Sky Garden, Bengaluru",
        "event_date": datetime(2026, 7, 13, 7, 0),
        "total_tickets": 30,
        "category": "Social",
        "price": 299,
        "image_url": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?auto=format&fit=crop&w=600&h=400&q=80",
    },
    {
        "name": "Bollywood Retro Night 🎶",
        "venue": "Heritage Hall, Jaipur",
        "event_date": datetime(2026, 8, 8, 19, 0),
        "total_tickets": 200,
        "category": "Music",
        "price": 1299,
        "image_url": "https://images.unsplash.com/photo-1484704849700-f032a568e944?auto=format&fit=crop&w=600&h=400&q=80",
    },
    {
        "name": "Indie Film Showcase 🎞️",
        "venue": "The Art House, Delhi",
        "event_date": datetime(2026, 9, 18, 18, 30),
        "total_tickets": 75,
        "category": "Movies",
        "price": 449,
        "image_url": "https://images.unsplash.com/photo-1507676184212-d03ab07a01bf?auto=format&fit=crop&w=600&h=400&q=80",
    },
]

for ev_data in EVENTS:
    event = models.Event(
        **ev_data,
        available_tickets=ev_data["total_tickets"],
        organizer_id=organizer.id,
    )
    db.add(event)

db.commit()
db.close()

print("Database seeded!")
print("   Organizer login: admin@jtickets.com / jtickets2026")
print(f"   {len(EVENTS)} events created")
