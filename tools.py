import json
from datetime import datetime, timedelta

def parse_price_range(price_query):
    """Parse price range from user query
    
    Args:
        price_query: Price specification (str, int, float, or tuple)
    Returns:
        tuple: (min_price, max_price)
    """
    # Handle existing tuple format
    if isinstance(price_query, tuple):
        return price_query
        
    # Handle direct number (treat as maximum)
    if isinstance(price_query, (int, float)):
        return (0, float(price_query))
        
    # Handle string queries
    query = price_query.lower()
    if 'under' in query or 'less than' in query:
        try:
            max_price = float(''.join(c for c in query if c.isdigit() or c == '.'))
            return (0, max_price)
        except ValueError:
            return None
    elif 'between' in query:
        try:
            numbers = [float(n) for n in ''.join(c for c in query if c.isdigit() or c == '.' or c == ' ').split()]
            if len(numbers) >= 2:
                return (min(numbers), max(numbers))
        except ValueError:
            return None
    return None

def eccomerce_search_aggregtor(name=None, color=None, price_range=None, size=None, in_stock=None, store=None, delivery=None):
    """Search and filter products based on criteria
    
    Args:
        name (str, optional): Product name to search for
        color (str, optional): Color specification
        price_range (tuple, optional): (min_price, max_price)
        size (str, optional): Size specification
        in_stock (bool, optional): Stock status
        store (str, optional): Store name
        delivery (str, optional): Delivery time
    Returns:
        str: JSON string of filtered products
    """
    # Extended mock product database
    results = [
        {"name": "Floral Skirt", "color": "multi", "price": 35, "size": "S", "in_stock": True, "store": "SiteA", "delivery": "3-day"},
        {"name": "White Sneakers", "color": "white", "price": 65, "size": "8", "in_stock": True, "store": "SiteB", "delivery": "2-day"},
        {"name": "Casual Denim Jacket", "color": "blue", "price": 80, "size": "M", "in_stock": True, "store": "SiteA", "delivery": "2-day"},
        {"name": "Cocktail Dress", "color": "red", "price": 120, "size": "M", "in_stock": True, "store": "SiteB", "delivery": "4-day"},
        {"name": "Summer Floral Dress", "color": "yellow", "price": 75, "size": "S", "in_stock": True, "store": "SiteC", "delivery": "3-day"},
        {"name": "Classic White Sneakers", "color": "white", "price": 55, "size": "8", "in_stock": True, "store": "SiteA", "delivery": "5-day"},
        {"name": "Vintage Denim Jacket", "color": "blue", "price": 75, "size": "M", "in_stock": True, "store": "SiteC", "delivery": "2-day"},
        {"name": "Sport White Sneakers", "color": "white", "price": 65.00, "size": "8", "in_stock": True, "store": "SiteB", "delivery": "2-day"},
        {"name": "Canvas White Sneakers", "color": "white", "price": 45.99, "size": "8", "in_stock": True, "store": "SiteC", "delivery": "3-day"}
    ]
    
    filtered = []
    for product in results:
        # Name check - handle variations and partial matches
        if name:
            search_terms = set(name.lower().split())
            product_terms = set(product["name"].lower().split())
            
            # Check if any search terms match product name
            if not any(term in ' '.join(product_terms) for term in search_terms):
                continue

        # Color check - case insensitive
        if color and color.lower() != product["color"].lower():
            continue
            
        # Size check - case insensitive string comparison
        if size and str(size).upper() != str(product["size"]).upper():
            continue
            
        if price_range:
            parsed_range = parse_price_range(price_range)
            if parsed_range:
                min_price, max_price = parsed_range
                if not (float(min_price) <= float(product["price"]) <= float(max_price)):
                    continue
            else:
                continue
                
        # Store check
        if store and store.lower() != product["store"].lower():
            continue
            
        # In stock check
        if in_stock is not None and product["in_stock"] != in_stock:
            continue
            
        filtered.append(product)
    
    return json.dumps(filtered)

def shipping_time_estimator(product_name, delivery_target=None, zip_code=None):
    """
    Estimate shipping time for a product based on target delivery date/day and ZIP code
    
    Args:
        product_name (str): Name of the product (case-insensitive)
        delivery_target (str, optional): Target delivery date/day (e.g., 'Friday' or '15th')
        zip_code (str, optional): Delivery ZIP code
    Returns:
        str: JSON string with shipping details and delivery feasibility
    """
    def parse_delivery_days(delivery_str):
        """Extract number of days from delivery string"""
        return int(delivery_str.split('-')[0])
    
    def calculate_delivery_feasibility(days_needed, target):
        """Calculate if delivery is possible by target date/day"""
        today = datetime.now()
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        target = target.lower()
        
        # Handle specific date (e.g., "7th", "15th")
        if any(x in target for x in ['st', 'nd', 'rd', 'th']):
            try:
                target_day = int(''.join(c for c in target if c.isdigit()))
                current_month = today.month
                current_year = today.year
                
                # If target day is less than current day, assume next month
                if target_day < today.day:
                    if current_month == 12:
                        current_month = 1
                        current_year += 1
                    else:
                        current_month += 1
                
                target_date = datetime(current_year, current_month, target_day)
                delivery_date = today + timedelta(days=days_needed)
                
                return {
                    "can_deliver": delivery_date <= target_date,
                    "estimated_delivery": delivery_date.strftime("%A, %B %d"),
                    "requested_date": target_date.strftime("%A, %B %d")
                }
                
            except ValueError:
                return {"error": "Invalid date specified"}
        
        # Handle day names (e.g., "Friday")
        elif target in days:
            current_day_idx = today.weekday()
            target_day_idx = days.index(target)
            
            # Calculate days until target
            days_until_target = target_day_idx - current_day_idx
            if days_until_target <= 0:
                days_until_target += 7
                
            delivery_date = today + timedelta(days=days_needed)
            target_date = today + timedelta(days=days_until_target)
            
            return {
                "can_deliver": delivery_date <= target_date,
                "estimated_delivery": delivery_date.strftime("%A, %B %d"),
                "requested_date": target_date.strftime("%A, %B %d")
            }
        
        else:
            return {"error": "Invalid delivery target specified"}

    # Find matching product using case-insensitive partial match
    found_products = json.loads(eccomerce_search_aggregtor(name=product_name))
    if not found_products:
        return json.dumps({"error": "Product not found"})
    
    product = found_products[0]  # Use first matching product
    store = product["store"]
    delivery_days = parse_delivery_days(product["delivery"])
    
    # Get shipping info
    shipping_info = {
        "Summer Floral Skirt": {
            "SiteA": {
                "12345": {"estimated_delivery": "2-day", "cost": 4.99},
                "67890": {"estimated_delivery": "3-day", "cost": 5.99},
                "default": {"estimated_delivery": "3-day", "cost": 4.99}
            },
            "SiteB": {
                "12345": {"estimated_delivery": "3-day", "cost": 5.99},
                "67890": {"estimated_delivery": "4-day", "cost": 6.99},
                "default": {"estimated_delivery": "4-day", "cost": 5.99}
            },
            "SiteC": {
                "12345": {"estimated_delivery": "2-day", "cost": 4.99},
                "67890": {"estimated_delivery": "3-day", "cost": 5.99},
                "default": {"estimated_delivery": "3-day", "cost": 4.99}
            }
        },
        "White Sneakers": {
            "SiteA": {"estimated_delivery": "3-day", "cost": 5.99},
            "SiteB": {"estimated_delivery": "2-day", "cost": 4.99},
            "SiteC": {"estimated_delivery": "3-day", "cost": 4.99}
        },
        "Casual Denim Jacket": {
            "SiteA": {"estimated_delivery": "2-day", "cost": 5.99},
            "SiteB": {"estimated_delivery": "3-day", "cost": 6.99},
            "SiteC": {"estimated_delivery": "3-day", "cost": 5.99}
        },
        "Cocktail Dress": {
            "SiteA": {"estimated_delivery": "3-day", "cost": 6.99},
            "SiteB": {"estimated_delivery": "4-day", "cost": 7.99},
            "SiteC": {"estimated_delivery": "3-day", "cost": 6.99}
        },
        "Summer Floral Dress": {
            "SiteA": {"estimated_delivery": "3-day", "cost": 4.99},
            "SiteB": {"estimated_delivery": "3-day", "cost": 5.99},
            "SiteC": {"estimated_delivery": "3-day", "cost": 4.99}
        },
        "Classic White Sneakers": {
            "SiteA": {"estimated_delivery": "5-day", "cost": 4.99},
            "SiteB": {"estimated_delivery": "3-day", "cost": 5.99},
            "SiteC": {"estimated_delivery": "4-day", "cost": 4.99}
        },
        "Vintage Denim Jacket": {
            "SiteA": {"estimated_delivery": "3-day", "cost": 5.99},
            "SiteB": {"estimated_delivery": "3-day", "cost": 6.99},
            "SiteC": {"estimated_delivery": "2-day", "cost": 5.99}
        },
        "Sport White Sneakers": {
            "SiteA": {"estimated_delivery": "3-day", "cost": 5.99},
            "SiteB": {"estimated_delivery": "2-day", "cost": 4.99},
            "SiteC": {"estimated_delivery": "3-day", "cost": 4.99}
        },
        "Canvas White Sneakers": {
            "SiteA": {"estimated_delivery": "4-day", "cost": 4.99},
            "SiteB": {"estimated_delivery": "3-day", "cost": 5.99},
            "SiteC": {"estimated_delivery": "3-day", "cost": 4.99}
        }
    }
    
    # Get store's shipping details for ZIP code
    store_shipping = shipping_info.get(product["name"], {}).get(store, {})
    if not store_shipping:
        return json.dumps({"error": "Shipping information not available"})
        
    # Get ZIP code specific shipping or default
    zip_shipping = store_shipping.get(zip_code, store_shipping.get("default", {}))
    if not zip_shipping:
        return json.dumps({"error": f"Shipping not available to ZIP code {zip_code}"})
    
    delivery_days = parse_delivery_days(zip_shipping["estimated_delivery"])
    
    # Add delivery feasibility if day specified
    if delivery_target:
        delivery_check = calculate_delivery_feasibility(delivery_days, delivery_target)
        zip_shipping.update(delivery_check)
        if zip_code:
            zip_shipping["zip_code"] = zip_code
    
    return json.dumps(zip_shipping)

def discount_promo_checker(product_name):
    """Check available discount codes for a product
    
    Args:
        product_name (str): Name of the product
    Returns:
        str: JSON string with available discount codes
    """
    discounts = {
        "Floral Skirt": {"SPRING10": 10, "SAVE20": 20, "NEW15": 15},
        "White Sneakers": {"SHOES15": 15, "NEW10": 10},
        "Casual Denim Jacket": {"DENIM10": 10, "SAVE20": 20},
        "Cocktail Dress": {"PARTY25": 25, "NEW15": 15},
        "Summer Floral Dress": {"SUMMER": 15, "NEW10": 10},
        "Classic White Sneakers": {"SHOES15": 15, "NEW10": 10},
        "Vintage Denim Jacket": {"DENIM10": 10, "SAVE20": 20},
        "Sport White Sneakers": {"SHOES15": 15, "NEW10": 10},
        "Canvas White Sneakers": {"SHOES10": 10, "NEW10": 10}
    }
    return json.dumps(discounts.get(product_name, {}))

def return_policy_checker(store_name):
    """
    Check return policy for a store
    
    Args:
        store_name (str): Name of the store ('SiteA', 'SiteB', 'SiteC')
    Returns:
        str: JSON string with return policy
    """
    policies = {
        "SiteA": {
            "window": "30 days",
            "free_returns": True,
            "conditions": "Must have original tags",
            "processing_time": "3-5 business days"
        },
        "SiteB": {
            "window": "14 days",
            "free_returns": False,
            "conditions": "Return shipping fee applies",
            "processing_time": "5-7 business days"
        },
        "SiteC": {
            "window": "45 days",
            "free_returns": True,
            "conditions": "Items must be unworn with tags attached",
            "processing_time": "2-4 business days"
        }
    }
    
    # Get store from product if store_name is a product name
    if store_name not in policies:
        for product in json.loads(eccomerce_search_aggregtor(name=store_name)):
            if store_name.lower() in product['name'].lower():
                return json.dumps(policies.get(product['store'], {"error": "Store not found"}))
    
    return json.dumps(policies.get(store_name, {"error": "Store not found"}))

def competitor_price_comparison(product_name):
    """
    Compare prices across different stores
    
    Args:
        product_name (str): Name of the product
    Returns:
        str: JSON string with price comparisons
    """
    comparisons = {
        "Floral Skirt": [
            {"store": "SiteA", "price": 35.00, "in_stock": True},
            {"store": "SiteB", "price": 37.99, "in_stock": True},
            {"store": "SiteC", "price": 36.50, "in_stock": True}
        ],
        "White Sneakers": [
            {"store": "SiteA", "price": 63.99, "in_stock": True},
            {"store": "SiteB", "price": 65.00, "in_stock": True},
            {"store": "SiteC", "price": 67.99, "in_stock": True}
        ],
        "Casual Denim Jacket": [
            {"store": "SiteA", "price": 80.00, "in_stock": True},
            {"store": "SiteB", "price": 85.99, "in_stock": True},
            {"store": "SiteC", "price": 82.99, "in_stock": True}
        ],
        "Cocktail Dress": [
            {"store": "SiteA", "price": 118.99, "in_stock": True},
            {"store": "SiteB", "price": 120.00, "in_stock": True},
            {"store": "SiteC", "price": 122.99, "in_stock": True}
        ],
        "Summer Floral Dress": [
            {"store": "SiteA", "price": 72.99, "in_stock": True},
            {"store": "SiteB", "price": 77.99, "in_stock": True},
            {"store": "SiteC", "price": 75.00, "in_stock": True}
        ],
        "Classic White Sneakers": [
            {"store": "SiteA", "price": 55.00, "in_stock": True},
            {"store": "SiteB", "price": 57.99, "in_stock": True},
            {"store": "SiteC", "price": 56.50, "in_stock": True}
        ],
        "Vintage Denim Jacket": [
            {"store": "SiteA", "price": 77.99, "in_stock": True},
            {"store": "SiteB", "price": 75.00, "in_stock": True},
            {"store": "SiteC", "price": 75.00, "in_stock": True}
        ],
        "Sport White Sneakers": [
            {"store": "SiteA", "price": 67.99, "in_stock": True},
            {"store": "SiteB", "price": 65.00, "in_stock": True},
            {"store": "SiteC", "price": 66.50, "in_stock": True}
        ],
        "Canvas White Sneakers": [
            {"store": "SiteA", "price": 47.99, "in_stock": True},
            {"store": "SiteB", "price": 46.50, "in_stock": True},
            {"store": "SiteC", "price": 45.99, "in_stock": True}
        ]
    }
    
    # Case-insensitive product name matching
    for key in comparisons:
        if key.lower() == product_name.lower():
            return json.dumps(comparisons[key])
    return json.dumps([])