/* B DE BLOG — reusable comments component for story pages.
   Mount point: <section class="comments-section" data-historia="H_x.html">
   containing a .comment-form (with .comment-apodo / .comment-texto /
   .comment-counter), a .comments-list, and a .comment-feedback element.

   Security: every piece of user-provided text (apodo, comentario) is
   inserted with textContent, never innerHTML — the browser can't parse it
   as markup no matter what a visitor types. */
(function () {
    'use strict';

    var MAX_COMENTARIO = 1000;
    var MAX_APODO = 50;

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.comments-section[data-historia]').forEach(initComments);
    });

    function initComments(section) {
        const historia = section.dataset.historia;
        const form = section.querySelector('.comment-form');
        const apodoInput = section.querySelector('.comment-apodo-field');
        const textoInput = section.querySelector('.comment-texto-field');
        const counter = section.querySelector('.comment-counter');
        const list = section.querySelector('.comments-list');
        const emptyMsg = section.querySelector('.comments-empty');
        const feedback = section.querySelector('.comment-feedback');
        if (!historia || !form || !apodoInput || !textoInput || !list) return;

        function setFeedback(msg, isError) {
            if (!feedback) return;
            feedback.textContent = msg || '';
            feedback.classList.toggle('is-error', !!isError);
        }

        function updateCounter() {
            const len = textoInput.value.length;
            if (counter) {
                counter.textContent = `${len} / ${MAX_COMENTARIO}`;
                counter.classList.toggle('over-limit', len > MAX_COMENTARIO);
            }
        }
        textoInput.addEventListener('input', updateCounter);
        updateCounter();

        function formatFecha(value) {
            const d = new Date(value);
            if (isNaN(d.getTime())) return '';
            const dd = String(d.getDate()).padStart(2, '0');
            const mm = String(d.getMonth() + 1).padStart(2, '0');
            return `${dd}/${mm}/${d.getFullYear()}`;
        }

        function buildCommentItem(c) {
            const item = document.createElement('article');
            item.className = 'comment-item';

            const head = document.createElement('div');
            head.className = 'comment-head';

            const nick = document.createElement('span');
            nick.className = 'comment-author';
            nick.textContent = c.apodo; // never innerHTML — plain text only

            const date = document.createElement('span');
            date.className = 'comment-fecha';
            date.textContent = formatFecha(c.fecha);

            head.appendChild(nick);
            head.appendChild(date);

            const body = document.createElement('p');
            body.className = 'comment-body';
            body.textContent = c.comentario; // never innerHTML — plain text only

            item.appendChild(head);
            item.appendChild(body);
            return item;
        }

        function toggleEmpty(hasComments) {
            if (emptyMsg) emptyMsg.hidden = hasComments;
        }

        function loadComments() {
            fetch(`/api/comentarios/${encodeURIComponent(historia)}`)
                .then((res) => res.json())
                .then((data) => {
                    if (!data.success) throw new Error(data.error || 'Error');
                    list.innerHTML = '';
                    data.comentarios.forEach((c) => list.appendChild(buildCommentItem(c)));
                    toggleEmpty(data.comentarios.length > 0);
                })
                .catch(() => setFeedback('No se pudieron cargar los comentarios.', true));
        }

        loadComments();

        let busy = false;
        form.addEventListener('submit', (event) => {
            event.preventDefault();
            if (busy) return;

            const apodo = apodoInput.value.trim();
            const comentario = textoInput.value.trim();

            if (!apodo) return setFeedback('Escribe un apodo.', true);
            if (apodo.length > MAX_APODO) return setFeedback(`El apodo no puede superar ${MAX_APODO} caracteres.`, true);
            if (!comentario) return setFeedback('Escribe un comentario.', true);
            if (comentario.length > MAX_COMENTARIO) return setFeedback(`El comentario no puede superar ${MAX_COMENTARIO} caracteres.`, true);

            busy = true;
            setFeedback('Publicando...', false);

            fetch('/api/comentarios', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ historia, apodo, comentario }),
            })
                .then((res) => res.json().then((data) => ({ ok: res.ok, data })))
                .then(({ ok, data }) => {
                    busy = false;
                    if (!ok || !data.success) {
                        setFeedback((data && data.error) || 'Ocurrió un error. Intenta más tarde.', true);
                        return;
                    }
                    list.insertBefore(buildCommentItem(data.comentario), list.firstChild);
                    toggleEmpty(true);
                    form.reset();
                    updateCounter();
                    setFeedback('¡Comentario publicado!', false);
                })
                .catch(() => {
                    busy = false;
                    setFeedback('Ocurrió un error. Intenta más tarde.', true);
                });
        });
    }
})();
