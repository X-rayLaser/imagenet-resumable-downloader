function updateControlsValues(stateData) {
    location.download_path = stateData.downloadPath;
    total_amount_id.value = parseInt(stateData.numberOfImages);
    images_per_category_spnibox.value = parseInt(stateData.imagesPerCategory);

    progress_info_box.timeLeft = stateData.timeLeft;
    progress_info_box.imagesLoaded = stateData.imagesLoaded;
    progress_info_box.failures = stateData.failures;
    failed_urls_model.model = stateData.failedUrls;
    bar.value = parseFloat(stateData.progress);
}

function InitialState() {
    this.updateUI = function(stateData) {
        download_button.enabled = false;
        download_button.visible = true;
        toggle_button.visible = false;
        toggle_button.enabled = false;
        toggle_button.text = "Pause";

        bar.visible = false;
        complete_label.toastVisible = false;
        progress_info_box.visible = false;
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

        bar.visible = false;
        complete_label.toastVisible = false;
        progress_info_box.visible = false;
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

        complete_label.toastVisible = false;
        progress_info_box.visible = true;
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

        complete_label.toastVisible = false;
        progress_info_box.visible = true;
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

        complete_label.toastVisible = false;
        progress_info_box.visible = true;
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

        complete_label.toastVisible = false;
        progress_info_box.visible = true;
    }

    return this;
}

function FinishedState() {
    this.updateUI = function(stateData) {
        download_button.enabled = true;
        download_button.visible = true;
        toggle_button.visible = false;
        toggle_button.enabled = false;
        toggle_button.text = "Pause";

        complete_label.toastVisible = true;
        progress_info_box.visible = true;
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
