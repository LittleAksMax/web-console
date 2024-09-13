const socket = new WebSocket('ws://localhost:3000');

$(document).ready(() => {
    socket.addEventListener('open', async (event) => {
        console.log('Connection Established');
    });
    
    socket.addEventListener('close', (event) => {
        console.log('Connection Closed');
    })
    
    socket.addEventListener('message', (event) => {
        console.log(event);
    });

    $(document).ready(() => {
        $('#sendBtn').on('click', (event) => {
            socket.send('Ping');           
        });

        $('#quitBtn').on('click', () => {
            socket.send('QUIT');
        })
    });
});