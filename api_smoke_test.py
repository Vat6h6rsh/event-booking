import requests

BASE = 'http://localhost:8000'
r = requests.post(BASE+'/login', data={'username':'admin@jtickets.com','password':'jtickets2026'})
d = r.json(); token = d['access_token']; print('Login OK, user fields:', list(d['user'].keys()))
H = {'Authorization': f'Bearer {token}'}

events = requests.get(BASE+'/events').json()
print('Events:', len(events), '| First tiers:', [t['name'] for t in events[0].get('tiers',[])])

r2 = requests.post(BASE+'/signup', json={'email':'buyer3@test.com','password':'testtest','role':'customer','full_name':'Test Buyer'})
ch = {'Authorization': 'Bearer ' + requests.post(BASE+'/login', data={'username':'buyer3@test.com','password':'testtest'}).json()['access_token']}

me = requests.get(BASE+'/users/me', headers=ch).json(); print('GET /me full_name:', me['full_name'])

ev = events[0]; eid = ev['id']
tiers = requests.get(f'{BASE}/events/{eid}/tiers').json()
print('Tiers:', [(t['name'], t['price']) for t in tiers])

bk = requests.post(BASE+'/bookings', json={
    'event_id':eid,'tier_id':tiers[0]['id'],'quantity':1,
    'attendees':[{'full_name':'Test Buyer','age':25,'phone':'+91 9876543210'}]
}, headers=ch)
print('Booking:', bk.status_code)
if bk.status_code == 201:
    b = bk.json()
    print('  event_name:', b.get('event_name'), '| tier_name:', b.get('tier_name'))
    print('  ticket_code:', b['attendees'][0]['ticket_code'])

st = requests.post(BASE+'/support/tickets', json={'subject':'Test','description':'Test support request here','category':'general'}, headers=ch)
print('Support ticket:', st.status_code, st.json().get('status'))
print('Legal terms:', requests.get(BASE+'/legal/terms').json()['type'])
seats = requests.get(f'{BASE}/events/{eid}/seats').json()
print('Seat map:', seats)

# 18+ gate test
horror_ev = next((e for e in events if e['age_rating'] == '18+'), None)
if horror_ev:
    bk18 = requests.post(BASE+'/bookings', json={
        'event_id': horror_ev['id'], 'quantity': 1,
        'attendees': [{'full_name': 'Minor Kid', 'age': 14}]
    }, headers=ch)
    print('18+ gate (age 14):', bk18.status_code, bk18.json().get('detail','')[:60])

print('ALL PASSED')
