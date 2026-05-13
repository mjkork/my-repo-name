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

// (c) Esc key closes the top-most open modal only
document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    const open = [...document.querySelectorAll('.modal-backdrop:not([hidden])')];
    if (!open.length) return;
    // Close the one with the highest z-index (last in DOM order wins ties)
    open.sort((a, b) => {
        const za = parseInt(getComputedStyle(a).zIndex) || 0;
        const zb = parseInt(getComputedStyle(b).zIndex) || 0;
        return zb - za;
    });
    open[0].hidden = true;
});

/* ============================================================
 * confirmModal — reusable confirmation dialog
 *
 * Usage:
 *   confirmModal.show({
 *     title:     'Confirm changes',
 *     body:      'Are you sure you want to update this bow?',
 *     primary:   'Update bow information',
 *     onPrimary: () => { document.getElementById('my-form').submit(); },
 *     secondary: 'Cancel',  // optional, defaults to 'Cancel'
 *   });
 *
 * Stacks on top of other open modals (z-index 300 via .modal-backdrop-top).
 * Cancelling leaves any modal underneath visible and intact.
 * ============================================================ */
const confirmModal = (function () {
    const backdrop   = document.getElementById('confirm-modal');
    if (!backdrop) return null;

    const titleEl    = document.getElementById('cm-title-text');
    const bodyEl     = document.getElementById('cm-body');
    const primaryBtn = document.getElementById('cm-primary');
    const secondaryBtn = document.getElementById('cm-secondary');

    const modal = initModal('confirm-modal');
    let _primaryHandler = null;

    function show({ title, body, primary, onPrimary, secondary = 'Cancel' }) {
        titleEl.textContent      = title;
        bodyEl.textContent       = body;
        primaryBtn.textContent   = primary;
        secondaryBtn.textContent = secondary;

        if (_primaryHandler) primaryBtn.removeEventListener('click', _primaryHandler);
        _primaryHandler = () => { modal.close(); onPrimary(); };
        primaryBtn.addEventListener('click', _primaryHandler);

        modal.open();
    }

    return { show, close: modal.close };
}());
