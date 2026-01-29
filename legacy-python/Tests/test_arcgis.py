import geocoder

test_queries = ["London", "New York", "Dubai", "Istanbul"]

for query in test_queries:
    print(f"Searching for (ArcGIS): {query}")
    g = geocoder.arcgis(query)
    if g.ok:
        print(f"  Found: {g.lat}, {g.lng}, {g.city or g.address}")
    else:
        print(f"  Not found.")
