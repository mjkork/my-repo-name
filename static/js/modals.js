/* ============================================================
 * modals.js — reusable modal wiring
 *
 * Usage:
 *   1. Give your backdrop <div> the class "modal-backdrop" and a unique id.
 *   2. Put a .modal-close button (X) inside the .modal-header.
 *   3. Put .modal-cancel on any Cancel/Close buttons inside the modal.
 *   4. Call initModal('your-modal-id') — it returns { open, close }.
 *
 * Example:
 *   const myModal = initModal('my-modal');
 *   document.getElementById('open-btn').addEventListener('click', myModal.open);
 * ============================================================ */

function initModal(backdropId) {
    const backdrop = document.getElementById(backdropId);
    if (!backdrop) return null;

    const close = () => { backdrop.hidden = true; };
    const open  = () => { backdrop.hidden = false; };

    // (b) Click outside the modal card closes it
    backdrop.addEventListener('click', (e) => {
        if (e.target === backdrop) close();
    });

    // (a) X button
    backdrop.querySelector('.modal-close')?.addEventListener('click', close);

    // (d) Any Cancel / Close button inside
    backdrop.querySelectorAll('.modal-cancel').forEach(btn =>
        btn.addEventListener('click', close)
    );

    return { open, close };
}

// (c) Esc key closes every open modal
document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    document.querySelectorAll('.modal-backdrop:not([hidden])').forEach(m => {
        m.hidden = true;
    });
});
