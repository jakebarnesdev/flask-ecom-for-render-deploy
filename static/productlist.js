var minPrice = document.getElementById("price-min");
var priceRange = document.getElementById("price-range");
var content = document.getElementById("content");
// Set value
minPrice.value = priceRange.max;

function updateSlider() {
  minPrice.value = priceRange.value;
}

priceRange.addEventListener("input", updateSlider);
minPrice.addEventListener("input", updateSlider);

window.onload = () => {
  // Get the button, and when the user clicks on it, execute myFunction
  document.getElementById("hamburger-icon").onclick = function () {
    unhide();
  };

  /* unhide toggles between adding and removing the show class, which is used to hide and show the dropdown content */
  function unhide() {
    document.getElementById("dropdown-content").classList.toggle("show");
  }
};

function selectCategory(category) {
  document.getElementById("selected-category").value = category;
}

function resetForm() {
  document.getElementById("selected-category").value = "";
}
