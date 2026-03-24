"""
Q1 - MUTATION TESTING for the Order Calculation Module.

Tool Used: mutmut (Python mutation testing framework)
Run with: mutmut run --paths-to-mutate=app/core/order_calculation.py --tests-dir=tests/

Mutation testing injects small faults (mutants) into source code and checks
whether the existing test suite detects them. If a test fails when a mutant
is introduced, the mutant is "killed" (good). If all tests pass, the mutant
"survives" (test suite is weak for that case).

Mutation Operators demonstrated below:
  - AOR (Arithmetic Operator Replacement): e.g., * -> /, + -> -
  - ROR (Relational Operator Replacement): e.g., <= -> <, > -> >=
  - LCR (Logical Connector Replacement): e.g., and -> or
  - UOI (Unary Operator Insertion): e.g., x -> -x
  - SDL (Statement Deletion): removing a line
"""

import pytest
from app.core.order_calculation import OrderCalculator


class TestOrderCalculationMutation:
    """Comprehensive tests designed to kill mutants in OrderCalculator."""

    def setup_method(self):
        self.calc = OrderCalculator()

    # ─── BASE PRICE CALCULATION ─────────────────────────────────────────

    def test_base_price_single_page(self):
        """Kills AOR mutant: num_pages * price -> num_pages + price."""
        result = self.calc.calculate_base_price(1, 2.50)
        assert result == 2.50

    def test_base_price_multiple_pages(self):
        """Kills AOR mutant: num_pages * price -> num_pages / price."""
        result = self.calc.calculate_base_price(10, 2.50)
        assert result == 25.0

    def test_base_price_default_rate(self):
        """Kills SDL mutant: removing default price_per_page assignment."""
        result = self.calc.calculate_base_price(4)
        assert result == 4 * 2.50

    def test_base_price_zero_pages_raises(self):
        """Kills ROR mutant: num_pages <= 0 -> num_pages < 0."""
        with pytest.raises(ValueError, match="positive"):
            self.calc.calculate_base_price(0)

    def test_base_price_negative_pages_raises(self):
        """Kills ROR mutant: ensures negative values are rejected."""
        with pytest.raises(ValueError):
            self.calc.calculate_base_price(-5)

    # ─── DISCOUNT APPLICATION ───────────────────────────────────────────

    def test_apply_discount_zero_percent(self):
        """Kills AOR mutant: amount - discount -> amount + discount."""
        result = self.calc.apply_discount(100.0, 0)
        assert result == 100.0

    def test_apply_discount_ten_percent(self):
        """Kills AOR mutant: discount_percent / 100 -> discount_percent * 100."""
        result = self.calc.apply_discount(100.0, 10)
        assert result == 90.0

    def test_apply_discount_fifty_percent(self):
        """Kills boundary mutant for discount."""
        result = self.calc.apply_discount(200.0, 50)
        assert result == 100.0

    def test_apply_discount_hundred_percent(self):
        """Kills ROR mutant: discount_percent > 100 -> discount_percent >= 100."""
        result = self.calc.apply_discount(100.0, 100)
        assert result == 0.0

    def test_apply_discount_over_hundred_raises(self):
        """Kills ROR boundary mutant."""
        with pytest.raises(ValueError, match="between 0 and 100"):
            self.calc.apply_discount(100.0, 101)

    def test_apply_discount_negative_raises(self):
        """Kills ROR mutant: discount_percent < 0 -> discount_percent <= 0."""
        with pytest.raises(ValueError):
            self.calc.apply_discount(100.0, -5)

    # ─── TAX CALCULATION ────────────────────────────────────────────────

    def test_calculate_tax_default_rate(self):
        """Kills SDL mutant: removing default tax_rate assignment."""
        result = self.calc.calculate_tax(100.0)
        assert result == 18.0

    def test_calculate_tax_custom_rate(self):
        """Kills AOR mutant: amount * tax_rate -> amount + tax_rate."""
        result = self.calc.calculate_tax(100.0, 0.05)
        assert result == 5.0

    def test_calculate_tax_zero_amount(self):
        """Kills AOR mutant on zero boundary."""
        result = self.calc.calculate_tax(0.0, 0.18)
        assert result == 0.0

    def test_calculate_tax_negative_rate_raises(self):
        """Kills ROR mutant: tax_rate < 0 -> tax_rate <= 0."""
        with pytest.raises(ValueError, match="negative"):
            self.calc.calculate_tax(100.0, -0.05)

    def test_calculate_tax_rounding(self):
        """Kills mutant that removes round() call."""
        result = self.calc.calculate_tax(33.33, 0.18)
        assert result == 6.0  # round(33.33 * 0.18, 2) = round(5.9994, 2) = 6.0

    # ─── BULK DISCOUNT ──────────────────────────────────────────────────

    def test_bulk_discount_below_threshold(self):
        """Kills ROR mutant: num_pages >= 50 -> num_pages > 50."""
        result = self.calc.get_bulk_discount(49)
        assert result == 0.0

    def test_bulk_discount_at_threshold(self):
        """Kills ROR boundary mutant at exactly 50 pages."""
        result = self.calc.get_bulk_discount(50)
        assert result == 10.0

    def test_bulk_discount_above_threshold(self):
        """Confirms discount applied above threshold."""
        result = self.calc.get_bulk_discount(100)
        assert result == 10.0

    # ─── TOTAL ORDER CALCULATION ────────────────────────────────────────

    def test_total_order_simple(self):
        """Integration test killing multiple mutation operators."""
        result = self.calc.calculate_total_order(10, 2.50, 0, 0.18)
        assert result["base_price"] == 25.0
        assert result["discount_percent"] == 0.0
        assert result["discounted_price"] == 25.0
        assert result["tax_amount"] == 4.5
        assert result["final_total"] == 29.5

    def test_total_order_with_discount(self):
        """Kills AOR mutant in discount accumulation."""
        result = self.calc.calculate_total_order(10, 10.0, 20.0, 0.18)
        assert result["discounted_price"] == 80.0
        assert result["tax_amount"] == 14.4
        assert result["final_total"] == 94.4

    def test_total_order_bulk_discount_applied(self):
        """Kills LCR mutant: ensures bulk discount is added."""
        result = self.calc.calculate_total_order(60, 1.0)
        assert result["discount_percent"] == 10.0

    def test_total_order_premium_user(self):
        """Kills conditional mutant for is_premium check."""
        result = self.calc.calculate_total_order(10, 10.0, 0, 0.18, is_premium_user=True)
        assert result["discount_percent"] == 15.0

    def test_total_order_max_discount_cap(self):
        """Kills ROR mutant: min(total_discount, 50) boundary."""
        result = self.calc.calculate_total_order(
            60, 10.0, 30.0, 0.18, is_premium_user=True
        )
        # 30 (manual) + 10 (bulk) + 15 (premium) = 55 -> capped at 50
        assert result["discount_percent"] == 50.0

    def test_total_order_return_structure(self):
        """Kills SDL mutant: ensures all dict keys are present."""
        result = self.calc.calculate_total_order(5, 2.0)
        expected_keys = {"base_price", "discount_percent", "discounted_price",
                         "tax_amount", "final_total", "num_pages"}
        assert set(result.keys()) == expected_keys
        assert result["num_pages"] == 5


# ─── MUTATION OPERATOR EXAMPLES ─────────────────────────────────────────

class TestMutationOperatorExamples:
    """
    Demonstrates specific mutation operators and how tests detect them.

    EXAMPLE MUTATION OPERATORS:

    1. AOR (Arithmetic Operator Replacement):
       Original:  return num_pages * price_per_page
       Mutant:    return num_pages + price_per_page
       Killed by: test_base_price_multiple_pages (10*2.5=25 != 10+2.5=12.5)

    2. ROR (Relational Operator Replacement):
       Original:  if num_pages <= 0:
       Mutant:    if num_pages < 0:
       Killed by: test_base_price_zero_pages_raises (0 not < 0, so no error raised)

    3. LCR (Logical Connector Replacement):
       Original:  if discount_percent < 0 or discount_percent > 100:
       Mutant:    if discount_percent < 0 and discount_percent > 100:
       Killed by: test_apply_discount_negative_raises (-5 < 0 is True, but -5 > 100 is False)

    4. UOI (Unary Operator Insertion):
       Original:  return amount - discount
       Mutant:    return amount - (-discount)  [i.e., amount + discount]
       Killed by: test_apply_discount_ten_percent (100+10=110 != 90)

    5. SDL (Statement Deletion):
       Original:  tax_rate = self.DEFAULT_TAX_RATE
       Mutant:    (line deleted, tax_rate stays None)
       Killed by: test_calculate_tax_default_rate (None * 100 causes TypeError)
    """

    def test_aor_multiplication_to_addition(self):
        calc = OrderCalculator()
        result = calc.calculate_base_price(10, 2.50)
        assert result == 25.0, "AOR: * replaced with + would give 12.5"

    def test_ror_less_equal_to_less_than(self):
        calc = OrderCalculator()
        with pytest.raises(ValueError):
            calc.calculate_base_price(0)

    def test_lcr_or_to_and(self):
        calc = OrderCalculator()
        with pytest.raises(ValueError):
            calc.apply_discount(100.0, -5)
        with pytest.raises(ValueError):
            calc.apply_discount(100.0, 150)

    def test_uoi_negate_discount(self):
        calc = OrderCalculator()
        result = calc.apply_discount(100.0, 10)
        assert result == 90.0, "UOI: negating discount would give 110"
