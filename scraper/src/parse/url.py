import urllib.parse


def brewery_id(url):
	"""
	Extract the brewery's ID from the URL for a brewery profile in the form
	"/beer/profile/[brewery_id]" or from the URL for a beer in the form 
	"/beer/profile/[brewery_id]/[beer_id]".

	Raises:
		Error if the URL is not one of the above forms.
	"""
	path = urllib.parse.urlparse(url).path
	path_parts = [p for p in path.split('/') if p is not '']
	if len(path_parts) < 3:
		raise ValueError("Incorrect URL format.")
	if path_parts[0] != "beer" or path_parts[1] != "profile":
		raise ValueError("Incorrect URL format.")
	brewery_id = path_parts[2]
	return brewery_id


def beer_id(url):
	"""
	Extract the beer ID from the URL for a beer profile in the form 
	"/beer/profile/[brewery_id]/[beer_id]".

	Raises:
		Error if the URL is not the above forms.
	"""
	path = urllib.parse.urlparse(url).path
	path_parts = [p for p in path.split('/') if p is not '']
	if len(path_parts) < 4:
		raise ValueError("Incorrect URL format.")
	if path_parts[0] != "beer" or path_parts[1] != "profile":
		raise ValueError("Incorrect URL format.")
	beer_id = path_parts[3]
	return beer_id
