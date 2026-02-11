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
    if (document.activeElement) {
        document.activeElement.blur();
    }

    const titleElement = document.getElementById('player-title');
    if (titleElement) titleElement.innerText = title || "Now Playing";

    const modal = document.getElementById('video-modal');
    modal.style.display = 'flex';
    void modal.offsetWidth; 
    modal.classList.add('show');

    // Fetch Trailer
    fetch(`/get_trailer/${mediaType}/${tmdbId}`)
        .then(response => response.json())
        .then(data => {
            if (!modal.classList.contains('show')) {
                console.log("Modal closed, cancelling video start.");
                return; 
            }

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
    if (event.key === "Escape") {
        closeVideo();
    }
    
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
        container.classList.remove('paused');  
    } else {
        btn.className = 'fas fa-play';
        container.classList.add('paused');     
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
            player.destroy();  
            player = null;
        }
        
        if (!document.getElementById('youtube-player')) {
            const newPlayerDiv = document.createElement('div');
            newPlayerDiv.id = 'youtube-player';
            
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
    
    modal.style.display = 'flex'; 
    
    setTimeout(() => {modal.classList.add('show');}, 10);

    // 1. Fetch Details from Backend
    fetch(`/get_info/${mediaType}/${tmdbId}`)
        .then(res => res.json())
        .then(data => {
            if (data.error) return;

            // 2. Populate Data
            document.getElementById('info-backdrop').src = `https://image.tmdb.org/t/p/original${data.backdrop_path}`;
            
            const logoImg = document.getElementById('modal-logo');
            const titleText = document.getElementById('modal-title');

            let logoPath = null;
            if (data.images && data.images.logos && data.images.logos.length > 0) {
                logoPath = data.images.logos[0].file_path;
            }

            if (logoPath) {
                logoImg.src = `https://image.tmdb.org/t/p/w500${logoPath}`;
                logoImg.style.display = 'block';
                titleText.style.display = 'none';
            } else {
                logoImg.style.display = 'none';
                titleText.innerText = data.title || data.name; 
                titleText.style.display = 'block';
            }

            document.getElementById('info-overview').innerText = data.overview;
            document.getElementById('info-year').innerText = (data.release_date || data.first_air_date || "").substring(0,4);
            
            // Runtime (Handle minutes -> Xh Ym)
            const runtime = data.runtime || (data.episode_run_time ? data.episode_run_time[0] : 0);
            const hours = Math.floor(runtime / 60);
            const minutes = runtime % 60;
            document.getElementById('info-runtime').innerText = `${hours}h ${minutes}m`;

            // Genres
            const genres = data.genres ? data.genres.map(g => g.name).join(', ') : "N/A";
            document.getElementById('info-genres').innerText = genres;

            // Cast (Top 3)
            if (data.credits && data.credits.cast) {
                const cast = data.credits.cast.slice(0, 3).map(c => c.name).join(', ');
                document.getElementById('info-cast').innerText = cast;
            }

            // 3. Configure the "Play" button
            const playBtn = document.getElementById('info-play-btn');
            const title = (data.title || data.name || "").replace(/'/g, ""); // Remove apostrophes
            playBtn.setAttribute('onclick', `closeMoreInfo(); playTrailer('${mediaType}', ${tmdbId}, '${title}')`);

            // 4. Configure the "My List" button
            const listBtn = document.getElementById('info-list-btn');
            
            // This updates the onclick to include the specific ID and Type
            listBtn.setAttribute('onclick', `toggleMyList(event, this, '${mediaType}', ${tmdbId})`);
            
            // Reset button visual state
            listBtn.innerHTML = '<i class="fas fa-plus"></i> My List';
        })
        .catch(err => console.error(err));
}

/* --- 1. CLOSE FUNCTION --- */
function closeMoreInfo() {
    const modal = document.getElementById('info-modal');
    
    modal.classList.remove('show');
    
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
    
    // Stop video if playing
    const videoContainer = document.getElementById('trailer-container');
    if (videoContainer) videoContainer.innerHTML = ''; 
}


window.addEventListener('click', function(event) {
    const modal = document.getElementById('info-modal');
    
    if (event.target === modal) {
        closeMoreInfo();
    }
});

/* --- 2. CLOSE ON CLICK OUTSIDE (Must be outside functions) --- */
window.onclick = function(event) {
    
    // Get the modals
    const infoModal = document.getElementById('info-modal');
    const videoModal = document.getElementById('video-modal'); 

    
    if (event.target === infoModal) {
        closeMoreInfo();
    }

    if (videoModal && event.target === videoModal) {
        closeVideo(); 
    }
}


/* --- TOGGLE MY LIST (Final Polish) --- */
function toggleMyList(event, btn, mediaType, tmdbId, title) {
    if (event) {
        event.stopPropagation();
        event.preventDefault();
    }

    const icon = btn.querySelector('i');
    
    // --- 1. VISUAL TOGGLE ---
    if (window.location.pathname !== '/my-list') {
        
        if (icon.classList.contains('fa-plus')) {
            // Add to list
            icon.classList.remove('fa-plus');
            icon.classList.add('fa-check');
        } else {
            // Remove from list
            icon.classList.remove('fa-check');
            icon.classList.remove('fa-times'); 
            icon.classList.add('fa-plus');
        }
    }

    // --- 2. BACKEND CALL ---
    fetch(`/add_to_list/${mediaType}/${tmdbId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => {
        if (response.status === 401) window.location.href = "/login";
        return response.json();
    })
    .then(data => {
        if (window.location.pathname === '/my-list' && data.status === 'removed') {
            const card = document.getElementById(`card-${tmdbId}`);
            if (card) {
                card.style.display = 'none';

                checkEmptyState();

                showUndoToast(title || "Movie", mediaType, tmdbId, card);
            }
        }
    })
    .catch(error => console.error('Error:', error));
}

/* Helper: Toggle Empty State Message */
function checkEmptyState() {
    const container = document.getElementById('my-list-container');
    const emptyState = document.getElementById('empty-state');
    
    const visibleCards = Array.from(container.children).filter(card => card.style.display !== 'none');

    if (visibleCards.length === 0) {
        container.style.display = 'none';
        emptyState.style.display = 'block';
    } else {
        container.style.display = 'flex';
        emptyState.style.display = 'none';
    }
}

/* Helper: Show Undo Toast */
function showUndoToast(title, mediaType, tmdbId, cardElement) {
    const existing = document.querySelector('.toast-notification');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.innerHTML = `
        <span class="toast-text">Removed ${title}</span>
        <button class="toast-undo">Undo</button>
    `;

    document.body.appendChild(toast);

    // Animate In
    setTimeout(() => toast.classList.add('show'), 10);

    let isUndone = false;

    // Undo Click Handler
    toast.querySelector('.toast-undo').onclick = () => {
        isUndone = true;
        
        fetch(`/add_to_list/${mediaType}/${tmdbId}`, { method: 'POST' })
            .then(() => {
                // Show card again
                cardElement.style.display = 'block';
                
                // Targeted the 2nd button (Remove btn) instead of the 1st (Play btn)
                const icon = cardElement.querySelector('.card-buttons .mini-btn:nth-child(2) i');
                if (icon) {
                    icon.className = 'fas fa-times';
                }

                checkEmptyState();
                removeToast();
            });
    };

    setTimeout(() => {
        if (!isUndone) removeToast();
    }, 5000);

    function removeToast() {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }
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
            btn.style.borderColor = "white";  
        } else {
            icon.classList.remove('fa-check');
            icon.classList.add('fa-plus');
            btn.style.borderColor = "";  
        }
    } 
    else if (type === 'like') {
        // Toggle between Outline and Solid/Colored
        if (icon.classList.contains('far') || !icon.style.color) {
            icon.classList.remove('far');
            icon.classList.add('fas'); // Solid filled
            icon.style.color = "#46d369";  
        } else {
            icon.classList.remove('fas');
            icon.classList.add('far'); // Back to outline
            icon.style.color = ""; // Reset
        }
    }
}


