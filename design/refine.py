from make_avatar import ground, grain, draw_glyph, circle_preview, S, INK, FONTS
from PIL import Image

# Refinement pass: the glyph carries more of the circle (presence at 40px),
# and the light behind it is the only "effect" allowed.
img = ground()
draw_glyph(img, "?", f"{FONTS}/InstrumentSerif-Regular.ttf", 0.70)
img = grain(img, 4)
img.save("avatar-FINAL.png")

# side by side: first pass vs refined, at feed size and at profile size
a = Image.open("avatar-A-question.png")
sheet = Image.new("RGB", (2*300, 300+140), (18,18,18))
for i, im in enumerate([a, img]):
    sheet.paste(circle_preview(im, 240), (i*300+30, 20))
    sheet.paste(circle_preview(im, 40), (i*300+130, 275))
sheet.save("_refine-compare.png")
print("A (0.62)  vs  FINAL (0.70)")
