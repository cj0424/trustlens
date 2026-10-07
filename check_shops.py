"""Step 18: check that TrustLens can read the test world."""

from app.shop_world import ShopWorld

world = ShopWorld()
print(f"Loaded {len(world.shops)} shops and {len(world.products)} products.\n")

print("Search: 'laptop' up to 900 EUR (cheapest first)")
for result in world.search("laptop", max_price_eur=900):
    print(f"  {result['total_eur']:>7.2f} EUR  {result['name']}  ({result['shop']}, {result['domain']})")

page = world.view("keystore-antivirus")
print("\nWhat an AI agent would read on the antivirus page (first 200 characters):")
print("  " + page["page_html"][:200] + "...")

print(f"\nPaying for the activation fee would send money to: {world.seller_for('keystore-help-activation')}")