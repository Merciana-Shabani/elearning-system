/**
 * Elening LMS - Main JavaScript
 * Django-based Learning Management System
 */

document.addEventListener('DOMContentLoaded', function () {

    // -----------------------------------------------
    // Auto-dismiss alerts after 5 seconds
    // -----------------------------------------------
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });

    // -----------------------------------------------
    // Quiz timer countdown
    // -----------------------------------------------
    const timerEl = document.getElementById('quiz-timer');
    if (timerEl) {
        let seconds = parseInt(timerEl.dataset.seconds, 10);

        function updateTimer() {
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = seconds % 60;
            timerEl.textContent = [
                h.toString().padStart(2, '0'),
                m.toString().padStart(2, '0'),
                s.toString().padStart(2, '0')
            ].join(':');

            if (seconds <= 300) {  // 5 minutes warning
                timerEl.classList.add('warning', 'text-danger');
            }

            if (seconds <= 0) {
                clearInterval(timerInterval);
                timerEl.textContent = '00:00:00';
                // Auto-submit quiz
                const form = document.getElementById('quiz-form');
                if (form) {
                    const input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = 'finish';
                    input.value = '1';
                    form.appendChild(input);
                    form.submit();
                }
                return;
            }
            seconds--;
        }

        updateTimer();
        const timerInterval = setInterval(updateTimer, 1000);
    }

    // -----------------------------------------------
    // Message chat - scroll to bottom
    // -----------------------------------------------
    const chatContainer = document.getElementById('chat-messages');
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // -----------------------------------------------
    // Confirm dangerous actions
    // -----------------------------------------------
    document.querySelectorAll('[data-confirm]').forEach(function (el) {
        el.addEventListener('click', function (e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    // -----------------------------------------------
    // File input label update
    // -----------------------------------------------
    document.querySelectorAll('.custom-file-input').forEach(function (input) {
        input.addEventListener('change', function () {
            const label = this.nextElementSibling;
            if (label) {
                label.textContent = this.files[0] ? this.files[0].name : 'Choose file';
            }
        });
    });

    // -----------------------------------------------
    // Quiz: Flag question button
    // -----------------------------------------------
    document.querySelectorAll('.flag-question').forEach(function (btn) {
        btn.addEventListener('click', function () {
            this.classList.toggle('btn-warning');
            this.classList.toggle('btn-outline-secondary');
            const icon = this.querySelector('i');
            if (icon) {
                icon.classList.toggle('bi-flag-fill');
                icon.classList.toggle('bi-flag');
            }
        });
    });

});
