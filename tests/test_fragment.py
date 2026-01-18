"""Tests for the markupflow Fragment class.

This module contains comprehensive tests to verify that the markupflow
Fragment class produces correct HTML output and handles various edge cases properly.
"""

import pytest

from markupflow import (
    Fragment,
    MarkupFlowError,
    NoTagContextError,
    TagAlreadyOpenedError,
    UnclosedTagsError,
)


def test_simple_fragment():
    """Test basic fragment creation and rendering."""
    frag = Fragment()

    with frag.tag("html"):
        with frag.tag("head"):
            with frag.tag("title"):
                frag.text("Test Page")
        with frag.tag("body"):
            with frag.tag("h1"):
                frag.text("Hello World")

    html = frag.render()
    expected = "<html><head><title>Test Page</title></head><body><h1>Hello World</h1></body></html>"
    assert html == expected


def test_attributes():
    """Test attribute handling including special cases."""
    frag = Fragment()

    with frag.tag("div", class_="container", data_value="123", id="main"):
        with frag.tag("img", src="test.jpg", alt="Test Image"):
            pass  # Self-closing tag

    html = frag.render()
    # Note: img is self-closing
    expected = '<div class="container" data-value="123" id="main"><img src="test.jpg" alt="Test Image" /></div>'
    assert html == expected


def test_text_escaping():
    """Test that text content is properly escaped."""
    frag = Fragment()

    with frag.tag("p"):
        frag.text('Hello & <world> "test"')

    html = frag.render()
    expected = '<p>Hello &amp; &lt;world&gt; "test"</p>'
    assert html == expected


def test_attribute_escaping():
    """Test that attribute values are properly escaped."""
    frag = Fragment()

    with frag.tag("div", title='Test & "quoted" <value>'):
        pass

    html = frag.render()
    expected = '<div title="Test &amp; &quot;quoted&quot; &lt;value&gt;"></div>'
    assert html == expected


def test_raw_content():
    """Test raw HTML insertion."""
    frag = Fragment()

    with frag.tag("div"):
        frag.raw("<em>Already formatted</em>")
        frag.text(" and escaped")

    html = frag.render()
    expected = "<div><em>Already formatted</em> and escaped</div>"
    assert html == expected


def test_self_closing_tags():
    """Test that self-closing tags are handled correctly."""
    frag = Fragment()

    with frag.tag("div"):
        with frag.tag("br"):
            pass
        with frag.tag("img", src="test.jpg"):
            pass
        with frag.tag("input", type="text", name="test"):
            pass

    html = frag.render()
    expected = (
        '<div><br /><img src="test.jpg" /><input type="text" name="test" /></div>'
    )
    assert html == expected


def test_attribute_name_conversion():
    """Test attribute name conversion from Python to HTML."""
    frag = Fragment()

    with frag.tag(
        "div",
        class_="test",  # class_ -> class
        data_value="123",  # data_value -> data-value
        aria_label="button",
    ):  # aria_label -> aria-label
        pass

    html = frag.render()
    expected = '<div class="test" data-value="123" aria-label="button"></div>'
    assert html == expected


def test_reserved_keyword_attributes():
    """Test that reserved Python keywords work as HTML attributes."""
    frag = Fragment()

    # Test 'for' attribute - common with label tags
    with frag.label(for_="username", class_="form-label"):
        frag.text("Username:")

    with frag.input(type="text", id="username", name="username"):
        pass

    html = frag.render()
    expected = '<label for="username" class="form-label">Username:</label><input type="text" id="username" name="username" />'
    assert html == expected


def test_fragment_reuse():
    """Test that fragments can be cleared and reused."""
    frag = Fragment()

    # First use
    with frag.tag("p"):
        frag.text("First")
    html1 = frag.render()

    # Clear and reuse
    frag.clear()
    with frag.tag("h1"):
        frag.text("Second")
    html2 = frag.render()

    assert html1 == "<p>First</p>"
    assert html2 == "<h1>Second</h1>"


def test_tag_shortcuts():
    """Test that tag shortcuts work correctly."""
    frag = Fragment()

    # Test common tag shortcuts
    with frag.div(class_="container"):
        with frag.h1(id="title"):
            frag.text("Title")
        with frag.p(class_="text"):
            frag.text("Paragraph")
        with frag.ul():
            with frag.li():
                frag.text("Item 1")
            with frag.li():
                frag.text("Item 2")
        with frag.button(type="submit", disabled="true"):
            frag.text("Submit")
        # Test self-closing shortcuts
        frag.br()
        frag.hr()
        frag.img(src="test.jpg", alt="Test")

    html = frag.render()
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
    frag1 = Fragment()
    frag2 = Fragment()

    # Using shortcuts
    with frag1.div(class_="test"):
        with frag1.h1():
            frag1.text("Hello")
        with frag1.p():
            frag1.text("World")

    # Using tag() method
    with frag2.tag("div", class_="test"):
        with frag2.tag("h1"):
            frag2.text("Hello")
        with frag2.tag("p"):
            frag2.text("World")

    html1 = frag1.render()
    html2 = frag2.render()

    assert html1 == html2


def test_attr_function():
    """Test the attr() function for dynamic attribute addition."""
    frag = Fragment()

    # Basic attr() usage
    with frag.div():
        frag.attr("class", "container")
        frag.attr("id", "main")
        frag.text("Content")

    html = frag.render()
    expected = '<div class="container" id="main">Content</div>'
    assert html == expected


def test_attr_conditional_logic():
    """Test attr() with conditional logic - the main use case."""
    frag = Fragment()

    user_is_admin = True
    show_tooltip = False

    with frag.div():
        if user_is_admin:
            frag.attr("class", "admin-panel")
            frag.attr("data-role", "administrator")
        if show_tooltip:
            frag.attr("title", "This is a tooltip")
        frag.text("Admin Panel")

    html = frag.render()
    expected = '<div class="admin-panel" data-role="administrator">Admin Panel</div>'
    assert html == expected

    # Test with different conditions
    frag.clear()
    user_is_admin = False
    show_tooltip = True

    with frag.div():
        if user_is_admin:
            frag.attr("class", "admin-panel")
            frag.attr("data-role", "administrator")
        if show_tooltip:
            frag.attr("title", "This is a tooltip")
        frag.text("Regular Panel")

    html = frag.render()
    expected = '<div title="This is a tooltip">Regular Panel</div>'
    assert html == expected


def test_attr_with_initial_attributes():
    """Test attr() when the tag already has initial attributes."""
    frag = Fragment()

    with frag.div(id="container", data_type="widget"):
        frag.attr("class", "active")
        frag.attr("data-value", "123")
        frag.text("Widget")

    html = frag.render()
    expected = '<div id="container" data-type="widget" class="active" data-value="123">Widget</div>'
    assert html == expected


def test_attr_attribute_name_conversion():
    """Test that attr() properly converts attribute names."""
    frag = Fragment()

    with frag.div():
        frag.attr("class_", "test")
        frag.attr("data_value", "123")
        frag.attr("aria_label", "button")
        frag.attr("for_", "username")
        frag.text("Content")

    html = frag.render()
    expected = '<div class="test" data-value="123" aria-label="button" for="username">Content</div>'
    assert html == expected


def test_attr_value_escaping():
    """Test that attr() properly escapes attribute values."""
    frag = Fragment()

    with frag.div():
        frag.attr("title", 'Test & "quoted" <value>')
        frag.attr("data-info", "Line 1\nLine 2")
        frag.text("Content")

    html = frag.render()
    expected = '<div title="Test &amp; &quot;quoted&quot; &lt;value&gt;" data-info="Line 1\nLine 2">Content</div>'
    assert html == expected


def test_attr_error_cases():
    """Test error cases for attr() function."""
    frag = Fragment()

    # Test calling attr() outside of a tag context
    with pytest.raises(NoTagContextError, match="No current tag context"):
        frag.attr("class", "test")

    # Test calling attr() after tag has been opened
    with frag.div():
        frag.text("This opens the tag")
        with pytest.raises(TagAlreadyOpenedError, match="Tag already opened"):
            frag.attr("class", "test")


def test_attr_with_nested_tags():
    """Test attr() with nested tag structures."""
    frag = Fragment()

    with frag.div():
        frag.attr("class", "outer")

        with frag.p():
            frag.attr("class", "inner")
            frag.text("Paragraph")

        frag.text("Outer text")

    html = frag.render()
    expected = '<div class="outer"><p class="inner">Paragraph</p>Outer text</div>'
    assert html == expected


def test_attr_with_shortcuts():
    """Test attr() works with tag shortcuts."""
    frag = Fragment()

    with frag.div():
        frag.attr("class", "container")

        with frag.h1():
            frag.attr("id", "title")
            frag.text("Title")

        with frag.p():
            frag.attr("class", "description")
            frag.text("Description")

    html = frag.render()
    expected = '<div class="container"><h1 id="title">Title</h1><p class="description">Description</p></div>'
    assert html == expected


def test_complex_nested_structure():
    """Test complex nested HTML structure similar to benchmark tests."""
    frag = Fragment()

    with frag.tag("html", lang="en"):
        with frag.tag("head"):
            with frag.tag("title"):
                frag.text("Complex Page")
            with frag.tag("meta", charset="utf-8"):
                pass
        with frag.tag("body"):
            with frag.tag("nav", class_="navigation"):
                with frag.tag("ul"):
                    for item in ["Home", "About", "Contact"]:
                        with frag.tag("li"):
                            with frag.tag("a", href=f"#{item.lower()}"):
                                frag.text(item)
            with frag.tag("main"):
                with frag.tag("h1"):
                    frag.text("Welcome")
                with frag.tag("p"):
                    frag.text("This is a test page.")
                    frag.text("Welcome")
                with frag.tag("p"):
                    frag.text("This is a test page.")

    html = frag.render()

    # Verify it contains expected elements
    assert '<html lang="en">' in html
    assert '<meta charset="utf-8" />' in html
    assert '<nav class="navigation">' in html
    assert '<a href="#home">Home</a>' in html
    assert '<a href="#about">About</a>' in html
    assert '<a href="#contact">Contact</a>' in html


def test_unclosed_tags_error():
    """Test that unclosed tags raise an appropriate error."""
    frag = Fragment()

    # Manually create unclosed tags by not using context managers properly
    frag._tag_stack.append("html")
    frag._tag_stack.append("head")

    # Missing closing tags for head and html
    with pytest.raises(UnclosedTagsError, match="Unclosed tags"):
        frag.render()


def test_exception_hierarchy():
    """Test that all markupflow exceptions inherit from MarkupFlowError."""
    frag = Fragment()

    # Test that NoTagContextError is caught by MarkupFlowError
    with pytest.raises(MarkupFlowError):
        frag.attr("class", "test")

    # Test that TagAlreadyOpenedError is caught by MarkupFlowError
    with frag.div():
        frag.text("This opens the tag")
        with pytest.raises(MarkupFlowError):
            frag.attr("class", "test")

    # Test that UnclosedTagsError is caught by MarkupFlowError
    frag._tag_stack.append("html")
    with pytest.raises(MarkupFlowError):
        frag.render()


def test_none_content_handling():
    """Test that None content is handled gracefully."""
    frag = Fragment()

    with frag.tag("div"):
        frag.text(None)  # Should be ignored
        frag.attr("title", None)  # Should be ignored (not rendered)
        frag.text("Some text")

    html = frag.render()
    expected = "<div>Some text</div>"  # No title attribute when value is None
    assert html == expected


def test_classes_function():
    """Test the classes() function for adding classes to current tag."""
    frag = Fragment()

    # Basic classes() usage
    with frag.div():
        frag.classes("container")
        frag.text("Content")

    html = frag.render()
    expected = '<div class="container">Content</div>'
    assert html == expected


def test_classes_appends_to_existing():
    """Test that classes() appends to existing classes."""
    frag = Fragment()

    # With initial class
    with frag.div(class_="container"):
        frag.classes("active")
        frag.classes("highlighted")
        frag.text("Content")

    html = frag.render()
    expected = '<div class="container active highlighted">Content</div>'
    assert html == expected


def test_classes_multiple_calls():
    """Test multiple classes() calls."""
    frag = Fragment()

    with frag.div():
        frag.classes("container")
        frag.classes("fluid")
        frag.classes("bordered")
        frag.text("Content")

    html = frag.render()
    expected = '<div class="container fluid bordered">Content</div>'
    assert html == expected


def test_classes_with_conditional_logic():
    """Test classes() with conditional logic - the main use case."""
    frag = Fragment()

    is_admin = True
    is_active = True
    is_highlighted = False

    with frag.div(class_="panel"):
        if is_admin:
            frag.classes("admin")
        if is_active:
            frag.classes("active")
        if is_highlighted:
            frag.classes("highlighted")
        frag.text("Panel Content")

    html = frag.render()
    expected = '<div class="panel admin active">Panel Content</div>'
    assert html == expected


def test_classes_with_nested_tags():
    """Test classes() with nested tag structures."""
    frag = Fragment()

    with frag.div(class_="outer"):
        frag.classes("container")

        with frag.p():
            frag.classes("inner")
            frag.classes("text")
            frag.text("Paragraph")

        frag.text("Outer text")

    html = frag.render()
    expected = '<div class="outer container"><p class="inner text">Paragraph</p>Outer text</div>'
    assert html == expected


def test_classes_error_cases():
    """Test error cases for classes() function."""
    frag = Fragment()

    # Test calling classes() outside of a tag context
    with pytest.raises(NoTagContextError, match="No current tag context"):
        frag.classes("test")

    # Test calling classes() after tag has been opened
    with frag.div():
        frag.text("This opens the tag")
        with pytest.raises(TagAlreadyOpenedError, match="Tag already opened"):
            frag.classes("test")


def test_classes_with_shortcuts():
    """Test classes() works with tag shortcuts."""
    frag = Fragment()

    with frag.div(class_="container"):
        frag.classes("fluid")

        with frag.h1():
            frag.classes("title")
            frag.classes("large")
            frag.text("Title")

        with frag.p(class_="text"):
            frag.classes("muted")
            frag.text("Description")

    html = frag.render()
    expected = '<div class="container fluid"><h1 class="title large">Title</h1><p class="text muted">Description</p></div>'
    assert html == expected


def test_fragment_insertion():
    """Test that fragments can be inserted into other fragments."""
    # Create a reusable callout fragment
    callout = Fragment()
    with callout.div(class_="callout"):
        callout.text("Warning")

    # Insert it into another fragment
    doc = Fragment()
    with doc.div(class_="container"):
        doc.fragment(callout)

    html = doc.render()
    expected = '<div class="container"><div class="callout">Warning</div></div>'
    assert html == expected


def test_fragment_multiple_insertions():
    """Test that the same fragment can be inserted multiple times."""
    # Create a reusable fragment
    badge = Fragment()
    with badge.span(class_="badge"):
        badge.text("New")

    # Insert it multiple times
    doc = Fragment()
    with doc.div():
        doc.fragment(badge)
        doc.text(" Item 1 ")
        doc.fragment(badge)
        doc.text(" Item 2 ")
        doc.fragment(badge)

    html = doc.render()
    expected = '<div><span class="badge">New</span> Item 1 <span class="badge">New</span> Item 2 <span class="badge">New</span></div>'
    assert html == expected


def test_fragment_nested_insertion():
    """Test that fragments can contain other fragments."""
    # Create inner fragment
    icon = Fragment()
    with icon.span(class_="icon"):
        icon.text("✓")

    # Create middle fragment
    button = Fragment()
    with button.button(type="button"):
        button.fragment(icon)
        button.text(" Click")

    # Create outer fragment
    doc = Fragment()
    with doc.div():
        doc.fragment(button)

    html = doc.render()
    expected = (
        '<div><button type="button"><span class="icon">✓</span> Click</button></div>'
    )
    assert html == expected


def test_fragment_with_dynamic_content():
    """Test creating reusable fragments with dynamic content."""

    def create_alert(message, alert_type="info"):
        """Create an alert fragment."""
        alert = Fragment()
        with alert.div(class_=f"alert alert-{alert_type}"):
            alert.text(message)
        return alert

    # Use the fragment factory
    doc = Fragment()
    with doc.div():
        doc.fragment(create_alert("Success!", "success"))
        doc.fragment(create_alert("Warning!", "warning"))
        doc.fragment(create_alert("Error!", "danger"))

    html = doc.render()
    assert '<div class="alert alert-success">Success!</div>' in html
    assert '<div class="alert alert-warning">Warning!</div>' in html
    assert '<div class="alert alert-danger">Error!</div>' in html


def test_fragment_str_method():
    """Test that Fragment supports str() conversion."""
    frag = Fragment()
    with frag.div():
        frag.text("Test")

    assert str(frag) == "<div>Test</div>"
    assert str(frag) == frag.render()


def test_fragment_with_context_manager_pattern():
    """Test the expandable fragment pattern using context managers."""
    import contextlib

    @contextlib.contextmanager
    def button_fragment(button_type="button"):
        """Create an expandable button fragment."""
        fragment = Fragment()
        with fragment.button(type=button_type):
            yield fragment

    # Use the new expandable fragment pattern with doc.fragment()
    doc = Fragment()
    with doc.div():
        with doc.fragment(button_fragment("submit")) as btn:
            btn.text("Submit")

    html = doc.render()
    expected = '<div><button type="submit">Submit</button></div>'
    assert html == expected


def test_fragment_api_from_issue():
    """Test the exact API pattern proposed in the issue."""
    import contextlib

    def get_callout(title):
        fragment = Fragment()
        with fragment.div(class_="callout"):
            fragment.text(title)
        return fragment

    @contextlib.contextmanager
    def button(button_type="button"):
        fragment = Fragment()
        with fragment.button(type=button_type):
            yield fragment

    # Test the proposed API with the new context manager support
    doc = Fragment()
    with doc.tag("html"):
        with doc.tag("body"):
            # Finished fragment
            doc.fragment(get_callout("Warning"))

            # Expandable fragment with new API
            with doc.fragment(button()) as f:
                f.text("Ok")

    html = doc.render()
    assert '<div class="callout">Warning</div>' in html
    assert '<button type="button">Ok</button>' in html
