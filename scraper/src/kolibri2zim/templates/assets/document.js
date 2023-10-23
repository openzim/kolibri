function resizeFrameToFullHeight(){
    let windowHeight = window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight;
    let frame = document.getElementById("frame");
    let headerHeight = frame.getBoundingClientRect().top;
    let newHeight = windowHeight - headerHeight;
    frame.style.height = newHeight + 'px';
}
window.addEventListener('resize', resizeFrameToFullHeight, {capture: true});
resizeFrameToFullHeight();
