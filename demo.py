from AppKit import *
from fontTools.pens.cocoaPen import CocoaPen
from compositor import Font

# a simple function that implements path caching
def getCachedNSBezierPath(glyph, font):
    if not hasattr(glyph, "nsBezierPath"):
        pen = CocoaPen(font)
        glyph.draw(pen)
        glyph.nsBezierPath = pen.path
    return glyph.nsBezierPath

# a path to a font
fontPath = aPathToYourFont

# a path to save the image to
imagePath = "demo.tiff"

# setup the layout engine
font = Font(fontPath)

# turn the aalt feature on so that we get any alternates
font.setFeatureState("aalt", True)

# process some text
glyphRecords = font.process(u"HERE IS SOME TEXT!")

# calculate the image size
pointSize = 50.0
offset = 20
scale = pointSize / font.info.unitsPerEm
imageWidth = sum([font[record.glyphName].width + record.xAdvance for record in glyphRecords]) * scale
imageWidth = int(round(imageWidth))
imageWidth += offset * 2
imageHeight = pointSize + (offset * 2)

# setup the image
image = NSImage.alloc().initWithSize_((imageWidth, imageHeight))
image.lockFocus()
# fill it with white
NSColor.whiteColor().set()
NSRectFill(((0, 0), (imageWidth, imageHeight)))
# offset and set the scale
transform = NSAffineTransform.transform()
transform.translateXBy_yBy_(offset, offset)
transform.scaleBy_(scale)
transform.translateXBy_yBy_(0, abs(font.info.descender))
transform.concat()
# iterate over the glyph records
for record in glyphRecords:
    glyph = font[record.glyphName]
    # shift for x and y placement
    transform = NSAffineTransform.transform()
    transform.translateXBy_yBy_(record.xPlacement, record.yPlacement)
    transform.concat()
    # if alternates are present, switch the color
    if record.alternates:
        NSColor.redColor().set()
    # otherwise, set the color to black
    else:
        NSColor.blackColor().set()
    # get a NSBezierPath for the glyph and fill it
    path = getCachedNSBezierPath(glyph, font)
    path.fill()
    # shift for the next glyph
    transform = NSAffineTransform.transform()
    transform.translateXBy_yBy_(record.xAdvance + glyph.width, -record.yPlacement)
    transform.concat()
# release the image
image.unlockFocus()
# write the image to disk
tiff = image.TIFFRepresentation()
tiff.writeToFile_atomically_(imagePath, False)
