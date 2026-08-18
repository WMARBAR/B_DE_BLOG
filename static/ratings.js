/* B DE BLOG — reusable star-rating component.
   Two independent jobs, both driven entirely by data-attributes so no
   template needs its own copy of this logic:

   1. Interactive widget: <div class="rating-container" data-contenido="..."
      data-tipo="historia|resena"> on every story/review page. Handles
      hover preview, click-to-vote via fetch(), and re-renders in place —
      no page reload.

   2. Read-only mini-rating: <span class="story-card-rating"
      data-contenido="..."> on the index cards (historias.html/resenas.html).
      Fetched once, in a single batched request, on page load.
*/
(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.rating-container[data-contenido]').forEach(initInteractiveWidget);
        initCardMiniRatings();
    });

    function paintStars(stars, value) {
        stars.forEach((star, i) => {
            const fill = Math.min(Math.max(value - i, 0), 1) * 100;
            star.style.setProperty('--fill', `${fill}%`);
        });
    }

    function formatVotos(total) {
        if (!total) return 'Sé el primero en calificar.';
        return `${total} calificación${total === 1 ? '' : 'es'}`;
    }

    function initInteractiveWidget(container) {
        const contenido = container.dataset.contenido;
        const tipo = container.dataset.tipo;
        const stars = Array.from(container.querySelectorAll('.stars-average .star'));
        const msgEl = container.querySelector('#rating-msg, .rating-msg');
        const countEl = container.querySelector('.rating-count');
        if (!stars.length || !contenido || !tipo) return;

        let average = 0;
        let mine = 0;
        let busy = false;

        fetch(`/api/calificacion/${encodeURIComponent(contenido)}`)
            .then((res) => res.json())
            .then((data) => {
                if (!data.success) throw new Error(data.error || 'Error');
                average = data.promedio || 0;
                mine = data.mi_calificacion || 0;
                paintStars(stars, mine || average);
                if (countEl) countEl.textContent = formatVotos(data.total_votos);
            })
            .catch(() => {
                if (msgEl) msgEl.textContent = 'No se pudo cargar la calificación.';
            });

        stars.forEach((star, index) => {
            star.addEventListener('mouseenter', () => paintStars(stars, index + 1));
            star.addEventListener('mouseleave', () => paintStars(stars, mine || average));

            star.addEventListener('click', () => {
                if (busy) return;
                busy = true;
                const nueva = index + 1;

                fetch('/api/calificar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ contenido, tipo, calificacion: nueva }),
                })
                    .then((res) => res.json().then((data) => ({ ok: res.ok, data })))
                    .then(({ ok, data }) => {
                        busy = false;
                        if (!ok || !data.success) {
                            if (msgEl) msgEl.textContent = (data && data.error) || 'Ocurrió un error. Intenta más tarde.';
                            return;
                        }
                        mine = data.mi_calificacion;
                        average = data.promedio;
                        paintStars(stars, mine);
                        if (countEl) countEl.textContent = formatVotos(data.total_votos);
                        if (msgEl) msgEl.textContent = `¡Gracias! Has calificado con ${nueva} estrella${nueva === 1 ? '' : 's'}.`;
                    })
                    .catch(() => {
                        busy = false;
                        if (msgEl) msgEl.textContent = 'Ocurrió un error. Intenta más tarde.';
                    });
            });
        });
    }

    function initCardMiniRatings() {
        const nodes = Array.from(document.querySelectorAll('.story-card-rating[data-contenido]'));
        if (!nodes.length) return;

        fetch('/api/calificaciones')
            .then((res) => res.json())
            .then((data) => {
                if (!data.success) return;
                nodes.forEach((el) => {
                    const stats = data.calificaciones[el.dataset.contenido];
                    if (!stats || !stats.total_votos) return; // no votes yet — leave it blank
                    const filled = Math.round(stats.promedio);
                    const glyphs = '★★★★★☆☆☆☆☆'.slice(5 - filled, 10 - filled);
                    el.textContent = `${glyphs} ${stats.promedio.toFixed(1)} · ${stats.total_votos}`;
                });
            })
            .catch(() => { /* index pages stay silent on failure — read-only, non-critical */ });
    }
})();
