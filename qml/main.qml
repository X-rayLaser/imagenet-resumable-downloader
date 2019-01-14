import QtQuick 2.5
import QtQuick.Window 2.0
import QtQuick.Controls 1.4
import QtQuick.Dialogs 1.0


Window {
    id: root
    width: 600
    height: 500
    visible: true

    property int images_loaded: 0
    property int images_total: 10
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
            ProgressBar {
                id: bar
                width: 3 * parent.width / 4
                value: images_loaded / images_total
            }

            Button {
                id: download_button
                text: "Download"
                width: 1 * parent.width / 5
                onClicked: {
                    download_button.enabled = false;
                    downloader.start_download(download_path.text);
                }
            }
        }
    }

    Connections {
        target: downloader
        onImageLoaded: {
            root.images_loaded += 1;
            if (root.images_loaded === root.images_total) {
                download_button.enabled = true;
            }
        }
    }
}