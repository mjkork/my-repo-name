// Indoor/outdoor conditional display for the session form.
// Hides outdoor-only fields ([data-outdoor-only]) when location = indoor.
// Works in both Add and Modify modals — each form is initialized independently.
// Does NOT clear values on hide; data is preserved if the user switches back.

function initOutdoorFields(form) {
    const locationSelect = form.querySelector('[name$="-location"]');
    if (!locationSelect) return;

    const outdoorFields = form.querySelectorAll('[data-outdoor-only]');
    if (!outdoorFields.length) return;

    function updateVisibility() {
        const isIndoor = locationSelect.value === 'indoor';
        outdoorFields.forEach(el => el.classList.toggle('field-hidden', isIndoor));
    }

    locationSelect.addEventListener('change', updateVisibility);
    updateVisibility();
}

document.querySelectorAll('form').forEach(initOutdoorFields);
