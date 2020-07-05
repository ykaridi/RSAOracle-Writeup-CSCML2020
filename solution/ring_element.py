from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Tuple, Union

from solution.utils import naturals


class IntegerEuclideanDomainElement(ABC):
    """
    Represents an element in a euclidean domain "embedded" in the integers,
     in the sense that it is euclidean with respect to the standard norm on integers,
    which supports comparisons.

    Methods:
        + Addition
        + Subtraction
        + Multiplication
            - by an integer scalar
            - by another ring element
        + Comparison
        + Division (with remainder)
        + GCD (from division with remainder)
    """

    @classmethod
    @abstractmethod
    def zero(cls) -> IntegerEuclideanDomainElement:
        ...

    @abstractmethod
    def __eq__(self, other: IntegerEuclideanDomainElement):
        ...

    def __ne__(self, other: IntegerEuclideanDomainElement):
        return not self == other

    @abstractmethod
    def __mul__(self, other: Union[IntegerEuclideanDomainElement, int]) -> IntegerEuclideanDomainElement:
        ...

    @abstractmethod
    def __add__(self, other: IntegerEuclideanDomainElement) -> IntegerEuclideanDomainElement:
        ...

    def __sub__(self, other: IntegerEuclideanDomainElement) -> IntegerEuclideanDomainElement:
        return self + (other * (-1))

    @abstractmethod
    def __ge__(self, other: IntegerEuclideanDomainElement):
        ...

    def __le__(self, other: IntegerEuclideanDomainElement):
        return other >= self

    def __divmod__(self, other: IntegerEuclideanDomainElement):
        # We find an upper bound of the quotient (logarithmic [in actual quotient] complexity)
        b: int = 0
        for b in map(lambda exp: 2 ** exp, naturals()):
            if other * b >= self:
                break

        # Lower bound on the quotient
        a: int = 0

        # We now perform a binary search to find the exact quotient (logarithmic [in actual quotient] complexity)
        while b > a + 1:
            mid = (b + a) // 2
            if self >= other * mid:
                a = mid
            else:
                b = mid

        quotient: int = b if self >= other * b else a
        # Note remainder is a ring element and not a "proper" (meaningful?) integer
        remainder: IntegerEuclideanDomainElement = self - other * quotient
        return quotient, remainder

    def gcd(self, other: IntegerEuclideanDomainElement) -> Tuple[IntegerEuclideanDomainElement, int, int]:
        """:returns: (GCD, alpha, beta) such that: alpha * self + beta * other = GCD"""
        # Extended euclidean algorithm
        a: IntegerEuclideanDomainElement
        b: IntegerEuclideanDomainElement
        a, b = self, other

        alpha_a: int
        beta_a: int
        alpha_b: int
        beta_b: int
        alpha_a, beta_a = 1, 0
        alpha_b, beta_b = 0, 1

        iteration: int = 1
        while b != self.zero():
            logging.debug("Beginning euclidean algorithm iteration #%d" % iteration)
            quotient: int
            remainder: IntegerEuclideanDomainElement
            quotient, remainder = divmod(a, b)  # noqa: ignore divmod warning

            # GCD iteration
            # a, b = b, a % b
            a, b = b, remainder

            # Update coefficients of a to match remainder
            alpha_a, beta_a = alpha_a - quotient * alpha_b, beta_a - quotient * beta_b
            # Swap coefficients to match swap as well
            alpha_a, beta_a, alpha_b, beta_b = alpha_b, beta_b, alpha_a, beta_a

            iteration += 1

        return a, alpha_a, beta_a
