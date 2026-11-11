"""
Spotify Quiz Slideshow — Flask app.

Reads playlist_tracks.csv (song_name, artist_name, embed_link, artist_image_url).
Each empty row in the CSV starts a new page (round). Each page shows the artist
image with a play button on top; clicking it toggles the Spotify embed player.
Song titles are hidden (quiz mode) — a "Reveal" button shows the answer.

Run:
    pip install flask
    python app.py
    -> open http://127.0.0.1:5000
"""

import csv

from flask import Flask, render_template_string

CSV_PATH = "output.csv"

app = Flask(__name__)


def load_rounds(csv_path=CSV_PATH):
    """Return a list of rounds; an empty row starts a new round."""
    rounds = [[]]
    with open(csv_path, newline="", encoding="utf-8") as f:
        lines = [',' if line.isspace() else line for line in f][1:]# Skip header

        for row in csv.DictReader(lines, fieldnames=["song_name", "artist_name", "embed_link", "artist_image_url"],restval=""):
            print(row.values())
            if not any((v or "").strip() for v in row.values()):
                rounds.append([])
                continue
            rounds[-1].append({
                "song": (row.get("song_name") or "").strip(),
                "artist": (row.get("artist_name") or "").strip(),
                "embed": (row.get("embed_link") or "").strip(),
                "image": (row.get("artist_image_url") or "").strip(),
            })
    return [r for r in rounds if r]


TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Music Quiz</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: #121212; color: #fff;
         min-height: 100vh; display: flex; flex-direction: column; align-items: center; }
  header { width: 100%; padding: 16px; text-align: center; }
  .round-label { color: #1db954; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; }
  .grid { display: flex; flex-wrap: wrap; gap: 28px; justify-content: center;
          padding: 24px; max-width: 1100px; }
  .card { width: 240px; text-align: center; }
  .cover { position: relative; width: 240px; height: 240px; border-radius: 12px;
           overflow: hidden; cursor: pointer; background: #282828; }
  .cover img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .play-btn { position: absolute; inset: 0; display: flex; align-items: center;
              justify-content: center; background: rgba(0,0,0,.35); transition: .2s; }
  .card.playing .play-btn { opacity: 0; pointer-events: none; }
  .play-btn span { width: 72px; height: 72px; border-radius: 50%; background: #1db954;
                   display: flex; align-items: center; justify-content: center;
                   font-size: 30px; color: #000; }
  .player { display: none; margin-top: 10px; position: relative;}
  /* Spotify's own title sits in the top ~44px of the embed.
     This overlay hides it (cross-origin CSS can't reach inside the iframe). */
  .title-shield { position: absolute; top: 0; left: 0; right: 0; height: 100%;
                  background: #181818; border-radius: 12px 12px 0 0; z-index: 5;
                  display: flex; align-items: center; justify-content: center;
                  color: #1db954; font-size: 14px; letter-spacing: 3px; }
  .title-shield::after { content: "𝅘𝅥𝅮 QUIZ 𝅘𝅥𝅮"; }
  .card.playing .player { display: block; opcacity: 0.1; }
  .card.playing .cover { width: 240px; height: 152px; }
  .card.playing .cover img { filter: blur(6px) brightness(.6); }
  .reveal { margin-top: 10px; background: none; border: 1px solid #535353; color: #b3b3b3;
            padding: 6px 14px; border-radius: 20px; cursor: pointer; font-size: 13px; }
  .answer { display: none; margin-top: 8px; font-weight: 600; }
  .card.revealed .answer { display: block; }
  .card.revealed .reveal { display: none; }
  nav { padding: 20px; display: flex; gap: 16px; }
  nav a { background: #1db954; color: #000; text-decoration: none; font-weight: 700;
          padding: 10px 22px; border-radius: 24px; }
  nav a:disabled { opacity: .3; }
</style>
</head>
<body>
<header>
  <div class="round-label">Round {{ page + 1 }} / {{ rounds|length }}</div>
</header>

<div class="grid">
  {% for track in rounds[page] %}
  <div class="card" id="card-{{ loop.index }}">
    <div class="cover" onclick="toggle({{ loop.index }})">
      <img src="{{ track.image }}" alt="Mystery artist" onerror="this.style.display='none'">
      <div class="play-btn"><span>&#9654;</span></div>
    </div>
    <div class="player">
      <div id="embed-{{ loop.index }}"></div>
      <div class="title-shield"></div>
    </div>
    <button class="reveal" onclick="reveal({{ loop.index }})">Reveal answer</button>
    <div class="answer">{{ track.artist }} — {{ track.song }}</div>
  </div>
  {% endfor %}
</div>

<nav>
  {% if page > 0 %}<a href="/{{ page - 1 }}">&#8592; Previous</a>{% endif %}
  {% if page < rounds|length - 1 %}<a href="/{{ page + 1 }}">Next round &#8594;</a>{% endif %}
</nav>

<script src="https://open.spotify.com/embed/iframe-api/v1" async></script>
<script>
let controllers = {};

window.onSpotifyIframeApiReady = (IFrameAPI) => {
  const embedUrls = {{ embed_urls | tojson }};
  embedUrls.forEach((url, idx) => {
    const el = document.getElementById('embed-' + (idx + 1));
    if (!el) return;
    IFrameAPI.createController(el, { uri: url, width: 240, height: 152 }, (controller) => {
      controllers[idx + 1] = controller;
      controller.addListener('playback_update', (e) => {
        // keep the overlay in sync if playback ends
        if (e.data.isPaused && e.data.position === 0) {
          // noop: card stays open until user clicks another or the same cover
        }
      });
    });
  });
};

function toggle(i) {
  const card = document.getElementById('card-' + i);
  const wasPlaying = card.classList.contains('playing');

  // pause every other card
  document.querySelectorAll('.card.playing').forEach(c => {
    c.classList.remove('playing');
    const id = c.id.replace('card-', '');
    if (controllers[id]) controllers[id].pause();
  });

  if (!wasPlaying) {
    card.classList.add('playing');
    // user gesture -> allowed to start playback
    if (controllers[i]) controllers[i].play();
  }
}
function reveal(i) {
  document.getElementById('card-' + i).classList.add('revealed');
}

// --- Spacebar auto-advance ---
let spaceIndex = 0;                       // next card to play (1-based)
const totalCards = {{ rounds[page]|length }};
const currentPage = {{ page }};
const totalPages = {{ rounds|length }};

document.addEventListener('keydown', (e) => {
  if (e.code !== 'Space') return;
  e.preventDefault();                     // stop page scroll

  if (spaceIndex >= totalCards) {
    // all cards on this page have been played → go to next round
    if (currentPage < totalPages - 1) {
      window.location.href = '/' + (currentPage + 1);
    }
    return;
  }

  // play the next card
  toggle(spaceIndex + 1);
  spaceIndex++;
});
</script>
</body>
</html>
"""


@app.route("/")
@app.route("/<int:page>")
def slideshow(page=0):
    rounds = load_rounds()
    if not rounds:
        return "No tracks found in CSV.", 404
    page = max(0, min(page, len(rounds) - 1))
    # Convert embed links to track URIs for the Spotify IFrame API
    embed_urls = [t["embed"].replace(
        "https://open.spotify.com/embed/track/", "spotify:track:") for t in rounds[page]]
    return render_template_string(
        TEMPLATE, rounds=rounds, page=page, embed_urls=embed_urls)


if __name__ == "__main__":
    app.run(debug=True)