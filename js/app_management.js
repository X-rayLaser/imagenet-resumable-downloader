function ReadyState() {
    this.updateUI = function() {
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
    this.updateUI = function() {
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
    this.updateUI = function() {
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
    this.updateUI = function() {
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
    this.updateUI = function() {
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
    this.updateUI = function() {
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
        }
    };
    this.updateUI = function() {
        this.state.updateUI();
    }
    return this;
}
