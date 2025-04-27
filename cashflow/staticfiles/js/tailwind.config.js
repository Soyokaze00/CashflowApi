/** @type {import('tailwindcss').Config} */
module.exports = {
    content: ["./**/*.html"],
    theme: {
      extend: {
        fontFamily: {
          lemon: ['lemon'], 
          error:["error"],
          title:["title"],
          Material:["Material Symbols Outlined"]


        },
        colors: {
          clifford: '#da373d',
          Yellow: "#FBE39D",
          YellowText: "#F9D876",
          Orange: "#F2C84A",
          color3:"rgb(191 161 122 / 61%)"

      },
      animation: {
        'spin-slow': 'spin 3s linear infinite',
        wiggle: 'wiggle 1s ease-in-out ',
        moving:"moving 1s linear infinite",
        moving2:"moving 3s linear ",
        linear:"linear 1s linear ",
        flipInY:"flipInY 3s "

      },
      keyframes: {
         flipInY :{
          '0%': {
          webkitTransform: "perspective(400px) rotate3d(0, 1, 0, 90deg)",
          transform: 'perspective(400px) rotate3d(0, 1, 0, 90deg)',
          webkitTransitionTimingFunction: 'ease-in',
          transitionTimingFunction: 'ease-in',
          opacity: '0'
          },
          '40%':{
          webkitTransform: "perspective(400px) rotate3d(0, 1, 0, -20deg)",
          transform: 'perspective(400px) rotate3d(0, 1, 0, -20deg)',
          webkitTransitionTimingFunction: 'ease-in',
          transitionTimingFunction:' ease-in'
          },
          "60%":{
          webkitTransform: "perspective(400px) rotate3d(0, 1, 0, 10deg)",
          transform: 'perspective(400px) rotate3d(0, 1, 0, 10deg)',
          opacity:' 1'
          },
          '80%': {
          webkitTransform: 'perspective(400px) rotate3d(0, 1, 0, -5deg)',
          transform: 'perspective(400px) rotate3d(0, 1, 0, -5deg)'
          },
          '100%':{
          webkitTransform: 'perspective(400px)',
          transform:' perspective(400px)'
          }
          } 
        ,
        wiggle: {
          '0%, 100%': { transform: 'rotate(-3deg)' },
          '50%': { transform: 'rotate(3deg)' },
        },
        moving:{
          "0%":{transform: 'translateY(0)'},
          "50%":{transform: 'translateY(-30px)'},
          "100%":{transform: 'translateY(0)'},

        },
        linear:{
           "0%":{
            opacity: "0",
            webkiTtransform:" translateY(20px)",
            transform: "translateY(20px)",
          },
        
          "100%":{
            opacity: '1',
            webkitTransform: 'translateY(0)',
            transform: 'translateY(0)',
          }
        }
      }
      },
    },
    plugins: [],
  };
  