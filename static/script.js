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

/* --- 4. PLAY VIDEO FUNCTION (FIXED: Accepts Title) --- */
function playTrailer(mediaType, tmdbId, title) {
    // 1. UPDATE THE TITLE
    const titleElement = document.getElementById('player-title');
    if (titleElement) {
        titleElement.innerText = title || "Now Playing";
    }

    // 2. Fetch the trailer
    fetch(`/get_trailer/${mediaType}/${tmdbId}`)
        .then(response => response.json())
        .then(data => {
            if (data.key) {
                const modal = document.getElementById('video-modal');
                
                // Show modal
                modal.style.display = 'flex';
                void modal.offsetWidth; // Trigger reflow
                modal.classList.add('show');

                // Destroy old player to prevent duplicates
                if (player) {
                    player.destroy();
                }

                // Create new player
                player = new YT.Player('youtube-player', {
                    height: '100%',
                    width: '100%',
                    videoId: data.key,
                    playerVars: {
                        'autoplay': 1,
                        'controls': 0,       // Hide default controls
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
                alert("Sorry, no trailer available for this title.");
            }
        })
        .catch(error => console.error('Error fetching trailer:', error));
}

/* --- FULLSCREEN LOGIC --- */
function toggleFullscreen() {
    const videoContainer = document.querySelector('.video-container');
    
    if (!document.fullscreenElement) {
        if (videoContainer.requestFullscreen) videoContainer.requestFullscreen();
        else if (videoContainer.webkitRequestFullscreen) videoContainer.webkitRequestFullscreen();
        else if (videoContainer.msRequestFullscreen) videoContainer.msRequestFullscreen();
    } else {
        if (document.exitFullscreen) document.exitFullscreen();
        else if (document.webkitExitFullscreen) document.webkitExitFullscreen();
        else if (document.msExitFullscreen) document.msExitFullscreen();
    }
}

/* --- 5. PLAYER EVENT HANDLERS --- */
function onPlayerReady(event) {
    event.target.playVideo();
    startProgressLoop();
}

// Handles the Play/Pause Icon and Dark Overlay
function onPlayerStateChange(event) {
    const btn = document.querySelector('#play-pause-btn i');
    const container = document.getElementById('video-container');
    
    if (event.data == YT.PlayerState.PLAYING) {
        btn.className = 'fas fa-pause';
        container.classList.remove('paused'); // Remove dark overlay
    } else {
        btn.className = 'fas fa-play';
        container.classList.add('paused');    // Add dark overlay
    }
}

/* --- 6. CUSTOM CONTROL FUNCTIONS --- */
function togglePlay() {
    if (player) {
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

function closeVideo() {
    const modal = document.getElementById('video-modal');
    modal.classList.remove('show');
    clearInterval(updateInterval);

    setTimeout(() => {
        modal.style.display = 'none';
        if (player) {
            player.stopVideo();
            player.destroy();
            player = null;
        }
        // Reset controls for next time
        const controlsHTML = document.getElementById('custom-controls').outerHTML;
        document.querySelector('.video-container').innerHTML = 
            '<div id="youtube-player"></div>' + controlsHTML;
    }, 300);
}

document.addEventListener('keydown', function(event) {
    if (event.key === "Escape") closeVideo();
});

/* --- 7. PROGRESS BAR LOGIC --- */
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