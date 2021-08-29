function Login() {
  fetch(
    `https://frozen-beyond-41947.herokuapp.com/user/${
      document.getElementById("logUsername").value
    }`
  )
    .then((res) => res.json())
    .then((data) => {
      console.log(data);
    });
}

function getToken() {
  fetch(`https://frozen-beyond-41947.herokuapp.com/auth`, {
    method: "post",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      username: document.getElementById("logUsername").value,
      password: document.getElementById("logPassword").value,
    }),
  })
    .then((res) => res.json())
    .then((data) => {
      console.log(data);
      if (data) {
        Login();
      }
    });
}

document.getElementById("loginForm").addEventListener("submit", (e) => {
  e.preventDefault();
  getToken();
});

function register() {
  console.log(
    document.getElementById("registerFirstName").value,
    document.getElementById("registerLastName").value,
    document.getElementById("registerEmail").value,
    document.getElementById("registerUsername").value,
    document.getElementById("registerPassword").value
  );
  fetch(`https://frozen-beyond-41947.herokuapp.com/user/`, {
    method: "post",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      first_name: document.getElementById("registerFirstName").value,
      last_name: document.getElementById("registerLastName").value,
      email: document.getElementById("registerEmail").value,
      username: document.getElementById("registerUsername").value,
      password: document.getElementById("registerPassword").value,
    }),
  })
    .then((res) => res.json())
    .then((data) => {
      console.log(data);
    });
}

document.getElementById("registerForm").addEventListener("submit", (e) => {
  e.preventDefault();
  register();
});
