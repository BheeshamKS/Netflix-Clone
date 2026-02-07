// Wait for the window to scroll
window.addEventListener("scroll", function() {
    const navbar = document.querySelector(".navbar");
    
    // If user scrolls down more than 50px, add the black background class
    if (window.scrollY > 50) {
        navbar.classList.add("nav-black");
    } else {
        navbar.classList.remove("nav-black");
    }
});

const navbar = document.querySelector(".navbar");

window.addEventListener("scroll", () => {
    if (window.scrollY > 100) {
        // If we scroll down 100px, add the black background
        navbar.classList.add("nav-black");
    } else {
        // If we are at the top, make it transparent again
        navbar.classList.remove("nav-black");
    }
});

/* --- PLAY VIDEO FUNCTION --- */
function playTrailer(mediaType, tmdbId) {
    // 1. Fetch the trailer key from our Flask backend
    fetch(`/get_trailer/${mediaType}/${tmdbId}`)
        .then(response => response.json())
        .then(data => {
            if (data.key) {
                // 2. If found, show the modal and set the iframe source
                const modal = document.getElementById('video-modal');
                const player = document.getElementById('youtube-player');
                
                // Embed URL with autoplay enabled
                player.src = `https://www.youtube.com/embed/${data.key}?autoplay=1&rel=0&showinfo=0`;
                
                // Show modal (using Flex to center it)
                modal.style.display = 'flex';
            } else {
                alert("Sorry, no trailer available for this title.");
            }
        })
        .catch(error => console.error('Error:', error));
}

/* --- CLOSE VIDEO FUNCTION --- */
function closeVideo() {
    const modal = document.getElementById('video-modal');
    const player = document.getElementById('youtube-player');
    
    // Hide modal
    modal.style.display = 'none';
    
    // Stop video by clearing the source (important!)
    player.src = ""; 
}

// Close modal if user presses ESC key
document.addEventListener('keydown', function(event) {
    if (event.key === "Escape") {
        closeVideo();
    }
});