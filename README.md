# Markupflow

<p align="center">
    <em>Generate HTML, the Pythonic way</em>
</p>

[![build](https://github.com/frankie567/markupflow/workflows/Build/badge.svg)](https://github.com/frankie567/markupflow/actions)
[![codecov](https://codecov.io/gh/frankie567/markupflow/branch/master/graph/badge.svg)](https://codecov.io/gh/frankie567/markupflow)
[![PyPI version](https://badge.fury.io/py/markupflow.svg)](https://badge.fury.io/py/markupflow)

---

**Documentation**: <a href="https://frankie567.github.io/markupflow/" target="_blank">https://frankie567.github.io/markupflow/</a>

**Source Code**: <a href="https://github.com/frankie567/markupflow" target="_blank">https://github.com/frankie567/markupflow</a>

---

## Quickstart

### Installation

Install markupflow using pip:

```bash
pip install markupflow
```

Or with uv:

```bash
uv add markupflow
```

### Basic Usage

Here's a simple example to generate an HTML document:

```python
from markupflow import Document

# Create a document
doc = Document()

# Build your HTML structure
with doc.tag("html", lang="en"):
    with doc.tag("head"):
        with doc.tag("title"):
            doc.text("My Page")
    with doc.tag("body"):
        with doc.h1():
            doc.text("Hello, World!")
        with doc.p(class_="intro"):
            doc.text("Welcome to markupflow!")

# Get the HTML output
html = doc.render()
print(html)
```

This generates:

```html
<html lang="en"><head><title>My Page</title></head><body><h1>Hello, World!</h1><p class="intro">Welcome to markupflow!</p></body></html>
```

## Features

### Tag Shortcuts

Markupflow provides shortcuts for common HTML tags:

```python
from markupflow import Document

doc = Document()

with doc.html(lang="en"):
    with doc.head():
        with doc.title():
            doc.text("Shortcuts Example")
    with doc.body():
        with doc.h1(id="main-title"):
            doc.text("Main Title")
        with doc.div(class_="container"):
            with doc.p():
                doc.text("First paragraph")
            with doc.p():
                doc.text("Second paragraph")
        # Self-closing tags
        doc.br()
        doc.hr()
        doc.img(src="image.jpg", alt="Example")

print(doc.render())
```

### Dynamic Attributes

Add attributes conditionally using the `attr()` method:

```python
from markupflow import Document

doc = Document()

user_is_admin = True
show_tooltip = False

with doc.div():
    if user_is_admin:
        doc.attr("class", "admin-panel")
        doc.attr("data-role", "administrator")
    if show_tooltip:
        doc.attr("title", "Admin panel")
    doc.text("Content that changes based on conditions")

print(doc.render())
# Output: <div class="admin-panel" data-role="administrator">Content that changes based on conditions</div>
```

### Dynamic Classes

Add CSS classes conditionally using the `classes()` method. When classes already exist, new ones are appended:

```python
from markupflow import Document

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
    doc.text("Panel content")

print(doc.render())
# Output: <div class="panel admin active">Panel content</div>
```

### HTML Escaping

Markupflow automatically escapes content for security:

```python
from markupflow import Document

doc = Document()

with doc.p():
    doc.text("Hello & <world> \"test\"")

print(doc.render())
# Output: <p>Hello &amp; &lt;world&gt; &quot;test&quot;</p>

# For trusted content, use raw()
with doc.div():
    doc.raw("<em>Already escaped</em>")

print(doc.render())
# Output: <div><em>Already escaped</em></div>
```

### Attribute Name Conversion

Python attribute names are automatically converted to HTML format:

```python
from markupflow import Document

doc = Document()

with doc.div(
    class_="container",      # class_ -> class
    data_value="123",        # data_value -> data-value
    aria_label="button"      # aria_label -> aria-label
):
    doc.text("Content")

print(doc.render())
# Output: <div class="container" data-value="123" aria-label="button">Content</div>
```

### Document Reuse

Clear and reuse the same document object:

```python
from markupflow import Document

doc = Document()

# First use
with doc.p():
    doc.text("First content")

html1 = doc.render()

# Clear and reuse
doc.clear()

with doc.h1():
    doc.text("Second content")

html2 = doc.render()

print(html1)  # <p>First content</p>
print(html2)  # <h1>Second content</h1>
```

### Error Handling

Markupflow provides specific exception classes:

```python
from markupflow import Document, MarkupFlowError

doc = Document()

try:
    # This will raise NoTagContextError
    doc.attr("class", "test")
except MarkupFlowError as e:
    print(f"Caught markupflow error: {e}")

try:
    with doc.div():
        doc.text("Content")
        # This will raise TagAlreadyOpenedError
        doc.attr("class", "test")
except MarkupFlowError as e:
    print(f"Caught markupflow error: {e}")
```

## Reusable Components with Fragments

Markupflow supports creating reusable HTML components using the `Fragment` class. Fragments allow you to define components independently without carrying document instances around.

### Creating Finished Fragments

Finished fragments are complete, self-contained HTML components:

```python
from markupflow import Fragment, Document

def alert(message, severity="info"):
    """Create an alert component."""
    fragment = Fragment()
    with fragment.div(class_=f"alert alert-{severity}"):
        fragment.text(message)
    return fragment

def card(title, content):
    """Create a card component."""
    fragment = Fragment()
    with fragment.div(class_="card"):
        with fragment.div(class_="card-header"):
            with fragment.h3():
                fragment.text(title)
        with fragment.div(class_="card-body"):
            fragment.text(content)
    return fragment

# Use fragments in a document
doc = Document()
with doc.tag("body"):
    doc.fragment(alert("Welcome!", "success"))
    doc.fragment(alert("Please note", "warning"))
    doc.fragment(card("Getting Started", "Learn the basics"))

print(doc.render())
```

### Creating Expandable Fragments

Expandable fragments use context managers to allow dynamic content addition:

```python
import contextlib
from markupflow import Fragment, Document

@contextlib.contextmanager
def button(btn_type="button"):
    """Create an expandable button fragment."""
    fragment = Fragment()
    with fragment.button(type=btn_type, class_="btn"):
        yield fragment

@contextlib.contextmanager
def card_with_body(title):
    """Create a card where the body can be filled dynamically."""
    fragment = Fragment()
    with fragment.div(class_="card"):
        with fragment.div(class_="card-header"):
            fragment.text(title)
        with fragment.div(class_="card-body"):
            yield fragment

# Use expandable fragments
doc = Document()
with doc.tag("body"):
    # Button with custom content
    with doc.fragment(button("submit")) as btn:
        btn.text("Submit Form")
    
    # Card with dynamic body content
    with doc.fragment(card_with_body("User Info")) as card_body:
        with card_body.p():
            card_body.text("Name: John Doe")
        with card_body.p():
            card_body.text("Email: john@example.com")

print(doc.render())
```

### Composing Fragments

Fragments can contain other fragments, enabling complex component hierarchies:

```python
from markupflow import Fragment, Document

def icon(name):
    """Create an icon fragment."""
    fragment = Fragment()
    with fragment.span(class_=f"icon icon-{name}"):
        fragment.text(f"[{name}]")
    return fragment

def button_with_icon(text, icon_name):
    """Create a button with an icon."""
    fragment = Fragment()
    with fragment.button(class_="btn"):
        fragment.fragment(icon(icon_name))
        fragment.text(f" {text}")
    return fragment

# Use composed fragments
doc = Document()
with doc.tag("body"):
    doc.fragment(button_with_icon("Save", "save"))
    doc.fragment(button_with_icon("Delete", "trash"))

print(doc.render())
```

## Development

### Setup environment

We use [uv](https://docs.astral.sh/uv/) to manage the development environment and production build, and [just](https://github.com/casey/just) to manage command shortcuts. Ensure they are installed on your system.

### Run unit tests

You can run all the tests with:

```bash
just test
```

### Format the code

Execute the following command to apply linting and check typing:

```bash
just lint
```

### Publish a new version

You can bump the version, create a commit and associated tag with one command:

```bash
just version patch
```

```bash
just version minor
```

```bash
just version major
```

Your default Git text editor will open so you can add information about the release.

When you push the tag on GitHub, the workflow will automatically publish it on PyPi and a GitHub release will be created as draft.

## Serve the documentation

You can serve the Mkdocs documentation with:

```bash
just docs-serve
```

It'll automatically watch for changes in your code.

## License

This project is licensed under the terms of the MIT license.
