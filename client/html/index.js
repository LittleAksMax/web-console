const socket = new WebSocket('ws://localhost:3000');

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
                    socket.send(JSON.stringify({"type": "AUTH", "data": hex}));

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
        socket.send(JSON.stringify({"type": "SELECT", "data": process}));

        // get input elements inside the parameter box of
        // the current process
        let parameters = {}; // start with an empty object
        console.log($(`#${process}Params fieldset input`));
        const inputs = $(`#${process}Params fieldset input`);
        for (let i = 0; i < inputs.length; i++) {
            const input = $(inputs[i]);
            const name = input.attr('name');
            const value = input.val();

            parameters[name] = value;
        }

        console.log(parameters);
        socket.send(JSON.stringify({"type": "DATA", "data": parameters}));
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
        }, 500);
    });

    socket.addEventListener('message', ({ data }) => {
        $('#console').append(data);
        let psconsole = $('#console');
        if (psconsole.length) {
           psconsole.scrollTop(psconsole[0].scrollHeight - psconsole.height());
        }

        // if it is the specific error message, we need to reauthenticate
        if (data.trim() === 'error: invalid authentication') {
            window.location.reload();
            alert('invalid authentication');
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
