document.addEventListener("DOMContentLoaded", () => {
    const userData = JSON.parse(localStorage.getItem("chat_user") || "null");

    // Если пользователь не авторизован — перенаправляем на логин
    if (!userData || !userData.uuid || !userData.username) {
        window.location.href = "/login";
        return;
    }

    const socket = io({
        auth: { uuid: userData.uuid, username: userData.username }
    });

    const chatBox = document.getElementById("chat-box");
    const messageInput = document.getElementById("message-input");
    const sendBtn = document.getElementById("send-btn");
    const groupList = document.getElementById("group-list");
    const currentGroupName = document.getElementById("current-group-name");
    const newGroupBtn = document.getElementById("new-group-btn");

    let currentGroupId = null;

    // === Подключение ===
    socket.on("connect", () => {
        console.log("✅ Connected to chat server");
        socket.emit("user_connected", {
            uuid: userData.uuid,
            username: userData.username
        });
    });

    socket.on("disconnect", () => {
        console.log("⚠️ Disconnected from server");
    });

    // === Обработка новых сообщений ===
    socket.on("new_message", (msg) => {
        appendMessage(msg);
    });

    // === Обновление списка групп ===
    socket.on("group_list", (groups) => {
        updateGroupList(groups);
    });

    // === Обновление при добавлении новой группы ===
    socket.on("group_created", (group) => {
        addGroupToList(group);
    });

    // === Создание новой группы ===
    newGroupBtn?.addEventListener("click", () => {
        const name = prompt("Введите название новой группы:");
        if (!name) return;
        socket.emit("create_group", { name });
    });

    // === Отправка сообщений ===
    sendBtn?.addEventListener("click", () => sendMessage());
    messageInput?.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendMessage();
    });

    function sendMessage() {
        const text = messageInput.value.trim();
        if (!text || !currentGroupId) return;

        const msg = {
            group_id: currentGroupId,
            text: text,
            sender: userData.username,
            uuid: userData.uuid,
            timestamp: new Date().toISOString()
        };

        socket.emit("send_message", msg);
        messageInput.value = "";
        appendMessage(msg, true);
    }

    function appendMessage(msg, isOwn = false) {
        const msgEl = document.createElement("div");
        msgEl.classList.add("message");
        if (isOwn) msgEl.classList.add("own");

        const time = new Date(msg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

        msgEl.innerHTML = `
            <div class="message-header">
                <span class="message-user">${msg.sender}</span>
                <span class="message-time">${time}</span>
            </div>
            <div class="message-body">${msg.text}</div>
        `;

        chatBox.appendChild(msgEl);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function updateGroupList(groups) {
        groupList.innerHTML = "";
        groups.forEach(group => addGroupToList(group));
    }

    function addGroupToList(group) {
        const li = document.createElement("li");
        li.classList.add("group-item");
        li.textContent = group.name;
        li.dataset.groupId = group.id;

        li.addEventListener("click", () => {
            currentGroupId = group.id;
            currentGroupName.textContent = group.name;
            socket.emit("join_group", { group_id: group.id });
            chatBox.innerHTML = "";
        });

        groupList.appendChild(li);
    }

    // === Выход из аккаунта ===
    const logoutBtn = document.getElementById("logout-btn");
    logoutBtn?.addEventListener("click", () => {
        localStorage.removeItem("chat_user");
        socket.disconnect();
        window.location.href = "/login";
    });
});
