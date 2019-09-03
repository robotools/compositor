compositor
==========

A basic OpenType GSUB and GPOS layout engine written in Python.


Table of Contents
-----------------

- [Usage Reference](#usage-reference)
    - [Assumptions](#assumptions)
    - [The Font Object](#the-font-object)
     - [The GlyphRecord Object](#the-glyphrecord-object)
     - [The Glyph Object](#the-glyph-object)
     - [The Info Object](#the-info-object)
- [Development](#development)
- [Installation](#installation)


- - -


Usage Reference
---------------

This document covers the basic usage of the compositor package. For more detailed information read the documentation strings in the source.

### Assumptions

Some assumptions about the OpenType fonts being used are made by the package:

* The font is valid.
* The font's `cmap` table contains Platform 3 Encoding 1.
* The font does not contain `GSUB` or `GPOS` lookup types that are not supported by the GSUB or GPOS objects. If an unsupported lookup type is present, the lookup will simply be ignored. It will not raise an error.

### The Font Object

#### Importing

```python
from compositor import Font
```

#### Construction

```python
font = Font(path)
```

<dl>
  <dt>path
  <dd>A path to an OpenType font.
</dl>

#### Special Behavior

```python
glyph = font["aGlyphName"]
```

Returns the glyph object named `aGlyphName`. This will raise a `KeyError` if `aGlyphName` is not in the font.

```python
isThere = "aGlyphName" in font
```

Returns a boolean representing if `aGlyphName` is in the font.

#### Methods

```python
font.keys()
```

A list of all glyph names in the font.

```python
glyphRecords = font.process(aString)
```

This is the most important method. It takes a string (Unicode or plain ASCII) and processes it with the features defined in the font's `GSUB` and `GPOS` tables. A list of `GlyphRecord` objects will be returned.

```python
featureTags = font.getFeatureList()
```

A list of all available features in GSUB and GPOS.

```python
state = font.getFeatureState(featureTag)
```

Get a boolean representing if a feature is on or not. This assumes that the feature state is consistent in both the GSUB and GPOS tables. A `CompositorError` will be raised if the feature is inconsistently applied. A `CompositorError` will be raised if featureTag is not defined in GSUB or GPOS.

```python
font.setFeatureState(self, featureTag, state)
```

Set the application state of a feature.

#### Attributes

<dl>
  <dt>info
  <dd>The Info object for the font.
</dl>

### The GlyphRecord Object

#### Attributes

<dl>

  <dt>glyphName
  <dd>The name of the referenced glyph.

  <dt>xPlacement
  <dd>Horizontal placement.

  <dt>yPlacement
  <dd>Vertical placement.

  <dt>xAdvance
  <dd>Horizontal adjustment for advance.

  <dt>yAdvance
  <dd>Vertical adjustment for advance.

  <dt>alternates
  <dd>A list of `GlyphRecords` indicating alternates for the glyph.

</dl>

### The Glyph Object

#### Methods

```python
glyph.draw(pen)
```

Draws the glyph with a FontTools pen.

#### Attributes

<dl>

  <dt>name
  <dd>The name of the glyph.

  <dt>index
  <dd>The glyph's index within the source font.

  <dt>width
  <dd>The width of the glyph.

  <dt>bounds
  <dd>The bounding box for the glyph. Formatted as `(xMin, yMin, xMax, yMax)`. If the glyph contains no outlines, this will return `None`.

</dl>

### The Info Object

#### Attributes

- familyName
- styleName
- unitsPerEm
- ascender
- descender


Development
-----------

### Relationship to the GSUB and GPOS Specification

The Compositor GSUB and GPOS tables adhere as closely as possible to the GSUB and GPOS specification. Every effort has been made to keep terminology consistent. All known deviations from the spec are documented. (The deviations are generally trivial. For example, most the of the subtables don't implement the `Count` attributes. This is done because the Python iterator provides a more convenient and faster way to deal with iteration than creating a range. Therefore, the `Count` objects are not needed.)

### Object Loading

For performance reasons, when a new font is loaded, all of the GSUB and GPOS data is extracted from the font with fontTools. The data is placed into compositor objects. These objects are then used to process text. This initial loading can be relatively expensive, but the processing speed of the objects is worth the initial expense.


Installation
------------

To install this package, type the following in the command line:

```
python setup.py install
```
