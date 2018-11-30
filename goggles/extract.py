import cv2
import PIL
import pprint
import pytesseract

import fetch
import display
import process

image_file = '../images/maxs_excerpt.jpg'
#image_file = 'noisy.png'
page_seg_mode = 11	# Parse sparse text


def group_names(data):
	d2 = dict2list(data)
	non_empty_blocks = [b for b in d2 if b['text']]
	block_nums = set([b['block_num'] for b in non_empty_blocks])
	names = []
	for bn in block_nums:
		this_block = [b for b in non_empty_blocks if b['block_num'] == bn]
		names.append({
			'block_num': bn,
			'text': " ".join([b['text'] for b in this_block]),
			'left': min([b['left'] for b in this_block]),
			'top': max([b['top'] for b in this_block]),
			'right': max([b['left'] + b['width'] for b in this_block]),
			'bottom': max([b['top'] + b['height'] for b in this_block])
		})
	return names


def dict2list(d):
	"""
	Assumes list for each key is same length.
	"""
	return [{k: d[k][i] for k in d} for i in range(len(list(d.values())[0]))]


def add_rating(name, score):
	ratings[name] = score
	print("Added {}: {}".format(name, score))


pytesseract.pytesseract.tesseract_cmd = 'D:/Program Files (x86)/Tesseract-OCR/tesseract'

image = cv2.imread(image_file)
cv2.imshow("Rating", image)
cv2.waitKey(1)

"""
print("OCR (STRING)")
text = pytesseract.image_to_string(PIL.Image.open(image_file),
	config='--psm {}'.format(page_seg_mode),
	output_type=pytesseract.Output.DICT)

lines = text['text'].split('\n')
lines_stripped = [l for l in lines if l]
print("\toutput:\t\t", text)
print("\tlines:\t\t", lines)
print("\tnon-empty lines:", lines_stripped)
"""
"""
print("BOXES")
boxes = pytesseract.image_to_boxes(PIL.Image.open(image_file), output_type=pytesseract.Output.DICT)
pprint.pprint(boxes)
"""
print("OCR (DATA)")
data = pytesseract.image_to_data(PIL.Image.open(image_file),
	config='--psm {}'.format(page_seg_mode),
	output_type=pytesseract.Output.DICT)
pprint.pprint(data, indent=8)

"""
print("OSD")
osd = pytesseract.image_to_osd(PIL.Image.open(image_file), output_type=pytesseract.Output.DICT)
pprint.pprint(osd)
"""

# Simple approach to forming beer names from words returned by tesseract by
# grouping by blocks.
names = group_names(data)
print("names:", [n['text'] for n in names])

box_image = image.copy()
display.draw_boxes(box_image, names)
cv2.imshow("Rating", box_image)
cv2.waitKey(1)

cleaned_names = process.clean_names(names)
pprint.pprint(cleaned_names)

filtered_names = process.filter_abv(cleaned_names)
filtered_names = process.filter_styles_re(filtered_names)

filtered_names = process.filter_breweries(filtered_names)

filtered_box_image = image.copy()
print("filtered_names:", filtered_names)
display.draw_boxes(filtered_box_image, filtered_names)
cv2.imshow("Rating", filtered_box_image)
cv2.waitKey(1)

ratings = fetch.async_search_beers([n['clean_text'] for n in filtered_names])
longest = max([len(r) for r in ratings])
for n in sorted(ratings, key=lambda n: ratings[n], reverse=True):
	print("{}:{}\t{}".format(n, ' '*(longest-len(n)), ratings[n]))

filtered_box_image2 = image.copy()
for n in ratings:
	box = next(b for b in cleaned_names if b['clean_text'] == n)
	display.write_rating(filtered_box_image, (box['right'], box['bottom']), ratings[n])

cv2.imshow("Rating", filtered_box_image)
cv2.waitKey(1)
"""
sync_ratings = {}
for n in filtered_names:
	sync_ratings[n['text']] = fetch.search_beers(n['text'])
	if not sync_ratings[n['text']]:
		continue
	display.write_rating(filtered_box_image2, (n['right'], n['top']), sync_ratings[n['text']])
	cv2.imshow("Rating 2", filtered_box_image2)
	cv2.waitKey(1)
print(sync_ratings)
"""
cv2.waitKey(0)
