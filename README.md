# GenerateAnimatedBackgrounds
Quickly create animated backgrounds for anything from videos.

Supports:
- multiple quality levels
- choosing a start time from your video to start the animation at (in case the animation only appears in a specific point in the video)
- a perfect loop feature that automatically detects the right duration for your animated background so that it loops perfectly
- a boomerang mode which reverses the animation (thus creating a cheaper perfect loop. Not as good as a true perfect loop, but it is ideal for when you can't find a perfect loop in your source video)

## About

I made this to quickly grab cool looking animated backgrounds for animated tracks off of [YouTube](https://www.youtube.com/watch?v=rentoNxY6RA)

But since this project uses yt-dlp to grab videos, you could use this tool to make animated backgrounds off of videos you found from any of these sources and more:
- YouTube
- Vimeo
- Facebook
- Instagram
- Twitter
- TikTok
- Dailymotion
- Twitch
- Bilibili
- SoundCloud
- Youku
- Niconico
- Odysee
- Rumble
- Pornhub, Xvideos, Redtube (they're supported by yt-dlp...)
- Newgrounds
- PeerTube
- LiveLeak (okay you nasty 😭)
- Bandcamp
- Tumblr
- BBC iPlayer
- NBC
- CBC
- ABC
- ARTE TV
- FranceTV
- Mediaset
- Canal+
- MTV
- Crunchyroll
- Discovery
- TLC
- HGTV
- Food Network

And because this solution uses ffmpeg and Python, it is cross-platform and should work on Windows, Linux, and MacOS. Sorry FreeBSD users I don't know if you have ffmpeg or not

## Example

See `bloc-high-100.webp` as an example of what this script can make with default `high` quality. It is 32MB so you will likely have to download it to preview.

## Dependencies (Required installs before you can use)

You must have:
- ffmpeg installed (tested with ffmpeg version 7.1 on Win11. Other versions likely work too. The main thing is that you have access to the `libwebp_anim` module in ffmpeg, as its needed to convert to `.webp`
- yt-dlp installed (tested with version `2025.02.19`)
- Python (tested with 3.11.2, but as old as 3.8.x should work)

## Setup/Install

Assuming you have the aforementioned dependencies, you can

1. `git clone https://github.com/alanmun/GenerateAnimatedBackgrounds.git`

to grab the project into a local folder.

Then,

2. `pipenv install` to grab all Python packages needed and install in an isolated environment.

> If you don't have pipenv, do `pip install pipenv` first.

## Usage

`pipenv run python GenerateVSCodeBackground.py --help` will dump all the commandline args and options, as well as their defaults and descriptions on how each option works.

> If you are already in the virtual environment via `pipenv shell`, you just need to run `python GenerateVSCodeBackground.py`

## Performance

This project was intended to be used with VS Code to have backgrounds in your IDE. As such, it is limited to animated formats that work within the confines of css only. Because of this, my options were basically
- gif (old as fuck)
- apng (seems to be almost as good as webp)
- webp (more modern)

Even with webp, file sizes are pretty massive, I've taken care to cut them down as much as I can. For example right now I have one background that takes up 300MB on my GPU and contributes to ~9% GPU utilization. This is fine, but if you need to drive all performance out of your GPU (like you are playing a hard to run game or doing AI workloads on the side), you may find these animated backgrounds to be troublesome to run (especially at immaculate quality setting). If I am running AI workloads or gaming, I currently either just deal with it or disable backgrounds or close out all VS Code windows to free up resources 🤷🏻‍♂️
