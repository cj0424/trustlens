"""Step 20: check the TrustLens gateway (search, view and the event log)."""

from app.gateway import Gateway

gateway = Gateway()

print("1. Agent searches for 'antivirus':")
for result in gateway.search_products("antivirus"):
    print(f"   {result['product_id']}  ({result['shop']}, {result['total_eur']} EUR)")

print("\n2. Agent opens the antivirus page:")
page = gateway.view_product("keystore-antivirus")
print(f"   {page['name']} from {page['shop']}, {page['price_eur']} EUR")

print("\n3. Agent tries a product that doesn't exist:")
print(f"   {gateway.view_product('fake-product-123')}")

print("\n4. Event log (everything the agent did, in order):")
for event in gateway.events:
    details = {k: v for k, v in event.items() if k not in ("time", "kind")}
    print(f"   [{event['time']}] {event['kind']}: {details}")