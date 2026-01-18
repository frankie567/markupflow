from __future__ import annotations

import html
import re
from typing import Any

"""Generate HTML, the Pythonic way"""

__version__ = "0.0.1"

AttrValue = str | int | float | bool | None


class MarkupFlowError(Exception):
    """Base class for all markupflow exceptions."""


class TagAlreadyOpenedError(MarkupFlowError):
    """Raised when attempting to add attributes to an already opened tag."""

    def __init__(self) -> None:
        super().__init__("Tag already opened")


class NoTagContextError(MarkupFlowError):
    """Raised when attr() is called outside of a tag context."""

    def __init__(self) -> None:
        super().__init__("No current tag context")


class UnclosedTagsError(MarkupFlowError):
    """Raised when attempting to render a document with unclosed tags."""

    def __init__(self) -> None:
        super().__init__("Unclosed tags")


__all__ = [
    "AttrValue",
    "Document",
    "Fragment",
    "document",
    "MarkupFlowError",
    "TagAlreadyOpenedError",
    "NoTagContextError",
    "UnclosedTagsError",
]

# Pre-compiled regex for attribute name conversion
_ATTR_NAME_PATTERN = re.compile(r"(\w)_(\w)")

# Cache for attribute name conversions to avoid repeated regex operations
_ATTR_NAME_CACHE: dict[str, str] = {}


def _convert_attr_name(name: str) -> str:
    """Convert Python attribute names to HTML attribute names.

    Examples:
        data_value -> data-value
        aria_label -> aria-label
        class_ -> class
        classes -> class
    """
    if name not in _ATTR_NAME_CACHE:
        if name in ("class_", "classes"):
            _ATTR_NAME_CACHE[name] = "class"
        elif name.endswith("_"):
            # Remove trailing underscore for reserved keywords
            _ATTR_NAME_CACHE[name] = name[:-1]
        else:
            # Convert underscores to hyphens (e.g., data_value -> data-value)
            _ATTR_NAME_CACHE[name] = _ATTR_NAME_PATTERN.sub(r"\1-\2", name)
    return _ATTR_NAME_CACHE[name]


def _escape_attr_value(value: AttrValue) -> str:
    """Escape an attribute value for safe HTML output."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def _escape_text(text: AttrValue) -> str:
    """Escape text content for safe HTML output."""
    if text is None:
        return ""
    return html.escape(str(text), quote=False)


class _TagContext:
    """Context manager for HTML tags.

    This is a lightweight object that handles opening and closing tags
    with minimal overhead. It supports lazy tag writing to allow dynamic
    attribute addition via the attr() method.
    """

    __slots__ = ("_fragment", "_tag_name", "_self_closing", "_attrs", "_opened")

    def __init__(
        self,
        fragment: Fragment,
        tag_name: str,
        attrs: dict[str, AttrValue],
        self_closing: bool = False,
    ) -> None:
        self._fragment = fragment
        self._tag_name = tag_name
        self._self_closing = self_closing
        self._attrs = attrs.copy()  # Copy to avoid mutation issues
        self._opened = False

    def _ensure_opened(self) -> None:
        """Ensure the opening tag has been written to the fragment."""
        if not self._opened:
            self._opened = True

            # Build the opening tag
            if self._attrs:
                attr_str = " " + " ".join(
                    f'{_convert_attr_name(k)}="{_escape_attr_value(v)}"'
                    for k, v in self._attrs.items()
                    if v is not None
                )
            else:
                attr_str = ""

            if self._self_closing:
                self._fragment._parts.append(f"<{self._tag_name}{attr_str} />")
            else:
                self._fragment._parts.append(f"<{self._tag_name}{attr_str}>")

    def add_attr(self, name: str, value: AttrValue) -> None:
        """Add an attribute to this tag context.

        Args:
            name: The attribute name
            value: The attribute value

        Raises:
            RuntimeError: If the tag has already been opened
        """
        if self._opened:
            raise TagAlreadyOpenedError()

        self._attrs[name] = value

    def add_class(self, class_name: str) -> None:
        """Add a class to this tag context.

        If classes already exist, the new class is appended.

        Args:
            class_name: The class name to add

        Raises:
            TagAlreadyOpenedError: If the tag has already been opened
        """
        if self._opened:
            raise TagAlreadyOpenedError()

        # Check for existing class attribute (handle both class_ and class)
        existing_class = self._attrs.get("class_") or self._attrs.get("class")

        if existing_class:
            # Append to existing classes
            self._attrs["class_"] = f"{existing_class} {class_name}"
        else:
            # Set new class
            self._attrs["class_"] = class_name

    def __enter__(self) -> _TagContext:
        if not self._self_closing:
            self._fragment._tag_stack.append(self._tag_name)
            self._fragment._context_stack.append(self)
        else:
            # Self-closing tags are opened immediately
            self._ensure_opened()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if not self._self_closing:
            # Ensure the tag is opened before closing
            self._ensure_opened()

            closing_tag = self._fragment._tag_stack.pop()
            self._fragment._parts.append(f"</{closing_tag}>")

            # Remove this context from the stack
            self._fragment._context_stack.pop()


class Fragment:
    """A reusable HTML fragment that can be composed and rendered.

    Fragment is the base class that provides the core HTML building functionality.
    It can be used to create reusable components that can be inserted into documents
    or other fragments at any point. This allows you to define HTML fragments without
    carrying the document instance everywhere.

    The Fragment class provides an efficient way to build HTML using context managers,
    with focus on performance and simplicity. It includes shortcuts for common HTML
    tags and supports dynamic attribute addition via the attr() method.

    Example:
        def get_callout(title: str, level: str = "info") -> Fragment:
            fragment = Fragment()
            with fragment.div(class_=f"callout callout-{level}"):
                with fragment.strong():
                    fragment.text(title)
            return fragment

        # Use fragment standalone
        html = get_callout("Warning", "danger").render()

        # Or compose into a document
        doc = Document()
        with doc.body():
            doc.fragment(get_callout("Warning", "danger"))
    """

    __slots__ = ("_parts", "_tag_stack", "_context_stack")

    def __init__(self) -> None:
        """Initialize an empty document."""
        self._parts: list[str] = []
        self._tag_stack: list[str] = []
        self._context_stack: list[_TagContext] = []

    def tag(self, tag_name: str, **attrs: AttrValue) -> _TagContext:
        """Create a tag context manager.

        Args:
            tag_name: The HTML tag name (e.g., "div", "p", "img")
            **attrs: HTML attributes as keyword arguments

        Returns:
            A context manager that handles opening and closing the tag

        Example:
            with doc.tag("div", class_="container", data_value="123"):
                doc.text("Content")
        """
        # Ensure the current tag (if any) is opened before creating a nested tag
        if self._context_stack:
            self._context_stack[-1]._ensure_opened()

        # Check for self-closing tags
        self_closing = tag_name.lower() in {
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        }

        # Create the tag context (opening tag is written lazily)
        context = _TagContext(self, tag_name, attrs, self_closing)
        return context

    def text(self, content: AttrValue) -> None:
        """Add text content to the document.

        Args:
            content: The text content to add (will be escaped for safety)

        Example:
            doc.text("Hello & welcome!")  # Becomes "Hello &amp; welcome!"
        """
        if content is not None:
            # Ensure current tag is opened before adding content
            if self._context_stack:
                self._context_stack[-1]._ensure_opened()
            self._parts.append(_escape_text(content))

    def raw(self, content: AttrValue) -> None:
        """Add raw HTML content to the document without escaping.

        WARNING: This method does not escape content. Only use with trusted input.

        Args:
            content: The raw HTML content to add

        Example:
            doc.raw("<em>Already formatted</em>")
        """
        if content is not None:
            # Ensure current tag is opened before adding content
            if self._context_stack:
                self._context_stack[-1]._ensure_opened()
            self._parts.append(str(content))

    def attr(self, name: str, value: AttrValue) -> None:
        """Add an attribute to the current tag.

        This method allows dynamic addition of attributes to the currently
        open tag context. This is very useful for conditional logic.

        Args:
            name: The attribute name (will be converted like other attributes)
            value: The attribute value

        Raises:
            NoTagContextError: If there is no current tag context
            TagAlreadyOpenedError: If the tag has already been opened

        Example:
            with doc.div() as div_tag:
                if user_is_admin:
                    doc.attr("class", "admin-panel")
                    doc.attr("data-role", "administrator")
                doc.text("Content")
        """
        if not self._context_stack:
            raise NoTagContextError()

        self._context_stack[-1].add_attr(name, value)

    def classes(self, class_name: str) -> None:
        """Add a class to the current tag.

        This method allows dynamic addition of classes to the currently
        open tag context. If classes already exist, the new class is appended.

        Args:
            class_name: The class name to add

        Raises:
            NoTagContextError: If there is no current tag context
            TagAlreadyOpenedError: If the tag has already been opened

        Example:
            with doc.div(class_="container"):
                if user_is_admin:
                    doc.classes("admin")
                if is_active:
                    doc.classes("active")
                doc.text("Content")
            # Result: <div class="container admin active">Content</div>
        """
        if not self._context_stack:
            raise NoTagContextError()

        self._context_stack[-1].add_class(class_name)

    def render(self) -> str:
        """Render the document to an HTML string.

        Returns:
            The complete HTML document as a string

        Raises:
            RuntimeError: If there are unclosed tags
        """
        if self._tag_stack:
            raise UnclosedTagsError()

        return "".join(self._parts)

    def clear(self) -> None:
        """Clear the document content, allowing reuse of the same Document object."""
        self._parts.clear()
        self._tag_stack.clear()
        self._context_stack.clear()

    def __str__(self) -> str:
        """Return the rendered HTML when converting to string."""
        return self.render()

    # Shortcut methods for common HTML tags

    def html(self, **attrs: AttrValue) -> _TagContext:
        """Create an html tag. Shortcut for tag('html', **attrs)."""
        return self.tag("html", **attrs)

    def head(self, **attrs: AttrValue) -> _TagContext:
        """Create a head tag. Shortcut for tag('head', **attrs)."""
        return self.tag("head", **attrs)

    def body(self, **attrs: AttrValue) -> _TagContext:
        """Create a body tag. Shortcut for tag('body', **attrs)."""
        return self.tag("body", **attrs)

    def title(self, **attrs: AttrValue) -> _TagContext:
        """Create a title tag. Shortcut for tag('title', **attrs)."""
        return self.tag("title", **attrs)

    def div(self, **attrs: AttrValue) -> _TagContext:
        """Create a div tag. Shortcut for tag('div', **attrs)."""
        return self.tag("div", **attrs)

    def p(self, **attrs: AttrValue) -> _TagContext:
        """Create a p tag. Shortcut for tag('p', **attrs)."""
        return self.tag("p", **attrs)

    def span(self, **attrs: AttrValue) -> _TagContext:
        """Create a span tag. Shortcut for tag('span', **attrs)."""
        return self.tag("span", **attrs)

    def h1(self, **attrs: AttrValue) -> _TagContext:
        """Create an h1 tag. Shortcut for tag('h1', **attrs)."""
        return self.tag("h1", **attrs)

    def h2(self, **attrs: AttrValue) -> _TagContext:
        """Create an h2 tag. Shortcut for tag('h2', **attrs)."""
        return self.tag("h2", **attrs)

    def h3(self, **attrs: AttrValue) -> _TagContext:
        """Create an h3 tag. Shortcut for tag('h3', **attrs)."""
        return self.tag("h3", **attrs)

    def h4(self, **attrs: AttrValue) -> _TagContext:
        """Create an h4 tag. Shortcut for tag('h4', **attrs)."""
        return self.tag("h4", **attrs)

    def h5(self, **attrs: AttrValue) -> _TagContext:
        """Create an h5 tag. Shortcut for tag('h5', **attrs)."""
        return self.tag("h5", **attrs)

    def h6(self, **attrs: AttrValue) -> _TagContext:
        """Create an h6 tag. Shortcut for tag('h6', **attrs)."""
        return self.tag("h6", **attrs)

    def a(self, **attrs: AttrValue) -> _TagContext:
        """Create an a tag. Shortcut for tag('a', **attrs)."""
        return self.tag("a", **attrs)

    def button(self, **attrs: AttrValue) -> _TagContext:
        """Create a button tag. Shortcut for tag('button', **attrs)."""
        return self.tag("button", **attrs)

    def form(self, **attrs: AttrValue) -> _TagContext:
        """Create a form tag. Shortcut for tag('form', **attrs)."""
        return self.tag("form", **attrs)

    def input(self, **attrs: AttrValue) -> _TagContext:
        """Create an input tag. Shortcut for tag('input', **attrs)."""
        return self.tag("input", **attrs)

    def label(self, **attrs: AttrValue) -> _TagContext:
        """Create a label tag. Shortcut for tag('label', **attrs)."""
        return self.tag("label", **attrs)

    def select(self, **attrs: AttrValue) -> _TagContext:
        """Create a select tag. Shortcut for tag('select', **attrs)."""
        return self.tag("select", **attrs)

    def option(self, **attrs: AttrValue) -> _TagContext:
        """Create an option tag. Shortcut for tag('option', **attrs)."""
        return self.tag("option", **attrs)

    def textarea(self, **attrs: AttrValue) -> _TagContext:
        """Create a textarea tag. Shortcut for tag('textarea', **attrs)."""
        return self.tag("textarea", **attrs)

    def ul(self, **attrs: AttrValue) -> _TagContext:
        """Create a ul tag. Shortcut for tag('ul', **attrs)."""
        return self.tag("ul", **attrs)

    def ol(self, **attrs: AttrValue) -> _TagContext:
        """Create an ol tag. Shortcut for tag('ol', **attrs)."""
        return self.tag("ol", **attrs)

    def li(self, **attrs: AttrValue) -> _TagContext:
        """Create a li tag. Shortcut for tag('li', **attrs)."""
        return self.tag("li", **attrs)

    def table(self, **attrs: AttrValue) -> _TagContext:
        """Create a table tag. Shortcut for tag('table', **attrs)."""
        return self.tag("table", **attrs)

    def thead(self, **attrs: AttrValue) -> _TagContext:
        """Create a thead tag. Shortcut for tag('thead', **attrs)."""
        return self.tag("thead", **attrs)

    def tbody(self, **attrs: AttrValue) -> _TagContext:
        """Create a tbody tag. Shortcut for tag('tbody', **attrs)."""
        return self.tag("tbody", **attrs)

    def tr(self, **attrs: AttrValue) -> _TagContext:
        """Create a tr tag. Shortcut for tag('tr', **attrs)."""
        return self.tag("tr", **attrs)

    def td(self, **attrs: AttrValue) -> _TagContext:
        """Create a td tag. Shortcut for tag('td', **attrs)."""
        return self.tag("td", **attrs)

    def th(self, **attrs: AttrValue) -> _TagContext:
        """Create a th tag. Shortcut for tag('th', **attrs)."""
        return self.tag("th", **attrs)

    def section(self, **attrs: AttrValue) -> _TagContext:
        """Create a section tag. Shortcut for tag('section', **attrs)."""
        return self.tag("section", **attrs)

    def article(self, **attrs: AttrValue) -> _TagContext:
        """Create an article tag. Shortcut for tag('article', **attrs)."""
        return self.tag("article", **attrs)

    def header(self, **attrs: AttrValue) -> _TagContext:
        """Create a header tag. Shortcut for tag('header', **attrs)."""
        return self.tag("header", **attrs)

    def footer(self, **attrs: AttrValue) -> _TagContext:
        """Create a footer tag. Shortcut for tag('footer', **attrs)."""
        return self.tag("footer", **attrs)

    def nav(self, **attrs: AttrValue) -> _TagContext:
        """Create a nav tag. Shortcut for tag('nav', **attrs)."""
        return self.tag("nav", **attrs)

    def main(self, **attrs: AttrValue) -> _TagContext:
        """Create a main tag. Shortcut for tag('main', **attrs)."""
        return self.tag("main", **attrs)

    def aside(self, **attrs: AttrValue) -> _TagContext:
        """Create an aside tag. Shortcut for tag('aside', **attrs)."""
        return self.tag("aside", **attrs)

    def strong(self, **attrs: AttrValue) -> _TagContext:
        """Create a strong tag. Shortcut for tag('strong', **attrs)."""
        return self.tag("strong", **attrs)

    def em(self, **attrs: AttrValue) -> _TagContext:
        """Create an em tag. Shortcut for tag('em', **attrs)."""
        return self.tag("em", **attrs)

    def code(self, **attrs: AttrValue) -> _TagContext:
        """Create a code tag. Shortcut for tag('code', **attrs)."""
        return self.tag("code", **attrs)

    def pre(self, **attrs: AttrValue) -> _TagContext:
        """Create a pre tag. Shortcut for tag('pre', **attrs)."""
        return self.tag("pre", **attrs)

    def img(self, **attrs: AttrValue) -> None:
        """Create an img tag. Shortcut for tag('img', **attrs).

        Note: This is a self-closing tag and doesn't need a context manager.
        """
        with self.tag("img", **attrs):
            pass

    def br(self, **attrs: AttrValue) -> None:
        """Create a br tag. Shortcut for tag('br', **attrs).

        Note: This is a self-closing tag and doesn't need a context manager.
        """
        with self.tag("br", **attrs):
            pass

    def hr(self, **attrs: AttrValue) -> None:
        """Create an hr tag. Shortcut for tag('hr', **attrs).

        Note: This is a self-closing tag and doesn't need a context manager.
        """
        with self.tag("hr", **attrs):
            pass

    def fragment(self, fragment: Fragment) -> None:
        """Insert a fragment into the document.

        This method renders the fragment and inserts its HTML content
        into the current document at the current position.

        Args:
            fragment: The Fragment instance to insert

        Example:
            def get_callout(title):
                frag = Fragment()
                with frag.div(class_="callout"):
                    frag.text(title)
                return frag

            doc = Document()
            with doc.html():
                with doc.body():
                    doc.fragment(get_callout("Warning"))
        """
        # Ensure the current tag is opened before inserting fragment content
        if self._context_stack:
            self._context_stack[-1]._ensure_opened()

        # Render the fragment and insert its content as raw HTML
        self._parts.append(fragment.render())


class Document(Fragment):
    """A minimal HTML document builder with context manager support.

    Document extends Fragment to provide a complete document building interface.
    While Fragment is designed for reusable components, Document represents
    a complete HTML document.

    The Document class inherits all methods from Fragment, including tag
    shortcuts, text(), raw(), attr(), classes(), and the fragment() method
    for composing fragments into the document.

    Example:
        doc = Document()
        with doc.html():
            with doc.head():
                with doc.title():
                    doc.text("Hello World")
            with doc.body():
                with doc.h1(class_="title"):
                    doc.text("Welcome!")
                with doc.div():
                    doc.attr("class", "special")
                    with doc.p():
                        doc.text("This is a paragraph.")

        html_output = doc.render()
    """

    pass


def document() -> Document:
    """Create a new Document instance.

    This function provides a convenient way to create Document instances.

    Returns:
        A new Document instance

    Example:
        doc = document()
        with doc.tag("html"):
            # ... build document
    """
    return Document()
