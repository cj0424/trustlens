"""TrustLens gateway: the AI agent's only door to the shops (and, later, PayPal).

Every action the agent takes goes through here and is recorded in the event log.
Later steps add the shield, the bait, the cart and the payment gate."""

from datetime import datetime, timezone

from app.shop_world import ShopWorld


class Gateway:
    def __init__(self, world=None):
        self.world = world or ShopWorld()
        self.events = []

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