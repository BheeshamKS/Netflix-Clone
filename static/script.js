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