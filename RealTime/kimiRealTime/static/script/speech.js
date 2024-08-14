function speakSample(name) {
    console.log('speakSample', name)
    fetch('/demos/speech/speak?name='+name)
    .then((response) => response.json())
    .then((data) => {
        console.log(data)
        //document.getElementById('anim_'+name).classList.toggle('is-info')
    });
}

function singSample(name) {
    console.log('singSample', name)
    fetch('/demos/speech/sing?name='+name)
    .then((response) => response.json())
    .then((data) => {
        console.log(data)
        //document.getElementById('anim_'+name).classList.toggle('is-info')
    });
}

function speakText() {
    document.getElementById('speakTextButton').classList.toggle('is-loading')
    document.getElementById('speakTextButton').toggleAttribute("disabled");
    text = document.getElementById('speakText').value
    voice = document.getElementById('voice').value
    console.log('speakText', text)
    fetch('/demos/speech/speak?text='+text+'&voice='+voice)
    .then((response) => response.json())
    .then((data) => {
        console.log(data)
    })
    .finally(() => {
        document.getElementById('speakTextButton').classList.toggle('is-loading')
        document.getElementById('speakTextButton').toggleAttribute("disabled");
    });
}

function answerText(text='') {
    document.getElementById('answerTextButton').classList.toggle('is-loading')
    document.getElementById('answerTextButton').toggleAttribute("disabled");
    textfield = document.getElementById('gptInputText')
    if (text.length <= 0) {
      text = textfield.value
    }
    voice = document.getElementById('gptvoice').value
    dialogDiv = document.getElementById('dialog')
    dialogDiv.insertAdjacentHTML(
        'beforeend',
        '<p><strong>You:</strong> '+text+'</p>'
    );
    fetch('/demos/speech/answer?text='+text+'&voice='+voice)
    .then((response) => response.json())
    .then((data) => {
        console.log(data)
        dialogDiv.insertAdjacentHTML(
            'beforeend',
            '<p><strong>Android:</strong> '+data['answer']+'</p>'
        );
        textfield.value = ''
    })
    .finally(() => {
        document.getElementById('answerTextButton').classList.toggle('is-loading')
        document.getElementById('answerTextButton').toggleAttribute("disabled");
        addExternalButtonListeners();
    });
}

function cancelSpeech() {
    fetch('/demos/speech/cancel')
    .then((response) => response.json())
    .then((data) => {
        console.log(data)
        //document.getElementById('anim_'+name).classList.toggle('is-info')
    });
}

function resetDialogSession() {
    fetch('/demos/speech/resetdialog')
    .then((response) => response.json())
    .then((data) => {
        console.log(data)
        document.getElementById('dialog').innerHTML = '<h4 class="subtitle">Current Dialog</h4>'
    });
}

function toggleRecord() {
  listenButton = document.getElementById('recordButton')
  listenButton.classList.toggle('is-info')
  if (listenButton.innerHTML === 'Listen') {
    listenButton.innerHTML = 'Stop listening'
  } else {
    listenButton.innerHTML = 'Listen'
  }
  // device = document.getElementById('audio-input-devices').value
    fetch('/demos/speech/listen') // ?device='+device
    .then((response) => response.json())
    .then((data) => {
        console.log(data)
        if (data['recording'] === true) {
          console.log('in if recording true')
          //document.getElementById('recordButton').toggleAttribute("disabled");
        } else {
          console.log(data)
          answerText(data['text'])
        }
    });
}

function checkForEnterKey(event) {
    if (event.key === 'Enter' && document.getElementById("answerTextButton").getAttribute('disabled') === null) {
        answerText()
    }
}

function checkRecButtonDown(obj) {
  console.log("checkRecButtonDown: ", obj)
   e = obj || window.event;
      if (e.key === "p") { // extra USB key sends a 'p' letter to start recording
      	listenButton = document.getElementById('recordButton')
      	if (listenButton.innerHTML === 'Listen') {
    	  toggleRecord();
  	}
     }
}

function checkRecButtonUp(obj) {
  console.log("checkRecButtonUp: ", obj)
   e = obj || window.event;
      if (e.key === "p") { // extra USB key sends a 'p' letter to start recording
      	  removeExternalButtonListeners();
    	  toggleRecord();
     }
}

function addExternalButtonListeners() {
    document.addEventListener('keydown', checkRecButtonDown);
    document.addEventListener('keyup', checkRecButtonUp);
}

function removeExternalButtonListeners() {
    document.removeEventListener('keydown', checkRecButtonDown);
    document.removeEventListener('keyup', checkRecButtonUp);
}

document.addEventListener('DOMContentLoaded', () => {
    // Functions to open and close a modal
    function openModal($el) {
      $el.classList.add('is-active');
    }
  
    function closeModal($el) {
      $el.classList.remove('is-active');
    }
  
    function closeAllModals() {
      (document.querySelectorAll('.modal') || []).forEach(($modal) => {
        closeModal($modal);
      });
    }
  
    // Add a click event on buttons to open a specific modal
    (document.querySelectorAll('.js-modal-trigger') || []).forEach(($trigger) => {
      const modal = $trigger.dataset.target;
      const $target = document.getElementById(modal);
  
      $trigger.addEventListener('click', () => {
        openModal($target);
      });
    });
  
    // Add a click event on various child elements to close the parent modal
    (document.querySelectorAll('.modal-background, .modal-close, .modal-card-head .delete, .modal-card-foot .button') || []).forEach(($close) => {
      const $target = $close.closest('.modal');
  
      $close.addEventListener('click', () => {
        closeModal($target);
      });
    });
  
    // Add a keydown event listener to close all modals for 'Escape' or start recording for 'p' 
    document.addEventListener('keydown', (event) => {
      const e = event || window.event;
      if (e.key === "Escape") { // Escape key -> keyCode is deprecated https://www.w3schools.com/jsref/event_key_keycode.asp
        closeAllModals();
      }
    });
  
    addExternalButtonListeners();

  });
