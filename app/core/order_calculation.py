"""
Order Calculation Module for AI Document Enhancement System.

Handles pricing logic for document processing services including
base price computation, discount application, tax calculation,
and final total generation.
"""


class OrderCalculator:
    """Calculates the cost of document processing orders."""

    PRICE_PER_PAGE = 2.50
    BULK_THRESHOLD = 50
    BULK_DISCOUNT_RATE = 0.10
    PREMIUM_DISCOUNT_RATE = 0.15
    DEFAULT_TAX_RATE = 0.18  # GST 18%

    def calculate_base_price(self, num_pages: int, price_per_page: float = None) -> float:
        if num_pages <= 0:
            raise ValueError("Number of pages must be positive")
        if price_per_page is None:
            price_per_page = self.PRICE_PER_PAGE
        return num_pages * price_per_page

    def apply_discount(self, amount: float, discount_percent: float) -> float:
        if discount_percent < 0 or discount_percent > 100:
            raise ValueError("Discount must be between 0 and 100")
        discount = amount * (discount_percent / 100)
        return amount - discount

    def calculate_tax(self, amount: float, tax_rate: float = None) -> float:
        if tax_rate is None:
            tax_rate = self.DEFAULT_TAX_RATE
        if tax_rate < 0:
            raise ValueError("Tax rate cannot be negative")
        return round(amount * tax_rate, 2)

    def get_bulk_discount(self, num_pages: int) -> float:
        if num_pages >= self.BULK_THRESHOLD:
            return self.BULK_DISCOUNT_RATE * 100
        return 0.0

    def calculate_total_order(
        self,
        num_pages: int,
        price_per_page: float = None,
        discount_percent: float = 0.0,
        tax_rate: float = None,
        is_premium_user: bool = False,
    ) -> dict:
        base_price = self.calculate_base_price(num_pages, price_per_page)

        bulk_discount = self.get_bulk_discount(num_pages)
        total_discount = discount_percent + bulk_discount
        if is_premium_user:
            total_discount += self.PREMIUM_DISCOUNT_RATE * 100

        total_discount = min(total_discount, 50.0)

        discounted_price = self.apply_discount(base_price, total_discount)
        tax_amount = self.calculate_tax(discounted_price, tax_rate)
        final_total = round(discounted_price + tax_amount, 2)

        return {
            "base_price": base_price,
            "discount_percent": total_discount,
            "discounted_price": round(discounted_price, 2),
            "tax_amount": tax_amount,
            "final_total": final_total,
            "num_pages": num_pages,
        }
