$("#submit_facilities").click(function(){
    $.get("http://localhost:9000/add", function(data, status){
      $("#response").html(data["response"])
    });
  });


$("#submit_registration").click(function (e) {
    e.preventDefault();
  
    var form = $(this).closest('form');
    var formData = $(this).closest('form').serialize();
  
    $.post({
      url: "http://localhost:9000/register",
      data: formData,
      success: function (response) {
        $("#register_response").html(response["response"]);
        form[0].reset();
      },
      error: function (xhr, status, error) {
        console.error(xhr.responseText);
      }
    });
});


$("#submit_edit").click(function (e) {
    e.preventDefault();
  
    var form = $(this).closest('form');
    var formData = $(this).closest('form').serialize();
  
    $.post({
      url: "http://localhost:9000/edit_site",
      data: formData,
      success: function (response) {
        $("#edit_site_response").html(response["response"]);
        form[0].reset();
      },
      error: function (xhr, status, error) {
        console.error(xhr.responseText);
      }
    });
});


$("#submit_logo").click(function (e) {
    e.preventDefault();
  
    var form = $(this).closest('form');
    var formData = new FormData(form[0]);
  
    $.ajax({
        url: "http://localhost:9000/upload_logo",
        type: "POST",
        data: formData,
        processData: false,
        contentType: false,
        success: function (response) {
            $("#edit_site_response").html(response["response"]);
            form[0].reset();
        },
        error: function (xhr, status, error) {
            console.error(xhr.responseText);
        }
    });
});
