loadFunctions();

const fileUploadLabel = "<i class=\"fas fa-upload\"></i>Upload a file";

function loadFunctions() {


    $(document).ready(function () {
        handleRangeInputs();
        handleTextAreaAppearance();
        handleFileUpload();
        handleFormSubmit();
        handleUndoButton();
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
            $.ajax({
                method: "POST",
                url: '/generate-test',
                data: form_data,
                contentType: false,
                cache: false,
                processData: false,
                beforeSend: function () {
                    $('div#loader').show();
                },
                complete: function (data) {
                    console.log(data);
                    resetForm();
                }
            });
        }
    });
}

function handleUndoButton() {
    $('i#undo-selection').click(function (e) {
        $(e.target).addClass('hidden');
        $('input#file-upload').val('');
        $('div#file-upload-container label').html(fileUploadLabel);
        $('div#raw-text-container').removeClass('hidden');
    });
}

function exportPDF() {
    let doc = new jsPDF();
    doc.fromHTML(data, 15, 15);
    doc.save('sample-file.pdf');
}

function clearErrors() {
    $('form div.error').addClass('hidden');
}

function resetForm() {
    $('div#loader').hide();
    $('form#test-generation-form')[0].reset();
    $('div#file-upload-container').removeClass("hidden");
    $('div#raw-text-container').removeClass("hidden");
    $('i#undo-selection').addClass('hidden');
    $('div.border-container').addClass('hidden');
    $('div#file-upload-container label').html(fileUploadLabel);
    let sizeSpan = $('span.range-number');
    sizeSpan.text(sizeSpan.siblings('input').val() + "%")
}