#!/usr/bin/python3

import sys

import cgi
import cgitb

sys.path.append("..")
print(sys.path)

from goggles import extract

cgitb.enable()

print("Content-type: text/html\n\n")

# Get image from form
form = cgi.FieldStorage()
photo = form.getvalue('photo')

# Call extract
output = extract.extract(photo)

# Generate output page

# Write temp photo file
output.processed_image
cv2.imwrite()

# Depending on output options


# Generate chart of beers and ratings

# Additional Data
# OCR: raw read data, corrected data, filtered out data
# BA: beers not found
