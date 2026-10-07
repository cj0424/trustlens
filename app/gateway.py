"""TrustLens gateway: the AI agent's only door to the shops (and, later, PayPal).

Every action the agent takes goes through here and is recorded in the event log.

Current version: UNPROTECTED checkout. It records who would receive the money,
without any checks and without PayPal. Later steps replace it with the
payment gate, and add the shield and the bait."""

from datetime import datetime, timezone

from app.shop_world import ShopWorld


class Gateway:
    def __init__(self, world=None):
        self.world = world or ShopWorld()
        self.events = []
        self.cart = []
        self.payments = []

    def _log(self, kind, details):
        """Record one event. This log feeds the protection feed later."""
        event = {
            "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "kind": kind,
            **details,
        }
        self.events.append(event)
        return event

    # ---- Tools the agent is allowed to use ----

    def search_products(self, query, max_price_eur=None):
        """Search the shops. Returns a list of matching products."""
        results = self.world.search(query, max_price_eur)
        self._log(
            "search",
            {"query": query, "max_price_eur": max_price_eur, "results": len(results)},
        )
        return results

    def view_product(self, product_id):
        """Open a product page. Returns the page the agent will read."""
        page = self.world.view(product_id)
        if page is None:
            self._log("view_failed", {"product_id": product_id})
            return {"error": f"No product with id '{product_id}'"}

        self._log("view", {"product_id": product_id, "shop": page["shop"]})
        return page

    def add_to_cart(self, product_id):
        """Add a product to the cart."""
        product = self.world.products.get(product_id)
        if product is None:
            self._log("add_to_cart_failed", {"product_id": product_id})
            return {"error": f"No product with id '{product_id}'"}

        self.cart.append(product_id)
        self._log("add_to_cart", {"product_id": product_id, "price_eur": product["price_eur"]})
        return {"added": product_id, "cart": self.view_cart()}

    def view_cart(self):
        """Show what's in the cart and the total, including shipping."""
        items = []
        total = 0.0
        for product_id in self.cart:
            product = self.world.products[product_id]
            line_total = round(product["price_eur"] + product["shipping_eur"], 2)
            total += line_total
            items.append(
                {
                    "product_id": product_id,
                    "name": product["name"],
                    "shop": self.world.shops[product["shop_id"]]["name"],
                    "line_total_eur": line_total,
                }
            )
        return {"items": items, "total_eur": round(total, 2)}

    def checkout(self):
        """UNPROTECTED checkout: pays every seller in the cart, no questions asked.
        For now it only records the payments (no PayPal yet)."""
        if not self.cart:
            return {"error": "The cart is empty."}

        # Group the cart by who receives the money
        amounts = {}
        for product_id in self.cart:
            product = self.world.products[product_id]
            seller = self.world.seller_for(product_id)
            amounts[seller] = round(
                amounts.get(seller, 0.0) + product["price_eur"] + product["shipping_eur"], 2
            )

        paid = []
        for seller, amount in amounts.items():
            payment = {"seller": seller, "amount_eur": amount}
            self.payments.append(payment)
            self._log("payment", payment)
            paid.append(payment)

        self.cart = []
        return {"status": "paid", "payments": paid}