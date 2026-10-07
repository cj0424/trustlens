"""Step 10: check that TrustLens can connect to the PayPal sandbox
and list which permissions (scopes) the sandbox app has."""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
BASE_URL = os.getenv("PAYPAL_BASE_URL")

# Permissions TrustLens relies on, and what each one is for
NEEDED_SCOPES = {
    "https://uri.paypal.com/services/payments/payment/authcapture": "Hold, capture and cancel payments (payment gate)",
    "https://uri.paypal.com/services/vault/payment-tokens/readwrite": "Saved PayPal for agent payments (vault)",
    "https://uri.paypal.com/services/reporting/search/read": "Transaction search (checking results)",
}


def main():
    if not CLIENT_ID or not CLIENT_SECRET or not BASE_URL:
        print("Missing values in .env. Check PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET and PAYPAL_BASE_URL.")
        return

    response = requests.post(
        f"{BASE_URL}/v1/oauth2/token",
        auth=(CLIENT_ID, CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
        headers={"Accept": "application/json"},
        timeout=30,
    )

    if response.status_code != 200:
        print(f"Connection failed. Status code: {response.status_code}")
        print(response.text)
        return

    data = response.json()
    scopes = data.get("scope", "").split()

    print("Connected to the PayPal sandbox.")
    print(f"Access token received, valid for about {data.get('expires_in', 0) // 60} minutes.")
    print(f"Your app has {len(scopes)} permissions in total.\n")

    print("Permissions TrustLens needs:")
    for scope, purpose in NEEDED_SCOPES.items():
        status = "YES" if scope in scopes else "NOT FOUND"
        print(f"  [{status}] {purpose}")


if __name__ == "__main__":
    main()