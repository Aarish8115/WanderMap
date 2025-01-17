const scroll = new LocomotiveScroll({
  el: document.querySelector(".main"),
  smooth: true,
});
document.getElementById("suggestions").addEventListener("wheel", function (e) {
  e.stopPropagation(); // Prevent Locomotive Scroll from affecting the dropdown
});

// Initialize the map
var map = L.map("map").setView([0, 0], 2);

// Set the tile layer with noWrap to prevent infinite horizontal scrolling
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  noWrap: true, // Prevent the tiles from wrapping horizontally
  attribution:
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
}).addTo(map);

// Set the bounds to limit the map view to a specific area (world bounds)
var southWest = L.latLng(-85, -180),
  northEast = L.latLng(85, 180);
var bounds = L.latLngBounds(southWest, northEast);

map.setMaxBounds(bounds);
map.on("drag", function () {
  map.panInsideBounds(bounds, { animate: false });
});
document.getElementById("city-search").addEventListener("input", function () {
  var query = this.value.trim();
  if (query.length > 2) {
    // Fetch only when the query has more than 2 characters
    fetch(
      `https://api.opencagedata.com/geocode/v1/json?q=${query}&key=f4ae94146a744187b2f78b6637aaec82`
    )
      .then((response) => response.json())
      .then((data) => {
        var suggestions = document.getElementById("suggestions");
        suggestions.innerHTML = "";
        suggestions.style.display = "block"; // Show the suggestions list
        data.results.forEach((result) => {
          var li = document.createElement("li");
          li.textContent = result.formatted;
          li.style.padding = "8px";
          li.style.cursor = "pointer";
          li.addEventListener("click", function () {
            document.getElementById("city-search").value = result.formatted;
            suggestions.innerHTML = "";
            suggestions.style.display = "none"; // Hide the suggestions after selection
          });
          suggestions.appendChild(li);
        });
      });
  } else {
    document.getElementById("suggestions").innerHTML = "";
    document.getElementById("suggestions").style.display = "none"; // Hide suggestions when query is too short
  }
});

// Hide suggestions when clicking outside
document.addEventListener("click", function (e) {
  if (
    !document.getElementById("city-search").contains(e.target) &&
    !document.getElementById("suggestions").contains(e.target)
  ) {
    document.getElementById("suggestions").innerHTML = "";
    document.getElementById("suggestions").style.display = "none";
  }
});
