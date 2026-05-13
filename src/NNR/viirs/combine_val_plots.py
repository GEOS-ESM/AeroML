from PIL import Image
import os


ret = 'dtocean'

# List of your PNG files (change these to your actual filenames)
image_files = [
        f'val_{ret}_plots/kde2d_{ret}_outliers_std.png',
        f'val_{ret}_plots/kde2d_{ret}_outliers_nnr.png'
        ]
out_file = f'val_{ret}_plots/kde2d_{ret}_outliers.png'

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
max_height = max(heights)
total_height = sum(heights)
total_width = sum(widths)

# Add a small gap between images (e.g., 5 pixels)
gap = 0
total_height += gap * (len(images) - 1)
total_width  += gap * (len(images) - 1)

# Create a new blank image
#combined = Image.new('RGB', (max_width, total_height), (255, 255, 255))
combined = Image.new('RGB', (total_width, max_height), (255, 255, 255))

# Paste each image
#y_offset = 0
#for img in images:
#    combined.paste(img, (0, y_offset))
#    y_offset += img.height + gap

x_offset = 0
for img in images:
    combined.paste(img, (x_offset, 0))
    x_offset += img.width + gap


# Save the combined image
combined.save(out_file)
print(f"Images combined and saved as {out_file}")
