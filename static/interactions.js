/* B DE BLOG — shared front-end micro-interactions.
   Purely presentational: nav active-state, banner shrink-on-scroll,
   scroll-reveal, and a DRY footer. Never touches ratings/data logic. */
(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', () => {
        highlightActiveNav();
        setupBannerScroll();
        setupScrollReveal();
        injectFooter();
    });

    function highlightActiveNav() {
        const here = window.location.pathname.replace(/\/+$/, '') || '/';
        document.querySelectorAll('.banner-menu .menu-button').forEach((btn) => {
            const onclick = btn.getAttribute('onclick') || '';
            const match = onclick.match(/location\.href=['"]([^'"]+)['"]/);
            if (!match) return;
            const target = match[1].replace(/\/+$/, '') || '/';
            if (target === here) btn.classList.add('active');
        });
    }

    function setupBannerScroll() {
        const banner = document.querySelector('.banner');
        if (!banner) return;
        const toggle = () => banner.classList.toggle('scrolled', window.scrollY > 40);
        toggle();
        window.addEventListener('scroll', toggle, { passive: true });
    }

    function setupScrollReveal() {
        const targets = document.querySelectorAll(
            '.hero, .page-header, .story-title, .story-text, .image-container, ' +
            '.rating-container, .story-author, .story-card, .site-footer'
        );
        if (!targets.length) return;

        if (!('IntersectionObserver' in window)) {
            targets.forEach((el) => el.classList.add('reveal', 'in-view'));
            return;
        }

        let cardIndex = 0;
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('in-view');
                        observer.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0, rootMargin: '0px 0px -30px 0px' }
        );

        targets.forEach((el) => {
            el.classList.add('reveal');
            if (el.classList.contains('story-card')) {
                el.style.transitionDelay = `${Math.min(cardIndex * 60, 300)}ms`;
                cardIndex += 1;
            }
            observer.observe(el);
        });
    }

    function injectFooter() {
        if (document.querySelector('.site-footer')) return;
        const footer = document.createElement('footer');
        footer.className = 'site-footer';
        footer.innerHTML =
            '<img src="/static/guyfox.webp" alt="" aria-hidden="true">' +
            '<p><strong>B DE BLOG</strong> &mdash; historias y reseñas sin filtro</p>' +
            '<p>Ing. Wilson Felipe Martínez Barrantes</p>';
        document.body.appendChild(footer);
    }
})();
