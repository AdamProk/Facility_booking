$("#submitfacilities").click(function(){
    $.get("http://localhost:9000/add", function(data, status){
      $("#response").html(data["response"])
    });
  });


$("#submitregistration").submit(function (e) {
    e.preventDefault();
  
    var form = $(this).closest('form');
    // Serialize the form data
    var formData = $(this).closest('form').serialize();
  
    // Make the POST request
    $.ajax({
      type: "POST",
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

$("#submitlogin").submit(function (e) {
  e.preventDefault();

  var form = $(this).closest('form');
  // Serialize the form data
  var formData = $(this).closest('form').serialize();

  // If all fields are filled, submit the form
  $.ajax({
    type: "POST",
    url: "http://localhost:9000/login", 
    data: formData,  // Pass serialized form data as the request body
    success: function (response) {
      $("#login_response").html(response["response"]);
      // Handle success 
      window.location.href = "/";
    },
    error: function (xhr, status, error) {
      // Handle error
      if (xhr.status === 401) {
        var errorResponse = $.parseJSON(xhr.responseText);
        // Unauthorized - Incorrect credentials
        $("#login_response").html(errorResponse.response);
        form[0].reset();
    }
  }});
  // Make the POST request
});