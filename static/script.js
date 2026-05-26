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
});
