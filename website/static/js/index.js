$("#submitfacilities").click(function(){
    $.get("http://localhost:9000/add", function(data, status){
      $("#response").html(data["response"])
    });
  });

  $("#submitregistration").click(function(){
    $.get("http://localhost:9000/register_acc", function(data, status){
      $("#register_response").html(data["response"])
    });
  });