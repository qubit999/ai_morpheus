function getCookie(name) {
    let match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    if (match) return match[2];
    return null;
}

function setCookie(name, value, days) {
    let date = new Date();
    date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
    document.cookie = `${name}=${value};expires=${date.toUTCString()};path=/`;
}

function deleteCookie(name) {
    document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:01 GMT;path=/`;
}

function isJSON(str) {
    try {
      JSON.parse(str);
      return true;
    } catch (e) {
        console.log('Error:', e);
      return false;
    }
  }

function createThread(payload) {
    deleteCookie('thread_id');
    const accessToken = getCookie('access_token');
    fetch('/threads/create/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
        }, body: JSON.stringify(payload)
    }).then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        setCookie('thread_id', response.json().thread_id, 7);
        thread_id = response.json().thread_id;
        return thread_id;
    }).catch(error => {
        console.error('Error during fetch:', error);
    });
}

function updateThread(payload) {
    const accessToken = getCookie('access_token');
    const thread_id = getCookie('thread_id');
    fetch(`/threads/get/${thread_id}/add_message`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
        }, body: JSON.stringify(payload, thread_id)
    }).then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        if (response.json().successful) {
            return true;
        } else {
            return null;
        }
    }).catch(error => {
        console.error('Error during fetch:', error);
    });
}

function getThread(thread_id) {
    const accessToken = getCookie('access_token');
    setCookie('thread_id', thread_id, 7);
    fetch(`/threads/get/${thread_id}/messages`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
        }, body: JSON.stringify(payload)
    }).then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    }).catch(error => {
        console.error('Error during fetch:', error);
    });
}

function getAllThreads() {
    const accessToken = getCookie('access_token');
    fetch('/model/get_all_threads', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
        }
    }).then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    }).catch(error => {
        console.error('Error during fetch:', error);
    });
}

function disableThread(thread_id) {
    const accessToken = getCookie('access_token');
    fetch(`/threads/get/${thread_id}/disable`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
        }, body: JSON.stringify(payload)
    }).then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    }).catch(error => {
        console.error('Error during fetch:', error);
    });
}

async function postAndStreamSSE(url, payload, result_element) {
    const accessToken = getCookie('access_token');
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            console.log(buffer);

            let boundary;
            while ((boundary = buffer.indexOf("\n\n\n\n")) !== -1) {
                const message = buffer.slice(0, boundary).trim();
                buffer = buffer.slice(boundary + 1);

                if (message.startsWith('data:')) {
                    let data = message.slice(5).trim();
                    try {
                        let element = document.createElement('p');
                        element.textContent = data;
                        result_element.appendChild(element);
                    } catch (e) {
                        console.error('Error: ', e);
                    }
                }
            }
        }
    } catch (error) {
        console.error('Error reading stream:', error);
    } finally {
        reader.releaseLock();
    }
}

if(document.querySelector("#send_message")){

    document.querySelector("#send_message").addEventListener("click", async function() {
        const formData = new FormData(document.querySelector('#chat_form'));
        const payload = {};
        formData.forEach((value, key) => {
            payload[key] = value;
        });
        console.log('Payload:', payload); // Log the payload
        let chatbox = document.querySelector("#chat");
        let messages = formData.get('messages');
        console.log('Messages:', messages);
        let newMessage = document.createElement('p');
        newMessage.textContent = `User: ${messages}`;
        chatbox.appendChild(newMessage);
        await postAndStreamSSE('/model/streaming_response', payload, document.querySelector('#chat'));
    });
}

    document.body.addEventListener('htmx:configRequest', function(event) {
        const accessToken = getCookie('access_token');
        
        if (accessToken) {
            event.detail.headers['Authorization'] = `Bearer ${accessToken}`;
        }
    });

    let form_reg = document.querySelector('#register');
    if(form_reg){
        form_reg.addEventListener('input', function(e){
            checkForm();
        });

        function checkForm(){
            password1 = document.querySelector('input[name="password1"]');
            password2 = document.querySelector('#password2');
            username = document.querySelector('input[name="username"]');
            checkbox = document.querySelector('input[type="checkbox"]');
            button = document.querySelector('button[type="submit"]');
            if(checkbox.checked == false || password1.value != password2.value || password1.value == "" || password2.value == "" || username.value == ""){
                button.disabled = true;
                button.classList.add('cursor-not-allowed');
            } else {
                button.disabled = false;
                button.classList.remove('cursor-not-allowed');
            }
        }
    }

let response_info = document.querySelector('#response_info');

const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {

        if(!isJSON(mutation.target.innerHTML)){
            return;
        }

        let response_info = document.querySelector('#response_info');
        const jsonResponse = JSON.parse(response_info.textContent);

        if(jsonResponse['error']){
            return;
        }

        let content = '<ul>';
        for (const [key, value] of Object.entries(jsonResponse)) {
            if (key != "" && value != "") { 
                content += `<li><strong>${key}:</strong> ${value}</li>`;
            }
        }
        content += '</ul>';

        document.querySelector('#response_info').innerHTML = content;
    });
});

observer.observe(response_info, {
    childList: true,
    subtree: false,
    characterData: false
  });

  /*
  document.getElementById('send_message').addEventListener('click', function(event) {
      const formData = new FormData(document.querySelector('#chat_form'));
      const message = formData.get('messages');
      const model = formData.get('model');

      if (message.trim() !== '') {
          const chatDiv = document.getElementById('chat');
          const newMessage = document.createElement('p');
          newMessage.textContent = message;
          chatDiv.appendChild(newMessage);
      }

      const access_token = getCookie('access_token');
      fetch('/model/response', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${access_token}`,
          },
          body: JSON.stringify({ messages: [{"role": "user", "content": message}], model: model }),
      })
      .then(response => {
          if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
      })
      .then(jsonResponse => {
          try {
              let result_element = document.querySelector('#chat');
              result_element.appendChild(document.createTextNode(jsonResponse));
          } catch (error) {
              console.error('Error accessing message content:', error);
          }
      })
      .catch(error => {
          console.error('Error during fetch:', error);
      });
  });
*/