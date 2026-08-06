# Video and audio overviews

Both slots on the home page are placeholders. To fill them:

## Audio

Drop an MP3 here as `overview.mp3`, then in `scripts/pages.py` replace the
audio placeholder block in `home_page` with:

```html
<audio controls preload="none" style="width:100%">
  <source src="media/overview.mp3" type="audio/mpeg">
  Your browser does not support audio playback.
</audio>
```

Rebuild with `python3 scripts/build.py`.

## Video

Two options.

**Self-hosted** — drop `overview.mp4` here and use a `<video controls>` element
the same way. Keep it under ~50 MB; GitHub warns above 50 MB and rejects at 100 MB.

**YouTube** — an iframe embed reaches a third-party host, which the rest of the
site deliberately avoids. If that trade-off is acceptable, use a click-to-load
facade so nothing loads until the reader asks for it: show a poster image, and
swap in the iframe on click.

## Why the placeholders look the way they do

They render as labelled empty states rather than broken players. A missing
`<audio>` source shows a dead control; a labelled placeholder tells the reader
the thing is coming.
