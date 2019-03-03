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
                    $('button#generate').attr('disabled', true).css('cursor', 'not-allowed');
                },
                complete: function (data) {
                    if (data && data.status === 200) {
                        let bonuses = data.responseJSON['BONUSES'];
                        let gaps = data.responseJSON['GAPS'];
                        let completions = data.responseJSON['COMPLETION'];
                        let questionIndex = 1;
                        let test = `<h1>TEST</h1>`;
                        let answers = `<h1>ANSWERS</h1>`;
                        for (let gap of gaps) {
                            test += `<h4>${questionIndex}. ${gap[0]}</h4>`;
                            answers += `<h4>${questionIndex} - ${gap[1].join(', ')}</h4>`;
                            questionIndex++;
                        }

                        for (let completion of completions) {
                            test += `<h4>${questionIndex}. ${completion[0]}</h4>`;
                            for (let index in completion[1]) {
                                test += `<div>${index}. ${completion[1][index]}</div>`;
                            }
                            answers += `<h4>${questionIndex} - ${completion[2]}</h4>`;
                            questionIndex++;
                        }

                        if (bonuses) {
                            test += "<h1>BONUS QUESTINOS</h1>";
                        }

                        for (let bonus of bonuses) {
                            test += `<h4>${questionIndex}. ${bonus[1]}</h4>`;
                            answers += `<h4>${questionIndex} - ${bonus[0]}</h4>`;
                            questionIndex++;
                        }

                        exportPDF(test + answers);


                    } else if (data && data.status === 400) {
                        let error = data.responseJSON['ERROR'];
                        let errorHtml = $('div.form-group .error');
                        errorHtml.text("Error: " + error);
                        errorHtml.removeClass('hidden');
                    }

                    resetForm();
                    $('button#generate').attr('disabled', false).css('cursor', 'pointer');
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

function exportPDF(data) {
    let margins = {top: 20, bottom: 20, left: 20, right: 20, width: 110};
    let doc = new jsPDF();
    doc.fromHTML(data, 15, 15, margins);
    let splitTitle = doc.splitTextToSize(data, 180);
    doc.fromHTML(splitTitle);
    doc.save('test-generator-project.pdf');

}

function clearErrors() {
    $('form div.error').addClass('hidden');
    $('div.form-group .error').text('Error: At least one of the options above must be checked.');
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