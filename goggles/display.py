import cv2


def write_rating(image, bottomLeft, score):
	font = cv2.FONT_HERSHEY_SIMPLEX
	fontScale = 1
	fontColor = score_color(score)
	lineType = 2
	cv2.putText(image, score, bottomLeft, font, fontScale, fontColor, lineType)


def score_color(score):
	# TEMP
	return (255, 0, 0)
	if isinstance(score, str):
		score = float(score)
	if 4.50 <= score <= 5.00:    # World-Class
		return (255, 0, 0)
	elif 4.25 <= score <= 4.49:  # Outstanding
		return (255, 127, 0)
	elif 4.00 <= score <= 4.24:  # Exceptional
		return (255, 255, 0)
	elif 3.75 <= score <= 3.99:  # Very Good
		return (127, 255, 0)
	elif 3.50 <= score <= 3.74:  # Good
		return (0, 255, 127)
	elif 3.00 <= score <= 3.49:  # Okay
		return (0, 255, 255)
	elif 2.00 <= score <= 2.99:  # Poor
		return (0, 127, 255)
	elif 1.00 <= score <= 1.99:  # Awful
		return (0, 0, 255)
	else:
		return (0, 0, 0)


def draw_boxes(img, names):
	thickness = 2
	color = (0, 0, 255)
	for n in names:
		print(n['text'], "top", n['top'], "left", n['left'], "bottom", n['bottom'], "right", n['right'])
		cv2.rectangle(img, (n['left'], n['top']), (n['right'], n['bottom']), color, thickness)
