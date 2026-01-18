"""Tests for the markupflow Document class.

This module contains comprehensive tests to verify that the markupflow
library produces correct HTML output and handles various edge cases properly.
"""

import pytest

from markupflow import (
    Document,
    Fragment,
    MarkupFlowError,
    NoTagContextError,
    TagAlreadyOpenedError,
    UnclosedTagsError,
    document,
)


def test_simple_document():
    """Test basic document creation and rendering."""
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


def test_attributes():
    """Test attribute handling including special cases."""
    doc = Document()

    with doc.tag("div", class_="container", data_value="123", id="main"):
        with doc.tag("img", src="test.jpg", alt="Test Image"):
            pass  # Self-closing tag

    html = doc.render()
    # Note: img is self-closing
    expected = '<div class="container" data-value="123" id="main"><img src="test.jpg" alt="Test Image" /></div>'
    assert html == expected


def test_text_escaping():
    """Test that text content is properly escaped."""
    doc = Document()

    with doc.tag("p"):
        doc.text('Hello & <world> "test"')

    html = doc.render()
    expected = '<p>Hello &amp; &lt;world&gt; "test"</p>'
    assert html == expected


def test_attribute_escaping():
    """Test that attribute values are properly escaped."""
    doc = Document()

    with doc.tag("div", title='Test & "quoted" <value>'):
        pass

    html = doc.render()
    expected = '<div title="Test &amp; &quot;quoted&quot; &lt;value&gt;"></div>'
    assert html == expected


def test_raw_content():
    """Test raw HTML insertion."""
    doc = Document()

    with doc.tag("div"):
        doc.raw("<em>Already formatted</em>")
        doc.text(" and escaped")

    html = doc.render()
    expected = "<div><em>Already formatted</em> and escaped</div>"
    assert html == expected


def test_self_closing_tags():
    """Test that self-closing tags are handled correctly."""
    doc = Document()

    with doc.tag("div"):
        with doc.tag("br"):
            pass
        with doc.tag("img", src="test.jpg"):
            pass
        with doc.tag("input", type="text", name="test"):
            pass

    html = doc.render()
    expected = (
        '<div><br /><img src="test.jpg" /><input type="text" name="test" /></div>'
    )
    assert html == expected


def test_attribute_name_conversion():
    """Test attribute name conversion from Python to HTML."""
    doc = Document()

    with doc.tag(
        "div",
        class_="test",  # class_ -> class
        data_value="123",  # data_value -> data-value
        aria_label="button",
    ):  # aria_label -> aria-label
        pass

    html = doc.render()
    expected = '<div class="test" data-value="123" aria-label="button"></div>'
    assert html == expected


def test_reserved_keyword_attributes():
    """Test that reserved Python keywords work as HTML attributes."""
    doc = Document()

    # Test 'for' attribute - common with label tags
    with doc.label(for_="username", class_="form-label"):
        doc.text("Username:")

    with doc.input(type="text", id="username", name="username"):
        pass

    html = doc.render()
    expected = '<label for="username" class="form-label">Username:</label><input type="text" id="username" name="username" />'
    assert html == expected


def test_document_reuse():
    """Test that documents can be cleared and reused."""
    doc = Document()

    # First use
    with doc.tag("p"):
        doc.text("First")
    html1 = doc.render()

    # Clear and reuse
    doc.clear()
    with doc.tag("h1"):
        doc.text("Second")
    html2 = doc.render()

    assert html1 == "<p>First</p>"
    assert html2 == "<h1>Second</h1>"


def test_convenience_function():
    """Test the convenience document() function."""
    doc = document()

    with doc.tag("span"):
        doc.text("Test")

    html = doc.render()
    expected = "<span>Test</span>"
    assert html == expected


def test_tag_shortcuts():
    """Test that tag shortcuts work correctly."""
    doc = Document()

    # Test common tag shortcuts
    with doc.div(class_="container"):
        with doc.h1(id="title"):
            doc.text("Title")
        with doc.p(class_="text"):
            doc.text("Paragraph")
        with doc.ul():
            with doc.li():
                doc.text("Item 1")
            with doc.li():
                doc.text("Item 2")
        with doc.button(type="submit", disabled="true"):
            doc.text("Submit")
        # Test self-closing shortcuts
        doc.br()
        doc.hr()
        doc.img(src="test.jpg", alt="Test")

    html = doc.render()
    expected = (
        '<div class="container">'
        '<h1 id="title">Title</h1>'
        '<p class="text">Paragraph</p>'
        "<ul><li>Item 1</li><li>Item 2</li></ul>"
        '<button type="submit" disabled="true">Submit</button>'
        '<br /><hr /><img src="test.jpg" alt="Test" />'
        "</div>"
    )

    assert html == expected


def test_shortcuts_equivalent_to_tag():
    """Test that shortcuts produce identical output to tag() method."""
    doc1 = Document()
    doc2 = Document()

    # Using shortcuts
    with doc1.div(class_="test"):
        with doc1.h1():
            doc1.text("Hello")
        with doc1.p():
            doc1.text("World")

    # Using tag() method
    with doc2.tag("div", class_="test"):
        with doc2.tag("h1"):
            doc2.text("Hello")
        with doc2.tag("p"):
            doc2.text("World")

    html1 = doc1.render()
    html2 = doc2.render()

    assert html1 == html2


def test_attr_function():
    """Test the attr() function for dynamic attribute addition."""
    doc = Document()

    # Basic attr() usage
    with doc.div():
        doc.attr("class", "container")
        doc.attr("id", "main")
        doc.text("Content")

    html = doc.render()
    expected = '<div class="container" id="main">Content</div>'
    assert html == expected


def test_attr_conditional_logic():
    """Test attr() with conditional logic - the main use case."""
    doc = Document()

    user_is_admin = True
    show_tooltip = False

    with doc.div():
        if user_is_admin:
            doc.attr("class", "admin-panel")
            doc.attr("data-role", "administrator")
        if show_tooltip:
            doc.attr("title", "This is a tooltip")
        doc.text("Admin Panel")

    html = doc.render()
    expected = '<div class="admin-panel" data-role="administrator">Admin Panel</div>'
    assert html == expected

    # Test with different conditions
    doc.clear()
    user_is_admin = False
    show_tooltip = True

    with doc.div():
        if user_is_admin:
            doc.attr("class", "admin-panel")
            doc.attr("data-role", "administrator")
        if show_tooltip:
            doc.attr("title", "This is a tooltip")
        doc.text("Regular Panel")

    html = doc.render()
    expected = '<div title="This is a tooltip">Regular Panel</div>'
    assert html == expected


def test_attr_with_initial_attributes():
    """Test attr() when the tag already has initial attributes."""
    doc = Document()

    with doc.div(id="container", data_type="widget"):
        doc.attr("class", "active")
        doc.attr("data-value", "123")
        doc.text("Widget")

    html = doc.render()
    expected = '<div id="container" data-type="widget" class="active" data-value="123">Widget</div>'
    assert html == expected


def test_attr_attribute_name_conversion():
    """Test that attr() properly converts attribute names."""
    doc = Document()

    with doc.div():
        doc.attr("class_", "test")
        doc.attr("data_value", "123")
        doc.attr("aria_label", "button")
        doc.attr("for_", "username")
        doc.text("Content")

    html = doc.render()
    expected = '<div class="test" data-value="123" aria-label="button" for="username">Content</div>'
    assert html == expected


def test_attr_value_escaping():
    """Test that attr() properly escapes attribute values."""
    doc = Document()

    with doc.div():
        doc.attr("title", 'Test & "quoted" <value>')
        doc.attr("data-info", "Line 1\nLine 2")
        doc.text("Content")

    html = doc.render()
    expected = '<div title="Test &amp; &quot;quoted&quot; &lt;value&gt;" data-info="Line 1\nLine 2">Content</div>'
    assert html == expected


def test_attr_error_cases():
    """Test error cases for attr() function."""
    doc = Document()

    # Test calling attr() outside of a tag context
    with pytest.raises(NoTagContextError, match="No current tag context"):
        doc.attr("class", "test")

    # Test calling attr() after tag has been opened
    with doc.div():
        doc.text("This opens the tag")
        with pytest.raises(TagAlreadyOpenedError, match="Tag already opened"):
            doc.attr("class", "test")


def test_attr_with_nested_tags():
    """Test attr() with nested tag structures."""
    doc = Document()

    with doc.div():
        doc.attr("class", "outer")

        with doc.p():
            doc.attr("class", "inner")
            doc.text("Paragraph")

        doc.text("Outer text")

    html = doc.render()
    expected = '<div class="outer"><p class="inner">Paragraph</p>Outer text</div>'
    assert html == expected


def test_attr_with_shortcuts():
    """Test attr() works with tag shortcuts."""
    doc = Document()

    with doc.div():
        doc.attr("class", "container")

        with doc.h1():
            doc.attr("id", "title")
            doc.text("Title")

        with doc.p():
            doc.attr("class", "description")
            doc.text("Description")

    html = doc.render()
    expected = '<div class="container"><h1 id="title">Title</h1><p class="description">Description</p></div>'
    assert html == expected


def test_complex_nested_structure():
    """Test complex nested HTML structure similar to benchmark tests."""
    doc = Document()

    with doc.tag("html", lang="en"):
        with doc.tag("head"):
            with doc.tag("title"):
                doc.text("Complex Page")
            with doc.tag("meta", charset="utf-8"):
                pass
        with doc.tag("body"):
            with doc.tag("nav", class_="navigation"):
                with doc.tag("ul"):
                    for item in ["Home", "About", "Contact"]:
                        with doc.tag("li"):
                            with doc.tag("a", href=f"#{item.lower()}"):
                                doc.text(item)
            with doc.tag("main"):
                with doc.tag("h1"):
                    doc.text("Welcome")
                with doc.tag("p"):
                    doc.text("This is a test page.")
                    doc.text("Welcome")
                with doc.tag("p"):
                    doc.text("This is a test page.")

    html = doc.render()

    # Verify it contains expected elements
    assert '<html lang="en">' in html
    assert '<meta charset="utf-8" />' in html
    assert '<nav class="navigation">' in html
    assert '<a href="#home">Home</a>' in html
    assert '<a href="#about">About</a>' in html
    assert '<a href="#contact">Contact</a>' in html


def test_unclosed_tags_error():
    """Test that unclosed tags raise an appropriate error."""
    doc = Document()

    # Manually create unclosed tags by not using context managers properly
    doc._tag_stack.append("html")
    doc._tag_stack.append("head")

    # Missing closing tags for head and html
    with pytest.raises(UnclosedTagsError, match="Unclosed tags"):
        doc.render()


def test_exception_hierarchy():
    """Test that all markupflow exceptions inherit from MarkupFlowError."""
    doc = Document()

    # Test that NoTagContextError is caught by MarkupFlowError
    with pytest.raises(MarkupFlowError):
        doc.attr("class", "test")

    # Test that TagAlreadyOpenedError is caught by MarkupFlowError
    with doc.div():
        doc.text("This opens the tag")
        with pytest.raises(MarkupFlowError):
            doc.attr("class", "test")

    # Test that UnclosedTagsError is caught by MarkupFlowError
    doc._tag_stack.append("html")
    with pytest.raises(MarkupFlowError):
        doc.render()


def test_none_content_handling():
    """Test that None content is handled gracefully."""
    doc = Document()

    with doc.tag("div"):
        doc.text(None)  # Should be ignored
        doc.attr("title", None)  # Should be ignored (not rendered)
        doc.text("Some text")

    html = doc.render()
    expected = "<div >Some text</div>"  # No title attribute when value is None
    assert html == expected


def test_classes_function():
    """Test the classes() function for adding classes to current tag."""
    doc = Document()

    # Basic classes() usage
    with doc.div():
        doc.classes("container")
        doc.text("Content")

    html = doc.render()
    expected = '<div class="container">Content</div>'
    assert html == expected


def test_classes_appends_to_existing():
    """Test that classes() appends to existing classes."""
    doc = Document()

    # With initial class
    with doc.div(class_="container"):
        doc.classes("active")
        doc.classes("highlighted")
        doc.text("Content")

    html = doc.render()
    expected = '<div class="container active highlighted">Content</div>'
    assert html == expected


def test_classes_multiple_calls():
    """Test multiple classes() calls."""
    doc = Document()

    with doc.div():
        doc.classes("container")
        doc.classes("fluid")
        doc.classes("bordered")
        doc.text("Content")

    html = doc.render()
    expected = '<div class="container fluid bordered">Content</div>'
    assert html == expected


def test_classes_with_conditional_logic():
    """Test classes() with conditional logic - the main use case."""
    doc = Document()

    is_admin = True
    is_active = True
    is_highlighted = False

    with doc.div(class_="panel"):
        if is_admin:
            doc.classes("admin")
        if is_active:
            doc.classes("active")
        if is_highlighted:
            doc.classes("highlighted")
        doc.text("Panel Content")

    html = doc.render()
    expected = '<div class="panel admin active">Panel Content</div>'
    assert html == expected


def test_classes_with_nested_tags():
    """Test classes() with nested tag structures."""
    doc = Document()

    with doc.div(class_="outer"):
        doc.classes("container")

        with doc.p():
            doc.classes("inner")
            doc.classes("text")
            doc.text("Paragraph")

        doc.text("Outer text")

    html = doc.render()
    expected = '<div class="outer container"><p class="inner text">Paragraph</p>Outer text</div>'
    assert html == expected


def test_classes_error_cases():
    """Test error cases for classes() function."""
    doc = Document()

    # Test calling classes() outside of a tag context
    with pytest.raises(NoTagContextError, match="No current tag context"):
        doc.classes("test")

    # Test calling classes() after tag has been opened
    with doc.div():
        doc.text("This opens the tag")
        with pytest.raises(TagAlreadyOpenedError, match="Tag already opened"):
            doc.classes("test")


def test_classes_with_shortcuts():
    """Test classes() works with tag shortcuts."""
    doc = Document()

    with doc.div(class_="container"):
        doc.classes("fluid")

        with doc.h1():
            doc.classes("title")
            doc.classes("large")
            doc.text("Title")

        with doc.p(class_="text"):
            doc.classes("muted")
            doc.text("Description")

    html = doc.render()
    expected = '<div class="container fluid"><h1 class="title large">Title</h1><p class="text muted">Description</p></div>'
    assert html == expected


def test_fragment_basic():
    """Test basic fragment creation and rendering."""
    fragment = Fragment()

    with fragment.div(class_="callout"):
        with fragment.strong():
            fragment.text("Warning")

    html = fragment.render()
    expected = '<div class="callout"><strong>Warning</strong></div>'
    assert html == expected


def test_fragment_standalone():
    """Test that fragments can be used standalone like documents."""
    fragment = Fragment()

    with fragment.ul():
        with fragment.li():
            fragment.text("Item 1")
        with fragment.li():
            fragment.text("Item 2")
        with fragment.li():
            fragment.text("Item 3")

    html = fragment.render()
    expected = "<ul><li>Item 1</li><li>Item 2</li><li>Item 3</li></ul>"
    assert html == expected


def test_fragment_reusable_component():
    """Test creating reusable fragment components."""

    def get_callout(title: str, level: str = "info") -> Fragment:
        frag = Fragment()
        with frag.div(class_=f"callout callout-{level}"):
            with frag.strong():
                frag.text(title)
        return frag

    # Create multiple instances
    warning = get_callout("Warning", "danger")
    info = get_callout("Info", "info")

    assert (
        warning.render()
        == '<div class="callout callout-danger"><strong>Warning</strong></div>'
    )
    assert (
        info.render() == '<div class="callout callout-info"><strong>Info</strong></div>'
    )


def test_document_fragment_insertion():
    """Test inserting fragments into documents."""

    def get_callout(title: str) -> Fragment:
        frag = Fragment()
        with frag.div(class_="callout"):
            frag.text(title)
        return frag

    doc = Document()
    with doc.html():
        with doc.body():
            doc.fragment(get_callout("Warning"))

    html = doc.render()
    expected = '<html><body><div class="callout">Warning</div></body></html>'
    assert html == expected


def test_document_multiple_fragments():
    """Test inserting multiple fragments into a document."""

    def get_button(label: str, btn_type: str = "primary") -> Fragment:
        frag = Fragment()
        with frag.button(class_=f"btn btn-{btn_type}"):
            frag.text(label)
        return frag

    doc = Document()
    with doc.div(class_="button-group"):
        doc.fragment(get_button("Save", "primary"))
        doc.fragment(get_button("Cancel", "secondary"))
        doc.fragment(get_button("Delete", "danger"))

    html = doc.render()
    expected = (
        '<div class="button-group">'
        '<button class="btn btn-primary">Save</button>'
        '<button class="btn btn-secondary">Cancel</button>'
        '<button class="btn btn-danger">Delete</button>'
        "</div>"
    )
    assert html == expected


def test_fragment_with_text_and_raw():
    """Test fragments with text and raw content."""
    fragment = Fragment()

    with fragment.div():
        fragment.text("Safe <text>")
        fragment.raw("<em>raw</em>")

    html = fragment.render()
    expected = "<div>Safe &lt;text&gt;<em>raw</em></div>"
    assert html == expected


def test_fragment_with_attr_and_classes():
    """Test fragments with dynamic attributes and classes."""
    fragment = Fragment()

    is_active = True

    with fragment.div():
        fragment.attr("id", "main")
        if is_active:
            fragment.classes("active")
        fragment.text("Content")

    html = fragment.render()
    expected = '<div id="main" class="active">Content</div>'
    assert html == expected


def test_nested_fragments():
    """Test that fragments can contain other fragments."""

    def get_list_item(text: str) -> Fragment:
        frag = Fragment()
        with frag.li():
            frag.text(text)
        return frag

    fragment = Fragment()
    with fragment.ul():
        fragment.fragment(get_list_item("First"))
        fragment.fragment(get_list_item("Second"))
        fragment.fragment(get_list_item("Third"))

    html = fragment.render()
    expected = "<ul><li>First</li><li>Second</li><li>Third</li></ul>"
    assert html == expected


def test_fragment_reuse():
    """Test that fragments can be cleared and reused."""
    fragment = Fragment()

    # First use
    with fragment.p():
        fragment.text("First")
    html1 = fragment.render()

    # Clear and reuse
    fragment.clear()
    with fragment.h1():
        fragment.text("Second")
    html2 = fragment.render()

    assert html1 == "<p>First</p>"
    assert html2 == "<h1>Second</h1>"


def test_fragment_all_shortcuts():
    """Test that fragments have all tag shortcuts."""
    fragment = Fragment()

    with fragment.div():
        with fragment.h1():
            fragment.text("Title")
        with fragment.p():
            fragment.text("Paragraph")
        fragment.br()
        fragment.img(src="test.jpg")

    html = fragment.render()
    assert "<div>" in html
    assert "<h1>Title</h1>" in html
    assert "<p>Paragraph</p>" in html
    assert "<br />" in html
    assert '<img src="test.jpg" />' in html


def test_fragment_with_complex_structure():
    """Test fragments with complex nested structures."""

    def get_card(title: str, content: str) -> Fragment:
        frag = Fragment()
        with frag.div(class_="card"):
            with frag.div(class_="card-header"):
                with frag.h3():
                    frag.text(title)
            with frag.div(class_="card-body"):
                with frag.p():
                    frag.text(content)
        return frag

    doc = Document()
    with doc.div(class_="container"):
        doc.fragment(get_card("Card 1", "Content 1"))
        doc.fragment(get_card("Card 2", "Content 2"))

    html = doc.render()
    assert '<div class="card">' in html
    assert '<div class="card-header">' in html
    assert "<h3>Card 1</h3>" in html
    assert "<p>Content 1</p>" in html
    assert "<h3>Card 2</h3>" in html
    assert "<p>Content 2</p>" in html


def test_fragment_empty():
    """Test that empty fragments render correctly."""
    fragment = Fragment()
    html = fragment.render()
    assert html == ""


def test_fragment_inheritance():
    """Test that Document properly inherits from Fragment."""
    # Document should have all Fragment methods
    doc = Document()
    assert isinstance(doc, Fragment)
    assert hasattr(doc, "fragment")
    assert hasattr(doc, "tag")
    assert hasattr(doc, "text")
    assert hasattr(doc, "raw")
    assert hasattr(doc, "attr")
    assert hasattr(doc, "classes")


def test_fragment_composition_example():
    """Test the example from the issue description."""

    def get_callout(title: str) -> Fragment:
        fragment = Fragment()
        with fragment.div():
            fragment.text(title)
        return fragment

    doc = Document()
    with doc.html():
        with doc.body():
            doc.fragment(get_callout("Warning"))

    html = doc.render()
    expected = "<html><body><div>Warning</div></body></html>"
    assert html == expected
