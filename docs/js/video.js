// Click-to-load video. The poster is local, so the page makes no request to
// YouTube until a reader presses play. Uses the no-cookie host.
document.querySelectorAll('.video-facade').forEach((facade) => {
  facade.addEventListener('click', () => {
    const id = facade.dataset.video;
    const frame = document.createElement('iframe');
    frame.src = `https://www.youtube-nocookie.com/embed/${id}?autoplay=1&rel=0`;
    frame.title = facade.dataset.title || 'Video overview';
    frame.loading = 'lazy';
    frame.allow = 'accelerometer; autoplay; encrypted-media; picture-in-picture';
    frame.referrerPolicy = 'strict-origin-when-cross-origin';
    frame.allowFullscreen = true;
    frame.className = 'video-frame';
    facade.replaceWith(frame);
  }, { once: true });
});
