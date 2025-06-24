# Billing Service Flexible Payment Configuration

## Required Changes to Billing Service

### 1. Update Minimum Purchase Amount

**File**: `/Users/nishants/Desktop/Alchemist-v1/billing-service/app/config/settings.py`

**Change**: Update MIN_PURCHASE_AMOUNT from 100.0 to 1000.0

```python
# Line 46 - Change from:
MIN_PURCHASE_AMOUNT: float = 100.0  # Minimum ₹100

# To:
MIN_PURCHASE_AMOUNT: float = 1000.0  # Minimum ₹1000
```

**Also update in FallbackSettings class** (around line 119):
```python
# Change from:
MIN_PURCHASE_AMOUNT = 100.0

# To:
MIN_PURCHASE_AMOUNT = 1000.0
```

### 2. Update Bonus Tiers for Larger Amounts

**File**: `/Users/nishants/Desktop/Alchemist-v1/billing-service/app/config/settings.py`

**Change**: Update BONUS_TIERS to support ₹1000+ minimum

```python
# Line 52-57 - Change from:
BONUS_TIERS: dict = {
    500: 10,    # 10% bonus for ₹500+
    1000: 15,   # 15% bonus for ₹1000+
    2000: 20,   # 20% bonus for ₹2000+
    5000: 25,   # 25% bonus for ₹5000+
}

# To:
BONUS_TIERS: dict = {
    1000: 0,    # No bonus for minimum ₹1000
    5000: 25,   # 25% bonus for ₹5000+
    10000: 30,  # 30% bonus for ₹10000+
    25000: 35,  # 35% bonus for ₹25000+
    50000: 40,  # 40% bonus for ₹50000+
}
```

**Also update in FallbackSettings class** (around line 124):
```python
# Change from:
BONUS_TIERS = {500: 10, 1000: 15, 2000: 20, 5000: 25}

# To:
BONUS_TIERS = {1000: 0, 5000: 25, 10000: 30, 25000: 35, 50000: 40}
```

### 3. Update Default Credit Packages

**File**: `/Users/nishants/Desktop/Alchemist-v1/billing-service/app/config/settings.py`

**Change**: Update DEFAULT_CREDIT_PACKAGES in both the main config and FallbackSettings

```python
# Lines 140-192 in FallbackSettings and 198+ in main config
# Replace entire DEFAULT_CREDIT_PACKAGES array with:

DEFAULT_CREDIT_PACKAGES = [
    {
        "id": "suggested_1000",
        "name": "Starter Amount",
        "description": "Perfect for getting started with Alchemist",
        "price": 1000.0,
        "base_credits": 1000.0,
        "bonus_credits": 0.0,
        "total_credits": 1000.0,
        "category": "suggested",
        "popular": False,
        "features": [
            "1000 credits",
            "Basic support",
            "Standard features"
        ]
    },
    {
        "id": "suggested_5000",
        "name": "Popular Amount",
        "description": "Great for regular users and small teams",
        "price": 5000.0,
        "base_credits": 5000.0,
        "bonus_credits": 1250.0,
        "total_credits": 6250.0,
        "category": "suggested",
        "popular": True,
        "features": [
            "5000 base credits",
            "1250 bonus credits (25% bonus)",
            "Priority support",
            "Advanced features"
        ]
    },
    {
        "id": "suggested_10000",
        "name": "Best Value Amount",
        "description": "Best value for heavy users and large teams",
        "price": 10000.0,
        "base_credits": 10000.0,
        "bonus_credits": 3000.0,
        "total_credits": 13000.0,
        "category": "suggested",
        "popular": False,
        "features": [
            "10000 base credits",
            "3000 bonus credits (30% bonus)",
            "Premium support",
            "All features included",
            "Custom integrations"
        ]
    },
    {
        "id": "custom_amount",
        "name": "Custom Amount",
        "description": "Choose any amount starting from ₹1000",
        "price": None,
        "base_credits": None,
        "bonus_credits": None,
        "total_credits": None,
        "category": "custom",
        "popular": False,
        "features": [
            "Minimum ₹1000",
            "No upper limit",
            "Bonus credits for larger amounts",
            "Flexible payment"
        ]
    }
]
```

## Deployment Command

After making these changes:

```bash
cd /Users/nishants/Desktop/Alchemist-v1/billing-service
gcloud run deploy billing-service --source . --platform managed --region us-central1 --allow-unauthenticated --project alchemist-e69bb
```

This will create a flexible payment system where:
- Minimum payment is ₹1000
- No upper limit
- Bonus credits scale with larger amounts
- Custom amounts are fully supported