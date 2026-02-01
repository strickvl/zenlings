"""
The Map Pattern - Exercise 5: Solution

The bug was a length mismatch between the two lists.
When using .map() with multiple inputs, they must have the same length.
"""

from zenml import pipeline, step


@step(enable_cache=False)
def get_products() -> list[str]:
    """Get product names."""
    return ["Widget", "Gadget", "Gizmo"]


@step(enable_cache=False)
def get_prices() -> list[float]:
    """Get product prices."""
    # SOLUTION: Match the length to products (3 items)
    return [9.99, 19.99, 29.99]


@step(enable_cache=False)
def create_listing(product: str, price: float) -> str:
    """Create a product listing."""
    listing = f"{product}: ${price:.2f}"
    print(listing)
    return listing


@step(enable_cache=False)
def show_catalog(listings: list[str]) -> None:
    """Display the product catalog."""
    print("\n=== Product Catalog ===")
    for listing in listings:
        print(f"  • {listing}")


@pipeline(dynamic=True)
def map5_pipeline():
    products = get_products()  # 3 items
    prices = get_prices()       # 3 items - NOW MATCHES!

    # Now this works because both lists have 3 items
    listings = create_listing.map(product=products, price=prices)

    show_catalog(listings)


if __name__ == "__main__":
    map5_pipeline()
