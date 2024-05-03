document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search');

    searchInput.addEventListener('input', function(event) {
        const searchTerm = event.target.value.toLowerCase();
        const sections = document.querySelectorAll('section');

        sections.forEach(section => {
            const sectionTitle = section.querySelector('h2').textContent.toLowerCase();
            const sectionContent = section.querySelector('p').textContent.toLowerCase();

            if (sectionTitle.includes(searchTerm) || sectionContent.includes(searchTerm)) {
                section.style.display = 'block';
            } else {
                section.style.display = 'none';
            }
        });
    });
});
