"""
LAST MILE DELIVERY - Stripe Connection Test
Run this script to verify your Stripe integration is working.

Usage:
    python stripe_test.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')

if not STRIPE_SECRET_KEY:
    print("ERROR: STRIPE_SECRET_KEY not found.")
    print("Set it in your .env file or as an environment variable.")
    sys.exit(1)

import stripe
stripe.api_key = STRIPE_SECRET_KEY

print("=" * 60)
print("STRIPE CONNECTION TEST")
print("=" * 60)
print()

# Test 1: API Key
print("1. Testing API Key...")
try:
    balance = stripe.Balance.retrieve()
    print(f"   ✓ API Key valid")
    print(f"   Available: ${balance.available[0].amount / 100:.2f} {balance.available[0].currency.upper()}")
    print(f"   Pending: ${balance.pending[0].amount / 100:.2f} {balance.pending[0].currency.upper()}")
except stripe.error.AuthenticationError:
    print("   ✗ Invalid API Key")
    sys.exit(1)
print()

# Test 2: List Products
print("2. Listing Products...")
try:
    products = stripe.Product.list(limit=10)
    print(f"   Found {len(products.data)} products")
    for p in products.data:
        if 'last-mile' in p.name.lower() or 'lastmile' in p.name.lower():
            print(f"   ✓ {p.name} ({p.id})")
except Exception as e:
    print(f"   Error: {e}")
print()

# Test 3: List Prices
print("3. Listing Prices...")
try:
    prices = stripe.Price.list(limit=10)
    print(f"   Found {len(prices.data)} prices")
    for p in prices.data:
        if p.recurring:
            print(f"   ✓ {p.id}: ${p.unit_amount / 100:.2f} {p.currency.upper()}/{p.recurring.interval}")
except Exception as e:
    print(f"   Error: {e}")
print()

# Test 4: Webhook Endpoints
print("4. Listing Webhook Endpoints...")
try:
    webhooks = stripe.WebhookEndpoint.list(limit=10)
    print(f"   Found {len(webhooks.data)} endpoints")
    for w in webhooks.data:
        print(f"   ✓ {w.url} ({'enabled' if w.status == 'enabled' else 'disabled'})")
except Exception as e:
    print(f"   Error: {e}")
print()

print("=" * 60)
print("TEST COMPLETE")
print("=" * 60)
