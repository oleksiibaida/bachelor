const app = document.getElementById('device_app');

function appRouter() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/';
        return
    } else {
        renderMainPage();
    }
}
// <form id="FRaddDevice">
async function renderMainPage() {
    app.innerHTML = `
    <div class="main_page">
    <div class="mx-10 justify-center items-center">
        <button id="BTNaddDevice" class="create_house-btn">Add new Device</button>
        <div id="MNaddDevice" class="hidden mn-createhouse">
            
                 <h1>Add New Device</h1>
                <div class="flex items-center">
                    <label for="deviceID" class="block text-gray-700 text-sm font-bold mb-2 mr-2 w-10">ID:</label>
                    <input type="text" id="deviceID" value="" autocomplete="off"
                        class="required flex-1 w-full border border-gray-300 rounded px-3 py-2 mb-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>
                <p id="ERRORaddDeviceId" class="text-red-700 font-bold text-sm"></p>
                <div class="flex items-center">
                    <label for="deviceName" class="block text-gray-700 text-sm font-bold mb-2 mr-2">Name:</label>
                    <input type="text" id="deviceName" value="" autocomplete="off"
                        class="required flex-1 w-full border border-gray-300 rounded px-3 py-2 mb-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>
                <div class="flex items-center">
                    <label for="deviceDesc" class="block text-gray-700 text-sm font-bold mb-2 mr-2">Description:</label>
                    <input type="text" id="deviceDesc" value="" autocomplete="off"
                        class="flex-1 w-full border border-gray-300 rounded px-3 py-2 mb-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>
                <p id="ERRORaddDeviceName" class="text-red-700 font-bold text-sm"></p>
                <div class="flex justify-between">
                    <button id="BTNsaveAddDevice" class="add_room-btn">Save</button>
                    <button id="BTNcancelAddDevice" class="cancel-btn">CancelCCC</button>
                </div>
            
        </div>
    </div>
    <div id="deviceList" class="device_list"></div>
    </div>
    `;

    document.getElementById('BTNaddDevice').addEventListener('click', () => {
        document.getElementById('MNaddDevice').classList.toggle('hidden');
    });

    document.getElementById('BTNcancelAddDevice').addEventListener('click', () => {
        document.getElementById('MNaddDevice').classList.toggle('hidden');
        document.getElementById('deviceID').value = "";
        document.getElementById('deviceName').value = "";
        document.getElementById('deviceDesc').value = "";
    });

    document.getElementById('BTNsaveAddDevice').addEventListener('click', async () => {

        // addNewDevice(document.getElementById('deviceID').value, document.getElementById('deviceName').value);
        // TODO Check if fields are filled
        try {
            const response = await fetch('/add_new_device', {
                method: 'POST',
                headers: {
                    'auth': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    dev_id: document.getElementById('deviceID').value,
                    name: document.getElementById('deviceName').value,
                    description: document.getElementById('deviceDesc').value
                })
            });
            if (!response.ok) {
                console.error(response.status);
                throw new Error(response.status);
            }
            else {
                const response_data = await response.json();
                if (response_data.success) {
                    await loadDevices();
                    console.info(response_data.success);
                }
            }
        } catch (error) {
            errorHandler(error);
        }
        document.getElementById('MNaddDevice').classList.add('hidden');
        document.getElementById('deviceID').value = "";
        document.getElementById('deviceName').value = "";
    });

    await loadDevices();

    async function loadDevices() {
        try {
            const response = await fetch('/get_devices', {
                method: 'GET',
                headers: { 'auth': `Bearer ${localStorage.getItem('token')}` }
            })
            const response_data = await response.json()
            if (!response.ok) {
                throw new Error(response_data.error);
            }
            if (response_data.error) {
                errorHandler(response_data.error);
            }
            displayDevices(response_data);
        } catch (error) {
            console.error(error.message)
            errorHandler(error);
        }
    }

    function displayDevices(device_list) {
        const parent_div = document.getElementById('deviceList');
        parent_div.innerHTML = "";
        if (device_list.length == 0) {
            parent_div.innerHTML = "You have no devices saved. Please add new device";
        } else {
            for (let i = 0; i < device_list.length; i++) {
                const device = device_list[i];
                let room_name = "This device is not signed to Room";
                if (device.room.length > 0) {
                    room_name = device.room[0].name;
                }
                const device_element = document.createElement('div');
                device_element.classList.add('device_element');
                device_element.innerHTML = `
                <div id="device_element${device.dev_id}">
                    <p id="device_name${device.dev_id}" class="flex mx-2 text-3xl">NAME: ${device.name}</p>
                    <h1>DEV_ID: ${device.dev_id}</h1>
                    <p id="device_desc${device.dev_id}" class="flex mx-2">DESC: ${device.description ? device.description : ""}</p>
                    <p>ROOM: ${room_name}</p>
                    <div id="deviceData${device.dev_id}">Waiting for data from device...</div>
                </div>
                <div class="grid place-items-center m-1 p-2">
                    <button id="BTNeditDevice${device.dev_id}" class="add_room-btn my-1">Edit</button>
                    <button id="BTNdeleteDevice${device.dev_id}" class="cancel-sm-btn my-1">Delete</button>
                </div>
                `;

                const ws = new WebSocket(`ws://127.0.0.1:8000/mqtt/device/${device.dev_id}`);

                ws.onopen = () => {
                    ws.send("WS OPEN");
                };

                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    console.info(data);
                    const parent_div = device_element.querySelector(`#deviceData${device.dev_id}`)
                    for (const key in data) {
                        if (data.hasOwnProperty(key)) {
                            let dataField = device_element.querySelector(`#${key}${device.dev_id}`);
                            if (!dataField) {
                                dataField = document.createElement('p');
                                dataField.id = `${key}${device.dev_id}`;
                                parent_div.appendChild(dataField);
                            }
                            dataField.innerHTML = `${key}: ${data[key]}`
                        }
                    }
                    // document.getElementById(`devTemp${device.dev_id}`).textContent = `TEMP: ${data.id}`;
                    // document.getElementById(`devHum${device.dev_id}`).textContent = `HUM: ${data.humidity}`;
                    // document.getElementById(`ambient${device.dev_id}`).textContent = `AMBIENT: ${data.ambient}`;
                };

                ws.onclose = () => {
                    console.error(`WebSocket for device ${device.dev_id} closed`);
                };

                const BTNeditDevice = device_element.querySelector(`#BTNeditDevice${device.dev_id}`);

                // edit device
                BTNeditDevice.addEventListener('click', async () => {
                    const device_name_element = device_element.querySelector(`#device_name${device.dev_id}`);
                    const device_description_element = device_element.querySelector(`#device_desc${device.dev_id}`);
                    if (BTNeditDevice.textContent == "Edit") {
                        // show input fields to change values
                        device_name_element.innerHTML = `Name: <input id="input_device_name${device.dev_id}" type="text" value="${device.name}" autocomplete="off" class="device_edit_input" />`;
                        device_description_element.innerHTML = `DESC: <input id="input_device_description${device.dev_id}" type="text" value="${device.description ? device.description : ""}" autocomplete="off" class="device_edit_input" />`;

                        BTNeditDevice.textContent = "Save";
                    } else {  // save updated data
                        const new_name = device_element.querySelector(`#input_device_name${device.dev_id}`).value;
                        const new_description = device_element.querySelector(`#input_device_description${device.dev_id}`).value;
                        if (device.name != new_name || device.description != new_description) {
                            try {
                                const response = await fetch('/update_device', {
                                    method: 'POST',
                                    headers: {
                                        'auth': `Bearer ${localStorage.getItem('token')}`,
                                        'Content-Type': 'application/json'
                                    },
                                    body: JSON.stringify({ primary: device.primary, dev_id: device.dev_id, name: new_name, description: new_description })
                                });
                                const response_data = await response.json()
                                if (!response.ok) {
                                    throw new Error(response_data.error);
                                }
                                if (response_data.error) {
                                    errorHandler(response_data.error);
                                }
                                device_name_element.innerHTML = `NAME: ${response_data.name}`;
                                device_description_element.innerHTML = `DESC: ${response_data.description}`;

                                BTNeditDevice.textContent = "Edit";
                            } catch (error) {
                                console.error(error);
                            }
                            appRouter();
                        }
                    }
                });

                device_element.querySelector(`#BTNdeleteDevice${device.dev_id}`).addEventListener('click', async () => {
                    try {
                        const response = await fetch('/delete_device', {
                            method: 'DELETE',
                            headers: {
                                'auth': `Bearer ${localStorage.getItem('token')}`,
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(
                                { device_id: device.dev_id, room_id: device.room_id }
                            )
                        });
                        if (!response.ok) {
                            throw new Error(response.stat)
                        }
                        else {
                            const response_data = await response.json();
                            console.info(response_data)
                            if (response_data.success) {
                                console.info(response_data.success);
                                loadHouses();
                            }
                            else {
                                if (response_data.error) {
                                    throw new Error(response_data.error)
                                } else if (response_data.success) {
                                    loadDevices()
                                }
                            }
                        }
                    } catch (error) {
                        appRouter();
                    }
                });

                parent_div.appendChild(device_element);
            }
        }
    }
}

function errorHandler(error) {
    console.error(error);
    alert("ERROR READ CONSOLE");
    if (error.status_code == 401 || error.status == 401) {
        window.location.href = '/';
        return;
    }
}

appRouter();