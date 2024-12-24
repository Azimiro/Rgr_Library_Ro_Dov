function sendRequest(endpoint) {
    fetch(endpoint)
        .then(response => response.json().then(data => ({ status: response.status, body: data })))
        .then(({ status, body }) => {
            const type = status === 200 ? 'success' : 'error';
            showPopup(body.message, type);
        })
        .catch(err => {
            showPopup('Something went wrong!', 'error');
        });
}

function showPopup(message, type) {
    const popup = document.createElement('div');
    popup.className = `popup ${type}`;
    popup.innerHTML = `<span>${message}</span>`;

    document.body.appendChild(popup);

    setTimeout(() => {
        popup.remove();
    }, 5000); // 5 seconds
}
