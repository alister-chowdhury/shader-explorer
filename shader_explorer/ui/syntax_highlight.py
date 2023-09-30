# THIS IS VERY TODO


from PySide6.QtGui import QSyntaxHighlighter
from PySide6.QtCore import Qt, QRegularExpression


import re

_CSTYLE_COMMENTS_EXPR = re.compile(
    # Single line
    r"//(?:\\\n|.)*$"
    # Multi line
    r"|/\*(?:.|\n)*?\*/",
    flags=re.MULTILINE,
)

_SEMICOLON_COMMENTS_EXPR = QRegularExpression(r";+$")

_VAR_EXPR = QRegularExpression(r"\b[A-Za-z_][A-Za-z_0-9]*")

_SPIRV_VAR_EXPR = QRegularExpression(r"\b%[A-Za-z_0-9]+\b")

_NUMERIC_EXPR = QRegularExpression(
    r"\b[-\+]?(?:"
    # Decimal / float
    r"(?:\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)"
    r"|(?:\.\d+([eE][+-]?\d+)?)"
    # Hex / hex float literal
    r"|(?:0[xX][0-9a-fA-F]+(?:(?:\.[0-9]*)?p[+-]?[0-9]+)?)"
    # Binary
    r"|(?:0[bB][01]+)"
    # Oct
    r"|(?:0[oO][0-7]+)"
    r")\b"
)


_BLOCK_STATE_END_NORMAL = 0
_BLOCK_STATE_END_CSINGLE_COMMENT = 1
_BLOCK_STATE_END_CMULTI_COMMENT = 2


def _comment_filter_c(state, ranges, allow_multiline=True):
    """Filter comment ranges out.

    Args:
        state (_CurrentLineState): Current state.
        ranges (iterable[int, int]): Valid ranges.
        allow_multiline (bool): Allow multiline comments.
            (Default: True).

    Yields:
        tuple(int, int): Ranges to process further.
    """
    for start, end in ranges:
        while start < end:
            found_single = state.text.find("//", start, end)

            if allow_multiline:
                found_multi = state.text.find("/*", start, end)
            else:
                found_multi = -1
            if found_single == -1 and found_multi == -1:
                yield (start, end)
                break
            # We got comment in a comment situation going on
            if found_multi != -1 and found_single != -1:
                if found_multi < found_single:
                    found_single = -1
                else:
                    found_multi = -1
            # One will be -1, the other valid index
            comment_start = found_single + found_multi + 1
            if start != comment_start:
                yield (start, comment_start)
            if found_single != -1:
                if state.text.endswith("\\"):
                    state.current_state = _BLOCK_STATE_END_CSINGLE_COMMENT
                state.col_ranges.append(
                    (comment_start, len(state.text), "comment")
                )
                return
            else:
                found_end = state.text.find("*/", found_multi + 2, end)
                if found_end == -1:
                    state.current_state = _BLOCK_STATE_END_CMULTI_COMMENT
                    state.col_ranges.append(
                        (comment_start, len(state.text), "comment")
                    )
                    return
                else:
                    start = found_end + 2
                    state.col_ranges.append((comment_start, start, "comment"))


class _CurrentLineState(object):
    def __init__(self, text, prev_state):
        self.text = text
        self.prev_state = prev_state
        self.current_state = _BLOCK_STATE_END_NORMAL
        self.col_ranges = []


class SyntaxHighligher(QSyntaxHighlighter):
    def __init__(self, text_document):
        self._rules = None
        super(SyntaxHighligher, self).__init__(text_document)

    def set_rules(self, rules):
        self._rules = rules
        # todo signal dirty

    def highlightBlock(self, text):
        state = _CurrentLineState(text, self.previousBlockState())
        ranges = [(0, len(text))]

        # Last line had a ctyle // comment, with a \ at the end
        # keep this line in comment, and continue if it also ends
        # with a \ at the end.
        if state.prev_state == _BLOCK_STATE_END_CSINGLE_COMMENT:
            if text.endswith("\\"):
                state.current_state = _BLOCK_STATE_END_CSINGLE_COMMENT
            state.col_ranges.append((0, len(text), "comment"))
            ranges = []
        # We're in a ctyle /* */ comment, keep this in comment
        # if no */ is detected.
        if state.prev_state == _BLOCK_STATE_END_CMULTI_COMMENT:
            found = text.find("*/")
            if found == -1:
                state.current_state = _BLOCK_STATE_END_CMULTI_COMMENT
                state.col_ranges.append((0, len(text), "comment"))
                ranges = []
            else:
                found += 2
                state.col_ranges.append((0, found, "comment"))
                if found == len(text):
                    ranges = []
                else:
                    ranges = [(found, len(text))]
        single_c_style = True
        multi_c_style = True

        ranges = _comment_filter_c(state, ranges)

        # Collapse the generators
        for _ in ranges:
            pass
        for s, e, _ in state.col_ranges:
            self.setFormat(s, e - s, Qt.green)
        self.setCurrentBlockState(state.current_state)


from PySide6.QtWidgets import *
from PySide6.QtGui import QPalette, QFontDatabase


class Tester(QMainWindow):
    def __init__(self, parent=None):
        super(Tester, self).__init__(parent)

        self.central = QWidget(self)
        self.setCentralWidget(self.central)

        self.horizontal_layout = QHBoxLayout(self.central)

        self.resize(500, 500)
        self._editor = QTextEdit(self.central)

        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        font.setPointSize(32)
        self._editor.setFont(font)
        self._editor.setSizePolicy(
            QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        )

        p = self._editor.palette()
        p.setColor(QPalette.Base, Qt.black)
        p.setColor(QPalette.Text, Qt.white)
        self._editor.setPalette(p)
        # self._editor.resize(500, 500)
        self._h = SyntaxHighligher(self._editor.document())

        self.horizontal_layout.addWidget(self._editor)


qapp = QApplication([])
x = Tester()
x.show()
qapp.exec()
