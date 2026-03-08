import urllib.request, json

d = json.loads(urllib.request.urlopen('http://localhost:8000/api/events/upcoming').read())
print('city:', d.get('city_name'))
print('tz:', d.get('timezone'))
print('total events:', d.get('total_events'))
print('num days:', len(d.get('days', [])))
for day in d.get('days', []):
    print(f"  {day.get('day_of_week')}, {day.get('date')}: {len(day.get('events',[]))} events")
    for ev in day.get('events', []):
        print(f"    - {ev.get('name')} [{ev.get('category')}] {ev.get('start_time','')[:16]}")
