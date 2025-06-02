document.addEventListener("DOMContentLoaded", function() {
    const form = document.querySelector("form");
    form.addEventListener("submit", function(event) {
        const email = document.getElementById("email").value;
        const website = document.getElementById("website").value;
        
        // Email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            alert("Please enter a valid email address");
            event.preventDefault();
            return;
        }
        
        // Website validation
        if (website && !website.match(/^https?:\/\/.+/)) {
            alert("Please enter a valid URL starting with http:// or https://");
            event.preventDefault();
            return;
        }
    });
    console.log("Signup page loaded");
});