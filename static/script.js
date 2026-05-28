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

    if (loadingOverlay) {
        uploadForms.forEach((form) => {
            form.addEventListener('submit', () => {
                loadingOverlay.classList.add('active');
            });
        });
    }
});
