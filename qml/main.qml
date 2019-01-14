import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Dialogs 1.0


Rectangle {
    id: root
    width: 600
    height: 500

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
                value: 0.65
            }

            Button {
                text: "Download"
                width: 1 * parent.width / 5
            }
        }
    }
}