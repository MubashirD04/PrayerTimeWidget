from prayer_api import search_location

test_queries = ["London", "New York", "Dubai", "Istanbul", "InvalidCityNameXYZ123"]

for query in test_queries:
    print(f"Searching for: {query}")
    res = search_location(query)
    if res:
        print(f"  Found: {res}")
    else:
        print(f"  Not found.")
