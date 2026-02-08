/* --- 1. NAVBAR SCROLL EFFECT --- */
const navbar = document.querySelector(".navbar");

window.addEventListener("scroll", () => {
    if (window.scrollY > 50) {
        navbar.classList.add("nav-black");
    } else {
        navbar.classList.remove("nav-black");
    }
});

/* --- 2. YOUTUBE CUSTOM PLAYER VARIABLES --- */
let player;
let updateInterval;

/* --- 3. YOUTUBE API SETUP --- */
function onYouTubeIframeAPIReady() {
    console.log("YouTube API Ready");
}

/* --- 4. PLAY VIDEO FUNCTION --- */
function playTrailer(mediaType, tmdbId, title) {
    // FIX: Remove focus from the button we just clicked. 
    // This stops the Space bar from "clicking" it again and restarting the video.
    if (document.activeElement) {
        document.activeElement.blur();
    }

    // Update Title
    const titleElement = document.getElementById('player-title');
    if (titleElement) titleElement.innerText = title || "Now Playing";

    // Show Modal
    const modal = document.getElementById('video-modal');
    modal.style.display = 'flex';
    void modal.offsetWidth; 
    modal.classList.add('show');

    // Fetch Trailer
    fetch(`/get_trailer/${mediaType}/${tmdbId}`)
        .then(response => response.json())
        .then(data => {
            if (data.key) {
                if (player) {
                    player.destroy();
                }

                player = new YT.Player('youtube-player', {
                    height: '100%',
                    width: '100%',
                    videoId: data.key,
                    playerVars: {
                        'autoplay': 1,
                        'controls': 0,
                        'showinfo': 0,
                        'modestbranding': 1,
                        'rel': 0,
                        'enablejsapi': 1,
                        'origin': window.location.origin
                    },
                    events: {
                        'onReady': onPlayerReady,
                        'onStateChange': onPlayerStateChange
                    }
                });
            } else {
                alert("Sorry, no trailer available.");
                closeVideo();
            }
        })
        .catch(error => console.error('Error:', error));
}

/* --- 5. KEYBOARD CONTROLS (Space & Esc) --- */
document.addEventListener('keydown', function(event) {
    // ESCAPE: Close Video
    if (event.key === "Escape") {
        closeVideo();
    }
    
    // SPACE BAR: Toggle Play/Pause
    // We check if the modal is actually open first
    const modal = document.getElementById('video-modal');
    if ((event.code === "Space" || event.key === " ") && modal.style.display === 'flex') {
        event.preventDefault(); // Stop the page from scrolling down
        togglePlay();
    }
});

/* --- 6. PLAYER EVENT HANDLERS --- */
function onPlayerReady(event) {
    event.target.playVideo();
    startProgressLoop();
}

function onPlayerStateChange(event) {
    const btn = document.querySelector('#play-pause-btn i');
    const container = document.getElementById('video-container');
    
    if (event.data == YT.PlayerState.PLAYING) {
        btn.className = 'fas fa-pause';
        container.classList.remove('paused'); // Hide dark overlay
    } else {
        btn.className = 'fas fa-play';
        container.classList.add('paused');    // Show dark overlay
    }
}

/* --- 7. CUSTOM CONTROL FUNCTIONS --- */
function togglePlay() {
    if (player && typeof player.getPlayerState === 'function') {
        const state = player.getPlayerState();
        if (state == YT.PlayerState.PLAYING) {
            player.pauseVideo();
        } else {
            player.playVideo();
        }
    }
}

function toggleMute() {
    if (!player) return;
    const btn = document.querySelector('#mute-btn i');
    if (player.isMuted()) {
        player.unMute();
        btn.className = 'fas fa-volume-up';
    } else {
        player.mute();
        btn.className = 'fas fa-volume-mute';
    }
}

function toggleFullscreen() {
    const videoContainer = document.querySelector('.video-container');
    if (!document.fullscreenElement) {
        if (videoContainer.requestFullscreen) videoContainer.requestFullscreen();
        else if (videoContainer.webkitRequestFullscreen) videoContainer.webkitRequestFullscreen();
    } else {
        if (document.exitFullscreen) document.exitFullscreen();
        else if (document.webkitExitFullscreen) document.webkitExitFullscreen();
    }
}

function closeVideo() {
    const modal = document.getElementById('video-modal');
    modal.classList.remove('show');
    
    // Stop the progress bar loop
    if (updateInterval) clearInterval(updateInterval);

    setTimeout(() => {
        modal.style.display = 'none';
        
        if (player) {
            player.stopVideo();
            player.destroy(); // This removes the iframe from the DOM
            player = null;
        }
        
        // FIX: Check if the player placeholder is gone, and restore it 
        // WITHOUT deleting the Close Button or Title!
        if (!document.getElementById('youtube-player')) {
            const newPlayerDiv = document.createElement('div');
            newPlayerDiv.id = 'youtube-player';
            
            // Insert the new div exactly where it belongs: BEFORE the controls
            const container = document.getElementById('video-container');
            const controls = document.getElementById('custom-controls');
            container.insertBefore(newPlayerDiv, controls);
        }
        
    }, 300);
}

/* --- 8. PROGRESS BAR --- */
function startProgressLoop() {
    if (updateInterval) clearInterval(updateInterval);
    updateInterval = setInterval(() => {
        if (player && player.getCurrentTime) {
            const duration = player.getDuration();
            const current = player.getCurrentTime();
            if (duration > 0) {
                const percent = (current / duration) * 100;
                document.getElementById('progress-bar').style.width = percent + '%';
            }
        }
    }, 500);
}

function seekVideo(event) {
    if (!player) return;
    const container = document.querySelector('.progress-container');
    const newTime = (event.offsetX / container.offsetWidth) * player.getDuration();
    player.seekTo(newTime, true);
}

/* --- MORE INFO MODAL LOGIC --- */
function openMoreInfo(mediaType, tmdbId) {
    const modal = document.getElementById('info-modal');
    modal.style.display = 'block';
    
    // Slight delay for animation
    setTimeout(() => { modal.classList.add('show'); }, 10);

    // 1. Fetch Details from Backend
    fetch(`/get_info/${mediaType}/${tmdbId}`)
        .then(res => res.json())
        .then(data => {
            if (data.error) return;

            // 2. Populate Data
            document.getElementById('info-backdrop').src = `https://image.tmdb.org/t/p/original${data.backdrop_path}`;
            document.getElementById('info-title').innerText = data.title || data.name;
            document.getElementById('info-overview').innerText = data.overview;
            document.getElementById('info-year').innerText = (data.release_date || data.first_air_date || "").substring(0,4);
            
            // Runtime (Handle minutes -> Xh Ym)
            const runtime = data.runtime || (data.episode_run_time ? data.episode_run_time[0] : 0);
            const hours = Math.floor(runtime / 60);
            const minutes = runtime % 60;
            document.getElementById('info-runtime').innerText = `${hours}h ${minutes}m`;

            // Genres
            const genres = data.genres.map(g => g.name).join(', ');
            document.getElementById('info-genres').innerText = genres;

            // Cast (Top 3)
            if (data.credits && data.credits.cast) {
                const cast = data.credits.cast.slice(0, 3).map(c => c.name).join(', ');
                document.getElementById('info-cast').innerText = cast;
            }

            // 3. Configure the "Play" button
            const playBtn = document.getElementById('info-play-btn');
            const title = (data.title || data.name).replace(/'/g, ""); // Remove apostrophes
            playBtn.setAttribute('onclick', `closeMoreInfo(); playTrailer('${mediaType}', ${tmdbId}, '${title}')`);

            // --- 4. NEW: Configure the "My List" button ---
            const listBtn = document.getElementById('info-list-btn');
            
            // This updates the onclick to include the specific ID and Type
            listBtn.setAttribute('onclick', `toggleMyList(event, this, '${mediaType}', ${tmdbId})`);
            
            // Optional: Reset button visual state to "Add" every time you open a new modal
            // (Unless you add a check to see if it's already saved)
            const icon = listBtn.querySelector('i');
            icon.className = 'fas fa-plus';
            listBtn.innerHTML = '<i class="fas fa-plus"></i> My List';
        })
        .catch(err => console.error(err));
}

function closeMoreInfo() {
    const modal = document.getElementById('info-modal');
    modal.classList.remove('show');
    setTimeout(() => { modal.style.display = 'none'; }, 300);
}

// Close on clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('info-modal');
    if (event.target == modal) {
        closeMoreInfo();
    }
}


/* --- TOGGLE MY LIST (Final Fix: Handles Cross & Removes Card) --- */
function toggleMyList(event, btn, mediaType, tmdbId) {
    // 1. Stop click from opening the popup
    if (event) {
        event.stopPropagation();
        event.preventDefault();
    }

    const icon = btn.querySelector('i');
    const isModalButton = btn.classList.contains('btn-list');

    // --- VISUAL TOGGLE ---
    if (icon.classList.contains('fa-plus')) {
        // CASE: Add to List
        icon.classList.remove('fa-plus');
        icon.classList.add('fa-check');
        
        if (isModalButton) btn.innerHTML = '<i class="fas fa-check"></i> Added';
    } else {
        // CASE: Remove from List
        // FIX: We must remove BOTH 'fa-check' AND 'fa-times' to be safe
        icon.classList.remove('fa-check');
        icon.classList.remove('fa-times'); 
        
        icon.classList.add('fa-plus');
        
        if (isModalButton) btn.innerHTML = '<i class="fas fa-plus"></i> My List';
    }

    // --- BACKEND SAVE & REMOVE CARD ---
    if (!tmdbId) return;

    fetch(`/add_to_list/${mediaType}/${tmdbId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => {
        if (response.status === 401) window.location.href = "/login";
        return response.json();
    })
    .then(data => {
        console.log("Status:", data.status);

        // EXTRA FEATURE: If we are on the "My List" page, remove the card visually!
        if (window.location.pathname === '/my-list' && data.status === 'removed') {
            const card = btn.closest('.movie-card');
            if (card) {
                // Fade out animation
                card.style.transition = "opacity 0.3s, transform 0.3s";
                card.style.opacity = "0";
                card.style.transform = "scale(0.9)";
                
                // Remove from HTML after animation
                setTimeout(() => card.remove(), 300);
            }
        }
    })
    .catch(error => console.error('Error:', error));
}

/* --- CARD ICON TOGGLES (Visual Only) --- */
function toggleCardIcon(event, btn, type) {
    // STOP the click from bubbling up to the card (prevents opening More Info)
    event.stopPropagation();

    const icon = btn.querySelector('i');

    if (type === 'plus') {
        // Toggle between Plus (+) and Check (✔)
        if (icon.classList.contains('fa-plus')) {
            icon.classList.remove('fa-plus');
            icon.classList.add('fa-check');
            btn.style.borderColor = "white"; // Optional: Highlight border
        } else {
            icon.classList.remove('fa-check');
            icon.classList.add('fa-plus');
            btn.style.borderColor = ""; // Reset
        }
    } 
    else if (type === 'like') {
        // Toggle between Outline and Solid/Colored
        if (icon.classList.contains('far') || !icon.style.color) {
            icon.classList.remove('far');
            icon.classList.add('fas'); // Solid filled
            icon.style.color = "#46d369"; // Netflix Green match
        } else {
            icon.classList.remove('fas');
            icon.classList.add('far'); // Back to outline
            icon.style.color = ""; // Reset
        }
    }
}