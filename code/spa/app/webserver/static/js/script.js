const app = document.getElementById('app')

// redicrets user to login page if no token
function appRouter() {
    const token = localStorage.getItem('token');
    if (!token) {
        renderLoginForm();
        return;
    }

    fetch('/user', {
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
            else renderPage('main', user_data);
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
        case "main":
            renderMainPage(data);
            break;
        case "signup":
            renderSignUpPage();
            break;
        default:
            renderLoginForm();
            break;
    }
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
        } catch (error) {
            console.error(error);
        }
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
            if (response_data == null){
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
            console.error(error);
            renderPage('login');
        }
    });
}

async function renderMainPage(data) {
    app.innerHTML = `
    <div class="main_page">
        <div class="flex flex-col justify-center items-center space-y-3">
            <h1>Hello, ${data.username}</h1>
            <button id="BTNcreateHouse" type="button" class="create_house-btn">Create New House</button>
        </div>
        <div id="MNcreateHouse" class="hidden mn-createhouse">
            <div class="p-4">
                <label for="houseName" class="block text-gray-700 text-sm font-bold mb-2">House Name:</label>
                <input type="text" id="houseName" value="House 1"
                    class="w-full border border-gray-300 rounded px-3 py-2 mb-2 focus:outline-none focus:ring-2 focus:ring-blue-500">

                <div class="flex justify-between">
                    <button id="BTNaddHouse"
                        class="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded">Save</button>
                    <button id="BTNcloseHouseMN"
                        class="cancel-btn">Close</button>
                </div>
            </div>
        </div>
        <div class="hidden">
            <p>FIND ME</p>
        </div>
        <div id="houseList" class="houseList"></div>
    </div>
    `;

    await loadHouses(); // shows user houses
    var BTNcreateHouse = document.getElementById("BTNcreateHouse");
    var MNcreateHouse = document.getElementById("MNcreateHouse");
    // MNcreateHouse.style.display = "none";
    var BTNaddHouse = document.getElementById("BTNaddHouse");
    var BTNcloseHouseMN = document.getElementById("BTNcloseHouseMN")

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
        try {
            await addHouse();
        } catch (error) {
            console.error(error);
            alert("ERROR ADD HOUSE")
        }
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

    async function loadHouses() {
        try {
            const response = await fetch('/get_houses', {
                method: 'GET',
                headers: { 'auth': `Bearer ${localStorage.getItem('token')}` }
            })
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error);
            }
            const response_data = await response.json()
            if (response_data.error) {
                console.error(response_data.error)
                throw new Error(response_data.error)
            }
            displayHouses(response_data);
        } catch (error) {
            console.error(error)
        }
    }

    function displayHouses(house_list) {
        const parent_div = document.getElementById('houseList');
        parent_div.innerHTML = '';
        if (house_list.length == 0) {
            parent_div.innerHTML = '<p> EMPTY </p>';
        } else {
            for (let i = 0; i < house_list.length; i++) {
                // create div for house
                // let element_height = (window.innerHeight - 100)/house_list.length;
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
                            <p id="ERRORaddroom" class="text-red-700 font-bold text-sm"></p>
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

                house_element.addEventListener('click', (event) => {
                    // await displayHouseDetails(house_element, house);
                    if (!house_element.querySelector(`#house_element_details${house.id}`).contains(event.target)) {
                        document.getElementById(`house_element_details${house.id}`).classList.toggle('hidden');

                        // side arrows > or down
                        if (document.getElementById(`house_element_details${house.id}`).classList.contains("hidden")) {
                            document.getElementById(`header${house.id}`).innerHTML = `&#x25B7 ${house.name}`;
                        } else {
                            document.getElementById(`header${house.id}`).innerHTML = `&#x25BD ${house.name}`;
                        }
                    }
                });
                const BTNcreateRoom = document.getElementById(`BTNcreateRoom${house.id}`);

                BTNcreateRoom.addEventListener('click', () => {
                    BTNcreateRoom.classList.toggle('hidden');
                    document.getElementById(`create_room_element${house.id}`).classList.toggle('hidden');
                });

                // cancel event
                document.getElementById(`BTNcancelRoom${house.id}`).addEventListener('click', () => {
                    BTNcreateRoom.classList.remove('hidden');
                    document.getElementById(`create_room_element${house.id}`).classList.toggle('hidden');
                });

                // add room click
                document.getElementById(`BTNaddRoom${house.id}`).addEventListener('click', async () => {
                    const roomName = document.getElementById(`roomName${house.id}`).value;
                    if (roomName == '' || roomName == null) {
                        alert("EMPTY ROOM NAME");
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
                            <label for="deviceName${room.id}" class="block text-gray-700 text-sm font-bold mb-2 mr-2">Name:</label>
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

                room_element.querySelector(`#BTNdeleteRoom${room.id}`).addEventListener('click', async () => {
                    deleteRoom(room.id, house_data.id);
                })

                room_element.querySelector(`#BTNaddDevice${room.id}`).addEventListener('click', () => {
                    room_element.querySelector(`#FRaddDevice${room.id}`).classList.remove('hidden'); // open form
                    room_element.querySelector(`#BTNaddDevice${room.id}`).classList.add('hidden'); // hide button
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
                    if (dev_id == "") {
                        room_element.querySelector(`#ERRORaddDeviceId${room.id}`).textContent = 'ID cannot be empty';
                        return;
                    } else if (dev_name == "") {
                        room_element.querySelector(`#ERRORaddDeviceName${room.id}`).textContent = 'Name cannot be empty';
                        return;
                    } else {
                        room_element.querySelector(`#ERRORaddDeviceId${room.id}`).textContent = '';
                        room_element.querySelector(`#ERRORaddDeviceName${room.id}`).textContent = '';
                        const res = addDeviceRoom(room.id, dev_id, dev_name);
                        if (res == true) {
                            // close form
                        } else {
                            // give error message
                        }
                    }
                });

                room_list_element.appendChild(room_element)
            }
        }
    }

    function displayDevices(parent_div, room) {
        const dev_list = room.devices;
        parent_div.innerHTML = '';
        if (dev_list.length == 0) {
            parent_div.innerHTML = 'NO DEVICES IN THIS ROOM';
        }
        else {
            for (let i = 0; i < dev_list.length; i++) {
                const device = dev_list[i];
                const device_element = document.createElement('div');
                device_element.classList.add('device_element');
                device_element.innerHTML = `
                <div>
                    <h1>DEVICE_ID ${device.dev_id} NAME ${device.name}</h1>
                    <h4>TEMP</h4>
                    <h4>HUM</h4>
                </div>
                <button id="deleteDevice${device.dev_id}" class="cancel-sm-btn"> DELETE </button>
                `;

                device_element.querySelector(`#deleteDevice${device.dev_id}`).addEventListener('click', async () => {
                    deleteDeviceRoom(room.id, device.dev_id);
                });

                parent_div.appendChild(device_element);
            }
        }

    }

    async function addHouse() {
        const houseName = document.getElementById("houseName").value;
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
                alert(data.error)
                throw new Error(data.error);
            } else {
                // appRouter();
                displayHouses();
            }
        } catch (error) {
            console.error(error);
        } finally {
            closeHouseForm();
            appRouter();
        }
    }

    async function delete_house(house_id) {
        const response = await fetch(`/delete_house`, {
            method: 'DELETE',
            headers: {
                'auth': `Bearer ${localStorage.getItem('token')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({house_id})
        });
        if (!response.ok) { console.error(response.status); }
        else {
            const data = await response.json();
            if (data.success) {
                // alert("HOUSE DELETED");
                document.getElementById(`house${house_id}`).remove();
            }
            else {
                console.info(data);
                alert("HOUSE COULD NOT BE DELETED")
            }
            appRouter();
        }

    }

    async function addRoom(house_id, room_name) {
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
        else {
            // document.getElementById(`create_room_element${house.id}`).classList.add('hidden');
            loadHouses();
            // document.getElementById(`BTNcreateRoom${house.id}`).classList.remove('hidden');
            // appRouter();
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
                body: JSON.stringify({room_id, house_id})
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error);
            }
            const response_data = await response.json();
            if (response_data.eror) {
                console.error(response_data.error);
                alert("ERROR WHEN DELETING THE ROOM")
            } else if (response_data.success) {
                document.getElementById(`room${room_id}`).remove();
                // appRouter();
            }
        } catch (error) {
            console.error(error)
        }
    }

    async function addDeviceRoom(room_id, device_id, device_name) {
        try {
            const response = await fetch('/add_new_device', {
                method: 'POST',
                headers: {
                    'auth': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(
                    { dev_id: device_id, name: device_name, room_id: room_id }
                )
            });
            if (!response.ok) {
                console.error(response.status);
                throw new Error(response.status);
            }
            else {
                const response_data = await response.json();
                if (response_data.success) {
                    loadHouses();
                    console.info(response_data.success);
                }
            }
        } catch (error) {

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
                if (response_data.success) {
                    console.info(response_data.success);
                    loadHouses();
                }
                else {
                    if (response_data.error) {
                        throw new Error(response_data.error)
                    }
                }
            }
        } catch (error) {
            console.error(error);
            appRouter();
        }
    }
}

appRouter();