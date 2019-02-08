loadFunctions();

function loadFunctions() {
    $(document).ready(function () {
        handleRangeInputs();
        handleTextAreaAppearance();
    });
}


function handleRangeInputs() {
    $('input[type=range]').on("input", function (e) {
        let slider = $(e.target);
        let spans = slider.siblings(".range-number:not(.readonly)");
        for (let index = 0; index < spans.length; index++) {
            if (index === 0 && spans.length === 1) {
                let span = $(spans[0]);
                span.text(parseInt(slider.val()));
            }
            if (index === 0 && spans.length > 1) {
                let span = $(spans[0]);
                span.text(100 - parseInt(slider.val()));
            } else if (index === 1) {
                let span = $(spans[1]);
                span.text(parseInt(slider.val()));
            }
        }
    })
}

function handleTextAreaAppearance() {
    $('div.interactive label[for="raw-text"]').on('click', function (e) {
        let textarea = $(e.target).siblings('textarea');
        if(textarea.hasClass("hidden")) {
            textarea.removeClass("hidden");
        } else {
            textarea.addClass("hidden");
        }
    })
}
