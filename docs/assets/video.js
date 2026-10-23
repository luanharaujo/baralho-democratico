// Carrega o player do YouTube (youtube-nocookie) só quando a pessoa toca para assistir.
document.addEventListener('click', function (ev) {
  var a = ev.target.closest && ev.target.closest('.video-caixa .video-play');
  if (!a) return;
  var caixa = a.closest('.video-caixa');
  var src = caixa.getAttribute('data-embed');
  if (!src) return;
  ev.preventDefault();
  var f = document.createElement('iframe');
  f.src = src;
  f.title = caixa.getAttribute('data-titulo') || 'Vídeo';
  f.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
  f.allowFullscreen = true;
  f.referrerPolicy = 'strict-origin-when-cross-origin';
  caixa.innerHTML = '';
  caixa.appendChild(f);
  caixa.classList.add('tocando');
});
