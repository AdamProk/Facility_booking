function performSearch() {
    var query = document.getElementById("search").value.toLowerCase();
    var facilityList = document.getElementById("facility_list");
    var facilities = facilityList.getElementsByTagName("li");

    for (var i = 0; i < facilities.length; i++) {
        var facilityName = facilities[i].textContent.toLowerCase();
        if (facilityName.includes(query)) {
            facilities[i].style.display = "block";
        } else {
            facilities[i].style.display = "none";
        }
    }
}
