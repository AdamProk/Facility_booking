
main();

function main() {

    let scrollPosition = 0;
    let fade = 100;
    let solidFade = 100;

    document.addEventListener("DOMContentLoaded", function() {
        window.addEventListener("scroll", function() {
          var header = document.querySelector("nav");
          scrollPosition = window.scrollY;
        
          fade = (/*document.body.scrollHeight*/ (this.window.innerHeight * 0.8) - scrollPosition) / (scrollPosition * 0.05);
          solidFade = fade / 3;
          
          // Ensure transparency stays between 0 and 100
          fade = Math.min(100, fade);
          fade = Math.max(0, fade);
          solidFade = Math.min(100, solidFade);
          solidFade = Math.max(0, solidFade);
                    
          // Update the background with the new transparency
          header.style.background = "linear-gradient(0deg, rgba(255, 255, 255, 0.00) "+ solidFade +"%, #40fcbc "+ fade +"%)";
        });
      });

}

