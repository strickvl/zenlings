"""
The Map Pattern - Exercise 5: Debug the Map Bug

CONCEPT: Common .map() mistakes include:
         1. Inputs have different lengths (not allowed with .map())
         2. Passing raw Python lists instead of artifact references
         3. Parameter names don't match the step signature
         4. Using .map() outside a dynamic pipeline

THE BUG: This pipeline has a bug. Find and fix it!

HINT: Look carefully at the lengths of the two lists being mapped.
"""

from zenml import pipeline, step


@step
def get_products() -> list[str]:
    """Get product names."""
    return ["Widget", "Gadget", "Gizmo"]


@step
def get_prices() -> list[float]:
    """Get product prices."""
    # BUG: This list has a different length than products!
    return [9.99, 19.99, 29.99, 39.99]


@step
def create_listing(product: str, price: float) -> str:
    """Create a product listing."""
    listing = f"{product}: ${price:.2f}"
    print(listing)
    return listing


@step
def show_catalog(listings: list[str]) -> None:
    """Display the product catalog."""
    print("\n=== Product Catalog ===")
    for listing in listings:
        print(f"  • {listing}")


@pipeline(dynamic=True)
def map5_pipeline():
    products = get_products()  # 3 items
    prices = get_prices()       # 4 items - MISMATCH!

    # This will fail because lists have different lengths
    listings = create_listing.map(product=products, price=prices)

    show_catalog(listings)


if __name__ == "__main__":
    map5_pipeline()
