let popup

function toggle_facedetection() {
    console.log('toggle_facedetection')
    document.getElementById('fd_startstop').classList.toggle('is-loading')
    document.getElementById('fd_startstop').toggleAttribute("disabled")
    fetch('/facedetector/toggle_facedetection')
    .then((response) => response.json())
    .then((data) => {
        console.log(data)
        document.getElementById('fd_startstop').classList.toggle('is-info')
    })
    .finally(() => {
        document.getElementById('fd_startstop').classList.toggle('is-loading')
        document.getElementById('fd_startstop').toggleAttribute("disabled")
    });
}

function toggle_facetracking() {
    console.log('toggle_facetracking')
    fetch('/facedetector/track_faces')
    .then((response) => response.json())
    .then((data) => {
        console.log(data)
        document.getElementById('ft_startstop').classList.toggle('is-info')
    });
}

function toggle_img_stream() {
    console.log('popup', popup)
    if (popup && !popup.closed) {
        console.log('popup true')
        stop_img_stream()
    } else {
        console.log('popup false')
        start_img_stream()
    }
}

function start_img_stream() {
    console.log('start_img_stream')
    popup = window.open('/facedetector/video_popup', 'detection stream', 'width=650,height=490');
}

function stop_img_stream() {
    popup.close()
    console.log('stop_img_stream')
    fetch('/facedetector/stop_video')
    .then((response) => response.json())
    .then((data) => {
        console.log(data)
        document.getElementById('start_video_stream').classList.toggle('is-info')
    });
}