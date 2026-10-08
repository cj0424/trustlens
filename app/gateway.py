"""TrustLens gateway: the AI agent's only door to the shops (and, later, PayPal).

Every action is saved in the shared record (app/record.py), linked to one
errand: who the user is and what they asked for. Later steps (Detect,
Verify, Decide, Enforce, Learn) read and write the same record.

Current version: UNPROTECTED checkout. It records who would receive the money,
without any checks and without PayPal. Step 26 replaces it with Enforce."""

from datetime import datetime, timezone

from app.record import Record
from app.shop_world import ShopWorld


class Gateway:
    def __init__(self, world=None, record=None, user_id="demo-user", request=None):
        self.world = world or ShopWorld()
        self.record = record or Record()
        self.events = []
        self.cart = []
        self.payments = []
        self.user_id = user_id
        self.request = request or "(no request given)"
        self.errand_id = self.record.start_errand(self.user_id, self.request)

    def _log(self, kind, details, step="agent"):
        """Record one event, in memory and in the shared record."""
        event = {
            "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "step": step,
            "kind": kind,
            **details,
        }
        self.events.append(event)
        self.record.add_event(self.errand_id, step, kind, details)
        return event

    # ---- Tools the agent is allowed to use ----

    def search_products(self, query, max_price_eur=None):
        """Search the shops. Returns a list of matching products."""
        results = self.world.search(query, max_price_eur)
        self._log(
            "search",
            {
                "query": query,
                "max_price_eur": max_price_eur,
                "results": [result["product_id"] for result in results],
            },
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
        self.record.finish_errand(self.errand_id, "paid")
        return {"status": "paid", "payments": paid}