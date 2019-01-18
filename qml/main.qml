import QtQuick 2.5
import QtQuick.Window 2.0
import QtQuick.Controls 2.2
import QtQuick.Dialogs 1.0


Window {
    id: root
    x: 400
    y: 400
    width: 600
    height: 650
    visible: true

    property int images_loaded: 0
    property int images_total: 10
    property int failures: 0
    property bool download_completed: true

    FileDialog {
        id: fileDialog
        title: "Please choose a file"
        folder: shortcuts.home
        selectFolder: true
        onAccepted: {
            console.log("You chose: " + fileDialog.fileUrls)
            download_path.text = String(fileDialog.fileUrls[0]);
        }
        onRejected: {
            console.log("Canceled")
        }
    }

    Column {
        spacing: 10
        width: parent.width

        Row {
            spacing: 15
            Text {
                text: "Download path"
            }
            Text {
                id: download_path
                text: ""
            }

            Button {
                text: "Choose"
                onClicked: {
                    fileDialog.open();
                    fileDialog.visible = true;
                }
            }
        }

        Row {
            spacing: 15
            width: parent.width

            Text {
                text: "maximum # of images to download"
            }
            SpinBox {
                id: amount_spnibox
                from: 1
                to: 100000
                value: 90
                editable: true
            }
        }

        Row {
            spacing: 15
            width: parent.width

            Text {
                text: "# of images per category"
            }
            SpinBox {
                id: images_per_category_spnibox
                from: 1
                to: 100000
                value: 100
                editable: true
            }
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
                onClicked: startDownload()
            }

            Button {
                id: toggle_button
                text: "Pause"
                onClicked: togglePause()
                visible: false
            }
        }

        Row {
            id: time_left_row
            spacing: 15
            visible: false
            anchors.horizontalCenter: parent.horizontalCenter
            Text {
                text: "Time remaining:"
                font.pointSize: 20.5
                font.bold: true
            }

            Text {
                id: time_left
                text: "0 seconds"
                font.pointSize: 20.5
                font.bold: true
            }
        }

        Row {
            id: downloaded_amount_row
            spacing: 15
            visible: false
            anchors.horizontalCenter: parent.horizontalCenter
            Text {
                text: "Downloaded:"
                font.pointSize: 20.5
                font.bold: true
            }

            Text {
                id: downloaded_amount
                text: root.images_loaded
                font.pointSize: 20.5
                font.bold: true
            }
        }

        Row {
            id: failures_amount_row
            spacing: 15
            visible: false
            anchors.horizontalCenter: parent.horizontalCenter
            Text {
                text: "Failures:"
                font.pointSize: 20.5
                font.bold: true
            }

            Text {
                id: failures_amount
                text: root.failures
                font.pointSize: 20.5
                font.bold: true
            }
        }

        ScrollView {
            width: parent.width
            height: 200

            ListView {
                id: failed_urls_model
                model: []
                delegate: ItemDelegate {
                    text: modelData
                }
            }
        }

        Text {
            id: complete_label
            text: "Download is complete"
            font.pointSize: 20.5
            font.bold: true
            visible: false
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
            complete_label.visible = true;
            time_left_row.visible = false;
            toggle_button.visible = false;
        }
    }

    function handleDownloadFailed(failures, failed_urls) {
        root.failures += failures;
        failed_urls_model.model = failed_urls;
    }

    function startDownload() {
        download_button.enabled = false;
        root.images_loaded = 0;
        root.failures = 0;
        complete_label.visible = false;
        time_left_row.visible = true;
        downloaded_amount_row.visible = true;
        failures_amount_row.visible = true;
        root.images_total = amount_spnibox.value;

        downloader.start_download(download_path.text,
                amount_spnibox.value,
                images_per_category_spnibox.value
        );

        download_button.visible = false;
        toggle_button.visible = true;
        toggle_button.enabled = true;
        toggle_button.text = "Pause";
    }

    function togglePause() {
        if (toggle_button.text === "Pause") {
            toggle_button.enabled = false;
            toggle_button.text = "Pausing"
            downloader.pause();
        } else {
            toggle_button.enabled = false;
            toggle_button.text = "Resume"
            downloader.resume();
        }
    }

    function handlePaused() {
        toggle_button.text = "Resume";
        toggle_button.enabled = true;
    }

    function handleResumed() {
        toggle_button.text = "Pause";
        toggle_button.enabled = true;
    }
}