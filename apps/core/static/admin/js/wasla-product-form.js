document.addEventListener("DOMContentLoaded", () => {
    const mobileQuery = window.matchMedia(
        "(max-width: 640px)"
    );

    const tabs = Array.from(
        document.querySelectorAll("[data-language-tab]")
    );

    const panels = Array.from(
        document.querySelectorAll("[data-language-panel]")
    );

    const activateLanguage = (language) => {
        tabs.forEach((tab) => {
            const isActive =
                tab.dataset.languageTab === language;

            tab.classList.toggle(
                "is-active",
                isActive
            );

            tab.setAttribute(
                "aria-selected",
                String(isActive)
            );
        });

        panels.forEach((panel) => {
            const isActive =
                panel.dataset.languagePanel === language;

            panel.classList.toggle(
                "is-active",
                isActive
            );
        });
    };

    tabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            activateLanguage(
                tab.dataset.languageTab
            );
        });
    });

    const selectInitialLanguage = () => {
        if (!mobileQuery.matches) {
            panels.forEach((panel) => {
                panel.classList.add("is-active");
            });

            return;
        }

        const panelWithError = panels.find((panel) => {
            return panel.querySelector(".has-errors");
        });

        const initialLanguage =
            panelWithError?.dataset.languagePanel || "en";

        activateLanguage(initialLanguage);
    };

    selectInitialLanguage();

    mobileQuery.addEventListener(
        "change",
        selectInitialLanguage
    );

    document
        .querySelectorAll("[data-counter-for]")
        .forEach((counter) => {
            const input = document.getElementById(
                counter.dataset.counterFor
            );

            const maximum = Number(
                counter.dataset.counterMax
            );

            if (!input || !maximum) {
                return;
            }

            const updateCounter = () => {
                const currentLength = input.value.length;

                counter.textContent =
                    `${currentLength} / ${maximum}`;

                counter.classList.toggle(
                    "is-near-limit",
                    currentLength >= maximum * 0.9
                );
            };

            input.addEventListener(
                "input",
                updateCounter
            );

            updateCounter();
        });
});