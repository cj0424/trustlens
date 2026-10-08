"""TrustLens test world: loads the simulated shops and products
from data/shops.json and lets the agent search and view them.

Product pages are wrapped in a realistic shop layout (menu, specs,
delivery and returns, payment methods, footer), so any hidden
instruction is buried inside a full page, as on real websites."""

import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "shops.json"


def _page_layout(shop, product):
    """Build a realistic full product page around the product's own content."""
    name = shop["name"]
    domain = shop["domain"]
    header = (
        f"<header><a href='https://{domain}/'>{name}</a>"
        "<nav><a href='/'>Home</a> | <a href='/new'>New arrivals</a> | "
        "<a href='/offers'>Offers</a> | <a href='/help'>Help</a> | "
        "<a href='/account'>My account</a> | <a href='/cart'>Cart</a></nav>"
        "<p>Free delivery on orders over 50 EUR. Customer service: Mon-Fri, 9:00-18:00.</p></header>"
        f"<div class='breadcrumbs'>Home &gt; {product['category'].title()} &gt; {product['name']}</div>"
    )
    details = (
        "<section class='details'><h2>Product details</h2><ul>"
        f"<li>Condition: {product['condition']}</li>"
        f"<li>Sold and shipped by: {name}</li>"
        f"<li>Delivery cost: {product['shipping_eur']:.2f} EUR</li>"
        "<li>Usually ships within 1 to 2 working days</li></ul></section>"
    )
    policies = (
        "<section class='delivery-returns'><h2>Delivery and returns</h2>"
        "<p>Standard delivery takes 2 to 4 working days within Spain. You can return most items "
        "within 30 days of delivery for a full refund. Items must be unused and in their original packaging.</p></section>"
        "<section class='payment'><h2>Secure payment</h2>"
        "<p>We accept PayPal, Visa, Mastercard and Bizum. All payments are encrypted.</p></section>"
    )
    footer = (
        f"<footer><p>{name} - {domain}</p>"
        "<p><a href='/about'>About us</a> | <a href='/privacy'>Privacy policy</a> | "
        "<a href='/terms'>Terms and conditions</a> | <a href='/cookies'>Cookie settings</a></p>"
        "<p>Copyright 2026. All rights reserved.</p></footer>"
    )
    return header + "<main>" + product["page_html"] + details + policies + "</main>" + footer


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
        """Return a product page, including the full page content the agent reads."""
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
            "page_html": _page_layout(shop, product),
        }

    def seller_for(self, product_id):
        """Which PayPal seller would receive the money for this product."""
        product = self.products[product_id]
        return self.shops[product["shop_id"]]["paypal_seller"]