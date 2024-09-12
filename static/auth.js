document.addEventListener('DOMContentLoaded', function(event) {
    const words = [
      "Wealth building",
      "Digital currency",
      "Financial literacy",
      "Portfolio growth",
      "Market simulation",
      "Risk-free trading",
      "Financial freedom",
      "Virtual investing",
      "Smart trading",
      "Crypto education",
      "Trading skills",
      "Investment wisdom"
    ]

    text = document.querySelector(".animationText");

    function* wordGen()
    {
      var position = 0;
      while (true)
      {
        yield position++;
        if (position >= words.length)
        {
          position = 0;
        }
      }
    }

    function printCharacter(word)
    {
      let i = 0;
      text.innerHTML = "";
      let id = setInterval(() => {
        if (i < word.length) {
          text.innerHTML += word[i];
          i++;
        } else {
          clearInterval(id);
          setTimeout(deleteCharacter, 1000);
        }
      }, 250);
    }

    function deleteCharacter() {
      let word = text.innerHTML;
      let l = word.length - 1;
      let i_d = setInterval(() => {
        if (l >= 0) {
          text.innerHTML = text.innerHTML.substring(0, l);
          l--;
        } else {
          clearInterval(i_d);
          printCharacter(words[wordGenObj.next().value]);
        }
      }, 150);
    }

    let wordGenObj = wordGen();
    printCharacter(words[wordGenObj.next().value]);
  });
