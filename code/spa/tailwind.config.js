/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/webserver/templates/*.html", 
    "./app/webserver/templates/components/*.html",
    "./app/webserver/static/js/*.js"
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}

