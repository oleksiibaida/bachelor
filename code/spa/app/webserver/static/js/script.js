const app = document.getElementById('app')

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

async function renderPage(page, data = null) {
    switch (page) {
        case "main":
            renderMainPage(data);
        case "settings":
            renderSettingsPage(data);
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
    <div class="form-container">
        <h2>SIGN UP</h2>
        <form id="signUpForm">
            <label for="username">Username:</label>
            <input type="text" id="username" name="username" required><br>
        
            <label for="email">Email:</label>
            <input type="email" id="email" name="email" required><br>
        
            <label for="password">Password:</label>
            <input type="password" id="password" name="password" required><br>
        
            <button type="submit" class="font-bold">Sign Up</button>
        </form>
    </div>
    `

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
            if (!response.ok) {
                console.error(response.status)
                renderPage('login')
            }
            const response_data = await response.json();
            if (response_data['auth'] && response_data['token']) {
                localStorage.setItem('token', response_data['token']);
                appRouter();
            } else {
                alert('LOGIN FAILED');
                renderPage('login');
                return;
            }
        } catch (error) {
            console.error(error);
        }
    });
}

function renderLoginForm() {
    app.innerHTML = `
    <div class="form-container">
        <h2>LOGIN</h2>
        <form id="loginForm">
            <label for="username">Username</label>
            <input type="text" id="username" name="username"><br>
            <label for="password">Password</label>
            <input type="password" id="password" name="password"><br>
            <button type="submit" class="login-btn">LOGIN</button>
        </form>
        <div class="label_register">
            <button id="BTNsignup">SignUp here</button>
        </div>
    </div>
    `;

    document.getElementById('BTNsignup').addEventListener('click', (event) => {
        renderSignUpPage();
    }),

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
                if (!response.ok) {
                    if (response.status === 401) {
                        alert("Invalid username or password");
                    } else {
                        alert(`LOGIN FAIL STATUS: ${response.status}`);
                    }
                    return;
                }
                const response_data = await response.json();
                if (response_data['auth'] && response_data['token']) {
                    localStorage.setItem('token', response_data['token']);
                    // renderPage('main');
                    // renderMainPage();
                    appRouter();
                } else {
                    alert('LOGIN FAILED');
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
        <div>
            <h1>Hello, ${data.username}</h1>
            <button id="BTNcreateHouse" type="button"
                class="create_house-btn">Create New House</button>
            <div id="MNcreateHouse" class="hidden relative bg-white shadow-md rounded-md mt-2 w-64">
                <div class="p-4">
                    <label for="houseName" class="block text-gray-700 text-sm font-bold mb-2">House Name:</label>
                    <input type="text" id="houseName" value="House 1"
                        class="w-full border border-gray-300 rounded px-3 py-2 mb-2 focus:outline-none focus:ring-2 focus:ring-blue-500">

                    <label for="roomName" class="block text-gray-700 text-sm font-bold mb-2">Room Name:</label>
                    <input type="text" id="roomName"
                        class="w-full border border-gray-300 rounded px-3 py-2 mb-2 focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <div class="flex space-x-2">
                        <button id="BTNaddHouse"
                            class="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded">Save</button>
                        <button id="BTNcloseHouseMN"
                            class="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded">Close</button>
                    </div>
                </div>
            </div>
            <div class="hidden"><p>FIND ME</p></div>
            <div id="houseList" class="houseList"></div>
        </div>
    `;

    await loadHouses();
    var BTNcreateHouse = document.getElementById("BTNcreateHouse");
    var MNcreateHouse = document.getElementById("MNcreateHouse");
    // MNcreateHouse.style.display = "none";
    var BTNaddHouse = document.getElementById("BTNaddHouse");
    var BTNcloseHouseMN = document.getElementById("BTNcloseHouseMN")

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
            }
        } catch (error) {
            console.error(error);
        } finally {
            closeHouseForm();
            appRouter();
        }
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
            console.info(response_data)
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
                const house = house_list[i];
                const house_element = document.createElement('div');
                house_element.classList.add('house_element');
                house_element.innerHTML = `<h4>${house.name}</h4>`;
                parent_div.appendChild(house_element);
            }
        }
    }
}

function renderSettingsPage() {

}

appRouter();