window.addEventListener('DOMContentLoaded', () => {
    const messages = document.querySelectorAll('.flash-message');

    messages.forEach((msg) => {
        requestAnimationFrame(() => {
            msg.classList.add('visible');
        });

        setTimeout(() => {
            msg.classList.add('fade-out');
        }, 4000);

        msg.addEventListener('transitionend', () => {
            if (msg.classList.contains('fade-out')) {
                msg.remove();
            }
        }, { once: true });
    });

    const loadingOverlay = document.getElementById('loading-overlay');
    const uploadForms = document.querySelectorAll('form.admin-form');
    const rerunButtons = document.querySelectorAll('.rerun-ai-btn');

    if (loadingOverlay) {
        uploadForms.forEach((form) => {
            form.addEventListener('submit', () => {
                loadingOverlay.classList.add('active');
            });
        });
    }

    rerunButtons.forEach((button) => {
        button.addEventListener('click', async () => {
            const projectId = button.dataset.projectId;
            if (!projectId) {
                alert('Het project kon niet worden gevonden.');
                return;
            }

            button.disabled = true;
            const originalHTML = button.innerHTML;
            button.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Controleren...';

            try {
                const response = await fetch(`/rerun_project_ai/${projectId}`, {
                    method: 'POST',
                    headers: {
                        'Accept': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                const data = await response.json();
                if (!response.ok) {
                    alert(data.error || 'Er is iets misgegaan bij het opnieuw analyseren van je project.');
                    return;
                }

                const card = button.closest('.project-card');
                if (card) {
                    const scoreElement = card.querySelector('.ai-score-value');
                    const feedbackElement = card.querySelector('.ai-feedback-text');
                    if (scoreElement) scoreElement.textContent = `${data.ai_score}/5`;
                    if (feedbackElement) feedbackElement.textContent = `"${data.ai_feedback}"`;
                }

                alert('AI-heranalyse is voltooid. De score is bijgewerkt.');
            } catch (error) {
                alert('Er ging iets mis bij de verbinding met de server. Probeer opnieuw.');
            } finally {
                button.disabled = false;
                button.innerHTML = originalHTML;
            }
        });
    });

    // Zoekfunctionaliteit
    const searchInput = document.getElementById('project-search');
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            const filter = searchInput.value.toLowerCase();
            const cards = document.querySelectorAll('.project-card');

            cards.forEach(card => {
                const title = card.querySelector('h4').textContent.toLowerCase();
                const meta = card.querySelector('.project-meta').textContent.toLowerCase();
                
                // Toon de kaart als de filter matcht met de titel of de meta-informatie (studentnaam)
                const isMatch = title.includes(filter) || meta.includes(filter);
                card.style.display = isMatch ? "" : "none";
            });
        });
    }
});