"""Output formats for an audit result: Marp deck, CSV spreadsheet."""

from como_tag_audit.reporters.deck import render_deck
from como_tag_audit.reporters.spreadsheet import render_csv

__all__ = ["render_csv", "render_deck"]
