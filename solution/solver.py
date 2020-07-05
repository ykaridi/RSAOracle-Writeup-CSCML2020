from __future__ import annotations

import logging
import random
import socket
from dataclasses import dataclass
from typing import Union, Optional

from Crypto.Util.number import long_to_bytes

from solution.ring_element import IntegerEuclideanDomainElement
from solution.utils import naturals

logging.basicConfig(level=logging.DEBUG)


SETUP_MAX_INVOCATIONS: int = 2 ** 11


def try_attack() -> Optional[str]:
    # Configured to check against local socat server
    sock: socket.socket = socket.socket()
    sock.connect(('127.0.0.1', 1337))

    # Receive public parameters from server.
    n: int
    e: int
    encrypted_flag: int
    n, e, encrypted_flag = map(int, sock.recv(4096).decode('ascii').split("\n")[0].split(';'))

    uses: int = 0

    def oracle(x: int) -> bool:
        # Implement oracle by querying the server
        nonlocal uses
        uses += 1

        sock.send(f"{x}\n".encode('ascii'))
        msg: str = sock.recv(1024).decode('ascii')
        return 'True' in msg

    # We consider the ring of plaintexts corresponding to f( Zn^x )
    # [plaintexts of images of invertible integers mod n via f]
    # for f(x) = encrypted_flag * (x ** e).
    # This function corresponds to multiplying the [plaintext] flag by x (and then encrypting).
    @dataclass(frozen=True)
    class RingElement(IntegerEuclideanDomainElement):
        pre_image: int

        @classmethod
        def zero(cls) -> RingElement:
            return RingElement(0)

        @property
        def image(self) -> int:
            # This corresponds to f(self.pre_image)
            return (encrypted_flag * pow(self.pre_image, e, n)) % n

        def __eq__(self, other: RingElement):
            return (self.image % n) == (other.image % n)

        def __mul__(self, other: Union[RingElement, int]) -> RingElement:
            return RingElement(self.pre_image * (other if isinstance(other, int) else other.pre_image))

        def __add__(self, other: RingElement) -> RingElement:
            return RingElement(self.pre_image + other.pre_image)

        def __ge__(self, other: IntegerEuclideanDomainElement):
            # This is an heuristic for comparison:
            # Assuming (the plaintexts of) self and other are sufficiently small
            # and the random number chosen by the oracle is sufficiently large,
            # this will indeed yield comparison:
            # + self >= other yields that (self - other) is small (self, other were sufficiently small to begin with),
            # + self < other yields  that (self - other) is large (subtraction overflows).
            return oracle((self - other).image)

    # Overview
    # ========
    #
    # We try considering random projections of our function f: f(k), f(l).
    # With high probability the corresponding plaintexts of these projections, (flag * k) % n and (flag * l) % n),
    #   will be co-prime,
    #
    # thus we can find alpha, beta such that:
    #                 alpha * (flag * k) + beta * (flag * l) = gcd((flag * k) % n, (flag * l) % m) = 1.
    # [ This is since we are able to perform the euclidean algorithm *beneath* the encryption,  ]
    # [ see ComparableIntegerRingElement                                                        ]
    #
    # In total: 1 = alpha * (flag * k) + beta * (flag * l) = flag * (alpha * k + beta * l).
    # This implies that (alpha * k + beta * l) is the inverse (mod n) of flag, and inverting mod n is easy.

    # ------------------------------------------------------------------------------------------------------------------

    # First, we try finding projections with sufficiently small plaintexts,
    #   as this is a requirement for the comparison oracle to work.
    # Note: We will slightly abuse notation and let k, l be their respective RingElements.

    # Note that comparing with zero is like asking whether the element is sufficiently small,
    #   since if the element was large with high probability the oracle would return True.
    zero: RingElement = RingElement.zero()

    k: RingElement
    while not ((k := RingElement(random.randint(1, n))) >= zero) and uses <= SETUP_MAX_INVOCATIONS:
        pass

    l: RingElement
    while not ((l := RingElement(random.randint(1, n))) >= zero) and uses <= SETUP_MAX_INVOCATIONS:
        pass

    if uses > SETUP_MAX_INVOCATIONS:
        # We want to have enough oracle invocations for actual computation,
        #   so we stop in case setup took too many invocations
        logging.error("Setup took too many oracle invocations")
        return None

    logging.info("Setup took %d random projections" % uses)

    try:
        # Perform the euclidean algorithm to find alpha, beta
        gcd: RingElement
        alpha: int
        beta: int
        gcd, alpha, beta = k.gcd(l)
    except OSError:
        # OSError caused by broken socket
        logging.error("Ran out of oracle invocations")
        return None

    logging.info("Attempt %s; took %d oracle invocations" %
                 ("was successful" if gcd.image == 1 else "has failed", uses))

    if gcd.image == 1:
        # We compute the inverse of (alpha * k + beta * l), which is the flag
        flag = long_to_bytes(pow(alpha * k.pre_image + beta * l.pre_image, -1, n)).decode('ascii')
        return flag
    else:
        return None


if __name__ == '__main__':
    for attempt in naturals(offset=1):
        logging.info("Starting attempt #%d" % attempt)
        if (flag := try_attack()) is not None:
            logging.info("Flag found! %s" % flag)
            break
