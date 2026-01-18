"""Tests for the markupflow Document class.

This module contains tests specifically for the Document class.
Most functionality is tested in test_fragment.py since Document inherits from Fragment.
"""

from markupflow import (
    Document,
    document,
)


def test_document_inherits_from_fragment():
    """Test that Document is a proper subclass with all Fragment functionality."""
    doc = Document()

    with doc.tag("html"):
        with doc.tag("head"):
            with doc.tag("title"):
                doc.text("Test Page")
        with doc.tag("body"):
            with doc.tag("h1"):
                doc.text("Hello World")

    html = doc.render()
    expected = "<html><head><title>Test Page</title></head><body><h1>Hello World</h1></body></html>"
    assert html == expected


def test_document_convenience_function():
    """Test the convenience document() function."""
    doc = document()

    with doc.tag("span"):
        doc.text("Test")

    html = doc.render()
    expected = "<span>Test</span>"
    assert html == expected


def test_document_with_fragments():
    """Test that Document can use fragments."""
    from markupflow import Fragment

    # Create a reusable fragment
    header = Fragment()
    with header.tag("header"):
        with header.h1():
            header.text("My Site")

    # Use it in a document
    doc = Document()
    with doc.tag("html"):
        with doc.tag("body"):
            doc.fragment(header)
            with doc.tag("main"):
                doc.text("Content")

    html = doc.render()
    assert "<header><h1>My Site</h1></header>" in html
    assert "<main>Content</main>" in html
