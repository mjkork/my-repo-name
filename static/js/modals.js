/* ============================================================
 * modals.js — reusable modal wiring
 *
 * Usage:
 *   1. Give your backdrop <div> the class "modal-backdrop" and a unique id.
 *   2. Put a .modal-close button (X) inside the .modal-header.
 *   3. Put .modal-cancel on any Cancel/Close buttons inside the modal.
 *   4. Call initModal('your-modal-id') — it returns { open, close, reset }.
 *
 * Form-reset pattern (automatic):
 *   If the modal contains a <form>, every dismiss (Cancel, X, backdrop
 *   click, Esc) resets the form to the state it had when open() was
 *   called. This covers JS-populated forms too because the snapshot is
 *   captured inside open(), after the caller has filled the fields.
 *   Any "disabled-until-changed" buttons re-evaluate automatically
 *   because a synthetic 'change' event is dispatched on the form after
 *   restore — no extra code needed per modal.
 *
 *   Confirmation modals that stack on top of a form modal are NOT
 *   affected — they contain no form, so their close() is a no-op for
 *   reset purposes, leaving the form modal underneath untouched.
 *
 * Example:
 *   const myModal = initModal('my-modal');
 *   document.getElementById('open-btn').addEventListener('click', myModal.open);
 * ============================================================ */

function initModal(backdropId) {
    const backdrop = document.getElementById(backdropId);
    if (!backdrop) return null;

    // ---- Form-reset state ----
    const form = backdrop.querySelector('form');
    let _snapshot = null;

    function _capture() {
        if (!form) return;
        _snapshot = {};
        form.querySelectorAll('input, select, textarea').forEach(el => {
            if (el.name) _snapshot[el.name] = el.value;
        });
    }

    function _restore() {
        if (!form || !_snapshot) return;
        form.querySelectorAll('input, select, textarea').forEach(el => {
            if (el.name && _snapshot[el.name] !== undefined) el.value = _snapshot[el.name];
        });
        // Let change-detection listeners (e.g. "Accept changes") re-evaluate
        form.dispatchEvent(new Event('change', { bubbles: true }));
    }

    const close = () => { _restore(); backdrop.hidden = true; };
    const open  = () => { _capture(); backdrop.hidden = false; };
    const reset = () => { _restore(); };  // restore fields without hiding

    // Stored on the element so the Esc handler can call close() (not just hide)
    backdrop._initModalClose = close;

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

    return { open, close, reset };
}

// (c) Esc closes only the top-most open modal (calls close() so form resets fire)
document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    const open = [...document.querySelectorAll('.modal-backdrop:not([hidden])')];
    if (!open.length) return;
    open.sort((a, b) => {
        const za = parseInt(getComputedStyle(a).zIndex) || 0;
        const zb = parseInt(getComputedStyle(b).zIndex) || 0;
        return zb - za;
    });
    (open[0]._initModalClose || (() => { open[0].hidden = true; }))();
});

/* ============================================================
 * confirmModal — reusable confirmation dialog
 *
 * Usage:
 *   confirmModal.show({
 *     title:        'Confirm changes',
 *     body:         'Are you sure you want to update this bow?',
 *     primary:      'Update bow information',
 *     onPrimary:    () => { document.getElementById('my-form').submit(); },
 *     secondary:    'Cancel',           // optional, defaults to 'Cancel'
 *     primaryClass: 'btn btn-danger',   // optional, defaults to 'btn btn-primary'
 *     onCancel:     () => myModal.reset(),  // optional, called when secondary is clicked
 *   });
 *
 * Stacks on top of other open modals (z-index 300 via .modal-backdrop-top).
 * Cancelling leaves any modal underneath visible and intact — the confirm
 * modal contains no form, so its close() does not reset the parent form.
 * ============================================================ */
const confirmModal = (function () {
    const backdrop   = document.getElementById('confirm-modal');
    if (!backdrop) return null;

    const titleEl      = document.getElementById('cm-title-text');
    const bodyEl       = document.getElementById('cm-body');
    const primaryBtn   = document.getElementById('cm-primary');
    const secondaryBtn = document.getElementById('cm-secondary');

    const modal = initModal('confirm-modal');
    let _primaryHandler = null;
    let _cancelHandler  = null;

    function show({ title, body, primary, onPrimary, secondary = 'Cancel', primaryClass = 'btn btn-primary', onCancel = null }) {
        titleEl.textContent      = title;
        bodyEl.textContent       = body;
        primaryBtn.textContent   = primary;
        primaryBtn.className     = primaryClass;
        secondaryBtn.textContent = secondary;

        if (_primaryHandler) primaryBtn.removeEventListener('click', _primaryHandler);
        _primaryHandler = () => { modal.close(); onPrimary(); };
        primaryBtn.addEventListener('click', _primaryHandler);

        if (_cancelHandler) secondaryBtn.removeEventListener('click', _cancelHandler);
        if (onCancel) {
            _cancelHandler = () => onCancel();
            secondaryBtn.addEventListener('click', _cancelHandler);
        } else {
            _cancelHandler = null;
        }

        modal.open();
    }

    return { show, close: modal.close };
}());

/* ============================================================
 * Quick-delete row action — generic handler for any list page.
 *
 * To enable quick-delete on a list row, add a <button> with:
 *   class="list-row-action list-row-action--danger"
 *   data-delete-url="/path/to/<pk>/delete/"
 *   data-delete-name="Display name shown in the confirmation"
 *   data-delete-label="noun for title/button (e.g. 'bow', 'session')"
 *
 * stopPropagation prevents the row's own click handler from firing.
 * ============================================================ */
document.addEventListener('click', (e) => {
    const btn = e.target.closest('.list-row-action--danger');
    if (!btn) return;
    e.stopPropagation();

    const { deleteUrl, deleteName, deleteLabel } = btn.dataset;
    const label = deleteLabel || 'item';

    confirmModal.show({
        title:        `Delete ${label}`,
        body:         `Are you sure you want to delete "${deleteName}"? This action cannot be undone.`,
        primary:      `Delete ${label}`,
        primaryClass: 'btn btn-danger',
        onPrimary:    () => {
            const form     = document.createElement('form');
            form.method    = 'post';
            form.action    = deleteUrl;
            const csrf     = document.createElement('input');
            csrf.type      = 'hidden';
            csrf.name      = 'csrfmiddlewaretoken';
            csrf.value     = document.querySelector('[name="csrfmiddlewaretoken"]')?.value ?? '';
            form.appendChild(csrf);
            document.body.appendChild(form);
            form.submit();
        },
    });
});
