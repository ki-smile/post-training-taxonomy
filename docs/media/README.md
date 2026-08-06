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

## Audio — still a placeholder

Drop an MP3 here as `overview.mp3`, then replace the audio placeholder block in
`home_page` (`scripts/pages.py`) with:

    <audio controls preload="none" style="width:100%">
      <source src="media/overview.mp3" type="audio/mpeg">
      Your browser does not support audio playback.
    </audio>

`preload="none"` matters: without it the browser starts fetching the file for
every visitor.
