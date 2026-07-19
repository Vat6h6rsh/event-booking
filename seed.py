"""Seed: organizer + 12 events + ticket tiers."""
from datetime import datetime
from app.database import SessionLocal, Base, engine
from app import models, auth

Base.metadata.create_all(bind=engine)
db = SessionLocal()

if db.query(models.User).filter_by(email="admin@jtickets.com").first():
    print("Already seeded.")
    db.close(); exit(0)

org = models.User(email="admin@jtickets.com",
                  hashed_password=auth.hash_pw("jtickets2026"),
                  role="organizer", full_name="Jtickets Admin")
db.add(org); db.commit(); db.refresh(org)

EVENTS = [
    dict(name="Neon Dreamz Live 2026", venue="Starlight Arena, Mumbai",
         event_date=datetime(2026,8,15,20,0), total_tickets=300, category="Music",
         price=2999, age_rating="UA", event_type="Music",
         image_url="https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?auto=format&fit=crop&w=600&h=400&q=80",
         tiers=[dict(name="General",price=2999,total_seats=200,color="#A78BFA",position=0),
                dict(name="VIP",price=5999,total_seats=80,color="#FF6B9D",position=1,benefits="Front row,Backstage pass"),
                dict(name="Backstage",price=12999,total_seats=20,color="#FCD34D",position=2,benefits="Meet & greet,Signed merch")]),
    dict(name="Studio Ghibli Night", venue="Moonlit Open Theatre, Bangalore",
         event_date=datetime(2026,7,20,19,30), total_tickets=150, category="Movies",
         price=799, age_rating="U", event_type="Movie", has_seat_selection=True,
         image_url="https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=600&h=400&q=80",
         tiers=[dict(name="Regular",price=799,total_seats=100,color="#7DD3FC",position=0),
                dict(name="Premium",price=1299,total_seats=50,color="#A78BFA",position=1,benefits="Bean bag seating,Popcorn combo")]),
    dict(name="Sakura Pop Festival", venue="Riverside Grounds, Delhi",
         event_date=datetime(2026,9,5,16,0), total_tickets=500, category="Music",
         price=1499, age_rating="U", event_type="Festival",
         image_url="https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=600&h=400&q=80",
         tiers=[dict(name="General",price=1499,total_seats=350,color="#6EE7B7",position=0),
                dict(name="Festival Pass",price=2999,total_seats=150,color="#FF6B9D",position=1,benefits="All-day access,Festival kit")]),
    dict(name="The Great Backyard BBQ Bash", venue="Green Meadows, Pune",
         event_date=datetime(2026,7,4,12,0), total_tickets=80, category="Social",
         price=499, age_rating="U", event_type="Social",
         image_url="https://images.unsplash.com/photo-1527529482837-4698179dc6ce?auto=format&fit=crop&w=600&h=400&q=80",
         tiers=[dict(name="Entry",price=499,total_seats=60,color="#FDBA74",position=0),
                dict(name="All-inclusive",price=999,total_seats=20,color="#FF6B9D",position=1,benefits="Unlimited food & drinks")]),
    dict(name="Anime Movie Marathon", venue="CineWorld Premium, Hyderabad",
         event_date=datetime(2026,8,1,14,0), total_tickets=120, category="Movies",
         price=999, age_rating="UA", event_type="Movie", has_seat_selection=True,
         image_url="https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=600&h=400&q=80",
         tiers=[dict(name="Standard",price=999,total_seats=80,color="#7DD3FC",position=0),
                dict(name="IMAX",price=1599,total_seats=40,color="#A78BFA",position=1,benefits="IMAX screen,Recliner seats")]),
    dict(name="Jazz Under The Stars", venue="Rooftop at The Grand, Chennai",
         event_date=datetime(2026,8,22,19,0), total_tickets=60, category="Music",
         price=1899, age_rating="U", event_type="Music",
         image_url="https://images.unsplash.com/photo-1506157786151-b8491531f063?auto=format&fit=crop&w=600&h=400&q=80",
         tiers=[dict(name="Standard",price=1899,total_seats=40,color="#A78BFA",position=0),
                dict(name="Table for 2",price=3999,total_seats=20,color="#FCD34D",position=1,benefits="Reserved table,Dinner included")]),
    dict(name="K-Pop Extravaganza", venue="Dome Arena, Mumbai",
         event_date=datetime(2026,10,12,18,0), total_tickets=1000, category="Music",
         price=3499, age_rating="U", event_type="Music",
         image_url="https://images.unsplash.com/photo-1429962714451-bb934ecdc4ec?auto=format&fit=crop&w=600&h=400&q=80",
         tiers=[dict(name="Bronze",price=3499,total_seats=600,color="#FDBA74",position=0),
                dict(name="Silver",price=5999,total_seats=300,color="#9CA3AF",position=1,benefits="Seated section"),
                dict(name="Gold VIP",price=12999,total_seats=100,color="#FCD34D",position=2,benefits="Front floor,VIP lounge,Merch bag")]),
    dict(name="Horror Classics Night", venue="Retro Screen, Kolkata",
         event_date=datetime(2026,10,31,21,0), total_tickets=100, category="Movies",
         price=599, age_rating="18+", event_type="Movie",
         image_url="https://images.unsplash.com/photo-1509347528160-9a9e33742cdb?auto=format&fit=crop&w=600&h=400&q=80",
         tiers=[dict(name="Standard",price=599,total_seats=100,color="#374151",position=0)]),
    dict(name="Acoustic Sessions: Indie Night", venue="The Loft Cafe, Goa",
         event_date=datetime(2026,7,30,20,30), total_tickets=50, category="Music",
         price=699, age_rating="U", event_type="Music",
         image_url="https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=600&h=400&q=80",
         tiers=[dict(name="General",price=699,total_seats=35,color="#6EE7B7",position=0),
                dict(name="Premium",price=1299,total_seats=15,color="#FF6B9D",position=1,benefits="Front row,1 drink included")]),
    dict(name="Rooftop Yoga & Chill", venue="Sky Garden, Bengaluru",
         event_date=datetime(2026,7,13,7,0), total_tickets=30, category="Social",
         price=299, age_rating="U", event_type="Social",
         image_url="https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?auto=format&fit=crop&w=600&h=400&q=80",
         tiers=[dict(name="Drop-in",price=299,total_seats=30,color="#6EE7B7",position=0)]),
    dict(name="Bollywood Retro Night", venue="Heritage Hall, Jaipur",
         event_date=datetime(2026,8,8,19,0), total_tickets=200, category="Music",
         price=1299, age_rating="U", event_type="Music",
         image_url="https://images.unsplash.com/photo-1484704849700-f032a568e944?auto=format&fit=crop&w=600&h=400&q=80",
         tiers=[dict(name="General",price=1299,total_seats=150,color="#FDBA74",position=0),
                dict(name="Royal",price=2499,total_seats=50,color="#FCD34D",position=1,benefits="Royal box,Dinner buffet")]),
    dict(name="Indie Film Showcase", venue="The Art House, Delhi",
         event_date=datetime(2026,9,18,18,30), total_tickets=75, category="Movies",
         price=449, age_rating="A", event_type="Movie",
         image_url="https://images.unsplash.com/photo-1507676184212-d03ab07a01bf?auto=format&fit=crop&w=600&h=400&q=80",
         tiers=[dict(name="Standard",price=449,total_seats=75,color="#7DD3FC",position=0)]),
]

for data in EVENTS:
    tiers_data = data.pop("tiers", [])
    event = models.Event(**data, available_tickets=data["total_tickets"], organizer_id=org.id)
    db.add(event); db.flush()
    for t in tiers_data:
        db.add(models.TicketTier(**t, event_id=event.id, available_seats=t["total_seats"]))

db.commit(); db.close()
print(f"Seeded: {len(EVENTS)} events with tiers")
print("Organizer: admin@jtickets.com / jtickets2026")
