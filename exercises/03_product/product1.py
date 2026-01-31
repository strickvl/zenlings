"""
The Product Pattern - Exercise 1: Your First .product()

CONCEPT: step.product() creates a CARTESIAN PRODUCT of inputs.
         Every combination of inputs is tried!

         Example: colors=['red','blue'] and sizes=['S','M','L']
         step.product(color=colors, size=sizes) produces 2×3 = 6 calls:
           - step('red', 'S'), step('red', 'M'), step('red', 'L')
           - step('blue', 'S'), step('blue', 'M'), step('blue', 'L')

THE BUG: The code uses .map() instead of .product()

FIX: Change .map() to .product() to try all combinations.
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

    # TODO: Fix this line - we want ALL combinations, not zip!
    # .map() pairs items 1:1 (requires same length)
    # .product() creates all combinations (cartesian product)
    variants = create_variant.map(color=colors, size=sizes)

    count_variants(variants)


if __name__ == "__main__":
    product1_pipeline()
