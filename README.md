### Setup venv
```bash
python -m venv .venv
``` 

```bash
# windows:
.\.venv\Scripts\activate
# linux:
source ./.venv/bin/activate
```

```bash
pip install -r requirements.txt
``` 

### Run main.py
```bash
python main.py <https://open.spotify.com/playlist/<GUID>>
```
### Add empty rows between the grouped songs
Go through the csv add empty rows to delimit new pages

### run webapp
```bash
python flaskapp.py
```

### open the game
Go to http://127.0.0.1:5000 in your browser
