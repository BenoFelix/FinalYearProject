function getVillageInfo() {
    var location = encodeURIComponent(document.getElementById('villageInput').value);
    var searchUrl = 'https://www.google.com/maps/search/?api=1&query=Esevai+Maiyam+near+' + location;
    window.open(searchUrl, '_blank');
}

function closeAlert(alertElement) {
        alertElement.classList.remove("show");
        setTimeout(function() {
            alertElement.style.display = "none";
        }, 500);
    }

function toggleChat() {
    // Show/hide the chat modal
    var chatModal = new bootstrap.Modal(document.getElementById('chatModal'));
    chatModal.toggle();
}

function makeCall() {
    // Add logic for making a call
    console.log("Initiate call");
} // Function to open the call modal
function openCallModal() {
    var callModal = new bootstrap.Modal(document.getElementById('callModal'));
    callModal.show();
}

function checkValues() {
    var value1 = document.getElementById('new').value;
    var value2 = document.getElementById('retype').value;

    if (value1 !== value2) {
        alert('The both values are not the same.');
    } else {
        document.getElementById('Password_form').submit();
    }
}

async function sendMessage() {
    // Get user input
    var userInput = document.querySelector('.chat-input textarea').value.trim();

    // Check if the input is not empty
    if (userInput !== '') {
        // Display user message
        displayMessage('sent', userInput);

        // Send user message to backend
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_message: userInput }),
        });

        const data = await response.json();

        // Display chatbot response
        displayMessage('received', data.reply);
    }

    // Clear user input
    document.querySelector('.chat-input textarea').value = '';
}

document.addEventListener("DOMContentLoaded", function() {
    displayMessage('received', 'Hello, how can I assist you today?', getCurrentTime());
});

function displayMessage(sender, message, timestamp) {
    var chatbox = document.querySelector('.chat-messages');
    var messageDiv = document.createElement('div');
    messageDiv.className = 'message ' + sender;
    var messageContent = '';
    var lines = message.split('\n'); // Split message by new line
    for (var i = 0; i < lines.length; i++) {
        var line = lines[i];
        var colonIndex = line.indexOf(':'); // Find the index of the colon
        if (colonIndex !== -1) {
            var key = line.substring(0, colonIndex + 1); // Extract key
            var value = line.substring(colonIndex + 1); // Extract value
            // Append key-value pair with proper alignment
            messageContent += '<p><span class="key">' + key + '</span>' + value + '</p>';
        } else {
            messageContent += '<p>' + line + '</p>'; // If no colon, append the line as is
        }
    }
    messageContent += '<span class="timestamp">' + (timestamp || getCurrentTime()) + '</span>' + '<span class="tick-mark">&#10004;</span>';
    messageDiv.innerHTML = messageContent;
    chatbox.appendChild(messageDiv);
    if (sender === 'received') {
        var receivedMessage = messageDiv;
        var tickMark = receivedMessage.querySelector('.tick-mark');
        tickMark.innerHTML = '&#10004;&#10004;';
    }
}



function getCurrentTime() {
    // Simulate getting the current time (replace with actual time logic if needed)
    var currentTime = new Date();
    var hours = currentTime.getHours();
    var minutes = currentTime.getMinutes();
    return hours + ':' + (minutes < 10 ? '0' : '') + minutes;
}

function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault(); // Prevents the default behavior (e.g., newline in the textarea)
        sendMessage(); // Call your sendMessage function when Enter key is pressed
    }
}


  function addTextBox() {
    var additionalTextBoxesContainer = document.getElementById('additionalTextBoxesContainer');
    var newInputGroup = document.createElement('div');
    newInputGroup.className = 'input-group';

    var textBox1 = document.createElement('input');
    textBox1.type = 'text';
    textBox1.name = 'textbox1[]';
    textBox1.className = 'form-control';
    textBox1.placeholder = 'Text Box 1';

    var textBox2 = document.createElement('input');
    textBox2.type = 'text';
    textBox2.name = 'textbox2[]';
    textBox2.className = 'form-control';
    textBox2.placeholder = 'Text Box 2';

    var removeButton = document.createElement('span');
    removeButton.className = 'remove-btn';
    removeButton.textContent = 'Remove';
    removeButton.onclick = function() {
      removeTextBox(this);
    };

    newInputGroup.appendChild(textBox1);
    newInputGroup.appendChild(textBox2);
    newInputGroup.appendChild(removeButton);

    additionalTextBoxesContainer.appendChild(newInputGroup);
  }

  function removeTextBox(element) {
    var parentDiv = element.parentNode;
    parentDiv.parentNode.removeChild(parentDiv);
  }
