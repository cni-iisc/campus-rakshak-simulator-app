$("#search").on("keyup", function() {
     var value = $(this).val().toLowerCase();
     console.clear()
     $("table tr").each(function(index) {
       if (index !== 0) {
         $row = $(this);
         $row.find("td").each(function(i, td) {
           var id = $(td).text().toLowerCase();
           if (id.indexOf(value) !== -1) {
             $row.show();
             return false;
           } else {
             $row.hide();
           }
         })
       }
     });
   });