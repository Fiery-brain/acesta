function typeMarkdown(initialText, element, speed = 50) {
  // Полный набор слов для неразрывных пробелов
  const NON_BREAK_WORDS = new Set([
    "в",
    "во",
    "на",
    "над",
    "под",
    "к",
    "ко",
    "от",
    "до",
    "по",
    "со",
    "из",
    "без",
    "у",
    "о",
    "об",
    "обо",
    "за",
    "про",
    "при",
    "с",
    "со",
    "для",
    "перед",
    "через",
    "сквозь",
    "между",
    "среди",
    "вокруг",
    "возле",
    "близ",
    "вдоль",
    "поперёк",
    "около",
    "подле",
    "вне",
    "внутри",
    "после",
    "до",
    "кроме",
    "бы",
    "же",
    "ли",
    "не",
    "ни",
    "то",
    "ведь",
    "мол",
    "де",
    "только",
    "лишь",
    "именно",
    "почти",
    "даже",
    "уж",
    "разве",
    "неужели",
    "что",
    "вот",
    "вон",
    "и",
    "а",
    "но",
    "или",
    "да",
    "то",
    "как",
    "чтобы",
    "что",
    "потому",
    "так как",
    "так что",
    "если",
    "хотя",
    "будто",
    "словно",
    "либо",
    "ни",
    "не только",
    "но и",
  ]);

  // Состояние процесса
  let currentProcess = {
    controller: new AbortController(),
    version: 0,
    text: initialText,
    scrollContainer: element.closest(".modal-body, .modal-content") || element,
  };

  async function runTyping(textToType, version, controller) {
    element.innerHTML = "";
    let i = 0;
    let visibleText = "";
    let tagStack = [];
    let state = {
      inList: false,
      headerLevel: 0,
      newLine: true,
      inCode: false,
      inLink: false,
      inTag: false,
      inBold: false,
      inItalic: false,
      lastChar: "",
    };

    const updateOutput = () => {
      element.innerHTML = visibleText + [...tagStack].reverse().join("");
      currentProcess.scrollContainer.scrollTo({
        top: currentProcess.scrollContainer.scrollHeight,
        behavior: "smooth",
      });
    };

    const shouldAddNbsp = (pos) => {
      // Пропускаем специальные контексты
      if (state.inCode || state.inTag || state.inLink) return false;

      // Находим начало текущего слова
      let wordStart = pos;
      while (wordStart > 0 && /[а-яёa-z-]/i.test(textToType[wordStart - 1])) {
        wordStart--;
      }

      // Получаем слово и контекст
      const word = textToType.substring(wordStart, pos + 1).toLowerCase();
      const nextChar = textToType[pos + 1];
      const prevChar = pos > 0 ? textToType[pos - 1] : "";
      const nextNextChar =
        pos + 2 < textToType.length ? textToType[pos + 2] : "";

      // Основные условия для неразрывного пробела
      if (NON_BREAK_WORDS.has(word) && nextChar === " ") {
        // Исключения:
        // 1. Слово является частью другого слова
        if (/[а-яёa-z0-9-]/i.test(prevChar)) return false;

        // 2. Перед закрывающей кавычкой/скобкой
        if (/^[\"\'»\)\]}]$/.test(nextNextChar)) return false;

        // 3. Между цифрами
        if (/^\d$/.test(prevChar) && /^\d$/.test(nextNextChar)) return false;

        // 4. Часть URL или специального синтаксиса
        if (/[:@#/\\]/.test(prevChar)) return false;

        // 5. После дефиса или тире
        if (/[-—]/.test(prevChar)) return false;

        // 6. Перед знаком препинания (кроме пробела)
        if (/^[,;:!?]/.test(nextNextChar)) return false;

        return true;
      }

      return false;
    };

    const processMarkdown = () => {
      const char = textToType[i];
      const nextChar = i + 1 < textToType.length ? textToType[i + 1] : "";

      // Заголовки
      if (char === "#" && state.newLine) {
        state.headerLevel = 1;
        while (
          i + state.headerLevel < textToType.length &&
          textToType[i + state.headerLevel] === "#"
        ) {
          state.headerLevel++;
        }
        if (textToType[i + state.headerLevel] === " ") {
          visibleText += `<h${state.headerLevel}>`;
          tagStack.push(`</h${state.headerLevel}>`);
          i += state.headerLevel + 1;
          state.newLine = false;
          return true;
        }
      }

      // Списки
      if (
        (char === "-" || char === "*" || char === "+") &&
        nextChar === " " &&
        state.newLine
      ) {
        visibleText += state.inList ? "</li><li>" : "<ul><li>";
        if (!state.inList) tagStack.push("</li></ul>");
        state.inList = true;
        i += 2;
        state.newLine = false;
        return true;
      }

      // Жирный текст
      if (char === "*" && nextChar === "*") {
        visibleText += state.inBold ? "</strong>" : "<strong>";
        state.inBold = !state.inBold;
        i += 2;
        return true;
      }

      // Курсив
      if ((char === "*" || char === "_") && !state.inBold) {
        //visibleText += state.inItalic ? "</em>" : "<em>";
        state.inItalic = !state.inItalic;
        i += 1;
        return true;
      }

      // Код
      if (char === "`") {
        if (nextChar === "`" && textToType[i + 2] === "`") {
          visibleText += tagStack.includes("</code></pre>")
            ? "</code></pre>"
            : "<pre><code>";
          if (!tagStack.includes("</code></pre>"))
            tagStack.push("</code></pre>");
          state.inCode = true;
          i += 3;
        } else {
          visibleText += tagStack.includes("</code>") ? "</code>" : "<code>";
          if (!tagStack.includes("</code>")) tagStack.push("</code>");
          state.inCode = !state.inCode;
          i += 1;
        }
        return true;
      }

      // Ссылки
      if (char === "[") {
        state.inLink = true;
      }
      if (char === "]" && nextChar === "(") {
        state.inLink = false;
      }

      return false;
    };

    try {
      while (i < textToType.length && currentProcess.version === version) {
        if (controller.signal.aborted) return;

        const char = textToType[i];
        const nextChar = i + 1 < textToType.length ? textToType[i + 1] : "";

        // Обработка HTML-тегов
        if (char === "<") {
          state.inTag = true;
          visibleText += char;
          i++;
          continue;
        }
        if (char === ">") {
          state.inTag = false;
          visibleText += char;
          i++;
          continue;
        }

        // Приоритетная обработка неразрывных пробелов
        if (
          !state.inCode &&
          !state.inTag &&
          char !== " " &&
          nextChar === " " &&
          shouldAddNbsp(i)
        ) {
          visibleText += char + "&nbsp;";
          i += 2;
          updateOutput();
          await delay(speed);
          continue;
        }

        // Обработка Markdown
        if (processMarkdown()) {
          updateOutput();
          await delay(speed);
          continue;
        }

        // Переносы строк
        if (char === "\n") {
          if (state.headerLevel > 0) {
            visibleText += `</h${state.headerLevel}>`;
            tagStack = tagStack.filter((t) => t !== `</h${state.headerLevel}>`);
            state.headerLevel = 0;
          }

          if (nextChar === "\n") {
            if (state.inList) {
              visibleText += "</li></ul>";
              tagStack = tagStack.filter((t) => t !== "</li></ul>");
              state.inList = false;
            }
            visibleText += "<p>";
            tagStack.push("</p>");
            i += 2;
          } else {
            visibleText += state.headerLevel === 0 ? "<br>" : "";
            i += 1;
          }

          state.newLine = true;
          updateOutput();
          await delay(speed);
          continue;
        }

        // Обычные символы
        visibleText += char;
        state.lastChar = char;
        state.newLine = false;
        i++;

        if (
          i % 3 === 0 ||
          char === " " ||
          char === "\n" ||
          char === "<" ||
          char === ">"
        ) {
          updateOutput();
          await delay(speed);
        }
      }

      // Закрываем все теги
      while (tagStack.length > 0) {
        visibleText += tagStack.pop();
        updateOutput();
        await delay(speed);
      }
    } catch (e) {
      if (e.message !== "Aborted") console.error(e);
    }
  }

  const delay = (ms) =>
    new Promise((resolve, reject) => {
      const timer = setTimeout(resolve, ms);
      currentProcess.controller.signal.addEventListener("abort", () => {
        clearTimeout(timer);
        reject(new Error("Aborted"));
      });
    });

  runTyping(initialText, currentProcess.version, currentProcess.controller);

  return {
    update(newText) {
      if (newText !== currentProcess.text) {
        currentProcess.controller.abort();
        currentProcess.version++;
        currentProcess.text = newText;
        currentProcess.controller = new AbortController();
        runTyping(newText, currentProcess.version, currentProcess.controller);
      }
    },
    stop() {
      currentProcess.controller.abort();
    },
  };
}

function copyWithFormatting(elementId) {
  const element = document.getElementById(elementId);

  // Создаем диапазон и выделение
  const range = document.createRange();
  range.selectNode(element);
  window.getSelection().removeAllRanges();
  window.getSelection().addRange(range);

  // Копируем с форматированием
  document.execCommand("copy");

  // Снимаем выделение
  window.getSelection().removeAllRanges();
}

$(function () {
  var recommendationsModal = document.getElementById("recommendations");

  var textElement = $("#recommendationsText");

  $("#copyRecommendations").click(function () {
    copyWithFormatting("recommendationsText");
  });

  let storage = window.sessionStorage;
  let markdownPrinter = null;

  recommendationsModal.addEventListener("show.bs.modal", function (e) {
    if (JSON.parse(storage.getItem("context-changed"))) {
      if (markdownPrinter) {
        markdownPrinter.stop();
        markdownPrinter = null;
      }
      textElement.empty();
    }
  })

  recommendationsModal.addEventListener("shown.bs.modal", function (e) {
    if (
      JSON.parse(storage.getItem("context-changed")) ||
      textElement.text().length == 0
    ) {
      $("#ai-loader").css("display", "block");
      $.ajax({
        url: recommendationsUrl,
        type: "POST",
        data: {
          csrfmiddlewaretoken: csrfToken,
          data: data,
        },

        success: function (data) {
          $("#ai-loader").css("display", "none");

          text = data.recommendations;
          markdownPrinter = typeMarkdown(text, textElement[0], 50);

          storage.setItem("context-changed", false);
        },

        error: function (xhr, status, error) {
          $("#ai-loader").css("display", "none");
          textElement.text(
            "Сервис перегружен, попробуйте повторить попытку чуть позже"
          );
        },
      });
    }
  });
})
