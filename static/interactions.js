/* B DE BLOG — shared front-end micro-interactions.
   Purely presentational: nav active-state, banner shrink-on-scroll,
   scroll-reveal, and a DRY footer. Never touches ratings/data logic. */
(function () {
    'use strict';

    document.addEventListener('DOMContentLoaded', () => {
        highlightActiveNav();
        setupBannerScroll();
        setupScrollReveal();
        initCategoryTabs();
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

    function initCategoryTabs() {
        const tabs = document.querySelectorAll('.category-tab');
        const grid = document.querySelector('.card-grid');
        if (!tabs.length || !grid) return;

        const cards = Array.from(grid.querySelectorAll('.story-card[data-story-category]'));

        // Hiding is always instant/synchronous — display:none and the fade
        // class land in the same pass, so a non-matching card never spends
        // even one frame occupying a grid track while invisible. That's the
        // difference between "no empty space, ever" and "no empty space
        // after a brief animated delay". Only the reveal of matching cards
        // is animated, and it's a pure opacity ramp applied *after* the
        // grid has already reflowed to its final, correct set of tracks —
        // so the fade never has incorrect geometry to hide.
        function applyCategory(category, animate) {
            cards.forEach((card) => {
                const matches = card.dataset.storyCategory === category;
                if (!matches) {
                    card.classList.add('is-category-hidden', 'is-category-removed');
                    return;
                }

                card.classList.remove('is-category-removed');
                // Cards that started hidden (display:none) may never have
                // crossed the scroll-reveal IntersectionObserver's
                // threshold, so .in-view might be missing — without it
                // .reveal alone would hold the card at opacity:0 forever.
                card.classList.add('in-view');

                if (animate) {
                    card.classList.add('is-category-hidden');
                    void card.offsetWidth; // flush so the browser registers the starting (hidden) state
                    requestAnimationFrame(() => card.classList.remove('is-category-hidden'));
                } else {
                    card.classList.remove('is-category-hidden');
                }
            });
        }

        tabs.forEach((tab) => {
            tab.addEventListener('click', () => {
                if (tab.classList.contains('is-active')) return;
                tabs.forEach((t) => {
                    const active = t === tab;
                    t.classList.toggle('is-active', active);
                    t.setAttribute('aria-selected', active ? 'true' : 'false');
                });
                applyCategory(tab.dataset.category, true);
            });
        });

        const initialTab = document.querySelector('.category-tab.is-active') || tabs[0];
        applyCategory(initialTab.dataset.category, false);
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
