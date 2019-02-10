loadFunctions();

function loadFunctions() {
    $(document).ready(function () {
        handleRangeInputs();
        handleTextAreaAppearance();
        handleFileUpload();
        handleFormSubmit();
    });
}


function handleRangeInputs() {
    $('input[type=range]').on("input", function (e) {
        let slider = $(e.target);
        let spans = slider.siblings(".range-number:not(.readonly)");
        for (let index = 0; index < spans.length; index++) {
            if (index === 0 && spans.length === 1) {
                let span = $(spans[0]);
                span.text(parseInt(slider.val()) + "%");
            }
            if (index === 0 && spans.length > 1) {
                let span = $(spans[0]);
                span.text(100 - parseInt(slider.val()) + "%");
            } else if (index === 1) {
                let span = $(spans[1]);
                span.text(parseInt(slider.val()) + "%");
            }
        }
    })
}

function handleTextAreaAppearance() {
    $('div.interactive label[for="raw-text"]').on('click', function (e) {
        let item = $(e.target).siblings('div');
        let interactiveSibling = $(e.target).parent().siblings('div.interactive');
        if (item.hasClass("hidden")) {
            item.removeClass("hidden");
            interactiveSibling.addClass("hidden");
        } else {
            item.addClass("hidden");
            interactiveSibling.removeClass("hidden");
        }
    })
}

function handleFileUpload() {
    $('#file-upload').on('change', function (e) {
        let label = $(e.target).siblings('label');
        let interactiveSibling = $(e.target).parent().siblings('div.interactive');

        if (this.files && this.files.length > 0) {
            label.html("<i class=\"fas fa-upload\"></i>" + this.files[0].name);
            interactiveSibling.addClass("hidden");
        } else {
            label.html("<i class=\"fas fa-upload\"></i>Upload a file");
            interactiveSibling.removeClass("hidden");
        }
    })
}

function handleFormSubmit() {
    $('#generate').on('click', function (e) {
        let btn = $(e.target);
        console.log(this.files);
    })
}