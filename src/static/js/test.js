document.addEventListener('htmx:afterSwap', function(evt) {
    if (evt.detail.xhr.getResponseHeader('Content-Type').includes('application/json')) {
        evt.preventDefault(); 

        const jsonResponse = JSON.parse(evt.detail.xhr.responseText);

        let csrf_token = document.querySelector('#csrf_token').innerHTML;
        let content = `<form id="profile_update"><ul>`;
        content+= `<input type="hidden" name="csrf_token" value="${csrf_token}">`;
        let keys = Object.keys(jsonResponse);
        let filter_list = ['_id', 'password1', 'password2', 'registration_date', 'last_login', 'registration_ip', 'last_ip', 'role', 'disabled', 'message'];

        for (const [key, value] of Object.entries(jsonResponse)) {
            if(filter_list.includes(key)){
                continue;
            }
            content += `<li><strong>${key}</strong> <input name="${key}" type="text" value="${value}"></li>`;
        }
        content += `<button type="submit" id="update_profile" hx-post="/user/update/" hx-params="*" hx-ext="json-enc" hx-target="#info_result" hx-swap="innerHTML">Save</button></ul></form>`;

        document.getElementById('settings').innerHTML = content;
        htmx.process(document.getElementById('settings'));

        document.querySelector("#info_result").addEventListener('change', function(e){
            const event = new Event('result_ready');
            document.dispatchEvent(event);
        });        
    }
});

document.addEventListener('result_ready', function(e){
    let info_result_content = document.querySelector('#info_result').innerHTML;
    console.log(info_result_content);
    try {
        let info_result = JSON.parse(info_result_content);
        document.querySelector('#info_result').innerHTML = info_result.message;
    } catch (error) {
        console.error('Error parsing JSON:', error);
    }
});