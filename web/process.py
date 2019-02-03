#!/usr/bin/python3

import os
import sys

import cgi
import cgitb

import cv2

cgitb.enable()

print("Content-type: text/html\n\n")

WEB_DIR = os.path.dirname(os.path.realpath(__file__))
SRC_DIR = os.path.join(WEB_DIR, "..")
sys.path.append(SRC_DIR)
#print(sys.path)

import goggles.extract


WEB_ROOT = "/var/www/html"
IMG_REL_DIR = "goggles/img"
UPLOAD_REL_DIR = "upload"
OUTPUT_REL_DIR = "output"
UPLOAD_WEB_DIR = os.path.join(IMG_REL_DIR, UPLOAD_REL_DIR)
OUTPUT_WEB_DIR = os.path.join(IMG_REL_DIR, OUTPUT_REL_DIR)

UPLOAD_FULL_DIR = os.path.join(WEB_ROOT, UPLOAD_WEB_DIR)
OUTPUT_FULL_DIR = os.path.join(WEB_ROOT, OUTPUT_WEB_DIR)


def upload_img():
  
	# Get image from form
	form = cgi.FieldStorage()
	photo = form['photo']

	fn = os.path.basename(photo.filename)
	#print("fn:", fn, "<br>")

	fp = os.path.join(UPLOAD_FULL_DIR, fn)
	#print("fp:", fp, "<br>")

	# TODO Duplicate filenames?
	open(fp, 'wb').write(photo.file.read())

	#print("Wrote file to {}.<br>".format(fp))
	#img_web_path = os.path.join("/", UPLOAD_WEB_DIR, fn)
	#print("<img src={}><br>".format(img_web_path))
	#print("<br>")
	
	return fp


# Get image from form
form = cgi.FieldStorage()
photo = form['photo']
#print(form)
#print(photo)

fn = os.path.basename(photo.filename)
#print("fn:", fn, "<br>")

fp = os.path.join(UPLOAD_FULL_DIR, fn)
#print("fp:", fp, "<br>")

# TODO Duplicate filenames?
open(fp, 'wb').write(photo.file.read())

#print("Wrote file to {}.<br>".format(fp))
#img_web_path = os.path.join("/", UPLOAD_WEB_DIR, fn)
#print("<img src={}><br>".format(img_web_path))
#print("<br>")

# Call extract
output = goggles.extract.extract(fp)
output_img = output["img"]

# Generate performance table
print("""
  <h3>Performance</h3>
  <table>
    <tr>
      <th>Segment</th>
      <th>Time(ms)</th> 
    </tr>""")

for s in output["perf"]:
  print("""
    <tr>
      <td>{}</td>
      <td>{}</td>
    </tr>""".format(s, output["perf"][s]))

print("</table>")

# Write temp photo file
output_fp = os.path.join(OUTPUT_FULL_DIR, photo.filename)
cv2.imwrite(output_fp, output_img)

#print("Wrote file to {}.<br>".format(output_fp))
output_img_web_path = os.path.join("/", OUTPUT_WEB_DIR, photo.filename)
#print("Wrote file to {}<br>.".format(fp))
img_web_path = os.path.join("/", UPLOAD_WEB_DIR, fn)
print("<img src={}>".format(output_img_web_path))
print("<br>")

# Depending on output options


# Generate chart of beers and ratings

# Additional Data
# OCR: raw read data, corrected data, filtered out data
# BA: beers not found

print("""
	<table>
		<tr>
			<th>Name</th>
			<th>Brewery</th>
			<th>Rating</th>
			<th>Ratings</th>
			<th>OCR Raw Text</th>
			<th>Clean Text</th>
			<th>Filtered?</th>
		</tr>""")

for n in output["names"]:
	print("\t<tr>")
	print("\t\t<td>{}</td>".format(n["name"]))
	print("\t\t<td>{}</td>".format(n["brewery"]))
	print("\t\t<td>{}</td>".format(n["rating"]))
	print("\t\t<td>{}</td>".format(n["rating_count"]))
	print("\t\t<td>{}</td>".format(n["text"]))
	print("\t\t<td>{}</td>".format(n["clean_text"]))
	print("\t\t<td>{}</td>".format("" if n["filtered"]["passed"] else n["filtered"]["reason"]))

print("</table>")
