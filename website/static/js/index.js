$("#submitfacilities").click(function(){
    $.get("http://localhost:9000/add", function(data, status){
      $("#response").html(data["response"])
    });
  });

  $("#submitregistration").click(function (e) {
    e.preventDefault();
  
    var form = $(this).closest('form');
    // Serialize the form data
    var formData = $(this).closest('form').serialize();
  
    // Make the POST request
    $.post({
      url: "http://localhost:9000/register",
      data: formData,  // Pass serialized form data as the request body
      success: function (response) {
        $("#register_response").html(response["response"]);
        // Handle success
        form[0].reset();
      },
      error: function (xhr, status, error) {
        // Handle error
        console.error(xhr.responseText);
      }
    });
  });