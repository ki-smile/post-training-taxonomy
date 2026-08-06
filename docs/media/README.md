# Video and audio overviews

## Video — done

The home page embeds the overview as a **click-to-load facade**. The poster
(`video-poster.jpg`) is served from this folder, and nothing is requested from
YouTube until a reader presses play, at which point `js/video.js` swaps in an
iframe pointed at the no-cookie host.

That keeps the page's promise of making no third-party requests on load. A
plain `<iframe>` would contact Google for every visitor, including those who
never watch. A test asserts no iframe appears in the static HTML.

To change the video, edit `VIDEO_ID`, `VIDEO_TITLE` and `VIDEO_CHANNEL` in
`scripts/layout.py`, replace the poster, and rebuild:

    curl -o docs/media/video-poster.jpg https://i.ytimg.com/vi/<ID>/maxresdefault.jpg
    python3 scripts/build.py

## Audio — done

`The_6D_Taxonomy_of_AI_Adaptation.mp3` (19 MB, 128 kbps stereo, ~21 min) plays
inline on the home page with a download link beside it.

The player carries `preload="none"`. Without it every visitor downloads 19 MB
whether or not they press play, which on a mobile connection is real money. A
test asserts the attribute is present.

To change the audio, replace the file and update `AUDIO_FILE`, `AUDIO_TITLE`
and `AUDIO_LENGTH` in `scripts/layout.py`, then rebuild.

## A note on repository size

The audio is 19 MB and the poster 115 KB, so `docs/media/` dominates the
repository. That is under GitHub's 50 MB per-file warning and well under the
100 MB hard limit, so committing it directly is fine. If more large media
accumulates, move it to a release asset or external host and link out.
