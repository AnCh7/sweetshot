from __future__ import division
class Amount(dict):
    u""" This class helps deal and calculate with the different assets on the chain.

        :param str amountString: Amount string as used by the backend (e.g. "10 SBD")
    """
    def __init__(self, amountString=u"0 SBD"):
        if isinstance(amountString, Amount):
            self[u"amount"] = amountString[u"amount"]
            self[u"asset"] = amountString[u"asset"]
        elif isinstance(amountString, unicode):
            self[u"amount"], self[u"asset"] = amountString.split(u" ")
        else:
            raise ValueError(u"Need an instance of 'Amount' or a string with amount and asset")

        self[u"amount"] = float(self[u"amount"])

    @property
    def amount(self):
        return self[u"amount"]

    @property
    def symbol(self):
        return self[u"asset"]

    @property
    def asset(self):
        return self[u"asset"]

    def __str__(self):
        # STEEM
        if self[u"asset"] == u"SBD":
            prec = 3
        elif self[u"asset"] == u"STEEM":
            prec = 3
        elif self[u"asset"] == u"VESTS":
            prec = 6

        # GOLOS
        elif self[u"asset"] == u"GBG":
            prec = 3
        elif self[u"asset"] == u"GOLOS":
            prec = 3
        elif self[u"asset"] == u"GESTS":
            prec = 6
        # default
        else:
            prec = 6
        return u"{:.{prec}f} {}".format(self[u"amount"], self[u"asset"], prec=prec)

    def __float__(self):
        return self[u"amount"]

    def __int__(self):
        return int(self[u"amount"])

    def __add__(self, other):
        a = Amount(self)
        if isinstance(other, Amount):
            assert other[u"asset"] == self[u"asset"]
            a[u"amount"] += other[u"amount"]
        else:
            a[u"amount"] += float(other)
        return a

    def __sub__(self, other):
        a = Amount(self)
        if isinstance(other, Amount):
            assert other[u"asset"] == self[u"asset"]
            a[u"amount"] -= other[u"amount"]
        else:
            a[u"amount"] -= float(other)
        return a

    def __mul__(self, other):
        a = Amount(self)
        if isinstance(other, Amount):
            a[u"amount"] *= other[u"amount"]
        else:
            a[u"amount"] *= other
        return a

    def __floordiv__(self, other):
        a = Amount(self)
        if isinstance(other, Amount):
            raise Exception(u"Cannot divide two Amounts")
        else:
            a[u"amount"] //= other
        return a

    def __div__(self, other):
        a = Amount(self)
        if isinstance(other, Amount):
            raise Exception(u"Cannot divide two Amounts")
        else:
            a[u"amount"] /= other
        return a

    def __mod__(self, other):
        a = Amount(self)
        if isinstance(other, Amount):
            a[u"amount"] %= other[u"amount"]
        else:
            a[u"amount"] %= other
        return a

    def __pow__(self, other):
        a = Amount(self)
        if isinstance(other, Amount):
            a[u"amount"] **= other[u"amount"]
        else:
            a[u"amount"] **= other
        return a

    def __iadd__(self, other):
        if isinstance(other, Amount):
            assert other[u"asset"] == self[u"asset"]
            self[u"amount"] += other[u"amount"]
        else:
            self[u"amount"] += other
        return self

    def __isub__(self, other):
        if isinstance(other, Amount):
            assert other[u"asset"] == self[u"asset"]
            self[u"amount"] -= other[u"amount"]
        else:
            self[u"amount"] -= other
        return self

    def __imul__(self, other):
        if isinstance(other, Amount):
            self[u"amount"] *= other[u"amount"]
        else:
            self[u"amount"] *= other
        return self

    def __idiv__(self, other):
        if isinstance(other, Amount):
            assert other[u"asset"] == self[u"asset"]
            return self[u"amount"] / other[u"amount"]
        else:
            self[u"amount"] /= other
            return self

    def __ifloordiv__(self, other):
        if isinstance(other, Amount):
            self[u"amount"] //= other[u"amount"]
        else:
            self[u"amount"] //= other
        return self

    def __imod__(self, other):
        if isinstance(other, Amount):
            self[u"amount"] %= other[u"amount"]
        else:
            self[u"amount"] %= other
        return self

    def __ipow__(self, other):
        self[u"amount"] **= other
        return self

    def __lt__(self, other):
        if isinstance(other, Amount):
            assert other[u"asset"] == self[u"asset"]
            return self[u"amount"] < other[u"amount"]
        else:
            return self[u"amount"] < float(other or 0)

    def __le__(self, other):
        if isinstance(other, Amount):
            assert other[u"asset"] == self[u"asset"]
            return self[u"amount"] <= other[u"amount"]
        else:
            return self[u"amount"] <= float(other or 0)

    def __eq__(self, other):
        if isinstance(other, Amount):
            assert other[u"asset"] == self[u"asset"]
            return self[u"amount"] == other[u"amount"]
        else:
            return self[u"amount"] == float(other or 0)

    def __ne__(self, other):
        if isinstance(other, Amount):
            assert other[u"asset"] == self[u"asset"]
            return self[u"amount"] != other[u"amount"]
        else:
            return self[u"amount"] != float(other or 0)

    def __ge__(self, other):
        if isinstance(other, Amount):
            assert other[u"asset"] == self[u"asset"]
            return self[u"amount"] >= other[u"amount"]
        else:
            return self[u"amount"] >= float(other or 0)

    def __gt__(self, other):
        if isinstance(other, Amount):
            assert other[u"asset"] == self[u"asset"]
            return self[u"amount"] > other[u"amount"]
        else:
            return self[u"amount"] > float(other or 0)

    __repr__ = __str__
    __truediv__ = __div__
    __truemul__ = __mul__


if __name__ == u"__main__":
    a = Amount(u"2 SBD")
    b = Amount(u"9 SBD")
    print a + b
    print b
    b **= 2
    b += .5
    print b
    print b > a

    c = Amount(u"100 STEEM")
    print c * .10

    # print(a + c)
    # print(a < c)
