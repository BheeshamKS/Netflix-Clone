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

/* --- PLAY VIDEO FUNCTION (Optimized) --- */
function playTrailer(mediaType, tmdbId, title) {
    // 1. OPEN MODAL IMMEDIATELY (Instant Feedback)
    const modal = document.getElementById('video-modal');
    const spinner = document.getElementById('loading-spinner');
    const titleElement = document.getElementById('player-title');
    
    // Set Title
    if (titleElement) titleElement.innerText = title || "Now Playing";
    
    // Show Modal & Spinner
    modal.style.display = 'flex';
    void modal.offsetWidth; // Trigger reflow
    modal.classList.add('show');
    spinner.style.display = 'block'; // Show spinner

    // 2. FETCH TRAILER
    fetch(`/get_trailer/${mediaType}/${tmdbId}`)
        .then(response => response.json())
        .then(data => {
            if (data.key) {
                loadYoutubeVideo(data.key);
            } else {
                alert("Sorry, no trailer available.");
                closeVideo(); // Close if failed
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert("Something went wrong loading the video.");
            closeVideo();
        })
        .finally(() => {
            // Hide spinner when done (success or fail)
            spinner.style.display = 'none';
        });
}

// Helper: Handles Player Creation vs Reuse
function loadYoutubeVideo(videoId) {
    // If player exists and is ready, just load the new video (FAST)
    if (player && typeof player.loadVideoById === 'function') {
        player.loadVideoById(videoId);
    } else {
        // Otherwise, create a new player (Initial Load)
        player = new YT.Player('youtube-player', {
            height: '100%',
            width: '100%',
            videoId: videoId,
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
    }
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

/* --- CLOSE VIDEO FUNCTION --- */
function closeVideo() {
    const modal = document.getElementById('video-modal');
    modal.classList.remove('show');
    
    // Stop progress bar updates
    if (updateInterval) clearInterval(updateInterval);

    setTimeout(() => {
        modal.style.display = 'none';
        
        // PAUSE video instead of destroying it (Faster next time)
        if (player && typeof player.pauseVideo === 'function') {
            player.pauseVideo();
        }
        
        // We DO NOT destroy the player anymore.
        // We leave it hidden in the background so it's ready for the next click.
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