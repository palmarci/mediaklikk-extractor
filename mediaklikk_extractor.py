import requests
import re
import json
from time import sleep

setup_pattern = r'pl\.setup(.*?)\)\;'
player_url = "https://player.mediaklikk.hu/playernew/player.php?video="
stream_url = 'https://m4sport.hu/wp-content/plugins/hms-global-widgets/interfaces/streamJSONs/StreamSelector.json'
wait_time = 0.2 # seconds

def get_player_data(stream):
	url = player_url + stream

	payload = {}
	headers = {
		'Referer': 'https://m4sport.hu/',
	}

	r = requests.request("GET", url, headers=headers, data=payload)
	if r.status_code != 200:
		raise Exception(f"Got {r.status_code} from server!")
	return r.text

def get_setup_data(response):
	#input_text = response.replace("\n", "")
	input_text = response
	match = re.search(setup_pattern, input_text, re.DOTALL)

	if match is None:
			raise Exception("Could not extract setup config!")

	setup_text = match.group(0)
	setup_text = setup_text.strip('pl.setup(') # strip from the beginning
	setup_text = setup_text.strip(');') # strip from the end
	setup_text = setup_text.replace('\/', '/') # fix forward slashes
	setup_text = bytes(setup_text, 'utf-8').decode('unicode_escape') # unicode escape

	try:
		setup_json = json.loads(setup_text)
	except json.JSONDecodeError:
		raise Exception("Could not decode setup config!")

	return setup_json

def get_stream_list():
	r = requests.get(stream_url)
	if r.status_code != 200:
		raise Exception(f"Coult not get stream list, server returned {r.status_code}")
	
	try:
		js = json.loads(r.text)
	except json.JSONDecodeError:
		raise Exception("Could not parse stream list data")
	
	streams = set()
	for i in js['streams']:
		streams.add(i['code'])
	
	return sorted(list(streams))

def main():
	for stream in get_stream_list():
		try:
			html_response = get_player_data(stream)
			setup_data = get_setup_data(html_response)
			if setup_data['playlist'][0]['type'] == 'hls':
				url = setup_data['playlist'][0]['file']
				print(f'{stream} : {url}')
			sleep(wait_time) # just to be on the safe side
		except Exception as e:
				print(f'{stream} : failed: {e}')

if __name__ == "__main__":
	main()