function toggleAnimation(name) {
    console.log('toggleAnimation', name)
    fetch('/animations/toggle?name='+name)
    .then((response) => response.json())
    .then((data) => {
        console.log(data)
        document.getElementById('anim_'+name).classList.toggle('is-info')
    });
}
function postData(uri, data) {
    fetch(uri, {
        method: "POST", // *GET, POST, PUT, DELETE, etc.
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data), // body data type must match "Content-Type" header
      })
    .then((response) => response.json())
    .then((data) => {
        console.log(data)
        //document.getElementById('anim_'+name).classList.toggle('is-info')
    });
}

function runAnimation() {
    console.log('runAnimation')
    var {valid, data} = parseAndValidateJSONAnimation(document.getElementById('animationArea').value);
    if (valid === true) {
        document.getElementById('animationValidation').classList.add('is-hidden')
        postData('/animations/run', data)
    } else {
        document.getElementById('animationValidation').classList.remove('is-hidden')
        console.log('error parsing animation json:', data)
    }
}


function saveAnimation() {
    console.log('saveAnimation')
    var {valid, data} = parseAndValidateJSONAnimation(document.getElementById('animationArea').value);
    if (valid === true) {
        document.getElementById('animationValidation').classList.add('is-hidden')
        postData('/animations/save', data)
    } else {
        document.getElementById('animationValidation').classList.remove('is-hidden')
        console.log('error parsing animation json:', data)
    }
}

function stopAnimation() {
    const name = JSON.parse(document.getElementById('animationArea').value)['header']['name'];
    console.log('stopAnimation'+name)
    fetch('/animations/stop?name='+name)
    .then((response) => response.json())
    .then((data) => {
        console.log(data)
    });
}


window.onload = function loadcurrentanimation() {
    console.log('loadcurrentanimation')
    console.log(document.getElementById('animationArea') !== null)
    let storedAnimation = sessionStorage.getItem('currentAnimation')
    if (storedAnimation === null || storedAnimation.trim().length === 0) {
        console.log('loadcurrentanimation, nothing found using default')
        storedAnimation = 
`{
    "description": "Default animation for editor based on blink animation",
    "header": {"target": "head", "name": "work_in_progress", "group": "test", "minPauseFrames": 20, "maxPauseFrames": 100, "loop": -1, "prio": 50},
    "frames": [
        {"frame": 0, "values": [0, null, null, 0, null, null, null, null, null, null, null, null, null, null]},
        {"frame": 1, "values": [255, null, null, 70, null, null, null, null, null, null, null, null, null, null]},
        {"frame": 3, "values": [0, null, null, 0, null, null, null, null, null, null, null, null, null, null]}
    ]
}`
    }
    if (document.getElementById('animationArea') !== null) {
        document.getElementById('animationArea').value = storedAnimation
    }
}

window.onunload = function savecurrentanimation() {
    console.log('savecurrentanimation')
    console.log(document.getElementById('animationArea') !== null)
    console.log(document.getElementById('animationArea').value)

    if (document.getElementById('animationArea') !== null) {
        sessionStorage.setItem("currentAnimation", document.getElementById('animationArea').value);
    }
}

function parseAndValidateJSONAnimation(animStr) {
    try {
        var obj = JSON.parse(animStr);
        if (!obj.hasOwnProperty('frames')) {
            return {valid: false, data: 'missing frames'}
        }
        return {valid: true, data: obj}
    }
    catch (e) {
        return {valid: false, data: e}
    }
}

function startStaring() {
    fetch('/animations/facetracking')
    .then((response) => response.json())
    .then((data) => {
        console.log(data)
        //document.getElementById('anim_'+name).classList.toggle('is-info')
    });
}