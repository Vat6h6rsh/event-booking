"""Seed: organizer + ~50 events across India (incl. 15 in Bihar & Jharkhand) + ticket tiers.

Images are local, pre-downloaded, heavily-compressed Unsplash photos
(frontend/public/images/events/*.jpg) — never hotlinked — so the site stays fast.
"""
from datetime import datetime, timedelta
from sqlalchemy import delete, select, update
from app.database import SessionLocal, ensure_schema
from app import models, auth

ensure_schema()  # also upgrades a DB created by an older version (seed runs before the API)
db = SessionLocal()

IMG = "/images/events/{}.jpg"


def tier(name, price, seats, color, pos, benefits=None):
    d = dict(name=name, price=price, total_seats=seats, color=color, position=pos)
    if benefits:
        d["benefits"] = benefits
    return d


EVENTS = [
    # ── Original flagship events (kept, now served from local compressed images) ──
    dict(name="Neon Dreamz Live 2026", venue="Starlight Arena, Mumbai",
         event_date=datetime(2026,8,15,20,0), total_tickets=300, category="Music",
         price=2999, age_rating="UA", event_type="Music", image_url=IMG.format("music-01"),
         tags="live music,nightlife", description="Mumbai's biggest indie-electronic crossover night, headlined by three touring acts on one stage.",
         tiers=[tier("General",2999,200,"#A78BFA",0),
                tier("VIP",5999,80,"#FF6B9D",1,"Front row,Backstage pass"),
                tier("Backstage",12999,20,"#FCD34D",2,"Meet & greet,Signed merch")]),
    dict(name="Studio Ghibli Night", venue="Moonlit Open Theatre, Bangalore",
         event_date=datetime(2026,7,20,19,30), total_tickets=150, category="Movies",
         price=799, age_rating="U", event_type="Movie", has_seat_selection=True, image_url=IMG.format("movies-01"),
         tags="anime,open-air", description="A double-feature open-air screening of Studio Ghibli classics under the stars.",
         tiers=[tier("Regular",799,100,"#7DD3FC",0),
                tier("Premium",1299,50,"#A78BFA",1,"Bean bag seating,Popcorn combo")]),
    dict(name="Sakura Pop Festival", venue="Riverside Grounds, Delhi",
         event_date=datetime(2026,9,5,16,0), total_tickets=500, category="Festival",
         price=1499, age_rating="U", event_type="Festival", image_url=IMG.format("music-06"),
         tags="j-pop,festival", description="A day-long J-pop and K-pop festival with live sets, cosplay contests and food stalls.",
         tiers=[tier("General",1499,350,"#6EE7B7",0),
                tier("Festival Pass",2999,150,"#FF6B9D",1,"All-day access,Festival kit")]),
    dict(name="The Great Backyard BBQ Bash", venue="Green Meadows, Pune",
         event_date=datetime(2026,7,4,12,0), total_tickets=80, category="Food",
         price=499, age_rating="U", event_type="Social", image_url=IMG.format("food-01"),
         tags="bbq,outdoors", description="An open-lawn BBQ cookout with live grilling stations and unlimited sides.",
         tiers=[tier("Entry",499,60,"#FDBA74",0),
                tier("All-inclusive",999,20,"#FF6B9D",1,"Unlimited food & drinks")]),
    dict(name="Anime Movie Marathon", venue="CineWorld Premium, Hyderabad",
         event_date=datetime(2026,8,1,14,0), total_tickets=120, category="Movies",
         price=999, age_rating="UA", event_type="Movie", has_seat_selection=True, image_url=IMG.format("movies-02"),
         tags="anime,marathon", description="Six hours, three films, one giant IMAX screen — the ultimate anime marathon.",
         tiers=[tier("Standard",999,80,"#7DD3FC",0),
                tier("IMAX",1599,40,"#A78BFA",1,"IMAX screen,Recliner seats")]),
    dict(name="Jazz Under The Stars", venue="Rooftop at The Grand, Chennai",
         event_date=datetime(2026,8,22,19,0), total_tickets=60, category="Music",
         price=1899, age_rating="U", event_type="Music", image_url=IMG.format("music-08"),
         tags="jazz,rooftop", description="An intimate rooftop jazz evening with a live quartet and skyline views.",
         tiers=[tier("Standard",1899,40,"#A78BFA",0),
                tier("Table for 2",3999,20,"#FCD34D",1,"Reserved table,Dinner included")]),
    dict(name="K-Pop Extravaganza", venue="Dome Arena, Mumbai",
         event_date=datetime(2026,10,12,18,0), total_tickets=1000, category="Music",
         price=3499, age_rating="U", event_type="Music", image_url=IMG.format("music-07"),
         tags="k-pop,arena", description="A stadium-scale K-pop tribute show with fan-favourite setlists and pyrotechnics.",
         tiers=[tier("Bronze",3499,600,"#FDBA74",0),
                tier("Silver",5999,300,"#9CA3AF",1,"Seated section"),
                tier("Gold VIP",12999,100,"#FCD34D",2,"Front floor,VIP lounge,Merch bag")]),
    dict(name="Horror Classics Night", venue="Retro Screen, Kolkata",
         event_date=datetime(2026,10,31,21,0), total_tickets=100, category="Movies",
         price=599, age_rating="18+", event_type="Movie", image_url=IMG.format("movies-10"),
         tags="horror,halloween", description="A midnight double-bill of cult horror classics on 35mm-style projection.",
         tiers=[tier("Standard",599,100,"#374151",0)]),
    dict(name="Acoustic Sessions: Indie Night", venue="The Loft Cafe, Goa",
         event_date=datetime(2026,7,30,20,30), total_tickets=50, category="Music",
         price=699, age_rating="U", event_type="Music", image_url=IMG.format("music-09"),
         tags="acoustic,indie", description="Unplugged sets from Goa's indie singer-songwriter scene in a candlelit cafe.",
         tiers=[tier("General",699,35,"#6EE7B7",0),
                tier("Premium",1299,15,"#FF6B9D",1,"Front row,1 drink included")]),
    dict(name="Rooftop Yoga & Chill", venue="Sky Garden, Bengaluru",
         event_date=datetime(2026,7,13,7,0), total_tickets=30, category="Wellness",
         price=299, age_rating="U", event_type="Social", image_url=IMG.format("wellness-01"),
         tags="yoga,sunrise", description="A sunrise rooftop yoga flow followed by herbal tea and a skyline breakfast.",
         tiers=[tier("Drop-in",299,30,"#6EE7B7",0)]),
    dict(name="Bollywood Retro Night", venue="Heritage Hall, Jaipur",
         event_date=datetime(2026,8,8,19,0), total_tickets=200, category="Music",
         price=1299, age_rating="U", event_type="Music", image_url=IMG.format("movies-08"),
         tags="bollywood,retro", description="A live band plays back-to-back 90s and 2000s Bollywood hits in a royal heritage hall.",
         tiers=[tier("General",1299,150,"#FDBA74",0),
                tier("Royal",2499,50,"#FCD34D",1,"Royal box,Dinner buffet")]),
    dict(name="Indie Film Showcase", venue="The Art House, Delhi",
         event_date=datetime(2026,9,18,18,30), total_tickets=75, category="Movies",
         price=449, age_rating="A", event_type="Movie", image_url=IMG.format("movies-09"),
         tags="indie,shortfilm", description="Six award-winning independent shorts followed by a director Q&A.",
         tiers=[tier("Standard",449,75,"#7DD3FC",0)]),

    # ── Bihar (9 events) ──
    dict(name="Ganga Ghat Live Sessions", venue="Gandhi Maidan Grounds, Patna",
         event_date=datetime(2026,8,29,18,30), total_tickets=400, category="Music",
         price=899, age_rating="U", event_type="Music", image_url=IMG.format("music-02"),
         tags="live music,patna", description="Live folk-fusion bands perform on the banks of the Ganga as the sun sets over Patna.",
         tiers=[tier("General",899,300,"#A78BFA",0),
                tier("VIP",1899,100,"#FF6B9D",1,"Front zone,Complimentary snacks")]),
    dict(name="Patna Laughter Riot", venue="Adhaura Auditorium, Patna",
         event_date=datetime(2026,9,12,20,0), total_tickets=250, category="Comedy",
         price=499, age_rating="UA", event_type="Comedy", image_url=IMG.format("comedy-01"),
         tags="stand-up,comedy", description="Four of Bihar's sharpest stand-up comics take the stage for one riotous night.",
         tiers=[tier("General",499,200,"#FDBA74",0),
                tier("Front Row",999,50,"#FF6B9D",1,"Front row seating")]),
    dict(name="Chhath Mahaparv Cultural Mela", venue="Kali Ghat, Patna",
         event_date=datetime(2026,11,15,16,0), total_tickets=800, category="Festival",
         price=0, age_rating="U", event_type="Festival", image_url=IMG.format("festival-01"),
         tags="chhath,culture", description="A riverside cultural mela celebrating Chhath Puja with folk performances, food and craft stalls. Free entry.",
         tiers=[tier("General Entry",0,700,"#6EE7B7",0),
                tier("Priority Viewing",299,100,"#FCD34D",1,"Reserved viewing deck")]),
    dict(name="Bodhi Tree Yoga Retreat", venue="Magadh Wellness Grounds, Gaya",
         event_date=datetime(2026,8,2,6,30), total_tickets=60, category="Wellness",
         price=599, age_rating="U", event_type="Social", image_url=IMG.format("wellness-02"),
         tags="yoga,retreat", description="A half-day meditation and yoga retreat near Bodh Gaya, guided by visiting monks.",
         tiers=[tier("Drop-in",599,45,"#6EE7B7",0),
                tier("Full Day",1199,15,"#A78BFA",1,"Meals included,Guided meditation")]),
    dict(name="Shahi Litchi Food Carnival", venue="Company Bagh, Muzaffarpur",
         event_date=datetime(2026,6,10,11,0), total_tickets=350, category="Food",
         price=199, age_rating="U", event_type="Social", image_url=IMG.format("food-02"),
         tags="litchi,foodie", description="A celebration of Muzaffarpur's famous Shahi litchi with tastings, chaat stalls and local chefs.",
         tiers=[tier("Entry",199,300,"#FDBA74",0),
                tier("Tasting Pass",449,50,"#FCD34D",1,"Unlimited tastings")]),
    dict(name="Silk City Sufi Night", venue="Vikramshila Grounds, Bhagalpur",
         event_date=datetime(2026,9,26,19,30), total_tickets=200, category="Music",
         price=699, age_rating="U", event_type="Music", image_url=IMG.format("music-03"),
         tags="sufi,qawwali", description="A soulful evening of Sufi qawwali music honouring Bhagalpur's silk-weaving heritage.",
         tiers=[tier("General",699,160,"#A78BFA",0),
                tier("VIP",1399,40,"#FF6B9D",1,"Front section seating")]),
    dict(name="Mithila Art Mela", venue="Kamla Ground, Darbhanga",
         event_date=datetime(2026,10,3,10,0), total_tickets=300, category="Art",
         price=149, age_rating="U", event_type="Festival", image_url=IMG.format("art-01"),
         tags="madhubani,art", description="A showcase of traditional Madhubani and Mithila painting with live artist demonstrations.",
         tiers=[tier("Entry",149,300,"#DDD6FE",0)]),
    dict(name="Seemanchal Youth Meetup", venue="Town Hall, Purnia",
         event_date=datetime(2026,7,25,17,0), total_tickets=150, category="Social",
         price=99, age_rating="U", event_type="Social", image_url=IMG.format("food-03"),
         tags="networking,youth", description="An informal networking mixer for students and young professionals across the Seemanchal region.",
         tiers=[tier("Entry",99,150,"#6EE7B7",0)]),
    dict(name="Ganga Riverfront Marathon", venue="Munger Riverfront, Munger",
         event_date=datetime(2026,12,6,6,0), total_tickets=500, category="Sports",
         price=349, age_rating="U", event_type="Sports", image_url=IMG.format("sports-01"),
         tags="marathon,running", description="A scenic 10K/half-marathon along the Ganga riverfront, open to all skill levels.",
         tiers=[tier("10K Run",349,350,"#7DD3FC",0),
                tier("Half Marathon",599,150,"#FDBA74",1,"Finisher medal,Race kit")]),

    # ── Jharkhand (6 events) ──
    dict(name="Jharkhand Rock Fest", venue="Morabadi Ground, Ranchi",
         event_date=datetime(2026,10,17,18,0), total_tickets=600, category="Music",
         price=1199, age_rating="UA", event_type="Music", image_url=IMG.format("music-04"),
         tags="rock,festival", description="Jharkhand's biggest rock festival featuring homegrown and touring bands.",
         tiers=[tier("General",1199,450,"#A78BFA",0),
                tier("VIP",2499,150,"#FF6B9D",1,"Pit access,Artist meet & greet")]),
    dict(name="Ranchi Hockey Premier Night", venue="Birsa Munda Stadium, Ranchi",
         event_date=datetime(2026,11,8,19,0), total_tickets=1500, category="Sports",
         price=299, age_rating="U", event_type="Sports", image_url=IMG.format("sports-02"),
         tags="hockey,stadium", description="A floodlit exhibition hockey match celebrating Jharkhand's hockey legacy.",
         tiers=[tier("General Stand",299,1200,"#7DD3FC",0),
                tier("Premium Stand",799,300,"#FCD34D",1,"Covered seating")]),
    dict(name="Steel City Stand-up Nite", venue="JRD Tata Auditorium, Jamshedpur",
         event_date=datetime(2026,9,19,20,0), total_tickets=220, category="Comedy",
         price=449, age_rating="UA", event_type="Comedy", image_url=IMG.format("comedy-02"),
         tags="comedy,standup", description="A night of stand-up comedy poking fun at steel-city life, traffic and everything in between.",
         tiers=[tier("General",449,180,"#FDBA74",0),
                tier("Front Row",899,40,"#FF6B9D",1,"Front row seating")]),
    dict(name="Coalfield Film Festival", venue="Sinfor Cinema, Dhanbad",
         event_date=datetime(2026,10,24,17,0), total_tickets=140, category="Movies",
         price=349, age_rating="UA", event_type="Movie", image_url=IMG.format("movies-03"),
         tags="film,festival", description="A weekend film festival spotlighting regional cinema from the coal belt.",
         tiers=[tier("Standard",349,110,"#7DD3FC",0),
                tier("Festival Pass",799,30,"#A78BFA",1,"All-screenings access")]),
    dict(name="Bokaro Startup & Innovation Summit", venue="Sector 4 Convention Centre, Bokaro",
         event_date=datetime(2026,8,14,9,30), total_tickets=300, category="Tech",
         price=799, age_rating="U", event_type="Tech", image_url=IMG.format("tech-01"),
         tags="startup,tech", description="A day of founder talks, product demos and investor networking for East India's startup scene.",
         tiers=[tier("General",799,250,"#7DD3FC",0),
                tier("Founder Pass",1999,50,"#A78BFA",1,"Investor lounge access,Priority networking")]),
    dict(name="Baidyanath Shravani Mela", venue="Temple Grounds, Deoghar",
         event_date=datetime(2026,7,29,15,0), total_tickets=1000, category="Festival",
         price=0, age_rating="U", event_type="Festival", image_url=IMG.format("art-02"),
         tags="temple,culture", description="A cultural mela alongside the annual Shravani pilgrimage, with folk music and craft bazaars. Free entry.",
         tiers=[tier("General Entry",0,900,"#6EE7B7",0),
                tier("Guided Tour",249,100,"#FCD34D",1,"Guided heritage walk")]),

    # ── Other Indian cities (23 events) ──
    dict(name="Marine Drive Comedy Club", venue="Rangsharda Auditorium, Mumbai",
         event_date=datetime(2026,8,21,20,30), total_tickets=180, category="Comedy",
         price=699, age_rating="UA", event_type="Comedy", image_url=IMG.format("comedy-03"),
         tags="comedy,mumbai", description="An open-mic-turned-headline night with Mumbai's rising comedy stars.",
         tiers=[tier("General",699,140,"#FDBA74",0),
                tier("Front Row",1299,40,"#FF6B9D",1,"Front row seating")]),
    dict(name="Bombay Founders Night", venue="BKC Innovation Hub, Mumbai",
         event_date=datetime(2026,9,4,18,0), total_tickets=250, category="Tech",
         price=999, age_rating="U", event_type="Tech", image_url=IMG.format("tech-02"),
         tags="startup,networking", description="An evening of pitch demos and founder networking in the heart of Mumbai's business district.",
         tiers=[tier("General",999,200,"#7DD3FC",0),
                tier("VIP",2499,50,"#A78BFA",1,"Investor roundtable access")]),
    dict(name="Lodhi Art District Walk", venue="Lodhi Colony, Delhi",
         event_date=datetime(2026,10,10,9,0), total_tickets=100, category="Art",
         price=249, age_rating="U", event_type="Art", image_url=IMG.format("art-03"),
         tags="street art,walk", description="A guided walking tour through Delhi's open-air street art district.",
         tiers=[tier("Standard",249,100,"#DDD6FE",0)]),
    dict(name="Delhi Night Marathon", venue="India Gate Lawns, Delhi",
         event_date=datetime(2026,11,22,4,30), total_tickets=2000, category="Sports",
         price=399, age_rating="U", event_type="Sports", image_url=IMG.format("sports-03"),
         tags="marathon,running", description="A floodlit night run past Delhi's most iconic monuments.",
         tiers=[tier("10K Run",399,1500,"#7DD3FC",0),
                tier("Half Marathon",699,500,"#FDBA74",1,"Finisher medal,Race kit")]),
    dict(name="Namma Bengaluru Startup Summit", venue="Palace Grounds, Bangalore",
         event_date=datetime(2026,9,11,9,0), total_tickets=800, category="Tech",
         price=1499, age_rating="U", event_type="Tech", image_url=IMG.format("tech-03"),
         tags="startup,summit", description="Bangalore's flagship startup summit with keynotes, demo booths and VC speed-networking.",
         tiers=[tier("General",1499,600,"#7DD3FC",0),
                tier("All-Access",3999,200,"#A78BFA",1,"VIP lounge,Networking dinner")]),
    dict(name="Garden City Food Truck Carnival", venue="Cubbon Park, Bangalore",
         event_date=datetime(2026,7,18,12,0), total_tickets=400, category="Food",
         price=99, age_rating="U", event_type="Social", image_url=IMG.format("food-04"),
         tags="foodtrucks,carnival", description="Forty food trucks, live music and lawn seating in the middle of Cubbon Park.",
         tiers=[tier("Entry",99,400,"#FDBA74",0)]),
    dict(name="Marina Art & Culture Fest", venue="Marina Beach Promenade, Chennai",
         event_date=datetime(2026,8,30,16,0), total_tickets=500, category="Art",
         price=149, age_rating="U", event_type="Art", image_url=IMG.format("art-04"),
         tags="art,beachfront", description="A beachfront art fair featuring Tamil Nadu's sculptors, painters and craft artisans.",
         tiers=[tier("Entry",149,500,"#DDD6FE",0)]),
    dict(name="Hyderabad Premier Cricket Night", venue="GMC Balayogi Stadium, Hyderabad",
         event_date=datetime(2026,10,4,19,30), total_tickets=3000, category="Sports",
         price=499, age_rating="U", event_type="Sports", image_url=IMG.format("sports-04"),
         tags="cricket,stadium", description="A floodlit T20 exhibition match under the Hyderabad night sky.",
         tiers=[tier("General Stand",499,2200,"#7DD3FC",0),
                tier("Premium Stand",1299,600,"#FCD34D",1,"Covered seating"),
                tier("Box",4999,200,"#FF6B9D",2,"Private box,Catering included")]),
    dict(name="Deccan Wellness & Sound Bath", venue="Osho Garden, Pune",
         event_date=datetime(2026,7,27,7,0), total_tickets=80, category="Wellness",
         price=449, age_rating="U", event_type="Social", image_url=IMG.format("wellness-03"),
         tags="soundbath,wellness", description="A morning of guided meditation and Himalayan sound-bowl therapy in a garden setting.",
         tiers=[tier("Drop-in",449,60,"#6EE7B7",0),
                tier("Full Package",899,20,"#A78BFA",1,"Herbal breakfast included")]),
    dict(name="Park Street Food Carnival", venue="Park Street, Kolkata",
         event_date=datetime(2026,12,20,17,0), total_tickets=600, category="Food",
         price=149, age_rating="U", event_type="Social", image_url=IMG.format("food-05"),
         tags="streetfood,winter", description="Kolkata's iconic winter street-food carnival returns with 60+ stalls along Park Street.",
         tiers=[tier("Entry",149,600,"#FDBA74",0)]),
    dict(name="Sabarmati Riverfront Kite Mela", venue="Sabarmati Riverfront, Ahmedabad",
         event_date=datetime(2026,1,14,10,0), total_tickets=700, category="Festival",
         price=199, age_rating="U", event_type="Festival", image_url=IMG.format("art-05"),
         tags="uttarayan,kites", description="Ahmedabad's famous Uttarayan kite festival along the Sabarmati riverfront.",
         tiers=[tier("General",199,600,"#6EE7B7",0),
                tier("Rooftop Pass",599,100,"#FCD34D",1,"Rooftop viewing,Snacks included")]),
    dict(name="Pink City Heritage Art Walk", venue="City Palace Grounds, Jaipur",
         event_date=datetime(2026,11,1,8,30), total_tickets=120, category="Art",
         price=299, age_rating="U", event_type="Art", image_url=IMG.format("art-06"),
         tags="heritage,art", description="A curated walk through Jaipur's old-city art studios and miniature-painting workshops.",
         tiers=[tier("Standard",299,120,"#DDD6FE",0)]),
    dict(name="Anjuna Beach Sunset EDM", venue="Anjuna Beach, Goa",
         event_date=datetime(2026,12,28,17,0), total_tickets=1200, category="Music",
         price=1999, age_rating="UA", event_type="Music", image_url=IMG.format("music-05"),
         tags="edm,beach", description="A sunset-to-sunrise electronic music set on the sands of Anjuna beach.",
         tiers=[tier("General",1999,900,"#A78BFA",0),
                tier("VIP Deck",4499,300,"#FF6B9D",1,"Elevated deck,Complimentary drinks")]),
    dict(name="Chandigarh Cycling Marathon", venue="Sukhna Lake, Chandigarh",
         event_date=datetime(2026,9,27,6,0), total_tickets=400, category="Sports",
         price=299, age_rating="U", event_type="Sports", image_url=IMG.format("sports-05"),
         tags="cycling,lake", description="A scenic cycling marathon looping around Sukhna Lake, for amateurs and pros alike.",
         tiers=[tier("20K Ride",299,300,"#7DD3FC",0),
                tier("50K Ride",549,100,"#FDBA74",1,"Finisher medal,Hydration kit")]),
    dict(name="Awadhi Food & Culture Festival", venue="Hazratganj Grounds, Lucknow",
         event_date=datetime(2026,11,29,13,0), total_tickets=450, category="Food",
         price=249, age_rating="U", event_type="Social", image_url=IMG.format("food-06"),
         tags="awadhi,culture", description="A celebration of Lucknow's Awadhi cuisine, Kathak performances and Nawabi culture.",
         tiers=[tier("Entry",249,400,"#FDBA74",0),
                tier("Feast Pass",699,50,"#FCD34D",1,"Full course tasting menu")]),
    dict(name="Indore Improv Comedy Night", venue="Abhay Prashal, Indore",
         event_date=datetime(2026,8,7,20,0), total_tickets=200, category="Comedy",
         price=399, age_rating="UA", event_type="Comedy", image_url=IMG.format("music-10"),
         tags="improv,comedy", description="A fully improvised comedy show built from audience suggestions.",
         tiers=[tier("General",399,160,"#FDBA74",0),
                tier("Front Row",799,40,"#FF6B9D",1,"Front row seating")]),
    dict(name="Diamond City Garba Night", venue="VIP Road Grounds, Surat",
         event_date=datetime(2026,10,20,20,0), total_tickets=1000, category="Festival",
         price=349, age_rating="U", event_type="Festival", image_url=IMG.format("music-11"),
         tags="garba,navratri", description="Nine nights of Navratri garba and dandiya in Surat's biggest open-air venue — this is night one.",
         tiers=[tier("General",349,800,"#A78BFA",0),
                tier("Season Pass",1999,200,"#FCD34D",1,"All 9 nights access")]),
    dict(name="Kochi-Muziris Art Biennale Preview", venue="Fort Kochi Waterfront, Kochi",
         event_date=datetime(2026,12,12,15,0), total_tickets=300, category="Art",
         price=399, age_rating="U", event_type="Art", image_url=IMG.format("art-07"),
         tags="biennale,contemporary", description="An exclusive preview walkthrough of installations ahead of the Kochi-Muziris Biennale.",
         tiers=[tier("Standard",399,250,"#DDD6FE",0),
                tier("Curator Tour",899,50,"#A78BFA",1,"Guided curator tour")]),
    dict(name="Lakes of Bhopal Yoga Sunrise", venue="Upper Lake Promenade, Bhopal",
         event_date=datetime(2026,8,16,6,0), total_tickets=100, category="Wellness",
         price=249, age_rating="U", event_type="Social", image_url=IMG.format("wellness-04"),
         tags="yoga,lakeside", description="A lakeside sunrise yoga session followed by a guided breathing workshop.",
         tiers=[tier("Drop-in",249,100,"#6EE7B7",0)]),
    dict(name="Brahmaputra Cultural Carnival", venue="Nehru Stadium Grounds, Guwahati",
         event_date=datetime(2026,4,14,16,0), total_tickets=600, category="Festival",
         price=199, age_rating="U", event_type="Festival", image_url=IMG.format("music-12"),
         tags="bihu,culture", description="A Rongali Bihu carnival with folk dance troupes, riverside food stalls and craft bazaars.",
         tiers=[tier("General",199,550,"#6EE7B7",0),
                tier("Priority Viewing",449,50,"#FCD34D",1,"Reserved viewing area")]),
    dict(name="Golden City Sufi Qawwali Night", venue="Heritage Street, Amritsar",
         event_date=datetime(2026,9,20,19,0), total_tickets=350, category="Music",
         price=599, age_rating="U", event_type="Music", image_url=IMG.format("music-13"),
         tags="qawwali,heritage", description="A devotional Sufi qawwali evening near the Golden Temple's heritage precinct.",
         tiers=[tier("General",599,280,"#A78BFA",0),
                tier("VIP",1199,70,"#FF6B9D",1,"Front section seating")]),
    dict(name="Ganga Ghats Documentary Screening", venue="Assi Ghat, Varanasi",
         event_date=datetime(2026,11,7,18,30), total_tickets=90, category="Movies",
         price=199, age_rating="U", event_type="Movie", image_url=IMG.format("movies-05"),
         tags="documentary,ghats", description="An open-air documentary screening on the ghats, exploring the life of the Ganga.",
         tiers=[tier("Standard",199,90,"#7DD3FC",0)]),
    dict(name="Kovai Tech & Robotics Expo", venue="CODISSIA Trade Fair Complex, Coimbatore",
         event_date=datetime(2026,10,25,10,0), total_tickets=500, category="Tech",
         price=349, age_rating="U", event_type="Tech", image_url=IMG.format("tech-04"),
         tags="robotics,expo", description="A robotics and manufacturing-tech expo showcasing South India's engineering talent.",
         tiers=[tier("General",349,400,"#7DD3FC",0),
                tier("Workshop Pass",799,100,"#A78BFA",1,"Hands-on workshop access")]),
]

m = models
org = db.query(m.User).filter_by(email="admin@jtickets.com").first()
if org:
    demo_ids = db.scalars(select(m.Event.id).where(m.Event.organizer_id == org.id)).all()
    if len(demo_ids) >= len(EVENTS):
        print("Already seeded.")
        db.close(); exit(0)
    # A legacy (v2) catalogue: fewer events and rupee-valued prices. Replace only the demo
    # organizer's events and their dependents; other organizers' data is untouched.
    print(f"Replacing legacy demo catalogue ({len(demo_ids)} events)...")
    booking_ids = select(m.Booking.id).where(m.Booking.event_id.in_(demo_ids))
    db.execute(delete(m.BookingAttendee).where(m.BookingAttendee.booking_id.in_(booking_ids)))
    db.execute(delete(m.IdempotencyKey).where(m.IdempotencyKey.booking_id.in_(booking_ids)))
    db.execute(update(m.SupportTicket).where(m.SupportTicket.reference_booking_id.in_(booking_ids))
               .values(reference_booking_id=None))
    db.execute(delete(m.Notification).where(m.Notification.event_id.in_(demo_ids)))
    db.execute(delete(m.Booking).where(m.Booking.event_id.in_(demo_ids)))
    db.execute(delete(m.TicketTier).where(m.TicketTier.event_id.in_(demo_ids)))
    db.execute(delete(m.Event).where(m.Event.id.in_(demo_ids)))
else:
    org = models.User(email="admin@jtickets.com",
                      hashed_password=auth.hash_pw("jtickets2026"),
                      role="organizer", full_name="Jtickets Admin")
    db.add(org); db.flush()

now = datetime.now()
for data in EVENTS:
    tiers_data = data.pop("tiers", [])
    # Literals above read as rupees; the API stores integer paise.
    data["price"] *= 100
    for t in tiers_data: t["price"] *= 100
    # Keep the catalogue bookable: roll already-past dates forward a year.
    while data["event_date"] < now:
        data["event_date"] = data["event_date"].replace(year=data["event_date"].year + 1)
    # Literals are IST wall-clock times; the API stores naive UTC (IST = UTC+5:30).
    data["event_date"] -= timedelta(hours=5, minutes=30)
    # Tier sales draw from the event pool, so capacity must cover every tier.
    data["total_tickets"] = max(data["total_tickets"], sum(t["total_seats"] for t in tiers_data))
    event = models.Event(**data, available_tickets=data["total_tickets"], organizer_id=org.id)
    db.add(event); db.flush()
    for t in tiers_data:
        db.add(models.TicketTier(**t, event_id=event.id, available_seats=t["total_seats"]))

db.commit(); db.close()
print(f"Seeded: {len(EVENTS)} events with tiers")
print("Organizer: admin@jtickets.com / jtickets2026")
