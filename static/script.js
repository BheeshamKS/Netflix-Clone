
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
// This function is automatically called by the YouTube API script when it loads
function onYouTubeIframeAPIReady() {
    console.log("YouTube API Ready");
}

/* --- 4. PLAY VIDEO FUNCTION --- */
function playTrailer(mediaType, tmdbId) {
    // Fetch the trailer key from our Flask backend
    fetch(`/get_trailer/${mediaType}/${tmdbId}`)
        .then(response => response.json())
        .then(data => {
            if (data.key) {
                const modal = document.getElementById('video-modal');
                
                // Show modal with Flexbox
                modal.style.display = 'flex';
                
                // Force browser reflow (needed for transition)
                void modal.offsetWidth; 
                
                // Add class to trigger CSS fade-in
                modal.classList.add('show');

                // If a player already exists, destroy it so we can make a new one
                if (player) {
                    player.destroy();
                }

                // Create the new YouTube Player with Custom Settings
                player = new YT.Player('youtube-player', {
                    height: '100%',
                    width: '100%',
                    videoId: data.key,
                    playerVars: {
                        'autoplay': 1,       // Auto-play
                        'controls': 0,       // HIDE default YouTube controls
                        'showinfo': 0,       // Hide title
                        'modestbranding': 1, // Minimal logo
                        'rel': 0,            // No related videos
                        'enablejsapi': 1     // Enable JS control
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
        // Enter Fullscreen
        if (videoContainer.requestFullscreen) {
            videoContainer.requestFullscreen();
        } else if (videoContainer.mozRequestFullScreen) { /* Firefox */
            videoContainer.mozRequestFullScreen();
        } else if (videoContainer.webkitRequestFullscreen) { /* Chrome, Safari & Opera */
            videoContainer.webkitRequestFullscreen();
        } else if (videoContainer.msRequestFullscreen) { /* IE/Edge */
            videoContainer.msRequestFullscreen();
        }
    } else {
        // Exit Fullscreen
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.mozCancelFullScreen) { 
            document.mozCancelFullScreen();
        } else if (document.webkitExitFullscreen) { 
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) { 
            document.msExitFullscreen();
        }
    }
}

/* --- 5. PLAYER EVENT HANDLERS --- */

// Called when video is ready to play
function onPlayerReady(event) {
    event.target.playVideo();
    startProgressLoop(); // Start updating the red progress bar
}

// Called when video pauses or plays (updates our custom icon)
function onPlayerStateChange(event) {
    const btn = document.querySelector('#play-pause-btn i');
    
    if (event.data == YT.PlayerState.PLAYING) {
        btn.className = 'fas fa-pause'; // Show Pause icon
    } else {
        btn.className = 'fas fa-play';  // Show Play icon
    }
}

/* --- 6. CUSTOM CONTROL FUNCTIONS --- */

// Toggle Play/Pause
function togglePlay() {
    if (player && player.getPlayerState() == YT.PlayerState.PLAYING) {
        player.pauseVideo();
    } else if (player) {
        player.playVideo();
    }
}

// Toggle Mute/Unmute
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

// Close the Video Modal
function closeVideo() {
    const modal = document.getElementById('video-modal');
    modal.classList.remove('show'); // Trigger fade-out
    
    // Stop the progress bar loop
    clearInterval(updateInterval);

    // Wait 300ms for animation, then hide and destroy player
    setTimeout(() => {
        modal.style.display = 'none';
        if (player) {
            player.stopVideo();
            player.destroy();
            player = null;
        }
        
        // Reset the inner HTML to prepare for next time
        // We preserve the 'custom-controls' div so it's not lost
        const controlsHTML = document.getElementById('custom-controls').outerHTML;
        document.querySelector('.video-container').innerHTML = 
            '<div id="youtube-player"></div>' + controlsHTML;
            
    }, 300);
}

// Close on Escape Key
document.addEventListener('keydown', function(event) {
    if (event.key === "Escape") {
        closeVideo();
    }
});

/* --- 7. PROGRESS BAR LOGIC --- */

// Update the red bar width every 500ms
function startProgressLoop() {
    // Clear any existing loop first
    if (updateInterval) clearInterval(updateInterval);
    
    updateInterval = setInterval(() => {
        if (player && player.getCurrentTime) {
            const duration = player.getDuration();
            const current = player.getCurrentTime();
            
            if (duration > 0) {
                const percent = (current / duration) * 100;
                const progressBar = document.getElementById('progress-bar');
                if (progressBar) {
                    progressBar.style.width = percent + '%';
                }
            }
        }
    }, 500);
}

// Click on the bar to seek (skip) to that time
function seekVideo(event) {
    if (!player) return;
    
    const container = document.querySelector('.progress-container');
    const newTime = (event.offsetX / container.offsetWidth) * player.getDuration();
    
    player.seekTo(newTime, true);
}