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