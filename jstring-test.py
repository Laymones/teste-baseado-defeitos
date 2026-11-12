"""Bateria de testes para JString (teste de mutação com Cosmic Ray).

Todos os testes passam no código original. Os comentários "DEFEITO" marcam
pontos onde o original difere do Java; nesses casos o teste fixa o
comportamento ATUAL (não o do Java) para que o baseline passe.
"""
import pytest

from jstring import JString, _coerce_str, _chars_region_match, _java_string_hash

EMOJI = "\U0001F600"  # 😀


def S(x=""):
    return JString(x)


# ======================================================================
# Funções auxiliares
# ======================================================================

class TestCoerceStr:
    def test_none(self):
        assert _coerce_str(None) is None

    def test_jstring(self):
        assert _coerce_str(S("abc")) == "abc"

    def test_str(self):
        assert _coerce_str("xyz") == "xyz"

    def test_tipo_invalido(self):
        with pytest.raises(TypeError) as e:
            _coerce_str(123)
        assert "int" in str(e.value)


class TestCharsRegionMatch:
    def test_iguais(self):
        assert _chars_region_match("a", "a", False) is True
        assert _chars_region_match("a", "a", True) is True

    def test_diferentes_sem_ignore(self):
        assert _chars_region_match("a", "A", False) is False

    def test_diferentes_com_ignore(self):
        assert _chars_region_match("a", "A", True) is True
        assert _chars_region_match("a", "b", True) is False

    def test_upper_igual_mas_lower_diferente(self):
        # 'ı' (i sem ponto) e 'i' têm o mesmo upper() ('I'), lower() diferente
        assert _chars_region_match("ı", "i", True) is False


class TestJavaHash:
    def test_vazio(self):
        assert _java_string_hash("") == 0

    def test_valores_conhecidos(self):
        assert _java_string_hash("a") == 97
        assert _java_string_hash("abc") == 96354
        assert _java_string_hash("Hello") == 69609650

    def test_overflow_negativo(self):
        # "hello world" em Java -> 1794106052
        assert _java_string_hash("hello world") == 1794106052
        # string longa que estoura int32 e fica negativa em Java
        assert _java_string_hash("polygenelubricants") == -2147483648

    def test_limite_sinal(self):
        h = _java_string_hash("zzzzzzzzzz")
        assert -2**31 <= h < 2**31


# ======================================================================
# Construtores
# ======================================================================

class TestConstrutores:
    def test_init_default(self):
        assert S().value == ""
        assert JString().value == ""

    def test_init_converte_para_str(self):
        assert JString(123).value == "123"

    def test_str_repr(self):
        assert str(S("abc")) == "abc"
        assert repr(S("abc")) == "abc"

    def test_string(self):
        assert JString.string(None) == ""

    def test_string_char_array(self):
        assert JString.stringCharArray(["a", "b", "c"]) == "abc"
        assert JString.stringCharArray([]) == ""

    def test_string_bytes(self):
        assert JString.stringBytes(b"abc") == "abc"
        assert JString.stringBytes("ç".encode()) == "ç"

    def test_string_original(self):
        assert JString.stringOriginal("abc") == "abc"
        assert JString.stringOriginal(12) == "12"

    def test_string_char_array_offset_count(self):
        arr = list("abcdef")
        assert JString.stringCharArrayOffsetCount(arr, 1, 3) == "bcd"
        assert JString.stringCharArrayOffsetCount(arr, 0, 6) == "abcdef"
        assert JString.stringCharArrayOffsetCount(arr, 2, 0) == ""

    def test_from_bytes(self):
        assert JString.from_bytes(b"abc").value == "abc"
        assert JString.from_bytes("ç".encode("latin-1"), "latin-1").value == "ç"
        assert JString.from_bytes(bytearray(b"xy")).value == "xy"

    def test_from_bytes_tipo_invalido(self):
        with pytest.raises(TypeError) as e:
            JString.from_bytes("abc")
        assert "bytes" in str(e.value)

    def test_from_codepoints(self):
        assert JString.from_codepoints([97, 98, 99]).value == "abc"
        assert JString.from_codepoints([97, 98, 99], 1).value == "bc"
        assert JString.from_codepoints([97, 98, 99, 100], 1, 2).value == "bc"
        assert JString.from_codepoints([0x1F600]).value == EMOJI

    def test_from_codepoints_count_zero(self):
        assert JString.from_codepoints([97, 98], 0, 0).value == ""

    def test_from_bytes_range(self):
        assert JString.from_bytes_range(b"abcdef", 1, 3).value == "bcd"
        assert JString.from_bytes_range(b"abcdef", 0, 6).value == "abcdef"
        assert JString.from_bytes_range("çx".encode("latin-1"), 0, 1, "latin-1").value == "ç"

    def test_from_bytes_range_tipo_invalido(self):
        with pytest.raises(TypeError) as e:
            JString.from_bytes_range("abc", 0, 1)
        assert "bytes" in str(e.value)


# ======================================================================
# Acesso e tamanho
# ======================================================================

class TestAcesso:
    def test_code_units(self):
        assert S("ab")._code_units() == [97, 98]
        assert S("")._code_units() == []
        assert S(EMOJI)._code_units() == [0xD83D, 0xDE00]
        assert S("é")._code_units() == [0xE9]
        assert S("Ā")._code_units() == [0x100]

    def test_from_code_unit(self):
        assert S()._from_code_unit(97) == "a"

    def test_length(self):
        assert S("").length() == 0
        assert S("abc").length() == 3
        assert S(EMOJI).length() == 2

    def test_is_empty(self):
        assert S("").isEmpty() is True
        assert S("a").isEmpty() is False

    def test_char_at(self):
        s = S("abc")
        assert s.charAt(0) == "a"
        assert s.charAt(2) == "c"

    def test_char_at_fora(self):
        s = S("abc")
        with pytest.raises(IndexError):
            s.charAt(3)
        with pytest.raises(IndexError):
            s.charAt(-1)
        with pytest.raises(IndexError):
            S("").charAt(0)

    def test_code_point_at(self):
        assert S("abc").codePointAt(1) == 98
        assert S(EMOJI).codePointAt(0) == 0x1F600
        assert S(EMOJI).codePointAt(1) == 0xDE00
        assert S("a" + EMOJI).codePointAt(1) == 0x1F600

    def test_code_point_at_surrogate_isolado_nao_suportado(self):
        # DEFEITO/LIMITAÇÃO: substituto isolado não é codificável em UTF-16,
        # logo os ramos "sem par" de codePointAt são inalcançáveis
        # (fonte de mutantes equivalentes).
        with pytest.raises(UnicodeEncodeError):
            S("a\ud83d").codePointAt(1)

    def test_code_point_at_limites(self):
        with pytest.raises(IndexError):
            S("abc").codePointAt(3)
        with pytest.raises(IndexError):
            S("abc").codePointAt(-1)

    def test_code_point_before(self):
        assert S("abc").codePointBefore(1) == 97
        assert S("abc").codePointBefore(3) == 99
        assert S(EMOJI).codePointBefore(2) == 0x1F600
        assert S(EMOJI).codePointBefore(1) == 0xD83D
        assert S("a" + EMOJI).codePointBefore(3) == 0x1F600

    def test_code_point_before_surrogate_isolado_nao_suportado(self):
        with pytest.raises(UnicodeEncodeError):
            S("x\ude00").codePointBefore(2)

    def test_code_point_before_limites(self):
        with pytest.raises(IndexError):
            S("abc").codePointBefore(0)
        with pytest.raises(IndexError):
            S("abc").codePointBefore(4)
        with pytest.raises(IndexError):
            S("abc").codePointBefore(-1)

    def test_code_point_count(self):
        assert S("abc").codePointCount(0, 3) == 3
        assert S("abc").codePointCount(1, 2) == 1
        assert S("abc").codePointCount(2, 2) == 0
        assert S(EMOJI).codePointCount(0, 2) == 1
        assert S("a" + EMOJI + "b").codePointCount(0, 4) == 3

    def test_code_point_count_par_cortado(self):
        # endIndex corta o par substituto -> conta unidades soltas
        assert S(EMOJI).codePointCount(0, 1) == 1
        assert S(EMOJI + EMOJI).codePointCount(1, 3) == 2

    def test_code_point_count_limites(self):
        with pytest.raises(IndexError):
            S("abc").codePointCount(-1, 2)
        with pytest.raises(IndexError):
            S("abc").codePointCount(0, 4)
        with pytest.raises(IndexError):
            S("abc").codePointCount(2, 1)

    def test_offset_by_code_points(self):
        s = S("abcde")
        assert s.offsetByCodePoints(0, 3) == 3
        assert s.offsetByCodePoints(5, 0) == 5
        assert s.offsetByCodePoints(5, -2) == 3
        assert s.offsetByCodePoints(0, 5) == 5
        assert s.offsetByCodePoints(0, 0) == 0

    def test_offset_by_code_points_limites(self):
        s = S("abcde")
        with pytest.raises(IndexError) as e:
            s.offsetByCodePoints(-1, 0)
        assert "index" in str(e.value)
        with pytest.raises(IndexError):
            s.offsetByCodePoints(6, 0)
        with pytest.raises(IndexError) as e:
            s.offsetByCodePoints(0, 6)
        assert "codePointOffset" in str(e.value)
        with pytest.raises(IndexError):
            s.offsetByCodePoints(0, -1)

    def test_get_chars(self):
        dst = ["_"] * 6
        S("abcdef").getChars(1, 4, dst, 2)
        assert dst == ["_", "_", "b", "c", "d", "_"]

    def test_get_chars_exato(self):
        dst = ["_"] * 3
        S("abc").getChars(0, 3, dst, 0)
        assert dst == ["a", "b", "c"]
        dst = ["_"] * 3
        S("abc").getChars(1, 1, dst, 3)  # copia 0, dstBegin == len(dst)
        assert dst == ["_", "_", "_"]

    def test_get_chars_erros(self):
        dst = ["_"] * 3
        s = S("abcdef")
        with pytest.raises(IndexError, match="srcBegin out of bounds"):
            s.getChars(-1, 2, dst, 0)
        with pytest.raises(IndexError, match="greater than srcEnd"):
            s.getChars(3, 2, dst, 0)
        with pytest.raises(IndexError, match="srcEnd out of bounds"):
            s.getChars(0, 7, dst, 0)
        with pytest.raises(IndexError, match="dstBegin out of bounds"):
            s.getChars(0, 2, dst, -1)
        with pytest.raises(IndexError, match="destination array too small"):
            s.getChars(0, 3, dst, 1)

    def test_get_chars_src_end_igual_tamanho(self):
        dst = ["_"] * 6
        S("abcdef").getChars(0, 6, dst, 0)
        assert dst == list("abcdef")

    def test_to_char_array(self):
        assert S("abc").toCharArray() == ["a", "b", "c"]
        assert S("").toCharArray() == []

    def test_get_bytes(self):
        assert S("abc").getBytes() == b"abc"
        assert S("ç").getBytes() == "ç".encode("utf-8")
        assert S("ç").getBytes("latin-1") == b"\xe7"

    def test_get_bytes_encoding_invalido(self):
        with pytest.raises(ValueError, match="Unsupported encoding: xyz"):
            S("a").getBytes("xyz")


# ======================================================================
# Comparação
# ======================================================================

class TestComparacao:
    def test_equals(self):
        a = S("abc")
        assert a.equals(a) is True
        assert a.equals(S("abc")) is True
        assert a.equals(S("abd")) is False
        assert a.equals("abc") is False
        assert a.equals(None) is False

    def test_equals_ignore_case(self):
        assert S("Abc").equalsIgnoreCase("aBC") is True
        assert S("Abc").equalsIgnoreCase(S("aBC")) is True
        assert S("abc").equalsIgnoreCase("abd") is False
        assert S("abc").equalsIgnoreCase(None) is False
        assert S("abc").equalsIgnoreCase("abcd") is False

    def test_compare_to(self):
        assert S("abc").compareTo("abc") == 0
        assert S("abc").compareTo(S("abd")) == -1
        assert S("abd").compareTo("abc") == 1
        assert S("a").compareTo("c") == -2
        assert S("abc").compareTo("ab") == 1
        assert S("ab").compareTo("abc") == -1
        assert S("abcde").compareTo("ab") == 3
        assert S("").compareTo("") == 0
        assert S("").compareTo("abc") == -3

    def test_compare_to_primeira_diferenca(self):
        # diferença no meio deve prevalecer sobre o tamanho
        assert S("axc").compareTo("abcdef") == ord("x") - ord("b")

    def test_compare_to_ignore_case(self):
        assert S("ABC").compareToIgnoreCase("abc") == 0
        assert S("abc").compareToIgnoreCase("ABD") == -1
        assert S("ABD").compareToIgnoreCase("abc") == 1
        assert S("abc").compareToIgnoreCase("AB") == 1
        assert S("AB").compareToIgnoreCase("abc") == -1
        assert S("").compareToIgnoreCase("") == 0

    def test_compare_to_ignore_case_primeira_diferenca(self):
        assert S("Axc").compareToIgnoreCase("abcdef") == ord("X") - ord("B")

    def test_compare_to_ignore_case_upper_igual_lower_diferente(self):
        # 'ı' vs 'i': upper() iguais ('I'), lower() diferentes
        assert S("ı").compareToIgnoreCase("i") == ord("ı") - ord("i")
        assert S("i").compareToIgnoreCase("ı") == ord("i") - ord("ı")

    def test_content_equals(self):
        assert S("abc").contentEquals("abc") is True
        assert S("abc").contentEquals(S("abc")) is True
        assert S("abc").contentEquals("abd") is False
        assert S("abc").contentEquals(None) is False

    def test_region_matches_sem_ignore(self):
        s = S("Hello World")
        assert s.regionMatches(6, "World", 0, 5) is True
        assert s.regionMatches(6, "world", 0, 5) is False
        assert s.regionMatches(0, S("Hello"), 0, 5) is True
        assert s.regionMatches(0, "Hello", 0, 0) is True

    def test_region_matches_com_ignore(self):
        s = S("Hello World")
        assert s.regionMatches(True, 6, "world", 0, 5) is True
        assert s.regionMatches(False, 6, "world", 0, 5) is False
        assert s.regionMatches(True, 6, "WORLD", 0, 5) is True
        assert s.regionMatches(True, 6, "WORLX", 0, 5) is False

    def test_region_matches_limites(self):
        s = S("Hello")
        assert s.regionMatches(-1, "Hello", 0, 2) is False
        assert s.regionMatches(0, "Hello", -1, 2) is False
        assert s.regionMatches(0, "Hello", 0, -1) is False
        assert s.regionMatches(1, "Hello", 0, 5) is False   # toffset > len-length
        assert s.regionMatches(0, "Hello", 1, 5) is False   # ooffset > len-length
        assert s.regionMatches(0, "Hello", 0, 5) is True    # exatamente no limite
        assert s.regionMatches(0, "Hello", 0, 6) is False
        assert s.regionMatches(4, "Hello", 0, 1) is False   # 'o' vs 'H'
        assert s.regionMatches(4, "xxxxo", 4, 1) is True

    def test_region_matches_diferenca_no_meio_e_fim(self):
        s = S("abcdef")
        assert s.regionMatches(0, "abXdef", 0, 6) is False
        assert s.regionMatches(0, "abcdeX", 0, 6) is False
        assert s.regionMatches(0, "Xbcdef", 0, 6) is False

    def test_hash_code(self):
        assert S("").hashCode() == 0
        assert S("abc").hashCode() == 96354
        assert S("polygenelubricants").hashCode() == -2147483648


# ======================================================================
# Busca
# ======================================================================

class TestBusca:
    def test_index_of(self):
        s = S("hello world")
        assert s.index_of("o") == 4
        assert s.index_of(ord("o")) == 4
        assert s.index_of("o", 5) == 7
        assert s.index_of("world") == 6
        assert s.index_of("z") == -1
        assert s.index_of("o", 8) == -1
        assert s.index_of("o", 0) == 4

    def test_index_of_string_from(self):
        s = S("abcabc")
        assert s.index_of_string_from("bc", 0) == 1
        assert s.index_of_string_from("bc", 2) == 4
        assert s.index_of_string_from("bc", 5) == -1

    def test_last_index_of(self):
        s = S("hello world")
        assert s.last_index_of("o") == 7
        assert s.last_index_of(ord("o")) == 7
        assert s.last_index_of("o", 6) == 4
        assert s.last_index_of("o", 7) == 7
        assert s.last_index_of("o", 3) == -1
        assert s.last_index_of("z") == -1
        assert s.last_index_of("h", 0) == 0

    def test_last_index_of_str(self):
        s = S("abcabc")
        assert s.lastIndexOf("bc") == 4
        assert s.lastIndexOf("z") == -1
        assert s.lastIndexOf("bc", 4) == 4
        assert s.lastIndexOf("bc", 3) == 1
        assert s.lastIndexOf("bc", 0) == -1
        assert s.lastIndexOf("abc", 0) == 0
        assert s.lastIndexOf("abc", 100) == 3
        assert s.lastIndexOf("a", 5) == 3

    def test_last_index_of_str_from_negativo(self):
        assert S("abc").lastIndexOf("a", -1) == -1

    def test_last_index_of_vazio(self):
        s = S("abc")
        assert s.lastIndexOf("") == 3
        assert s.lastIndexOf("", 1) == 1
        assert s.lastIndexOf("", 10) == 3
        assert s.lastIndexOf("", 0) == 0

    def test_last_index_of_str_maior_que_string(self):
        assert S("ab").lastIndexOf("abc", 5) == -1

    def test_contains(self):
        assert S("hello").contains("ell") is True
        assert S("hello").contains(S("ell")) is True
        assert S("hello").contains("xyz") is False
        assert S("hello").contains("") is True

    def test_starts_with(self):
        s = S("hello")
        assert s.startsWith("he") is True
        assert s.startsWith("lo") is False
        assert s.startsWith("ll", 2) is True
        assert s.startsWith("he", 1) is False
        assert s.startsWith("", 5) is True
        assert s.startsWith("", 6) is False
        assert s.startsWith("h", -1) is False
        assert s.startsWith("o", 4) is True

    def test_ends_with(self):
        s = S("hello")
        assert s.endsWith("lo") is True
        assert s.endsWith("he") is False
        assert s.endsWith("") is True
        assert s.endsWith("hello") is True
        assert s.endsWith("xhello") is False


# ======================================================================
# Transformação
# ======================================================================

class TestTransformacao:
    def test_substring(self):
        s = S("hello")
        assert s.substring(0).value == "hello"
        assert s.substring(2).value == "llo"
        assert s.substring(5).value == ""

    def test_substring_erros(self):
        with pytest.raises(IndexError, match="start"):
            S("hello").substring(-1)
        with pytest.raises(IndexError, match="start"):
            S("hello").substring(6)

    def test_substring_range(self):
        s = S("hello")
        assert s.substring_range(1, 3).value == "el"
        assert s.substring_range(0, 5).value == "hello"
        assert s.substring_range(2, 2).value == ""
        assert s.substring_range(5, 5).value == ""

    def test_substring_range_erros(self):
        s = S("hello")
        with pytest.raises(IndexError, match="start"):
            s.substring_range(-1, 2)
        with pytest.raises(IndexError, match="start"):
            s.substring_range(6, 6)
        with pytest.raises(IndexError, match="end"):
            s.substring_range(0, -1)
        with pytest.raises(IndexError, match="end"):
            s.substring_range(0, 6)
        with pytest.raises(IndexError, match="end"):
            s.substring_range(3, 2)

    def test_sub_sequence(self):
        s = S("hello")
        assert s.subSequence(1, 3).value == "el"
        assert s.subSequence(0, 5).value == "hello"
        assert s.subSequence(5, 5).value == ""
        assert s.subSequence(2, 2).value == ""

    def test_sub_sequence_erros(self):
        s = S("hello")
        with pytest.raises(IndexError, match="start"):
            s.subSequence(-1, 2)
        with pytest.raises(IndexError, match="start"):
            s.subSequence(6, 6)
        with pytest.raises(IndexError, match="end"):
            s.subSequence(0, -1)
        with pytest.raises(IndexError, match="end"):
            s.subSequence(0, 6)
        with pytest.raises(IndexError, match="end"):
            s.subSequence(3, 2)

    def test_concat(self):
        assert S("ab").concat("cd").value == "abcd"
        assert S("ab").concat(S("cd")).value == "abcd"
        assert S("ab").concat("").value == "ab"

    def test_concat_none(self):
        with pytest.raises(TypeError, match="None"):
            S("ab").concat(None)

    def test_replace(self):
        assert S("banana").replace("a", "o").value == "bonono"
        assert S("banana").replace(S("an"), S("AN")).value == "bANANa"
        assert S("banana").replace("x", "y").value == "banana"
        assert S("banana").replace("a", "").value == "bnn"

    def test_replace_tipo_invalido(self):
        with pytest.raises(TypeError):
            S("abc").replace(1, "x")
        with pytest.raises(TypeError):
            S("abc").replace("a", 1)

    def test_to_lower_upper(self):
        assert S("AbC").toLowerCase().value == "abc"
        assert S("AbC").toUpperCase().value == "ABC"

    def test_trim(self):
        assert S("  abc  ").trim().value == "abc"
        assert S("abc").trim().value == "abc"
        assert S("   ").trim().value == ""
        assert S("").trim().value == ""
        assert S("\t\n abc \r\n").trim().value == "abc"
        assert S(" a b ").trim().value == "a b"
        assert S("\x00abc\x1f").trim().value == "abc"

    def test_trim_limite_32(self):
        # espaço (32) é removido, '!' (33) não
        assert S(" !").trim().value == "!"
        assert S("! ").trim().value == "!"
        assert S("!").trim().value == "!"

    def test_trim_so_um_lado(self):
        assert S("  abc").trim().value == "abc"
        assert S("abc  ").trim().value == "abc"

    def test_intern(self):
        a = S("hello world").intern()
        assert a.value == "hello world"
        assert isinstance(a, JString)


# ======================================================================
# Expressões regulares
# ======================================================================

class TestRegex:
    def test_matches(self):
        assert S("abc123").matches(r"[a-z]+\d+") is True
        assert S("abc123x").matches(r"[a-z]+\d+") is False
        assert S("1abc123").matches(r"[a-z]+\d+") is False
        assert S("").matches("") is True

    def test_matches_regex_invalida(self):
        with pytest.raises(ValueError, match="PatternSyntaxException"):
            S("abc").matches("[")

    def test_replace_first(self):
        assert S("aaa").replaceFirst("a", "b").value == "baa"
        assert S("a1b2").replaceFirst(r"\d", "#").value == "a#b2"
        assert S("abc").replaceFirst("x", "y").value == "abc"

    def test_replace_first_invalida(self):
        with pytest.raises(ValueError, match="PatternSyntaxException"):
            S("abc").replaceFirst("[", "x")

    def test_replace_all(self):
        assert S("aaa").replaceAll("a", "b").value == "bbb"
        assert S("a1b2").replaceAll(r"\d", "#").value == "a#b#"
        assert S("abc").replaceAll("x", "y").value == "abc"

    def test_replace_all_invalida(self):
        with pytest.raises(ValueError, match="PatternSyntaxException"):
            S("abc").replaceAll("[", "x")

    def test_split_basico(self):
        r = S("a,b,c").split(",")
        assert [p.value for p in r] == ["a", "b", "c"]
        assert all(isinstance(p, JString) for p in r)

    def test_split_remove_vazios_finais(self):
        assert [p.value for p in S("a,b,,").split(",")] == ["a", "b"]
        assert [p.value for p in S("a,b,,").split(",", 0)] == ["a", "b"]

    def test_split_mantem_vazios_do_inicio(self):
        assert [p.value for p in S(",a,b").split(",")] == ["", "a", "b"]

    def test_split_so_separadores(self):
        # parts = ['', '', ''] -> remove até sobrar um elemento
        assert [p.value for p in S(",,").split(",")] == [""]

    def test_split_limit_1(self):
        assert [p.value for p in S("a,b,c").split(",", 1)] == ["a,b,c"]

    def test_split_limit_positivo(self):
        assert [p.value for p in S("a,b,c,d").split(",", 2)] == ["a", "b,c,d"]
        assert [p.value for p in S("a,b,c,d").split(",", 3)] == ["a", "b", "c,d"]
        # limit > 1 mantém vazios finais
        assert [p.value for p in S("a,b,,").split(",", 5)] == ["a", "b", "", ""]

    def test_split_limit_negativo(self):
        assert [p.value for p in S("a,b,,").split(",", -1)] == ["a", "b", "", ""]

    def test_split_sem_separador(self):
        assert [p.value for p in S("abc").split(",")] == ["abc"]

    def test_split_regex(self):
        assert [p.value for p in S("a1b22c").split(r"\d+")] == ["a", "b", "c"]

    def test_split_invalida(self):
        with pytest.raises(ValueError, match="PatternSyntaxException"):
            S("abc").split("[")


# ======================================================================
# Métodos estáticos
# ======================================================================

class TestEstaticos:
    def test_value_of_int(self):
        assert JString.valueOfInt(42).value == "42"
        assert JString.valueOfInt(-1).value == "-1"

    def test_value_of_float(self):
        assert JString.valueOfFloat(1.5).value == "1.5"

    def test_value_of_bool(self):
        # DEFEITO: Java retorna "true"/"false"; aqui "True"/"False"
        assert JString.valueOfBool(True).value == "True"
        assert JString.valueOfBool(False).value == "False"

    def test_value_of_char(self):
        assert JString.valueOfChar("a").value == "a"

    def test_value_of_char_invalido(self):
        with pytest.raises(ValueError, match="caractere"):
            JString.valueOfChar("ab")
        with pytest.raises(ValueError):
            JString.valueOfChar("")

    def test_value_of_char_array(self):
        assert JString.valueOfCharArray(["a", "b"]).value == "ab"
        assert JString.valueOfCharArray([]).value == ""

    def test_value_of_object(self):
        assert JString.valueOfObject(None).value == "null"
        assert JString.valueOfObject(12).value == "12"
        assert JString.valueOfObject([1, 2]).value == "[1, 2]"

    def test_copy_value_of(self):
        assert JString.copyValueOf(["x", "y"]).value == "xy"

    def test_format(self):
        assert JString.format("%s-%d", "a", 5).value == "a-5"
        assert JString.format("sem args").value == "sem args"

    def test_join(self):
        assert JString.join(",", "a", "b", "c").value == "a,b,c"
        assert JString.join(",", 1, 2).value == "1,2"
        assert JString.join(",").value == ""
        assert JString.join("-", "só").value == "só"
