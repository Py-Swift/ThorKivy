from PIL import Image
from collections import Counter

img = Image.open('thorkivy_demo.png')
w, h = img.size
print(f'Size: {w}x{h}')

print('--- Background (should be green 0,128,0 if Kivy canvas preserved) ---')
for x, y in [(10,10), (10,h-10), (w-10,10), (w-10,h-10), (w//2,h//2)]:
    print(f'  ({x},{y}) = {img.getpixel((x,y))[:4]}')

print('--- Shape areas ---')
print(f'  rect (150,{h-110}): {img.getpixel((150,h-110))[:4]}')
print(f'  circle (150,{h-320}): {img.getpixel((150,h-320))[:4]}')
print(f'  rrect (400,{h-110}): {img.getpixel((400,h-110))[:4]}')
print(f'  tri (400,{h-310}): {img.getpixel((400,h-310))[:4]}')
print(f'  quad (640,{h-130}): {img.getpixel((640,h-130))[:4]}')

colors = Counter()
for sx in range(0, w, 10):
    for sy in range(0, h, 10):
        colors[img.getpixel((sx,sy))[:3]] += 1
print('--- Top 10 colors (rgb) ---')
for c, n in colors.most_common(10):
    print(f'  {c}: {n}')
