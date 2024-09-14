const socket = new WebSocket('ws://localhost:3000');

$(document).ready(() => {
    addSocketEventListeners(socket);

    // start button should invoke the currently active process
    // with the currently active parameters
    $('#startBtn').on('click', () => {
        // obtain current process
        const process = $('#process').val();
        socket.send(process);

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
        socket.send(JSON.stringify(parameters));
    });

    // abort button should send request to kill process
    $('#abortBtn').on('click', () => {
        // TODO: cancellation token to abruptly kill process
        socket.send('QUIT');
    });

    // clear button should clear the console
    $('#clearBtn').on('click', () => {
        $('#console').val('');
    })

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
        console.log(event);
        console.log('Connection Closed');
    })

    socket.addEventListener('message', ({ data }) => {
        $('#console').val($('#console').val() + data);
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
