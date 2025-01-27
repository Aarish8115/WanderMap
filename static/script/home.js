const scroll = new LocomotiveScroll({
  el: document.querySelector(".main"),
  smooth: true,
});
document.getElementById("suggestions").addEventListener("wheel", function (e) {
  e.stopPropagation();
});
document.getElementById("textarea").addEventListener("wheel", function (e) {
  e.stopPropagation();
});

var map = L.map("map", { scrollWheelZoom: false }).setView([0, 0], 2);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  noWrap: true,
}).addTo(map);

function addMarker(city) {
  var color = city.visited ? "#7fad1a" : "#1794cf";
  var marker = L.marker([city.latitude, city.longitude], {
    icon: L.divIcon({
      className: `marker-${color}`,
      html: `<svg style="fill:${color};height:14px" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512"><path d="M384 192c0 87.4-117 243-168.3 307.2c-12.3 15.3-35.1 15.3-47.4 0C117 435 0 279.4 0 192C0 86 86 0 192 0S384 86 384 192z"/></svg>`,
    }),
  }).addTo(map);

  marker.bindPopup(
    `<div class="popup"><a href="/${city.id}">${city.name}</a></div>`
  );
}

fetch("/api/cities")
  .then((response) => response.json())
  .then((data) => {
    data.forEach((city) => addMarker(city));
  });

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
    fetch(
      `https://api.opencagedata.com/geocode/v1/json?q=${query}&key=f4ae94146a744187b2f78b6637aaec82`
    )
      .then((response) => response.json())
      .then((data) => {
        var suggestions = document.getElementById("suggestions");
        suggestions.innerHTML = "";
        suggestions.style.display = "block";
        data.results.forEach((result) => {
          var li = document.createElement("li");
          li.textContent = result.formatted;
          li.style.padding = "8px";
          li.style.cursor = "pointer";
          li.addEventListener("click", function () {
            document.getElementById("city-search").value = result.formatted;
            suggestions.innerHTML = "";
            suggestions.style.display = "none";
          });
          suggestions.appendChild(li);
        });
      });
  } else {
    document.getElementById("suggestions").innerHTML = "";
    document.getElementById("suggestions").style.display = "none";
  }
});

document.addEventListener("click", function (e) {
  if (
    !document.getElementById("city-search").contains(e.target) &&
    !document.getElementById("suggestions").contains(e.target)
  ) {
    document.getElementById("suggestions").innerHTML = "";
    document.getElementById("suggestions").style.display = "none";
  }
});

function visitCity(cityId) {
  fetch(`/visit/${cityId}`, { method: "POST" })
    .then((response) => response.text())
    .then(() => {
      location.reload();
    });
}
