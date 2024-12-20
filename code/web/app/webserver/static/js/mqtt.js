// Connect to WebSocket
var socket = io.connect('http://' + document.domain + ':' + location.port);

socket.on('connect', function() {
    console.log('WebSocket connected');
});

// Listen for MQTT messages from the server
socket.on('sensor_data', function(data) {
    console.log('Received data: ' + data.data);
    // Update the page with the new data (example: display it in a div)
    document.getElementById('sensorData').innerText = "Sensor Data: " + data.data;
});