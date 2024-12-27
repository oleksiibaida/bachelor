document.getElementById("loginForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
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

        const data = await response.json();
        if (data['token']) {
            // document.cookie = `session_id=${data.session_id}; path=/`;
            localStorage.setItem("token", data['token']);
            window.location.href = '/home'
        } else {
            alert("LOGIN SERVER ERROR");
        }
    } catch (error) {
        console.error(error);
        alert("LOGIN FAIL");
    }
});

async function fetch_with_token(url, options={}) {
    const token = localStorage.getItem('token');
    if(!token){
        window.location.href = '/';
        return;
    }

    const headers = {
        ...options.headers,
        Authorization: `Bearer ${token}`
    }

    const response = await fetch(url, {...options, headers});
    if (!response.ok) {
        if (response.status === 401) {
            localStorage.removeItem('token');
            alert('Your session has expired. Please log in again.');
            window.location.href = '/';
        } else {
            const errorData = await response.json();
            alert(`Request failed: ${errorData.detail || response.statusText}`);
        }
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    console.info(response)
    return response;
}