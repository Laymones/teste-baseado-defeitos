from __future__ import annotations

import re


def _coerce_str(value) -> str:
    if value is None:
        return None
    if isinstance(value, JString):
        return value.value
    if isinstance(value, str):
        return value
    raise TypeError(f"Tipo inválido: {type(value).__name__}")


def _chars_region_match(c1: str, c2: str, ignore_case: bool) -> bool:
    if c1 == c2:
        return True
    if not ignore_case:
        return False
    u1 = c1.upper()
    u2 = c2.upper()
    if u1 != u2:
        return False
    return c1.lower() == c2.lower()


def _java_string_hash(value: str) -> int:
    """Equivalente a String.hashCode() — polinômio 31 sobre code units."""
    h = 0
    for char in value:
        h = (31 * h + ord(char)) & 0xFFFFFFFF
    if h >= 2**31:
        h -= 2**32
    return h


class JString:
    def __init__(self, value: str = ""):
        self.value = str(value)

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value

    # ----------------------------------------------------------
    # UTILITÁRIO: converte string Python para UTF-16 code units
    # ----------------------------------------------------------
    def _code_units(self):
        b = self.value.encode("utf-16-le")
        return [b[i] + (b[i + 1] << 8) for i in range(0, len(b), 2)]

    def _from_code_unit(self, cu: int):
        return chr(cu)

    # ==========================================================
    # CONSTRUTORES
    # ==========================================================

    @staticmethod
    def string(self) -> str:
        return ""

    @staticmethod
    def stringCharArray(value: list[str]) -> str:
        return "".join(value)

    @staticmethod
    def stringBytes(byte: bytes) -> str:
        return byte.decode()

    def from_stringbuilder(self, builder):
        return self(str(builder))

    @staticmethod
    def stringOriginal(original: str) -> str:
        return str(original)

    @staticmethod
    def stringCharArrayOffsetCount(value: list[str], offset: int, count: int) -> str:
        return "".join(value[offset : offset + count])

    @classmethod
    def from_bytes(cls, data: bytes, charset: str = "utf-8"):
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes")
        return cls(data.decode(charset))

    @classmethod
    def from_codepoints(cls, codepoints: list[int], offset: int = 0, count: int | None = None):
        if count is None:
            count = len(codepoints) - offset

        chars = (chr(cp) for cp in codepoints[offset : offset + count])
        return cls("".join(chars))

    # String(byte[], int offset, int length)
    @classmethod
    def from_bytes_range(cls, data: bytes, start: int, length: int, charset: str = "utf-8"):
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes")
        subset = data[start : start + length]
        return cls(subset.decode(charset))

    # String(byte[] bytes, String charset)
    # String(int[] codePoints, int offset, int count)

    # ==========================================================
    # ACESSO E TAMANHO
    # ==========================================================

    def length(self) -> int:
        return len(self._code_units())

    def isEmpty(self) -> bool:
        return self.length() == 0

    def charAt(self, index: int) -> str:
        units = self._code_units()
        if index < 0 or index >= len(units):
            raise IndexError("String index out of range")
        return chr(units[index])

    def codePointAt(self, index: int) -> int:
        units = self._code_units()

        if index < 0 or index >= len(units):
            raise IndexError("Index out of range")

        cu1 = units[index]

        # high surrogate
        if 0xD800 <= cu1 <= 0xDBFF and index + 1 < len(units):
            cu2 = units[index + 1]
            if 0xDC00 <= cu2 <= 0xDFFF:
                return 0x10000 + ((cu1 - 0xD800) << 10) + (cu2 - 0xDC00)

        return cu1

    def codePointBefore(self, index: int) -> int:
        units = self._code_units()

        if index <= 0 or index > len(units):
            raise IndexError("Index out of range")

        cu1 = units[index - 1]

        # low surrogate
        if 0xDC00 <= cu1 <= 0xDFFF and index - 2 >= 0:
            cu2 = units[index - 2]
            if 0xD800 <= cu2 <= 0xDBFF:
                return 0x10000 + ((cu2 - 0xD800) << 10) + (cu1 - 0xDC00)

        return cu1

    def codePointCount(self, beginIndex: int, endIndex: int) -> int:
        units = self._code_units()

        if beginIndex < 0 or endIndex > len(units) or beginIndex > endIndex:
            raise IndexError("Index out of range")

        i = beginIndex
        count = 0

        while i < endIndex:
            cu1 = units[i]

            if 0xD800 <= cu1 <= 0xDBFF and i + 1 < endIndex and 0xDC00 <= units[i + 1] <= 0xDFFF:
                i += 2
            else:
                i += 1

            count += 1

        return count

    def offsetByCodePoints(self, index: int, codePointOffset: int) -> int:
        length = len(self.value)

        if index < 0 or index > length:
            raise IndexError("index out of bounds")

        result = index + codePointOffset

        if result < 0 or result > length:
            raise IndexError("codePointOffset out of bounds")

        return result

    def getChars(self, srcBegin: int, srcEnd: int, dst: list, dstBegin: int) -> None:

        length = len(self.value)

        if srcBegin < 0:
            raise IndexError("srcBegin out of bounds")

        if srcBegin > srcEnd:
            raise IndexError("srcBegin greater than srcEnd")

        if srcEnd > length:
            raise IndexError("srcEnd out of bounds")

        if dstBegin < 0:
            raise IndexError("dstBegin out of bounds")

        copy_len = srcEnd - srcBegin

        if dstBegin + copy_len > len(dst):
            raise IndexError("destination array too small")

        for i in range(copy_len):
            dst[dstBegin + i] = self.value[srcBegin + i]

    def toCharArray(self) -> list:
        return list(self.value)

    def getBytes(self, charsetName: str = None) -> bytes:  # type: ignore
        if charsetName is None:
            return self.value.encode()

        try:
            return self.value.encode(charsetName)
        except LookupError:
            raise ValueError(f"Unsupported encoding: {charsetName}")

    # ==========================================================
    # COMPARAÇÃO
    # ==========================================================

    def equals(self, other) -> bool:
        """String.equals(Object obj)."""
        if self is other:
            return True
        if not isinstance(other, JString):
            return False
        return self.value == other.value

    def equalsIgnoreCase(self, other) -> bool:
        """String.equalsIgnoreCase(String anotherString)."""
        if other is None:
            return False
        return self.value.casefold() == _coerce_str(other).casefold()

    def compareTo(self, other) -> int:
        """String.compareTo(String anotherString)."""
        other_str = _coerce_str(other)
        limit = min(len(self.value), len(other_str))
        for i in range(limit):
            c1 = self.value[i]
            c2 = other_str[i]
            if c1 != c2:
                return ord(c1) - ord(c2)
        return len(self.value) - len(other_str)

    def compareToIgnoreCase(self, other) -> int:
        """String.compareToIgnoreCase(String str)."""
        other_str = _coerce_str(other)
        limit = min(len(self.value), len(other_str))
        for i in range(limit):
            c1 = self.value[i]
            c2 = other_str[i]
            if c1 != c2:
                u1 = c1.upper()
                u2 = c2.upper()
                if u1 != u2:
                    return ord(u1) - ord(u2)
                l1 = c1.lower()
                l2 = c2.lower()
                if l1 != l2:
                    return ord(l1) - ord(l2)
        return len(self.value) - len(other_str)

    def contentEquals(self, cs) -> bool:
        """String.contentEquals(CharSequence cs)."""
        if cs is None:
            return False
        return self.value == _coerce_str(cs)

    def regionMatches(
        self,
        toffset_or_ignore,
        other=None,
        ooffset=None,
        length=None,
        maybe_length=None,
    ) -> bool:
        """String.regionMatches(...) — sobrecargas com e sem ignoreCase."""
        if isinstance(toffset_or_ignore, bool):
            ignore_case = toffset_or_ignore
            toffset, other, ooffset, length = other, ooffset, length, maybe_length
        else:
            ignore_case = False
            toffset, other, ooffset, length = toffset_or_ignore, other, ooffset, length

        other_str = _coerce_str(other)
        if ooffset < 0 or toffset < 0 or length < 0:
            return False
        if toffset > len(self.value) - length or ooffset > len(other_str) - length:
            return False

        for i in range(length):
            if not _chars_region_match(
                self.value[toffset + i],
                other_str[ooffset + i],
                ignore_case,
            ):
                return False
        return True

    def hashCode(self) -> int:
        """String.hashCode()."""
        return _java_string_hash(self.value)

    # ==========================================================
    # BUSCA
    # ==========================================================

    def index_of(self, value, inicio=None):
        "Equivale ao métodos indexOf(int ch),"
        "indexOf(int ch, int fromIndex) e "
        "indexOf(String str)"
        if isinstance(value, int):
            value = chr(value)

        if inicio is None:
            return self.value.find(value)

        return self.value.find(value, inicio)

    def index_of_string_from(self, value, inicio):
        return self.value.find(value, inicio)

    def last_index_of(self, value, inicio=None):
        "Equivale ao métodos lastIndexOf(int) e lastIndexOf(int, int)"
        if isinstance(value, int):
            value = chr(value)

        if inicio is None:
            return self.value.rfind(value)

        return self.value.rfind(value, 0, inicio + 1)

    def lastIndexOf(self, str_: str, fromIndex: int = None) -> int:  # type: ignore
        """
        Returns the index of the last occurrence of the specified substring.
        """

        if fromIndex is None:
            return self.value.rfind(str_)

        if fromIndex < 0:
            return -1

        if str_ == "":
            return min(fromIndex, len(self.value))

        max_start = min(fromIndex, len(self.value) - len(str_))

        for i in range(max_start, -1, -1):
            if self.value.startswith(str_, i):
                return i

        return -1

    def contains(self, s) -> bool:
        """
        Returns true if this string contains the specified sequence.
        """
        return str(s) in self.value

    def startsWith(self, prefix: str, toffset: int = 0) -> bool:
        """
        Tests if this string starts with the specified prefix.
        """

        if toffset < 0 or toffset > len(self.value):
            return False

        return self.value.startswith(prefix, toffset)

    def endsWith(self, suffix: str) -> bool:
        """
        Tests if this string ends with the specified suffix.
        """
        return self.value.endswith(suffix)

    # ==========================================================
    # TRANSFORMAÇÃO
    # ==========================================================

    # substring(int)
    def substring(self, start: int):
        n = len(self.value)

        if start < 0 or start > n:
            raise IndexError("start index out of range")

        return JString(self.value[start:])

    # substring(int, int)
    def substring_range(self, start: int, end: int):
        n = len(self.value)

        if start < 0 or start > n:
            raise IndexError("start index out of range")

        if end < 0 or end > n or end < start:
            raise IndexError("end index out of range")

        return JString(self.value[start:end])

    # subSequence(int, int)
    def subSequence(self, start: int, end: int):
        n = len(self.value)

        if start < 0 or start > n:
            raise IndexError("start index out of range")

        if end < 0 or end > n or end < start:
            raise IndexError("end index out of range")

        return JString(self.value[start:end])

    # concat(String)
    def concat(self, other: str):
        if other is None:
            raise TypeError("cannot concat None")

        return JString(self.value + str(other))

    # replace(char oldChar, char newChar)
    # replace(CharSequence target, CharSequence replacement)

    def replace(self, target, replacement) -> JString:
        """String.replace(CharSequence target, CharSequence replacement).

        Aceita `str` ou `JString`; equivalente a replace(char, char) para chars isolados.
        """
        tgt_str = _coerce_str(target)
        repl_str = _coerce_str(replacement)
        return JString(self.value.replace(tgt_str, repl_str))

    def toLowerCase(self) -> JString:
        """String.toLowerCase()."""
        return JString(self.value.lower())

    def toUpperCase(self) -> JString:
        """String.toUpperCase()."""
        return JString(self.value.upper())

    def trim(self) -> JString:
        """String.trim()."""
        start = 0
        end = len(self.value)

        while start < end and ord(self.value[start]) <= 32:
            start += 1
        while end > start and ord(self.value[end - 1]) <= 32:
            end -= 1

        return JString(self.value[start:end])

    def intern(self) -> JString:
        """String.intern()."""
        import sys

        return JString(sys.intern(self.value))

    # ==========================================================
    # EXPRESSÕES REGULARES
    # ==========================================================

    def matches(self, regex: str) -> bool:
        """String.matches(String regex) — a regex deve casar a string inteira."""
        try:
            return re.fullmatch(regex, self.value) is not None
        except re.error as err:
            raise ValueError("PatternSyntaxException") from err

    def replaceFirst(self, regex: str, replacement: str) -> JString:
        """String.replaceFirst(String regex, String replacement)."""
        try:
            return JString(re.sub(regex, replacement, self.value, count=1))
        except re.error as err:
            raise ValueError("PatternSyntaxException") from err

    def replaceAll(self, regex: str, replacement: str) -> JString:
        """String.replaceAll(String regex, String replacement)."""
        try:
            return JString(re.sub(regex, replacement, self.value))
        except re.error as err:
            raise ValueError("PatternSyntaxException") from err

    def split(self, regex: str, limit: int = 0) -> list[JString]:
        """String.split(String regex) e String.split(String regex, int limit)."""
        try:
            if limit == 1:
                return [JString(self.value)]

            if limit > 1:
                parts = re.split(regex, self.value, maxsplit=limit - 1)
            else:
                parts = re.split(regex, self.value)

            if limit == 0:
                while len(parts) > 1 and parts[-1] == "":
                    parts.pop()

            return [JString(part) for part in parts]
        except re.error as err:
            raise ValueError("PatternSyntaxException") from err

    # ==========================================================
    # MÉTODOS ESTÁTICOS
    # ==========================================================

    @staticmethod
    def valueOfInt(value: int) -> JString:
        return JString(str(value))

    @staticmethod
    def valueOfFloat(value: float) -> JString:
        return JString(str(value))

    @staticmethod
    def valueOfBool(value: bool) -> JString:
        return JString("True" if value else "False")

    @staticmethod
    def valueOfChar(value: str) -> JString:
        if len(value) != 1:
            raise ValueError("Argumento deve ser um caractere único")
        return JString(value)

    @staticmethod
    def valueOfCharArray(value: list) -> JString:
        return JString("".join(value))

    @staticmethod
    def valueOfObject(value: object) -> JString:
        if value is None:
            return JString("null")
        return JString(str(value))

    @staticmethod
    def copyValueOf(value: list) -> JString:
        return JString("".join(value))

    @staticmethod
    def format(fmt: str, *args) -> JString:
        return JString(fmt % args)

    @staticmethod
    def join(delimiter: str, *elements) -> JString:
        return JString(delimiter.join(str(e) for e in elements))
