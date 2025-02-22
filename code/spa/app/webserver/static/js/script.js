const app = document.getElementById('app');
let stored_data;
// Start function
// redicrets user to login page if no token
function appRouter() {
    const token = localStorage.getItem('token');
    if (!token) {
        renderLoginForm();
        return;
    }

    fetch('/get_user_data', {
        headers: {
            'auth': `Bearer ${token}`
        }
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error("Invalid Token");
            }
            else return response.json();
        })
        .then((user_data) => {
            if (user_data.error != null) {
                throw new Error(user_data.error);
            }
            else {
                // renderPage('navbar');
                // renderPage('main', user_data);
                stored_data = user_data;
                renderNavbar();
                renderMainPage(user_data);
            }
        })
        .catch((error) => {
            console.error(error)
            localStorage.removeItem('token');
            renderLoginForm();
            return;
        });

}

// shows defined page
async function renderPage(page, data = null) {
    switch (page) {
        case "navbar":
            renderNavbar();
        case "main":
            await renderMainPage(data);
            break;
        case "signup":
            renderSignUpPage();
            break;
        case "mydevice":
            renderMyDevicesPage();
        case "myscenario":
            renderMyScenariosPage();
        default:
            renderLoginForm();
            break;
    }
}


function renderNavbar() {
    navbar = document.querySelector('#navbar');
    navbar.innerHTML = `
    <div class="navbar bg-gray-800 text-white flex justify-between items-center p-6 fixed top-0 left-0 w-full z-10"
    style="height: 5vh;">
    <div class="logo text-xl font-bold">
        <a href="/">Home</a>
    </div>
    <div class="nav-links space-x-4">
        <button id="BTNmyaccount" class="btn-navbar">My Account</button>
        <button id="BTNmydevices" class="btn-navbar">My Devices</button>
        <button id="BTNmyscenario" class="btn-navbar">My Scenarios</button>
        <button id="BTNlogout" class="bg-red-600 px-4 py-2 rounded hover:bg-red-700 transition duration-300">Logout</button>
    </div>
    `;

    // Logout
    navbar.querySelector('#BTNlogout').addEventListener('click', () => {
        localStorage.removeItem('token');
        navbar.innerHTML = '';
        appRouter();
    });

    // My Devices
    navbar.querySelector('#BTNmydevices').addEventListener('click', async () => {
        // renderPage('mydevice');
        renderMyDevicesPage();
    });

    // My Scenarios
    navbar.querySelector('#BTNmyscenario').addEventListener('click', async () => {
        renderMyScenariosPage(stored_data.scenarios);
    });


}

function renderSignUpPage() {
    app.innerHTML = `
    <div class="flex items-center justify-center h-screen">
    <div class="container login-form">
        <h2 class="text-center text-2xl font-bold mb-4">Sign Up</h2>
        <form id="signUpForm">
            <label for="username" class="login-input-label">Username:</label>
            <input type="text" id="username" name="username" class="login-input" required><br>
        
            <label for="email" class="login-input-label">Email:</label>
            <input type="email" id="email" name="email" class="login-input" required><br>
        
            <label for="password" class="login-input-label">Password:</label>
            <input type="password" id="password" name="password" class="login-input" required><br>
        
            <button type="submit" class="login-btn">Sign Up</button>
        </form>
    </div>
    </div>
    `

    // reaction on SignUp button click
    document.getElementById('signUpForm').addEventListener('submit', async (event) => {
        event.preventDefault();
        const username = document.getElementById('username').value;
        const email = document.getElementById('email').value;
        // const password = await hashPassword(document.getElementById('password').value);
        const password = document.getElementById('password').value;

        try {
            const response = await fetch('/sign_up', {
                method: 'POST',
                headers: {
                    'auth': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, email, password })
            });
            // error 
            if (!response.ok) {
                console.error(response.status)
                renderPage('login')
            }
            const response_data = await response.json();
            if (response_data['error']) {
                // TODO tell to change username or email
                // alert(response_data['error']);
                console.error(response_data.error.detail)
                renderPage('login');
                return;
            } else {
                localStorage.setItem('token', response_data['token']);
                appRouter();
            }
        } catch (error) { console.error(error); }
    });
}

function renderLoginForm() {
    app.innerHTML = `
    <div class="flex items-center justify-center h-screen">
        <div class="container login-form">
        <h2 class="text-center text-2xl font-bold mb-4">LOGIN</h2>
        <form id="loginForm" class="space-y-4">
            <div>
            <label for="username" class="login-input-label">Username</label>
            <input type="text" id="username" name="username" class="login-input">
            <p id="ERRORusername" class=""></p>
            </div>
            <div>
            <label for="password" class="login-input-label">Password</label>
            <input type="password" id="password" name="password" class="login-input">
            </div>
            <button type="submit" class="login-btn">LOGIN</button>
        </form>
        <div class="label_register mt-4 text-center">
            <button id="BTNsignup" class="signup-btn text-blue-500 hover:underline">SignUp here</button>
        </div>
        </div>
    </div>
    `;

    // go to sign up
    document.getElementById('BTNsignup').addEventListener('click', (event) => {
        renderSignUpPage();
    });

    document.getElementById('loginForm').addEventListener('submit', async (event) => {
        event.preventDefault();
        const username = document.getElementById('username').value;
        // const password = await hashPassword(document.getElementById('password').value, salt_rounds);
        const password = document.getElementById('password').value;

        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });
            // error
            if (!response.ok) {
                if (response.status === 401) {
                    alert("Invalid username or password");
                } else {
                    alert(`LOGIN FAIL STATUS: ${response.status}`);
                }
                return;
            }
            const response_data = await response.json();
            if (response_data == null) {
                throw new Error('Response is Null');
            }
            if ('token' in response_data) {
                localStorage.setItem('token', response_data['token']);
                // renderPage('main');
                // renderMainPage();
                appRouter();
            } else {
                alert(response_data.error);
                console.error(response_data.error)
                renderPage('login');
                return;
            }
        } catch (error) {
            errorHandler(error);
            renderPage('login');
        }
    });
}

async function renderMainPage(data) {
    console.info(data);
    app.innerHTML = `
    <div class="main_page">
        <div class="flex flex-col justify-center items-center space-y-3">
            <h1>Hello, ${data.user_data.username}</h1>
            <button id="BTNcreateHouse" type="button" class="create_house-btn">Create New House</button>
            <button id="BTNcreateScenario" type="button" class="create_house-btn">Create Scenario</button>
        </div>
        <div id="MNcreateHouse" class="hidden mn-createhouse">
            <div class="p-4">
                <label for="houseName" class="block text-gray-700 text-sm font-bold mb-2">House Name:</label>
                <input type="text" id="houseName" value="House 1"
                    class="w-full border border-gray-300 rounded px-3 py-2 mb-2 focus:outline-none focus:ring-2 focus:ring-blue-500">

                <div class="flex justify-between">
                    <button id="BTNaddHouse"
                        class="create_house-btn">Save</button>
                    <button id="BTNcloseHouseMN"
                        class="cancel-btn">Close</button>
                </div>
            </div>
        </div>
        <div id="MNcreateScenario" class="hidden mn-createhouse">
            <input type="text" id="sourceDevice" placeholder="if">
            <input type="text" id="data_field" placeholder="data_field">
            <input type="text" id="condition" placeholder="condition">
            <input type="number" id="value" placeholder="value">
            <input type="text" id="targetDevice" placeholder="thenDevice">
            <input type="text" id="command" placeholder="command">
            <button id="BTNaddScenario" class="create_house-btn">Save</button>
        </div>

        <div id="houseList" class="houseList"></div>
    </div>
    `;

    displayHouses(data.houses, document.querySelector('#houseList'));

    var BTNcreateHouse = document.getElementById("BTNcreateHouse");
    var MNcreateHouse = document.getElementById("MNcreateHouse");
    // MNcreateHouse.style.display = "none";
    var BTNaddHouse = document.getElementById("BTNaddHouse");
    var BTNcloseHouseMN = document.getElementById("BTNcloseHouseMN")

    document.getElementById("BTNcreateScenario").addEventListener('click', () => {
        document.getElementById("MNcreateScenario").classList.toggle('hidden');
    });

    document.getElementById("BTNaddScenario").addEventListener('click', async () => {
        const source_dev = document.getElementById("sourceDevice").value;
        const data_field = document.getElementById("data_field").value;
        const condition = document.getElementById("condition").value;
        const value = document.getElementById("value").value;
        const target_dev = document.getElementById("targetDevice").value;
        const command = document.getElementById("command").value;
        await createScenario(source_dev, data_field, condition, value, target_dev, command);
        document.getElementById("MNcreateScenario").classList.add('hidden');
    });

    // Create New House click
    BTNcreateHouse.addEventListener("click", () => {
        MNcreateHouse.classList.remove("hidden");
        BTNcreateHouse.classList.add("hidden");
        // MNcreateHouse.style.display = "block";
        // BTNcreateHouse.style.display = "none";
    });

    BTNcloseHouseMN.addEventListener("click", () => {
        closeHouseForm();
    });

    BTNaddHouse.addEventListener("click", async () => {
        await addHouse(document.getElementById("houseName").value);
    });

    // close form if clicked outside
    document.addEventListener("click", (event) => {
        if (!BTNcreateHouse.contains(event.target) && !MNcreateHouse.contains(event.target)) {
            // MNcreateHouse.style.display = "none";
            // BTNcreateHouse.style.display = "block";
            MNcreateHouse.classList.add("hidden");
            BTNcreateHouse.classList.remove("hidden");
        }

    })

    function closeHouseForm() {
        // MNcreateHouse.style.display = "none";
        // BTNcreateHouse.style.display = "block";
        MNcreateHouse.classList.add("hidden");
        BTNcreateHouse.classList.remove("hidden");
    }

    async function createScenario(source_dev, data_field, condition, value, target_dev, command) {
        try {
            const response = await fetch(
                '/add_scenario',
                {
                    method: 'POST',
                    headers: {
                        'auth': `Bearer ${localStorage.getItem('token')}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ source_dev, data_field, condition, value, target_dev, command })
                }
            );
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error);
            }
            const response_data = await response.json()
            if (response_data.error) {
                console.error(response_data.error)
                throw new Error(response_data.error)
            }
            appRouter();
        } catch (error) {
            errorHandler(error);
        }
    }

    function displayHouses(house_list, parent_div) {
        parent_div.innerHTML = '<p> Create new House! </p>';
        if (house_list.length > 0) {
            parent_div.innerHTML = '';
            for (let i = 0; i < house_list.length; i++) {
                // create div for house
                const house = house_list[i];
                const house_element = document.createElement('div');
                house_element.setAttribute('id', `house${house.id}`)
                house_element.classList.add('house_element');
                house_element.innerHTML = `
                <div class="justify-start" id="header${house.id}">&#x25B7 ${house.name} </div>
                <div id="house_element_details${house.id}" class=" hidden house_element_details">
                    <div class="">        
                        <button id="BTNcreateRoom${house.id}" class="add_room-btn">New Room</button>
                        <div id="create_room_element${house.id}" class="hidden create_room_element">
                            <h1>Add New Room</h1>
                            <label for="roomName" class="block text-gray-700 text-sm font-bold mb-2">Room Name:</label>
                            <input type="text" id="roomName${house.id}" value=""
                                class="required w-full border border-gray-300 rounded px-3 py-2 mb-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                            <p id="ERRORaddroom${house.id}" class="text-red-700 font-bold text-sm"></p>
                            <div class="flex justify-between">
                                <button id="BTNaddRoom${house.id}" class="add_room-btn">Add Room</button>
                                <button id="BTNcancelRoom${house.id}" class="cancel-btn">Cancel</button>
                            </div>
                        </div>
                    </div>
                    <div id="room_list${house.id}">NO ROOMS</div>
                    <div>
                    <button id="BTNdeleteHouse${house.id}" class="cancel-btn">Delete House</button>
                    </div>
                </div>
                `;

                parent_div.appendChild(house_element);

                displayRooms(house_element.querySelector(`#room_list${house.id}`), house);

                // Expand House Details on click
                house_element.addEventListener('click', (event) => {
                    // await displayHouseDetails(house_element, house);
                    if (!house_element.querySelector(`#house_element_details${house.id}`).contains(event.target)) {
                        document.getElementById(`house_element_details${house.id}`).classList.toggle('hidden');

                        // side arrows > or down v
                        if (document.getElementById(`house_element_details${house.id}`).classList.contains("hidden")) {
                            document.getElementById(`header${house.id}`).innerHTML = `&#x25B7 ${house.name}`;
                        } else {
                            document.getElementById(`header${house.id}`).innerHTML = `&#x25BD ${house.name}`;
                        }
                    }
                });

                const BTNcreateRoom = document.getElementById(`BTNcreateRoom${house.id}`);
                // Button New Room open form
                BTNcreateRoom.addEventListener('click', () => {
                    BTNcreateRoom.classList.toggle('hidden');
                    document.getElementById(`create_room_element${house.id}`).classList.toggle('hidden');
                });

                // Cancel New Room
                document.getElementById(`BTNcancelRoom${house.id}`).addEventListener('click', () => {
                    BTNcreateRoom.classList.remove('hidden');
                    document.getElementById(`create_room_element${house.id}`).classList.toggle('hidden');
                });

                // Button Add Room
                document.getElementById(`BTNaddRoom${house.id}`).addEventListener('click', async () => {
                    const roomName = document.getElementById(`roomName${house.id}`).value;
                    if (roomName == '' || roomName == null) {
                        // alert("EMPTY ROOM NAME");
                        house_element.querySelector(`#ERRORaddroom${house.id}`).innerHTML = "Please give name for the room";
                        return;
                    }
                    addRoom(house.id, roomName)
                });

                // delete house click
                house_element.querySelector(`#BTNdeleteHouse${house.id}`).addEventListener('click', async () => {
                    await delete_house(house.id);
                });
            }
        }
    }

    function displayRooms(room_list_element, house_data) {
        room_list_element.innerHTML = '';
        if (house_data.rooms.length == 0) {
            room_list_element.innerHTML = `${house_data.name} has no rooms. Please add a room.`;
        } else {
            for (let i = 0; i < house_data.rooms.length; i++) {
                const room = house_data.rooms[i];
                const room_element = document.createElement('div');
                room_element.setAttribute('id', `room${room.id}`)
                room_element.classList.add("room_element");
                room_element.innerHTML = `
                <p id="headerRoom${room.id}" >&#x25B7 ${room.name}</p>
                <div id="room_element_details${room.id}" class="hidden">
                    <button id="BTNaddDevice${room.id}" class="add_room-btn">Add Device</button>
                    <div id="FRaddDevice${room.id}" class="hidden create_room_element">
                        <h1>Add New Device</h1>
                        <div class="flex items-center">
                            <label for="deviceID${room.id}" class="block text-gray-700 text-sm font-bold mb-2 mr-2 w-10">ID:</label>
                            <input type="text" id="deviceID${room.id}" value=""
                                class="required flex-1 w-full border border-gray-300 rounded px-3 py-2 mb-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                        </div>
                        <p id="ERRORaddDeviceId${room.id}" class="text-red-700 font-bold text-sm"></p>
                        <div class="flex items-center">
                            <label for="deviceType${room.id}" class="block text-gray-700 text-sm font-bold mb-2 mr-2 w-10">Type:</label>
                            <select id="deviceType${room.id}">
                                <option value="default">Choose type</option>
                            </select>
                        </div>
                        <p id="ERRORaddDeviceType${room.id}" class="text-red-700 font-bold text-sm"></p>
                        <div class="flex items-center">
                            <label for="deviceName${room.id}" class="block text-gray-700 text-sm font-bold mb-2 mr-2">Name:</label>
                            <button id="BTNnameSameId${room.id}" class = "add_room-sm-btn">Same to ID</button>
                            <input type="text" id="deviceName${room.id}" value=""
                                class="required flex-1 w-full border border-gray-300 rounded px-3 py-2 mb-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                            
                        </div>
                        <p id="ERRORaddDeviceName${room.id}" class="text-red-700 font-bold text-sm"></p>
                        <div class="flex justify-between">
                            <button id="BTNaddNewDevice${room.id}" class="add_room-btn">Save</button>
                            <button id="BTNcancelDevice${room.id}" class="cancel-btn">Cancel</button>
                        </div>
                    </div>                
                    <div id="deviceList${room.id}">NO Devices</div>
                    <button id="BTNdeleteRoom${room.id}" class="cancel-btn">Delete Room</button>
                </div>
                `;
                console.info(room);

                // TODO load device data for the room
                displayDevices(room_element.querySelector(`#deviceList${room.id}`), room);

                room_element.addEventListener('click', (event) => {
                    // await displayHouseDetails(house_element, house);
                    if (!room_element.querySelector(`#room_element_details${room.id}`).contains(event.target)) {
                        document.getElementById(`room_element_details${room.id}`).classList.toggle('hidden');

                        // side arrows > or down
                        if (document.getElementById(`room_element_details${room.id}`).classList.contains("hidden")) {
                            document.getElementById(`headerRoom${room.id}`).innerHTML = `&#x25B7 ${room.name}`;
                        } else {
                            document.getElementById(`headerRoom${room.id}`).innerHTML = `&#x25BD ${room.name}`;
                        }
                    }
                });

                room_element.querySelector(`#BTNnameSameId${room.id}`).addEventListener('click', () => {
                    room_element.querySelector(`#deviceName${room.id}`).value = room_element.querySelector(`#deviceID${room.id}`).value;
                });

                room_element.querySelector(`#BTNdeleteRoom${room.id}`).addEventListener('click', async () => {
                    deleteRoom(room.id, house_data.id);
                })

                room_element.querySelector(`#BTNaddDevice${room.id}`).addEventListener('click', () => {
                    room_element.querySelector(`#FRaddDevice${room.id}`).classList.remove('hidden'); // open form
                    room_element.querySelector(`#BTNaddDevice${room.id}`).classList.add('hidden'); // hide button
                    dev_types = ['Temperature & Humidity Sensor', 'Ligh Sensor', 'Alarming System'];
                    for (dt in dev_types) {
                        type_element = document.createElement('option');
                        type_element.setAttribute("value", dev_types[dt]);
                        type_element.innerHTML = dev_types[dt];
                        room_element.querySelector(`#deviceType${room.id}`).appendChild(type_element);
                    }
                });

                room_element.querySelector(`#BTNcancelDevice${room.id}`).addEventListener('click', () => {
                    room_element.querySelector(`#FRaddDevice${room.id}`).classList.add('hidden'); // open form
                    room_element.querySelector(`#BTNaddDevice${room.id}`).classList.remove('hidden'); // hide button
                    // clear input fields
                    room_element.querySelector(`#deviceID${room.id}`).value = "";
                    room_element.querySelector(`#deviceName${room.id}`).value = "";
                });

                room_element.querySelector(`#BTNaddNewDevice${room.id}`).addEventListener('click', async () => {
                    const dev_id = room_element.querySelector(`#deviceID${room.id}`).value;
                    const dev_name = room_element.querySelector(`#deviceName${room.id}`).value;
                    const dev_type = room_element.querySelector(`#deviceType${room.id}`).value;
                    if (dev_id == "") {
                        room_element.querySelector(`#ERRORaddDeviceId${room.id}`).textContent = 'ID cannot be empty';
                        return;
                    } else { room_element.querySelector(`#ERRORaddDeviceId${room.id}`).textContent = ''; }
                    if (dev_type == "default") {
                        room_element.querySelector(`#ERRORaddDeviceType${room.id}`).textContent = 'U must choose a type';
                        return;
                    } else { room_element.querySelector(`#ERRORaddDeviceType${room.id}`).textContent = ''; }
                    if (dev_name == "") {
                        room_element.querySelector(`#ERRORaddDeviceName${room.id}`).textContent = 'Name cannot be empty';
                        return;
                    } else { room_element.querySelector(`#ERRORaddDeviceName${room.id}`).textContent = ''; }
                    room_element.querySelector(`#ERRORaddDeviceId${room.id}`).textContent = '';
                    room_element.querySelector(`#ERRORaddDeviceName${room.id}`).textContent = '';
                    const res = addDeviceRoom(room.id, dev_id, dev_name, dev_type);
                    // if (res == true) {
                    //     room_element.querySelector(`#FRaddDevice${room.id}`).classList.add('hidden');
                    //     appRouter();
                    // } else {
                    //     // give error message
                    // }

                });

                room_list_element.appendChild(room_element)
            }
        }
    }

    function displayDevices(parent_div, room) {
        try {
            const dev_list = room.devices;
            parent_div.innerHTML = '';
            if (dev_list.length == 0) {
                parent_div.innerHTML = 'NO DEVICES IN THIS ROOM';
            }
            else {
                for (let i = 0; i < dev_list.length; i++) {
                    const device = dev_list[i];
                    const device_element = document.createElement('div');
                    device_element.id = `device${device.dev_id}`;
                    device_element.classList.add('device_element');
                    device_element.innerHTML = `
                    <div>
                        <p class="text-4xl">NAME: ${device.name}</p>
                        <p class="text-base"> ID: ${device.dev_id} </p>
                        <p class="text-2xl"> Type: ${device.dev_type} </p>
                        <div id="deviceData${device.dev_id}" class="device_data">
                            Waiting for data from device
                        </div>
                        <div>
                            <button id="wstest${device.dev_id}">TEST</button>
                        </div>
                    </div>
                    <button id="deleteDevice${device.dev_id}" class="cancel-sm-btn"> DELETE </button>
                    `;

                    const ws = new WebSocket(`ws://127.0.0.1:8000/mqtt/device/${device.dev_id}`);


                    ws.onopen = () => {
                        ws.send(JSON.stringify({ auth: "Bearer " + localStorage.getItem("token") }));
                    };

                    ws.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        console.info(data);
                        const parent_div = device_element.querySelector(`#deviceData${device.dev_id}`);
                        parent_div.innerHTML = "";
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

                    device_element.querySelector(`#wstest${device.dev_id}`).addEventListener('click', async () => {
                        ws.send(`TEST MESSAGE from dev ${device.dev_id}`);
                    });

                    device_element.querySelector(`#deleteDevice${device.dev_id}`).addEventListener('click', async () => {
                        deleteDeviceRoom(room.id, device.dev_id);
                    });

                    parent_div.appendChild(device_element);
                }
            }
        } catch (error) { errorHandler(error); }
    }

    async function addHouse(houseName) {
        try {
            const response = await fetch(
                '/add_house',
                {
                    method: 'POST',
                    headers: {
                        'auth': `Bearer ${localStorage.getItem('token')}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ name: houseName })
                }
            );

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error);
            }
            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }
            appRouter();
        } catch (error) {
            errorHandler(error);
        } finally {

        }
    }

    async function delete_house(house_id) {
        try {
            const response = await fetch(`/delete_house`, {
                method: 'DELETE',
                headers: {
                    'auth': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ house_id })
            });
            if (!response.ok) {
                console.error(response.status);
                throw new Error(response.error);
            }
            else {
                const data = await response.json();
                if (data.error) {
                    throw new Error(data.error);
                }
            }
            appRouter();
        } catch (error) { errorHandler(error); }
        finally {

        }
    }

    async function addRoom(house_id, room_name) {
        try {
            const response = await fetch('/add_room', {
                method: 'POST',
                headers: {
                    'auth': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name: room_name, house_id: house_id })
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error);
            }
            const response_data = await response.json()
            if (response_data.error) {
                console.error(response_data.error)
                document.getElementById('ERRORaddroom').textContent = "Room with this name already exists. Please choose other name";
                throw new Error(response_data.error)
            }
            appRouter();
        } catch (error) { errorHandler(error); }
        finally {
        }
    }

    async function deleteRoom(room_id, house_id) {
        try {
            const response = await fetch(`/delete_room`, {
                method: 'DELETE',
                headers: {
                    'auth': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ room_id, house_id })
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error);
            }
            const response_data = await response.json();
            if (response_data.error) {
                throw new Error(response_data.error)
            }
            appRouter();
        } catch (error) { errorHandler(error); }
        finally {
        }
    }

    async function addDeviceRoom(room_id, device_id, device_name, device_type) {
        try {
            const response = await fetch('/add_new_device', {
                method: 'POST',
                headers: {
                    'auth': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(
                    { dev_id: device_id, name: device_name, dev_type: device_type, room_id: room_id }
                )
            });
            if (!response.ok) {
                console.error(response.status);
                throw new Error(response.status);
            }
            else {
                const response_data = await response.json();
                if (response_data.error) {
                    throw new Error(response_data.error);
                }
            }
            appRouter();
        } catch (error) { errorHandler(error); }
        finally {
        }
    }

    async function deleteDeviceRoom(room_id, device_id) {
        try {
            const response = await fetch('/delete_device', {
                method: 'DELETE',
                headers: {
                    'auth': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(
                    { device_id, room_id }
                )
            });
            if (!response.ok) {
                console.error(response.status);
            }
            else {
                const response_data = await response.json();
                console.info(response_data)
                if (response_data.error) {
                    throw new Error(response_data.error)
                }
            }
            appRouter();
        } catch (error) {
        }
    }
}


async function renderMyDevicesPage() {
    console.info("MYDEV");
    app.innerHTML = `
    <div class="main_page">
        <div id="deviceList" class="device_list"></div>
    </div>
    `;

    let device_list = await loadDevices();
    console.info(device_list);
    displayDevices(device_list, document.querySelector(`#deviceList`));

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
            return response_data;
        } catch (error) {
            errorHandler(error);
        }
    }

    function displayDevices(device_list, parent_div) {
        parent_div.innerHTML = "You have no devices saved. Please add new device";
        if (device_list.length > 0) {
            parent_div.innerHTML = "";
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
                    parent_div.innerHTML = "";
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
                            await renderMyDevicesPage();
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
                            if (response_data.error) {
                                throw new Error(response_data.error)
                            }
                            else if (response_data.success) {
                                console.info(response_data.success);
                                await renderMyDevicesPage();
                            }
                        }
                    } catch (error) {
                        errorHandler(error);
                    }
                });

                parent_div.appendChild(device_element);
            }
        }
    }
}

async function renderMyScenariosPage(scenario_list) {
    app.innerHTML = `
    <div class="main_page">
    <div id="scenarioList" class="device_list"></div>
    </div>
    `;

    displayScenarios(scenario_list, app.querySelector('#scenarioList'));

    function displayScenarios(scenario_list, parent_div) {
        parent_div.innerHTML = "You have no scenarios saved. Please add new scenario";
        if (scenario_list.length > 0) {
            parent_div.innerHTML = "";
            for (let i = 0; i < scenario_list.length; i++) {
                const scenario = scenario_list[i];
                console.info(scenario);
                const scenario_element = document.createElement('div');
                scenario_element.classList.add('device_element');
                scenario_element.innerHTML = `
                    <div id="scenario_element${scenario.id}">
                        <p>IF: ${scenario.source_dev}.${scenario.data_field} ${scenario.condition} ${scenario.value}</p>
                        <p>THEN: ${scenario.target_dev} => ${scenario.command}</p>
                    </div>
                    <div class="grid place-items-center m-1 p-2">
                        <button id="BTNdeleteScenario${scenario.id}" class="cancel-sm-btn my-1">Delete</button>
                    </div>
                `;

                const BTNdeleteScenario = scenario_element.querySelector(`#BTNdeleteScenario${scenario.id}`);

                BTNdeleteScenario.addEventListener('click', async () => {
                    try {
                        const response = await fetch('/delete_scenario', {
                            method: 'DELETE',
                            headers: {
                                'auth': `Bearer ${localStorage.getItem('token')}`,
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(
                                { scenario_id: scenario.id }
                            )
                        });
                        if (!response.ok) {
                            throw new Error(response.stat)
                        } else {
                            const response_data = await response.json();
                            if (response_data.success) {
                                stored_data = await get_user_data();
                                renderMyScenariosPage(stored_data.scenarios);
                            }
                        }
                    } catch (error) {
                        errorHandler(error);
                    }
                });

                parent_div.appendChild(scenario_element);
            }
        }
    }
}

async function get_user_data() {
    try {
        const response = await fetch(
            '/get_user_data',
            {
                method: 'GET',
                headers: {
                    'auth': `Bearer ${localStorage.getItem('token')}`
                }
            }
        );
        if (!response.ok)
            throw new Error(response.stat);
        else {
            const response_data = await response.json();
            if (response_data.error) throw new Error(response_data.error);
            else return response_data;
        }
    } catch (error) {
        errorHandler();
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