$("#submit_facility").click(function (e) {
    e.preventDefault();

    var form = $(this).closest('form');
    var formData = new FormData(form[0]);

    $.ajax({
        type: "POST",
        url: "http://localhost:9000/add_facility",
        data: formData,
        contentType: false,
        processData: false,
        success: function (response) {
            $("#fac_response").html(response["response"]);
            form[0].reset();
        },
        error: function (xhr, status, error) {
            if (xhr.status === 404) {
                var errorResponse = $.parseJSON(xhr.responseText);
                $("#fac_response").html(errorResponse.response);
            }
            if (xhr.status === 500) {
                var errorResponse = $.parseJSON(xhr.responseText);
                $("#fac_response").html(errorResponse.response);
                form[0].reset();
            }
        }
    });
});



$("#edit_facility").submit(function (e) {
    e.preventDefault();
  
    var form = $(this).closest('form');
    var formData = $(this).closest('form').serialize();
  
    $.ajax({
        type: "POST",
        url: "http://localhost:9000/edit_facility",
        data: formData,
        success: function (response) {
            $("#fac_response").html(response["response"]);
        },
        error: function (xhr, status, error) {
        if (xhr.status === 404) {
            var errorResponse = $.parseJSON(xhr.responseText);
            $("#fac_response").html(errorResponse.response);
        }
        if (xhr.status === 500) {
            var errorResponse = $.parseJSON(xhr.responseText);
            $("#fac_response").html(errorResponse.response);
            form[0].reset();
        }
        }
    });
});


$("#submit_registration").submit(function (e) {
    e.preventDefault();
  
    var form = $(this).closest('form');
    var formData = $(this).closest('form').serialize();
  
    $.ajax({
      type: "POST",
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


$("#submit_login").submit(function (e) {
  e.preventDefault();

  var form = $(this).closest('form');
  var formData = $(this).closest('form').serialize();

  $.ajax({
    type: "POST",
    url: "http://localhost:9000/login", 
    data: formData,
    success: function (response) {
      $("#login_response").html(response["response"]);
      window.location.href = "/";
    },
    error: function (xhr, status, error) {
      if (xhr.status === 401) {
        var errorResponse = $.parseJSON(xhr.responseText);
        $("#login_response").html(errorResponse.response);
        form[0].reset();
    }
  }});
});


$("#submit_password_reset").submit(function (e) {
    e.preventDefault();
  
    var form = $(this).closest('form');
    var formData = $(this).closest('form').serialize();
  
    $.ajax({
        type: "POST",
        url: "http://localhost:9000/reset_password",
        data: formData,
        success: function (response) {
            $("#password_reset_response").html(response["response"]);
        },
        error: function (xhr, status, error) {
        if (xhr.status === 500) {
            var errorResponse = $.parseJSON(xhr.responseText);
            $("#password_reset_response").html(errorResponse.response);
            form[0].reset();
        }
        }
    });
});


$("#submit_edit_account_info").click(function (e) {
    e.preventDefault();
  
    var form = $(this).closest('form');
    var formData = $(this).closest('form').serialize();
  
    $.ajax({
        type: "PUT",
        url: "http://localhost:9000/edit_account_info",
        data: formData,
        success: function (response) {
            $("#edit_account_info_response").html(response["response"]);
        },
        error: function (xhr, status, error) {
        if (xhr.status === 404) {
            var errorResponse = $.parseJSON(xhr.responseText);
            $("#edit_account_info_response").html(errorResponse.response);
        }
        if (xhr.status === 500) {
            var errorResponse = $.parseJSON(xhr.responseText);
            $("#edit_account_info_response").html(errorResponse.response);
            form[0].reset();
        }
        }
    });
});


$("#submit_edit").click(function (e) {
    e.preventDefault();
  
    var form = $(this).closest('form');
    var formData = $(this).closest('form').serialize();
  
    $.ajax({
        type: "POST",
        url: "http://localhost:9000/edit_site",
        data: formData,
        success: function (response) {
            $("#edit_site_response").html(response["response"]);
        },
        error: function (xhr, status, error) {
        if (xhr.status === 404) {
            var errorResponse = $.parseJSON(xhr.responseText);
            $("#edit_site_response").html(errorResponse.response);
        }
        if (xhr.status === 500) {
            var errorResponse = $.parseJSON(xhr.responseText);
            $("#edit_site_response").html(errorResponse.response);
            form[0].reset();
        }
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
        if (xhr.status === 500) {
            var errorResponse = $.parseJSON(xhr.responseText);
            $("#edit_site_response").html(errorResponse.response);
            form[0].reset();
        }
        }
    });
});
