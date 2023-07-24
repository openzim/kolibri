var params = URLSearchParams && new URLSearchParams(document.location.search.substring(1));
    var url = params && params.get("url") && decodeURIComponent(params.get("url"));

    // Load the opf
    var book = ePub(url);
    var rendition = book.renderTo("viewer", {
      width: "100%",
      height: 600
    });

    rendition.display();

    /*
    var displayed = rendition.display();

    displayed.then(function(renderer){
      // -- do stuff
    });

    // Navigation loaded
    book.loaded.navigation.then(function(toc){
      // console.log(toc);
    });
    */

    var next = document.getElementById("next");
    next.addEventListener("click", function(){
      rendition.next();
    }, false);

    var prev = document.getElementById("prev");
    prev.addEventListener("click", function(){
      rendition.prev();
    }, false);

    var keyListener = function(e){

      // Left Key
      if ((e.keyCode || e.which) == 37) {
        rendition.prev();
      }

      // Right Key
      if ((e.keyCode || e.which) == 39) {
        rendition.next();
      }

    };

    rendition.on("keyup", keyListener);
    document.addEventListener("keyup", keyListener, false);
