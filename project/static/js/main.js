loadFunctions();

function loadFunctions() {
    $(document).ready(function () {
        handleRangeInputs();
        handleTextAreaAppearance();
        handleFileUpload();
        handleFormSubmit();
        handleUndoButton();
        handleAjaxLoader();
        test();
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
        let undo = $('i#undo-selection');
        let interactiveSibling = $(e.target).parent().siblings('div.interactive');

        if (this.files && this.files.length > 0) {
            label.html("<i class=\"fas fa-upload\"></i>" + this.files[0].name);
            interactiveSibling.addClass("hidden");
            undo.removeClass('hidden');
            clearErrors();
        } else {
            label.html("<i class=\"fas fa-upload\"></i>Upload a file");
            interactiveSibling.removeClass("hidden");
        }
    })
}

function handleFormSubmit() {
    $('#generate').on('click', function (e) {
        let btn = $(e.target);
        let file = $('#file-upload')[0].files[0];
        let rawText = $('#raw-text').val();
        if (file) {
            clearErrors();
        } else if ($.trim(rawText).length) {
            clearErrors();
        } else {
            btn.siblings('.error').removeClass('hidden');
        }

        if ($('input[type=checkbox]:checked').length < 1) {
            $('div.error-checkbox').removeClass('hidden');
        } else {
            $('div.error-checkbox').addClass('hidden');
        }

        if ($('div.error:not(.hidden)').length === 0) {
            let form_data = new FormData($('form#test-generation-form')[0]);
            console.log(form_data);
            $.ajax({
                method: "POST",
                url: '/generate-test',
                data: form_data,
                contentType: false,
                cache: false,
                processData: false,
                success: function (data) {
                    console.log(data);
                }
            });
        }
    });
}

function handleUndoButton() {
    $('i#undo-selection').click(function (e) {
        $(e.target).addClass('hidden');
        $('input#file-upload').val('');
        $('div#file-upload-container label').html("<i class=\"fas fa-upload\"></i>Upload a file");
        $('div#raw-text-container').removeClass('hidden');
    });
}

function test() {
    $.get('/test', function (data) {
        let doc = new jsPDF();
        doc.fromHTML(data, 15, 15);
        doc.save('sample-file.pdf');
    });

}

function handleAjaxLoader() {
    $(document).ajaxStart(function () {
        $('div#loader').show();
    }).ajaxStop(function () {
        $('div#loader').hide();
    });
}

function clearErrors() {
    $('form div.error').addClass('hidden');
}