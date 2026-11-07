"""The ordered signs of a word or sentence, and progress through them."""

from dataclasses import dataclass


@dataclass
class SignQueue:
    text: str
    positions: list  # index into text of each sign, skipping spaces
    current: int = 0

    def is_done(self):
        return self.current >= len(self.positions)

    def current_sign(self):
        return None if self.is_done() else self.text[self.positions[self.current]]

    def advance(self):
        if not self.is_done():
            self.current += 1


def make_queue(text):
    text = " ".join(text.upper().split())
    return SignQueue(text, [index for index, char in enumerate(text) if char != " "])


def missing_signs(text, sign_names):
    """Signs the text needs that have no recorded template."""
    return sorted({char for char in text.upper() if char != " " and char not in sign_names})
