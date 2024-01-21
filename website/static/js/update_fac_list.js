$(document).ready(function() {   
    $("#search").on("input", function() {
        var query = $(this).val();
        console.log(query);

        $.ajax({
            url: "http://localhost:9000/search_facility",
            method: "GET",
            data: { query: query },
            success: function(data) {
                $("#container").html(data);
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
});