"""Generate the app icon from the same simple geometry as assets/fretglow.svg."""
from pathlib import Path
from PIL import Image,ImageDraw

root=Path(__file__).resolve().parent/'assets'
image=Image.new('RGBA',(256,256));draw=ImageDraw.Draw(image)
draw.rounded_rectangle((0,0,255,255),radius=56,fill='#201D2B')
draw.polygon([(52,55),(204,55),(190,154),(128,218),(66,154)],fill='#BCA7E8')
draw.polygon([(65,66),(191,66),(179,147),(128,200),(77,147)],fill='#30283F')
for y,width,colour in [(83,88,'#D6C9F0'),(105,78,'#C2ACE9'),(127,66,'#AC8ADC'),(149,48,'#EDAA87'),(171,24,'#F3C1A6')]:
    draw.rounded_rectangle((128-width/2,y-6,128+width/2,y+6),radius=6,fill=colour)
image.save(root/'fretglow.ico',sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
image.save(root/'fretglow.png')
