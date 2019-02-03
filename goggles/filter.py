import os
import re


abv_re = re.compile(r'^[0-9]+\.?[0-9]*%?$')
style_re = re.compile(r'-[sS]tyle')

# ((country)(( |-)?([sS]tyle))? )?(type)

SRC_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = os.path.join(SRC_DIR, "..", "data")

styles_fn = "styles.txt"
breweries_fn = "breweries.txt"

styles_file = os.path.join(DATA_DIR, styles_fn)
breweries_file = os.path.join(DATA_DIR, breweries_fn)


def filter(names: list):
	pass


def filter_abv(names: list) -> list:
	for n in names:
		if not abv_re.match(n['text']):
			n['filtered'] = {"passed": True, "reason": ""}
		else:
			n['filtered'] = {"passed": False, "reason": "abv"}
	return names


def filter_styles_re(names: list) -> list:
	for n in names:
		if style_re.findall(n['text']) == [] and n['filtered']['passed']: 
			n['filtered'] = {"passed": True, "reason": ""}
		else:
			n['filtered'] = {"passed": False, "reason": "style"}
	return names


def filter_styles(names: list) -> list:
	for n in names:
		is_style = False
		if not n['filtered']['passed']:
			continue
		with open(styles_file, encoding="utf8") as f:
			for s in f:
				if n['clean_text'].lower() == s.rstrip().lower():
					is_style = True
					n['filtered'] = {"passed": False, "reason": "style"}
					break
			if not is_style:
				n['filtered'] = {"passed": True, "reason": ""}
	return names


def filter_breweries(names: list) -> list:
	for n in names:
		if 'filtered' in names and not names['filtered']['passed']:
			continue
		is_brewery = False
		with open(breweries_file, encoding="utf8") as f:
			for s in f:
				if n['clean_text'].lower() == s.rstrip().lower():
					is_brewery = True
					n['filtered'] = {"passed": False, "reason": "brewery"}
					break
			if not is_brewery:
				n['filtered'] = {"passed": True, "reason": ""}
	return names


def clean_names(names: list) -> list:
	problem_chars = ['|', '(', ')', '/']
	for n in names:
		n['clean_text'] = "".join([c if c not in problem_chars else ' ' for c in n['text']])
	return names
