$("#submitfacilities").click(function(){
    $.get("http://localhost:9000/add", function(data, status){
      $("#response").html(data["response"])
    });
  });