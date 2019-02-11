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

        Text {
            id: errors_id
            width: parent.width
            text: downloader.errors
            font.pointSize: 16
            color: "red"
        }

        Row {
            id: progress_info_id
            spacing: 15
            width: parent.width
            ProgressBar {
                id: bar
                width: parent.width
                value: 0
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
                width: 150;
                onClicked: togglePause()
            }

            Button {
                id: reset_button
                text: "New download"
                width: 150;
                onClicked: abortDownload()
            }
        }

        Toast {
            id: complete_label
            toastVisible: false
        }

        InfoText {
            width: parent.width
            id: time_left_id
            label: "Time remaining:"
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

    }

    Connections {
        target: downloader
        onStateChanged: updateUI()
    }

    function getActualStateData() {
        return JSON.parse(downloader.state_data_json);
    }

    function updateUI() {
        var stateData = getActualStateData();
        AppManagement.stateManager.setState(downloader.download_state);
        AppManagement.stateManager.updateUI(stateData);
    }

    function startDownload() {
        downloader.configure(location.download_path,
                total_amount_id.value,
                images_per_category_spnibox.value
        );
        downloader.start_download()
    }

    function togglePause() {
        if (toggle_button.text === "Pause") {
            downloader.pause();
        } else {
            downloader.resume();
        }
    }

    function abortDownload() {
        downloader.reset();
    }

    Component.onCompleted: {
        updateUI();
    }
}
