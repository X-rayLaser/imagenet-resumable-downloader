import QtQuick 2.5
import QtQuick.Window 2.0
import QtQuick.Controls 2.2
import QtQuick.Dialogs 1.0
import "../js/app_management.js" as AppManagement


Window {
    id: root
    x: 400
    y: 400
    width: 600
    height: 650
    visible: true

    property string download_state: "ready"
    property int images_loaded: 0
    property int images_total: 10
    property int failures: 0
    property bool download_completed: true

    Column {
        spacing: 10
        width: parent.width * 90 / 100
        anchors.horizontalCenter: parent.horizontalCenter

        DestinationLocation {
            id: location
            width: parent.width
            height: 50
        }

        QuantityInput {
            id: total_amount_id
            from: 1
            to: 100000
            value: 90
            labelText: "# of images to download"
        }

        QuantityInput {
            id: images_per_category_spnibox
            from: 1
            to: 100000
            value: 100
            labelText: "# of images per category"
        }

        Row {
            spacing: 15
            width: parent.width
            ProgressBar {
                id: bar
                width: parent.width
                value: images_loaded / images_total
            }
        }

        Row {
            anchors.horizontalCenter: parent.horizontalCenter

            Button {
                id: download_button
                text: "Download"
                width: 300;
                onClicked: startDownload()
            }

            Button {
                id: toggle_button
                text: "Pause"
                width: 300;
                onClicked: togglePause()
                visible: false
            }
        }

        StatusBox {
            id: progress_info_box
            width: parent.width
            visible: false
        }

        ScrollView {
            width: parent.width
            height: 150

            ListView {
                id: failed_urls_model
                model: []
                delegate: ItemDelegate {
                    text: modelData
                }
            }
        }

        Toast {
            id: complete_label
            toastVisible: false
        }
    }

    Connections {
        target: downloader
        onImageLoaded: handleImagesDownloaded()
        onDownloadFailed: handleDownloadFailed(failures, failed_urls)
        onDownloadPaused: handlePaused()
        onDownloadResumed: handleResumed()
    }

    function handleImagesDownloaded() {
        root.images_loaded += 1;
        time_left.text = downloader.time_remaining;
        if (root.images_loaded === root.images_total) {
            download_button.enabled = true;
            download_button.visible = true;
            complete_label.toastVisible = true;
            toggle_button.visible = false;
        }
    }

    function handleDownloadFailed(failures, failed_urls) {
        root.failures += failures;
        failed_urls_model.model = failed_urls;
    }

    function initializeState() {
        root.images_loaded = 0;
        root.failures = 0;
        root.images_total = amount_spnibox.value;
        root.download_state = "ready"
    }

    function updateUI() {
        var stateString = root.download_state;
        var stateManager = new AppManagement.DownloadStateManager();
        stateManager.setState(stateString);
        stateManager.updateUI();
    }

    function startDownload() {
        downloader.start_download(location.download_path,
                amount_spnibox.value,
                images_per_category_spnibox.value
        );

        initializeState();
        root.download_state = "running";
        updateUI();
    }

    function togglePause() {
        var stateManager = new AppManagement.DownloadStateManager();

        if (toggle_button.text === "Pause") {
            stateManager.setState("pausing");
            downloader.pause();
        } else {
            stateManager.setState("resuming");
            downloader.resume();
        }

        stateManager.updateUI();
    }

    function handlePaused() {
        var stateManager = new AppManagement.DownloadStateManager();
        stateManager.setState("resuming");
        stateManager.updateUI();
    }

    function handleResumed() {
        var stateManager = new AppManagement.DownloadStateManager();
        stateManager.setState("resumed");
        stateManager.updateUI();
    }

    Component.onCompleted: {
        initializeState();
        updateUI();
    }
}