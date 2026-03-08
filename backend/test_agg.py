import asyncio
import logging
from data_fetchers.osm_loader import load_intersections, get_intersection_coords
from data_fetchers.data_aggregator import aggregate_all_data
from db.redis_manager import get_redis, RedisStateManager

logging.basicConfig(level=logging.INFO)

async def main():
    print("Loading intersections...")
    geojson = await load_intersections()
    intersections = get_intersection_coords(geojson)
    print(f"Loaded {len(intersections)} intersections.")
    
    print("Running aggregator...")
    try:
        state = await aggregate_all_data(intersections)
        print(f"Aggregated state keys: {list(state.keys())}")
    except Exception as e:
        print(f"Aggregator crashed: {e}")

    print("Checking redis...")
    r = await get_redis()
    rsm = RedisStateManager(r)
    states = await rsm.get_all_intersection_states()
    print(f"Found {len(states)} states in Redis.")
    await r.close()

if __name__ == "__main__":
    asyncio.run(main())
