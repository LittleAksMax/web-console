const socket = new WebSocket('ws://localhost:3000/');

const getCookieMap = () => {
    const keyValPairs = document.cookie.split(';');

    let cookies = {};
    keyValPairs.forEach(keyValPair => {
        const [key, val] = keyValPair.split('=');

        // ignore empty
        if (!key || key === '') {
            return;
        }

        cookies[key] = val;
    });
    return cookies;
}

const getCookie = (key) => {
    const cookies = getCookieMap();
    if (key in cookies) {
        return cookies[key];
    } else {
        return '';
    }
}

const setCookie = (key, val) => {
    const cookies = getCookieMap();
    
    // if no change, do nothing
    if (key in cookies && cookies[key] === val) {
        return;
    }

    // otherwise update map, and reconstruct cookies
    cookies[key] = val;

    let cookie = '';
    for (const key in cookies) {
       cookie += `${key}=${cookies[key]};`;
    }
    
    document.cookie = cookie;
}

$(document).ready(() => {
    addSocketEventListeners(socket);

    window.addEventListener('beforeunload', (event) => {
        console.log('QUITTING');
    });

    $('.auth').on('submit', (event) => {
        event.preventDefault();
        const key = $('#authKey').val();
        crypto.subtle
            .digest('SHA-512', new TextEncoder('utf-8').encode(key))
                .then(res => {
                    // the hex conversion is ChatGPT:
                    // Convert ArrayBuffer to Array of bytes
                    const resArray = Array.from(new Uint8Array(res));
                    // Convert bytes to hexadecimal string
                    const hex = resArray.map(b => b.toString(16).padStart(2, '0')).join('');
                    
                    // send data
                    const sid = getCookie('sid');
                    socket.send(JSON.stringify({"type": "AUTH", "data": hex, "sid": sid}));

                    // change DOM
                    $('#process').show();
                    $('.parameters').show();
                    $('.controlBox').show();
                    $('.consoleContainer').show();
                    $('.auth').hide();
                    $('#authKey').val('');
                })
                .catch(err => {
                    console.error(err);
                });
    });

    // start button should invoke the currently active process
    // with the currently active parameters
    $('#startBtn').on('click', () => {
        // obtain current process
        const process = $('#process').val();
        const sid = getCookie('sid');
        socket.send(JSON.stringify({"type": "SELECT", "data": process, "sid": sid}));

        // get input elements inside the parameter box of
        // the current process
        let parameters = {}; // start with an empty object
        const inputs = $(`#${process}Params fieldset input`);
        for (let i = 0; i < inputs.length; i++) {
            const input = $(inputs[i]);
            const name = input.attr('name');
            const value = input.val();

            parameters[name] = value;
        }

        socket.send(JSON.stringify({"type": "DATA", "data": parameters, "sid": sid}));
    });

    // abort button should send request to kill process
    $('#abortBtn').on('click', () => {
        socket.close();

        // reload window
        window.location.reload();
    });

    // clear button should clear the console
    $('#clearBtn').on('click', () => { $('#console').val(''); });

    // we want to change the parameters every time the process
    // changes in the dropdown
    $('#process').on('change', activateCurrentProcessParameters);

    // make sure to activate the currently active process
    activateCurrentProcessParameters();
});

const addSocketEventListeners = (socket) => {
    socket.addEventListener('open', async (event) => {
        console.log('Connection Established');
    });

    socket.addEventListener('close', (event) => {
        console.log('Connection Closed');
        setTimeout(() => {
            // refresh to recreate-connection
            window.location.reload();
        }, 1000);
    });

    socket.addEventListener('message', ({ data }) => {
        const re = new RegExp('Session ID: ([a-f0-9]+)\\s?');
        const matches = data.trim().match(re);

        // if there is a match, then we were sent the SID
        if (matches) {
            const sid = matches[1]; // get first capture group
            setCookie('sid', sid);
        } else {
            $('#console').append(data);
            let psconsole = $('#console');
            if (psconsole.length) {
                psconsole.scrollTop(psconsole[0].scrollHeight - psconsole.height());
            }
        }

        // if it is the specific error message, we need to reauthenticate
        if (data.trim() === 'error: invalid authentication') {
            alert('invalid authentication');
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        }
    });
}

const activateCurrentProcessParameters = () => {
    // hide all of them
    $('.parameters > .paramGroup').attr('hidden', true);

    // get currently active process
    const activeProcess = $('#process').val();
    
    // all divs containing the parameters should have ID
    // in format '<processName>Params'
    // un-hide the active one process' parameters
    $(`#${activeProcess}Params`).attr('hidden', false);
}
