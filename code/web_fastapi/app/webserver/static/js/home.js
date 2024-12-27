var BTNcreateHouse = document.getElementById("BTNcreateHouse");
var MNcreateHouse = document.getElementById("MNcreateHouse");

BTNcreateHouse.addEventListener("click", () => {
    MNcreateHouse.classList.toggle("hidden");
    BTNcreateHouse.classList.add("hidden");
});

document.addEventListener("click", (event) => {
    if (!BTNcreateHouse.contains(event.target) && !MNcreateHouse.contains(event.target)) {
        MNcreateHouse.classList.add("hidden");
        BTNcreateHouse.classList.remove("hidden");
    }
})

function closeHouseForm() {
    MNcreateHouse.classList.add("hidden");
    BTNcreateHouse.classList.remove("hidden");
}

async function addHouse() {
    const houseName = document.getElementById("houseName").value;
    const userId = document.getElementById("userdata").dataset.userId;
    try {
        const response = await fetch(
            '/addHouse',
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ userId, houseName })
            }
        );

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error);
        }
        const data = await response.json();
    } catch (error) {
        console.error(error);
    } finally {
        closeHouseForm();
    }
}