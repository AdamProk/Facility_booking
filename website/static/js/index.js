$("#submit_facility").submit(function (e) {
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
        type: "PUT",
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
        if (xhr.status === 404) {
            var errorResponse = $.parseJSON(xhr.responseText);
            $("#password_reset_response").html(errorResponse.response);
            form[0].reset();
        }
        if (xhr.status === 405) {
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
$(document).ready(function(e) {
    $("#checkDate").click(function (e) {
        e.preventDefault();
        var reservation_date = $('#datePickerId').val();
        var id_facility = $('#id_facility').val();
        $.ajax({
            type: "POST",
            url: "http://localhost:9000/check_reservations_on_date",
            data: {reservation_date: reservation_date, id_facility: id_facility},
            success: function (response) {
                // Clear existing content
                $("#dynamicContent").empty();
                $("#checkdate_response").empty();
                // Check if reservation_list is not empty
                if (response.reservation_list && response.reservation_list.length > 0) {
                    // Iterate through the list and append data to dynamicContent
                    $("#dynamicContent").append('<div>' + "<strong>Reserved:</strong><br><br>" + '</div>');
                    $.each(response.reservation_list, function(index, reservation) {
                        var reservationHtml = '';
                        reservationHtml += `<strong> date: ${reservation['date']} </strong> ${reservation['start_hour']} - ${reservation['end_hour']}`
                        $("#dynamicContent").append('<div>' + reservationHtml + '</div>');
                    });
                } else {
                    // Display a message if the list is empty
                    $("#checkdate_response").html("No reservations on this day");
                }
            },
            error: function (xhr, status, error) {
            if (xhr.status === 404) {
                var errorResponse = $.parseJSON(xhr.responseText);
                $("#checkdate_response").html(errorResponse.response);
            }
            if (xhr.status === 500) {
                var errorResponse = $.parseJSON(xhr.responseText);
                $("#checkdate_response").html(errorResponse.response);
            }
            }
        });
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


$("#reserve").submit(function (e) {
    e.preventDefault();
  
    var form = $(this).closest('form');
    var formData = $(this).closest('form').serialize();
  
    $.ajax({
        type: "GET",
        url: "http://localhost:9000/reserve",
        data: formData,
        success: function (response) {
            $("#reservation_response").html(response["response"]);
        },
        error: function (xhr, status, error) {
        if (xhr.status === 404) {
            var errorResponse = $.parseJSON(xhr.responseText);
            $("#reservation_response").html(errorResponse.response);
        }
        if (xhr.status === 500) {
            var errorResponse = $.parseJSON(xhr.responseText);
            $("#reservation_response").html(errorResponse.response);
            form[0].reset();
        }
        }
    });
});


$("#submit_reservation").submit(function (e) {
    e.preventDefault();
  
    var form = $(this).closest('form');
    var formData = $(this).closest('form').serialize();
  
    $.ajax({
        type: "POST",
        url: "http://localhost:9000/reserve",
        data: formData,
        success: function (response) {
            $("#reservation_response").html(response["response"]);
        },
        error: function (xhr, status, error) {
        if (xhr.status === 404) {
            var errorResponse = $.parseJSON(xhr.responseText);
            $("#reservation_response").html(errorResponse.response);
        }
        if (xhr.status === 500) {
            var errorResponse = $.parseJSON(xhr.responseText);
            $("#reservation_response").html(errorResponse.response);
            form[0].reset();
        }
        }
    });
});
