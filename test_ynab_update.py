#!/usr/bin/env python3
"""
Simple YNAB Transaction Update Test Script
Tests updating a single transaction with a hardcoded category ID
"""

import os
import sys
from datetime import datetime

# Try to load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env file loaded")
except ImportError:
    print("ℹ️ python-dotenv not installed, skipping .env file")
    print("   Install with: pip install python-dotenv")
except Exception as e:
    print(f"ℹ️ Could not load .env file: {e}")

def test_ynab_update():
    """Test updating a YNAB transaction with hardcoded values."""

    # Hardcoded test values
    TRANSACTION_ID = "77013236-0484-4a7b-ad73-cb8d65b0c0ee"  # Real transaction from your budget
    CATEGORY_ID = "2f166614-ee27-47f1-9366-b7453609d873"  # BA Electronic rule category
    BUDGET_ID = None  # Will be detected from your budget

    print("🔍 YNAB Transaction Update Test")
    print("=" * 50)
    print(f"Transaction ID: {TRANSACTION_ID}")
    print(f"Category ID: {CATEGORY_ID}")
    print(f"Category ID Length: {len(CATEGORY_ID)}")
    print(f"Time: {datetime.now()}")
    print()

    # Check environment
    api_key = os.getenv('YNAB_API_KEY')
    if not api_key:
        print("❌ ERROR: YNAB_API_KEY environment variable not set!")
        print("Please set it in your .env file or environment")
        return False

    print("✅ YNAB API Key found")

    # Import ynab
    try:
        import ynab
        print("✅ YNAB module imported successfully")
    except ImportError as e:
        print(f"❌ ERROR: YNAB module not available: {e}")
        print("Please install with: pip install ynab")
        return False

    # Create configuration
    try:
        configuration = ynab.Configuration(access_token=api_key)
        print("✅ YNAB configuration created")
    except Exception as e:
        print(f"❌ ERROR creating configuration: {e}")
        return False

    # Get budgets
    try:
        with ynab.ApiClient(configuration) as api_client:
            from ynab.api.budgets_api import BudgetsApi
            budgets_api = BudgetsApi(api_client)
            budgets_response = budgets_api.get_budgets()

            if not budgets_response.data.budgets:
                print("❌ ERROR: No budgets found")
                return False

            # Use first budget
            budget = budgets_response.data.budgets[0]
            BUDGET_ID = budget.id
            print(f"✅ Using budget: {budget.name} (ID: {BUDGET_ID})")

            # Get categories to verify the category exists
            from ynab.api.categories_api import CategoriesApi
            categories_api = CategoriesApi(api_client)
            categories_response = categories_api.get_categories(BUDGET_ID)

            category_found = False
            for group in categories_response.data.category_groups:
                for cat in group.categories:
                    if cat.id == CATEGORY_ID:
                        category_found = True
                        print(f"✅ Category found: {group.name} > {cat.name}")
                        break
                if category_found:
                    break

            if not category_found:
                print(f"❌ ERROR: Category ID {CATEGORY_ID} not found in budget!")
                print("Available categories:")
                for group in categories_response.data.category_groups:
                    for cat in group.categories:
                        print(f"  • {cat.id[:8]}... → {group.name} > {cat.name}")
                return False

            # Get the transaction first to see its current state
            print("\n🔍 Getting current transaction state...")
            from ynab.api.transactions_api import TransactionsApi
            transactions_api = TransactionsApi(api_client)

            try:
                # Try to get the specific transaction
                # Note: YNAB API uses get_transactions (plural) and filters by ID
                response = transactions_api.get_transactions(BUDGET_ID)
                if response and response.data and response.data.transactions:
                    print(f"📊 Found {len(response.data.transactions)} total transactions in budget")

                    # Find the specific transaction by ID
                    txn = None
                    for transaction in response.data.transactions:
                        if transaction.id == TRANSACTION_ID:
                            txn = transaction
                            break

                    if not txn:
                        print(f"❌ ERROR: Transaction {TRANSACTION_ID} not found in budget")
                        print("\n🔍 Available transactions (showing first 10):")
                        for i, transaction in enumerate(response.data.transactions[:10]):
                            print(f"  {i+1}. ID: {transaction.id} | Payee: {transaction.payee_name} | Category: {transaction.category_id}")

                        # Look for transactions with similar payee names
                        print(f"\n🔍 Looking for transactions with 'BA Electronic' or similar payee names:")
                        ba_transactions = []
                        for transaction in response.data.transactions:
                            if transaction.payee_name and ('ba' in transaction.payee_name.lower() or 'electronic' in transaction.payee_name.lower()):
                                ba_transactions.append(transaction)

                        if ba_transactions:
                            print(f"Found {len(ba_transactions)} potential matches:")
                            for t in ba_transactions[:5]:
                                print(f"  • ID: {t.id} | Payee: {t.payee_name} | Category: {t.category_id}")
                        else:
                            print("No transactions with 'BA Electronic' found")

                        return False

                # Now we have the transaction, display its details
                print(f"✅ Transaction found: {txn.payee_name}")
                print(f"  • Current Category ID: {txn.category_id}")
                print(f"  • Current Category Name: {txn.category_name}")
                print(f"  • Date: {txn.var_date}")
                print(f"  • Amount: {txn.amount}")
                print(f"  • Cleared: {txn.cleared}")
                print(f"  • Approved: {txn.approved}")
                print(f"  • Import ID: {getattr(txn, 'import_id', 'None')}")
                print(f"  • Subtransactions: {len(getattr(txn, 'subtransactions', []))}")
                print(f"  • Transfer Account ID: {getattr(txn, 'transfer_account_id', 'None')}")

            except Exception as e:
                print(f"❌ ERROR getting transaction: {e}")
                return False

            # Now attempt the update
            print(f"\n🚀 Attempting to update transaction {TRANSACTION_ID}...")
            print(f"Setting category_id to: {CATEGORY_ID}")

            try:
                from ynab.models.put_transaction_wrapper import PutTransactionWrapper
                from ynab.models.existing_transaction import ExistingTransaction

                # Create update payload
                update_txn = ExistingTransaction(
                    id=TRANSACTION_ID,
                    category_id=CATEGORY_ID
                )
                wrapper = PutTransactionWrapper(transaction=update_txn)

                print("📤 Sending update request...")
                print(f"Payload: {wrapper}")

                # Make the update call
                response = transactions_api.update_transaction(BUDGET_ID, TRANSACTION_ID, wrapper)

                print("\n📥 Raw API Response:")
                print("=" * 50)
                print(f"Response Type: {type(response)}")
                print(f"Response: {response}")

                if response:
                    print(f"\nResponse Attributes: {dir(response)}")

                    if hasattr(response, 'data'):
                        print(f"\nResponse Data: {response.data}")
                        if hasattr(response.data, 'transaction'):
                            updated_txn = response.data.transaction
                            print(f"\nUpdated Transaction:")
                            print(f"  • ID: {updated_txn.id}")
                            print(f"  • Payee: {updated_txn.payee_name}")
                            print(f"  • Category ID: {updated_txn.category_id}")
                            print(f"  • Category Name: {updated_txn.category_name}")

                            if updated_txn.category_id == CATEGORY_ID:
                                print("✅ SUCCESS: Transaction updated with correct category!")
                            else:
                                print(f"❌ FAILED: Expected category {CATEGORY_ID}, got {updated_txn.category_id}")
                        else:
                            print("❌ Response missing transaction data")
                    else:
                        print("❌ Response missing data attribute")
                else:
                    print("❌ No response received")

            except Exception as e:
                print(f"❌ ERROR during update: {e}")
                print(f"Error type: {type(e)}")
                import traceback
                traceback.print_exc()
                return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    print("Starting YNAB update test...")
    success = test_ynab_update()

    if success:
        print("\n✅ Test completed successfully")
    else:
        print("\n❌ Test failed")
        sys.exit(1)
