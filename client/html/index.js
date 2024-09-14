const socket = new WebSocket('ws://localhost:3000');

$(document).ready(() => {
    socket.addEventListener('open', async (event) => {
        console.log('Connection Established');
    });
    
    socket.addEventListener('close', (event) => {
        console.log('Connection Closed');
    })
    
    socket.addEventListener('message', ({ data }) => {
        $('#console').val($('#console').val() + data);
    });

    $('#startBtn').on('click', () => {
        // TODO: JSONify and send data to initialise process
        socket.send('Ping');
    });

    $('#abortBtn').on('click', () => {
        // TODO: cancellation token to abruptly kill process
        socket.send('QUIT');
    });

    $('#clearBtn').on('click', () => {
        $('#console').val('');
    })
});