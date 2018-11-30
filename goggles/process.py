import re


abv_re = re.compile(r'^[0-9]+\.?[0-9]*%?$')
style_re = re.compile(r'-[sS]tyle')

# ((country)(( |-)?([sS]tyle))? )?(type)

styles_file = "../data/styles.txt"
breweries_file = "../data/breweries.txt"


def filter(names: list):
	pass


def filter_abv(names: list) -> list:
	filtered_names = [n for n in names if not abv_re.match(n['text'])]
	return filtered_names


def filter_styles_re(names: list) -> list:
	filtered_names = [n for n in names if style_re.findall(n['text']) == []]
	return filtered_names


def filter_styles(names: list) -> list:
	filtered_names = []
	for n in names:
		is_style = False
		with open(styles_file, encoding="utf8") as f:
			for s in f:
				if n['clean_text'].lower() == s.rstrip().lower():
					is_style = True
					break
			if not is_style:
				filtered_names.append(n)
	return filtered_names


def filter_breweries(names: list) -> list:
	filtered_names = []
	for n in names:
		is_brewery = False
		with open(breweries_file, encoding="utf8") as f:
			for s in f:
				if n['clean_text'].lower() == s.rstrip().lower():
					is_brewery = True
					break
			if not is_brewery:
				filtered_names.append(n)
			else:
				print("Brewery Only:", n['clean_text'])
	return filtered_names


def clean_names(names: list) -> list:
	problem_chars = ['|', '(', ')', '/']
	for n in names:
		n['clean_text'] = "".join([c if c not in problem_chars else ' ' for c in n['text']])
	return names
