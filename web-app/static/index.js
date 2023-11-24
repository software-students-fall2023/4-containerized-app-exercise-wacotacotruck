// Function to handle description button 
function toggleDescription() {
    const modalBackground = document.getElementById("modal-background");
    if (modalBackground.style.display === "none" || !modalBackground.style.display) {
        modalBackground.style.display = "flex";
    } else {
        modalBackground.style.display = "none";
    }
  }