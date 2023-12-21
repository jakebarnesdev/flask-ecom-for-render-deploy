window.addEventListener("scroll", function () {
  var navbar = document.querySelector(".navbar");
  var prenavbar = document.querySelector(".prenavbar");

  if (window.scrollY > prenavbar.offsetHeight) {
    navbar.classList.add("fixed");
  } else {
    navbar.classList.remove("fixed");
  }
});
