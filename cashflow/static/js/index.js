const form = document.getElementById("registrationForm");
const userError = document.getElementById("usernameError");
const passError = document.getElementById("passwordError");
const amountError = document.getElementById("amountError");
const descriptionError = document.getElementById("descriptionError");
const form2 = document.getElementById("error");
form2.addEventListener("submit", (event) => {
  let hasError = false;
  userError.textContent = "";
  passError.textContent = "";

  amountError.textContent = "";
  descriptionError.textContent = "";

  const amount = document.querySelector(".amount").value;
  const description = document.querySelector(".description").value;

  if (!amount) {
    amountError.textContent = "این فیلد الزامی است";
    hasError = true;
  }
  if (!description) {
    amountError.textContent = "این فیلد الزامی است";
    hasError = true;
  }

  // اگر خطایی وجود دارد، ارسال فرم متوقف می‌شود
  if (hasError) {
    event.preventDefault();
  }
});

form.addEventListener("submit", (event) => {
  let hasError = false;
  userError.textContent = "";
  passError.textContent = "";

  amountError.textContent = "";
  descriptionError.textContent = "";

  const username = document.querySelector(".username").value;
  const password = document.querySelector(".password").value;
  const amount = document.querySelector(".amount").value;
  const description = document.querySelector(".description").value;

  // بررسی نام کاربری
  if (!username) {
    userError.textContent = "این فیلد الزامی است";
    hasError = true;
  } else if (username.length < 3) {
    userError.textContent = "تعداد کاراکترها باید از 3 تا بیشتر باشد";
    hasError = true;
  }
  if (!amount) {
    amountError.textContent = "این فیلد الزامی است";
    hasError = true;
  }
  if (!description) {
    amountError.textContent = "این فیلد الزامی است";
    hasError = true;
  }

  // بررسی رمز عبور
  if (!password) {
    passError.textContent = "این فیلد الزامی است";
    hasError = true;
  } else if (password.length < 6) {
    passError.textContent = "تعداد کاراکترها باید از 6 تا بیشتر باشد";
    hasError = true;
  }

  // اگر خطایی وجود دارد، ارسال فرم متوقف می‌شود
  if (hasError) {
    event.preventDefault();
  }
});

// پنهان کردن پیام خطا با تایپ
const usernameInput = document.querySelector(".username");
const passwordInput = document.querySelector(".password");
const amountInput = document.querySelector(".amount");
const descriptonInput = document.querySelector(".description");
const value1 = document.querySelector(".value1");

usernameInput.addEventListener("input", () => {
  userError.textContent = ""; // پنهان کردن پیام خطا
});

passwordInput.addEventListener("input", () => {
  passError.textContent = ""; // پنهان کردن پیام خطا
});

amountInput.addEventListener("input", () => {
  amountError.textContent = ""; // پنهان کردن پیام خطا
});

descriptonInput.addEventListener("input", () => {
  descriptionError.textContent = ""; // پنهان کردن پیام خطا
});

value1.addEventListener("input", () => {
  passError.textContent = ""; // پنهان کردن پیام خطا
});

// const icon = document.querySelector(".icon");
// const input = document.querySelector(".input");

// icon.addEventListener("click", () => {
//   if (icon.textContent === "visibility") {
//     icon.textContent = "visibility_off";
//     input.type = "text";
//   } else {
//     icon.textContent = "visibility";
//     input.type = "password";
//   }
// });
