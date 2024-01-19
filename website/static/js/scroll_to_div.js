
function scrollToDiv(divId) {
    var targetElement = document.getElementById(divId); // Replace with your actual div id

    if (targetElement) {
        var targetOffsetTop = targetElement.getBoundingClientRect().top + window.scrollY;
        window.scrollTo({ top: targetOffsetTop * 0.8, behavior: 'smooth' });
    }
    
}