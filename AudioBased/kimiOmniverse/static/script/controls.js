
function singleupdate(idx, value) {
    console.log(idx, value)
    fetch('/controls/update?idx='+idx+'&value='+value)
    .then((response) => response.json())
    .then((data) => {
        console.log(data)
        document.getElementById('slider-val-'+idx).innerHTML = value
        document.getElementById('values_display').textContent = JSON.stringify(data['values'])
        document.getElementById('changed_values_display').textContent = JSON.stringify(data['changed_values'])
    });
}

function resetChangedValues() {
    fetch('/controls/resetchangedvalues')
    .then((response) => response.json())
    .then((data) => {
        console.log(data)
        document.getElementById('changed_values_display').textContent = JSON.stringify(data['changed_values'])
    });
}


function pressureoff() {
    fetch('/controls/pressureoff')
    .then((response) => response.json())
    .then((data) => {
        console.log(data)
        // document.getElementById('slider-val-'+idx).innerHTML = value
    });
}

function pressureoffdisconnect() {
    fetch('/controls/pressureoffdisconnect')
    .then((response) => response.json())
    .then((data) => {
        console.log(data)
        // document.getElementById('slider-val-'+idx).innerHTML = value
    });
}

function pressureon() {
    fetch('/controls/pressureon')
    .then((response) => response.json())
    .then((data) => {
        console.log(data)
        // document.getElementById('slider-val-'+idx).innerHTML = value
    });
}

function switchpressure() {
    console.log('switching pressure')
    path = '/controls/'+document.getElementById('pressurebutton').value.split(" ").join("").toLowerCase()
    fetch(path)
    .then((response) => response.json())
    .then((data) => {
        console.log(data)
        v = 'Pressure on'
        if (data['pressure']) {
            v = 'Pressure off'
        }
        document.getElementById('pressurebutton').value = v
    });
}
function changeActuators() {
    fetch('/controls/change_actuators')
    .then((response) => response.json())
    .then((data) => {
        console.log(data);
        document.getElementById('values_display').textContent = JSON.stringify(data['values']);
        document.getElementById('changed_values_display').textContent = JSON.stringify(data['changed_values']);
    });
}



