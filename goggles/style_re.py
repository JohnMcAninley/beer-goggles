import re


styles_file = "../data/styles.txt"

origins = ['american', 'belgian', 'berlin', 'berliner', 'bohemian', 'british', 
	'czech', 'english', 'german', 'irish', 'munich', 'münchen', 'münchner', 'vienna']
adjectives = []
types = ['ale', 'pale ale', 'india pale ale', 'imperial pale ale', 'ipa',
	'imperial ipa',	'double ipa', 'amber', 'amber ale', 'blonde', 'red ale',
	'brown ale',
	'lager', 'pils', 'pilsener', 'porter', 'saison',
	'stout', 'oatmeal stout', 'coffee stout', 'nitro stout', 'milk stout'
	'starkbier', 'schwarzbier', 'kolsch', 'kölsch', 'eisbock', 'doppelbock',
	'hell', 'helles', 'dunkel', 'altbier', 'märzen', 'märzenbier', 'weiss',
	'weisse', 'weissbier', 'hefeweizen', 'marzen', 'gose', 'festbier',
	'double bock', 'doublebock', 'bock', 'oktoberfestbier', 'wiesn', 'maerzen',
	'Bière de Garde',
	'barley wine', 'barleywine',
	'wit', 'witbier', 'lambic', 'oud bruin', 'dubbel', 'tripel', 'trippel',
	'double', 'triple', 'quad',
	'malt liquor', 'sour']

base_style_str = '(({})(( |-)?([sS]tyle))? )?({})'


def test_style_re(style_re) -> list:
	matches = []
	misses = []
	with open(styles_file, encoding="utf8") as f:
		for s in f:
			if style_re.match(s.rstrip().lower()):
				matches.append(s.rstrip())
			else:
				misses.append(s.rstrip())
	return (matches, misses)


def build_style_re():
	origin_opts = "|".join(origins)
	type_opts = "|".join(types)
	style_str = base_style_str.format(origin_opts, type_opts)
	style_re = re.compile(style_str)
	return style_re


if __name__ == "__main__":
	style_re = build_style_re()
	matches, misses = test_style_re(style_re)
	print("MATCHES:")
	for m in matches:
		print("\t", m)
	print("MISSES:")
	for m in misses:
		print("\t", m)
	print("matches:", len(matches))
	print("misses:", len(misses))
