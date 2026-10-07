"""Step 11: test the TrustLens payment gate in the PayPal sandbox.

Creates an order that only HOLDS money (authorise). After you approve it
as the test buyer, the script either cancels the hold (void) or takes the
money (capture), then confirms the final status with PayPal."""

import os
import uuid

import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
BASE_URL = os.getenv("PAYPAL_BASE_URL")


def get_token():
    response = requests.post(
        f"{BASE_URL}/v1/oauth2/token",
        auth=(CLIENT_ID, CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
        headers={"Accept": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "PayPal-Request-Id": str(uuid.uuid4()),
    }


def show_error(step, response):
    print(f"\n{step} failed. Status code: {response.status_code}")
    print(response.text)


def create_order(token):
    body = {
        "intent": "AUTHORIZE",
        "purchase_units": [
            {
                "reference_id": "trustlens-test",
                "description": "TrustLens payment gate test",
                "amount": {"currency_code": "USD", "value": "25.00"},
            }
        ],
        "payment_source": {
            "paypal": {
                "experience_context": {
                    "return_url": "https://example.com/approved",
                    "cancel_url": "https://example.com/cancelled",
                    "user_action": "CONTINUE",
                }
            }
        },
    }
    response = requests.post(
        f"{BASE_URL}/v2/checkout/orders", json=body, headers=headers(token), timeout=30
    )
    if response.status_code not in (200, 201):
        show_error("Creating the order", response)
        return None, None
    data = response.json()
    approve_link = next(
        link["href"] for link in data["links"] if link["rel"] in ("payer-action", "approve")
    )
    return data["id"], approve_link


def authorize_order(token, order_id):
    response = requests.post(
        f"{BASE_URL}/v2/checkout/orders/{order_id}/authorize",
        json={},
        headers=headers(token),
        timeout=30,
    )
    if response.status_code not in (200, 201):
        show_error("Holding the money (authorise)", response)
        return None
    data = response.json()
    return data["purchase_units"][0]["payments"]["authorizations"][0]["id"]


def void_authorization(token, auth_id):
    response = requests.post(
        f"{BASE_URL}/v2/payments/authorizations/{auth_id}/void",
        headers=headers(token),
        timeout=30,
    )
    if response.status_code not in (200, 204):
        show_error("Cancelling the hold (void)", response)
        return False
    return True


def capture_authorization(token, auth_id):
    response = requests.post(
        f"{BASE_URL}/v2/payments/authorizations/{auth_id}/capture",
        json={"final_capture": True},
        headers=headers(token),
        timeout=30,
    )
    if response.status_code not in (200, 201):
        show_error("Taking the money (capture)", response)
        return False
    return True


def get_status(token, auth_id):
    response = requests.get(
        f"{BASE_URL}/v2/payments/authorizations/{auth_id}",
        headers=headers(token),
        timeout=30,
    )
    if response.status_code != 200:
        show_error("Checking the status", response)
        return None
    return response.json().get("status")


def main():
    if not CLIENT_ID or not CLIENT_SECRET or not BASE_URL:
        print("Missing values in .env.")
        return

    token = get_token()

    order_id, approve_link = create_order(token)
    if not order_id:
        return
    print("1. Order created (USD 25.00, hold only).")
    print("\nOpen this link in a private browser window and approve as the TEST BUYER:")
    print(approve_link)

    input("\nAfter approving (you'll land on an 'Example Domain' page), press Enter here...")

    auth_id = authorize_order(token, order_id)
    if not auth_id:
        return
    print(f"2. Money is now HELD. Status: {get_status(token, auth_id)}")

    choice = input("\nType V to cancel the hold (void) or C to take the money (capture), then Enter: ")

    if choice.strip().upper() == "C":
        if capture_authorization(token, auth_id):
            print(f"3. Money TAKEN. Final status: {get_status(token, auth_id)}")
    else:
        if void_authorization(token, auth_id):
            print(f"3. Hold CANCELLED, no money taken. Final status: {get_status(token, auth_id)}")


if __name__ == "__main__":
    main()