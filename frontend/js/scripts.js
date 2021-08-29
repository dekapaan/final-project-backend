function Login() {
  fetch(
    `https://frozen-beyond-41947.herokuapp.com/user/${
      document.getElementById("logUsername").value
    }`
  )
    .then((res) => res.json())
    .then((data) => {
      console.log(data);
      if (data) {
        getToken();
      }
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
    });
}

document.getElementById("loginForm").addEventListener("submit", (e) => {
  e.preventDefault();
  Login();
});
