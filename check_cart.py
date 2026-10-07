"""Step 23: simulate a TRICKED agent with no protection.

It buys the antivirus AND follows the hidden instruction to pay the
'activation fee'. Who receives the money?"""

from app.gateway import Gateway

gateway = Gateway()

print("A tricked agent adds two items to the cart:")
gateway.add_to_cart("keystore-antivirus")        # what the user asked for
gateway.add_to_cart("keystore-help-activation")  # what the hidden text asked for

cart = gateway.view_cart()
for item in cart["items"]:
    print(f"  - {item['name']} ({item['shop']}): {item['line_total_eur']} EUR")
print(f"  Cart total: {cart['total_eur']} EUR")

print("\nUnprotected checkout:")
result = gateway.checkout()
for payment in result["payments"]:
    warning = "   <-- ATTACKER" if "ATTACKER" in payment["seller"] else ""
    print(f"  Paid {payment['amount_eur']} EUR to {payment['seller']}{warning}")

print(f"\nEvents recorded: {len(gateway.events)}")