document.addEventListener('DOMContentLoaded', function () {
    const geoField = document.getElementById('geo-location-field');
    const cityField = document.getElementById('city-field');
    const geoBtn = document.getElementById('geo-btn');
    const cityBtn = document.getElementById('city-btn');

    function toggleFields() {
        const selected = document.querySelector('input[name="location_type"]:checked').value;
        if (selected === 'geo') {
            geoField.classList.remove('hidden-by-opacity');
            cityField.classList.add('hidden-by-opacity');
            geoBtn.classList.add('active');
            cityBtn.classList.remove('active');
        } else {
            geoField.classList.add('hidden-by-opacity');
            cityField.classList.remove('hidden-by-opacity');
            cityBtn.classList.add('active');
            geoBtn.classList.remove('active');
        }
    }

    geoBtn.addEventListener('click', toggleFields);
    cityBtn.addEventListener('click', toggleFields);

    toggleFields(); // Initial call
});
