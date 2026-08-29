from PIL import Image
im = Image.open('/Users/Ashan/.gemini/antigravity-ide/brain/19078c78-6553-4706-8666-a7303377bb60/.user_uploaded/media_1787944144559.png')
# Assuming standard A4 ratio, Sinhala text is somewhere around Y=200 to 280
# Let's crop a wide horizontal strip and see
box = (50, 220, 670, 280)
cropped = im.crop(box)
cropped.save('backend/api/routers/sinhala_text.png')
print("Cropped successfully")
