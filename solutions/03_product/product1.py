"""
The Product Pattern - Exercise 1: Solution

Use .product() instead of .map() to create all combinations.
.map() zips inputs (1:1), .product() creates cartesian product (N×M).
"""

from zenml import pipeline, step


@step
def get_colors() -> list[str]:
    """Get available colors."""
    return ["red", "blue", "green"]


@step
def get_sizes() -> list[str]:
    """Get available sizes."""
    return ["S", "M"]


@step
def create_variant(color: str, size: str) -> str:
    """Create a product variant."""
    variant = f"{color}-{size}"
    print(f"Created variant: {variant}")
    return variant


@step
def count_variants(variants: list[str]) -> None:
    """Count total variants."""
    print(f"\nTotal variants created: {len(variants)}")
    print("Expected: 6 (3 colors × 2 sizes)")


@pipeline(dynamic=True)
def product1_pipeline():
    colors = get_colors()  # 3 colors
    sizes = get_sizes()    # 2 sizes

    # SOLUTION: Use .product() for cartesian product
    # Creates 3 × 2 = 6 variant combinations
    variants = create_variant.product(color=colors, size=sizes)

    count_variants(variants)


if __name__ == "__main__":
    product1_pipeline()
