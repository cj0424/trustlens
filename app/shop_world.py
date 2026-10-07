"""TrustLens test world: loads the simulated shops and products
from data/shops.json and lets the agent search and view them."""

import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "shops.json"


class ShopWorld:
    def __init__(self, path=DATA_FILE):
        with open(path, encoding="utf-8") as file:
            data = json.load(file)

        self.shops = {shop["id"]: shop for shop in data["shops"]}
        self.products = {product["id"]: product for product in data["products"]}

        # Safety check: every product must belong to a shop that exists
        for product in self.products.values():
            if product["shop_id"] not in self.shops:
                raise ValueError(
                    f"Product {product['id']} points to unknown shop {product['shop_id']}"
                )

    def search(self, query, max_price_eur=None):
        """Find products whose name, category or description match the query.
        Results are sorted from cheapest to most expensive (total with shipping)."""
        words = [word for word in query.lower().split() if word]
        results = []

        for product in self.products.values():
            text = f"{product['name']} {product['category']} {product['description']}".lower()
            if words and not any(word in text for word in words):
                continue

            total = round(product["price_eur"] + product["shipping_eur"], 2)
            if max_price_eur is not None and total > max_price_eur:
                continue

            shop = self.shops[product["shop_id"]]
            results.append(
                {
                    "product_id": product["id"],
                    "name": product["name"],
                    "shop": shop["name"],
                    "domain": shop["domain"],
                    "price_eur": product["price_eur"],
                    "shipping_eur": product["shipping_eur"],
                    "total_eur": total,
                    "condition": product["condition"],
                }
            )

        return sorted(results, key=lambda result: result["total_eur"])

    def view(self, product_id):
        """Return a product page, including the raw page content the agent reads."""
        product = self.products.get(product_id)
        if product is None:
            return None

        shop = self.shops[product["shop_id"]]
        return {
            "product_id": product["id"],
            "name": product["name"],
            "shop": shop["name"],
            "domain": shop["domain"],
            "price_eur": product["price_eur"],
            "shipping_eur": product["shipping_eur"],
            "condition": product["condition"],
            "page_html": product["page_html"],
        }

    def seller_for(self, product_id):
        """Which PayPal seller would receive the money for this product."""
        product = self.products[product_id]
        return self.shops[product["shop_id"]]["paypal_seller"]