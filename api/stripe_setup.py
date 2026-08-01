"""
LAST MILE DELIVERY - Stripe Products & Prices Setup
Run this script ONCE to create your Stripe products and prices.

Usage:
    1. Set STRIPE_SECRET_KEY in your .env file
    2. Run: python stripe_setup.py
    3. Copy the output Price IDs to your .env file
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')

if not STRIPE_SECRET_KEY:
    print("ERROR: STRIPE_SECRET_KEY not found in environment variables.")
    print("Please set it in your .env file or as an environment variable.")
    sys.exit(1)

import stripe
stripe.api_key = STRIPE_SECRET_KEY

# ========================================
# PRODUCTS DEFINITION
# ========================================
PRODUCTS = [
    {
        'name': 'Last Mile - Plan Starter',
        'description': 'Plataforma de delivery para pequeñas empresas. Hasta 5 usuarios, 10 choferes, 500 pedidos/mes.',
        'metadata': {
            'plan': 'STARTER',
            'price_mxn': '999',
            'max_usuarios': '5',
            'max_choferes': '10',
            'max_pedidos_mes': '500',
            'platform': 'last-mile-delivery',
        }
    },
    {
        'name': 'Last Mile - Plan Pro',
        'description': 'Plataforma de delivery para empresas en crecimiento. Hasta 15 usuarios, 30 choferes, 2000 pedidos/mes. Incluye API y WhatsApp.',
        'metadata': {
            'plan': 'PRO',
            'price_mxn': '2499',
            'max_usuarios': '15',
            'max_choferes': '30',
            'max_pedidos_mes': '2000',
            'platform': 'last-mile-delivery',
        }
    },
    {
        'name': 'Last Mile - Plan Enterprise',
        'description': 'Plataforma de delivery empresarial. Hasta 50 usuarios, 100 choferes, 10000 pedidos/mes. Incluye SSO, SLA, branding custom.',
        'metadata': {
            'plan': 'ENTERPRISE',
            'price_mxn': '5999',
            'max_usuarios': '50',
            'max_choferes': '100',
            'max_pedidos_mes': '10000',
            'platform': 'last-mile-delivery',
        }
    },
]

# ========================================
# CREATE PRODUCTS & PRICES
# ========================================
def create_products():
    print("=" * 60)
    print("LAST MILE DELIVERY - Stripe Setup")
    print("=" * 60)
    print()

    created = []

    for product_def in PRODUCTS:
        print(f"Creating Product: {product_def['name']}...")

        # Create Product
        product = stripe.Product.create(
            name=product_def['name'],
            description=product_def['description'],
            metadata=product_def['metadata'],
            active=True,
        )

        # Create Price (monthly, MXN)
        price = stripe.Price.create(
            product=product.id,
            unit_amount=999 if 'STARTER' in product_def['name'] else (2499 if 'PRO' in product_def['name'] else 5999),
            currency='mxn',
            recurring={'interval': 'month'},
            metadata={
                'plan': product_def['metadata']['plan'],
                'platform': 'last-mile-delivery',
            }
        )

        created.append({
            'product_id': product.id,
            'price_id': price.id,
            'plan': product_def['metadata']['plan'],
            'amount': product_def['metadata']['price_mxn'],
        })

        print(f"  ✓ Product: {product.id}")
        print(f"  ✓ Price:   {price.id}")
        print()

    return created


def create_webhook_endpoint():
    """Create webhook endpoint for Stripe events."""
    print("Creating Webhook Endpoint...")

    webhook_url = os.environ.get('STRIPE_WEBHOOK_URL', 'https://lastmile-platform.onrender.com/api/billing/webhook/stripe')

    try:
        webhook = stripe.WebhookEndpoint.create(
            url=webhook_url,
            enabled_events=[
                'checkout.session.completed',
                'invoice.paid',
                'invoice.payment_failed',
                'customer.subscription.created',
                'customer.subscription.updated',
                'customer.subscription.deleted',
                'payment_intent.succeeded',
                'payment_intent.payment_failed',
            ],
            metadata={
                'platform': 'last-mile-delivery',
            }
        )

        print(f"  ✓ Webhook Endpoint: {webhook.id}")
        print(f"  ✓ Webhook Secret:   {webhook.secret}")
        print()
        return webhook

    except stripe.error.InvalidRequestError as e:
        print(f"  ⚠ Could not create webhook endpoint: {e}")
        print("  You can create it manually in the Stripe Dashboard.")
        print()
        return None


def print_env_config(created, webhook):
    """Print environment variables configuration."""
    print("=" * 60)
    print("ENVIRONMENT VARIABLES - Add to your .env file:")
    print("=" * 60)
    print()

    price_map = {item['plan']: item['price_id'] for item in created}

    print("# Stripe Configuration")
    print(f"STRIPE_SECRET_KEY={STRIPE_SECRET_KEY[:8]}... (keep secure)")
    if webhook:
        print(f"STRIPE_WEBHOOK_SECRET={webhook.secret}")
    else:
        print("STRIPE_WEBHOOK_SECRET=whsec_... (create in Dashboard)")
    print()
    print("# Stripe Price IDs")
    print(f"STRIPE_PRICE_STARTER={price_map.get('STARTER', 'price_...')}")
    print(f"STRIPE_PRICE_PRO={price_map.get('PRO', 'price_...')}")
    print(f"STRIPE_PRICE_ENTERPRISE={price_map.get('ENTERPRISE', 'price_...')}")
    print()
    print("=" * 60)
    print("NEXT STEPS:")
    print("=" * 60)
    print()
    print("1. Copy the Price IDs above to your .env file")
    print("2. If webhook secret was created, copy it too")
    print("3. If not, create webhook in Dashboard:")
    print(f"   URL: https://lastmile-platform.onrender.com/api/billing/webhook/stripe")
    print("   Events: checkout.session.completed, invoice.paid, invoice.payment_failed,")
    print("           customer.subscription.created, customer.subscription.updated,")
    print("           customer.subscription.deleted")
    print("4. Deploy to Render with these environment variables")
    print()


if __name__ == '__main__':
    try:
        created = create_products()
        webhook = create_webhook_endpoint()
        print_env_config(created, webhook)
    except stripe.error.AuthenticationError:
        print("ERROR: Invalid Stripe API key. Please check your STRIPE_SECRET_KEY.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
