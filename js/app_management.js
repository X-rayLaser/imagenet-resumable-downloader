function updateControlsValues(stateData) {
    location.download_path = stateData.downloadPath;
    total_amount_id.value = parseInt(stateData.numberOfImages);
    images_per_category_spnibox.value = parseInt(stateData.imagesPerCategory);

    time_left_id.value = stateData.timeLeft;
    progress_info_box.imagesLoaded = stateData.imagesLoaded;
    progress_info_box.failures = stateData.failures;
    failed_urls_model.model = stateData.failedUrls;
    bar.value = parseFloat(stateData.progress);

    errors_id.text = String(stateData.errors);
}

function showInputElements() {
    location.visible = true;
    total_amount_id.visible = true;
    images_per_category_spnibox.visible = true;
    errors_id.visible = true;
}

function hideInputElements() {
    location.visible = false;
    total_amount_id.visible = false;
    images_per_category_spnibox.visible = false;
    errors_id.visible = false;
}

function showProgress() {
    bar.visible = true;
    time_left_id.visible = true;
    progress_info_box.visible = true;
}

function hideProgress() {
    bar.visible = false;
    time_left_id.visible = false;
    progress_info_box.visible = false;
}

function InitialState() {
    this.updateUI = function(stateData) {
        download_button.enabled = false;
        download_button.visible = true;

        toggle_button.visible = false;
        toggle_button.enabled = false;
        toggle_button.text = "Pause";

        reset_button.enabled = false;
        reset_button.visible = false;

        showInputElements();

        hideProgress();
        complete_label.toastVisible = false;
    };

    return this;
}

function ReadyState() {
    this.updateUI = function(stateData) {
        download_button.enabled = true;
        download_button.visible = true;

        toggle_button.visible = false;
        toggle_button.enabled = false;
        toggle_button.text = "Pause";

        reset_button.enabled = false;
        reset_button.visible = false;

        showInputElements();

        hideProgress();
        complete_label.toastVisible = false;
    };

    return this;
}

function PausingInProgressState() {
    this.updateUI = function(stateData) {
        download_button.enabled = false;
        download_button.visible = false;
        toggle_button.visible = true;
        toggle_button.enabled = true;
        toggle_button.text = "Pausing";

        reset_button.enabled = false;
        reset_button.visible = false;

        complete_label.toastVisible = false;
        hideInputElements();
        showProgress();
    }
    return this;
}

function ResumingInProgressState() {
    this.updateUI = function(stateData) {
        download_button.enabled = false;
        download_button.visible = false;
        toggle_button.visible = true;
        toggle_button.enabled = true;
        toggle_button.text = "Resuming";

        reset_button.enabled = false;
        reset_button.visible = false;

        complete_label.toastVisible = false;
        hideInputElements();
        showProgress();
    }
    return this;
}

function RunningState() {
    this.updateUI = function(stateData) {
        download_button.enabled = false;
        download_button.visible = false;
        toggle_button.visible = true;
        toggle_button.enabled = true;
        toggle_button.text = "Pause";

        reset_button.enabled = false;
        reset_button.visible = false;

        complete_label.toastVisible = false;
        hideInputElements();
        showProgress();
    }

    return this;
}

function PausedState() {
    this.updateUI = function(stateData) {
        download_button.enabled = false;
        download_button.visible = false;
        toggle_button.visible = true;
        toggle_button.enabled = true;
        toggle_button.text = "Resume";

        reset_button.enabled = true;
        reset_button.visible = true;

        complete_label.toastVisible = false;
        hideInputElements();
        showProgress();
    }

    return this;
}

function FinishedState() {
    this.updateUI = function(stateData) {
        download_button.enabled = false;
        download_button.visible = false;
        toggle_button.visible = false;
        toggle_button.enabled = false;
        toggle_button.text = "Pause";

        reset_button.enabled = true;
        reset_button.visible = true;

        complete_label.toastVisible = true;
        bar.visible = false;

        time_left_id.visible = false;
        errors_id.visible = false;
        hideInputElements();
    }

    return this;
}

function DownloadStateManager() {
    this.state = new ReadyState();

    this.setState = function(state) {
        switch(state) {
            case "initial":
                this.state = new InitialState();
            case "ready":
                this.state = new ReadyState();
                break;
            case "running":
                this.state = new RunningState();
                break;
            case "pausing":
                this.state = new PausingInProgressState();
                break;
            case "paused":
                this.state = new PausedState();
                break;
            case "resuming":
                this.state = new ResumingInProgressState();
                break;
            case "finished":
                this.state = new FinishedState();
                break;
            default:
                throw "Unknown state " + state;
        }
    };
    this.updateUI = function(stateData) {
        this.state.updateUI(stateData);
        updateControlsValues(stateData);
    }
    return this;
}


var stateManager = new DownloadStateManager();
