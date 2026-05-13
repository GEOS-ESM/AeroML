from PIL import Image
import os

ret = 'tau'
prod = 'merged'
image_files = [
        f'seasonal_maps/2019MAM/combined_{ret}_{prod}_2019MAM.pdf',
        f'seasonal_maps/2019JJA/combined_{ret}_{prod}_2019JJA.pdf',
        f'seasonal_maps/2019SON/combined_{ret}_{prod}_2019SON.pdf',
        f'seasonal_maps/2019DJF/combined_{ret}_{prod}_2019DJF.pdf'
        ]
out_file = f'seasonal_maps/combined_{ret}_{prod}_2019.pdf'


# Open all images and check their sizes
images = []
widths = []
heights = []

for file in image_files:
    if os.path.exists(file):
        img = Image.open(file)
        images.append(img)
        widths.append(img.width)
        heights.append(img.height)
    else:
        print(f"Warning: File {file} not found!")

if not images:
    print("No images found!")
    exit()

# Get the max width and total height
max_width = max(widths)
total_height = sum(heights)

# Add a small gap between images (e.g., 5 pixels)
gap = 5
total_height += gap * (len(images) - 1)

# Create a new blank image
combined = Image.new('RGB', (max_width, total_height), (255, 255, 255))

# Paste each image
y_offset = 0
for img in images:
    combined.paste(img, (0, y_offset))
    y_offset += img.height + gap

# Save the combined image
combined.save(out_file)
print(f"Images combined and saved as {out_file}")
